#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>

void bubblesort(double *restrict items, size_t items_len)
{
    // If it's 0, 0 - 1 is greater than 0, so our loop would be wrong
    // if it's 1, it doesn't need sorting
    // so, skip sorting in those cases
    if (items_len < 2) return;

    bool swapped;
    do {
        swapped = false;
        for (size_t i = 0; i < items_len - 1; i++) {
            if (items[i] > items[i + 1]) {
                double tmp = items[i];
                items[i] = items[i + 1];
                items[i + 1] = tmp;
                swapped = true;
            }
        }
    } while (swapped);
}

int main(unsigned int argc, char **argv)
{
    size_t items_len = argc - 1;
    double *items = malloc(items_len * sizeof *items);
    for (size_t i = 0; i < items_len; i++) {
        int scanned = sscanf(argv[i + 1], "%lf", &items[i]);
        if (scanned != 1) {
            fprintf(stderr, "Bad argument (should be double): argument %d: \"%s\"\n", i + 1, argv[i + 1]);
            return 1;
        }
    }

    bubblesort(items, items_len);

    for (size_t i = 0; i < items_len; i++)
        printf("%lg\n", items[i]);

    return 0;
}
