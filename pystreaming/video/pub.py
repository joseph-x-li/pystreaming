import zmq
import time
import multiprocessing as mp
import pystreaming.video.interface as intf

TIMESTEP = 0.01


def pullpub_ps(shutdown, infd, outfd, rcvhwm, sndhwm):
    context = zmq.Context()

    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.bind(infd)

    out = context.socket(zmq.PUB)
    out.setsockopt(zmq.SNDHWM, sndhwm)
    out.bind(outfd)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    while not shutdown.is_set():
        target = time.time() + TIMESTEP
        if poller.poll(0):
            try:
                buf, idx = intf.recv(socket, buf=True, flags=zmq.NOBLOCK)
                intf.send(out, idx, buf=buf, flags=zmq.NOBLOCK)
            except zmq.error.Again:
                pass

        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)  # loop takes at minimum TIMESTEP seconds


class Publisher:
    rcvhwm = sndhwm = 10

    def __init__(self, endpoint, seed=""):
        """Create a multiprocessing publisher.

        Binds to a zmq PULL socket and republishes through a PUB socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
        """
        self.infd = "ipc:///tmp/encout" + seed
        self.outfd = endpoint
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.rcvhwm, self.sndhwm)
        self.ps = None

    def start(self):
        """Create and start multiprocessing publisher threads.

        Raises:
            RuntimeError: Raised when method is called while a Publisher is running.
        """
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Publisher obj")
        self.ps = mp.Process(target=pullpub_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        """Join and destroy multiprocessing publisher threads.

        Raises:
            RuntimeError: Raised when method is called while a Publisher is stopped.
        """
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Publisher obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += "-----Publisher-----\n"
        rpr += f"IN:\t{self.infd}\n"
        rpr += f"OUT:\t{self.outfd}\n"
        rpr += f"HWM:\t=IN> {self.rcvhwm})::({self.sndhwm} =OUT> "
        return rpr
