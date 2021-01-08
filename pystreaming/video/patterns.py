from pystreaming import Encoder, Distributor, Decoder, Requester, Publisher, Subscriber
import pystreaming.video.interface as intf
import pystreaming
import zmq
import uuid
from zmq.devices import ProcessDevice


class Streamer:
    def __init__(self, context, endpoint, procs=2, mapreduce=False):
        """Video streamer with P2P and Map-Reduce functionality.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of stream endpoint.
            procs (int, optional): Number of processes devoted to encoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        self.encoder = Encoder(context, seed=seed, procs=procs)
        if mapreduce:
            self.distributor = Distributor(endpoint, seed=seed)
        else:
            self.distributor = Publisher(endpoint, seed=seed)
        self.started = False

    def start(self):
        """Start internal pystreaming objects.

        Raises:
            RuntimeError: Raised when method is called while Streamer is running.
        """
        if self.started:
            raise RuntimeError("Tried to start a started Streamer")
        self.started = True
        self.encoder.start()
        self.distributor.start()

    def stop(self):
        """Cleanup and stop interal pystreaming objects.

        Raises:
            RuntimeError: Raised when method is called while the Streamer is stopped.
        """
        if not self.started:
            raise RuntimeError("Tried to stop a stopped Streamer")
        self.started = False
        self.encoder.stop()
        self.distributor.stop()

    def send(self, frame):
        """Send a video frame into the stream.

        Args:
            frame (np.ndarray): Video frame

        Raises:
            RuntimeError: Raised when method is called while the Streamer is running.
        """
        if not self.started:
            raise RuntimeError("Start the Streamer before sending frames")
        self.encoder.send(frame)

    def _testsignal(self):
        """Send a test signal through the stream. This method blocks."""
        if not self.started:
            self.start()
        self.encoder._testcard(pystreaming.TEST_M)


class Worker:
    outhwm = 30

    def __init__(self, context, source, drain, track="none", reqprocs=3, decprocs=2):
        """Map pattern in the Map-Reduce streaming pattern.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            source (str): Descriptor of map-enabled stream.
            drain (str): Descriptor of Collector.
            track (str, optional): Video stream track name. Defaults to "none".
            reqprocs (int, optional): Number of request threads. Defaults to 3.
            decprocs (int, optional): Number of decoder processes. Defaults to 2.
        """
        seed = uuid.uuid1().hex
        self.requester = Requester(source, seed=seed, track=track, procs=reqprocs)
        self.decoder = Decoder(context, seed=seed, sndbuf=True, procs=decprocs)
        self.drain = context.socket(zmq.PUSH)
        self.drain.setsockopt(zmq.SNDHWM, self.outhwm)
        self.drain.connect(drain)

    def run(self, func):
        """Run map-enabled worker.

        Args:
            func (function): Stream-mapped function.
        """
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

    def __init__(self, context, endpoint, procs=2, mapreduce=False):
        """Collect frames from  video stream.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of collection endpoint.
            procs (int, optional): Number of processes devoted to decoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        self.mapreduce = mapreduce
        self.startedonce = False
        if mapreduce:
            # https://het.as.utexas.edu/HET/Software/pyZMQ/api/zmq.devices.html#zmq.devices.ProcessDevice
            self.device = ProcessDevice(zmq.STREAMER, zmq.PULL, zmq.PUSH)
            self.device.setsockopt_in(zmq.RCVHWM, self.rcvhwm)
            self.device.setsockopt_out(zmq.SNDHWM, self.outhwm)
            self.device.bind_in(endpoint)
            self.device.bind_out("ipc:///tmp/decin" + seed)
        else:
            self.device = Subscriber(endpoint, seed=seed)

        self.decoder = Decoder(context, procs=procs, seed=seed, rcvmeta=mapreduce)
        self.started = False

    def start(self):
        """Start internal pystreaming objects.

        Raises:
            RuntimeError: Raised when method is called while Collector is running.
        """
        if self.started:
            raise RuntimeError("Tried to start a started Collector")
        self.started = True
        self.decoder.start()
        if self.startedonce and self.mapreduce:
            return
        self.device.start()
        self.startedonce = True

    def handler(self):
        """Returns a handler that is used for future data handling.

        Returns:
            generator: Generator that yields [arr, meta, idx] if map-reduce else [arr, idx]
        """
        if not self.started:
            self.start()
        return self.decoder.handler()

    def stop(self):
        """Cleanup and stop interal pystreaming objects.

        Raises:
            RuntimeError: Raised when method is called while the Collector is stopped.
        """
        if not self.started:
            raise RuntimeError("Tried to stop a stopped Collector")
        self.started = False
        if not self.mapreduce:
            self.device.stop()
        self.decoder.stop()
