
import pyros2
from pyros2 import node

import dbm.dumb as dbm
import glob
import os
import pickle
import json
import time

def replay_dbm(node_name, tag="temp"):
    patt = str(pyros2.HOME / node_name / f"*_{tag}.*")
    file_paths = sorted(glob.glob(patt))
    # print(patt, file_paths)

    if len(file_paths) > 0:
        file_path = file_paths[-1][:-4]
        file = dbm.open(file_path, "r")

        num_of_msg = int(file["N"])
        log_start_time = float(file["start_time"])
        start_time = time.time()
        # delta_time = start_time - log_start_time

        # print("num_of_msg", num_of_msg)
        # print("log_start_time   ", log_start_time)

        # values = [file[key] for key in file.keys()]
        # print(file.keys())

        for id in file.keys():
            if id.isdigit():
                topic, msg_info, dat = pickle.loads(file[id])
                dict_info = json.loads(msg_info)
                recv_time = float(dict_info["time"])
                # print(recv_time)
                if time.time() - start_time < (recv_time - log_start_time):
                    time.sleep(max(0, (recv_time - log_start_time) - (time.time() - start_time)))
                
                # print(topic, dat)
                node.send(topic, dat)