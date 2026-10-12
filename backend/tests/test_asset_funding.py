import asyncio
import json
import time
import unittest
import asyncpg
from uuid import UUID, uuid4
from unittest.mock import patch, AsyncMock
from tests import test_transak
from services.payments import asset_funding as funding


class FundingTests(unittest.IsolatedAsyncioTestCase):
    asyncTearDown = test_transak.TransakTests.asyncTearDown
    async def asyncSetUp(self):
        await test_transak.TransakTests.asyncSetUp(self)
        p = patch.object(funding, "get_conn", self.isolated); p.start(); self.addCleanup(p.stop)
        await funding.setup_funding()
        self.user = {"id":1,"wallet_address":"0x"+"1"*40}
        self.terms = {"payment_token":funding.TRNSK,"decimals":18,"token_id":"1", "marketplace":"0x"+"2"*40,
                      "buyer_token_total_base_units":"10000000000000000001"}
        self.quote = {"fetched_at":time.time(),"freshness_seconds":60,"fiatCurrency":"USD","paymentMethod":"credit_debit_card",
                      "fiatAmount":"11.46","cryptoAmount":"10.000000000000000001","totalFee":"1.46","fees":[],"conversionPrice":"1"}
        p = patch.object(funding,"purchase_terms",side_effect=lambda *_:dict(self.terms));p.start();self.addCleanup(p.stop)
        p = patch.object(funding.transak_discovery,"quote",side_effect=lambda *_:dict(self.quote));p.start();self.addCleanup(p.stop)
        self.body = funding.FundingRequest(token_id=1,fiat_currency="USD",payment_method="credit_debit_card")

    async def test_binding_freshness_and_concurrent_session_attempt(self):
        result = await funding.funding_quote(self.body,self.user,"127.0.0.1")
        identifier = UUID(result["id"])
        with self.assertRaises(ValueError):
            await funding.funding_session(identifier,{**self.user,"id":2},"127.0.0.1")
        self.quote["totalFee"]="2"
        with self.assertRaises(ValueError):await funding.funding_session(identifier,self.user,"127.0.0.1")
        self.quote["totalFee"]="1.46"
        result = await asyncio.gather(*(funding.funding_session(identifier,self.user,"127.0.0.1") for _ in range(2)),return_exceptions=True)
        self.assertEqual(sum(isinstance(r,dict) for r in result),1)
        self.assertEqual(self.sessions,1)
        self.quote["fetched_at"]=time.time()-120
        expired=await funding.funding_quote(self.body,self.user,"127.0.0.1")
        with self.assertRaises(ValueError):await funding.funding_session(UUID(expired["id"]),self.user,"127.0.0.1")

    async def test_completed_provider_is_not_chain_delivery_or_entitlement(self):
        result=await funding.funding_quote(self.body,self.user,"127.0.0.1")
        conn=await self.isolated()
        try:
            row=await conn.fetchrow("SELECT * FROM asset_funding WHERE id=$1",UUID(result["id"]))
            data={"partnerOrderId":result["id"],"partnerCustomerId":str(row["customer_reference"])}
            receipt={"order_id":str(uuid4()),"verification_state":"provider_verified","status":"COMPLETED",
                     "fiat_currency":"USD","fiat_amount":"11.460","crypto_amount":self.quote["cryptoAmount"],"transaction_hash":"0x"+"a"*64}
            with patch.object(funding,"verify_delivery",side_effect=ValueError("wrong receipt")):
                checked=await funding.reconcile_funding(conn,data,receipt,self.user)
                self.assertEqual(checked["chain_delivery_state"],"chain_delivery_unverified")
                self.assertNotEqual(checked["funding_state"],"wallet_funded")
            valid={"chain_delivery_state":"verified","transaction_hash":receipt["transaction_hash"],"grants_access":False}
            with patch.object(funding,"verify_delivery",return_value=valid):
                checked=await funding.reconcile_funding(conn,data,receipt,self.user)
                self.assertEqual(checked["funding_state"],"wallet_funded")
                self.assertFalse(checked["grants_access"])
                replay=await funding.reconcile_funding(conn,data,receipt,self.user)
                self.assertEqual(checked,replay)
            with self.assertRaises(ValueError):await funding.reconcile_funding(conn,data,receipt,{**self.user,"id":2})
            conflict=await funding.reconcile_funding(conn,data,{**receipt,"fiat_currency":"EUR"},self.user)
            self.assertEqual(conflict["funding_state"],"review_required")
            self.assertEqual(conflict["previous_verified_delivery"],valid)
            other=await funding.funding_quote(self.body,self.user,"127.0.0.1")
            with self.assertRaises(asyncpg.UniqueViolationError):
                await conn.execute("UPDATE asset_funding SET delivery=$2 WHERE id=$1",UUID(other["id"]),json.dumps(valid))
            self.assertIsNone(await conn.fetchval("SELECT to_regclass('payment_orders')"))
        finally:await conn.close()
