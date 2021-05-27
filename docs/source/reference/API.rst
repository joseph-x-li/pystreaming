.. _API:

****
API
****

Basic API Interface
-------------------

.. autosummary::
	:nosignatures: 
	
	pystreaming.Streamer
	pystreaming.Worker
	pystreaming.Receiver


Internal API Interface
----------------------

.. autosummary::
	:nosignatures: 
	
	pystreaming.video.collect.CollectDevice
	pystreaming.video.enc.EncoderDevice
	pystreaming.video.dec.DecoderDevice
	pystreaming.video.dist.DistributorDevice
	pystreaming.video.req.RequesterDevice
	pystreaming.video.pub.PublisherDevice
	pystreaming.video.sub.SubscriberDevice
    pystreaming.listlib.circularlist.CircularList
    pystreaming.listlib.circulardict.CircularOrderedDict
