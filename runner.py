import cv2 
import time
import pystreaming as stream
import zmq
import numpy as np

def gstreamer_pipeline(
    capture_width=1920,
    capture_height=1080,
    display_width=1920,
    display_height=1080,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def encdistmain(cam):
    try:
        context = zmq.Context()
        bank = stream.Encoder(context, procs=2)
        dist = stream.Distributor("tcp://*:5553")
        bank.start()
        dist.start()
        if cam is not None:
            while True:
                _, frame = cam.read()
                bank.send(frame)
        else:
            bank._testcard(stream.TEST_M, animated=True)
    except KeyboardInterrupt:
        pass
    finally:
        bank.stop()
        dist.stop()

def recvmain():
    context = zmq.Context()
    req = stream.Requester("tcp://172.16.0.49:5553")
    # req = stream.Requester("tcp://127.0.0.1:5553")
    dec = stream.Decoder(context, procs=2)
    req.start()
    dec.start()
    stream.display(stream.collate(dec.handler()), BGR=True)
    # stream.display(dec.handler(), BGR=True)
    req.stop()
    dec.stop()

def getstandcam(gst=False):
    if gst:
        cap = cv2.VideoCapture(gstreamer_pipeline(
            capture_width=640,
            capture_height=480,
            display_width=640,
            display_height=480,
            flip_method=2,
        ), cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPEG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def yielder(animated=True):
    print("yielder primed")
    testimage = stream.loadimage(5)
    storage = []
    for ang in range(360):
        storage.append(np.asarray(testimage.rotate(ang)))
    i = 0
    if animated:
        while True:
            time.sleep(1/30)
            yield (i, storage[i % 360])
            i += 1
    else:
        while True:
            time.sleep(1/30)
            yield storage[0]

if __name__ == "__main__":
    # stream.display(stream.collate(yielder()), BGR=False)
    # encdistmain(getstandcam(gst=True))
    recvmain()