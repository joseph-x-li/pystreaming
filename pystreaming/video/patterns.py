from pystreaming import Encoder, Distributor, Decoder, Requester
import pystreaming.video.interface as intf
import pystreaming
import zmq, uuid
from zmq.devices import ProcessDevice


class Streamer:
    def __init__(self, context, endpoint, procs=2):
        seed = uuid.uuid1().hex
        self.encoder = Encoder(context, seed=seed, procs=procs)
        self.distributor = Distributor(endpoint, seed=seed)
        self.started = False

    def start(self):
        if self.started:
            raise RuntimeError("Tried to start a started Streamer")
        self.started = True
        self.encoder.start()
        self.distributor.start()

    def stop(self):
        if not self.started:
            raise RuntimeError("Tried to stop a stopped Streamer")
        self.started = False
        self.encoder.stop()
        self.distributor.stop()

    def send(self, frame):
        if not self.started:
            raise RuntimeError("Start the Streamer before sending frames")
        self.encoder.send(frame)

    def testsignal(self):
        if not self.started:
            self.start()
        self.encoder._testcard(pystreaming.TEST_M)


class Worker:
    outhwm = 30

    def __init__(self, context, source, drain, track="none", reqprocs=3, decprocs=2):
        seed = uuid.uuid1().hex
        self.requester = Requester(source, seed=seed, track=track, procs=reqprocs)
        self.decoder = Decoder(context, seed=seed, sndbuf=True, procs=decprocs)
        self.drain = context.socket(zmq.PUSH)
        self.drain.setsockopt(zmq.SNDHWM, self.outhwm)
        self.drain.connect(drain)

    def run(self, func):
        try:
            self.decoder.start()
            self.requester.start()
            for arr, buf, idx in self.decoder.handler():
                res = func(arr)
                print(res)
                try:
                    intf.send(self.drain, idx, buf=buf, meta=res, flags=zmq.NOBLOCK)
                except zmq.error.Again:
                    pass  # ignore send misses to drain.

        finally:
            self.requester.stop()
            self.decoder.stop()


class Collector:
    rcvhwm = 30
    outhwm = 30
    
    def __init__(self, context, endpoint):
        seed = uuid.uuid1().hex
        # https://het.as.utexas.edu/HET/Software/pyZMQ/api/zmq.devices.html#zmq.devices.ProcessDevice
        self.device = ProcessDevice(zmq.STREAMER, zmq.PULL, zmq.PUSH)
        self.device.setsockopt_in(zmq.RCVHWM, self.rcvhwm)
        self.device.setsockopt_out(zmq.SNDHWM, self.outhwm)
        self.device.bind_in(endpoint)
        self.device.bind_out("ipc:///tmp/decin" + seed)
        
        
        self.decoder = Decoder(context, seed=seed, rcvmeta=True)

    def handler(self):
        self.device.start()
        self.decoder.start()
        return self.decoder.handler()
