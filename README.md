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

node.save_as("test")

new_counter = 500
node.send("counter", new_counter)
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

If you want to replay what `pub.py` published, simply run the following in the command line:
```bash
# pyros2 [-r/--replay] <python file name> <save_as tag>
pyros2 --replay pub test
```

### Flags

The following flags are supported:


- `LAST`: get the last value regardless if new or old (default is None when there is no new value)
- `NEXT`: read the next recieved value, even if much newer values exist (default is reading the latest value)
- `WAIT`: wait until a message is recieved (default is non-blocking)
- `NOUPDATE`: get the last returned cached value (default is check for new and get latest)
- `ALL`: read all new values as a list (default is just get the last value)

## Licensing
Initially developed by Ibrahim Abdulhafiz with support from the G0 Lab team.