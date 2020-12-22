from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import numpy as np
import zmq, time
import multiprocessing as mp
from functools import partial
from itertools import count
from pystreaming.video.testimages.imageloader import loadimage
import pystreaming.video.interface as intf

QUALITY = 50


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
        TurboJPEG().encode,
        quality=QUALITY,
        jpeg_subsample=TJSAMP_420,
        flags=TJFLAG_FASTDCT,
    )
    while not shutdown.is_set():
        time.sleep(0.01)  # 100 cycles/sec
        if poller.poll(0):
            try:
                arr, idx = intf.recv(socket, arr=True, flags=zmq.NOBLOCK)
                intf.send(out, idx, buf=encoder(arr), flags=zmq.NOBLOCK)
            except zmq.error.Again:
                # ignore send misses to distributor.
                # Should not happen if there is a distributor.
                # Could implement a signal that there is a distributor. Not strictly necessary tho.
                pass


class Encoder:
    tellhwm = 30
    rcvhwm = outhwm = 10

    def __init__(self, context, seed="", procs=2):
        self.infd = "ipc:///tmp/encin" + seed
        self.outfd = "ipc:///tmp/encout" + seed
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.rcvhwm, self.outhwm)
        self.workers = []
        self.idx = 0

        self.sender = self.context.socket(zmq.PUSH)
        self.sender.setsockopt(zmq.SNDHWM, self.tellhwm)
        self.sender.bind(self.infd)

    def send(self, frame):
        if self.workers == []:
            raise RuntimeError("Tried to send frame to stopped Encoder")
        try:
            intf.send(self.sender, self.idx, arr=frame, flags=zmq.NOBLOCK)
            self.idx += 1
        except zmq.error.Again:
            raise RuntimeError("Worker processes are not processing frames fast enough")
            # change behavior to:
            # IF working, but slow, print a warning
            # If not responding, only then raise runtime error

    def start(self):
        if self.workers != []:
            raise RuntimeError("Tried to start running Encoder")
        for _ in range(self.procs):
            self.workers.append(mp.Process(target=enc_ps, args=self.psargs))

        for ps in self.workers:
            ps.daemon = True
            ps.start()

        time.sleep(2)  # Allow workers to spin up
        print(self)

    def stop(self):
        """Stop a pool of encoders.

        Raises:
            RuntimeError: Raised when the Encoder is already stopped
        """
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Encoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()

    def _testcard(self, cardenum, animated=False):
        testimage = loadimage(cardenum)
        if self.workers == []:
            self.start()
        if animated:
            storage = []
            for ang in range(360):
                storage.append(np.asarray(testimage.rotate(ang)))
        else:
            storage = np.asarray(testimage)
        for i in count():
            print(i)
            self.send(storage[i % 360] if animated else storage)
            time.sleep(1 / 30)

    def __repr__(self):
        rpr = ""
        rpr += f"-----Encoder-----\n"
        rpr += f"PCS: \t{self.procs}\n"
        rpr += f"IN: \t{self.infd}\n"
        rpr += f"OUT: \t{self.outfd}\n"
        rpr += f"HWM: \t({self.tellhwm} =IN> {self.rcvhwm})::({self.outhwm} =OUT> "
        return rpr