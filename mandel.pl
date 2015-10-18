#!/usr/bin/perl
# Mandelbrot in your terminal
# for /tech/ with love
use strict;
use warnings;
$|++;

my $mandel_color_min = 16; #mandel_color_min=232 for greyscale
my $mandel_color_max = 255;
my $mandel_color_range = $mandel_color_max - $mandel_color_min;

my $cols = 80;
my $rows = 20;

my $resize = `resize`;
if ($resize =~ /COLUMNS=(\d+)/) { $cols = int($1); }
if ($resize =~ /LINES=(\d+)/) { $rows = int($1); }

my $centre_x = $cols / 2.;
my $centre_y = $rows / 2.;

# Conversion from char-in-terminal space to abstract-mathematical-bullshite space
my $scale_x = 2. / $cols;  # We want the whole thing to be 2 units wide. It is currently cols chars wide.
my $scale_y = 2. / $rows;  # Ditto for rows

$centre_x += 0.5 / $scale_x;

my $max_iters=10;

while ($max_iters<200) {
    printf "\033[1;1H";
    my $row = 0;
    while ($row < $rows) {
        my $col = 0;
        while ($col < $cols) {
            # Mandel math:
            my $mandel_re = ($col - $centre_x) * $scale_x;
            my $mandel_im = ($row - $centre_y) * $scale_y;
            my $orig_re = $mandel_re;
            my $orig_im = $mandel_im;
            my $iters = 0;
            # Skip a huge circle that we know can't be escaped
            if (($mandel_re + 0.25)**2 + $mandel_im**2 < 0.25) {
                $iters=$max_iters;
            } else {
                # While the modulus of the imaginary number is less than 2...
                while ($mandel_re * $mandel_re + $mandel_im * $mandel_im < 4 && $iters != $max_iters) {
                    # Square it and add the original value
                    ($mandel_re, $mandel_im) = ($mandel_re**2 - $mandel_im**2 + $orig_re, $mandel_re * $mandel_im * 2 + $orig_im);

                    # Count how many iterations we've done
                    $iters++;
                }
            }

            printf "\033[38;5;%dm%s", $iters * $mandel_color_range / $max_iters + $mandel_color_min, "█";
            $col++;
        }
        $row++;
    }
    $max_iters *= 2;
}
