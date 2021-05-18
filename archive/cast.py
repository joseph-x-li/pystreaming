import pystreaming as ps
import numpy as np
import zmq
import time

def sender():
    image = ps.loadimage(ps.IMAG_L)
    imnp = np.asarray(image)
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("ipc:///tmp/mooey565")
    arr = imnp
    while True:
        # msg = socket.recv()
        md = {"dtype": str(arr.dtype), "shape": arr.shape}
        socket.send_json(md, flags=zmq.SNDMORE)
        socket.send(arr, copy=False)

def receiver():
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("ipc:///tmp/mooey565")
    start = time.time()
    n = 0
    while True:
        # socket.send(b"hi")
        md = socket.recv_json()
        msg = socket.recv(copy=False)
        arrbuf = memoryview(msg)
        frame = np.frombuffer(arrbuf, dtype=md["dtype"]).reshape(md["shape"])
        n += 1
        print(f"Received frame size {frame.shape}. FPS: {n / (time.time() - start)}")
    
if __name__ == '__main__':
    sender()
    # receiver()