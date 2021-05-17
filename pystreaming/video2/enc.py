import time
import zmq
import numpy as np
from functools import partial
from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT

from . import interface as intf
from . import QUALITY, STOPSTREAM, ENC_TIMESTEP, ENC_HWM
from .BASE import Device


def enc_ps(*, shutdown, barrier, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, ENC_HWM)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, ENC_HWM)
    out.connect(outfd)
    barrier.wait()
    encoder = partial(
        TurboJPEG().encode,
        quality=QUALITY,
        jpeg_subsample=TJSAMP_420,
        flags=TJFLAG_FASTDCT,
    )
    while not shutdown.is_set():
        target = time.time() + ENC_TIMESTEP
        if socket.poll(0):
            arr, meta, ftime, fno = intf.recv(
                socket=socket, arr=True, flags=zmq.NOBLOCK
            )
            try:
                intf.send(
                    contex=out,
                    fno=fno,
                    ftime=ftime,
                    meta=meta,
                    buf=encoder(arr),
                    flags=zmq.NOBLOCK,
                )
            except zmq.error.Again:
                pass
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class EncoderDevice(Device):
    def __init__(self, context, nproc, seed):
        """Create a multiprocessing frame encoder device.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            nproc (int): Number of encoding processes.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.context = context
        self.infd = "ipc:///tmp/encin" + seed
        self.outfd = "ipc:///tmp/encout" + seed
        dkwargs = {"infd": self.infd, "outfd": self.outfd}
        super().__init__(enc_ps, dkwargs, nproc)
        self.idx = 0
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.setsockopt(zmq.SNDHWM, ENC_HWM)
        self.sender.bind(self.infd)

    def send(self, frame):
        """Send a frame to the encoder bank.

        Args:
            frame (np.ndarray): A frame of video. Send None to stop the stream.

        Raises:
            RuntimeError: Raised if encoder processes cannot compresss frame fast enough
        """
        try:
            if frame is None:
                intf.send(
                    socket=self.sender,
                    fno=STOPSTREAM,
                    ftime=time.time(),
                    arr=np.zeros((10, 10, 3)),
                    flags=zmq.NOBLOCK,
                )
                time.sleep(1)
                self.stop()
                return
            intf.send(
                socket=self.sender,
                fno=self.idx,
                ftime=time.time(),
                arr=frame,
                flags=zmq.NOBLOCK,
            )
            self.idx += 1
        except zmq.error.Again:
            raise RuntimeError(
                "Worker processes are not processing frames fast enough. Decrease resolution or increase nproc."
            )

    def __repr__(self):
        rpr = "-----EncoderDevice-----\n"
        rpr += f"{'PCS': <8}{self.nproc}\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}({ENC_HWM} > {ENC_HWM})({ENC_HWM} >"
        return rpr
