import argparse
import os
import socket
from neuralcodec.common.audio_io import load_audio
import numpy as np

CHUNK_SIZE = 960


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transmitter audio')
    parser.add_argument('file')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5005)

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Audio file not found: {args.file}")
        exit(1)

    host = args.host
    port = args.port
    file = args.file

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((host, port))
    
    audio, sr = load_audio(file)

    # chunking
    for i in range(0, len(audio), CHUNK_SIZE):
        chunk = audio[i:i + CHUNK_SIZE]
        print(f"send chunk: {len(chunk)}")
        sock.send(chunk.astype(np.float32).tobytes())

    sock.send(b"END")



