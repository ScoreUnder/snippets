#!/usr/bin/env perl
use strict;

sub format_ip {
	join '.', unpack 'CCCC', pack 'N', $_[0];
}

sub unformat_ip {
	unpack 'N', pack 'CCCC', split /\./, $_[0];
}

sub mask_ip {
	my ($ip, $block) = @_;
	my $mask = 0xFFFFFFFF & ~((1 << (32 - $block)) - 1);
	my $start_ip = $ip & $mask;
	my $end_ip = $ip | (0xFFFFFFFF & ~$mask);
	return ($start_ip, $end_ip);
}

sub main {
	die "Pass an IP with CIDR block as an argument (e.g. 192.168.1.0/24)\n" if @_ != 1;

	my ($ip, $block) = split qr(/), $_[0];

	my ($start_ip, $end_ip) = map {format_ip $_} mask_ip(unformat_ip($ip), $block);
	print "$start_ip\n";
	print "$end_ip\n";
}

main(@ARGV);
