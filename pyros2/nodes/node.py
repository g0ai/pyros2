import threading
import zmq
import time
import pickle
import dbm
import json

import inspect
import os


from zmq import ssh
import paramiko

from pynput.keyboard import Key, Listener

import pyros2
from pyros2.topics import Topic, topic_parse, topic_packer, topic_code


MASTER_IP = "localhost"
MASTER_PORT = 8768
MAX_NODES = 10

WAIT_TIME = 0.001
SLOWDOWN = 0.25

class Node:
    def __init__(self, hz=1000, autoupdate=True, save=False, file=None, ssh_server=None, ssh_pass="", publish=[], subscribe=[], start=True):
        self.autoupdate = autoupdate
        self.is_alive = False
        self.saving = save
        # self.rate = Rate(hz=hz)
        self._rate = 1/hz
        self.start_time = None
        # self.protocol = protocol
        # self.mode = mode
        # self.config = config
        self.ssh_server = ssh_server
        self.ssh_pass = ssh_pass
        self.tunnels = []

        # if ssh_server is not None:
        #     self.tunnel = create_ssh_tunnel(MASTER_PORT, MASTER_PORT)

        self.file = None if file is None else dbm.open(file, "r")
        self.playback_start_time = None
        self.playback_counter = 1

        self.ip = MASTER_IP if self.ssh_server is None else self.ssh_server.split("@")[1] # "127.0.0.1"
        self.ips = [self.ip] # ip4_addresses()
        # print(ip4_addresses())
        self.master_port = MASTER_PORT
        self.position = 1

        self.thread = None
        self.trigger = Listener(on_press=self._trigger)
        # self.trigger.start()

        self.recv_data = {}
        self.send_data = [] # [pickle.dumps("hello")]

        self.last_data = {}
        self.frozen = {}

        self.ctx = zmq.Context()

        self.sub_sock = self.ctx.socket(zmq.SUB)
        self.sub_topics = ["ros0", "main"] + subscribe

        for topic in self.sub_topics:
            self.sub_sock.subscribe(topic)
            self.sub_sock.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.recv_data[topic] = []
            self.last_data[topic] = None # {} if topic_code(topic) == "jsn" else None
            self.frozen[topic] = False
        

        self.pub_sock = self.ctx.socket(zmq.PUB) # SO_REUSEADDR
        self.pub_topics = ["main"] + publish
        self.send_counter = 0


        while True:
            try:
                self.pub_sock.bind(f"tcp://*:{self._node_port()}")
                # if self.ssh_server is None:
                #     self.pub_sock.bind(f"tcp://*:{self._node_port()}")
                # else:
                #     self.tunnel = ssh.tunnel_connection(self.sub_sock, self.conn, ssh_server, password = "password")
                break
            except zmq.ZMQError as e:
                self.position += 1

                # print("Already in use.")
                # self.sub_sock.connect(f"tcp://{self.ip}:{self.node_port}")
        print(f"My node_port: {self._node_port()}")

        # self.sub_sock.connect(f"tcp://{self.ip}:{self.port}")
        for i in range(MAX_NODES): # self.position):
            for ip in self.ips:
                conn = f"tcp://{ip}:{self._node_port(i)}"
                if self.ssh_server is None:
                    self.sub_sock.connect(conn)
                else:
                    self.tunnels.append(ssh.tunnel_connection(self.sub_sock, conn, ssh_server, password = self.ssh_pass))
        

        time.sleep(SLOWDOWN) # switch later to ack to make sure everything is ok
        msg = {"new_node":self.position}
        self.pub_sock.send_multipart([b"ros0", self._make_info().encode(), json.dumps(msg).encode()])

        # logging
        if self.saving:
            # folder_name = Path(__file__).name.split(".")[0]
            folder_name = os.path.basename(inspect.stack()[-1].filename).split(".")[0]
            # log_name = time.strftime("%Y%m%d-%H%M%S") # + ".log"
            log_name = "test"
            output_file = pyros2.HOME / folder_name / log_name
            output_file.parent.mkdir(exist_ok=True, parents=True)
            # self.logger = open(output_file, "wb")
            self.logger = dbm.open(str(output_file), "c")

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
            self.last_data[topic] = None # {} if topic_code(topic) == "jsn" else None
        self.sub_sock.subscribe(topic)
        self.sub_sock.setsockopt(zmq.SUBSCRIBE, topic.encode())
        return True
    
    def pub(self, topic):
        self.pub_topics.append(topic)
        return True
    
    def unsub(self, topic):
        self.sub_sock.unsubscribe(topic)
        self.sub_sock.setsockopt(zmq.UNSUBSCRIBE, topic.encode())
        return True

    def __del__(self):
        self.close()

    def close(self):
        if self.is_alive:
            self.stop()
            time.sleep(SLOWDOWN)
        ##
        if self.saving and self.logger is not None:
            self.logger["N"] = str(self.send_counter)
            self.logger.close()
            # time.sleep(1)
            self.logger = None
        self.sub_sock.close()
        self.pub_sock.close()
        self.ctx.term()

    def __getitem__(self, index):
        topic = index[0] if isinstance(index, tuple) else index
        if topic not in self.sub_topics:
            self.sub(topic)
        autoupdate = self.autoupdate
        if isinstance(index, tuple):
            configs = [index[i] for i in range(1,len(index))]
            # if pyros2.FREEZE in configs and self.last_data[topic] is not None:
            #     if self.frozen[topic]:
            #         return self.last_data[topic]
            #     else:
            #         self.frozen[topic] = True
            # elif pyros2.REFREEZE in configs and self.last_data[topic] is not None:
            #     pass
            # else:
            #     self.frozen[topic] = False
            # autoupdate = False if pyros2.NOUPDATE in configs else autoupdate
            if pyros2.NOUPDATE in configs:
                return self.last_data[topic]

        else:
            configs = () # None
            self.frozen[topic] = False
            # return None
        ok = not autoupdate or len(self.recv_data[topic]) > 0

        if pyros2.WAIT in configs and not ok:
            while len(self.recv_data[topic]) == 0:
                time.sleep(WAIT_TIME)
        
        if autoupdate and len(self.recv_data[topic]) > 0:
            ok = self._update(topic, configs)
        ok = True if pyros2.LAST in configs else ok
        return self.last_data[topic] if ok else None
    

    def __setitem__(self, topic, data):
        if topic not in self.pub_topics:
            self.pub(topic)
        self.send(data, topic)

    # def __setitem__(self, topic, data):
    #     if topic not in self.sub_topics:
    #         self.sub(topic)
    #     if topic_code(topic) == "jsn":
    #         self.last_data[topic].update(data)
    #     else:
    #         self.last_data[topic] = data


    def start(self):
        if not self.is_alive:
            self.is_alive = True
            self.start_time = time.time()
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
        else:
            print(f"Node already running ...")

    def stop(self, force=False):
        if self.is_alive:
            self.is_alive = False
            self.start_time = None
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

    def get(self, topic, *configs):
        if topic not in self.sub_topics:
            self.sub(topic)
        autoupdate = self.autoupdate
        is_config = len(configs) > 0
        if is_config:
            if pyros2.NOUPDATE in configs:
                return self.last_data[topic]

        else:
            configs = () # None
            self.frozen[topic] = False
            # return None
        ok = not autoupdate or len(self.recv_data[topic]) > 0

        if is_config and pyros2.WAIT in configs and not ok:
            while len(self.recv_data[topic]) == 0:
                time.sleep(WAIT_TIME)
        
        if autoupdate and len(self.recv_data[topic]) > 0:
            ok = self._update(topic, configs)
        
        ok = True if pyros2.LAST in configs else ok
        return self.last_data[topic] if ok else None
    

    def set(self, topic, data):
        if topic not in self.pub_topics:
            self.pub(topic)
        self.send(data, topic)

    def _update(self, topic, configs=None):
        ## only works for json currently
        n = 1 if configs is not None and pyros2.NEXT in configs else None
        new_data = self.recv(topic, n=n)
        if len(new_data) == 0 and configs is not None and pyros2.ONCE in configs:
            return False
        for data in new_data:
            if topic_code(topic) != "jsn":
                self.last_data[topic] = data
            else:
                self.last_data[topic].update(data)
        return True
    
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

    def send(self, inp_dat, topic="main", info=None):
        self.send_counter += 1
        send_info = info if info is not None else self._make_info()
        dat = (topic.encode(), send_info.encode(), self._topic_packer(topic)(inp_dat))
        self.send_data.append(dat)
        # log_dat = {"topic": topic, "info": send_info, "data": self._topic_packer(topic)(dat)}
        # self.logger.write(log_dat)
        # json.dump(log_dat, self.logger)
        # log_dat = {"topic": topic, "info": send_info, "data": dat}
        if self.saving:
            log_dat = (topic, send_info, inp_dat)
            # pickle.dump(log_dat, self.logger, protocol=pickle.HIGHEST_PROTOCOL)
            self.logger[str(self.send_counter)] = pickle.dumps(log_dat, protocol=pickle.HIGHEST_PROTOCOL)
            
        return True

    def recv(self, topic="main", last=False, n=None):
        if n is None:
            dats = self.recv_data[topic].copy()
            self.recv_data[topic].clear()
        else:
            n = min(n, len(self.recv_data))
            dats = self.recv_data[topic][:n].copy()
            self.recv_data[topic] = self.recv_data[topic][n:]
        return [self._topic_parser(topic)(dat[1]) for dat in dats]
        # return [self._topic_parser(topic)(dats[-1][1])] if len(dats) > 0 else []
    
    def recv_n(self, topic="main", n=1):
        dat = self.recv_data[topic][:n]
        self.recv_data[topic].clear()
        return [self._topic_parser(topic)(dat[1])]

    def _make_info(self):
        info = {}
        info["time"] = time.time()
        return json.dumps(info) #.encode()

    def info(self):
        return self.is_alive
    
    def _trigger(self, key):
        try:
            if key.char == 's':
                self.stop()
        except:
            pass
    
    def _topic_parser(self, topic):
        return topic_parse(topic, default=Topic.PYOBJ)
    

    def _topic_packer(self, topic):
        return topic_packer(topic, default=Topic.PYOBJ)

    def _loop(self):
        while self.is_alive:
            t1 = time.time()
            try:
                while True:
                    # topic = self.sub_sock.recv_string(zmq.NOBLOCK)
                    # info = self.sub_sock.recv_json(zmq.NOBLOCK)
                    # dat = self.sub_sock.recv()
                    topic, info, dat = self.sub_sock.recv_multipart(zmq.NOBLOCK)
                    topic = topic.decode()
                    info = json.loads(info)
                    # print("> ", topic, info, dat)
                    recv_time_ns = time.perf_counter_ns()
                    if dat is not None:
                        if topic == "ros0":
                            msg = json.loads(dat)
                            if "new_node" in msg:
                                # self.pub_sock.connect(f"tcp://{self.ip}:{self._node_port(msg['new_node'])}")
                                for ip in self.ips:
                                    conn = f"tcp://{ip}:{self._node_port(msg['new_node'])}"
                                    if self.ssh_server is None:
                                        self.sub_sock.connect(conn)
                                    else:
                                        self.tunnels.append(ssh.tunnel_connection(self.sub_sock, conn, self.ssh_server, password = self.ssh_pass))
                                    if self.position != msg['new_node']:
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
            for topic, info, data in self.send_data:
                self.pub_sock.send_multipart([topic, info, data])
                # print("sent ", json.loads(info.decode()))
            self.send_data = []

            if self.file is not None and self.playback_counter < int(self.file["N"]):
                topic, msg_info, dat = pickle.loads(self.file[str(self.playback_counter)])
                dict_info = json.loads(msg_info)
                # self.send(dat, topic) ## remove
                # self.playback_counter += 1 ## remove
                # print(self.playback_counter)

                if self.playback_start_time is None:
                    self.playback_start_time = dict_info["time"]
                else:
                    while (time.time() - self.start_time) > (dict_info["time"] - self.playback_start_time):
                        # print("dict delta time", dict_info["time"] - self.playback_start_time)
                        # print("node delta time", time.time() - self.start_time)
                        # print("++")
                        self.send(dat, topic)
                        self.playback_counter += 1
                        if self.playback_counter >= int(self.file["N"]):
                            break
                        topic, msg_info, dat = pickle.loads(self.file[str(self.playback_counter)])
                        dict_info = json.loads(msg_info)

                print(self.playback_counter)

            if (time.time() - t1) < self._rate:
                time.sleep(max(self._rate - (time.time() - t1), 0))
                    

        print(f"Node {self.position} @ {self._node_port()} stopped.")
        self.close()



if __name__=="__main__":
    import sys

    counter = 0

    # trigger = Listener(on_press=on_press)
    # trigger.start()

    if sys.argv[1] == "1":
        node = Node()
        # node["carstate-jsn"] = {"test":10}
        # node["numbers-str"] = "hello world"
        # node["lidar-pyo"] = None

        while node.alive(wait=100):
            # node.update()
            # print(b.get(last=True), end="\r")
            # node.send(counter)
            # print(node["carstate-jsn"])
            # print(node["numbers-str"])
            joy_data = node["joystick", pyros2.ONCE, pyros2.NEXT]
            if joy_data is not None:
                print(joy_data)
            

            gps_state = node["gps_state"]
            if gps_state is not None:
                print(gps_state)

            
            nums = node["numbers", pyros2.ONCE]
            if nums is not None:
                print("________________")
                print(nums)
                print("again > ", node["numbers", pyros2.NOUPDATE])
                print("again > ", node["numbers", pyros2.NOUPDATE])
                print("last > ", node["numbers", pyros2.NOUPDATE])
            # print(node["lidar-pyo"])
            # print(b.get("letters-str"))
            counter += 1

        print("node.py | server closing ...")

    elif sys.argv[1] == "2":
        b = Node()

        while b.alive(wait=50):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{1000+counter}", "numbers-str")
            b["numbers"] = 1000+counter
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            print(1000+counter)
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

    
    elif sys.argv[1] == "playback":
        b = Node(file=pyros2.HOME / "joystick" / "test")

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{5000+counter}", "letters-str")
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            # print(None)
            counter += 1

        print("node.py | client closing ...")
    

    
    elif sys.argv[1] == "ssh":
        b = Node(ssh_server="ibrahim@192.168.100.125")
        # b = Node()

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{5000+counter}", "letters-str")
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            # print(None)
            res = b["numbers"]
            if res is not None:
                print(res)
            # b["numbers"] = counter + 3000
            # print(counter + 3000)
            counter += 1

        print("node.py | client closing ...")