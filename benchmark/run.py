from acodecs.opus_codec import encode as opus_encode, decode as opus_decode
from mesure import calc_bitrate, calc_pesq
import matplotlib.pyplot as plt

ORIGINAL_AUDIO = "data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac"
OUTPUT_DIR = "data/encoded"
CODECS = ["opus"]
BITRATES = {
    "opus": [6, 16, 32, 64],
}


def start(codec_name):
    bitrates = BITRATES[codec_name]
    plot_scale_x = []
    plot_scale_y = []
    for bitrate in bitrates:
        res = benchmark_codec(codec_name, bitrate)
        plot_scale_x.append(res['real_bitrate'])
        plot_scale_y.append(res['pesq'])
    plot_data(plot_scale_x, plot_scale_y, 'Opus')
    


def benchmark_codec(codec_name, bitrate):
    compressed_path = f"{OUTPUT_DIR}/{codec_name}_{bitrate}.opus"
    decoded_path = f"{OUTPUT_DIR}/{codec_name}_{bitrate}_decoded.wav"
    
    match codec_name:
        case "opus":
            opus_encode(ORIGINAL_AUDIO, compressed_path, bitrate)
            opus_decode(compressed_path, decoded_path)
        case _:
            raise ValueError(f"Unknown codec: {codec_name}")
    
    compression_bitrate = calc_bitrate(compressed_path)
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