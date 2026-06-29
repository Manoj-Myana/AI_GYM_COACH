import sys
import os

path = os.path.join(os.getcwd(), 'last_groq_audio.wav')
if not os.path.exists(path):
    print('File not found:', path)
    sys.exit(1)

with open(path, 'rb') as f:
    data = f.read()

print('File:', path)
print('Size:', len(data), 'bytes')
print('\nFirst 32 bytes (hex):')
print(data[:32].hex())

# Check MP3 signatures
if data.startswith(b'ID3') or data[0:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
    print('\nDetected: MP3-like signature')

# Check WAV RIFF
if data[0:4] != b'RIFF' or data[8:12] != b'WAVE':
    print('\nNot a standard WAV RIFF file')
else:
    print('\nRIFF/WAVE header detected')
    # find fmt chunk
    fmt_pos = data.find(b'fmt ')
    if fmt_pos == -1:
        print('fmt chunk not found')
    else:
        # fmt chunk usually 16 or more bytes after 'fmt '
        fmt_size = int.from_bytes(data[fmt_pos+4:fmt_pos+8], 'little')
        print('fmt chunk at', fmt_pos, 'size', fmt_size)
        if fmt_size >= 16 and len(data) >= fmt_pos+8+16:
            audio_format = int.from_bytes(data[fmt_pos+8:fmt_pos+10], 'little')
            num_channels = int.from_bytes(data[fmt_pos+10:fmt_pos+12], 'little')
            sample_rate = int.from_bytes(data[fmt_pos+12:fmt_pos+16], 'little')
            byte_rate = int.from_bytes(data[fmt_pos+16:fmt_pos+20], 'little')
            block_align = int.from_bytes(data[fmt_pos+20:fmt_pos+22], 'little')
            bits_per_sample = int.from_bytes(data[fmt_pos+22:fmt_pos+24], 'little')
            print('Audio format code:', audio_format)
            print('Channels:', num_channels)
            print('Sample rate:', sample_rate)
            print('Byte rate:', byte_rate)
            print('Block align:', block_align)
            print('Bits per sample:', bits_per_sample)

print('\nDone')
