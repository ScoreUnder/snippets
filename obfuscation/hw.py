#!/usr/bin/env python3
def get_bit(stream, pos): return (stream[pos // 8] >> (pos % 8)) & 1

palette = ["l", "o", "He", ", W", "r", "d!"]

def decode(in_, len_):
    out = ""
    in_index = 0
    for _ in range(len_):
        long_code = get_bit(in_, in_index)
        palette_index = get_bit(in_, in_index + 1)
        in_index += 2
        if long_code:
            palette_index = 2 + 2*palette_index + get_bit(in_, in_index)
            in_index += 1
        out += palette[palette_index]
    return out

# What you came here for
print(decode([0x01, 0xEB, 0x38], 9))

# Easter egg
print(decode([0x48, 0xF5], 7))
