from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import numpy as np
import zmq, time, asyncio, zmq.asyncio
import multiprocessing as mp
from functools import partial
from pystreaming.listlib.circularlist import CircularList


def recv_ndarray_idx(socket):  # returns frame, idx
    md = socket.recv_json()
    msg = socket.recv(copy=False)
    buf = memoryview(msg)
    A = np.frombuffer(buf, dtype=md["dtype"])
    return A.reshape(md["shape"]), md["idx"]


def send_ndarray_idx(arr, socket, idx):
    md = dict(
        dtype=str(arr.dtype),
        shape=arr.shape,
        idx=idx,
    )
    socket.send_json(md, zmq.SNDMORE)
    socket.send(arr, copy=False)


def enc_ps(shutdown, infd, outfd):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(infd)
    out = context.socket(zmq.PUSH)
    out.connect(outfd)
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    encoder = partial(
        TurboJPEG().encode, quality=70, jpeg_subsample=TJSAMP_420, flags=TJFLAG_FASTDCT
    )
    while not shutdown.is_set():
        if poller.poll(0):
            arr, idx = recv_ndarray_idx(socket)
            buf = encoder(arr)
            out.send(buf, copy=False, flags=zmq.SNDMORE)
            out.send_pyobj(idx)
            print(f"ENC: idx={idx}")

class UltraJPGEnc:
    infd = "ipc:///tmp/encin"
    outfd = "ipc:///tmp/encout"

    def __init__(self, context, procs=2):
        self.context, self.procs = context, procs
        self.shutdown = mp.Event()
        self.workers = []
        self.idx = 0

        self.sender = self.context.socket(zmq.PUSH)
        self.sender.bind(self.infd)

    def tell(self, frame):
        send_ndarray_idx(frame, self.sender, self.idx)
        self.idx += 1

    def start_workers(self):
        if self.workers != []:
            raise RuntimeError(
                "Warning: tried to start running jpg encoder bank... Ignoring"
            )
        self.workers = [
            mp.Process(target=enc_ps, args=(self.shutdown, self.infd, self.outfd))
            for _ in range(self.procs)
        ]
        for ps in self.workers:
            ps.daemon = True
            ps.start()

    def stop_workers(self):
        if self.workers == []:
            print("Warning: tried to stop stopped jpg encoder bank... Ignoring")
            return

        self.shutdown.set()
        for ps in self.workers:
            ps.join()
        self.workers = []
        self.shutdown.clear()