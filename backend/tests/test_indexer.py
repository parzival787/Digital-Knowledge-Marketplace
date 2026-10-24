import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from tests import test_transak
from services import event_indexer as index
from web3 import Web3
from web3.datastructures import AttributeDict
from eth_abi import encode
from eth_utils import event_abi_to_log_topic
from hexbytes import HexBytes


class IndexTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_transak.TransakTests.asyncSetUp
    asyncTearDown=test_transak.TransakTests.asyncTearDown

    async def test_idempotent_history_accounting_and_reorg_fail_closed(self):
        mock=patch.object(index,'get_conn',self.isolated);mock.start();self.addCleanup(mock.stop)
        await index.setup_indexer()
        address='0x'+'1'*40;wallet='0x'+'2'*40
        block_hash=bytes.fromhex('ab'*32)
        eth=SimpleNamespace(chain_id=80002,block_number=12,get_block=lambda _:SimpleNamespace(hash=block_hash))
        row={'tx_hash':'0x'+'3'*64,'log_index':1,'block_number':10,'block_hash':'0x'+block_hash.hex(),
            'kind':'PurchaseCompleted','args':{'buyer':wallet,'seller':wallet,'tokenId':'1'},
            'accounting':{'seller':wallet,'token':'0x'+'4'*40,'gross':'100','platform_fee':'5','royalties':'10','seller_net':'85'}}
        with patch.object(index.blockchain,'w3',SimpleNamespace(eth=eth)),patch.object(index,'first_code_block',return_value=10),patch.object(index,'fetch_page',return_value=([row],'0x'+block_hash.hex())) as fetch,patch.object(index.blockchain,'entitlement_markets',return_value=[SimpleNamespace(address=address)]):
            await asyncio.gather(index.sync_market(address),index.sync_market(address))
            await index.sync_market(address)
            self.assertEqual(fetch.call_count,1)
            history=await index.history({'id':1,'wallet_address':wallet})
            self.assertEqual(len(history['events']),1)
            self.assertEqual(history['totals'][0]['net'],'85')
            self.assertFalse(history['lifetime_complete'])
            eth.get_block=lambda _:SimpleNamespace(hash=bytes(32))
            await index.sync_market(address)
            history=await index.history({'id':1,'wallet_address':wallet})
            self.assertEqual(history['events'],[])
            self.assertEqual(history['totals'],[])
            self.assertEqual(history['coverage'][0]['state'],'review_required')
            await index.rebuild_market(address)
            conn=await self.isolated()
            self.assertEqual(await conn.fetchval('SELECT count(*) FROM market_events'),0)
            self.assertEqual(await conn.fetchval('SELECT next_block FROM chain_sync'),10)
            await conn.close()

    def test_deployment_binary_search_and_large_integers(self):
        w3=SimpleNamespace(eth=SimpleNamespace(get_code=lambda address,block:b'code' if block>=37 else b''))
        self.assertEqual(index.first_code_block(w3,'market',100),37)
        self.assertEqual(index.normalized({'amount':2**200})['amount'],str(2**200))

    async def test_rpc_failure_shrinks_page_and_persists_backoff_without_advancing(self):
        mock=patch.object(index,'get_conn',self.isolated);mock.start();self.addCleanup(mock.stop)
        await index.setup_indexer()
        address='0x'+'5'*40
        eth=SimpleNamespace(chain_id=80002,block_number=100)
        with patch.object(index.blockchain,'w3',SimpleNamespace(eth=eth)),patch.object(index,'first_code_block',return_value=10),patch.object(index,'fetch_page',side_effect=RuntimeError('RPC range rejected')) as fetch:
            with self.assertRaises(RuntimeError):await index.sync_market(address)
            await index.sync_market(address)
            self.assertEqual(fetch.call_count,1)
        conn=await self.isolated()
        try:
            row=await conn.fetchrow('SELECT * FROM chain_sync WHERE market=$1',address)
            self.assertEqual(row['next_block'],10)
            self.assertEqual(row['page_size'],5)
            self.assertEqual(row['failures'],1)
            self.assertIsNotNone(row['retry_after'])
        finally:await conn.close()

    def test_auction_and_refund_logs_decode_with_market_identity(self):
        market_address='0x'+'1'*40;buyer='0x'+'2'*40;seller='0x'+'3'*40
        block_hash=HexBytes('0x'+'a'*64);tx_hash=HexBytes('0x'+'b'*64)
        logs=[]
        for i,(name,args) in enumerate([
            ('AuctionCreated',{'tokenId':1,'reservePrice':100,'startTime':1,'endTime':20}),
            ('BidPlaced',{'tokenId':1,'bidder':buyer,'amount':110}),
            ('AuctionEnded',{'tokenId':1,'winner':buyer,'amount':110}),
            ('RefundWithdrawn',{'bidder':buyer,'amount':100})]):
            abi=next(e for e in index.ABIS['marketplace'] if e.get('name')==name)
            indexed=[p for p in abi['inputs'] if p['indexed']];data=[p for p in abi['inputs'] if not p['indexed']]
            logs.append({'address':market_address,'topics':[event_abi_to_log_topic(abi),*[HexBytes(encode([p['type']],[args[p['name']]])) for p in indexed]],
                'data':HexBytes(encode([p['type'] for p in data],[args[p['name']] for p in data])),
                'blockNumber':10,'blockHash':block_hash,'transactionHash':tx_hash,'transactionIndex':0,'logIndex':i})
        market=MagicMock(address=market_address)
        market.functions.tokenToAuction.return_value.call.return_value=7
        market.functions.auctions.return_value.call.return_value=[1,100,110,buyer,seller,False,True,1,20]
        market.decode_function_input.return_value=(SimpleNamespace(fn_name='placeBid'),{'auctionId':7})
        eth=MagicMock(chain_id=80002)
        eth.contract.return_value=market;eth.get_block.return_value=AttributeDict({'hash':block_hash})
        eth.get_logs.return_value=list(reversed(logs))
        eth.get_transaction.return_value={'to':market_address,'input':'0x1234'}
        with patch.object(index.blockchain,'w3',SimpleNamespace(eth=eth,codec=Web3().codec)),patch.object(index,'sale_accounting',return_value=None):
            rows,_=index.fetch_page(market_address,10,10)
            self.assertEqual([r['kind'] for r in rows],['AuctionCreated','BidPlaced','AuctionEnded','RefundWithdrawn'])
            self.assertEqual(rows[0]['args']['auctionId'],'7')
            self.assertEqual(rows[1]['args']['seller'],seller)
            self.assertEqual(rows[2]['args']['winner'],buyer)
            self.assertEqual(rows[3]['args']['bidder'],buyer)
            logs[0]['removed']=True
            with self.assertRaises(ValueError):index.fetch_page(market_address,10,10)
