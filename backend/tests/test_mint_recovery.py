import unittest
from unittest.mock import Mock
from services.mint_recovery import find_mint

class MintRecoveryTests(unittest.TestCase):
    def test_matches_both_content_ids_and_creator_at_same_block(self):
        registry = Mock()
        registry.functions.totalMinted.return_value.call.return_value = 3
        rows = {1: ("file", "wrong", 10000, "0xABC"),
                2: ("file", "meta", 10000, "0xother"),
                3: ("file", "meta", 10000, "0xABC")}
        def asset(token):
            result = Mock()
            result.call.side_effect = lambda block_identifier: rows[token] if block_identifier == 123 else self.fail("Unpinned lookup")
            return result
        registry.functions.getAsset.side_effect = asset
        self.assertEqual(find_mint(registry, 123, "file", "meta", "0xabc"), 3)
        self.assertIsNone(find_mint(registry, 123, "other", "meta", "0xabc"))
        registry.functions.totalMinted.return_value.call.assert_called_with(block_identifier=123)

    def test_rpc_failure_and_oversized_catalog_never_report_not_minted(self):
        registry = Mock()
        registry.functions.totalMinted.return_value.call.return_value = 101
        with self.assertRaises(ValueError): find_mint(registry, 1, "file", "meta", "wallet")
        registry.functions.totalMinted.return_value.call.side_effect = RuntimeError("RPC unavailable")
        with self.assertRaises(RuntimeError): find_mint(registry, 1, "file", "meta", "wallet")
