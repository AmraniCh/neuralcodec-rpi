import socket
import argparse
from neuralcodec.common.codec_registry import codecs
import tempfile
import os
import sounddevice as sd
from neuralcodec.common.audio_io import load_audio

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transmitter audio')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', default=5005)
    parser.add_argument('--codec', default='encodec', choices=['opus', 'codec2', 'encodec', 'soundstream'])
    parser.add_argument('--bitrate', type=float, default=6.0) # 6 kbps to change later, make it not optional
    parser.add_argument('--play', action='store_true', help='Play audio on speaker')

    args = parser.parse_args()

    host    = args.host
    port    = args.port
    codec   = codecs[args.codec]
    bitrate = args.bitrate
    play    = args.play

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    chunks = []
    while True:
        data, addr = sock.recvfrom(4096)
        if data == b"END":
            break
        chunks.append(data)
    
    compressed_data = b"".join(chunks)

    tmp_compressed = tempfile.mktemp(suffix=f'.{codec["extension"]}')
    
    with open(tmp_compressed, 'wb') as f:
        f.write(compressed_data)
    
    output_file = 'data/received.wav'

    codec['decode'](tmp_compressed, output_file, bitrate)
    
    audio, sr = load_audio(output_file)

    if play:
        sd.play(audio, sr)
        sd.wait()
    
    os.remove(tmp_compressed)

