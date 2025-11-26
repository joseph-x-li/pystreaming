import contextlib
import time
from functools import partial

import numpy as np
import zmq
from turbojpeg import TJFLAG_FASTDCT, TJSAMP_420, TurboJPEG

from ..stream import interface as intf
from . import (
    ENC_HWM,
    ENC_TIMESTEP,
    QUALITY,
    STOPSTREAM,
    STOPSTREAM_DUMMY_FRAME_SIZE,
    STOPSTREAM_SLEEP_SECONDS,
)
from .device import Device


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
    try:
        while not shutdown.is_set():
            target = time.time() + ENC_TIMESTEP
            if socket.poll(0):
                data = intf.recv(socket=socket, arr=True, flags=zmq.NOBLOCK)
                if data.arr is not None:
                    buf_data = encoder(data.arr)
                with contextlib.suppress(zmq.Again):
                    intf.send(
                        socket=out,
                        fno=data.fno,
                        ftime=data.ftime,
                        meta=data.meta,
                        buf=buf_data,
                        flags=zmq.NOBLOCK,
                    )
            missing = target - time.time()
            if missing > 0:
                time.sleep(missing)
    finally:
        # Clean up sockets and context
        with contextlib.suppress(Exception):
            socket.close(linger=0)
            out.close(linger=0)
            context.term()


class EncoderDevice(Device):
    def __init__(self, nproc, seed):
        """Create a multiprocessing frame encoder device.

        Args:
            nproc (int): Number of encoding processes.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.context = zmq.Context.instance()
        self.infd = "ipc:///tmp/encin" + seed
        self.outfd = "ipc:///tmp/encout" + seed
        dkwargs = {"infd": self.infd, "outfd": self.outfd}
        super().__init__(enc_ps, dkwargs, nproc)
        self.idx = 0
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.setsockopt(zmq.SNDHWM, ENC_HWM)
        self.sender.bind(self.infd)

    def stop(self) -> None:
        """Stop the encoder device and clean up resources."""
        if hasattr(self, "sender") and self.sender:
            with contextlib.suppress(Exception):
                self.sender.close(linger=0)
            self.sender = None
        super().stop()

    def send(self, frame: np.ndarray | None) -> None:
        """Send a frame to the encoder bank.

        Args:
            frame (np.ndarray | None): A frame of video. Send None to stop the stream.

        Raises:
            RuntimeError: Raised if encoder processes cannot compress frame fast enough
        """
        if self.sender is None:
            raise RuntimeError("Encoder device has been stopped")
        try:
            if frame is None:
                intf.send(
                    socket=self.sender,
                    fno=STOPSTREAM,
                    ftime=time.time(),
                    meta=None,
                    arr=np.zeros((STOPSTREAM_DUMMY_FRAME_SIZE, STOPSTREAM_DUMMY_FRAME_SIZE, 3)),
                    flags=zmq.NOBLOCK,
                )
                time.sleep(STOPSTREAM_SLEEP_SECONDS)
                self.stop()
                return
            intf.send(
                socket=self.sender,
                fno=self.idx,
                ftime=time.time(),
                arr=frame,
                meta=None,
                flags=zmq.NOBLOCK,
            )
            self.idx += 1
        except zmq.Again as e:
            raise RuntimeError(
                "Worker processes are not processing frames fast enough. Decrease resolution or increase nproc."
            ) from e

    def __repr__(self):
        rpr = "-----EncoderDevice-----\n"
        rpr += f"{'PCS': <8}{self.nproc}\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}({ENC_HWM} > {ENC_HWM})"
        return rpr
