import zmq, zmq.asyncio
import asyncio, time
import multiprocessing as mp

async def aioreq(context, source, shutdown, drain):
    socket = context.socket(zmq.REQ)
    socket.connect(source)
    print("Started a frame request async thread")
    while not shutdown.is_set():
        await socket.send(b"TRACK1")
        buf = await socket.recv()
        idx = await socket.recv_pyobj()
        if idx == -1:
            continue
        print(f"AIO: Dropped in drain: {idx}")
        await drain.send(buf, copy=False, flags=zmq.SNDMORE)
        await drain.send_pyobj(idx)

async def workz(shutdown):
    while True:
        print("Work...")
        await asyncio.sleep(1)
async def stopcheck(shutdown):
    while True:
        print("SLEEP")
        await asyncio.sleep(5)
        print("hehexd RAISE")
        raise StopAsyncIteration

def aiomain(shutdown):
    args = [stopcheck(1), workz(1), workz(2)]
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(*args))
    except StopAsyncIteration as e:
        loop.stop()
        print("STOPPED DUE TO RAISED ERROR")


def main():
    time.sleep(1)
    ps = mp.Process(
            target=aiomain,
            args=(1,)
    )
    ps.daemon = True
    ps.start()
    ps.join()
    
if __name__ == "__main__":
    main()


class AIOREQ:
    outfd = "ipc:///tmp/decin"

    def __init__(self, source, procs=3):
        self.source, self.procs = source, procs
        self.shutdown = mp.Event()
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning AIOREQ obj")

        self.ps = mp.Process(
            target=aiomain,
            args=(self.source, self.outfd, self.procs, self.shutdown),
        )
        self.ps.daemon = True
        self.ps.start()

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped AIOREQ obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()