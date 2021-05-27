import zmq
import time
import pystreaming as ps


def teststartstop():
    def stopandgo(x):
        x.start()
        time.sleep(1)
        x.stop()
        time.sleep(1)
        x.start()
        time.sleep(1)
        x.stop()

    devices = [
        ps.EncoderDevice(2, "a"),
        ps.DecoderDevice(2, "b"),
        ps.DistributorDevice(["none"], "tcp://*:5555", "c"),
        ps.PublisherDevice("tcp://*:5556", "d"),
        ps.RequesterDevice("tcp://localhost:5557", "none", 3, "e"),
        ps.SubscriberDevice("tcp://127.0.0.1:5558", "f"),
        ps.CollectDevice("tcp://*:5559", "g"),
    ]
    for dev in devices:
        stopandgo(dev)

def testpatterns():
    patterns = [
        ps.Streamer("tcp://*:5560"),
        ps.Streamer("tcp://*:5561", mapreduce=True),
        ps.Receiver("tcp://localhost:5562"),
        ps.Receiver("tcp://*:5563", mapreduce=True),
        ps.Worker("tcp://localhost:5564", "tcp://localhost:5565"),
    ]
    for pattern in patterns:
        with pattern:
            time.sleep(1)
        time.sleep(1)
        with pattern:
            time.sleep(1)