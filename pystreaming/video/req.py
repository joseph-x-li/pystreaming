import zmq
import zmq.asyncio
import asyncio
import multiprocessing as mp
from pystreaming.video import STOPSTREAM, FRAMEMISS, TRACKMISS


"""Stop on STOPSTREAM, or TRACKMISS
Continue on FRAMEMISS
Wait at most TIMEOUT for receiving a response?
    have to use async poll for this behavior
"""


async def aioreq(context, source, track, drain):
    socket = context.socket(zmq.REQ)
    socket.connect(source)
    track_bytes = bytes(track, "utf-8")
    while True:
        # rate limit to 30x a second => 90x requests a sec by default with 3 threads
        await asyncio.sleep(1 / 30)
        await socket.send(track_bytes)
        buf = await socket.recv()
        idx = await socket.recv_pyobj()
        if idx == STOPSTREAM:
            raise StopAsyncIteration(f"Stop stream signal received... Exiting...")
        if idx == FRAMEMISS:
            continue  # throw away if no frame available
        if idx == TRACKMISS:
            raise StopAsyncIteration(
                f'Track "{track}" was not recognized by the Distributor.'
            )
        try:
            await drain.send(buf, copy=False, flags=zmq.SNDMORE | zmq.NOBLOCK)
            await drain.send_pyobj(idx, flags=zmq.NOBLOCK)
        except zmq.error.Again:
            pass  # ignore send misses to drain.


async def stop(shutdown):
    while True:
        await asyncio.sleep(0.1)  # Check 10x a second
        if shutdown.is_set():
            raise StopAsyncIteration()


def aiomain(source, track, outfd, procs, shutdown, outhwm):
    context = zmq.asyncio.Context()
    drain = context.socket(zmq.PUSH)
    drain.setsockopt(zmq.SNDHWM, outhwm)
    drain.bind(outfd)
    args = [aioreq(context, source, track, drain) for _ in range(procs)]
    args.append(stop(shutdown))
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(*args))
    except Exception:
        loop.stop()
        context.destroy(linger=0)
        loop.close()


class Requester:
    outhwm = 10

    def __init__(self, source, seed="", track="none", procs=3):
        """Create a forked asyncio frame requester object.

        Args:
            source (str): Descriptor of stream endpoint.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
            track (str, optional): Video stream track name. Defaults to "none".
            procs (int, optional): Number of requester threads. Defaults to 3.
        """
        self.outfd = "ipc:///tmp/decin" + seed
        self.source, self.procs, self.track = source, procs, track
        self.shutdown = mp.Event()
        self.psargs = (
            self.source,
            self.track,
            self.outfd,
            self.procs,
            self.shutdown,
            self.outhwm,
        )
        self.ps = None

    def start(self):
        """Create and start asyncio requester threads.

        Raises:
            RuntimeError: Raised when method is called while a Requester is running.
        """
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Requester obj")
        self.ps = mp.Process(target=aiomain, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        """Join and destroy asyncio requester threads.

        Raises:
            RuntimeError: Raised when method is called while a Requester is stopped.
        """
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Requester obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += "-----Requester-----\n"
        rpr += f"THD:\t{self.procs}\n"
        rpr += f"TRACK:\t{self.track}\n"
        rpr += f"IN:\t{self.source}\n"
        rpr += f"OUT:\t{self.outfd}\n"
        rpr += f"HWM:\t=IN> XX)::({self.outhwm} =OUT> "
        return rpr
