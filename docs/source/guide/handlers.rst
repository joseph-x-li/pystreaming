**************
Using Handlers
**************


When receiving a stream, pystreaming utilizes generators to hand computation between different stream handlers.

The collector handler is used to access frames decoded in the Decoder.
If the handler was created with M-R enabled, it yields [arr, meta, idx].
If the handler was created with M-R disabled, it yields [arr, idx].

The collate handler is used to sort frames in chronological order. It is suggested to place this immediately after the decoder handler.

The display handler takes a frame and displays it in a OpenCV window.

Getters are used to handle different argument types between the handlers. A common example is using a getter for the display handler. 

You can define a custom handler for your own usage (e.g, drawing boxes for object detection).
