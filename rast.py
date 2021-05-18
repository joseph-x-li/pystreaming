from pystreaming import Collector, AudioReceiver, Buffer, display, playbuffer
import zmq


def main():
    context = zmq.Context()
    stream = Collector(context, "tcp://172.16.0.29:5555")
    audiostream = AudioReceiver(context, "tcp://172.16.0.29:5556")
    stream.start()
    collator = Buffer(
        0.5, 
        {'video': stream.handler, 'audio': audiostream.handler
    })
    try:
        for data in collator.handler():
            stream, data = data
            if stream == 'video':
                frame, _, _ = data
                display(frame)
            if stream == 'audio':
                buf, _, _ = data
                display(frame)
    except RuntimeError:
        collator.empty()
        stream.stop()
        print("Exiting Stream")


if __name__ == "__main__":
    main()
