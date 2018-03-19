def fib():
    n, m = 1, 0
    while True:
        yield m
        n, m = n + m, n

class IteratorCache(object):
    def __init__(self, iterator):
        self._iter = iterator
        self._cache = []

    def __getitem__(self, index):
        if index < 0:
            raise IndexError("Index out of bounds")
        if not isinstance(index, int):
            raise IndexError("Non-integral index")
        self._ensure_cache(index)
        return self._cache[index]

    def _ensure_cache(self, index):
        try:
            while len(self._cache) <= index:
                self._cache.append(next(self._iter))
        except StopIteration:
            pass
