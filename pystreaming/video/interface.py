import numpy as np
import zmq


def send(socket, idx, arr=None, buf=None, meta=None, flags=0):
    """Send items (idx, arr, buf, meta) through a zmq socket.

    Args:
        socket (zmq.Context.socket): Socket through which to send data.
        idx (int): Index of the sent object.
        arr (np.ndarray, optional): Numpy array to send. Defaults to None.
        buf (bytes, optional): Buffer to send. Defaults to None.
        meta (pyobj, optional): Any reasonably small picklable object. Defaults to None.
        flags (int, optional): [description]. Defaults to 0.
    """
    if not (arr is None):
        md = {"dtype": str(arr.dtype), "shape": arr.shape}
        socket.send_json(md, flags=zmq.SNDMORE | flags)
        socket.send(arr, copy=False, flags=zmq.SNDMORE | flags)
    if not (buf is None):
        socket.send(buf, copy=False, flags=zmq.SNDMORE | flags)
    if not (meta is None):
        socket.send_pyobj(meta, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(idx, flags=flags)


def recv(socket, arr=False, buf=False, meta=False, flags=0):
    """Receive data from a zmq socket.

    Args:
        socket (zmq.Context.socket): Socket through which to receive data.
        arr (bool, optional): Change to True if you expect an arr. Defaults to False.
        buf (bool, optional): Change to True if you expect a buf. Defaults to False.
        meta (bool, optional): Change to True if you expect a meta item. Defaults to False.
        flags (int, optional): Zmq flags to execute with (only zmq.NOBLOCK). Defaults to 0.

    Returns:
        list: Expected items, in the order: [arr, buf, meta, idx]
    """
    out = []
    if arr:
        md = socket.recv_json(flags=flags)
        msg = socket.recv(copy=False, flags=flags)
        arrbuf = memoryview(msg)
        out.append(np.frombuffer(arrbuf, dtype=md["dtype"]).reshape(md["shape"]))
    if buf:
        out.append(socket.recv(copy=False, flags=flags))
    if meta:
        out.append(socket.recv_pyobj(flags=flags))
    out.append(socket.recv_pyobj(flags=flags))
    return out


def send_ndarray_idx(socket, arr, idx, meta=None, flags=0):
    """Send a numpy array and an index.

    Args:
        socket (zmq.Context.socket): Socket through which to send data.
        arr (numpy.ndarray): Numpy array to send.
        idx (int): Index of the sent object.
        flags (int, optional): Zmq flags to execute with
            (only zmq.NOBLOCK or zmq.SNDMORE). Defaults to 0.
    """
    md = dict(
        dtype=str(arr.dtype),
        shape=arr.shape,
        idx=idx,
    )
    socket.send_json(md, flags=zmq.SNDMORE | flags)
    if meta is not None:
        socket.send_pyobj(meta, flags=zmq.SNDMORE | flags)
    socket.send(arr, copy=False, flags=flags)


def recv_ndarray_idx(socket, flags=0):
    """Receive a numpy array and an index.

    Args:
        socket (zmq.Context.socket): Socket through which to receive data.
        flags (int, optional): Zmq flags to execute with
            (only zmq.NOBLOCK). Defaults to 0.

    Returns:
        [tuple(numpy.ndarray, int)]: Numpy array and index received.
    """
    md = socket.recv_json(flags=flags)
    msg = socket.recv(copy=False, flags=flags)
    buf = memoryview(msg)
    A = np.frombuffer(buf, dtype=md["dtype"])
    return A.reshape(md["shape"]), md["idx"]


def send_buf_idx(socket, buf, idx, flags=0):
    """Send a buffer and an index.

    Args:
        socket (zmq.Context.socket): Socket through which to send data.
        buf (bytes): Buffer to send.
        idx (int): Index of the sent object.
        flags (int, optional): Zmq flags to execute with
            (only zmq.NOBLOCK or zmq.SNDMORE). Defaults to 0.
    """
    socket.send(buf, copy=False, flags=zmq.SNDMORE | flags)
    socket.send_pyobj(idx, flags=flags)


def recv_buf_idx(socket, flags=0):
    """Receive a buffer and an index.

    Args:
        socket (zmq.Context.socket): Socket through which to receive data.
        flags (int, optional): Zmq flags to execute with
            (only zmq.NOBLOCK). Defaults to 0.

    Returns:
        [tuple(bytes, int)]: Buffer and index received.
    """
    buf = socket.recv(copy=False, flags=flags)
    idx = socket.recv_pyobj(flags=flags)
    return buf, idx
