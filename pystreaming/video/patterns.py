from pystreaming import Encoder, Distributor, Decoder, Requester
import zmq, uuid

class Streamer:
    def __init__(self, context, endpoint, procs=2):
        self.encoder = Encoder(context, procs=procs)
        self.distributor = Distributor(endpoint)
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
        
class Worker:
    def __init__(self, context, sourcepoint, drainpoint, track=None, reqprocs=3, procs=2):
        self.requester = Requester(sourcepoint, track=track, procs=reqprocs)
        self.decoder = Decoder(context, procs=procs)
        self.drain = context.socket(zmq.PUSH)
    
    def run(self, func):
        self.decoder.start()
        self.requester.start()
        
