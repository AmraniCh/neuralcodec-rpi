import os
from pprint import pprint
from audio_io import get_audio_info

def calc_bitrate(path):
    # for a compressed audio we can use the formula 
    # bitrate = size (bits) / duration (seconds) / 1000
    size = get_file_size(path) * 8
    duration = get_audio_info(path)['duration']
    print("duration: ", duration)
    return (size / duration) / 1000

def get_file_size(path):
    return os.path.getsize(path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 0:
        sound_file = sys.argv[1]

        print("bitrate (Kbps) ", calc_bitrate(sound_file ))