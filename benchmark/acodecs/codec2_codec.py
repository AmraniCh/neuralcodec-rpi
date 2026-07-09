import numpy as np
import pycodec2
from neuralcodec.common.audio_io import load_audio, save_audio
import librosa


def encode(source_path, output_path, mode=2400):
    audio_data, sr = load_audio(source_path, target_sr=16000)
    audio_8k = librosa.resample(audio_data, orig_sr=16000, target_sr=8000)
    audio_int16 = (audio_8k * 32767).astype(np.int16)

    codec = pycodec2.Codec2(round(mode * 1000))
    frame_size = codec.samples_per_frame()

    remainder = len(audio_int16) % frame_size
    if remainder != 0:
        padding = frame_size - remainder
        audio_int16 = np.append(audio_int16, np.zeros(padding, dtype=np.int16))

    with open(output_path, 'wb') as f:
        for i in range(0, len(audio_int16), frame_size):
            frame = audio_int16[i:i + frame_size]
            encoded = codec.encode(frame)
            f.write(encoded)


def decode(source_path, output_path, mode=2400):
    codec = pycodec2.Codec2(round(mode * 1000))
    bytes_per_frame = codec.bytes_per_frame()

    with open(source_path, 'rb') as f:
        encoded_data = f.read()

    decoded_frames = []
    for i in range(0, len(encoded_data), bytes_per_frame):
        encoded_frame = encoded_data[i:i + bytes_per_frame]
        decoded = codec.decode(encoded_frame)
        decoded_frames.append(decoded)

    audio_int16 = np.concatenate(decoded_frames)
    audio_float = audio_int16.astype(np.float32) / 32767.0
    audio_16k = librosa.resample(audio_float, orig_sr=8000, target_sr=16000)
    save_audio(audio_16k, output_path, sr=16000)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        source = sys.argv[1]
        output = sys.argv[2]
        mode = int(sys.argv[3])
        encode(source, output, mode)

    elif len(sys.argv) == 3:
        source = sys.argv[1]
        output = sys.argv[2]
        decode(source, output)