

from pyros2 import Node

_node = Node()

ONCE = 2
NEXT = 3

FREEZE = 4
WAIT = 5
REFREEZE = 6

NOUPDATE = 7

def get(topic, *config):
    return _node.get(topic, config)

def set(topic, val):
    return _node.set(topic, val)

def wait(ms=0):
    return _node.alive(wait=ms)


def ok():
    return _node.alive(wait=0)