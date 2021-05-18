import pystreaming, cv2, zmq, time
import sounddevice as sd

# set up camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# set up microphone
indevice = 0
device_info = sd.query_devices(indevice, 'input')
samplerate = int(device_info['default_samplerate'])

# set up video stream backend
stream = pystreaming.Streamer(zmq.Context(), "tcp://*:5555") 
stream.start()

# set up audio stream backend
audiostream = pystreaming.AudioStreamer(zmq.Context(), "tcp://*:5556")
def callback_in(indata, frames, time, status):
    audiostream.send(indata.copy())

time.sleep(1)

start, n = time.time(), 0
with sd.InputStream(samplerate=samplerate, device=indevice, channels=1, callback=callback_in):
    while True:
        n += 1
        ret, frame = cap.read()
        stream.send(frame)
        print(f"\rFPS: {(n / (time.time() - start)):.3f}", end="")

