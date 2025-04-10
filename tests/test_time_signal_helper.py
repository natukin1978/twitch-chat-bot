import datetime
import unittest

from time_signal_helper import calculate_next_time


class TestCalculateNextTime(unittest.TestCase):

    def test_interval_30_before(self):
        now = datetime.datetime(2025, 4, 10, 10, 15, 0)
        interval = 30
        expected = datetime.datetime(2025, 4, 10, 10, 30, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_30_on(self):
        now = datetime.datetime(2025, 4, 10, 10, 30, 0)
        interval = 30
        expected = datetime.datetime(2025, 4, 10, 11, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_30_after(self):
        now = datetime.datetime(2025, 4, 10, 10, 45, 0)
        interval = 30
        expected = datetime.datetime(2025, 4, 10, 11, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_60_before(self):
        now = datetime.datetime(2025, 4, 10, 10, 15, 0)
        interval = 60
        expected = datetime.datetime(2025, 4, 10, 11, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_60_on(self):
        now = datetime.datetime(2025, 4, 10, 11, 0, 0)
        interval = 60
        expected = datetime.datetime(2025, 4, 10, 12, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_60_after(self):
        now = datetime.datetime(2025, 4, 10, 11, 45, 0)
        interval = 60
        expected = datetime.datetime(2025, 4, 10, 12, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_60_next_day(self):
        now = datetime.datetime(2025, 4, 10, 23, 55, 0)
        interval = 60
        expected = datetime.datetime(2025, 4, 11, 0, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_15(self):
        now = datetime.datetime(2025, 4, 10, 10, 7, 0)
        interval = 15
        expected = datetime.datetime(2025, 4, 10, 10, 15, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)

    def test_interval_1(self):
        now = datetime.datetime(2025, 4, 10, 10, 59, 30)
        interval = 1
        expected = datetime.datetime(2025, 4, 10, 11, 0, 0)
        self.assertEqual(calculate_next_time(now, interval), expected)
