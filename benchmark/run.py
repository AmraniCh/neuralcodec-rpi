from acodecs.opus_codec import encode as opus_encode, decode as opus_decode
from acodecs.codec2_codec import encode as codec2_encode, decode as codec2_decode
from audio_io import get_audio_info
from mesure import calc_bitrate, calc_pesq
import matplotlib.pyplot as plt 
import os

ORIGINAL_AUDIO = "data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac"
OUTPUT_DIR = "data/encoded"

codecs = {
    "Opus": {
        "bitrates": [6, 12, 16, 32, 64],
        "extension": "opus",
        "encode": opus_encode,
        "decode": opus_decode
    },
    "Codec2": {
        "bitrates": [1.2, 1.3, 1.6, 2.4, 3.2],
        "extension": "c2",
        "encode": codec2_encode,
        "decode": codec2_decode
    }
}


def run():
    all_results = {}
    for codec, props in codecs.items():
        bitrates, extension = props['bitrates'], props['extension']

        plot_scale_x = []
        plot_scale_y = []

        for bitrate in bitrates:
            res = benchmark_codec(codec, bitrate, props)
            plot_scale_x.append(res['real_bitrate'])
            plot_scale_y.append(res['pesq'])

        all_results[codec] = {
            'x': plot_scale_x,
            'y': plot_scale_y
        }

        # keep this for debugging to inspect the actual plot axes values
        # print(plot_scale_x, plot_scale_y, codec)
        
        plot_data(plot_scale_x, plot_scale_y, codec)
    
    plot_comparison(all_results)


def benchmark_codec(codec_name, bitrate, props):
    extension, encoder, decoder = props['extension'], props['encode'], props['decode']

    encoding_path = f"{OUTPUT_DIR}/{codec_name}"
    if not os.path.exists(encoding_path):
       os.mkdir(encoding_path) 

    compressed_path = f"{encoding_path}/{codec_name}_{bitrate}.{extension}"
    decoded_path = f"{encoding_path}/{codec_name}_{bitrate}_decoded.wav"

    encoder(ORIGINAL_AUDIO, compressed_path, bitrate)
    decoder(compressed_path, decoded_path, bitrate) # passing bitrate to the decoder also, because some decoders like codec2 do not produce headers with the compressed output

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
    plt.figure()
    plt.plot(scale_x, scale_y, label=label, marker="o")
    
    plt.axhline(y=3.0, color='red', linestyle='--', alpha=0.5, label='Acceptable threshold')

    for x, y in zip(scale_x, scale_y):
        plt.annotate(
            f"({x:.1f}, {y:.2f})",
            (x, y),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8
        )
    
    plt.xlabel('Bitrate (kbps)')
    plt.ylabel('PESQ')
    plt.legend()
    plt.savefig(f"benchmark/results/{label}.png")

def plot_comparison(all_resules):
    plt.clf()

    for codec, data in all_resules.items():
        plt.plot(data['x'], data['y'], label=codec, marker="o")
    
    plt.axhline(y=3.0, color='red', linestyle='--', alpha=0.5, label='Acceptable threshold')

    plt.xlabel('Bitrate (kbps)')
    plt.ylabel('PESQ')
    plt.title('Codec Comparison')
    plt.legend()
    plt.grid(True)
    plt.savefig("benchmark/results/comparison.png")

if __name__ == '__main__':
    run()