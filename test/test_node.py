import unittest

import pyros2
from pyros2 import Node
from pyros2 import node

class TestNodeCase(unittest.TestCase):

    def test_node(self):
        val = 5
        node1 = Node()
        node.set("test", val)
        resp = node1.get("test", pyros2.WAIT)
        self.assertEqual(val, resp)

        # node1.close()
        # node.close()

if __name__ == '__main__':
    unittest.main()
