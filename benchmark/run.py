from acodecs.opus_codec import encode as opus_encode, decode as opus_decode
from acodecs.codec2_codec import encode as codec2_encode, decode as codec2_decode
from audio_io import get_audio_info
from mesure import calc_bitrate, calc_pesq
import matplotlib.pyplot as plt
import os

ORIGINAL_AUDIO = "data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac"
OUTPUT_DIR = "data/encoded"
CODECS = ["opus", "codec2"]
BITRATES = {
    "opus": [6, 16, 32, 64],
    "codec2": [1.2, 1.3, 1.6, 2.4, 3.2],
}


def start(codec_name):
    bitrates = BITRATES[codec_name]
    plot_scale_x = []
    plot_scale_y = []
    for bitrate in bitrates:
        res = benchmark_codec(codec_name, bitrate)
        plot_scale_x.append(res['real_bitrate'])
        plot_scale_y.append(res['pesq'])
    plot_data(plot_scale_x, plot_scale_y, codec_name)


def benchmark_codec(codec_name, bitrate):
    compressed_path = f"{OUTPUT_DIR}/{codec_name}_{bitrate}.opus"
    decoded_path = f"{OUTPUT_DIR}/{codec_name}_{bitrate}_decoded.wav"

    match codec_name:
        case "opus":
            opus_encode(ORIGINAL_AUDIO, compressed_path, bitrate)
            opus_decode(compressed_path, decoded_path)
        case "codec2":
            compressed_path = f"{OUTPUT_DIR}/codec2_{bitrate}.c2"
            codec2_encode(ORIGINAL_AUDIO, compressed_path, bitrate)
            codec2_decode(compressed_path, decoded_path, bitrate)
        case _:
            raise ValueError(f"Unknown codec: {codec_name}")

    # used original audio to bypass some encoders does not produce
    # a playable format for computing the audio duration (like in the codec2 case)
    duration = get_audio_info(ORIGINAL_AUDIO)['duration']
    compression_bitrate = calc_bitrate(compressed_path, duration)

    pesq_score = calc_pesq(ORIGINAL_AUDIO, decoded_path)

    return {
        'codec_name': codec_name,
        'target_bitrate': bitrate,
        'real_bitrate': compression_bitrate,
        'pesq': pesq_score
    }

def plot_data(scale_x, scale_y, label):
    plt.plot(scale_x, scale_y, label=label)
    plt.xlabel('Bitrate (kbps)')
    plt.ylabel('PESQ')
    plt.legend()
    plt.savefig(f"benchmark/results/benchmark_{label}_results.png")

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        codec = sys.argv[1]
        start(codec)