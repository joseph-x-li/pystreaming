import time
import zmq
from functools import partial
from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE

from . import interface as intf
from . import DEC_TIMESTEP, DEC_HWM
from .BASE import Device


def dec_ps(*, shutdown, barrier, infd, outfd, fwdbuf):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, DEC_HWM)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, DEC_HWM)
    out.connect(outfd)
    barrier.wait()
    decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))
    while not shutdown.is_set():
        target = time.time() + DEC_TIMESTEP
        if socket.poll(0):
            buf, meta, ftime, fno = intf.recv(
                socket=socket, buf=True, flags=zmq.NOBLOCK
            )
            buf = buf if fwdbuf else None
            try:
                intf.send(
                    socket=out,
                    fno=fno,
                    ftime=ftime,
                    meta=meta,
                    arr=decoder(buf),
                    buf=buf,
                    flags=zmq.NOBLOCK,
                )
            except zmq.error.Again:
                pass
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class DecoderDevice(Device):
    def __init__(self, context, nproc, seed, fwdbuf=False):
        """Create a multiprocessing frame decoder device.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            nproc (int): Number of decoding processes.
            seed (str): File descriptor seed (to prevent ipc collisions).
            fwdbuf (bool, optional): True if we forward the compressed frame. Defaults to False.
        """
        self.infd = "ipc:///tmp/decin" + seed
        self.outfd = "ipc:///tmp/decout" + seed
        self.context, self.nproc, self.fwdbuf = context, nproc, fwdbuf
        dkwargs = {"infd": self.infd, "outfd": self.outfd, "fwdbuf": self.fwdbuf}
        super().__init__(dec_ps, dkwargs, nproc)
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.setsockopt(zmq.RCVHWM, DEC_HWM)
        self.receiver.bind(self.outfd)

    def recv(self, timeout=60_000):
        """Receive a package of data from the decoder pool.

        Args:
            timeout (int, optional): Timeout period in milliseconds.
            Set to None to wait forever. Defaults to 60_000.

        Raises:
            TimeoutError: Raised when no messages are received in the timeout period.

        Returns:
            list: [arr, buf, meta, ftime, fno].
        """
        self.start()
        if self.receiver.poll(timeout):
            return intf.recv(
                socket=self.receiver,
                arr=True,
                buf=self.fwdbuf,
                meta=self.rcvmeta,
                flags=zmq.NOBLOCK,
            )
        else:
            raise TimeoutError(
                f"No messages were received within the timeout period {timeout}ms"
            )

    def handler(self):
        """Yield a package of data from the decoder pool.

        Yields:
            list: [arr, buf, meta, ftime, fno].
        """
        while True:
            yield self.recv()

    def __repr__(self):
        rpr = "-----DecoderDevice-----\n"
        rpr += f"{'PCS': <8}{self.nproc}\n"
        rpr += f"{'FWDBUF': <8}{self.fwdbuf}\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}> {DEC_HWM})({DEC_HWM} > {DEC_HWM})"
        return rpr
