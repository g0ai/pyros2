import threading
import zmq
import time
import pickle

from pynput.keyboard import Key, Listener

import ros0
from ros0.rate import Rate

class Bridge:
    def __init__(self, hz=10, protocol=ros0.ZMQ, mode=ros0.PUBSUB, config=ros0.SERVER):
        self.is_alive = False
        self.rate = Rate(hz=hz)
        self.protocol = protocol
        self.mode = mode
        self.config = config

        self.ip = "localhost" # "127.0.0.1"
        self.port = 8768

        self.thread = None
        self.trigger = Listener(on_press=self._trigger)
        # self.trigger.start()

        self.recv_data = []
        self.send_data = [pickle.dumps("hello")]

        if self.protocol == ros0.ZMQ:
            self.ctx = zmq.Context()
            if self.mode & ros0.SUB:
                self.sub_sock = self.ctx.socket(zmq.SUB)
                self.sub_topic = "ros0"
                self.sub_sock.subscribe(self.sub_topic)
                self.sub_sock.setsockopt(zmq.SUBSCRIBE, b"")
                if self.config & ros0.SERVER:
                    self.sub_sock.connect(f"tcp://{self.ip}:{self.port}")
                elif self.config & ros0.CLIENT:
                    self.sub_sock.bind(f"tcp://*:{self.port+1}")


            if self.mode & ros0.PUB:
                self.pub_sock = self.ctx.socket(zmq.PUB)
                self.pub_topic = "ros0"
                if self.config & ros0.SERVER:
                    self.pub_sock.connect(f"tcp://{self.ip}:{self.port+1}")
                elif self.config & ros0.CLIENT:
                    self.pub_sock.bind(f"tcp://*:{self.port}")


    def __del__(self):
        if self.protocol == ros0.ZMQ:
            if self.mode & ros0.SUB:
                self.sub_sock.close()
            if self.mode & ros0.PUB:
                self.pub_sock.close()
            self.ctx.term()

    def start(self):
        if not self.is_alive:
            self.is_alive = True
            self.thread = threading.Thread(target=self._loop)
            self.thread.start()
        else:
            print("thread already running")

    def stop(self, force=False):
        if self.is_alive:
            self.is_alive = False
            if force:
                pass
        else:
            print("thread already stopped")

    def alive(self, wait=0):
        if self.is_alive:
            if wait > 0:
                time.sleep(wait * 1e-3)
            return self.is_alive
        else:
            return False
    

    def send(self, dat):
        dat = [self.pub_topic.encode(), pickle.dumps(dat)]
        self.send_data.extend(dat)
        return True

    def recv(self, last=False):
        dat = self.recv_data
        self.recv_data = []
        return [pickle.loads(d) for d in dat]
    
    def _trigger(self, key):
        try:
            if key.char == 's':
                self.stop()
        except:
            pass

    def _loop(self):
        while self.is_alive:
            self.rate.limit_rate()
            if self.mode & ros0.SUB:
                try:
                    topic = self.sub_sock.recv_string(zmq.NOBLOCK)
                    dat = self.sub_sock.recv()
                    if dat is not None:
                        self.recv_data.append(dat)
                except:
                    pass
            if self.mode & ros0.PUB:
                # self.pub_sock.send(b"testing")
                if len(self.send_data) > 0:
                    self.pub_sock.send_multipart(self.send_data)
                    self.send_data = []
                    

        print("thread stopped")



if __name__=="__main__":
    import sys

    counter = 0

    # trigger = Listener(on_press=on_press)
    # trigger.start()

    if sys.argv[1] == "1":
        b = Bridge(hz=1000, protocol=ros0.ZMQ, mode=ros0.PUBSUB, config=ros0.SERVER)
        b.start()

        while b.alive(wait=100):
            # print(b.get(last=True), end="\r")
            b.send(counter)
            print(b.recv())
            counter += 1

        print("bridge.py | server closing ...")

    elif sys.argv[1] == "2":
        b = Bridge(hz=1000, protocol=ros0.ZMQ, mode=ros0.PUBSUB, config=ros0.CLIENT)
        b.start()

        while b.alive(wait=1):
            # b.send_data.append(f"{counter}".encode())
            b.send(counter)
            # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("bridge.py | client closing ...")