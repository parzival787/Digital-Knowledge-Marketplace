import unittest
from decimal import Decimal
from services.asset_price import asset_price


class AssetPriceTests(unittest.TestCase):
    def test_cents_and_existing_whole_prices_are_exact(self):
        for value in [0.01, 0.29, 0.99, 1, 7, 100]:
            self.assertEqual(asset_price(value), Decimal(str(value)))
            self.assertEqual(asset_price(value) * 1000000, int(Decimal(str(value)) * 1000000))

    def test_invalid_prices_are_rejected(self):
        for value in [0, -1, 0.001, 1.001, 100.01, True, None, "0.01", float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                asset_price(value)
