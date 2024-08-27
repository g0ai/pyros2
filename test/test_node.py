import unittest

import pyros2
from pyros2.nodes.zmq_node import Node
from pyros2 import node
import time

class TestNodeCase(unittest.TestCase):

    def test_node(self):
        print("Testing")
        val = 5
        node1 = Node()
        node.send("test", val)
        resp = node1.get("test", pyros2.WAIT)
        self.assertEqual(val, resp)


        print("Done general Testing")

        # node1.close()
        # node.close()
    


    def test_update(self):
        print("Testing Update")
        val = 5
        node1 = Node()
        node.send("test", val)
        tmp = node1.get("test", pyros2.WAIT)
        node.send("test", 0)

        resp = node1.get("test", pyros2.NOUPDATE)

        self.assertEqual(tmp, resp)
        self.assertEqual(val, resp)

        print("Done testing Update")

        # node1.close()
        # node.close()
    

    def test_wait(self):
        print("Testing Wait")
        val1 = 6
        val2 = 10
        node1 = Node()
        node.send("test", 0)
        node.send("test", val1)
        node.send("test", val2)
        
        tmp = node1.get("test", pyros2.WAIT, pyros2.NEXT)
        resp1 = node1.get("test", pyros2.NEXT)
        self.assertEqual(val1, resp1)
        resp2 = node1.get("test", pyros2.NEXT)
        self.assertEqual(val2, resp2)

        print("Done testing Wait")

    def test_all(self):
        print("Testing All")
        val1 = 6
        val2 = 10
        node1 = Node()
        node.send("test", 0)
        node.send("test", val1)
        node.send("test", val2)
        
        resp = node1.get("test", pyros2.WAIT, pyros2.ALL)
        self.assertEqual(val1, resp[1])
        self.assertEqual(val2, resp[2])

        print("Done Testing All")

if __name__ == '__main__':
    unittest.main()
