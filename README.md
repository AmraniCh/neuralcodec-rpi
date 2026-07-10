# NeuralCodec-RPi

> Real-time voice transmission system on Raspberry Pi 4 using neural speech codecs for low-bandwidth networks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

---

## Setup

### System dependencies

```bash
sudo apt install -y opus-tools codec2 libcodec2-dev \
                    python3.12-dev build-essential libportaudio2
```

### Install pip dependencies

```bash
pip install -r requirements-torch.txt
pip install -r requirements.txt
```

### SoundStream (Lyra v2) — full workflow

SoundStream support uses Google's Lyra v2 codec (built on the SoundStream
architecture, with pretrained weights, real-time on ARM). Lyra only builds
on Linux — use the Raspberry Pi or WSL (Ubuntu). Tested on Ubuntu 24.04 /
GCC 13.

**1. Install Bazel (via bazelisk) and build prerequisites**

```bash
sudo apt update
sudo apt install -y build-essential git python3-dev python3-numpy
sudo wget -O /usr/local/bin/bazel \
    https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-amd64
sudo chmod +x /usr/local/bin/bazel
```

`python3-numpy` must be in the **system** python (deactivate any venv) —
Lyra's TensorFlow toolchain probes it during workspace setup.

**2. Clone and patch Lyra** (clone into `~`, not `/mnt/c`, for build speed)

```bash
cd ~ && git clone https://github.com/google/lyra.git && cd lyra

# glog is fetched from master and expects an @gflags repo — pin it:
sed -i 's/branch = "master"/tag = "v0.5.0"/' WORKSPACE

# GCC 13 no longer implicitly includes <cstdint> — force it globally:
echo 'build --cxxopt=-includecstdint' >> .bazelrc
```

**3. Build (~5–40 min first time)**

```bash
bazel build -c opt lyra/cli_example:encoder_main lyra/cli_example:decoder_main
```

Ignore the thousands of `deprecated` warnings from NEON_2_SSE — only
`ERROR:` lines matter.

**4. Point the wrapper at the binaries** (append to `~/.bashrc`)

```bash
export LYRA_ENCODER=$HOME/lyra/bazel-bin/lyra/cli_example/encoder_main
export LYRA_DECODER=$HOME/lyra/bazel-bin/lyra/cli_example/decoder_main
export LYRA_MODEL_PATH=$HOME/lyra/lyra/model_coeffs
```

**5. Test**

```bash
$LYRA_ENCODER --helpshort          # sanity check
python3 benchmark/run.py SoundStream
```

Outputs `benchmark/results/SoundStream.png`. To include SoundStream in
`comparison.png`, run all codecs together:

```bash
python3 benchmark/run.py                          # all codecs
python3 benchmark/run.py Opus Codec2 SoundStream  # or a subset
```

(The comparison plot is rebuilt from scratch each run — only codecs in the
current run appear on it.)

### Test dataset (LibriSpeech dev-clean, ~322 MB)

```bash
cd data/samples
wget https://www.openslr.org/resources/12/dev-clean.tar.gz
tar -xzf dev-clean.tar.gz
```

## Usage

### Transmit & Receive

**Terminal 1 - Receiver:**

```bash
python src/neuralcodec/receiver.py --codec encodec --bitrate 6
```

**Terminal 2 - Transmitter:**

```bash
python src/neuralcodec/transmitter.py data/samples/LibriSpeech/dev-clean/2902/9008/2902-9008-0000.flac --codec encodec --bitrate 6
```

Output saved to `data/received.wav`. Add `--play` to play on speaker.

### Run benchmark

```bash
python3 benchmark/run.py               # all codecs
python3 benchmark/run.py SoundStream   # only one (case-insensitive)
python3 benchmark/run.py Opus Codec2   # any subset
```

Outputs in `benchmark/results/`:
- `Opus.png`, `Codec2.png` — individual codec curves
- `comparison.png` — overlaid comparison


### Test codecs separately

```bash
# Encode at 16 kbps
python3 src/neuralcodec/common/acodecs/opus_codec.py input.flac output.opus 16

# Decode
python3 src/neuralcodec/common/acodecs/opus_codec.py input.opus output.wav
```

Other codecs follow the same pattern — see files in `src/neuralcodec/common/acodecs/`.


### Manual measurements

```bash
# PESQ + bitrate comparison
python3 benchmark/mesure.py original.flac decoded.wav

# Real bitrate
python3 benchmark/mesure.py compressed.opus
```

---

## Project Structure

```
neuralcodec-rpi/
├── benchmark/
│   ├── audio_io.py
│   ├── mesure.py
│   ├── run.py
│   └── results
├── src/neuralcodec/
│   ├── common/
│   │   ├── audio_io.py
│   │   └── acodecs/
│   │       ├── opus_codec.py
│   │       ├── codec2_codec.py
│   │       ├── encodec_codec.py
│   │       └── soundstream_codec.py
│   ├── transmitter.py
│   └── receiver.py
└── data/
    ├── samples/   # LibriSpeech
    └── encoded/   # codec outputs
```

---

## License

MIT — see [LICENSE](LICENSE)