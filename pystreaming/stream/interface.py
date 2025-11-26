import time
from dataclasses import dataclass
from typing import Any, TypedDict, cast

import numpy as np
import zmq


class ArrayMetadata(TypedDict):
    """Metadata for numpy array transmission."""

    dtype: str
    shape: tuple[int, ...]


@dataclass
class RecvData:
    """Data structure returned by recv function."""

    meta: Any
    ftime: float
    fno: int
    arr: np.ndarray | None = None
    buf: bytes | None = None

    def __post_init__(self) -> None:
        """Validate data structure."""
        # ftime can be 0.0 for error cases (FRAMEMISS, TRACKMISS), so we don't validate it
        pass

    def age(self) -> float:
        """Calculate age of frame in seconds since capture.

        Returns:
            float: Age in seconds.
        """
        return time.time() - self.ftime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for unpacking or serialization.

        Returns:
            dict: Dictionary representation excluding None values.
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}


def send(
    *,
    socket: zmq.Socket,
    fno: int,
    ftime: float,
    meta: Any,
    arr: np.ndarray | None = None,
    buf: bytes | None = None,
    flags: int = 0,
) -> None:
    """Internal video data send command.

    Args:
        socket (zmq.Context.socket): Socket through which to send data.
        fno (int): Frame number.
        ftime (float): Frame timestamp.
        meta (pyobj): Any reasonably small picklable object.
        arr ([type], optional): Numpy array to send. Defaults to None.
        buf (bytes, optional): Byte buffer to send. Defaults to None.
        flags (int, optional): Zmq flags to execute with (zmq.NOBLOCK or zmq.SNDMORE).
            Defaults to 0.
    """
    if arr is not None:
        md: ArrayMetadata = {"dtype": str(arr.dtype), "shape": arr.shape}
        socket.send_json(md, flags=zmq.SNDMORE | flags)
        socket.send(arr, copy=False, flags=zmq.SNDMORE | flags)
    if buf is not None:
        socket.send(buf, copy=False, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(meta, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(ftime, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(fno, flags=flags)


def recv(
    *,
    socket: zmq.Socket,
    arr: bool = False,
    buf: bool = False,
    flags: int = 0,
) -> RecvData:
    """Internal video data receive command.

    Args:
        socket (zmq.Context.socket): Socket through which to receive data.
        arr (bool, optional): Change to True if you expect an arr. Defaults to False.
        buf (bool, optional): Change to True if you expect a byte buffer. Defaults to False.
        flags (int, optional): Zmq flags to execute with (zmq.NOBLOCK). Defaults to 0.

    Returns:
        RecvData: Expected items, with possible fields: {arr, buf, meta, ftime, fno}.
    """
    arr_data: np.ndarray | None = None
    buf_data: bytes | None = None

    if arr:
        md = cast(ArrayMetadata, socket.recv_json(flags=flags))
        msg = socket.recv(copy=False, flags=flags)
        # zmq.Frame has .bytes property that returns bytes
        arrbuf = memoryview(msg.bytes)
        arr_data = np.frombuffer(arrbuf, dtype=md["dtype"]).reshape(md["shape"])
    if buf:
        msg = socket.recv(copy=False, flags=flags)
        # zmq.Frame has .bytes property that returns bytes
        buf_data = msg.bytes

    meta = socket.recv_pyobj(flags=flags)
    ftime = cast(float, socket.recv_pyobj(flags=flags))
    fno = cast(int, socket.recv_pyobj(flags=flags))

    return RecvData(meta=meta, ftime=ftime, fno=fno, arr=arr_data, buf=buf_data)
