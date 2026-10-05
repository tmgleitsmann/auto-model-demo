import unittest

from greeting import greet, farewell


class TestGreeting(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("Droid"), "Hello, Droid!")

    def test_farewell(self):
        self.assertEqual(farewell("Droid"), "Goodbye, Droid.")


if __name__ == "__main__":
    unittest.main()
