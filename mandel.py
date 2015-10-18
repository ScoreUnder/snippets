#!/usr/bin/env python
# Mandelbrot in your terminal
# for /tech/ with love
import subprocess

mandel_color_min = 16; #mandel_color_min=232 for greyscale
mandel_color_max = 255;
mandel_color_range = mandel_color_max - mandel_color_min;

cols = 80;
rows = 20;

resize = [cmd.strip().split('=', 1) for cmd in subprocess.check_output(['resize']).decode('utf-8').split(';')]
resize = filter(lambda x: len(x) == 2, resize)
resize = dict(resize)

cols = int(resize['COLUMNS'])
rows = int(resize['LINES'])

centre_x = cols / 2.;
centre_y = rows / 2.;

# Conversion from char-in-terminal space to abstract-mathematical-bullshite space
scale_x = 2. / cols;  # We want the whole thing to be 2 units wide. It is currently cols chars wide.
scale_y = 2. / rows;  # Ditto for rows

centre_x += 0.5 / scale_x;

max_iters=10;

while max_iters < 200:
    print("\033[1;1H", end='');
    row = 0;
    while row < rows:
        col = 0;
        while col < cols:
            # Mandel math:
            mandel_re = (col - centre_x) * scale_x;
            mandel_im = (row - centre_y) * scale_y;
            orig_re = mandel_re;
            orig_im = mandel_im;
            iters = 0;
            # Skip a huge circle that we know can't be escaped
            if (mandel_re + 0.25)**2 + mandel_im**2 < 0.25:
                iters=max_iters;
            else:
                # While the modulus of the imaginary number is less than 2...
                while mandel_re * mandel_re + mandel_im * mandel_im < 4 and iters != max_iters:
                    # Square it and add the original value
                    (mandel_re, mandel_im) = (mandel_re**2 - mandel_im**2 + orig_re, mandel_re * mandel_im * 2 + orig_im);

                    # Count how many iterations we've done
                    iters+=1;

            print("\033[38;5;%dm%s" % (iters * mandel_color_range / max_iters + mandel_color_min, "█"), end='');
            col+=1;
        row+=1;
    max_iters *= 2;
