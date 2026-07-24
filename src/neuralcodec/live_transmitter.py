import argparse
import os
import socket
import time
import librosa
import sounddevice as sd
import soundfile as sf

from neuralcodec.common.codec_registry import codecs

CHUNK_DURATION = 1
MIC_SAMPLE_RATE = 44100
CODEC_SAMPLE_RATE = 16000
MIC_DEVICE = 1
UDP_CHUNK_SIZE = 1400
TMP_DIR = "/dev/shm"

def main():
    parser = argparse.ArgumentParser(description='Transmitter')
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

    ext = codec_info["extension"]
    wav_path = os.path.join(TMP_DIR, "tx_chunk.wav")
    compressed_path = os.path.join(TMP_DIR, f"tx_chunk.{ext}")
    chunk_num = 0

    try:
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

            audio_16k = librosa.resample(audio.flatten(), orig_sr=MIC_SAMPLE_RATE, target_sr=CODEC_SAMPLE_RATE)

            t0 = time.time()
            sf.write(wav_path, audio_16k, CODEC_SAMPLE_RATE, subtype="PCM_16")
            codec_info["encode"](wav_path, compressed_path, args.bitrate)

            with open(compressed_path, "rb") as f:
                compressed = f.read()

            for i in range(0, len(compressed), UDP_CHUNK_SIZE):
                sock.send(compressed[i:i + UDP_CHUNK_SIZE])
            sock.send(b"END")

            elapsed = time.time() - t0
            print(f"[Chunk {chunk_num}] {len(compressed)} bytes, encode+send duration: {elapsed:.3f}s")

            if os.path.exists(wav_path):
                os.remove(wav_path)
            if os.path.exists(compressed_path):
                os.remove(compressed_path)

    except KeyboardInterrupt:
        print("\nStopped.")
        sock.close()


if __name__ == '__main__':
    main()