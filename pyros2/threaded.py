import threading
import time

from pynput.keyboard import Key, Listener

from pyros2.extra.rate import Rate

"""
# template structure
class X(Threaded):
    def init(self):
        pass
    
    def close(self):
        pass
    
    def get(self):
        pass

    def set(self):
        pass

    def iter(self):
        pass
"""

class Threaded:

    def init(self):
        pass


    def iter(self):
        pass


    def close(self):
        pass


    def get(self):
        pass

    def set(self):
        pass


    ##########################################################


    def __init__(self, hz=1000, threaded=True):
        self.is_alive = False
        # self._rate = Rate(hz=hz)
        self._rate = 1/hz
        self.threaded = threaded
        self.iter_time = None

        self._thread = None
        self.trigger = Listener(on_press=self._trigger)
        # self.trigger.start()

    def __del__(self):
        self.stop()
        self.close()
        pass


    def start(self):
        if not self.is_alive:
            self.is_alive = True
            if self.threaded:
                self._thread = threading.Thread(target=self._loop)
                self._thread.daemon = True
                self._thread.start()
                print(f"thread {self.__class__.__name__} starting ...")
            else:
                self._loop()
        else:
            print(f"thread {self.__class__.__name__} already running")


    def stop(self, wait=100, force=False):
        if self.is_alive:
            print(f"thread {self.__class__.__name__} stopping ...")
            self.is_alive = False
            time.sleep(wait * 1e-3)
            if force:
                pass
        else:
            print(f"thread {self.__class__.__name__} already stopped")


    def alive(self, wait=0):
        if self.is_alive:
            if wait > 0:
                time.sleep(wait * 1e-3)
            return self.is_alive
        else:
            return False
    

    def do_break(self):
        self.is_alive = False
    
    def _trigger(self, key):
        try:
            if key.char == 's':
                self.stop()
        except:
            pass

    def _loop(self):
        while self.is_alive:
            # self._rate.limit_rate()
            t1 = time.time()
            self.iter()
            self.iter_time = time.time() - t1
            if self.iter_time < self._rate:
                time.sleep(max(self._rate - (time.time() - t1), 0))

        print(f"thread {self.__class__.__name__} succesfully stopped.")



if __name__=="__main__":
    b = Threaded(hz=1000)
    b.start()

    while b.alive(wait=100):
        print("Ping.")

    print("threaded.py | server closing ...")
