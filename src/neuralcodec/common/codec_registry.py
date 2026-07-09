from neuralcodec.common.acodecs.opus_codec import encode as opus_encode, decode as opus_decode
from neuralcodec.common.acodecs.codec2_codec import encode as codec2_encode, decode as codec2_decode
from neuralcodec.common.acodecs.encodec_codec import encode as encodec_encode, decode as encodec_decode
from neuralcodec.common.acodecs.soundstream_codec import encode as soundstream_encode, decode as soundstream_decode

codecs = {
    "opus": {
        "bitrates": [6, 8, 12, 16, 32, 64],
        "extension": "opus",
        "encode": opus_encode,
        "decode": opus_decode,
        "is_neural": False,
        "label": "Opus"
    },
    "codec2": {
        "bitrates": [1.2, 1.3, 1.6, 2.4, 3.2],
        "extension": "c2",
        "encode": codec2_encode,
        "decode": codec2_decode,
        "is_neural": False,
        "label": "Codec2"
    },
    "encodec": {
        "bitrates": [1.5, 3, 6, 12, 24],
        "extension": "ecdc",
        "encode": encodec_encode,
        "decode": encodec_decode,
        "is_neural": True,
        "label": "EnCodec"
    },
    "soundstream": {
        "bitrates": [3.2, 6, 9.2],
        "extension": "lyra",
        "encode": soundstream_encode,
        "decode": soundstream_decode,
        "is_neural": True,
        "label": "SoundStream"
    }
}