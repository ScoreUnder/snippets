#!/usr/bin/env python
def rsum(r):
    range_start = r.start
    range_end = range_start + (r.stop - range_start - 1) // r.step * r.step
    return (range_end + range_start) * (range_end - range_start + r.step) // (2 * r.step)
