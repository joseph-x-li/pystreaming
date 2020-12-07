from turbojpeg import TurboJPEG, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import zmq
from functools import partial
import pystreaming.video.interface as intf
import multiprocessing as mp

# Status: Not loop optimized

def dec_ps(shutdown, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.connect(outfd)
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    decoder = partial(TurboJPEG().decode, flags=(TJFLAG_FASTDCT + TJFLAG_FASTUPSAMPLE))

    while not shutdown.is_set():
        if poller.poll(0):
            buf = socket.recv()
            idx = socket.recv_pyobj()
            frame = decoder(buf)
            send_ndarray_idx(frame, out, idx)


class UltraJPGDec:
    infd = "ipc:///tmp/decin"
    outfd = "ipc:///tmp/decout"

    def __init__(self, context, procs=2):
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.workers = []

        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(self.outfd)

    def hear(self):  # returns frame, idx
        return recv_ndarray_idx(self.receiver)

    def start_workers(self):
        if self.workers != []:
            print("Warning: tried to start a running jpg decoder bank... Ignoring")
            return

        for _ in range(self.procs):
            self.workers.append(
                mp.Process(target=dec_ps, args=(self.shutdown, self.infd, self.outfd))
            )
        for ps in self.workers:
            ps.daemon = True
            ps.start()

    def stop_workers(self):
        if self.workers == []:
            print("Warning: tried to stop a stopped jpg decoder bank... Ignoring")
            return

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()
        self.running = False