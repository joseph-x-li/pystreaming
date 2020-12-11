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

n = 10000

def encdistmain(cam):
    context = zmq.Context()
    bank = stream.Encoder(context, procs=2)
    dist = stream.Distributor("tcp://*:5553")
    bank.start()
    dist.start()
    bank._testcard(stream.TEST_M)
    # start = time.time()
    # for i in range(n):
    #     print(i)
    #     bank.send(cam.read()[1])
    #     time.sleep(1/30)
    # print(f"Did {n} frames in {time.time() - start}, fps = {n / (time.time() - start)}")
    # print("STOPPING")
    # bank.stop_workers()
    # dist.stop()

def recvmain():
    context = zmq.Context()
    req = stream.Requester("tcp://172.16.0.49:5553")
    dec = stream.Decoder(context, procs=2)
    req.start()
    dec.start()
    while True:
        frame, idx = dec.recv()
        cv2.imshow("test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
        print(f"Finally got idx={idx}")

class fakecamera:
    def __init__(self, size):
        self.frame = cv2.imread(f"./pystreaming/video/testimages/{size}.png")
    def read(self):
        time.sleep(1/35)
        return None, self.frame

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
    testimage = stream.loadimage(5)
    storage = []
    for ang in range(360):
        storage.append(np.asarray(testimage.rotate(ang)))
    i = 0
    if animated:
        while True:
            time.sleep(1/30)
            yield storage[i % 360]
            i += 1
    else:
        while True:
            time.sleep(1/30)
            yield storage[0]

if __name__ == "__main__":
    x = fakecamera("640x480_c")
    
    stream.display(yielder(), BGR=False)
    
    # encdistmain(fakecamera("1920x1080"))
    # recvmain()