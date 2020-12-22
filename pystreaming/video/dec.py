from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import zmq, time
from functools import partial
import pystreaming.video.interface as intf
import multiprocessing as mp


def dec_ps(shutdown, infd, outfd, rcvmeta, sndbuf, rcvhwm, outhwm):
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
                package = intf.recv(socket, buf=True, meta=rcvmeta, flags=zmq.NOBLOCK)
                if rcvmeta:
                    buf, meta, idx = package
                else:
                    buf, idx = package
                    meta = None
                arr = decoder(buf)
                buf = buf if sndbuf else None
                intf.send(out, idx, arr=arr, buf=buf, meta=meta, flags=zmq.NOBLOCK)
            except zmq.error.Again:
                pass  # ignore send misses to out.


class Decoder:
    hearhwm = 30
    rcvhwm = outhwm = 10

    def __init__(self, context, seed="", rcvmeta=False, sndbuf=False, procs=2):
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
            self.outhwm,
        )
        self.workers = []

        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.setsockopt(zmq.RCVHWM, self.hearhwm)
        self.receiver.bind(self.outfd)

    def recv(self):
        if self.workers == []:
            raise RuntimeError("Tried to receive frame from stopped Decoder")
        # Add timeout function?
        return intf.recv(self.receiver, arr=True, buf=self.sndbuf, meta=self.rcvmeta)

    def handler(self):
        if self.workers == []:
            raise RuntimeError("Cannot produce stream handler from stopped Decoder")
        while True:
            yield intf.recv(self.receiver, arr=True, buf=self.sndbuf, meta=self.rcvmeta)

    def start(self):
        if self.workers != []:
            raise RuntimeError("Tried to start running Decoder")
        for _ in range(self.procs):
            self.workers.append(mp.Process(target=dec_ps, args=self.psargs))
        for ps in self.workers:
            ps.daemon = True
            ps.start()

        time.sleep(2)  # allow workers to initialize
        print(self)

    def stop(self):
        if self.workers == []:
            raise RuntimeError("Tried to stop stopped Decoder")

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()

    def __repr__(self):
        rpr = ""
        rpr += f"-----Decoder-----\n"
        rpr += f"PCS: \t{self.procs}\n"
        rpr += f"IN: \t{self.infd}\n"
        rpr += f"OUT: \t{self.outfd}\n"
        rpr += f"HWM: \t=IN> {self.rcvhwm})::({self.outhwm} =OUT> {self.hearhwm})"
        return rpr