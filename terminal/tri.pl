#!/usr/bin/env perl
my $layers = $ARGV[0];
print ' ' x ($layers - $_) . "\033[4m" . ('╱╲' x $_) . "\033[0m\n" for 1..$layers;
