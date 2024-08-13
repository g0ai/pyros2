from pathlib import Path

HOME = Path.home() / "pyros2"

from pyros2.node import Node
from pyros2.threaded import Threaded

ONCE = 2
NEXT = 3

# # protocol
# ZMQ = 1
# WEBSOCKET = 2
# ROS = 3
# ROS2 = 4


# # mode
# PUB = 1
# SUB = 2
# PUBSUB = 3


# # type
# SERVER = 1
# CLIENT = 2
# ALT = 3