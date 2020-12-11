import zmq, time
import multiprocessing as mp
import pystreaming.video.interface as intf
from pystreaming.listlib.circularlist import CircularList, Empty


# Note. It might be better to implement this as a asyncio system?


def dist_ps(shutdown, infd, endpt, rcvhwm, tracks):
    print(f"Start Distributing to {endpt}")
    context = zmq.Context()
    collector = context.socket(zmq.PULL)
    collector.setsockopt(zmq.RCVHWM, rcvhwm)
    collector.bind(infd)
    distributor = context.socket(zmq.REP)
    distributor.bind(endpt)
    if tracks is None:  # default track is "none"
        tracks = ["none"]
    queues = {track: CircularList() for track in tracks}
    while not shutdown.is_set():

        time.sleep(0.001)  # 1000 cycles/sec ~> 4-6 streams at once.

        if collector.poll(0):  # returns 0 if no event, something else if there is
            buf, idx = intf.recv_buf_idx(collector, flags=zmq.NOBLOCK)
            for fqueue in queues.values():
                fqueue.push((buf, idx))  # add to buf queue

        if distributor.poll(0):  # got frame req
            track = distributor.recv().decode()
            try:
                buf, idx = queues[track].pop()
                intf.send_buf_idx(distributor, buf, idx, flags=zmq.NOBLOCK)
            except (KeyError, Empty):  # no frames available or wrong track selected
                intf.send_buf_idx(distributor, b"nil", -1, flags=zmq.NOBLOCK)

    print("Distributor stopped")


class Distributor:
    infd = "ipc:///tmp/encout"
    rcvhwm = 30

    def __init__(self, endpoint, tracks=None):
        self.shutdown = mp.Event()
        self.ps = None
        self.psargs = (self.shutdown, self.infd, endpoint, self.rcvhwm, tracks)

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Distributor")

        self.ps = mp.Process(target=dist_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Distributor")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()
