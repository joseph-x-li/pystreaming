from pystreaming import (
    EncoderDevice,
    DistributorDevice,
    DecoderDevice,
    RequesterDevice,
    PublisherDevice,
    SubscriberDevice,
)
import zmq
import uuid
from zmq.devices import ProcessDevice

from . import interface as intf


class Streamer:
    def __init__(self, context, endpoint, tracks=None, nproc=2, mapreduce=False):
        """Video streamer with P2P and Map-Reduce functionality.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of stream endpoint.
            tracks (list[str], optional): Video stream tracks. Defaults to None.
            nproc (int, optional): Number of processes devoted to encoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        self.encoder = EncoderDevice(context, nproc, seed)
        if mapreduce:
            self.distributor = DistributorDevice(
                ["none"] if tracks is None else tracks, endpoint, seed
            )
        else:
            self.distributor = PublisherDevice(endpoint, seed)
        self.started = False

    def start(self):
        """Start internal pystreaming devices."""
        self.encoder.start()
        self.distributor.start()
        self.started = True

    def stop(self):
        """Cleanup and stop interal pystreaming objects."""
        self.started = False
        self.encoder.stop()
        self.distributor.stop()

    def send(self, frame):
        """Send a video frame into the stream.

        Args:
            frame (np.ndarray): Video frame
        """
        if not self.started:
            raise RuntimeError("Start the Streamer before sending frames")
        self.encoder.send(frame)

    def testcard(self, card, animated=False):
        """Display a testcard or a test image. Automatically starts the device
        if not already started. This method is blocking.

        Args:
            card (int): One of
                pystreaming.TEST_S
                pystreaming.TEST_M
                pystreaming.TEST_L
                pystreaming.IMAG_S
                pystreaming.IMAG_M
                pystreaming.IMAG_L
            animated (bool, optional): Set True to make image rotate. Defaults to False.
        """
        import cv2
        import numpy as np
        from itertools import count
        import time
        from pystreaming import loadimage

        self.start()
        testimage = loadimage(card)
        if animated:
            storage = []
            for ang in range(360):
                storage.append(
                    cv2.cvtColor(np.asarray(testimage.rotate(ang)), cv2.COLOR_RGB2BGR)
                )
        else:
            storage = np.asarray(testimage)
        for i in count():
            print(i)
            self.send(storage[i % 360] if animated else storage)
            time.sleep(1 / 30)


class Worker:
    def __init__(self, context, source, drain, track="none", reqthread=3, decproc=2):
        """Map pattern in the Map-Reduce streaming pattern.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            source (str): Descriptor of map-enabled stream.
            drain (str): Descriptor of Collector.
            track (str, optional): Video stream track name. Defaults to "none".
            reqthread (int, optional): Number of request threads. Defaults to 3.
            decproc (int, optional): Number of decoder processes. Defaults to 2.
        """
        seed = uuid.uuid1().hex
        self.requester = RequesterDevice(source, track, reqthread, seed)
        self.decoder = DecoderDevice(context, decproc, seed, fwdbuf=True)
        self.context = context
        self.drain = None

    def run(self, func):
        """Run map-enabled worker. This method blocks.

        Args:
            func (function): Stream-mapped function.
        """
        if self.drain is None:
            self.drain = self.context.socket(zmq.PUSH)
            self.drain.setsockopt(zmq.SNDHWM, self.outhwm)
            self.drain.connect(self.drain)
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
    def __init__(self, context, endpoint, nproc=2, mapreduce=False):
        """Collect frames from  video stream.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of collection endpoint.
            nproc (int, optional): Number of processes devoted to decoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        self.mapreduce = mapreduce
        self.startedonce = False
        if mapreduce:
            # https://het.as.utexas.edu/HET/Software/pyZMQ/api/zmq.devices.html#zmq.devices.ProcessDevice
            self.device = ProcessDevice(zmq.STREAMER, zmq.PULL, zmq.PUSH)
            self.device.setsockopt_in(zmq.RCVHWM, 10)
            self.device.setsockopt_out(zmq.SNDHWM, 10)
            self.device.bind_in(endpoint)
            self.device.bind_out("ipc:///tmp/decin" + seed)
        else:
            self.device = SubscriberDevice(endpoint, seed)
        self.decoder = DecoderDevice(context, nproc, seed)
        self.started = False

    def start(self):
        """Start internal pystreaming objects."""
        self.started = True
        self.decoder.start()
        if self.startedonce and self.mapreduce:
            return
        self.device.start()
        self.startedonce = True

    def handler(self):
        """Returns a handler that is used for future data handling.

        Returns:
            generator: Generator that yields [arr, meta, ftime, fno]
        """
        self.start()
        return self.decoder.handler()

    @property
    def recv(self):
        return self.decoder.recv

    def stop(self):
        """Cleanup and stop interal pystreaming objects."""
        if not self.mapreduce:
            self.device.stop()
        self.decoder.stop()
        self.started = False
