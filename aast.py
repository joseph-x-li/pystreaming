# NOTE: (FOR MACS) DO NOT RUN IN VSCODE; ONLY RUN IN TERMINAL DUE TO DUMBASS PERMISSION SHIT
import sounddevice as sd
import soundfile as sf
# from scipy.io.wavfile import write

# fs = 44100  # Sample rate
# seconds = 10  # Duration of recording

# myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
# sd.wait()  # Wait until recording is finished
# write('output2.wav', fs, myrecording)  # Save as WAV file +

def readplay():
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
    
if __name__ == "__main__":
    readplay()