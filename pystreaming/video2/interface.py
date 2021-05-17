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
        flags (int, optional): [description]. Defaults to 0.

    Returns:
        list: Expected items, in the order: [arr, buf, meta, ftime, fno]
    """
    out = []
    if arr:
        md = socket.recv_json(flags=flags)
        msg = socket.recv(copy=False, flags=flags)
        arrbuf = memoryview(msg)
        out.append(np.frombuffer(arrbuf, dtype=md["dtype"]).reshape(md["shape"]))
    if buf:
        out.append(socket.recv(copy=False, flags=flags))
    out.append(socket.recv_pyobj(flags=flags))  # meta
    out.append(socket.recv_pyobj(flags=flags))  # ftime
    out.append(socket.recv_pyobj(flags=flags))  # fno
    return out
