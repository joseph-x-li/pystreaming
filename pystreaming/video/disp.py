import cv2
import pystreaming.video.interface as intf
import types

# handler (function or generator): Any object that yield or return frames in BGR format.
def display(handler, BGR=True):
    if isinstance(handler, types.GeneratorType):
        for frame in handler:
            if not BGR:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("pystreaming-display", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
                break
    else:
        while True:
            if not BGR:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = handler()
            cv2.imshow("pystreaming-display", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
                break
