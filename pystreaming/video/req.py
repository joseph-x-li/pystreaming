import zmq, zmq.asyncio, asyncio
import multiprocessing as mp


async def aioreq(context, source, track, drain):
    socket = context.socket(zmq.REQ)
    socket.connect(source)
    while True:
        # rate limit to 30x a second => 90x requests a sec by default
        await asyncio.sleep(1 / 30)
        await socket.send(bytes(track, "utf-8"))
        buf = await socket.recv()
        idx = await socket.recv_pyobj()
        if idx == -1:
            continue  # throw away if no frame available
        await drain.send(buf, copy=False, flags=zmq.SNDMORE)
        await drain.send_pyobj(idx)


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
        self.outfd = "ipc:///tmp/decin" + seed
        self.source, self.procs, self.track = source, procs, track
        self.shutdown = mp.Event()
        self.psargs = (self.source, self.track, self.outfd, self.procs, self.shutdown, self.outhwm)
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning AIOREQ obj")
        self.ps = mp.Process(target=aiomain, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped AIOREQ obj")
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