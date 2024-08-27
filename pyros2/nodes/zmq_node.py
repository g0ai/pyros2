import threading
import zmq
import time
import pickle
import dbm.dumb as dbm
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
        self.last_data_list = {}
        self.frozen = {}

        self.ctx = zmq.Context()
        self.ctx.setsockopt(zmq.IPV6,1)

        self.sub_sock = self.ctx.socket(zmq.SUB)
        self.sub_topics = ["ros0", "main"] + subscribe

        for topic in self.sub_topics:
            self.sub_sock.subscribe(topic)
            self.sub_sock.setsockopt(zmq.SUBSCRIBE, topic.encode())
            self.recv_data[topic] = []
            self.last_data[topic] = None # {} if topic_code(topic) == "jsn" else None
            self.last_data_list[topic] = []
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

        for ip in self.ips:
            self._connect_sub(ip)
        

        time.sleep(SLOWDOWN) # switch later to ack to make sure everything is ok
        msg = {"new_node":self.position}
        self.pub_sock.send_multipart([b"ros0", self._make_info().encode(), json.dumps(msg).encode()])

        # logging
        if self.saving:
            self._saving()

        if start:
            self.start()
    

    def _saving(self, tag="temp"):
        if self.saving:
            self.logger["N"] = str(self.send_counter)
            self.logger.close()

        # logging
        # folder_name = Path(__file__).name.split(".")[0]
        folder_name = os.path.basename(inspect.stack()[-1].filename).split(".")[0]
        log_name = time.strftime("%Y%m%d-%H%M%S") + f"_{tag}" # + ".log"
        # log_name = "test"
        output_file = pyros2.HOME / folder_name / log_name
        output_file.parent.mkdir(exist_ok=True, parents=True)
        # self.logger = open(output_file, "wb")
        self.logger = dbm.open(str(output_file), "n") # c for create but not overwrite
        self.logger["N"] = str(-1)
        self.logger["start_time"] = str(time.time())

        self.saving = True

    def _connect_sub(self, ip):
        # self.sub_sock.connect(f"tcp://{self.ip}:{self.port}")
        for i in range(MAX_NODES): # self.position):
            conn = f"tcp://{ip}:{self._node_port(i)}"
            if self.ssh_server is None:
                self.sub_sock.connect(conn)
            else:
                self.tunnels.append(ssh.tunnel_connection(self.sub_sock, conn, ssh_server, password = self.ssh_pass))

    def _node_port(self, pos=None):
        if pos is None:
            pos = self.position
        return MASTER_PORT + 2*pos

    def set_ip(self, ip=MASTER_IP):
        if ip not in self.ips:
            self.ips.append(ip)
            self._connect_sub(ip)


    def pub(self, topic):
        self.pub_topics.append(topic)
        return True
    
    def sub(self, topic):
        if topic not in self.sub_topics:
            self.sub_topics.append(topic)
            self.recv_data[topic] = []
            self.last_data[topic] = None # {} if topic_code(topic) == "jsn" else None
            self.last_data_list[topic] = []
        self.sub_sock.subscribe(topic)
        self.sub_sock.setsockopt(zmq.SUBSCRIBE, topic.encode())
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

    
    def get(self, topic, *configs):
        if topic not in self.sub_topics:
            self.sub(topic)
        autoupdate = True # self.autoupdate
        is_config = len(configs) > 0
        if is_config:
            if pyros2.NOUPDATE in configs:
                return self.last_data[topic]

        else:
            configs = () # None
            self.frozen[topic] = False
            # return None
        update_available = len(self.recv_data[topic]) > 0

        if is_config and pyros2.WAIT in configs and not update_available:
            while len(self.recv_data[topic]) == 0:
                time.sleep(WAIT_TIME)
            update_available = len(self.recv_data[topic]) > 0
            assert update_available
        
        # if autoupdate and len(self.recv_data[topic]) > 0:
        update_success = False
        if update_available:
            update_success = self._update(topic, configs)

        if pyros2.ALL in configs:
            if not update_available:
                self.last_data_list[topic].clear()
            return self.last_data_list[topic]

        return self.last_data[topic] if update_success or pyros2.LAST in configs else None


    def __getitem__(self, index):
        topic = index[0] if isinstance(index, tuple) else index
        configs = (index[i] for i in range(1,len(index))) if isinstance(index, tuple) else ()
        return self.get(topic, *configs)
    

    def set(self, topic, data):
        if topic not in self.pub_topics:
            self.pub(topic)
        self.send(data, topic)

    def __setitem__(self, topic, data):
        self.set(topic, data)

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



    def _update(self, topic, configs=None):
        ## only works for json currently
        n = 1 if configs is not None and pyros2.NEXT in configs else None
        new_data = self.recv(topic, n=n)
        self.last_data_list[topic] = new_data
        if len(new_data) == 0: # and configs is not None and pyros2.ONCE in configs:
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
            # print(self.send_counter, "      ", json.loads(send_info)["time"])
            # pickle.dump(log_dat, self.logger, protocol=pickle.HIGHEST_PROTOCOL)
            self.logger[str(self.send_counter)] = pickle.dumps(log_dat, protocol=pickle.HIGHEST_PROTOCOL)
            self.logger["N"] = str(self.send_counter)
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
    pass