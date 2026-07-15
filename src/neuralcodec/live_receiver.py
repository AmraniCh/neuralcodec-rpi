import argparse
import os
import socket
import tempfile
import threading
import queue

import numpy as np
import soundfile as sf

from neuralcodec.common.codec_registry import codecs

try:
    import sounddevice as sd
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False

SAMPLE_RATE = 16000

chunk_queue = queue.Queue()


def receive_chunk(sock):
    chunks = []
    while True:
        data, addr = sock.recvfrom(4096)
        if data == b"CHUNK_END":
            break
        chunks.append(data)
    return b"".join(chunks)


def decode_chunk(compressed, codec_info, bitrate):
    ext = codec_info["extension"]
    tmp_dir = tempfile.mkdtemp()
    compressed_path = os.path.join(tmp_dir, f"rx_chunk.{ext}")
    wav_path = os.path.join(tmp_dir, f"rx_chunk_decoded.wav")

    with open(compressed_path, "wb") as f:
        f.write(compressed)

    codec_info["decode"](compressed_path, wav_path, bitrate)

    audio, sr = sf.read(wav_path)

    os.remove(compressed_path)
    os.remove(wav_path)
    os.rmdir(tmp_dir)

    return audio, sr


def receive_loop(sock):
    chunk_num = 0
    while True:
        chunk_num += 1
        compressed = receive_chunk(sock)
        print(f"[Chunk {chunk_num}] Received {len(compressed)} bytes")
        chunk_queue.put((chunk_num, compressed))


def decode_play_loop(codec_info, bitrate, play, all_audio):
    while True:
        chunk_num, compressed = chunk_queue.get()
        audio, sr = decode_chunk(compressed, codec_info, bitrate)
        all_audio.append(audio)
        print(f"[Chunk {chunk_num}] Decoded {len(audio)/sr:.2f}s")

        if play and HAS_AUDIO:
            sd.play(audio, sr)
            sd.wait()


if __name__ == '__main__':
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

    print(f"Codec: {codec_info['label']} @ {args.bitrate} kbps")
    print(f"Listening on port {args.port}")
    print("Ctrl+C to stop\n")

    all_audio = []

    try:
        recv_thread = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
        recv_thread.start()
        decode_play_loop(codec_info, args.bitrate, args.play, all_audio)
    except KeyboardInterrupt:
        print("\nStopped.")
        if all_audio:
            full_audio = np.concatenate(all_audio)
            sf.write(args.output, full_audio, SAMPLE_RATE)
            print(f"Saved {len(full_audio)/SAMPLE_RATE:.1f}s to {args.output}")
        sock.close()