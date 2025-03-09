import time
import unittest

from function_skipper import FunctionSkipper


class TestFunctionSkipper(unittest.TestCase):

    def setUp(self):
        self.skipper = FunctionSkipper(1)  # 短いスキップ間隔でテスト

    def test_should_skip_first_call(self):
        self.assertFalse(self.skipper.should_skip("test_id"))

    def test_should_skip_within_interval(self):
        self.skipper.should_skip("test_id")
        self.assertTrue(self.skipper.should_skip("test_id"))

    def test_should_not_skip_after_interval(self):
        self.skipper.should_skip("test_id")
        time.sleep(1.1)  # スキップ間隔より長く待機
        self.assertFalse(self.skipper.should_skip("test_id"))

    def test_should_skip_different_ids(self):
        self.assertFalse(self.skipper.should_skip("id1"))
        self.assertFalse(self.skipper.should_skip("id2"))
        self.assertTrue(self.skipper.should_skip("id1"))
        self.assertTrue(self.skipper.should_skip("id2"))
