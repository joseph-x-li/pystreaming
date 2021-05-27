import zmq
import time

from ..stream import interface as intf
from . import TRACKMISS, FRAMEMISS, DIST_TIMESTEP, DIST_HWM
from .device import Device
from ..listlib.circularlist import CircularList, Empty


def dist_ps(*, shutdown, barrier, infd, endpoint, tracks):
    context = zmq.Context()
    collector = context.socket(zmq.PULL)
    collector.setsockopt(zmq.RCVHWM, DIST_HWM)
    collector.bind(infd)
    distributor = context.socket(zmq.REP)
    distributor.bind(endpoint)
    barrier.wait()
    queues = {track: CircularList() for track in tracks}
    while not shutdown.is_set():
        target = time.time() + DIST_TIMESTEP
        if collector.poll(0):  # returns 0 if no event, something else if there is
            data = intf.recv(socket=collector, buf=True, flags=zmq.NOBLOCK)
            for fqueue in queues.values():  # add to every buf queue
                fqueue.push(data)
        if distributor.poll(0):  # got frame req
            track = distributor.recv().decode()
            data = {}
            try:
                data = queues[track].pop()
            except Empty:  # Regular frame miss
                data["fno"] = FRAMEMISS
                data["ftime"] = None
                data["meta"] = None
                data["buf"] = b"nil"
            except KeyError:  # Track miss
                data["fno"] = TRACKMISS
                data["ftime"] = None
                data["meta"] = None
                data["buf"] = b"nil"
            intf.send(
                socket=distributor,
                flags=zmq.NOBLOCK,
                **data,
            )
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class DistributorDevice(Device):
    def __init__(self, tracks, endpoint, seed):
        """Create a multiprocessing frame distributor device.

        Args:
            tracks (list): List of strings, where each string describes a track.
            endpoint (str): Descriptor of distributor endpoint.
            seed (str): File descriptor seed (to prevent ipc collisions).
        """
        self.infd = "ipc:///tmp/encout" + seed
        self.endpoint, self.tracks = endpoint, tracks
        dkwargs = {"infd": self.infd, "endpoint": self.endpoint, "tracks": self.tracks}
        super().__init__(dist_ps, dkwargs, 1)

    def __repr__(self):
        rpr = "-----DistributorDevice-----\n"
        rpr += f"{'TRACKS': <8}{self.tracks}\n"
        rpr += f"{'IN': <8}{self.infd}\n"
        rpr += f"{'OUT': <8}{self.endpoint}\n"
        rpr += f"{'HWM': <8}> {DIST_HWM})(XX >"
        return rpr
