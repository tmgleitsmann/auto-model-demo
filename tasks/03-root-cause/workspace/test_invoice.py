import unittest

from invoice import invoice_total, line_total


class TestInvoiceTotals(unittest.TestCase):
    """Expected values are exact money math: round half up, to the cent."""

    def test_line_totals(self):
        self.assertEqual(line_total(19.99, 3), 59.97)

    def test_invoice_totals(self):
        cases = [
            ([(19.99, 3), (4.99, 1)], 70.73),
            ([(2.675, 1)], 2.92),
            ([(0.10, 3), (0.20, 1)], 0.54),
            ([(1.005, 2)], 2.19),
        ]
        for lines, expected in cases:
            with self.subTest(lines=lines):
                self.assertEqual(invoice_total(lines), expected)


if __name__ == "__main__":
    unittest.main()
