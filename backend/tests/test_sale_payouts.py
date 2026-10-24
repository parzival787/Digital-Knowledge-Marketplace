import asyncio
import json
import time
import unittest
from uuid import UUID, uuid4
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
from tests import test_transak
from services.payments import payouts, sale_payouts as sales


class SaleEvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_canonical_matching_seller_trnsk_proceeds_qualify(self):
        market, wallet = '0x'+'2'*40, '0x'+'1'*40
        body = sales.SaleQuote(market=market,transaction_hash='0x'+'3'*64,log_index=1,currency='EUR',payment_method='card')
        accounting = {'seller':wallet,'token':sales.TRNSK,'seller_net':str(10**19)}
        event = {'tx_hash':body.transaction_hash,'log_index':1,'block_hash':'0x'+'4'*64,'accounting':accounting}
        row = {'block_number':10,'block_hash':event['block_hash'],'accounting':json.dumps(accounting)}
        conn = SimpleNamespace(fetchrow=AsyncMock(return_value=row))
        with patch.object(sales.blockchain,'entitlement_markets',return_value=[SimpleNamespace(address=market)]), patch.object(sales.event_indexer,'fetch_page',return_value=([event],None)):
            result = await sales.verified_sale(conn,body,wallet)
            self.assertEqual(result['amount_base_units'],str(10**19))
            with self.assertRaises(ValueError): await sales.verified_sale(conn,body,'0x'+'5'*40)
            for key,value in [('token','0x'+'6'*40),('seller_net','0')]:
                old = accounting[key]; accounting[key] = value; row['accounting'] = json.dumps(accounting)
                with self.assertRaises(ValueError): await sales.verified_sale(conn,body,wallet)
                accounting[key] = old; row['accounting'] = json.dumps(accounting)
            event['block_hash'] = '0x'+'7'*64
            with self.assertRaises(ValueError): await sales.verified_sale(conn,body,wallet)


class SalePayoutTests(unittest.IsolatedAsyncioTestCase):
    asyncTearDown=test_transak.TransakTests.asyncTearDown
    async def asyncSetUp(self):
        await test_transak.TransakTests.asyncSetUp(self)
        for module in (sales,payouts):
            p=patch.object(module,'get_conn',self.isolated);p.start();self.addCleanup(p.stop)
        await payouts.setup_payouts()
        self.user={'id':1,'wallet_address':'0x'+'1'*40}
        self.body=sales.SaleQuote(market='0x'+'2'*40,transaction_hash='0x'+'3'*64,log_index=1,currency='EUR',payment_method='credit_debit_card')
        self.terms={'market':self.body.market,'transaction_hash':self.body.transaction_hash,'log_index':1,'seller':self.user['wallet_address'],
                    'token':sales.TRNSK,'amount_base_units':str(10**19),'block_hash':'0x'+'4'*64}
        self.quote={'fetched_at':time.time(),'freshness_seconds':60,'fiatCurrency':'EUR','paymentMethod':'credit_debit_card',
                    'fiatAmount':'9','cryptoAmount':'10','totalFee':'1','fees':[],'conversionPrice':'1'}
        p=patch.object(sales,'verified_sale',side_effect=lambda *_:dict(self.terms));p.start();self.addCleanup(p.stop)
        p=patch.object(sales.transak_discovery,'quote',side_effect=lambda *_:dict(self.quote));p.start();self.addCleanup(p.stop)

    async def test_quote_refresh_and_only_one_sale_session(self):
        quoted=await sales.create_quote(self.body,self.user,'127.0.0.1')
        self.assertEqual((await sales.create_quote(self.body,self.user,'127.0.0.1'))['id'],quoted['id'])
        with self.assertRaises(ValueError):await sales.open_session(UUID(quoted['id']),{**self.user,'id':2},'127.0.0.1')
        with patch.object(sales.transak,'create_session',new=AsyncMock(return_value='https://global-stg.transak.com?session=test')) as create:
            values=await asyncio.gather(*(sales.open_session(UUID(quoted['id']),self.user,'127.0.0.1') for _ in range(2)),return_exceptions=True)
            self.assertEqual(create.await_count,1)
            self.assertEqual(sum(isinstance(v,dict) for v in values),1)
        with self.assertRaises(ValueError):await sales.create_quote(self.body,self.user,'127.0.0.1')

    async def test_sell_binding_rejects_wrong_token_amount_network_and_currency(self):
        quoted=await sales.create_quote(self.body,self.user,'127.0.0.1')
        conn=await self.isolated()
        try:row=await conn.fetchrow('SELECT * FROM seller_payouts WHERE id=$1',UUID(quoted['id']))
        finally:await conn.close()
        order={**self.order,'isBuyOrSell':'SELL','cryptoCurrency':'USDC','network':'polygon','cryptoAmount':'10','fiatCurrency':'EUR',
               'status':'COMPLETED','partnerOrderId':quoted['id'],'partnerCustomerId':str(row['customer_reference'])}
        result=payouts.verified_sell(order,row,self.order_id)
        self.assertEqual(result['expected_amount_base_units'],str(10**19))
        for change in ({'network':'ethereum'},{'cryptoCurrency':'ETH'},{'cryptoAmount':'9.999999999999999999'},{'fiatCurrency':'USD'},{'partnerCustomerId':str(uuid4())}):
            with self.assertRaises(ValueError):payouts.verified_sell({**order,**change},row,self.order_id)
        with patch.object(sales,'verify_delivery',side_effect=ValueError()):
            chain=await sales.outgoing_delivery(order,result,self.terms)
            self.assertEqual(chain['chain_delivery_state'],'chain_delivery_unverified')
            self.assertFalse(chain['grants_access'])
