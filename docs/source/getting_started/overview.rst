********
Overview
********

Solves real-time map-reduce video streaming problem, but can also be used for general-purpose video streaming.

5 line webcam P2P streaming example. Stream is bound to port 5555.

.. code-block:: Python

    import pystreaming, cv2, zmq
    stream, cap = pystreaming.Streamer(zmq.Context(), "tcp://*:5555"), cv2.VideoCapture(0)
    stream.start()
    while True:
        stream.send(cap.read()[1])


4 line stream P2P receiving example. Receives a video stream from localhost port 5555 and displays it using OpenCV.

.. code-block:: Python

    from pystreaming import Collector, collate, display
    import zmq
    stream = Collector(zmq.Context(), "tcp://127.0.0.1:5555")
    display(collate(stream.handler(), getter=lambda x : x[0], None, x[1]), getter=lambda x : x[0])