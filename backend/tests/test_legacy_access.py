"""Legacy entitlement tests run without a database or network."""
import os
import unittest
from unittest.mock import Mock, patch
from dotenv import load_dotenv
load_dotenv()
from services import blockchain


class LegacyAccessTests(unittest.TestCase):
    def test_old_purchase_counts_and_registry_validation(self):
        current = Mock(address="0x" + "11" * 20)
        old = Mock(address="0x" + "22" * 20)
        registry = "0x" + "33" * 20
        wallet = "0x" + "44" * 20
        current.functions.hasPurchased.return_value.call.return_value = False
        current.functions.purchaseCount.return_value.call.return_value = 0
        old.functions.hasPurchased.return_value.call.return_value = True
        old.functions.purchaseCount.return_value.call.return_value = 2
        old.functions.knowledgeAsset.return_value.call.return_value = registry
        w3 = Mock()
        w3.eth.chain_id = 80002
        w3.eth.contract.return_value = old
        with patch.object(blockchain, "marketplace", current), patch.object(blockchain, "w3", w3), \
             patch.object(blockchain, "CHAIN_ID", 80002), patch.object(blockchain, "KNOWLEDGE_ASSET_ADDRESS", registry), \
             patch.dict(os.environ, {"LEGACY_MARKETPLACE_ADDRESSES": f"{old.address},{old.address},{current.address}"}):
            self.assertTrue(blockchain.has_purchased(1, wallet))
            self.assertEqual(blockchain.get_purchase_count(1, wallet), 2)
            self.assertEqual(len(blockchain.entitlement_markets()), 2)
            old.functions.knowledgeAsset.return_value.call.return_value = wallet
            with self.assertRaises(ValueError):
                blockchain.has_purchased(1, wallet)
            old.functions.knowledgeAsset.return_value.call.side_effect = RuntimeError("RPC unavailable")
            with self.assertRaises(RuntimeError):
                blockchain.has_purchased(1, wallet)
