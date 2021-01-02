**********
Map-Reduce
**********


A Map-Reduce pattern can be used to process a live video stream across many workers.

On the streaming computer, set up a stream using the Streamer class and a webcam.

Be sure to enable the map-reduce pattern.

.. code-block:: Python

    # Assume this computer has IP 192.168.0.22
    import pystreaming, cv2, zmq
    cap = cv2.VideoCapture(0)
    stream = pystreaming.Streamer(zmq.Context(), "tcp://*:5555", mapreduce=True)
    stream.start()
    while True:
        stream.send(cap.read()[1])


On a collection computer (reduce), set up a Collector class. 

Be sure to enable the map-reduce pattern.

An example custom handler is provided as an example. It simply prints the type of the meta item.

.. code-block:: Python

    # Assume this computer has IP 192.168.0.23
    def customhandler(handler):
        for data in handler:
            print(type(data[1]))
            yield data

    def runner(handler):
        for _ in handler:
            pass

    from pystreaming import Collector, collate, display
    import zmq
    stream = Collector(zmq.Context(), "tcp://*:5556", mapreduce=True)
    runner(customhandler(
        collate(
            stream.handler(), 
        ),
    ))

Worker computers connect to the streaming and the collection servers.

A function is provided as an argument to ``run()``. This function should take a ndarray and return a (reasonably small) picklable python object.

Examples include taking a frame and returning bounding boxes of objects.

This example takes a frame and returns the RGB values of its top left pixel.

.. code-block:: Python

    from pystreaming import Worker
    import zmq
    stream = Worker(
        zmq.Context(), 
        "tcp://192.168.0.22:5555", 
        "tcp://192.168.0.23:5556",
    )
    stream.run(lambda x : tuple(x[0,0]))
