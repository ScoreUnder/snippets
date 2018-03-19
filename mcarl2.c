#include <stdio.h>
#include <stdint.h>

int main(){
    uint64_t hit = 0, r = 0x10000000, r_sq = r*r;
    uint64_t x = r;
    uint64_t y = 0;
    while (x > y) {
        int64_t err_u  = x*x         + (y+1)*(y+1) - r_sq;
        int64_t err_ul = (x-1)*(x-1) + (y+1)*(y+1) - r_sq;
        int64_t err_l  = (x-1)*(x-1) + y*y         - r_sq;

        if (err_u  < 0) err_u  = -err_u;
        if (err_ul < 0) err_ul = -err_ul;
        if (err_l  < 0) err_l  = -err_l;

        if (err_u < err_l) {
            y++;
            if (err_ul < err_u) {
                x--;
                hit += y;
            }
            hit += x;
        } else {
            x--;
            if (err_ul < err_l) {
                y++;
                hit += x;
            }
            hit += y;
        }
    }

    printf("Result: %.20Lf\n", hit / (long double)r_sq * 4);
}
