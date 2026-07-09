import socket
import argparse
from neuralcodec.common.codec_registry import codecs
import tempfile
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transmitter audio')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', default=5005)
    parser.add_argument('--codec', default='encodec', choices=['opus', 'codec2', 'encodec', 'soundstream'])
    parser.add_argument('--bitrate', type=float, default=6.0)

    args = parser.parse_args()

    host = args.host
    port = args.port
    codec = codecs[args.codec]
    bitrate = args.bitrate

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
    
    audio_decoded = codec['decode'](tmp_compressed, 'data/received.wav', bitrate)
    
    os.remove(tmp_compressed)

