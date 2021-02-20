from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT
import numpy as np
import zmq
import time
import multiprocessing as mp
from functools import partial
from itertools import count
from pystreaming.video.testimages.imageloader import loadimage
import pystreaming.video.interface as intf
from pystreaming.video import QUALITY, STOPSTREAM

TIMESTEP = 0.01


def enc_ps(shutdown, infd, outfd, rcvhwm, sndhwm):
    context = zmq.Context()

    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.connect(infd)

    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, sndhwm)
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
        target = time.time() + TIMESTEP
        if poller.poll(0):
            try:
                arr, idx = intf.recv(socket, arr=True, flags=zmq.NOBLOCK)
                intf.send(out, idx, buf=encoder(arr), flags=zmq.NOBLOCK)
            except zmq.error.Again:
                pass
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class Encoder:
    inhwm = 30
    rcvhwm = sndhwm = 10

    def __init__(self, context, seed="", procs=2):
        """Create a multiprocessing frame encoder object.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
            procs (int, optional): Number of encoding processes. Defaults to 2.
        """
        self.infd = "ipc:///tmp/encin" + seed
        self.outfd = "ipc:///tmp/encout" + seed
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.rcvhwm, self.sndhwm)
        self.workers = []
        self.idx = 0

        self.sender = self.context.socket(zmq.PUSH)
        self.sender.setsockopt(zmq.SNDHWM, self.inhwm)
        self.sender.bind(self.infd)

    def send(self, frame):
        """Send a frame to the encoder bank.

        Args:
            frame (np.ndarray): A frame of video. Send None to stop the stream.

        Raises:
            RuntimeError: Raised when method is called while a Encoder is stopped.
            RuntimeError: Raised if encoder processes cannot compresss frame fast enough
        """
        if self.workers == []:
            raise RuntimeError("Tried to send frame to stopped Encoder")
        try:
            if frame is None:
                intf.send(
                    self.sender, STOPSTREAM, np.zeros((10, 10, 3)), flags=zmq.NOBLOCK
                )
                ...  # Initiate STOPSTREAM
                return
            intf.send(self.sender, self.idx, arr=frame, flags=zmq.NOBLOCK)
            self.idx += 1
        except zmq.error.Again:
            raise RuntimeError("Worker processes are not processing frames fast enough")
            # change behavior to:
            # IF working, but slow, print a warning
            # If not responding, only then raise runtime error

    def start(self):
        """Create and start multiprocessing encoder threads.

        Raises:
            RuntimeError: Raised when method is called while a Encoder is running.
        """
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
        """Join and destroy multiprocessing encoder threads.

        Raises:
            RuntimeError: Raised when method is called while a Encoder is stopped.
        """
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Encoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()

    def _testcard(self, cardenum, animated=False):
        """Display a testcard or a test image. Automatically starts the object
        if not already started. This method is blocking.

        Args:
            cardenum (int): One of
                pystreaming.TEST_S
                pystreaming.TEST_M
                pystreaming.TEST_L
                pystreaming.IMAG_S
                pystreaming.IMAG_M
                pystreaming.IMAG_L
            animated (bool, optional): Set True to make image rotate. Defaults to False.
        """
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
        rpr += "-----Encoder-----\n"
        rpr += f"PCS: \t{self.procs}\n"
        rpr += f"IN: \t{self.infd}\n"
        rpr += f"OUT: \t{self.outfd}\n"
        rpr += f"HWM: \t({self.inhwm} =IN> {self.rcvhwm})::({self.sndhwm} =OUT> "
        return rpr
