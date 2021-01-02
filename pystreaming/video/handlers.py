import cv2
from pystreaming.listlib.circulardict import CircularOrderedDict


def display(handler, BGR=True, getter=None):
    """Yield frames from a generator and display using OpenCV.

    Args:
        handler (generator): Generator that yields data.
        BGR (bool, optional): False if frame is RGB format. Defaults to True.
        getter (function, optional): Returns the frame from the return type of handler. Defaults to None.
    """
    for data in handler:
        frame = data if getter is None else getter(data)
        if not BGR:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("pystreaming-display", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
            break


def collate(handler, buffer=10, getter=None):
    """Reorder frames that are mixed in transit.

    Args:
        handler (generator): Generator that yields data.
        buffer (int, optional): Size of collate buffer. Defaults to 10.
        getter (function, optional): Returns (frame, meta, idx) from the return type of handler.
            Defaults to None, which acts as an identity.

    Yields:
        tuple(np.ndarray, int): (frame, meta, idx)
    """
    initsize = int(buffer * 1.2)
    collate = CircularOrderedDict(initsize)
    for data in handler:
        frame, meta, idx = data if getter is None else getter(data)
        if idx == 0:  # Restart collate if stream restart occurs
            collate = CircularOrderedDict(initsize)
        collate.insert_end(idx, (frame, meta))
        if len(collate) >= buffer:
            most_recent = min(collate.keys())
            yield collate[most_recent] + (most_recent,)
            collate.delete(most_recent)
