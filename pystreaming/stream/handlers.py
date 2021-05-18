import cv2
import time
from collections import OrderedDict


class Buffer:
    def __init__(self, bufferlen, handlers):
        assert isinstance(handlers, dict)
        self.handlers = {k: handlers[k](timeout=0) for k in handlers}
        self.bufferlen = bufferlen
        self.buffers = {k: OrderedDict() for k in handlers}

    def empty(self):
        self.buffers = {k: OrderedDict() for k in self.handlers}

    def handler(self):
        tdelta = None
        while True:
            for k, handler in self.handlers.items():
                data = next(handler)
                buffer = self.buffers[k]

                if data is None:
                    # handler hit
                    time.sleep(0.001)
                else:
                    # handler miss
                    data, meta, ftime, fno = data
                    if tdelta is None:
                        tdelta = ftime - time.time()

                    # skip if packet is stale
                    if ftime < time.time() + tdelta - self.bufferlen:
                        continue

                    # packet is fresh. write data to buffer
                    buffer[ftime] = (data, meta, ftime)

                if buffer.keys():  # if buffer is not empty
                    mint = min(buffer.keys())
                    thshold = time.time() + tdelta - self.bufferlen
                    # yield data if time is right
                    if mint < thshold:
                        yield (k, buffer.pop(mint))


def display(frame, BGR=True):
    """Display a frame using OpenCV. Must be uint8.

    Press [ESC] to stop

    Args:
        frame ([type]): [description]
        BGR (bool, optional): [description]. Defaults to True.
    """
    if not BGR:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("pystreaming-display", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
        raise RuntimeError("StopStream")


#     Yields:
#         tuple(np.ndarray, int): (frame, meta, idx), which is the expected return type of the getter.
#     """
#     initsize = int(buffer + 2)
#     collate = CircularOrderedDict(initsize)
#     for data in handler:
#         frame, meta, idx = data if getter is None else getter(data)
#         if idx == 0:  # Restart collate if stream restart occurs
#             del collate
#             collate = CircularOrderedDict(initsize)
#         collate.insert_end(idx, (frame, meta))
#         if len(collate) >= buffer:
#             most_recent = min(collate.keys())
#             yield collate[most_recent] + (most_recent,)
#             collate.delete(most_recent)


# def dispfps(handler, n=100):
#     """Average iterations per second over last n iterations.

#     Args:
#         handler (generator): Generator that yields data.
#         n (int, optional): Number of iterations to average over. Defaults to 100.

#     Yields:
#         pyobj: Forwards data from handler
#     """
#     times = deque()
#     for data in handler:
#         end = time.time()
#         times.append(end)
#         if len(times) > n:
#             diff = end - times.popleft()
#             print(f"\rFPS: {(n / diff):.3f}", end="")
#         yield data
