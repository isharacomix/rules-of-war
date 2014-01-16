# This is a simple sanity checker test... a hello world of sorts. This will
# basically allow us to make sure the testing libraries are working.

import unittest

class TestTests(unittest.TestCase):
    def setUp(self):
        self.a = "Hello "
        self.b = "world"

    def test_addition(self):
        self.assertEqual(self.a+self.b, "Hello world")

