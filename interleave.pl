#!/usr/bin/env perl
use strict;
use warnings;

my $len = shift;

my @files = map {
    open my $fh, '<', $_ or die "Could not open $_: $!\n";
    $fh
} @ARGV;

my $data_remains = 1;
while ($data_remains) {
    $data_remains = 0;
    for (@files) {
        my $data = '';
        my $res;
        $res = read $_, $data, $len;
        $data_remains ||= $res;
        if (!defined $res) {
            print STDERR "Can't read $_: $!\n";
        }
        print $data;
    }
}
