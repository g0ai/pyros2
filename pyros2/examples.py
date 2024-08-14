

import pyros2
import time
from pyros2 import Node
from pyros2 import nd


if __name__=="__main__":
    import sys

    counter = 0

    # trigger = Listener(on_press=on_press)
    # trigger.start()


    if sys.argv[1] == "0":
        while nd.wait(100):
            nums = nd.get("numbers")
            if nums is not None:
                print(nums)
            
            counter += 1

        print("node.py | server closing ...")

    if sys.argv[1] == "1":
        node = Node()
        # node["carstate-jsn"] = {"test":10}
        # node["numbers-str"] = "hello world"
        # node["lidar-pyo"] = None

        while node.alive(wait=100):
            # node.update()
            # print(b.get(last=True), end="\r")
            # node.send(counter)
            # print(node["carstate-jsn"])
            # print(node["numbers-str"])
            joy_data = node["joystick", pyros2.ONCE, pyros2.NEXT]
            if joy_data is not None:
                print(joy_data)
            

            gps_state = node["gps_state"]
            if gps_state is not None:
                print(gps_state)

            
            nums = node["numbers", pyros2.ONCE]
            if nums is not None:
                print("________________")
                print(nums)
                print("again > ", node["numbers", pyros2.NOUPDATE])
                print("again > ", node["numbers", pyros2.NOUPDATE])
                print("last > ", node["numbers", pyros2.NOUPDATE])
            # print(node["lidar-pyo"])
            # print(b.get("letters-str"))
            counter += 1

        print("node.py | server closing ...")

    elif sys.argv[1] == "2":
        b = Node()

        while b.alive(wait=50):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{1000+counter}", "numbers-str")
            b["numbers"] = 1000+counter
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            print(1000+counter)
            counter += 1


        print("node.py | client closing ...")
    
    elif sys.argv[1] == "3":
        b = Node(hz=1000, subscribe=["numbers-str"])

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            b.send(f"{5000+counter}", "letters-str")
            print(b.recv()) # print("Ping pong.")
            # print(b.get())
            counter += 1

        print("node.py | client closing ...")

    
    elif sys.argv[1] == "playback":
        b = Node(file=pyros2.HOME / "joystick" / "test")

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{5000+counter}", "letters-str")
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            # print(None)
            counter += 1

        print("node.py | client closing ...")
    

    
    elif sys.argv[1] == "ssh":
        b = Node(ssh_server="ibrahim@192.168.100.125")
        # b = Node()

        while b.alive(wait=100):
            # b.send_data.append(f"{counter}".encode())
            # b.send(f"{5000+counter}", "letters-str")
            # print(b.recv()) # print("Ping pong.")
            # print(b.get())
            # print(None)
            res = b["numbers"]
            if res is not None:
                print(res)
            # b["numbers"] = counter + 3000
            # print(counter + 3000)
            counter += 1

        print("node.py | client closing ...")