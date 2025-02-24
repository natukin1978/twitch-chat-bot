import unittest

from text_helper import read_text, read_text_set, read_texts


class TestTextHelper(unittest.TestCase):
    def test_read_text(self):
        actual = read_text("test_data/test_text_helper.txt")
        self.assertEqual("c\nb\nc\na\na\nb\n", actual)

    def test_read_texts(self):
        actual = read_texts("test_data/test_text_helper.txt")
        self.assertEqual(["c", "b", "c", "a", "a", "b"], actual)

    def test_read_text_set(self):
        actual = read_text_set("test_data/test_text_helper.txt")
        self.assertEqual({"a", "b", "c"}, actual)
