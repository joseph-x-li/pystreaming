from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import zmq, time
from functools import partial
import pystreaming.video.interface as intf
import multiprocessing as mp


def dec_ps(shutdown, infd, outfd, rcvhwm, outhwm):
    print("Starting Decoder")
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.setsockopt(zmq.RCVHWM, rcvhwm)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.setsockopt(zmq.SNDHWM, outhwm)
    out.connect(outfd)
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))

    while not shutdown.is_set():
        time.sleep(0.01)  # 100 cycles a sec
        if poller.poll(0):
            try:
                buf, idx = intf.recv_buf_idx(socket, flags=zmq.NOBLOCK)
                intf.send_ndarray_idx(out, decoder(buf), idx, flags=zmq.NOBLOCK)
            except zmq.error.Again:
                # ignore send misses to out.
                pass

    print("Stopping Decoder")


class Decoder:
    infd = "ipc:///tmp/decin"
    outfd = "ipc:///tmp/decout"
    hearhwm = 30
    rcvhwm = outhwm = 10

    def __init__(self, context, procs=2):
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.psargs = (self.shutdown, self.infd, self.outfd, self.rcvhwm, self.outhwm)
        self.workers = []

        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(self.outfd)

    def recv(self):
        if self.workers == []:
            raise RuntimeError("Tried to receive frame from stopped Decoder")
        # Add timeout function?
        return intf.recv_ndarray_idx(self.receiver)

    def handler(self):
        if self.workers == []:
            raise RuntimeError("Cannot produce stream handler from stopped Decoder")
        while True:
            yield intf.recv_ndarray_idx(self.receiver)

    def start(self):
        if self.workers != []:
            raise RuntimeError("Tried to start running Decoder")
        for _ in range(self.procs):
            self.workers.append(mp.Process(target=dec_ps, args=self.psargs))
        for ps in self.workers:
            ps.daemon = True
            ps.start()

        time.sleep(2)

    def stop(self):
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Decoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()
