import argparse
import os
import socket
import time
import threading
import queue

import librosa
import sounddevice as sd
import soundfile as sf

from neuralcodec.common.codec_registry import codecs

CHUNK_DURATION = 1
MIC_SAMPLE_RATE = 44100
LYRA_SAMPLE_RATE = 16000
MIC_DEVICE = 1
UDP_CHUNK_SIZE = 1400
TMP_DIR = "/dev/shm"

audio_queue = queue.Queue()


def record_loop():
    chunk_num = 0
    while True:
        chunk_num += 1
        audio = sd.rec(
            int(CHUNK_DURATION * MIC_SAMPLE_RATE),
            samplerate=MIC_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=MIC_DEVICE,
        )
        sd.wait()
        audio_16k = librosa.resample(audio.flatten(), orig_sr=MIC_SAMPLE_RATE, target_sr=LYRA_SAMPLE_RATE)
        audio_queue.put((chunk_num, audio_16k))


def encode_chunk(audio, codec_info, bitrate):
    ext = codec_info["extension"]
    wav_path = os.path.join(TMP_DIR, f"tx_chunk.wav")
    compressed_path = os.path.join(TMP_DIR, f"tx_chunk.{ext}")

    sf.write(wav_path, audio, LYRA_SAMPLE_RATE, subtype="PCM_16")
    codec_info["encode"](wav_path, compressed_path, bitrate)

    with open(compressed_path, "rb") as f:
        compressed = f.read()

    os.remove(wav_path)
    if os.path.exists(compressed_path):
        os.remove(compressed_path)

    return compressed


def send_compressed(sock, data):
    for i in range(0, len(data), UDP_CHUNK_SIZE):
        sock.send(data[i:i + UDP_CHUNK_SIZE])
    sock.send(b"CHUNK_END")


def encode_send_loop(sock, codec_info, bitrate):
    while True:
        chunk_num, audio = audio_queue.get()
        t0 = time.time()
        compressed = encode_chunk(audio, codec_info, bitrate)
        send_compressed(sock, compressed)
        enc_time = time.time() - t0
        print(f"[Chunk {chunk_num}] {len(compressed)} bytes, {enc_time:.3f}s (RTF {enc_time/CHUNK_DURATION:.3f})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Live transmitter')
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=5005)
    parser.add_argument('--codec', default='soundstream', choices=list(codecs.keys()))
    parser.add_argument('--bitrate', type=float, default=3.2)

    args = parser.parse_args()
    codec_info = codecs[args.codec]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((args.host, args.port))

    print(f"Codec: {codec_info['label']} @ {args.bitrate} kbps")
    print(f"Transmitting to {args.host}:{args.port}")
    print("Ctrl+C to stop\n")

    try:
        rec_thread = threading.Thread(target=record_loop, daemon=True)
        rec_thread.start()
        encode_send_loop(sock, codec_info, args.bitrate)
    except KeyboardInterrupt:
        print("\nStopped.")
        sock.close()