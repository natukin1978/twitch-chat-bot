import unittest

from config_helper import read_config


class TestConfigHelper(unittest.TestCase):
    def test_read_config(self):
        expected = {
            "a": 1,
            "b": "2",
            "c": False,
        }
        actual = read_config("test_data/test_config_helper.json")
        self.assertEqual(expected, actual)
