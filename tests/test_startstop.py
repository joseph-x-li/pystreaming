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
        ps.Encoder(context),
        ps.Decoder(context),
        ps.Distributor("tcp://*:5555"),
        ps.Publisher("tcp://*:5556"),
        ps.Requester("tcp://127.0.0.1:5557"),
        ps.Subscriber("tcp://127.0.0.1:5558"),
        ps.Streamer(context, "tcp://*:5559"),
        ps.Streamer(context, "tcp://*5560", mapreduce=True),
        ps.Collector(context, "tcp://*:5561"),
        ps.Collector(context, "tcp://*:5562", mapreduce=True),
        # ps.Worker(),
    ]
    for dev in devices:
        stopandgo(dev)
