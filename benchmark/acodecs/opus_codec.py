import subprocess


def encode(source_path, output_path, bitrate=16):
    return subprocess.run(["opusenc", "--bitrate", str(bitrate), source_path, output_path])

def decode(source_path, output_path):
    return subprocess.run(["opusdec", source_path, output_path])



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        source = sys.argv[1]
        output = sys.argv[2]
        bitrate = int(sys.argv[3])
        encode(source, output, bitrate)

    elif len(sys.argv) == 3:
        source = sys.argv[1]
        output = sys.argv[2]
        decode(source, output)