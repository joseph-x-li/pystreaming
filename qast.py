import pystreaming, cv2, zmq, time
import sounddevice as sd

# set up camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# set up microphone
indevice = 0
blocksize = 256
samplerate = 32000

# set up video stream backend
context = zmq.Context()
stream = pystreaming.Streamer(context, "tcp://*:5555")
stream.start()

# set up audio stream backend
audiostream = pystreaming.AudioStreamer(context, "tcp://*:5556")


def callback_in(indata, frames, time, status):
    audiostream.send(indata.copy(), realtime=time)


time.sleep(1)

start, n = time.time(), 0
with sd.InputStream(
    samplerate=samplerate,
    blocksize=blocksize,
    device=indevice,
    channels=1,
    callback=callback_in,
):
    while True:
        n += 1
        ret, frame = cap.read()
        stream.send(frame)
        print(f"\rFPS: {(n / (time.time() - start)):.3f}", end="")
