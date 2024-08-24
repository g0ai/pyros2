# PyROS2
A minimalistic pythonic module as an alternative to ROS.

## About
In order to make use of all the ROS features (pub/sub, recording and playback, autodiscovery, remote machine communication, standarized topics, etc.), `pyros2` was developed using the `zmq` backend to work flawlessly out of the box.

Eventually, `pyros2` will support `ros2` discovery and chatting.

## Instalation

The python package can simply be installed using pip:
```
pip install git+https://github.com/g0ai/pyros2.git@main
```

## Usage

Here is a simple example to publish a topic from a script:
```py
# pub.py
from pyros2 import node

new_counter = 500
node.set("counter", new_counter)
print(f"Sent {new_counter} on topic 'counter'")
# Sent 500 on topic 'counter'

```
```py
# sub.py
from pyros2 import node

counter = node.get("counter", node.WAIT)
print(f"Recieved {counter} on topic 'counter'")
# Recieved 500 on topic 'counter'
```

### Flags

The following flags are supported:

- `ONCE`: read new value only once; next call is either a newer value or `None` (default is last received value)
- `NEXT`: read the next recieved value, even if much newer values exist (default is reading the latest value)
- `WAIT`: wait until a message is recieved (default is non-blocking)
- `NOUPDATE`: get the last returned cached value (default is check for new and get latest)
- `LAST`: get the last value regardless if new or old (default is None when there is no new value)

## Licensing
Initially developed by Ibrahim Abdulhafiz with support from the G0 Lab team.