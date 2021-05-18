from pystreaming import Collector
from pystreaming.stream.handlers import Collator, display
import zmq

def main():
    stream = Collector(zmq.Context(), "tcp://172.16.0.29:5555")
    stream.start()
    collator = Collator(0.5, {'video': stream.handler})
    try:
        for data in collator.handler():
            stream, data = data
            if stream == 'video':
                frame, _, _ = data
                display(frame)
    except RuntimeError:
        collator.empty()
        stream.stop()
        print("Exiting Stream")
if __name__ == '__main__':
    main()
