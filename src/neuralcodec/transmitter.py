import argparse
import os
import socket
import tempfile

from neuralcodec.common.audio_io import load_audio, save_audio
from neuralcodec.common.codec_registry import codecs


CHUNK_SIZE = 1400


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transmitter audio')
    parser.add_argument('file')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5005)
    parser.add_argument('--codec', default='encodec', choices=['opus', 'codec2', 'encodec', 'soundstream'])
    parser.add_argument('--bitrate', type=float, default=6.0) # 6 kbps to change later, make it not optional

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Audio file not found: {args.file}")
        exit(1)

    file = args.file
    host = args.host
    port = args.port
    codec = codecs[args.codec]
    bitrate = args.bitrate

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((host, port))
    
    audio, sr = load_audio(file)

    tmp_wav = tempfile.mktemp(suffix='.wav')
    tmp_compressed = tempfile.mktemp(suffix=f'.{codec['extension']}')

    save_audio(audio, tmp_wav, sr)

    encoder = codec['encode']
    encoder(tmp_wav, tmp_compressed, bitrate)
    
    with open(tmp_compressed, 'rb') as f:
        compressed_data = f.read()

        # chunking
        for i in range(0, len(compressed_data), CHUNK_SIZE):
            chunk = compressed_data[i:i + CHUNK_SIZE]
            print(f"send chunk: {len(chunk)}")
            sock.send(chunk)

    sock.send(b"END")
    
    os.remove(tmp_compressed)



