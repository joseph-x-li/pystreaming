import numpy as np
import zmq


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
