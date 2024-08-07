import threading
import zmq
import time
import pickle
import json

from pynput.keyboard import Key, Listener

import pyros2
from pyros2.rate import Rate

MASTER_IP = "localhost"
MASTER_PORT = 8768

class Node:
    def __init__(self, hz=10, publish=[], subscribe=[]):
        self.is_alive = False
        self.rate = Rate(hz=hz)
        # self.protocol = protocol
        # self.mode = mode
        # self.config = config

        self.ip = MASTER_IP # "127.0.0.1"
        self.master_port = MASTER_PORT
        self.position = 1

        self.thread = None
        self.trigger = Listener(on_press=self._trigger)
        # self.trigger.start()

        self.recv_data = []
        self.send_data = [pickle.dumps("hello")]

        self.ctx = zmq.Context()

        self.sub_sock = self.ctx.socket(zmq.SUB)
        self.sub_topics = ["ros0", "info"] + subscribe

        for topics in self.sub_topics:
            self.sub_sock.subscribe(topics)
            self.sub_sock.setsockopt(zmq.SUBSCRIBE, topics.encode())
        

        self.pub_sock = self.ctx.socket(zmq.PUB) # SO_REUSEADDR
        self.pub_topics = ["info"] + publish

        while True:
            try:
                self.sub_sock.bind(f"tcp://*:{self._node_port()}")
                break
            except zmq.ZMQError as e:
                self.position += 1

                # print("Already in use.")
                # self.sub_sock.connect(f"tcp://{self.ip}:{self.node_port}")
        print(f"New node_port: {self._node_port()}")

        # self.sub_sock.connect(f"tcp://{self.ip}:{self.port}")
        for i in range(self.position):
            self.pub_sock.connect(f"tcp://{self.ip}:{self._node_port(i)}")
        

        time.sleep(0.1)
        msg = {"new_node":self.position}
        self.pub_sock.send_multipart([b"ros0", json.dumps(msg).encode()])

    def _node_port(self, pos=None):
        if pos is None:
            pos = self.position
        return MASTER_PORT + 2*pos

    def __del__(self):
        self.sub_sock.close()
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
    
    def get(self, name=None, default=None):
        new_data = self.recv()
        if len(new_data) > 0:
            self.states.update(new_data[-1])
        if name is None:
            return self.states
        elif name in self.states:
            return self.states[name]
        return default

    def set(self, name={}, val=None):
        if isinstance(name, dict):
            self.states.update(name) 
            self.send(self.states)
        elif name in self.states:
            self.states[name] = val
            self.send(self.states)
        return None

    def send(self, dat, topic="info"):
        dat = [topic.encode(), pickle.dumps(dat)]
        self.send_data.extend(dat)
        return True

    def recv(self, last=False):
        dat = self.recv_data
        self.recv_data = []
        return [pickle.loads(d) for d in dat]
    
    def info(self):
        return self.is_alive
    
    def _trigger(self, key):
        try:
            if key.char == 's':
                self.stop()
        except:
            pass

    def _loop(self):
        while self.is_alive:
            self.rate.limit_rate()
            try:
                while True:
                    topic = self.sub_sock.recv_string(zmq.NOBLOCK)
                    dat = self.sub_sock.recv()
                    if dat is not None:
                        if topic == "ros0":
                            msg = json.loads(dat.decode())
                            if "new_node" in msg:
                                self.pub_sock.connect(f"tcp://{self.ip}:{self._node_port(msg["new_node"])}")
                        elif topic in self.sub_topics:
                            self.recv_data.append(dat)
                        # dat_dict = pickle.loads(dat)
                        # print("> ", dat, self.states)
                        # if isinstance(dat, dict):
                        #     self.states.update(dat)
            except:
                pass
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
        b = Node(hz=1000)
        b.start()

        while b.alive(wait=100):
            # print(b.get(last=True), end="\r")
            # b.send(counter)
            print(b.recv())
            counter += 1

        print("bridge.py | server closing ...")

    elif sys.argv[1] == "2":
        b = Node(hz=1000)
        b.start()

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            b.send(1000+counter)
            print(b.recv()) # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("bridge.py | client closing ...")
    
    elif sys.argv[1] == "3":
        b = Node(hz=1000)
        b.start()

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            b.send(5000+counter)
            print(b.recv()) # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("bridge.py | client closing ...")