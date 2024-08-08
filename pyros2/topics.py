import pickle
import json

TOPIC_SPLIT = "-"


class Topic:
    PYOBJ = 1
    STRING = 2
    JSON = 3


def null(x):
    return x


def topic_packer(topic, default):
    ts = topic.split(TOPIC_SPLIT)
    topic_code = ts[-1] if len(ts) > 1 and len(ts[-1]) == 3 else None
    default = default if topic_code is None else None
    if default == Topic.PYOBJ or topic_code == "pyo":
        return pickle.dumps
    elif default == Topic.STRING or topic_code == "str":
        return lambda x : x.encode()
    elif default == Topic.JSON or topic_code == "jsn":
        return json.dumps
    else:
        return null


# def data_encode(data, topic_type):
#     fn = topic_encode(topic_type)
#     return fn(data).encode()


def topic_parse(topic, default=Topic.PYOBJ):
    ts = topic.split(TOPIC_SPLIT)
    topic_code = ts[-1] if len(ts) > 1 and len(ts[-1]) == 3 else None
    default = default if topic_code is None else None
    if default == Topic.PYOBJ or topic_code == "pyo":
        return pickle.loads
    elif default == Topic.STRING or topic_code == "str":
        return lambda x : x.decode()
    elif default == Topic.JSON or topic_code == "jsn":
        return json.loads
    else:
        return null