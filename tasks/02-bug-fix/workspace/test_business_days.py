import unittest
from datetime import date

from business_days import business_days_between


class TestBusinessDays(unittest.TestCase):
    def test_full_week(self):
        # Mon 2026-10-05 .. Sat 2026-10-10: five weekdays
        self.assertEqual(business_days_between(date(2026, 10, 5), date(2026, 10, 10)), 5)

    def test_same_day(self):
        self.assertEqual(business_days_between(date(2026, 10, 7), date(2026, 10, 7)), 1)

    def test_weekend_only(self):
        # Sat 2026-10-10 .. Sun 2026-10-11: no weekdays
        self.assertEqual(business_days_between(date(2026, 10, 10), date(2026, 10, 11)), 0)

    def test_over_sunday(self):
        # Fri 2026-10-09 .. Mon 2026-10-12: Fri and Mon
        self.assertEqual(business_days_between(date(2026, 10, 9), date(2026, 10, 12)), 2)


if __name__ == "__main__":
    unittest.main()
