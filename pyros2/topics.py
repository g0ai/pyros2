import pickle
import json


class Topic:
    PYOBJ = 1
    STRING = 2
    JSON = 3


def null(x):
    return x


def topic_packer(topic_type):
    if topic_type == Topic.PYOBJ:
        return pickle.dumps
    elif topic_type == Topic.STRING:
        return null
    elif topic_type == Topic.JSON:
        return json.dumps
    else:
        return null


# def data_encode(data, topic_type):
#     fn = topic_encode(topic_type)
#     return fn(data).encode()


def topic_parse(topic_type):
    if topic_type == Topic.PYOBJ:
        return pickle.loads
    elif topic_type == Topic.STRING:
        return null
    elif topic_type == Topic.JSON:
        return json.loads
    else:
        return null