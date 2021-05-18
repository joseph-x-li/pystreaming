# NOTE: (FOR MACS) DO NOT RUN IN VSCODE; ONLY RUN IN TERMINAL DUE TO DUMBASS PERMISSION SHIT
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy

# fs = 44100  # Sample rate
# seconds = 10  # Duration of recording

# myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
# sd.wait()  # Wait until recording is finished
# write('output2.wav', fs, myrecording)  # Save as WAV file +

def playfile():
    filename = "trimmed.wav"
    try:
        data, fs = sf.read(filename, dtype='float32')
        sd.play(data, fs, device=3)
        status = sd.wait()
        if status:
            print('Error during playback: ' + str(status))
    except KeyboardInterrupt:
        print('\nInterrupted by user')
    except Exception as e:
        print(type(e).__name__ + ': ' + str(e))

def recordmic():
    import queue
    q = queue.Queue()

    def callback(indata, frames, time, status):
        q.put(indata.copy())

    device = 0
    device_info = sd.query_devices(device, 'input')
    samplerate = int(device_info['default_samplerate'])

    try:
        with sf.SoundFile("_rec.wav", mode='x', samplerate=samplerate, channels=1) as file:
            with sd.InputStream(samplerate=samplerate, device=device, channels=1, callback=callback):
                print('#' * 80 + 'press Ctrl+C to stop the recording' + '#' * 80)
                while True:
                    file.write(q.get())
    except KeyboardInterrupt:
        print('Recording finished')

def passthrough():
    import queue
    IN = queue.Queue()
    OUT = queue.Queue()

    def callback_in(indata, frames, time, status):
        IN.put(indata.copy())
        
    def callback_out(outdata, frames, time, status):
        outdata[:] = OUT.get()

    indevice = 0
    outdevice = 1
    device_info = sd.query_devices(indevice, 'input')
    samplerate = int(device_info['default_samplerate'])

    blocksize = 256
        
    try:
        with sd.OutputStream(samplerate=samplerate, blocksize=blocksize, device=outdevice, channels=1, callback=callback_out):
            with sd.InputStream(samplerate=samplerate, blocksize=blocksize, device=indevice, channels=1, callback=callback_in):
                print('#' * 80 + 'press Ctrl+C to stop the recording' + '#' * 80)
                while True:
                    OUT.put(IN.get())
    except KeyboardInterrupt:
        print('Passthrough finished')

if __name__ == "__main__":
    # playfile()
    # recordmic()
    # passthrough()