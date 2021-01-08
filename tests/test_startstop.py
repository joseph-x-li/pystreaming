import time, zmq
import pystreaming as ps

def teststartstop():
    context = zmq.Context()
    x = ps.Encoder(context)
    x.start()
    time.sleep(1)
    x.stop()
        
    x = ps.Decoder(context)
    x.start()
    time.sleep(1)
    x.stop()

    x = ps.Distributor("tcp://*:5555")
    x.start()
    time.sleep(1)
    x.stop()

    x = ps.Publisher("tcp://*:5556")
    x.start()
    time.sleep(1)
    x.stop()

    x = ps.Requester("tcp://127.0.0.1:5557")
    x.start()
    time.sleep(1)
    x.stop()

    x = ps.Subscriber("tcp://127.0.0.1:5558")
    x.start()
    time.sleep(1)
    x.stop()
    
    x = ps.Streamer(context, "tcp://*5559")
    x.start()
    time.sleep(1)
    x.stop()
    
    x = ps.Streamer(context, "tcp://*5560", mapreduce=True)
    x.start()
    time.sleep(1)
    x.stop()
    
    x = ps.Collector(context, "tcp://127.0.0.1:5561")
    x.start()
    time.sleep(1)
    x.stop()
    
    x = ps.Collector(context, "tcp://127.0.0.1:5562", mapreduce=True)
    x.start()
    time.sleep(1)
    x.stop()