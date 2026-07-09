"""SoundStream codec wrapper (via Google Lyra v2 CLI).

Lyra v2 is Google's production codec built on the SoundStream neural
architecture. It ships pretrained weights and runs in real time on ARM,
which makes it usable on the Raspberry Pi 4.

Binaries required on PATH (or set via env vars):
    encoder_main / decoder_main  (built from github.com/google/lyra)

Env vars:
    LYRA_ENCODER     path to encoder binary   (default: encoder_main)
    LYRA_DECODER     path to decoder binary   (default: decoder_main)
    LYRA_MODEL_PATH  path to model_coeffs dir (default: model_coeffs)

Supported bitrates (kbps): 3.2, 6, 9.2
"""

import os
import shutil
import subprocess
import tempfile

import soundfile as sf

ENCODER = os.environ.get("LYRA_ENCODER", "encoder_main")
DECODER = os.environ.get("LYRA_DECODER", "decoder_main")
MODEL_PATH = os.environ.get("LYRA_MODEL_PATH", "model_coeffs")


def _to_wav(source_path, tmp_dir):
    """Lyra only accepts 16-bit PCM wav, convert the input if needed."""
    if source_path.lower().endswith(".wav"):
        return source_path

    data, sr = sf.read(source_path)
    wav_path = os.path.join(
        tmp_dir, os.path.splitext(os.path.basename(source_path))[0] + ".wav"
    )
    sf.write(wav_path, data, sr, subtype="PCM_16")
    return wav_path


def encode(source_path, output_path, bitrate=3.2):
    """Encode audio to a .lyra file. bitrate in kbps (3.2, 6 or 9.2)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = _to_wav(source_path, tmp_dir)

        result = subprocess.run([
            ENCODER,
            f"--input_path={wav_path}",
            f"--output_dir={tmp_dir}",
            f"--bitrate={int(float(bitrate) * 1000)}",
            f"--model_path={MODEL_PATH}",
        ])

        encoded = os.path.join(
            tmp_dir, os.path.splitext(os.path.basename(wav_path))[0] + ".lyra"
        )
        if os.path.exists(encoded):
            shutil.move(encoded, output_path)

        return result


def decode(compressed_path, decoded_path, bitrate=None):
    """Decode a .lyra file back to wav."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            DECODER,
            f"--encoded_path={compressed_path}",
            f"--output_dir={tmp_dir}",
            f"--model_path={MODEL_PATH}",
        ]
        
        if bitrate is not None:
            cmd.append(f"--bitrate={int(float(bitrate) * 1000)}")
        
        result = subprocess.run(cmd)

        name = os.path.splitext(os.path.basename(compressed_path))[0]
        decoded = os.path.join(tmp_dir, name + "_decoded.wav")
        if os.path.exists(decoded):
            shutil.move(decoded, decoded_path)

        return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        encode(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        decode(sys.argv[1], sys.argv[2])