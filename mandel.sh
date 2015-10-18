#!/bin/sh
# Mandelbrot in your terminal
# for /tech/ with love

if [ "${KSH_VERSION%MIRBSD*}" != "$KSH_VERSION" ] # If we're on mksh use print instead of printf
then put_colored() { print -n "\033[38;5;${1}m$2"; }
else put_colored() { printf '\033[38;5;%dm%s' "$1" "$2"; }
fi

# Speed up execution under some shells. This lets us avoid quoting, which also slows things down by a couple of ms.
IFS=
set -f

frac_scale=9000  # Non-zsh shells don't support floats so let's multiply
                 # everything by a constant to make up for that somewhat

mandel_color_min=16 #mandel_color_min=232 for greyscale
mandel_color_max=255
mandel_color_range=$((mandel_color_max - mandel_color_min))

eval $(resize)  # Get terminal width → $COLUMNS $LINES

centre_x=$((COLUMNS / 2))
centre_y=$((LINES / 2))

# Conversion from char-in-terminal space to abstract-mathematical-bullshite space
scale_x=$((frac_scale * 2 / COLUMNS))  # We want the whole thing to be 2 units wide. It is currently COLUMNS chars wide.
scale_y=$((frac_scale * 2 / LINES))    # Ditto for LINES

centre_x=$((centre_x + (frac_scale / 2) / scale_x))

max_iters=10
while true; do
    printf '\033[1;1H'
    row=0
    while [ $row -lt $LINES ]; do
        col=0
        while [ $col -lt $COLUMNS ]; do
            # Mandel math:
            mandel_re=$(((col - centre_x) * scale_x))
            mandel_im=$(((row - centre_y) * scale_y))
            orig_re=$mandel_re
            orig_im=$mandel_im
            iters=0
            if
                # Skip a huge circle that we know can't be escaped
                [ $(( (mandel_re + frac_scale / 4) * (mandel_re + frac_scale / 4) + mandel_im * mandel_im - frac_scale * frac_scale / 2 / 2)) -lt 0 ]
            then
                iters=$max_iters
            else
                # While the modulus of the imaginary number is less than 2... (counting the frac_scale crap too)
                while [ $((mandel_re * mandel_re + mandel_im * mandel_im)) -lt $((frac_scale * frac_scale * 4)) ]; do
                    # Square it and add the original value
                    _temp_im=$((mandel_re * mandel_im * 2 / frac_scale + orig_im))
                    mandel_re=$(((mandel_re * mandel_re - mandel_im * mandel_im) / frac_scale + orig_re))
                    mandel_im=$_temp_im

                    # Count how many iterations we've done
                    iters=$((iters + 1))

                    # Stop calculating if we've reached the highest we can represent in our colours
                    [ $iters -eq $max_iters ] && break
                done
            fi

            # Draw!
            put_colored $((iters * mandel_color_range / max_iters + mandel_color_min)) '█'
            col=$((col + 1))
        done
        row=$((row + 1))
    done
    max_iters=$((max_iters * 2))
done

# You have just witnessed a poorly hacked together full colour mandelbrot fractal using a shitty implementation of floating point complex numbers, in posix sh.
# Tested compatible with zsh, bash, dash (debian's /bin/sh), posh, mksh (android's /bin/sh), and busybox
