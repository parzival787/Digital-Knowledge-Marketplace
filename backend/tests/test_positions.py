import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from services import positions


class PositionTests(unittest.TestCase):
    def test_current_and_legacy_positions_are_account_scoped_and_pinned(self):
        wallet='0x'+'1'*40;asset_address='0x'+'2'*40
        current='0x'+'3'*40;legacy='0x'+'4'*40;other='0x'+'5'*40
        asset=Mock(address=asset_address);asset.functions.totalMinted.return_value.call.return_value=11
        markets={address:Mock(address=address) for address in (current,legacy)}
        for address,market in markets.items():
            f=market.functions
            f.knowledgeAsset.return_value.call.return_value=asset_address
            f.hasPurchased.side_effect=lambda token,who,a=address:SimpleNamespace(call=lambda **kw:a==legacy and token==1 and who==wallet)
            f.purchaseCount.return_value.call.return_value=1
            f.totalListingsCreated.return_value.call.return_value=2
            f.listings.side_effect=lambda i:SimpleNamespace(call=lambda **kw:[i,100,wallet if i==1 else other,0,True,1])
            f.totalAuctionsCreated.return_value.call.return_value=1
            f.auctions.return_value.call.return_value=[1,100,110,wallet,other,True,False,1,5]
            f.pendingRefunds.return_value.call.return_value=10
        eth=Mock(chain_id=80002,block_number=12)
        eth.get_block.return_value=SimpleNamespace(hash=bytes(32),timestamp=10)
        eth.contract.side_effect=lambda address,abi:asset if address==asset_address else markets[address]
        with patch.object(positions.blockchain,'w3',SimpleNamespace(eth=eth)),patch.object(positions.blockchain,'knowledge_asset',asset),patch.object(positions.blockchain,'MARKETPLACE_ADDRESS',current),patch.object(positions.blockchain,'legacy_registry_address',return_value=asset_address),patch.object(positions.blockchain,'entitlement_markets',return_value=list(markets.values())):
            result=positions.snapshot(wallet,0)
            self.assertEqual(result['entitlements'],[{'market':legacy,'token_id':'1','purchase_count':'1'}])
            self.assertEqual(len(result['listings']),2)
            self.assertEqual(len(result['auctions']),2)
            self.assertEqual(result['auctions'][0]['state'],'awaiting finalization')
            self.assertTrue(result['has_more'])
            self.assertEqual(result['block'],10)
            self.assertEqual(positions.snapshot(wallet,1)['listings'],[])
            markets[legacy].functions.knowledgeAsset.return_value.call.return_value=other
            with self.assertRaises(ValueError):positions.snapshot(wallet,0)
        asset.functions.totalMinted.return_value.call.assert_called_with(block_identifier=10)
