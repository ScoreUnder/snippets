from threading import Thread, current_thread
import time
import prctl

def sleeper():
    prctl.prctl(prctl.NAME, current_thread().name)
    while True:
        time.sleep(10)
        print "sleeping"

threads = [Thread(target=sleeper, name="Sleeper01"),
           Thread(target=sleeper, name="Sleeper02"),
           Thread(target=sleeper, name="something else")]
for t in threads:
    t.start()
for t in threads:
    t.join()
