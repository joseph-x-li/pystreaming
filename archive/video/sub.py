import zmq
import time
import multiprocessing as mp
import pystreaming.video.interface as intf

TIMESTEP = 0.01


def subpush_ps(shutdown, infd, outfd, rcvhwm, sndhwm):
    context = zmq.Context()

    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.connect(infd)
    socket.subscribe("")  # subscribe to all topics

    out = context.socket(zmq.PUSH)
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
                pass  # Ignore misses to send out
        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)  # loop takes at minimum TIMESTEP seconds


class Subscriber:
    rcvhwm = sndhwm = 10

    def __init__(self, endpoint, seed=""):
        """Create a multiprocessing subscriber.

        Connects to a zmq SUB socket and republishes through a PUSH socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
        """
        self.infd = endpoint
        self.outfd = "ipc:///tmp/decin" + seed
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.rcvhwm, self.sndhwm)
        self.ps = None

    def start(self):
        """Create and start multiprocessing subscriber threads.

        Raises:
            RuntimeError: Raised when method is called while a Subscriber is running.
        """
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Subscriber obj")
        self.ps = mp.Process(target=subpush_ps, args=self.psargs)
        self.ps.daemon = True
        self.ps.start()
        print(self)

    def stop(self):
        """Join and destroy multiprocessing subscriber threads.

        Raises:
            RuntimeError: Raised when method is called while a Subscriber is stopped.
        """
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Subscriber obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += "-----Subscriber-----\n"
        rpr += f"IN:\t{self.infd}\n"
        rpr += f"OUT:\t{self.outfd}\n"
        rpr += f"HWM:\t=IN> {self.rcvhwm})::({self.sndhwm} =OUT> "
        return rpr
