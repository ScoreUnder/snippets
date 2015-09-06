#!/usr/bin/env python
import fcntl
import numpy
import os
import sys
import termios
import time


class LinuxSingleCharInput(object):
    __slots__ = ['_fd', '_oldattr']
    def __init__(self):
        self._fd = sys.stdin.fileno()
        self._oldattr = None

    def __enter__(self):
        self._oldattr = termios.tcgetattr(self._fd)
        newattr = self._oldattr[:]
        newattr[3] &= ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(self._fd, termios.TCSANOW, newattr)
        return self

    def __exit__(self, etype, evalue, etraceback):
        termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._oldattr)
        return False

    def read(self):
        return sys.stdin.read(1)


class BPMClock(object):
    __slots__ = ['input', 'timings', 'last_time']
    def __init__(self, inp):
        self.input = inp.read
        self.timings = []
        self.last_time = None

    def grab_next_timing(self):
        self.input()
        this_time = time.time()
        if self.last_time is not None:
            self.timings.append(this_time - self.last_time)
        self.last_time = this_time

    def show_stats(self):
        if not self.timings:
            return
        try:
            def to_bpm(seconds):
                return 60 / seconds

            raw_median = numpy.median(self.timings)
            median = to_bpm(raw_median)
            mean = to_bpm(numpy.mean(self.timings))
            mean_no_outliers = to_bpm(numpy.mean([t for t in self.timings if raw_median * 0.5 <= t <= raw_median * 1.5]))
            print("Median: %3.3f\n"
                  "Mean  : %3.3f\n"
                  "Mean 2: %3.3f (excluding outliers)\n"
                  % (median, mean, mean_no_outliers))
        except ZeroDivisionError:
            print("Dividing by zero - you must have fast fingers")


def main(args):
    last_time = None
    timings = []
    with LinuxSingleCharInput() as inp:
        bpm = BPMClock(inp)
        print("Tap away...")
        while True:
            bpm.grab_next_timing()
            bpm.show_stats()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
