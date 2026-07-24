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

def run(machine, only=None):
    results_dir = f"benchmark/results/{machine}"
    os.makedirs(f"{results_dir}/quality", exist_ok=True)
    os.makedirs(f"{results_dir}/hardware", exist_ok=True)

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
    rtf_encode_results = {}
    rtf_decode_results = {}
    for codec, props in selected.items():
        bitrates = props['bitrates']

        plot_scale_x = []
        plot_scale_y = []

        rtf_enc_plot_scale_x = []
        rtf_enc_plot_scale_y = []

        rtf_dec_plot_scale_x = []
        rtf_dec_plot_scale_y = []

        for bitrate in bitrates:
            res = benchmark_codec(codec, bitrate, props)
            all_results_csv.append(res)
            plot_scale_x.append(res['real_bitrate'])
            plot_scale_y.append(res['pesq'])
            rtf_enc_plot_scale_x.append(res['real_bitrate'])
            rtf_enc_plot_scale_y.append(res['rtf_encode'])
            rtf_dec_plot_scale_x.append(res['real_bitrate'])
            rtf_dec_plot_scale_y.append(res['rtf_decode'])

        quality_results[codec] = {
            'x': plot_scale_x,
            'y': plot_scale_y
        }

        rtf_encode_results[codec] = {
            'x': rtf_enc_plot_scale_x,
            'y': rtf_enc_plot_scale_y
        }

        rtf_decode_results[codec] = {
            'x': rtf_dec_plot_scale_x,
            'y': rtf_dec_plot_scale_y
        }

        # keep this for debugging to inspect the actual plot axes values
        # print(plot_scale_x, plot_scale_y, codec)

        plot_data(
            results_dir=results_dir,
            scale_x=plot_scale_x, 
            scale_y=plot_scale_y, 
            label=props['label'], 
            categ='quality', 
            xlabel='Bitrate (kbps)', 
            ylabel='PESQ',
            acceptable_threshold=2 if props["is_neural"] else 3
        )

        plot_data(
            results_dir=results_dir,
            scale_x=rtf_enc_plot_scale_x, 
            scale_y=rtf_enc_plot_scale_y, 
            label=props['label'], 
            categ='hardware', 
            xlabel='Bitrate (kbps)', 
            ylabel='RTF Encode',
        )

        plot_data(
            results_dir=results_dir,
            scale_x=rtf_dec_plot_scale_x, 
            scale_y=rtf_dec_plot_scale_y, 
            label=props['label'], 
            categ='hardware', 
            xlabel='Bitrate (kbps)', 
            ylabel='RTF Decode',
        )

    df = pd.DataFrame(all_results_csv)
    df.to_csv(f'{results_dir}/results.csv', index=False)
    print(df.to_string(index=False))

    plot_comparison(
        results_dir=results_dir,
        data_dict=quality_results, 
        xlabel='Bitrate (kbps)', 
        ylabel='PESQ',
        categ='quality', 
        title='Codec Comparison (Quality)'
    )

    plot_comparison(
        results_dir=results_dir,
        data_dict=rtf_encode_results, 
        xlabel='Bitrate (kbps)', 
        ylabel='RTF Encode',
        categ='hardware', 
        title='Codec Comparison (Hardware)'
    )

    plot_comparison(
        results_dir=results_dir,
        data_dict=rtf_decode_results, 
        xlabel='Bitrate (kbps)', 
        ylabel='RTF Decode',
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

    enc_start_time = time.time()
    encoder(ORIGINAL_AUDIO, compressed_path, bitrate)
    enc_time = time.time() - enc_start_time
    
    dec_start = time.time()
    # passing bitrate to the decoder also, because some decoders
    # like codec2 do not produce headers with the compressed output
    decoder(compressed_path, decoded_path, bitrate)
    dec_time = time.time() - dec_start

    # used original audio to bypass some encoders does not produce
    # a playable format for computing the audio duration (like in the codec2 case)
    duration = get_audio_info(ORIGINAL_AUDIO)['duration']

    encode_rtf = enc_time / duration
    decode_rtf = dec_time / duration
    compression_bitrate = calc_bitrate(compressed_path, duration)
    pesq_score = calc_pesq(ORIGINAL_AUDIO, decoded_path)

    return {
        'codec_name': codec_name,
        'target_bitrate': bitrate,
        'real_bitrate': compression_bitrate,
        'pesq': pesq_score,
        'rtf_encode': encode_rtf,
        'rtf_decode': decode_rtf
    }


def plot_data(results_dir, scale_x, scale_y, label, categ, xlabel, ylabel, acceptable_threshold = None):
    plt.figure()
    plt.plot(scale_x, scale_y, label=label, marker="o")

    if acceptable_threshold:
        plt.axhline(y=acceptable_threshold, color='red', linestyle='--', alpha=0.5, label='Acceptable threshold')
    
    if categ == 'hardware':
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Real-time threshold')

    # if categ == 'quality':
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
    plt.savefig(f"{results_dir}/{categ}/{label}_{ylabel.replace(' ', '_').lower()}.png")


def plot_comparison(results_dir, data_dict, xlabel, ylabel, title, categ):
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
    plt.savefig(f"{results_dir}/{categ}/comparison_{ylabel.replace(' ', '_').lower()}.png")


if __name__ == '__main__':
    import sys
    import platform

    machine = 'pc' if platform.machine() == 'x86_64' else 'pi' 

    run(machine, sys.argv[1:] or None)