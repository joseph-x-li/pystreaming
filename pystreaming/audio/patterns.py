import zmq
import time
import pystreaming.video2.interface as intf
from . import STR_HWM, RCV_HWM


class AudioStreamer:
    def __init__(self, context, endpoint):
        """Audio streamer.

        Binds to a zmq PUB socket.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of stream publishing endpoint.
        """
        self.socket = context.Socket(zmq.PUB)
        self.socket.bind(endpoint)
        self.socket.setsockopt(zmq.SNDHWM, STR_HWM)
        self.endpoint = endpoint
        self.fno = 0

    def send(self, buf):
        """Send a buffer of audio.

        Args:
            buf (bytes): A segment of audio buffer
        """
        try:
            intf.send(
                socket=self.socket,
                fno=self.fno,
                ftime=time.time(),
                buf=buf,
                flags=zmq.NOBLOCK,
            )
        except zmq.error.Again:
            pass
        self.fno += 1

    def __repr__(self):
        rpr = "-----AudioStreamer-----\n"
        rpr += f"{'OUT': <8}{self.endpoint}\n"
        rpr += f"{'HWM': <8}({STR_HWM} >"
        return rpr


class AudioReceiver:
    def __init__(self, context, endpoint):
        """Audio receiver.

        Connects using a zmq SUB socket.

        Args:
            context (zmq.Context): Zmq context of calling thread.
            endpoint (str): Descriptor of stream publishing endpoint.
        """
        self.socket = context.Socket(zmq.SUB)
        self.socket.setsockopt(zmq.RCVHWM, RCV_HWM)
        self.socket.connect(endpoint)
        self.socket.subscribe("")
        self.endpoint = endpoint

    def recv(self, timeout=60_000):
        """Receive a package of data from the audio channel.

        Args:
            timeout (int, optional): Timeout period in milliseconds.
            Set to None to wait forever. Defaults to 60_000.

        Raises:
            TimeoutError: Raised when no messages are received in the timeout period.
        """
        if self.socket.poll(timeout):
            intf.recv(
                socket=self.socket,
                buf=True,
                flags=zmq.NOBLOCK,
            )
        else:
            raise TimeoutError(
                f"No messages were received within the timeout period {timeout}ms"
            )

    def handler(self):
        """Yield a package of data from audio channel.

        Yields:
            list: [buf, meta, ftime, fno].
        """
        while True:
            yield self.recv()

    def __repr__(self):
        rpr = "-----AudioReceiver-----\n"
        rpr += f"{'IN': <8}{self.endpoint}\n"
        rpr += f"{'HWM': <8}> {RCV_HWM})"
        return rpr
