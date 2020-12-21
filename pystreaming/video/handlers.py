import cv2
from pystreaming.listlib.circulardict import CircularOrderedDict

# handler (generator): Any object that yields frames.
def display(handler, BGR=True):
    for frame, idx in handler:
        if not BGR:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("pystreaming-display", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
            break


def collate(handler, buffer=10):
    initsize = buffer * 1.2
    collate = CircularOrderedDict(int(initsize))
    for frame, idx in handler:
        if idx == 0:  # Restart collate if stream restart occurs
            collate = CircularOrderedDict(initsize)
        collate.insert_end(idx, frame)
        if len(collate) >= buffer:
            most_recent = min(collate.keys())
            yield collate[most_recent], most_recent
            collate.delete(most_recent)
