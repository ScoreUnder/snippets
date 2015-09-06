# it's forked
import cPickle
import os
import sys
import tempfile

class Fork(object):
    def __init__(self):
        self._comm_file = tempfile.TemporaryFile(dir="/dev/shm")
        self.pid = os.fork()

    def is_parent(self):
        return self.pid != 0

    def join(self, value):
        if self.pid:
            os.waitpid(self.pid, 0)
            try:
                self._comm_file.seek(0)
                child_val = cPickle.load(self._comm_file)
                self._comm_file.close()
                return (value, child_val)
            except EOFError:
                return (value, None)
        else:
            cPickle.dump(value, self._comm_file)
            self._comm_file.close()
            sys.exit(0)
