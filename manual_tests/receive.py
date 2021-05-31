import sys
sys.path.insert(0,'..')
from pystreaming import Receiver, AudioReceiver, buffer, display
import sounddevice as sd
import zmq
import time


def main():
    outdevice = 1
    samplerate = 32000
    blocksize = 256
    source = "172.16.0.29"
    source = "localhost"

    import queue
    OUT = queue.Queue()
    def callback_out(outdata, frames, time, status):
        outdata[:] = OUT.get()

    with sd.OutputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            device=outdevice,
            channels=1,
            latency='low',
            callback=callback_out,
        ), Receiver(f"tcp://{source}:5555") as stream:
        audiostream = AudioReceiver(f"tcp://{source}:5556")
        for streamtype, data in buffer(0.5, {"video": stream.handler, "audio": audiostream.handler}):
            if streamtype == 'video':
                display(data['arr'])
            if streamtype == 'audio':
                OUT.put(data['arr'])


if __name__ == "__main__":
    main()
