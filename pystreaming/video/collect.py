import zmq
import time

from ..stream import interface as intf
from . import COLLECT_TIMESTEP, COLLECT_HWM
from .device import Device


def collect_ps(*, shutdown, barrier, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, COLLECT_HWM)
    socket.bind(infd)
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, COLLECT_HWM)
    out.bind(outfd)
    barrier.wait()
    while not shutdown.is_set():
        target = time.time() + COLLECT_TIMESTEP
        if socket.poll(0):
            data = intf.recv(socket=socket, buf=True, flags=zmq.NOBLOCK)
            try:
                intf.send(
                    socket=out,
                    flags=zmq.NOBLOCK,
                    **data,
                )
            except zmq.error.Again:
                pass
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)  # loop takes at minimum TIMESTEP seconds


class CollectDevice(Device):
    def __init__(self, endpoint, seed):
        """Create a collection device.

        Binds to a zmq PULL socket and republishes through a PUSH socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.infd = endpoint
        self.outfd = "ipc:///tmp/decin" + seed
        dkwargs = {"infd": self.infd, "outfd": self.outfd}
        super().__init__(collect_ps, dkwargs, 1)

    def __repr__(self):
        rpr = "-----CollectDevice-----\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}> {COLLECT_HWM})({COLLECT_HWM} >"
        return rpr
