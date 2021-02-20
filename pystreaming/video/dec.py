from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import zmq
import time
from functools import partial
import multiprocessing as mp
import pystreaming.video.interface as intf

TIMESTEP = 0.01


def dec_ps(shutdown, infd, outfd, rcvmeta, sndbuf, rcvhwm, sndhwm):
    context = zmq.Context()

    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.connect(infd)

    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, sndhwm)
    out.connect(outfd)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))
    while not shutdown.is_set():
        target = time.time() + TIMESTEP
        if poller.poll(0):
            try:
                package = intf.recv(socket, buf=True, meta=rcvmeta, flags=zmq.NOBLOCK)

                # Handle receiving meta
                if rcvmeta:
                    buf, meta, idx = package
                else:
                    buf, idx = package
                    meta = None

                arr = decoder(buf)

                # Handle forwarding buffer
                buf = buf if sndbuf else None

                intf.send(out, idx, arr=arr, buf=buf, meta=meta, flags=zmq.NOBLOCK)

            except zmq.error.Again:
                pass  # ignore send misses to out.

        missing = target - time.time()
        if missing > 0:
            time.sleep(missing)


class Decoder:
    outhwm = 20
    rcvhwm = sndhwm = 10

    def __init__(self, context, seed="", rcvmeta=False, sndbuf=False, procs=2):
        """Create a multiprocessing frame decoder object.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            seed (str, optional): File descriptor seed (to prevent ipc collisions). Defaults to "".
            rcvmeta (bool, optional): True if we expect to receive metadata. Defaults to False.
            sndbuf (bool, optional): True if we forward the compressed frame. Defaults to False.
            procs (int, optional): Number of decoding processes. Defaults to 2.
        """
        self.infd = "ipc:///tmp/decin" + seed
        self.outfd = "ipc:///tmp/decout" + seed
        self.context, self.procs = context, procs
        self.rcvmeta, self.sndbuf = rcvmeta, sndbuf
        self.shutdown = mp.Event()
        self.psargs = (
            self.shutdown,
            self.infd,
            self.outfd,
            rcvmeta,
            sndbuf,
            self.rcvhwm,
            self.sndhwm,
        )
        self.workers = []
        self.receiver = None

    def recv(self, timeout=60_000):
        """Receive a package of data from the decoder pool.

        Args:
            timeout (int, optional): Timeout period in milliseconds.
            Set to None to wait forever. Defaults to 60_000.

        Raises:
            RuntimeError: Raised when method is called while a Decoder is stopped.
            TimeoutError: Raised when no messages are received in the timeout period.

        Returns:
            list: Either [arr, buf, meta, idx] or [arr, buf, idx] or [arr, meta, idx] or [arr, idx]
        """
        if self.workers == []:
            raise RuntimeError("Tried to receive frame from stopped Decoder")

        if self.receiver is None:
            self.receiver = self.context.socket(zmq.PULL)
            self.receiver.setsockopt(zmq.RCVHWM, self.outhwm)
            self.receiver.bind(self.outfd)

        if self.receiver.poll(timeout):
            return intf.recv(
                self.receiver,
                arr=True,
                buf=self.sndbuf,
                meta=self.rcvmeta,
                flags=zmq.NOBLOCK,
            )
        else:
            raise TimeoutError(
                f"No messages were received within the timeout period {timeout}ms"
            )

    def handler(self):
        """Yield a package of data from the decoder pool.

        Yields:
            list: Either [arr, buf, meta, idx] or [arr, buf, idx]
        """
        while True:
            yield self.recv()

    def start(self):
        """Create and start multiprocessing decoder threads.

        Raises:
            RuntimeError: Raised when method is called while a Decoder is running.
        """
        if self.workers != []:
            raise RuntimeError("Tried to start running Decoder")
        for _ in range(self.procs):
            self.workers.append(mp.Process(target=dec_ps, args=self.psargs))
        for ps in self.workers:
            ps.daemon = True
            ps.start()

        time.sleep(2)  # Allow workers to initialize
        print(self)

    def stop(self):
        """Join and destroy multiprocessing decoder threads.

        Raises:
            RuntimeError: Raised when method is called while a Decoder is stopped.
        """
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Decoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += "-----Decoder-----\n"
        rpr += f"PCS: \t{self.procs}\n"
        rpr += f"IN: \t{self.infd}\n"
        rpr += f"OUT: \t{self.outfd}\n"
        rpr += f"HWM: \t=IN> {self.rcvhwm})::({self.sndhwm} =OUT> {self.outhwm})"
        return rpr
