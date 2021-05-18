# NOTE: (FOR MACS) DO NOT RUN IN VSCODE; ONLY RUN IN TERMINAL DUE TO DUMBASS PERMISSION SHIT
import sounddevice as sd
# from scipy.io.wavfile import write

# fs = 44100  # Sample rate
# seconds = 10  # Duration of recording

# myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
# sd.wait()  # Wait until recording is finished
# write('output2.wav', fs, myrecording)  # Save as WAV file +

def readplay():
    import soundfile as sf
    filename = "test.wav"
    data, fs = sf.read(filename, dtype='float32')