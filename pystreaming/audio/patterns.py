import contextlib
import time

import zmq

from ..stream import interface as intf
from . import RCV_HWM, STR_HWM


class AudioStreamer:
    def __init__(self, endpoint):
        """Audio streamer.

        Binds to a zmq PUB socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
        """
        self.socket: zmq.Socket | None = zmq.Context.instance().socket(zmq.PUB)
        self.socket.bind(endpoint)
        self.socket.setsockopt(zmq.SNDHWM, STR_HWM)
        self.endpoint = endpoint
        self.fno = 0

    def close(self) -> None:
        """Close the audio streamer and clean up resources."""
        if hasattr(self, "socket") and self.socket:
            with contextlib.suppress(Exception):
                self.socket.close(linger=0)
            self.socket = None

    def send(self, arr):
        """Send a buffer of audio.

        Args:
            arr (np.ndarray): A segment of audio as a numpy array.
        """
        if self.socket is None:
            return  # Device has been closed
        with contextlib.suppress(zmq.Again):
            intf.send(
                socket=self.socket,
                fno=self.fno,
                ftime=time.time(),
                meta=None,
                arr=arr,
                flags=zmq.NOBLOCK,
            )
        self.fno += 1

    def __repr__(self):
        rpr = "-----AudioStreamer-----\n"
        rpr += f"{'OUT': <8}{self.endpoint}\n"
        rpr += f"{'HWM': <8}(XX > {STR_HWM})"
        return rpr


class AudioReceiver:
    def __init__(self, endpoint):
        """Audio receiver.

        Connects using a zmq SUB socket.

        Args:
            endpoint (str): Descriptor of stream publishing endpoint.
        """
        self.socket: zmq.Socket | None = zmq.Context.instance().socket(zmq.SUB)
        self.socket.setsockopt(zmq.RCVHWM, RCV_HWM)
        self.socket.connect(endpoint)
        self.socket.subscribe("")
        self.endpoint = endpoint

    def close(self) -> None:
        """Close the audio receiver and clean up resources."""
        if hasattr(self, "socket") and self.socket:
            with contextlib.suppress(Exception):
                self.socket.close(linger=0)
            self.socket = None

    def recv(self, timeout):
        """Receive a package of data from the audio channel.

        Args:
            timeout (int): Timeout period in milliseconds.

        Raises:
            TimeoutError: Raised when no messages are received in the timeout period.
        """
        if self.socket is None:
            raise RuntimeError("Audio receiver has been closed")
        if self.socket.poll(timeout):
            return intf.recv(
                socket=self.socket,
                arr=True,
                flags=zmq.NOBLOCK,
            )
        else:
            raise TimeoutError(f"No messages were received within the timeout period {timeout}ms")

    def handler(self, timeout=0):
        """Yield a package of data from audio channel.

        Args:
            timeout (int, optional): Timeout period in milliseconds. Defaults to 0.

        Yields:
            dict: Expected items, with keys: {arr, meta, ftime, fno}.
        """
        while True:
            try:
                yield self.recv(timeout=timeout)
            except TimeoutError:
                yield None

    def __repr__(self):
        rpr = "-----AudioReceiver-----\n"
        rpr += f"{'IN': <8}{self.endpoint}\n"
        rpr += f"{'HWM': <8}> {RCV_HWM})"
        return rpr
