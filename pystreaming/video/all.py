from turbojpeg import TurboJPEG, TJSAMP_420, TJFLAG_FASTDCT, TJFLAG_FASTUPSAMPLE
import cv2
import numpy as np
import zmq, time, asyncio, zmq.asyncio
import multiprocessing as mp
from functools import partial
from ..listlib.circularlist import CircularList


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


def distributor(shutdown, infd, endpoint):
    context = zmq.Context()
    collector = context.socket(zmq.PULL)
    collector.bind(infd)
    distributor = context.socket(zmq.REP)
    distributor.bind(endpoint)
    queue = CircularList()
    queues = {}
    while not shutdown.is_set():
        if collector.poll(0):  # returns 0 if no event, something else if there is
            buf = collector.recv() # get buf
            idx = collector.recv_pyobj() # then get idx
            queue.push((buf, idx)) # add to queue
        if distributor.poll(0): # got frame req
            _ = distributor.recv()
            package = queue.pop()
            buf, idx = (b"nil", -1) if package is None else package
            distributor.send(buf, copy=False, flags=zmq.SNDMORE) # send out buf, the idx
            distributor.send_pyobj(idx)


async def aioreq(context, source, shutdown, drain):
    socket = context.socket(zmq.REQ)
    socket.connect(f"{source}")
    print("Started a frame request async thread")
    while not shutdown.is_set():
        await socket.send(b"TRACK1")
        buf = await socket.recv()
        idx = await socket.recv_pyobj()
        if idx == -1:
            continue
        print(f"AIO: Dropped in drain: {idx}")
        await drain.send(buf, copy=False, flags=zmq.SNDMORE)
        await drain.send_pyobj(idx)

def aiomain(source, outfd, procs, shutdown):
    context = zmq.asyncio.Context()
    drain = context.socket(zmq.PUSH)
    drain.bind(outfd)
    args = [aioreq(context, source, shutdown, drain) for _ in range(procs)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*args))

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

class Distributor:
    infd = "ipc:///tmp/encout"
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.shutdown = mp.Event()
        self.ps = None
    
    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning Distributor obj")

        self.ps = mp.Process(
            target=distributor,
            args=(self.shutdown, self.infd, self.endpoint),
        )
        self.ps.daemon = True
        self.ps.start()

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped Distributor obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()   

class AIOREQ:
    outfd = "ipc:///tmp/decin"
    def __init__(self, source, procs=3):
        self.source, self.procs = source, procs
        self.shutdown = mp.Event()
        self.ps = None

    def start(self):
        if self.ps is not None:
            raise RuntimeError("Tried to start a runnning AIOREQ obj")

        self.ps = mp.Process(
            target=aiomain,
            args=(self.source, self.outfd, self.procs, self.shutdown),
        )
        self.ps.daemon = True
        self.ps.start()

    def stop(self):
        if self.ps is None:
            raise RuntimeError("Tried to stop a stopped AIOREQ obj")
        self.shutdown.set()
        self.ps.join()
        self.ps = None
        self.shutdown.clear()

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

class Sequencer:
    infd1

class VideoPlayer:
    infd = "ipc:///tmp/sequenced"
    def play(self, context):
        socket = context.socket(zmq.SUB)
        socket.connect(self.infd)
        while True:
            id, frame, _ = socket.recv
            print(f"\r frame: {idx}", end="")
            cv2.imshow('mpjpeg.VideoPlayer', frame)
            if cv2.waitKey(1): 
                break
        cv2.destroyAllWindows() 
        
class VideoWriter:
    ...

# STREAM # cam =frame> ENC =buf,idx> DIS =buf,idx> 

# WORKER # =buf,idx> AIOREQ =buf,idx> DEC =frame,idx> func =res,idx> PUSH =res,idx>

# COLLEX # =res,idx> PULL =(resout)res,idx> 
# COLLEX # =buf,idx> AIOREQ =buf,idx> DEC =(decout)frame,idx> 
# COLLEX # =res,frame,idx> SEQ =(sequenced)res,frame,idx> 
# COLLEX # =res,frame,idx> Filewriter
# COLLEX # =res,frame,idx> VideoPlayer

def encdistmain():
    frame = cv2.imread("pystreaming/pycodec/test_imgs/1280x720.jpg")
    context = zmq.Context()
    bank = UltraJPGEnc(context)
    dist = Distributor("tcp://127.0.0.1:5553")
    bank.start_workers()
    dist.start()
    for i in range(100):
        print(i)
        time.sleep(.5)
        bank.tell(frame)
    print("call1")
    bank.stop_workers()
    print("call2")
    dist.stop()
    
    
if __name__ == "__main__":
    encdistmain()
    # context = zmq.Context()
    # bank = UltraJPGEnc(context, procs=2)
    # bank.start_workers()
    # cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # start = time.time()
    # for i in range(1000):
    #     print(i)
    #     ret, frame = cap.read()
    #     bank.tell(frame)
    #     if i > 4:
    #         buf = bank.hear()
    # print(f"Done in {1000/(time.time() - start)} FPS")

    # bank.stop_workers()
