import contextlib
import time

import zmq

from ..stream import interface as intf
from . import SUB_HWM, SUB_TIMESTEP
from .device import Device


def subpush_ps(*, shutdown, barrier, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, SUB_HWM)
    socket.connect(infd)
    socket.subscribe("")  # subscribe to all topics
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, SUB_HWM)
    out.bind(outfd)
    barrier.wait()
    try:
        while not shutdown.is_set():
            target = time.time() + SUB_TIMESTEP
            if socket.poll(0):
                data = intf.recv(socket=socket, buf=True, flags=zmq.NOBLOCK)
                with contextlib.suppress(zmq.Again):
                    intf.send(
                        socket=out,
                        flags=zmq.NOBLOCK,
                        **data,
                    )
            missing = target - time.time()
            if missing > 0:
                time.sleep(missing)  # loop takes at minimum TIMESTEP seconds
    finally:
        # Clean up sockets and context
        with contextlib.suppress(Exception):
            socket.close(linger=0)
            out.close(linger=0)
            context.term()


class SubscriberDevice(Device):
    def __init__(self, endpoint, seed):
        """Create a multiprocessing subscriber.

        Connects to a zmq SUB socket and republishes through a PUSH socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
        """
        self.infd = endpoint
        self.outfd = "ipc:///tmp/decin" + seed
        dkwargs = {"infd": self.infd, "outfd": self.outfd}
        super().__init__(subpush_ps, dkwargs, 1)

    def __repr__(self):
        rpr = "-----SubscriberDevice-----\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}({SUB_HWM} > {SUB_HWM})"
        return rpr
