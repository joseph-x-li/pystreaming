import zmq
import time
import pystreaming.video.interface as intf

from . import PUB_TIMESTEP, PUB_HWM
from .BASE import Device


def pullpub_ps(*, shutdown, barrier, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, PUB_HWM)
    socket.bind(infd)
    out = context.socket(zmq.PUB)
    out.setsockopt(zmq.SNDHWM, PUB_HWM)
    out.bind(outfd)
    barrier.wait()
    while not shutdown.is_set():
        target = time.time() + PUB_TIMESTEP
        if socket.poll(0):
            buf, meta, ftime, fno = intf.recv(
                socket=socket, buf=True, flags=zmq.NOBLOCK
            )
            try:
                intf.send(
                    socket=out,
                    fno=fno,
                    ftime=ftime,
                    meta=meta,
                    buf=buf,
                    flags=zmq.NOBLOCK,
                )
            except zmq.error.Again:
                pass
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)  # loop takes at minimum TIMESTEP seconds


class PublisherDevice(Device):
    def __init__(self, endpoint, seed):
        """Create a publisher device.

        Binds to a zmq PULL socket and republishes through a PUB socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.infd = "ipc:///tmp/encout" + seed
        self.outfd = endpoint
        dkwargs = {"infd": self.infd, "outfd": self.outfd}
        super().__init__(pullpub_ps, dkwargs, 1)

    def __repr__(self):
        rpr = "-----Publisher-----\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}> {PUB_HWM})({PUB_HWM} >"
        return rpr
