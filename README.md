# NeuralCodec-RPi

> Real-time voice transmission system on Raspberry Pi 4 using neural speech codecs for low-bandwidth networks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

---

## Setup

### System dependencies

```bash
sudo apt install -y opus-tools codec2 libcodec2-dev \
                    python3.12-dev build-essential
```

### Install pip dependecies

```bash
pip install -r requirements-torch.txt
pip install -r requirements.txt
```

### Test dataset (LibriSpeech dev-clean, ~322 MB)

```bash
cd data/samples
wget https://www.openslr.org/resources/12/dev-clean.tar.gz
tar -xzf dev-clean.tar.gz
```

## Usage

### Run benchmark

```bash
python3 benchmark/run.py
```

Outputs in `benchmark/results/`:
- `Opus.png`, `Codec2.png` — individual codec curves
- `comparison.png` — overlaid comparison

### Test codecs

**Opus**
```bash
# Encode at 16 kbps
python3 benchmark/acodecs/opus_codec.py input.flac output.opus 16

# Decode
python3 benchmark/acodecs/opus_codec.py input.opus output.wav
```

**Codec2**
```bash
# Encode at 2.4 kbps
python3 benchmark/acodecs/codec2_codec.py input.flac output.c2 2.4

# Decode
python3 benchmark/acodecs/codec2_codec.py input.c2 output.wav 2.4
```

**EnCodec**
```bash
# Compress + decode in one step (output .wav)
encodec -b 6 -f input.flac output.wav

# Two steps
encodec -b 6 -f input.flac compressed.ecdc
encodec -f compressed.ecdc decoded.wav
```

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
│   ├── audio_io.py        # load / save / info
│   ├── mesure.py          # bitrate, PESQ, compression ratio
│   ├── run.py             # evaluation orchestrator
│   ├── acodecs/           # codec wrappers
│   │   ├── opus_codec.py
│   │   └── codec2_codec.py
│   │   └── encodec_codec.py
│   └── results/           # plots, CSV
├── pi/                    # Phase 2 — real-time deployment (planned)
│   ├── transmitter.py     # mic → encode → UDP send
│   └── receiver.py        # UDP recv → decode → speaker
└── data/
    ├── samples/           # LibriSpeech (gitignored)
    └── encoded/           # codec outputs (gitignored)
```

---

## License

MIT — see [LICENSE](LICENSE)
