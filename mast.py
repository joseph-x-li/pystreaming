import pystreaming as ps
import zmq

def main():
    context = zmq.Context()
    devices = [
        ps.EncoderDevice(context, 2, ""),
        ps.DistributorDevice(["none"], "tcp://*:5555", ""),
        ps.DecoderDevice(context, 2, ""),
        ps.PublisherDevice("tcp://*:5556", ""),
        ps.SubscriberDevice("tcp://localhost:5557", ""),
        ps.RequesterDevice("tcp://localhost:5558", "none", 3, ""),
    ]
    for d in devices:
        d.start()
        print(d)
    for d in devices:
        d.stop()
    import time; time.sleep(4)
    print("done")

if __name__ == "__main__":
    main()