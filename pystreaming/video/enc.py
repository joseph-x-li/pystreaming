from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import numpy as np
import zmq
import multiprocessing as mp
from functools import partial
import pystreaming.video.interface as intf


def enc_ps(shutdown, infd, outfd, rcvhwm, outhwm):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, outhwm)
    out.connect(outfd)
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    encoder = partial(
        TurboJPEG().encode, quality=70, jpeg_subsample=TJSAMP_420, flags=TJFLAG_FASTDCT
    )
    while not shutdown.is_set():
        if poller.poll(0):
            try:
                arr, idx = intf.recv_ndarray_idx(socket, flags=zmq.NOBLOCK)
                intf.send_buf_idx(socket, encoder(arr), idx, flags=zmq.NOBLOCK)
            except zmq.exception.Again:
                # ignore send misses to distributor.
                # Should not happen if there is a distributor.
                # Could implement a signal that there is a distributor. Not strictly necessary tho.
                pass


class Encoder:
    infd = "ipc:///tmp/encin"
    outfd = "ipc:///tmp/encout"
    tellhwm = 30
    rcvhwm = outhwm = 10

    def __init__(self, context, procs=2):
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.psargs = (
            self.infd,
            self.outfd,
            self.rcvhwm,
            self.outhwm,
        )
        self.workers = []
        self.idx = 0

        self.sender = self.context.socket(zmq.PUSH)
        self.sender.set_sockopt(zmq.SNDHWM, self.sndhwm)
        self.sender.bind(self.infd)

    def send(self, frame):
        if self.workers == []:
            raise RuntimeError("Tried to send frame to stopped Encoder")
        try:
            intf.send_ndarray_idx(self.sender, frame, self.idx, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            raise RuntimeError("Worker processes are not processing frames fast enough")
        # change behavior to:
        # IF working, but slow, print a warning
        # If not responding, only then raise runtime error

    def start_workers(self):
        if self.workers != []:
            raise RuntimeError("Tried to start running Encoder")
        for _ in range(self.procs):
            self.workers.append(
                mp.Process(
                    target=enc_ps,
                    args=self.psargs,
                )
            )

        for ps in self.workers:
            ps.daemon = True
            ps.start()

    def stop_workers(self):
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Encoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()