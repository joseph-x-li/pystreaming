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

    context = zmq.Context()

    devices = [
        ps.EncoderDevice(context, 2, ""),
        ps.DecoderDevice(context, 2, ""),
        ps.DistributorDevice(["none"], "tcp://*:5555", ""),
        ps.PublisherDevice("tcp://*:5556", ""),
        ps.RequesterDevice("tcp://localhost:5557", "none", 3, ""),
        ps.SubscriberDevice("tcp://127.0.0.1:5558", ""),
        ps.Streamer(context, "tcp://*:5559"),
        ps.Streamer(context, "tcp://*:5560", mapreduce=True),
        ps.Collector(context, "tcp://localhost:5561"),
        ps.Collector(context, "tcp://*:5562", mapreduce=True),
        # ps.Worker(),
    ]
    for dev in devices:
        stopandgo(dev)
