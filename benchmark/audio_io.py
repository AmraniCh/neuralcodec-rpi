import soundfile as sf
import librosa
import numpy as np

def load_audio(path, target_sr=16000):
    audio_data, original_sr = sf.read(path)
    
    # if stereo convert to mono by averging channels
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    # resampling
    if target_sr != original_sr:
        audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=target_sr)
    
    return audio_data, target_sr




if __name__ == "__main__":
    import sys

    if len(sys.argv) > 0:
        sound_file = sys.argv[1]

        print(load_audio(sound_file))
 

