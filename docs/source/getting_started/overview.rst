********
Overview
********

Solves real-time map-reduce video streaming problem, but can also be used for general-purpose video streaming.

5 line webcam P2P streaming example. Stream is bound to port 5555.

.. code-block:: Python

    import pystreaming, cv2
    cap = cv2.VideoCapture(0)
    with pystreaming.Streamer("tcp://*:5555") as stream:
        while True:
            stream.send(cap.read()[1])


5 line stream P2P receiving example. Receives a video stream from localhost port 5555 and displays it using OpenCV.

.. code-block:: Python

    from pystreaming import Receiver, collate, display
    import zmq
    with Receiver("tcp://localhost:5555") as stream:
        for _, data in buffer(0.5, [stream.handler]):
            display(data['arr'])