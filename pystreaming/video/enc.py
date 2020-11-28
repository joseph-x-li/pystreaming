from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import numpy as np
import zmq
import multiprocessing as mp
from functools import partial
from pystreaming.listlib.circularlist import CircularList
from pystreaming.video.interface import recv_ndarray_idx, send_ndarray_idx


def ps(shutdown, infd, outfd, rcvhwm, outhwm):
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
                arr, idx = recv_ndarray_idx(socket, flags=zmq.NOBLOCK)
                out.send(encoder(arr), copy=False, flags=zmq.SNDMORE|zmq.NOBLOCK)
                out.send_pyobj(idx)
                print(f"ENC: idx={idx}")
            except zmq.exception.Again:
                # ignore 
                pass

class Encoder:
    infd = "ipc:///tmp/encin"
    outfd = "ipc:///tmp/encout"
    tellhwm = 30
    rcvhwm = outhwm = 10

    def __init__(self, context, procs=2):
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.workers = []
        self.idx = 0

        self.sender = self.context.socket(zmq.PUSH)
        self.sender.set_sockopt(zmq.SNDHWM, self.sndhwm)
        self.sender.bind(self.infd)

    def send(self, frame):
        if self.workers == []:
            raise RuntimeError("Tried to send frame to stopped Encoder")
        try:
            send_ndarray_idx(self.sender, frame, self.idx, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            raise RuntimeError("Worker processes are not processing frames fast enough")
        # change behavior to:
        # IF working, but slow, print a warning
        # If not responding, only then raise runtime error

    def start_workers(self):
        if self.workers != []:
            raise RuntimeError("Tried to start running Encoder")
        for _ in range(self.procs):
            self.workers.append(mp.Process(target=ps, args=(self.shutdown, self.infd, self.outfd)))

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