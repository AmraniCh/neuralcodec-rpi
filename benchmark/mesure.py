import os
from pprint import pprint
from audio_io import get_audio_info
from audio_io import load_audio
from pesq import pesq


def calc_bitrate(path):
    # for a compressed audio we can use the formula 
    # bitrate = size (bits) / duration (seconds) / 1000
    size = get_file_size(path) * 8
    duration = get_audio_info(path)['duration']
    return (size / duration) / 1000

# TODO fs and wb are hardcoded
def calc_pesq(original_path, decoded_path):
    original_vector = load_audio(original_path)[0]
    decoded_vector = load_audio(decoded_path)[0]
    return pesq(fs=16000, ref=original_vector, deg=decoded_vector, mode='wb')

def get_file_size(path):
    return os.path.getsize(path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        original_path = sys.argv[1]
        decoded_path = sys.argv[2]
        compressed_path = sys.argv[3]
        print("PESQ score:", calc_pesq(original_path, decoded_path))
        print("Bitrate (kbps) - Original: ", calc_bitrate(original_path))
        print("Bitrate (kbps) - Decoded: ", calc_bitrate(decoded_path))
        print("Bitrate (kbps) - Compressed: ", calc_bitrate(compressed_path))

    elif len(sys.argv) == 2:
        sound_file = sys.argv[1]
        print("Filesize (bytes):", get_file_size(sound_file))
        print("Bitrate (kbps):", calc_bitrate(sound_file))