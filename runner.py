import cv2 
import time
import pystreaming as stream
import zmq

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
    start = time.time()
    for i in range(n):
        print(i)
        bank.send(cam.read()[1])
        time.sleep(1/30)
    print(f"Did {n} frames in {time.time() - start}, fps = {n / (time.time() - start)}")
    print("STOPPING")
    bank.stop_workers()
    dist.stop()

def recvmain():
    context = zmq.Context()
    req = stream.Requester("tcp://172.16.0.49:5553")
    dec = stream.Decoder(context, procs=2)
    req.start()
    dec.start()
    while True:
        frame, idx = dec.hear()
        cv2.imshow("test", frame)
        cv2.waitKey(0)
        print(f"Finally got idx={idx}")

class fakecamera:
    def __init__(self, size):
        self.frame = cv2.imread(f"./pystreaming/video/testcards/{size}.png")
    def read(self):
        return None, self.frame

if __name__ == "__main__":
    # cap = cv2.VideoCapture(gstreamer_pipeline(
    #     capture_width=640,
    #     capture_height=480,
    #     display_width=640,
    #     display_height=480,
    #     flip_method=2,
    # ), cv2.CAP_GSTREAMER)
    # cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"RG10"))
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    # cap.set(cv2.CAP_PROP_FPS, 30)
    # encdistmain(fakecamera("1920x1080"))
    recvmain()