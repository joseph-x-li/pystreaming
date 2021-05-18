from pystreaming import Collector, AudioReceiver, Buffer, display
import sounddevice as sd
import zmq
import time


def main():
    context = zmq.Context()
    stream = Collector(context, "tcp://172.16.0.29:5555")
    audiostream = AudioReceiver(context, "tcp://172.16.0.29:5556")
    stream.start()
    buffer = Buffer(0.5, {"video": stream.handler, "audio": audiostream.handler})

    time.sleep(1)

    import queue

    outdevice = 1
    samplerate = 32000
    blocksize = 256
    OUT = queue.Queue()

    def callback_out(outdata, frames, time, status):
        outdata[:] = OUT.get()

    try:
        with sd.OutputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            device=outdevice,
            channels=1,
            callback=callback_out,
        ):
            for data in buffer.handler():
                streamtype, data = data
                if streamtype == 'video':
                    frame, _, _ = data
                    display(frame)
                if streamtype == 'audio':
                    arr, _, _ = data
                    OUT.put(arr)
    except RuntimeError:
        buffer.empty()
        stream.stop()
        print("Exiting Stream")


if __name__ == "__main__":
    main()
