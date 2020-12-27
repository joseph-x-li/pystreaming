.. _API:

****
API
****

Basic API Interface
-------------------

.. autosummary::
	:toctree: gen
	:nosignatures: 
	
	pystreaming.video.patterns.Streamer
	pystreaming.video.patterns.Worker
	pystreaming.video.patterns.Collector
    pystreaming.video.handlers.collate
    pystreaming.video.handlers.display


Internal API Interface
----------------------

.. autosummary::
	:toctree: gen
	:nosignatures: 
	
	pystreaming.video.enc.Encoder
	pystreaming.video.dec.Decoder
	pystreaming.video.dist.Distributor
	pystreaming.video.req.Requester
    pystreaming.listlib.circularlist.CircularList
    pystreaming.listlib.circulardict.CircularOrderedDict
