import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from services.payments.market_profiles import market_profile, parse_units
from verify_transak_token import verify


class MarketProfileTests(unittest.TestCase):
    def test_exact_amounts_and_invalid_inputs(self):
        self.assertEqual(parse_units("10", 6), 10_000_000)
        self.assertEqual(parse_units("10.000000000000000001", 18), 10**19 + 1)
        self.assertEqual(parse_units(str(2**256 - 1), 0), 2**256 - 1)
        for value, decimals in [("0.0000001", 6), ("1e6", 6), ("-1", 18),
                                ("NaN", 18), (1.1, 18), (str(2**256), 0), ("1", True), ("1", 78)]:
            with self.assertRaises(ValueError):
                parse_units(value, decimals)

    def test_profiles_preserve_distinct_denominations_and_fail_closed(self):
        address, registry, current = "0x" + "11"*20, "0x" + "22"*20, "0x" + "33"*20
        market, token, splitter = Mock(), Mock(), Mock()
        market.address = address
        market.functions.knowledgeAsset.return_value.call.return_value = registry
        market.functions.usdc.return_value.call.return_value = current
        market.functions.paused.return_value.call.return_value = False
        market.functions.royaltySplitter.return_value.call.return_value = registry
        market.functions.totalAuctionsCreated.return_value.call.return_value = 0
        splitter.functions.usdc.return_value.call.return_value = current
        splitter.functions.marketplace.return_value.call.return_value = address
        token.functions.name.return_value.call.return_value = "Test token"
        w3 = SimpleNamespace(eth=Mock(chain_id=80002, block_number=100))
        w3.eth.get_code.return_value = b"code"
        for decimals, symbol in [(6, "MockUSDC"), (18, "TRNSK")]:
            w3.eth.contract.side_effect = [market, token, splitter]
            token.functions.decimals.return_value.call.return_value = decimals
            token.functions.symbol.return_value.call.return_value = symbol
            profile = market_profile(w3, address, registry, current, 99)
            self.assertEqual((profile["decimals"], profile["symbol"], profile["legacy"]), (decimals, symbol, True))
            token.functions.decimals.return_value.call.assert_called_with(block_identifier=99)
        w3.eth.chain_id = 1
        with self.assertRaises(ValueError): market_profile(w3, address, registry, current)

    def test_verification_rejects_wrong_chain_and_missing_code(self):
        w3 = SimpleNamespace(eth=Mock(chain_id=1))
        with self.assertRaises(ValueError): verify(w3)
        w3.eth.chain_id, w3.eth.block_number = 80002, 100
        w3.eth.get_code.return_value = b""
        with self.assertRaises(ValueError): verify(w3)
        w3.eth.send_raw_transaction.assert_not_called()

    def test_persisted_legacy_and_new_amounts_do_not_reinterpret_units(self):
        from services.payments.settlement import order_amount
        self.assertEqual(order_amount(SimpleNamespace(payment_amount_base_units=None, amount_usdc=10)), 10_000_000)
        self.assertEqual(order_amount(SimpleNamespace(payment_amount_base_units="10000000000000000001", amount_usdc=10)), 10**19+1)
        with self.assertRaises(ValueError): order_amount(SimpleNamespace(payment_amount_base_units=str(2**256), amount_usdc=10))
