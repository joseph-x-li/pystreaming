********
Overview
********

Solves real-time map-reducce video streaming problem.
Can be used as a easy streaming service as well.
Extremely easy to use.
Videoz

5 line stream example
>>> import pystreaming, cv2, zmq
>>> stream, cap = pystreaming.Streamer(zmq.Context(), "tcp://*5555"), cv2.VideoCapture(0)
>>> stream.start()
>>> while True:
>>>     stream.send(cap.read()[1])


4 line stream recv example
>>> import pystreaming as ps
>>> import zmq
>>> stream = ps.Collector(zmq.Context(), "tcp://127.0.0.1:5555")
>>> ps.display(ps.collate(stream.handler(), getter=lambda x : (x[0], x[3])), getter=lambda x : x[0])