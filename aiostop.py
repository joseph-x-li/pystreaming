import time, zmq
from pystreaming import Requester, Encoder, Distributor, Decoder, Publisher, Subscriber

def main():
    context = zmq.Context()
    x = Encoder(context)
    x.start()
    time.sleep(1)
    x.stop()
    x = Requester("tcp://127.0.0.1:5555")
    x.start()
    time.sleep(1)
    x.stop()

    time.sleep(1)
    
    
    x = Distributor("tcp://*:5555")
    x.start()
    time.sleep(1)
    x.stop()
    
    x = Decoder(context)
    x.start()
    time.sleep(1)
    x.stop()
    
    x = Publisher("tcp://*:5556")
    x.start()
    time.sleep(1)
    x.stop()
    
    x = Subscriber("tcp://127.0.0.1:5557")
    x.start()
    time.sleep(1)
    x.stop()
    
if __name__ == "__main__":
    main()