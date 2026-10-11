import json
import unittest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from services import event_indexer as index
from services.payments import recording_sources as source
from tests import test_transak


class SourceTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_transak.TransakTests.asyncSetUp
    asyncTearDown=test_transak.TransakTests.asyncTearDown

    async def prepare(self):
        for module in (index,source):
            p=patch.object(module,'get_conn',self.isolated);p.start();self.addCleanup(p.stop)
        await index.setup_indexer()
        conn=await self.isolated()
        self.market='0x'+'1'*40;self.buyer='0x'+'2'*40
        await conn.execute('ALTER TABLE app_users ADD COLUMN wallet_address TEXT')
        await conn.execute('UPDATE app_users SET wallet_address=$1 WHERE id=1',self.buyer)
        await conn.execute("INSERT INTO chain_sync(market,deployment_block,next_block) VALUES ($1,1,11)",self.market)
        self.event={'tx_hash':'0x'+'3'*64,'log_index':0,'block_number':10,'block_hash':'0x'+'4'*64,
            'kind':'PurchaseCompleted','args':{'buyer':self.buyer,'tokenId':'1'},
            'accounting':{'token':'0x'+'5'*40,'seller':'0x'+'6'*40,'gross':'1000000','platform_fee':'50000','royalties':'0','seller_net':'950000'}}
        await conn.execute('INSERT INTO market_events(market,tx_hash,log_index,block_number,block_hash,kind,args,accounting) VALUES ($1,$2,0,10,$3,$4,$5,$6)',self.market,self.event['tx_hash'],self.event['block_hash'],self.event['kind'],json.dumps(self.event['args']),json.dumps(self.event['accounting']))
        await conn.close()

    async def test_only_reverified_market_sale_enqueues_once_and_wrong_block_fails(self):
        await self.prepare()
        with patch.object(index,'fetch_page',return_value=([self.event],self.event['block_hash'])),patch.object(source,'enqueue_verified',AsyncMock(return_value=uuid4())) as enqueue:
            await source.queue_indexed_sales();await source.queue_indexed_sales()
            self.assertEqual(enqueue.await_count,1)
            args=enqueue.call_args.args
            self.assertEqual(args[0],1)
            self.assertEqual(args[1],'amoy_marketplace')
            self.assertEqual(args[3]['paymentAmount'],1000000)
            self.assertEqual(args[3]['payoutAmount'],950000)
        conn=await self.isolated()
        await conn.execute('UPDATE market_events SET recording_evidence_id=NULL')
        await conn.close()
        changed={**self.event,'block_hash':'0x'+'7'*64}
        with patch.object(index,'fetch_page',return_value=([changed],changed['block_hash'])),patch.object(source,'enqueue_verified',AsyncMock()) as enqueue:
            with self.assertRaises(ValueError):await source.queue_indexed_sales()
            enqueue.assert_not_called()

    async def test_provider_capture_does_not_accept_authorized_refunded_or_wrong_amount(self):
        order={'provider_payment_id':'pay_test','provider_order_id':'order_test','fiat_amount':100,'fiat_currency':'INR'}
        import httpx
        from httpx._client import AsyncClient as original
        data={'id':'pay_test','order_id':'order_test','amount':100,'currency':'INR','status':'captured','amount_refunded':0}
        async def response(request):return httpx.Response(200,json=data)
        with patch.dict('os.environ',{'RAZORPAY_KEY_ID':'rzp_test_fixture','RAZORPAY_KEY_SECRET':'test'}),patch.object(source.httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(response),**kw)):
            await source.verify_saved_capture(order)
            for change in ({'status':'authorized'},{'amount_refunded':100},{'amount':99},{'currency':'USD'},{'order_id':'wrong'}):
                old=dict(data);data.update(change)
                with self.assertRaises(ValueError):await source.verify_saved_capture(order)
                data.clear();data.update(old)

    async def test_failed_oldest_sale_does_not_starve_other_sales(self):
        await self.prepare()
        conn=await self.isolated()
        events=[self.event]
        for i in range(1,6):
            event={**self.event,'log_index':i};events.append(event)
            await conn.execute('INSERT INTO market_events(market,tx_hash,log_index,block_number,block_hash,kind,args,accounting) VALUES ($1,$2,$3,10,$4,$5,$6,$7)',self.market,event['tx_hash'],i,event['block_hash'],event['kind'],json.dumps(event['args']),json.dumps(event['accounting']))
        await conn.close()
        with patch.object(index,'fetch_page',side_effect=OSError('RPC unavailable')):
            with self.assertRaises(OSError):await source.queue_indexed_sales()
        with patch.object(index,'fetch_page',return_value=(events,self.event['block_hash'])),patch.object(source,'enqueue_verified',AsyncMock(return_value=uuid4())) as enqueue:
            await source.queue_indexed_sales()
            self.assertEqual(enqueue.await_count,5)
