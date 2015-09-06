#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

// 232 greyscale, 16 colour
#define MANDEL_COLOR_MIN 16
#define MANDEL_COLOR_MAX 255

#define MANDEL_COLOR_RANGE (MANDEL_COLOR_MAX - MANDEL_COLOR_MIN)

void put_colored(int color, char *what) {
    printf("\033[38;5;%dm%s", color, what);
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fputs("Need 2 args: rows, columns\n", stderr);
        return 1;
    }

    int rows = atoi(argv[1]);
    int columns = atoi(argv[2]);

    int centre_x = columns / 2;
    int centre_y = rows / 2;

    double scale_x = 2 / (double)columns;
    double scale_y = 2 / (double)rows;

    centre_x += .5 / scale_x;

    int max_iters = 10;
    int *arr = malloc(rows * columns * sizeof *arr);

    while (true) {
        for (int row = 0; row < rows; row++) {
            for (int col = 0; col < columns; col++) {
                double mandel_re = (col - centre_x) * scale_x;
                double mandel_im = (row - centre_y) * scale_y;
                double orig_re = mandel_re;
                double orig_im = mandel_im;
                int iters = 0;
                if ((mandel_re + 1 / 4.) * (mandel_re + 1 / 4.) + mandel_im * mandel_im < 0.25) {
                    iters = max_iters;
                } else {
                    while (mandel_re * mandel_re + mandel_im * mandel_im < 4) {
                        double temp_im = mandel_re * mandel_im * 2 + orig_im;
                        mandel_re = mandel_re * mandel_re - mandel_im * mandel_im + orig_re;
                        mandel_im = temp_im;

                        iters++;

                        if (iters == max_iters) break;
                    }
                }

                iters = (int) (log(iters) / log(max_iters) * MANDEL_COLOR_RANGE);
                arr[row * columns + col] = iters + MANDEL_COLOR_MIN;
            }
        }

        // Draw!
        printf("\033[1;1H");
        for (int i = 0; i < rows * columns; i++)
            put_colored(arr[i], "█");
        fflush(stdout);

        max_iters *= 2;
    }
}
