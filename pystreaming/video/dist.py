import zmq
import multiprocessing as mp
import pystreaming.video.interface as intf
from pystreaming.listlib.circularlist import CircularList, Empty

def distributor(shutdown, infd, endpt, rcvhwm, tracks):
    context = zmq.Context()
    collector = context.socket(zmq.PULL)
    collector.setsockopt(zmq.RCVHWM, rcvhwm)
    collector.bind(infd)
    distributor = context.socket(zmq.REP)
    distributor.bind(endpt)
    if tracks is None:
        tracks = ["none"]
    queues = {track:CircularList() for track in tracks}
    while not shutdown.is_set():
        if collector.poll(0):  # returns 0 if no event, something else if there is
            buf, idx = intf.recv_buf_idx(collector, flags=zmq.NODELAY)
            for fqueue in queues.values():
                fqueue.push((buf, idx)) # add to queue
        if distributor.poll(0): # got frame req
            track = distributor.recv().decode()
            try:
                buf, idx = queues[track].pop()
                intf.send_buf_idx(distributor, buf, idx, flags=zmq.NODELAY)
            except (KeyError, Empty):
                intf.send_buf_idx(distributor, b'nil', -1, flags=zmq.NODELAY)

class Distributor:
    infd = "ipc:///tmp/encout"
    rcvhwm = 30
    def __init__(self, endpoint, tracks=None):
        self.shutdown = mp.Event()
        self.ps = None
        self.psargs = (self.shutdown, self.infd, endpoint, self.rcvhwm)
    
    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Distributor")

        self.ps = mp.Process(
            target=distributor,
            args=self.psargs
        )
        self.ps.daemon = True
        self.ps.start()

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Distributor")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()   