import socket
import numpy as np
import soundfile as sf

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 5005))

chunks = []
while True:
    data, addr = sock.recvfrom(4096)
    if data == b"END":
        break
    chunk = np.frombuffer(data, dtype=np.float32)
    chunks.append(chunk)

audio = np.concatenate(chunks)
sf.write(f"data/received.wav", audio, 16000)