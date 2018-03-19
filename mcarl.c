#include <stdio.h>
#include <stdint.h>

uint64_t binsearch_rad(uint64_t x, uint64_t y_start, uint64_t y_end, uint64_t rad_sq)
{
    if (y_start == y_end - 1) return y_start;
    uint64_t middle = (y_start + y_end) / 2;
    if (x*x + middle*middle < rad_sq)
        y_start = middle;
    else
        y_end = middle;
    return binsearch_rad(x, y_start, y_end, rad_sq);
}

int main(){
    uint64_t hit = 0, r = 0x1000000, r_sq = r*r;
    for (uint64_t x = 0; x < r; x++) {
        hit += binsearch_rad(x, 0, r, r_sq);
    }
    printf("Result: %.20Lf\n", hit / (long double)r_sq * 4);
}
