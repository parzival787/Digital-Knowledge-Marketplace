"""Quote isolation, expiry, concurrent acceptance and exact fee accounting."""
import asyncio
import json
import unittest
from uuid import uuid4
from unittest.mock import patch
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()
from services import pgvector_client as db
from services.payments import quotes


class AccountingTests(unittest.TestCase):
    def test_exact_solidity_rounding_and_no_buyer_markup(self):
        result = quotes.accounting(10000001, 500, [("a", 333), ("b", 777)])
        self.assertEqual(result["platform_fee_base_units"], "500000")
        self.assertEqual(result["buyer_token_total_base_units"], "10000001")
        self.assertEqual(result["buyer_dkm_fee_base_units"], "0")
        self.assertEqual(int(result["seller_net_base_units"]) + int(result["royalty_total_base_units"]) + int(result["platform_fee_base_units"]), 10000001)
        self.assertEqual(result["royalties"][0]["amount_base_units"], str(9500001 * 333 // 10000))
        for amount, bps, recipients in [(0,500,[]),(1,1001,[]),(1,500,[("a",2001)]),(1,500,[("a",1500),("b",1500)])]:
            with self.assertRaises(ValueError): quotes.accounting(amount, bps, recipients)


class QuoteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connect = db.get_conn
        self.schema = "quotes_test_" + uuid4().hex
        conn = await self.connect()
        await conn.execute(f'CREATE SCHEMA "{self.schema}"')
        await conn.close()
        async def connect():
            conn = await self.connect()
            await conn.execute(f'SET search_path TO "{self.schema}"')
            return conn
        self.isolated = connect
        patcher = patch.object(quotes, "get_conn", connect); patcher.start(); self.addCleanup(patcher.stop)
        conn = await connect()
        await conn.execute("CREATE TABLE app_users(id BIGINT PRIMARY KEY, wallet_address TEXT, payout_currency TEXT); INSERT INTO app_users VALUES (1,'buyer','USDC'),(2,'seller','EUR')")
        await conn.close()
        await quotes.setup_quotes()
        self.user = {"id":1,"wallet_address":"buyer"}
        self.terms = {"token_id":"1", "buyer":"buyer", "seller":"seller", **quotes.accounting(10000000,500,[])}
        patcher = patch.object(quotes, "purchase_terms", side_effect=lambda *_: dict(self.terms)); patcher.start(); self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        conn = await self.connect()
        await conn.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
        await conn.close()

    async def test_account_isolation_and_concurrent_idempotent_accept(self):
        from uuid import UUID
        quote = await quotes.create_quote(1,self.user)
        self.assertEqual(quote["terms"]["seller_payout_preference"], "EUR")
        key = UUID(quote["id"])
        with self.assertRaises(HTTPException) as err:
            await quotes.accept_quote(key, {"id":2,"wallet_address":"seller"})
        self.assertEqual(err.exception.status_code,404)
        accepted = await asyncio.gather(*(quotes.accept_quote(key,self.user) for _ in range(3)))
        self.assertTrue(all(v["accepted_at"] == accepted[0]["accepted_at"] for v in accepted))
        self.assertTrue(accepted[0]["accepted_at"])
        conn = await self.isolated()
        self.assertIsNone(await conn.fetchval("SELECT to_regclass('payment_orders')"))
        await conn.close()

    async def test_changes_expiry_and_failed_revalidation_do_not_accept(self):
        from uuid import UUID
        quote = await quotes.create_quote(1,self.user); key=UUID(quote["id"])
        original = dict(self.terms)
        self.terms["platform_fee_base_units"] = "1"
        with self.assertRaises(HTTPException) as err: await quotes.accept_quote(key,self.user)
        self.assertEqual(err.exception.status_code,409)
        self.terms = original
        with patch.object(quotes,"purchase_terms",side_effect=RuntimeError("private rpc")):
            with self.assertRaises(RuntimeError): await quotes.accept_quote(key,self.user)
        conn = await self.isolated()
        self.assertIsNone(await conn.fetchval("SELECT accepted_at FROM purchase_quotes WHERE id=$1",key))
        await conn.execute("UPDATE purchase_quotes SET expires_at=NOW()-INTERVAL '1 second' WHERE id=$1",key)
        await conn.close()
        with self.assertRaises(HTTPException) as err: await quotes.accept_quote(key,self.user)
        self.assertEqual(err.exception.status_code,409)
