************
Peer to Peer
************

On the streaming computer, set up a stream using the Streamer class and a webcam.

.. code-block:: Python

    import pystreaming, cv2, zmq
    cap = cv2.VideoCapture(0)
    stream = pystreaming.Streamer(zmq.Context(), "tcp://*:5555") # Stream to port 5555
    stream.start()
    while True:
        stream.send(cap.read()[1])


This example shows how to receive a stream from some IP and port and display it.

Since collate expects a meta item, we inject ``None`` in the collate getter.

.. code-block:: Python

    from pystreaming import Collector, collate, display
    import zmq
    stream = Collector(zmq.Context(), "tcp://192.168.x.x:5555")
    display(
        collate(
            stream.handler(), 
            getter=lambda x : x[0], None, x[1]
        ), 
        getter=lambda x : x[0]
    )