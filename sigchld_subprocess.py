from __future__ import print_function
from signal import signal, SIGCHLD, SIG_IGN
from subprocess import Popen, PIPE


def test_proc():
    proc = Popen("echo stdout thing; echo >&2 stderr thing; exit 123", shell=True, stdout=PIPE, stderr=PIPE)

    stdout, stderr = proc.communicate()
    exit_code = proc.wait()

    print("stdout:", repr(stdout))
    print("stderr:", repr(stderr))
    print("exit  :", exit_code)


print("Before signal handler change")
test_proc()

signal(SIGCHLD, SIG_IGN)

print("After signal handler change")
test_proc()
