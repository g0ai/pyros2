

from pyros2 import Node

_node = Node()

from pyros2.configs import *

def get(topic, *config):
    return _node.get(topic, *config)

def set(topic, val):
    return _node.set(topic, val)

def send(topic, val):
    return _node.set(topic, val)

def wait(ms=0):
    return _node.alive(wait=ms)


def close():
    return _node.close()


def ok():
    return _node.alive(wait=0)


def record(fname="test"):
    # TODO
    raise Exception


def stop_record():
    # TODO
    raise Exception

def get_nodes():
    # TODO
    raise Exception