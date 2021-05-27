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
        # ps.Streamer(context, "tcp://*:5559"),
        # ps.Streamer(context, "tcp://*:5560", mapreduce=True),
        # ps.Collector(context, "tcp://localhost:5561"),
        # ps.Collector(context, "tcp://*:5562", mapreduce=True),
        # ps.Worker(),
    ]
    for dev in devices:
        stopandgo(dev)
