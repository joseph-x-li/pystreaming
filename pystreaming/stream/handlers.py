import time
from collections import OrderedDict, deque
from collections.abc import Callable, Generator
from typing import Any

import numpy as np


def buffer(
    bufferlen: float,
    handlers: dict[str, Callable[[], Generator[dict[str, Any] | None, None, None]]],
) -> Generator[tuple[str, dict[str, Any]], None, None]:
    """Buffer and reorder incoming packets of data.

    Args:
        bufferlen ([type]): Length of buffer, in seconds.
        handlers (dict): Dictionary of str: generator.
            The key is a stream name, the value is an unprimed generator.

    Yields:
        tuple(str, data): str is stream name, data is data packet from corresponding handler.
    """
    assert isinstance(handlers, dict)
    # Prime the generators by calling them
    primed_handlers: dict[str, Generator[dict[str, Any] | None, None, None]] = {
        k: handlers[k]() for k in handlers
    }
    buffers = {k: OrderedDict() for k in primed_handlers}
    tdelta: float | None = None
    while True:
        for k, handler in primed_handlers.items():
            data = next(handler)
            buffer = buffers[k]

            if data is None:
                # handler miss
                time.sleep(0.001)
            else:
                # handler hit
                ftime = data["ftime"]
                if tdelta is None:
                    tdelta = ftime - time.time()

                # skip if packet is stale
                if tdelta is not None and ftime < time.time() + tdelta - bufferlen:
                    continue

                # packet is fresh. write data to buffer
                buffer[ftime] = data

            if buffer.keys():  # if buffer is not empty
                mint = min(buffer.keys())
                # yield data if time is right
                if tdelta is not None and mint < time.time() + tdelta - bufferlen:
                    yield (k, buffer.pop(mint))


def display(frame: np.ndarray, BGR: bool = True) -> None:
    """Display a frame using OpenCV.

    Press [ESC] to stop.

    Args:
        frame (np.ndarray): Frame must have dtype uint8.
        BGR (bool, optional): Is frame in BGR format (This is OpenCV format). Defaults to True.

    Raises:
        KeyboardInterrupt: Raised when [ESC] is pressed. Catch this exception to gracefully exit the stream.
    """
    import cv2  # type: ignore[import-untyped]

    if not BGR:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("pystreaming-display", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # esc pressed
        raise KeyboardInterrupt("StopStream")


def dispfps(
    handler: Generator[dict[str, Any], None, None],
    n: int = 100,
    write: bool = False,
) -> Generator[dict[str, Any], None, None]:
    """Average iterations per second over last n iterations.

    Args:
        handler (generator): Generator that yields data.
        n (int, optional): Number of iterations to average over. Defaults to 100.
        write (bool, optional): Set to true to write FPS to data['arr'] instead of console,
            assuming it is a video frame. Defaults to False.

    Yields:
        pyobj: Forwards data from handler
    """
    if write:
        import cv2  # type: ignore[import-untyped]
    times = deque()
    for data in handler:
        end = time.time()
        times.append(end)
        if len(times) > n:
            diff = end - times.popleft()
            if write:
                data["arr"] = cv2.putText(
                    data["arr"],
                    f"FPS: {(n / diff):.3f}",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                    cv2.LINE_4,
                )
            else:
                print(f"\rFPS: {(n / diff):.3f}", end="")
        yield data
