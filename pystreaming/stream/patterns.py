import contextlib
import uuid
from typing import Any

import numpy as np
import zmq

from ..stream import interface as intf
from ..video.collect import CollectDevice
from ..video.dec import DecoderDevice
from ..video.dist import DistributorDevice
from ..video.enc import EncoderDevice
from ..video.pub import PublisherDevice
from ..video.req import RequesterDevice
from ..video.sub import SubscriberDevice
from . import (
    DEGREES_IN_CIRCLE,
    TESTCARD_ANGLE_STEP,
    TESTCARD_FPS,
    WORKER_HWM,
)


class Streamer:
    def __init__(
        self,
        endpoint: str,
        tracks: list[str] | None = None,
        nproc: int = 2,
        mapreduce: bool = False,
    ) -> None:
        """Video streamer with P2P and Map-Reduce functionality.

        Args:
            endpoint (str): Descriptor of video stream endpoint.
            tracks (list[str], optional): Video stream tracks. Defaults to None which is ["none"].
            nproc (int, optional): Number of processes devoted to encoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        if tracks is None:
            tracks = ["none"]

        self.encoder = EncoderDevice(nproc, seed)
        if mapreduce:
            self.distributor = DistributorDevice(tracks, endpoint, seed)
        else:
            self.distributor = PublisherDevice(endpoint, seed)
        self.started: bool = False

    def start(self) -> None:
        """Start internal pystreaming devices."""
        self.encoder.start()
        self.distributor.start()
        self.started = True

    def stop(self) -> None:
        """Cleanup and stop internal pystreaming objects."""
        self.encoder.stop()
        self.distributor.stop()
        self.started = False

    def send(self, frame: np.ndarray) -> None:
        """Send a video frame into the stream.

        Args:
            frame (np.ndarray): Video frame
        """
        if not self.started:
            raise RuntimeError("Start the Streamer before sending frames")
        self.encoder.send(frame)

    def __enter__(self) -> "Streamer":
        self.start()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: Any | None,
    ) -> None:
        self.stop()

    def testcard(self, card: int, animated: bool = False) -> None:
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
        import time
        from itertools import count

        import cv2  # type: ignore[import-untyped]
        import numpy as np

        from pystreaming import loadimage

        self.start()
        testimage = loadimage(card)
        if animated:
            storage = []
            for ang in range(0, DEGREES_IN_CIRCLE, TESTCARD_ANGLE_STEP):
                storage.append(cv2.cvtColor(np.asarray(testimage.rotate(ang)), cv2.COLOR_RGB2BGR))
        else:
            storage: np.ndarray = np.asarray(testimage)
        for i in count():
            print(i)
            frame = storage[i % DEGREES_IN_CIRCLE] if animated else storage
            self.send(frame if isinstance(frame, np.ndarray) else np.asarray(frame))
            time.sleep(1 / TESTCARD_FPS)


class Worker:
    def __init__(self, source, drain, track="none", reqthread=3, decproc=2):
        """Worker in the Map-Reduce streaming pattern.

        Args:
            source (str): Descriptor of Streamer.
            drain (str): Descriptor of Receiver.
            track (str, optional): Video stream track name. Defaults to "none".
            reqthread (int, optional): Number of request threads. Defaults to 3.
            decproc (int, optional): Number of decoder processes. Defaults to 2.
        """
        seed = uuid.uuid1().hex
        self.requester = RequesterDevice(source, track, reqthread, seed)
        self.decoder = DecoderDevice(decproc, seed, fwdbuf=True)

        self.drain: zmq.Socket | None = zmq.Context.instance().socket(zmq.PUSH)
        self.drain.setsockopt(zmq.SNDHWM, WORKER_HWM)
        self.drain.connect(drain)

    def start(self):
        """Start internal pystreaming devices."""
        self.requester.start()
        self.decoder.start()
        self.started = True

    def stop(self) -> None:
        """Cleanup and stop internal pystreaming objects."""
        if hasattr(self, "drain") and self.drain:
            with contextlib.suppress(Exception):
                self.drain.close(linger=0)
            self.drain = None
        self.requester.stop()
        self.decoder.stop()
        self.started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    @property
    def handler(self) -> Any:  # Returns callable that returns Generator
        """Returns a handler that is used for worker data handling.

        Returns:
            callable: Callable that takes timeout and returns Generator yielding dicts with keys {arr, buf, meta, ftime, fno}.
        """
        return self.decoder.handler

    def send(self, data: intf.RecvData) -> None:
        """Send processed data to the drain endpoint.

        Args:
            data (RecvData): Data structure with fields {buf, meta, ftime, fno}.
                The 'arr' field should not be present (will be ignored if present).
        """
        if self.drain is None:
            return  # Device has been stopped
        with contextlib.suppress(zmq.Again):
            intf.send(
                socket=self.drain,
                fno=data.fno,
                ftime=data.ftime,
                meta=data.meta,
                buf=data.buf,
                flags=zmq.NOBLOCK,
            )


class Receiver:
    def __init__(self, endpoint, nproc=2, mapreduce=False):
        """Receiver frames from a video stream.

        Args:
            endpoint (str): Descriptor of collection endpoint.
            nproc (int, optional): Number of processes devoted to decoding. Defaults to 2.
            mapreduce (bool, optional): Enable Map-Reduce streaming pattern. Defaults to False.
        """
        seed = uuid.uuid1().hex
        self.mapreduce = mapreduce
        self.startedonce = False
        if mapreduce:
            self.receive = CollectDevice(endpoint, seed)
        else:
            self.receive = SubscriberDevice(endpoint, seed)
        self.decoder = DecoderDevice(nproc, seed)
        self.started = False

    def start(self):
        """Start internal pystreaming objects."""
        self.decoder.start()
        self.receive.start()
        self.started = True

    def stop(self):
        """Cleanup and stop internal pystreaming objects."""
        self.receive.stop()
        self.decoder.stop()
        self.started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    @property
    def handler(self):
        """Returns a handler that is used for future data handling.

        Returns:
            generator: Generator that yields dicts with keys {arr, meta, ftime, fno}.
        """
        return self.decoder.handler
