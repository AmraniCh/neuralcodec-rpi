from neuralcodec.common.codec_registry import codecs
from neuralcodec.common.audio_io import get_audio_info
from mesure import calc_bitrate, calc_pesq
import matplotlib.pyplot as plt
import os
import time
from pprint import pprint
import pandas as pd

ORIGINAL_AUDIO = "data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac"
OUTPUT_DIR = "data/encoded"

def run(only=None):
    # optional filter: run only the codecs named on the command line
    if only:
        wanted = {name.lower() for name in only}
        selected = {k: v for k, v in codecs.items() if k.lower() in wanted}
        if not selected:
            print(f"Unknown codec(s): {', '.join(only)}. Available: {', '.join(codecs)}")
            return
    else:
        selected = codecs

    all_results_csv = []
    quality_results = {}
    hardware_results = {}
    for codec, props in selected.items():
        bitrates = props['bitrates']

        plot_scale_x = []
        plot_scale_y = []

        hr_plot_scale_x = []
        hr_plot_scale_y = []

        for bitrate in bitrates:
            res = benchmark_codec(codec, bitrate, props)
            all_results_csv.append(res)
            plot_scale_x.append(res['real_bitrate'])
            plot_scale_y.append(res['pesq'])
            hr_plot_scale_x.append(res['real_bitrate'])
            hr_plot_scale_y.append(res['rtf'])

        quality_results[codec] = {
            'x': plot_scale_x,
            'y': plot_scale_y
        }

        hardware_results[codec] = {
            'x': hr_plot_scale_x,
            'y': hr_plot_scale_y
        }

        # keep this for debugging to inspect the actual plot axes values
        # print(plot_scale_x, plot_scale_y, codec)

        plot_data(
            scale_x=plot_scale_x, 
            scale_y=plot_scale_y, 
            label=props['label'], 
            categ='quality', 
            xlabel='Bitrate (kbps)', 
            ylabel='PESQ',
            acceptable_threshold=2 if props["is_neural"] else 3
        )

        plot_data(
            scale_x=hr_plot_scale_x, 
            scale_y=hr_plot_scale_y, 
            label=props['label'], 
            categ='hardware', 
            xlabel='Bitrate (kbps)', 
            ylabel='RTF',
        )

    df = pd.DataFrame(all_results_csv)
    df.to_csv('benchmark/results/results.csv', index=False)
    print(df.to_string(index=False))

    plot_comparison(
        data_dict=quality_results, 
        xlabel='Bitrate (kbps)', 
        ylabel='PESQ',
        categ='quality', 
        title='Codec Comparison (Quality)'
    )

    plot_comparison(
        data_dict=hardware_results, 
        xlabel='Bitrate (kbps)', 
        ylabel='RTF',
        categ='hardware', 
        title='Codec Comparison (Hardware)'
    )

def benchmark_codec(codec_name, bitrate, props):
    extension, encoder, decoder = props['extension'], props['encode'], props['decode']

    encoding_path = f"{OUTPUT_DIR}/{codec_name}"
    if not os.path.exists(encoding_path):
        os.mkdir(encoding_path)

    compressed_path = f"{encoding_path}/{codec_name}_{bitrate}.{extension}"
    decoded_path = f"{encoding_path}/{codec_name}_{bitrate}_decoded.wav"

    encdec_start_time = time.time()

    encoder(ORIGINAL_AUDIO, compressed_path, bitrate)
    
    # passing bitrate to the decoder also, because some decoders
    # like codec2 do not produce headers with the compressed output
    decoder(compressed_path, decoded_path, bitrate)

    # used original audio to bypass some encoders does not produce
    # a playable format for computing the audio duration (like in the codec2 case)
    duration = get_audio_info(ORIGINAL_AUDIO)['duration']

    encdec_time = time.time() - encdec_start_time
    rtf = encdec_time / duration
    compression_bitrate = calc_bitrate(compressed_path, duration)
    pesq_score = calc_pesq(ORIGINAL_AUDIO, decoded_path)

    return {
        'codec_name': codec_name,
        'target_bitrate': bitrate,
        'real_bitrate': compression_bitrate,
        'pesq': pesq_score,
        'rtf': rtf
    }


def plot_data(scale_x, scale_y, label, categ, xlabel, ylabel, acceptable_threshold = None):
    plt.figure()
    plt.plot(scale_x, scale_y, label=label, marker="o")

    if acceptable_threshold:
        plt.axhline(y=acceptable_threshold, color='red', linestyle='--', alpha=0.5, label='Acceptable threshold')
    
    if categ == 'hardware':
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Real-time threshold')

    if categ == 'quality':
        for x, y in zip(scale_x, scale_y):
            plt.annotate(
                f"({x:.1f}, {y:.2f})",
                (x, y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=7
            )

    if categ == 'hardware':
        min_rtf, max_rtf = min(scale_y), max(scale_y)
        plt.text(0.95, 0.85, 
            f'RTF range: {min_rtf:.2f} – {max_rtf:.2f}',
            transform=plt.gca().transAxes,
            ha='right', va='top',
            fontsize=9, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(f"benchmark/results/{categ}/{label}.png")


def plot_comparison(data_dict, xlabel, ylabel, title, categ):
    plt.clf()

    for codec, data in data_dict.items():
        plt.plot(data['x'], data['y'], label=codec, marker="o")
        
    if categ == 'quality':
        plt.axhline(y=3.0, color='green', linestyle='--', alpha=0.5, 
                    label='Acceptable Threshold (Traditional)')
        plt.axhline(y=2.0, color='purple', linestyle=':', alpha=0.7, 
                    label='Acceptable Threshold (Neural)')

    
    if categ == 'hardware':
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Real-time threshold')

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(f"benchmark/results/{categ}/comparison.png")


if __name__ == '__main__':
    import sys
    run(sys.argv[1:] or None)