#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals
import struct
import sys

def format_ip(ip):
    return '.'.join(map(str, struct.unpack("BBBB", struct.pack(">I", ip))))

def unformat_ip(ip):
    return struct.unpack(">I", struct.pack("BBBB", *map(int, ip.split('.'))))[0]

def mask_ip(ip, block):
    mask = 0xFFFFFFFF & ~((1 << (32 - block)) - 1)
    start_ip = ip & mask
    end_ip = ip | (0xFFFFFFFF & ~mask)
    return start_ip, end_ip

def main(argv):
    if len(argv) < 2:
        print("Pass an IP with CIDR block as an argument (e.g. 192.168.1.0/24)")
        return 1

    ip, block = argv[1].split('/')
    block = int(block)
    ip = unformat_ip(ip)

    start_ip, end_ip = mask_ip(ip, block)
    print(format_ip(start_ip))
    print(format_ip(end_ip))
    return 0

if __name__ == '__main__':
    exit(main(sys.argv))
