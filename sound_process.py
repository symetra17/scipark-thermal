import wave
import scipy.io.wavfile
import sounddevice as sd

AUDIO_FILE = 'doodoo.wav'      # sample rate 16KHz

def sound_process(snd_q):
    a, audio_array = scipy.io.wavfile.read(AUDIO_FILE)
    while True:
        snd_q.get()
        sd.play(audio_array, 16000)
        sd.wait()
