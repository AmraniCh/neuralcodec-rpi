from acodecs.opus_codec import encode as opus_encode, decode as opus_decode
from mesure import calc_bitrate, calc_pesq

ORIGINAL_AUDIO = "data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac"
OUTPUT_DIR = "data/encoded"
CODECS = ["opus"]
BITRATES = {
    "opus": [6, 16, 32, 64],
}


def start(codec_name):
    bitrates = BITRATES[codec_name]
    for bitrate in bitrates:
        res = benchmark_codec(codec_name, bitrate)
        print(res)

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


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        codec = sys.argv[1]
        start(codec)