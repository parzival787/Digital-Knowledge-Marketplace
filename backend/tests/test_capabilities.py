"""Availability cannot invent payment support or leak configuration."""
import unittest
from unittest.mock import patch
from services.payments import capabilities as cap


class CapabilityTests(unittest.TestCase):
    def test_unknown_chain_and_missing_configuration_fail_closed(self):
        with patch.object(cap, "chain_routes", side_effect=RuntimeError("secret RPC URL")), patch.object(cap.transak, "configuration", side_effect=ValueError("secret")), patch.object(cap.RazorpayProvider, "quote", side_effect=ValueError("secret")):
            result = cap.payment_capabilities()
        self.assertTrue(all(not r["enabled"] for r in result["routes"].values()))
        self.assertNotIn("secret", str(result))
        self.assertEqual(result["markets"], [])

    def test_funding_is_not_purchase_and_old_deployment_cannot_enable_fiat(self):
        with patch.object(cap, "chain_routes", return_value=([{"address": "market", "token_address": "token", "paused": False}], False)), patch.object(cap.transak, "configuration", return_value=("secret", "secret")), patch.object(cap.RazorpayProvider, "quote", return_value={}):
            result = cap.payment_capabilities()
        self.assertTrue(result["routes"]["fixed_price"]["enabled"])
        self.assertTrue(result["routes"]["auction"]["enabled"])
        self.assertTrue(result["routes"]["transak_buy"]["enabled"])
        self.assertFalse(result["routes"]["transak_buy"]["grants_access"])
        self.assertFalse(result["fiat_configured"])
        self.assertFalse(result["routes"]["upi"]["enabled"])
        self.assertFalse(result["routes"]["crypto_route"]["enabled"])
        self.assertNotIn("secret", str(result))

    def test_paused_market_does_not_disable_auction_recovery(self):
        with patch.object(cap, "chain_routes", return_value=([{"address": "market", "token_address": "token", "paused": True}], True)), patch.object(cap.transak, "configuration", side_effect=ValueError()), patch.object(cap.RazorpayProvider, "quote", return_value={}):
            result = cap.payment_capabilities()
        self.assertFalse(result["routes"]["fixed_price"]["enabled"])
        self.assertFalse(result["fiat_configured"])
        self.assertTrue(result["routes"]["auction"]["enabled"])
