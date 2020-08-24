import wave
import scipy.io.wavfile
import sounddevice as sd

AUDIO_FILE = 'doodoo.wav'      # sample rate 16KHz
MASK_AUDIO = 'mask.wav'

def sound_process(snd_q):
    a, audio_array = scipy.io.wavfile.read(AUDIO_FILE)
    try:
        b, mask_array = scipy.io.wavfile.read(MASK_AUDIO)
    except:
        pass
    while True:
        num=snd_q.get()
        if num==0:
            sd.play(audio_array, 16000)
            sd.wait()
        elif num==1:
            try:
                sd.play(mask_array, 44100)
                sd.wait()
            except:
                pass
