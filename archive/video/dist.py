import zmq
import time
import multiprocessing as mp
import pystreaming.video.interface as intf
from pystreaming.listlib.circularlist import CircularList, Empty
from pystreaming.video import TRACKMISS, FRAMEMISS

TIMESTEP = 0.001


def dist_ps(shutdown, infd, endpt, rcvhwm, tracks):
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
        target = time.time() + TIMESTEP
        if collector.poll(0):  # returns 0 if no event, something else if there is
            buf, idx = intf.recv(collector, buf=True, flags=zmq.NOBLOCK)
            for fqueue in queues.values():
                fqueue.push((buf, idx))  # add to every buf queue

        if distributor.poll(0):  # got frame req
            track = distributor.recv().decode()
            try:
                buf, idx = queues[track].pop()
                intf.send(distributor, idx, buf=buf, flags=zmq.NOBLOCK)
            except Empty:  # Regular frame miss
                intf.send(distributor, FRAMEMISS, buf=b"nil", flags=zmq.NOBLOCK)
            except KeyError:  # Track miss
                intf.send(distributor, TRACKMISS, buf=b"nil", flags=zmq.NOBLOCK)

        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class Distributor:
    rcvhwm = 30

    def __init__(self, endpoint, seed="", tracks=None):
        """Create a multiprocessing frame distributor object.

        Args:
            endpoint (str): Descriptor of distributor endpoint.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
            tracks (list, optional): List of strings, where each string describes a track. Defaults to None.
        """
        self.infd = "ipc:///tmp/encout" + seed
        self.endpoint, self.tracks = endpoint, tracks
        self.shutdown = mp.Event()
        self.ps = None
        self.psargs = (self.shutdown, self.infd, self.endpoint, self.rcvhwm, tracks)

    def start(self):
        """Create and start a multiprocessing distributor thread.

        Raises:
            RuntimeError: Raised when method is called while a Distributor is running.
        """
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Distributor")

        self.ps = mp.Process(target=dist_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        """Join and destroy the multiprocessing distributor thread.

        Raises:
            RuntimeError: Raised when method is called while a Distributor is stopped.
        """
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Distributor")

        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += "-----Distributor-----\n"
        rpr += f"TRACK: \t{self.tracks}\n"
        rpr += f"IN: \t{self.infd}\n"
        rpr += f"OUT: \t{self.endpoint}\n"
        rpr += f"HWM: \t=IN> {self.rcvhwm})::(XX =OUT> "
        return rpr
