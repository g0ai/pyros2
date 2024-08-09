import threading
import zmq
import time
import pickle
import json

from pynput.keyboard import Key, Listener

import pyros2
from pyros2.rate import Rate
from pyros2.topics import Topic, topic_parse, topic_packer, topic_code

MASTER_IP = "localhost"
MASTER_PORT = 8768

class Node:
    def __init__(self, hz=1000, publish=[], subscribe=[], start=True):
        self.is_alive = False
        # self.rate = Rate(hz=hz)
        self._rate = 1/hz
        # self.protocol = protocol
        # self.mode = mode
        # self.config = config

        self.ip = MASTER_IP # "127.0.0.1"
        self.master_port = MASTER_PORT
        self.position = 1

        self.thread = None
        self.trigger = Listener(on_press=self._trigger)
        # self.trigger.start()

        self.recv_data = {}
        self.send_data = [] # [pickle.dumps("hello")]

        self.last_data = {}

        self.ctx = zmq.Context()

        self.sub_sock = self.ctx.socket(zmq.SUB)
        self.sub_topics = ["ros0", "main"] + subscribe

        for topics in self.sub_topics:
            self.sub_sock.subscribe(topics)
            self.sub_sock.setsockopt(zmq.SUBSCRIBE, topics.encode())
            self.recv_data[topics] = []
            self.last_data[topics] = {} if topic_code(topics) == "jsn" else None
        

        self.pub_sock = self.ctx.socket(zmq.PUB) # SO_REUSEADDR
        self.pub_topics = ["main"] + publish

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
        

        time.sleep(0.5) # switch later to ack to make sure everything is ok
        msg = {"new_node":self.position}
        self.pub_sock.send_multipart([b"ros0", json.dumps(msg).encode()])

        if start:
            self.start()

    def _node_port(self, pos=None):
        if pos is None:
            pos = self.position
        return MASTER_PORT + 2*pos
    
    def sub(self, topic):
        if topic not in self.sub_topics:
            self.sub_topics.append(topic)
            self.recv_data[topic] = []
            self.last_data[topic] = {} if topic_code(topic) == "jsn" else None
        self.sub_sock.subscribe(topic)
        self.sub_sock.setsockopt(zmq.SUBSCRIBE, topic.encode())
    
    def unsub(self, topic):
        self.sub_sock.unsubscribe(topic)
        self.sub_sock.setsockopt(zmq.UNSUBSCRIBE, topic.encode())

    def __del__(self):
        self.sub_sock.close()
        self.pub_sock.close()
        self.ctx.term()

    def __getitem__(self, topic):
        return self.last_data[topic]
    

    def __setitem__(self, topic, data):
        if topic not in self.sub_topics:
            self.sub(topic)
        if topic_code(topic) == "jsn":
            self.last_data[topic].update(data)
        else:
            self.last_data[topic] = data


    def start(self):
        if not self.is_alive:
            self.is_alive = True
            self.thread = threading.Thread(target=self._loop)
            self.thread.start()
        else:
            print(f"Node already running ...")

    def stop(self, force=False):
        if self.is_alive:
            self.is_alive = False
            if force:
                pass
        else:
            print("Node already stopped")

    def alive(self, wait=0):
        if self.is_alive:
            if wait > 0:
                time.sleep(wait * 1e-3)
            return self.is_alive
        else:
            return False
    
    # def get(self, name=None, default=None):
    #     new_data = self.recv()
    #     if len(new_data) > 0:
    #         self.states.update(new_data[-1])
    #     if name is None:
    #         return self.states
    #     elif name in self.states:
    #         return self.states[name]
    #     return default

    def get(self, topic="main", default=None, try_last=True):
        new_data = self.recv(topic)
        if len(new_data) > 0:
            self.last_data[topic] = new_data[-1]
            return new_data[-1]
        # return default
        return self.last_data[topic] if try_last and self.last_data[topic] is not None else default

    def _update(self, topic):
        ## only works for json currently
        new_data = self.recv(topic)
        for data in new_data:
            if topic_code(topic) == "jsn":
                self.last_data[topic].update(data)
            else:
                self.last_data[topic] = data
    
    def update(self, topic=None):
        if topic is None:
            for t in self.sub_topics:
                self._update(t)
        else:
            self._update(topic)
        

    # def set(self, name={}, val=None):
    #     if isinstance(name, dict):
    #         self.states.update(name) 
    #         self.send(self.states)
    #     elif name in self.states:
    #         self.states[name] = val
    #         self.send(self.states)
    #     return None

    def send(self, dat, topic="main"):
        dat = (topic.encode(), self._topic_packer(topic)(dat))
        self.send_data.append(dat)
        return True

    def recv(self, topic="main", last=False):
        dats = self.recv_data[topic].copy()
        self.recv_data[topic].clear()
        return [self._topic_parser(topic)(dat[1]) for dat in dats]
        # return [self._topic_parser(topic)(dats[-1][1])] if len(dats) > 0 else []
    
    def info(self):
        return self.is_alive
    
    def _trigger(self, key):
        try:
            if key.char == 's':
                self.stop()
        except:
            pass
    
    def _topic_parser(self, topic):
        return topic_parse(topic, Topic.PYOBJ)
    

    def _topic_packer(self, topic):
        return topic_packer(topic, Topic.PYOBJ)

    def _loop(self):
        while self.is_alive:
            t1 = time.time()
            try:
                while True:
                    topic = self.sub_sock.recv_string(zmq.NOBLOCK)
                    dat = self.sub_sock.recv()
                    recv_time_ns = time.perf_counter_ns()
                    if dat is not None:
                        if topic == "ros0":
                            msg = json.loads(dat.decode())
                            if "new_node" in msg:
                                self.pub_sock.connect(f"tcp://{self.ip}:{self._node_port(msg['new_node'])}")
                                print(f"New node found at {msg['new_node']}!")
                        elif topic in self.sub_topics:
                            self.recv_data[topic].append((recv_time_ns, dat))
                        # dat_dict = pickle.loads(dat)
                        # print("> ", dat, self.states)
                        # if isinstance(dat, dict):
                        #     self.states.update(dat)
            except:
                pass
            # self.pub_sock.send(b"testing")
            for topic, data in self.send_data:
                self.pub_sock.send_multipart([topic, data])
            self.send_data = []

            if (time.time() - t1) < self._rate:
                time.sleep(max(self._rate - (time.time() - t1), 0))
                    

        print("Node stopped")
        self.__del__()



if __name__=="__main__":
    import sys

    counter = 0

    # trigger = Listener(on_press=on_press)
    # trigger.start()

    if sys.argv[1] == "1":
        node = Node()
        node["carstate-jsn"] = {"test":10}
        node["numbers-str"] = "hello world"

        while node.alive(wait=100):
            node.update()
            # print(b.get(last=True), end="\r")
            # node.send(counter)
            print(node["carstate-jsn"])
            print(node["numbers-str"])
            # print(b.get("letters-str"))
            counter += 1

        print("node.py | server closing ...")

    elif sys.argv[1] == "2":
        b = Node()

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            b.send(f"{1000+counter}", "numbers-str")
            print(b.recv()) # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("node.py | client closing ...")
    
    elif sys.argv[1] == "3":
        b = Node(hz=1000, subscribe=["numbers-str"])

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            b.send(f"{5000+counter}", "letters-str")
            print(b.recv()) # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("node.py | client closing ...")