import asyncio
import contextlib
from multiprocessing.synchronize import Barrier, Event
from typing import Any

import zmq
import zmq.asyncio

from . import (
    ASYNC_STOP_SLEEP_SECONDS,
    FRAMEMISS,
    REQ_HWM,
    REQ_TIMESTEP,
    STOPSTREAM,
    TRACKMISS,
)
from .device import Device

"""Stop on STOPSTREAM, or TRACKMISS
Continue on FRAMEMISS
Wait at most TIMEOUT for receiving a response?
    have to use async poll for this behavior
"""


async def aioreq(
    context: zmq.asyncio.Context,
    source: str,
    track: str,
    drain: zmq.asyncio.Socket,
    lock: asyncio.Lock,
) -> None:
    socket = context.socket(zmq.REQ)
    socket.connect(source)
    track_bytes = bytes(track, "utf-8")
    while True:
        await asyncio.sleep(REQ_TIMESTEP)
        await socket.send(track_bytes)
        buf = await socket.recv()
        meta = await socket.recv_pyobj()
        ftime = await socket.recv_pyobj()
        fno = await socket.recv_pyobj()
        if fno == STOPSTREAM:
            raise StopAsyncIteration("Stop stream signal received. Exiting.")
        if fno == FRAMEMISS:
            continue  # throw away if no frame available
        if fno == TRACKMISS:
            raise StopAsyncIteration(f'Track "{track}" was not recognized. Exiting.')
        with contextlib.suppress(zmq.Again):
            async with lock:
                await drain.send(buf, copy=False, flags=zmq.SNDMORE | zmq.NOBLOCK)
                await drain.send_pyobj(meta, flags=zmq.SNDMORE | zmq.NOBLOCK)
                await drain.send_pyobj(ftime, flags=zmq.SNDMORE | zmq.NOBLOCK)
                await drain.send_pyobj(fno, flags=zmq.NOBLOCK)


async def stop(shutdown: Event) -> None:
    while True:
        await asyncio.sleep(ASYNC_STOP_SLEEP_SECONDS)
        if shutdown.is_set():
            raise StopAsyncIteration()


def aiomain(
    *,
    shutdown: Event,
    barrier: Barrier,
    source: str,
    outfd: str,
    track: str,
    nthread: int,
) -> None:
    context = zmq.asyncio.Context()
    drain = context.socket(zmq.PUSH)
    drain.setsockopt(zmq.SNDHWM, REQ_HWM)
    drain.bind(outfd)
    lock = asyncio.Lock()
    args = [aioreq(context, source, track, drain, lock) for _ in range(nthread)]
    args.append(stop(shutdown))
    loop = asyncio.get_event_loop()
    barrier.wait()
    try:
        loop.run_until_complete(asyncio.gather(*args))
    except StopAsyncIteration:
        pass
    finally:
        # Clean up async context and loop
        with contextlib.suppress(Exception):
            loop.stop()
            context.destroy(linger=0)
            loop.close()


class RequesterDevice(Device):
    def __init__(self, source, track, nthread, seed):
        """Create a asyncio frame requester device.

        Args:
            source (str): Descriptor of stream endpoint.
            track (str): Video stream track name.
            nthread (int): Number of requester threads.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.outfd = "ipc:///tmp/decin" + seed
        self.source, self.nthread, self.track = source, nthread, track
        dkwargs = {
            "source": self.source,
            "outfd": self.outfd,
            "track": self.track,
            "nthread": self.nthread,
        }
        super().__init__(aiomain, dkwargs, 1)

    def __repr__(self):
        rpr = "-----RequesterDevice-----\n"
        rpr += f"{'THDS': <8}{self.nthread}\n"
        rpr += f"{'TRACK': <8}{self.track}\n"
        rpr += f"{'IN': <8}{self.source}\n"
        rpr += f"{'OUT': <8}{self.outfd}\n"
        rpr += f"{'HWM': <8}(XX > {REQ_HWM})"
        return rpr
