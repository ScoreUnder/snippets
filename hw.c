#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

char const *restrict const palette[] = {"l","o","He",", W","r","d!"};

uint_fast8_t get_bit(uint8_t const *restrict const stream, size_t pos)
{
    return (stream[pos >> 3] >> (pos & 7)) & 1;
}

size_t strcpy_get_len(char *restrict const dest, char const *restrict const src)
{
    size_t const len = strlen(src);
    memcpy(dest, src, len + 1);
    return len;
}

void decode(char *restrict out, uint8_t const *restrict const in, size_t len)
{
    size_t iind = 0, oind = 0;
    while (len--) {
        bool const long_code = get_bit(in, iind++);
        size_t pind = get_bit(in, iind++);
        if (long_code)
            pind = 2 + ((pind << 1) | get_bit(in, iind++));
        oind += strcpy_get_len(&out[oind], palette[pind]);
    }
}

int main(int const argc, char const *restrict const *restrict const argv)
{
    uint_fast8_t static const data_len = 9;
    uint8_t static const data[] = {0x01, 0xEB, 0x38};
    char buffer[0x20];

    // The "hello world"
    decode(buffer, data, data_len);
    puts(buffer);

    // An easter egg I guess
    decode(buffer, (uint8_t[]){0x48, 0xF5}, 7);
    puts(buffer);
}
