import cv2, zmq, time
import sys
sys.path.insert(0,'..')
import pystreaming
import sounddevice as sd


def main():
    # set up camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    indevice = 0
    blocksize = 256
    samplerate = 32000

    start, n = time.time(), 0

    audiostream = pystreaming.AudioStreamer("tcp://*:5556")
    def callback_in(indata, frames, time, status):
        audiostream.send(indata.copy())
    with sd.InputStream(
        samplerate=samplerate,
        blocksize=blocksize,
        device=indevice,
        channels=1,
        callback=callback_in,
    ), pystreaming.Streamer("tcp://*:5555") as stream:
        while True:
            n += 1
            ret, frame = cap.read()
            stream.send(frame)
            print(f"\rFPS: {(n / (time.time() - start)):.3f}", end="")

if __name__ == "__main__":
    main()