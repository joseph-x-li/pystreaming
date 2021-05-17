# import cv2
# import time
# from collections import deque, OrderedDict
# from pystreaming.listlib.circulardict import CircularOrderedDict
# from pystreaming.listlib.circularlist import CircularList


# class Collator:
#     def __init__(self, buffer, receive_fns):
#         self.receive_fns = receive_fns

#     def handler(self):
#         TDELTA = None
#         tapes = [OrderedDict() for _ in receive_fns]
#         while True:
#             for f in self.receive_fns:
#                 try:
#                     *data, ftime, fno = f(timeout=0)
#                 except TimeoutError:
#                     continue
#                 if TDELTA is None:
#                     TDELTA = ftime - time.time()


# def display(frame, BGR=True):
#     """Display a frame using OpenCV. Must be uint8.

#     Press [ESC] to stop

#     Args:
#         frame ([type]): [description]
#         BGR (bool, optional): [description]. Defaults to True.
#     """


# def display(handler, BGR=True, getter=None):
#     """Yield frames from a generator and display using OpenCV.

#     Args:
#         handler (generator): Generator that yields data.
#         BGR (bool, optional): Set to False if frame is RGB format. Defaults to True.
#         getter (function, optional): Returns the frame from the return type of handler.
#             Defaults to None, which acts as an identity.
#     """
#     for data in handler:
#         frame = data if getter is None else getter(data)
#         if not BGR:
#             frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
#         cv2.imshow("pystreaming-display", frame)
#         if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
#             break


# def collate(handler, buffer=10, getter=None):
#     """Reorder frames that are mixed in transit.

#     Args:
#         handler (generator): Generator that yields data.
#         buffer (int, optional): Size of collate buffer. Defaults to 10.
#         getter (function, optional): Returns (frame, meta, idx) from the return type of handler.
#             Defaults to None, which acts as an identity.

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


# def tape(*handlers):
#     ...
