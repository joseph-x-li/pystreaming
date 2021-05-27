import zmq
import numpy as np


def send(*, socket, fno, ftime, meta, arr=None, buf=None, flags=0):
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
        md = {"dtype": str(arr.dtype), "shape": arr.shape}
        socket.send_json(md, flags=zmq.SNDMORE | flags)
        socket.send(arr, copy=False, flags=zmq.SNDMORE | flags)
    if buf is not None:
        socket.send(buf, copy=False, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(meta, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(ftime, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(fno, flags=flags)


def recv(*, socket, arr=False, buf=False, flags=0):
    """Internal video data receive command.

    Args:
        socket (zmq.Context.socket): Socket through which to receive data.
        arr (bool, optional): Change to True if you expect an arr. Defaults to False.
        buf (bool, optional): Change to True if you expect a byte buffer. Defaults to False.
        flags (int, optional): Zmq flags to execute with (zmq.NOBLOCK). Defaults to 0.

    Returns:
        dict: Expected items, with possible keys: {arr, buf, meta, ftime, fno}.
    """
    out = {}
    if arr:
        md = socket.recv_json(flags=flags)
        msg = socket.recv(copy=False, flags=flags)
        arrbuf = memoryview(msg)
        out["arr"] = np.frombuffer(arrbuf, dtype=md["dtype"]).reshape(md["shape"])
    if buf:
        out["buf"] = socket.recv(copy=False, flags=flags)
    out["meta"] = socket.recv_pyobj(flags=flags)
    out["ftime"] = socket.recv_pyobj(flags=flags)
    out["fno"] = socket.recv_pyobj(flags=flags)
    return out
