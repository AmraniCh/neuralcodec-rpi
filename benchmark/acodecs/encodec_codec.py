import subprocess

def encode(original_path, compressed_path, bitrate):
    return subprocess.run(["encodec", "-b", str(bitrate), original_path, compressed_path])

def decode(compressed_path, decoded_path, bitrate=None):
    return subprocess.run(["encodec", compressed_path, decoded_path])

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        source = sys.argv[1]
        output = sys.argv[2]
        bitrate = sys.argv[3]
        encode(source, output, bitrate)

    elif len(sys.argv) == 3:
        source = sys.argv[1]
        output = sys.argv[2]
        decode(source, output)