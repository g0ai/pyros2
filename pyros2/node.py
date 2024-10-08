

from pyros2.nodes.zmq_node import Node

_node = Node()

from pyros2.configs import *

def get(topic, *config):
    return _node.get(topic, *config)

def get_block(topic, *config):
    return _node.get(topic, *(WAIT, *config))

def get_last(topic, *config):
    return _node.get(topic, *(LAST, *config))

def get_next(topic, *config):
    return _node.get(topic, *(NEXT, *config))

def get_all(topic, *config):
    return _node.get(topic, *(ALL, *config))

def get_cached(topic, *config):
    return _node.get(topic, *(NOUPDATE, *config))

def set(topic, val):
    return _node.set(topic, val)

def send(topic, val):
    return _node.set(topic, val)

def wait(ms=0):
    return _node.alive(wait=ms)

def save_as(file):
    return _node._saving(tag=file)

def stop_save():
    return _node._saving()


def set_ip(ip="localhost"):
    return _node.set_ip(ip)


def close():
    return _node.close()


def ok():
    return _node.info()


def record(fname="test"):
    # TODO
    raise Exception


def stop_record():
    # TODO
    raise Exception

def get_nodes():
    # TODO
    raise Exception