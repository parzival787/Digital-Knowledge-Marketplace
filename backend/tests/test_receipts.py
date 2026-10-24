"""Offline receipt tests: no database, RPC calls, signatures or broadcasts."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from web3 import Web3
from web3.exceptions import TransactionNotFound
from services.payments.settlement import confirmed_receipt


class ReceiptTests(unittest.TestCase):
    def test_canonical_receipt_and_reorg_boundaries(self):
        tx_hash = "0x" + "11" * 32
        receipt = SimpleNamespace(blockNumber=100, blockHash=bytes(32), status=1,
                                  transactionHash=Web3.to_bytes(hexstr=tx_hash))
        w3 = Mock()
        w3.eth.block_number = 101
        w3.eth.get_block.return_value = SimpleNamespace(hash=bytes(32))
        w3.eth.get_transaction_receipt.return_value = receipt
        self.assertTrue(confirmed_receipt(w3, tx_hash, receipt))
        w3.eth.block_number = 100
        self.assertFalse(confirmed_receipt(w3, tx_hash, receipt))
        w3.eth.block_number = 101
        for change in [{"blockHash": b"x" * 32}, {"blockNumber": 101},
                       {"status": 0}, {"transactionHash": b"y" * 32}]:
            with self.subTest(change=change):
                w3.eth.get_transaction_receipt.return_value = SimpleNamespace(**(vars(receipt) | change))
                with self.assertRaises(ValueError):
                    confirmed_receipt(w3, tx_hash, receipt)
        w3.eth.get_transaction_receipt.return_value = receipt
        w3.eth.get_block.return_value.hash = b"z" * 32
        with self.assertRaises(ValueError):
            confirmed_receipt(w3, tx_hash, receipt)
        w3.eth.get_block.return_value.hash = bytes(32)
        w3.eth.get_transaction_receipt.side_effect = TransactionNotFound("missing")
        with self.assertRaises(TransactionNotFound):
            confirmed_receipt(w3, tx_hash, receipt)
