import unittest
from unittest.mock import MagicMock, patch
from services import activity


class ActivityTests(unittest.TestCase):
    def test_bounded_chain_history_filters_by_wallet(self):
        w3 = MagicMock()
        w3.eth.chain_id = 80002
        w3.eth.block_number = 5002
        market = w3.eth.contract.return_value
        wallet = "0x" + "11" * 20
        other = "0x" + "22" * 20
        third = "0x" + "33" * 20
        market.events.PurchaseCompleted.return_value.get_logs.return_value = [
            {"args":{"listingId":1,"tokenId":10,"buyer":wallet,"amount":5000000},"blockNumber":4500,"transactionHash":bytes(32),"logIndex":0},
            {"args":{"listingId":2,"tokenId":11,"buyer":other,"amount":7000000},"blockNumber":4600,"transactionHash":bytes(32),"logIndex":1},
            {"args":{"listingId":3,"tokenId":12,"buyer":third,"amount":8000000},"blockNumber":4700,"transactionHash":bytes(32),"logIndex":2},
        ]
        market.functions.listings.side_effect = lambda listing: MagicMock(call=lambda: (0,0,wallet if listing == 2 else other))
        with patch.object(activity.blockchain,"w3",w3), patch.dict("os.environ", {"RPC_LOG_PAGE_SIZE":"2000"}):
            result = activity.account_activity(wallet)
        self.assertEqual([row["kind"] for row in result["activity"]],["sale","purchase"])
        self.assertEqual(result["next_before_block"],3000)
        market.events.PurchaseCompleted.return_value.get_logs.assert_called_once_with(from_block=3001,to_block=5000)
