import argparse
import os
import select
import socket

import numpy as np
import soundfile as sf

from neuralcodec.common.codec_registry import codecs

try:
    import sounddevice as sd
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False

SAMPLE_RATE = 16000
TMP_DIR = "/dev/shm"


def get_latest_chunk(sock):
    """Block for the first packet, then drain the socket and return only
    the newest complete chunk, discarding any older backlog."""
    latest = None
    chunks = []
    while True:
        timeout = None if (latest is None and not chunks) else 0.0
        ready, _, _ = select.select([sock], [], [], timeout)
        if not ready:
            if latest is not None:
                return latest      
            continue 
        data, _ = sock.recvfrom(4096)
        if data.startswith(b"END"):
            latest = b"".join(chunks) 
            chunks = []
        else:
            chunks.append(data)


def main():
    parser = argparse.ArgumentParser(description='Live receiver')
    parser.add_argument('--output', default='data/received.wav')
    parser.add_argument('--port', type=int, default=5005)
    parser.add_argument('--codec', default='soundstream', choices=list(codecs.keys()))
    parser.add_argument('--bitrate', type=float, default=3.2)
    parser.add_argument('--play', action='store_true')
    args = parser.parse_args()

    codec_info = codecs[args.codec]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    sock.setblocking(False)

    print(f"Codec: {codec_info['label']} @ {args.bitrate} kbps")
    print(f"Listening on port {args.port}")
    print("Ctrl+C to stop\n")

    ext = codec_info["extension"]
    compressed_path = os.path.join(TMP_DIR, f"rx_chunk.{ext}")
    decoded_path = os.path.join(TMP_DIR, "rx_decoded.wav")
    chunk_num = 0
    all_audio = []

    try:
        while True:
            compressed = get_latest_chunk(sock)
            chunk_num += 1

            with open(compressed_path, "wb") as f:
                f.write(compressed)

            codec_info["decode"](compressed_path, decoded_path, args.bitrate)

            audio, sr = sf.read(decoded_path)
            all_audio.append(audio)

            print(f"[Chunk {chunk_num}] {len(compressed)} bytes")

            if args.play and HAS_AUDIO:
                sd.play(audio, sr)
                sd.wait()

            if os.path.exists(compressed_path):
                os.remove(compressed_path)
            if os.path.exists(decoded_path):
                os.remove(decoded_path)

    except KeyboardInterrupt:
        print("\nStopped.")
        if all_audio:
            full_audio = np.concatenate(all_audio)
            sf.write(args.output, full_audio, SAMPLE_RATE)
            print(f"Saved {len(full_audio)/SAMPLE_RATE:.1f}s to {args.output}")
        sock.close()


if __name__ == '__main__':
    main()