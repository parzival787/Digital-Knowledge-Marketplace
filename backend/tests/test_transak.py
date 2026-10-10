"""Disposable database tests; provider HTTP is simulated and cannot grant entitlement."""
import asyncio
import time
import unittest
import uuid
from unittest.mock import patch

import httpx
from dotenv import load_dotenv
load_dotenv()
from services import pgvector_client as db
from services.payments import transak


class TransakTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.schema = "transak_test_" + uuid.uuid4().hex
        self.connect = db.get_conn
        conn = await self.connect()
        await conn.execute(f'CREATE SCHEMA "{self.schema}"')
        await conn.close()
        async def connect():
            conn = await self.connect()
            await conn.execute(f'SET search_path TO "{self.schema}"')
            return conn
        self.isolated = connect
        config = patch.dict("os.environ", {"TRANSAK_STAGING_API_KEY": "test-key", "TRANSAK_STAGING_API_SECRET": "test-secret",
            "CONTENT_MASTER_KEY": "dGVzdC1vbmx5LWtleS0zMi1ieXRlcy1sb25nLTAwMDA="})
        config.start(); self.addCleanup(config.stop)
        mock = patch.object(transak, "get_conn", connect)
        mock.start(); self.addCleanup(mock.stop)
        conn = await connect()
        await conn.execute("CREATE TABLE app_users (id BIGINT PRIMARY KEY); INSERT INTO app_users VALUES (1),(2)")
        await conn.close()
        await transak.setup_transak()
        self.refreshes = 0
        self.sessions = 0
        self.bad_url = False
        self.fail = False
        self.token_expired = False
        self.order_id = str(uuid.uuid4())
        self.order = {"_id": self.order_id, "walletAddress": "0x" + "1" * 40,
            "isBuyOrSell": "BUY", "network": "polygon", "cryptoCurrency": "USDC",
            "status": "AWAITING_PAYMENT_FROM_USER", "fiatCurrency": "USD", "fiatAmount": 100,
            "amountPaid": 0, "totalFeeInFiat": "3.99", "cryptoAmount": None,
            "transactionHash": "DUMMY_TX_ID", "email": "private@example.invalid"}
        async def handler(request):
            if self.fail:
                return httpx.Response(401, json={"error": "test-secret"})
            if "refresh-token" in request.url.path:
                self.refreshes += 1
                return httpx.Response(200, json={"data": {"accessToken": "secret-token", "expiresAt": time.time() + (-1 if self.token_expired else 3600)}})
            if request.method == "GET":
                return httpx.Response(200, json={"data": self.order})
            import json
            body = json.loads(request.content)["widgetParams"]
            if body["productsAvailed"] == "SELL":
                self.assertEqual(body["fiatCurrency"], "EUR")
                self.assertNotIn("walletAddress", body)
                self.assertNotIn("network", body)
                self.sessions += 1
                return httpx.Response(200, json={"data": {"widgetUrl": "https://global-stg.transak.com?sessionId=sell"}})
            self.assertEqual(body["walletAddress"], "0x" + "1" * 40)
            self.assertTrue(body["disableWalletAddressForm"])
            self.assertEqual(body["network"], "polygon")
            self.assertEqual(request.headers["access-token"], "secret-token")
            self.sessions += 1
            return httpx.Response(200, json={"data": {"widgetUrl": "https://" + ("attacker.invalid" if self.bad_url else "global-stg.transak.com") + "?sessionId=" + str(self.sessions)}})
        factory = httpx.AsyncClient
        mock = patch.object(transak.httpx, "AsyncClient", lambda **kwargs: factory(transport=httpx.MockTransport(handler), **kwargs))
        mock.start(); self.addCleanup(mock.stop)

    async def asyncTearDown(self):
        conn = await self.connect()
        await conn.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
        await conn.close()

    async def create(self):
        return await transak.create_session("0x" + "1" * 40, "127.0.0.1")

    async def test_concurrent_sessions_share_encrypted_token(self):
        urls = await asyncio.gather(self.create(), self.create(), self.create())
        self.assertEqual(self.refreshes, 1)
        self.assertEqual(len(set(urls)), 3)
        conn = await self.isolated()
        row = await conn.fetchrow("SELECT * FROM transak_staging_tokens")
        self.assertNotIn(b"secret-token", row["ciphertext"])
        await conn.execute("UPDATE transak_staging_tokens SET expires_at=0")
        await conn.close()
        await self.create()
        self.assertEqual(self.refreshes, 2)

    async def test_provider_errors_redacted_and_redirect_rejected(self):
        self.fail = True
        with self.assertRaises(ValueError) as exc:
            await self.create()
        self.assertNotIn("test-secret", str(exc.exception))
        self.fail = False; self.bad_url = True
        with self.assertRaisesRegex(ValueError, "unexpected staging URL"):
            await self.create()

    async def test_invalid_expiry_and_ip_fail_closed(self):
        self.token_expired = True
        with self.assertRaisesRegex(ValueError, "invalid token expiry"):
            await self.create()
        with self.assertRaises(ValueError):
            await transak.create_session("0x" + "1" * 40, "not-an-ip")
        self.assertEqual(self.sessions, 0)

    async def test_verified_orders_persist_and_follow_status_without_entitlement(self):
        user = {"id": 1, "wallet_address": "0x" + "1" * 40}
        first = await transak.refresh_order(self.order_id, user)
        self.assertFalse(first["grants_access"])
        self.assertNotIn("email", first)
        self.assertIsNone(first["transaction_hash"])
        for state in ("PENDING_DELIVERY_FROM_TRANSAK", "COMPLETED", "REFUNDED"):
            self.order["status"] = state
            self.order["amountPaid"] = 100
            self.order["transactionHash"] = "0x" + "a" * 64
            await asyncio.gather(transak.refresh_order(self.order_id, user), transak.refresh_order(self.order_id, user))
            saved = await transak.orders(user)
            self.assertEqual(len(saved["orders"]), 1)
            self.assertEqual(saved["orders"][0]["status"], state)
            self.assertFalse(saved["orders"][0]["grants_access"])
        self.assertEqual((await transak.orders({"id": 2}))["orders"], [])
        with self.assertRaises(ValueError):
            await transak.refresh_order(self.order_id, {"id": 2, "wallet_address": user["wallet_address"]})

    async def test_wrong_wallet_route_identity_or_amount_never_saves(self):
        user = {"id": 1, "wallet_address": "0x" + "1" * 40}
        original = dict(self.order)
        for change in ({"walletAddress": "0x" + "2" * 40}, {"network": "ethereum"},
                       {"_id": str(uuid.uuid4())}, {"isBuyOrSell": "SELL"},
                       {"cryptoCurrency": "ETH"}, {"amountPaid": "NaN"},
                       {"totalFeeInFiat": -1}, {"cryptoAmount": "1e-1000000"}, {"status": "<script>"}):
            self.order = {**original, **change}
            with self.assertRaises(ValueError):
                await transak.refresh_order(self.order_id, user)
        self.assertEqual((await transak.orders(user))["orders"], [])

    async def test_payout_session_uses_sell_and_no_forced_blockchain(self):
        url = await transak.create_session("0x" + "1" * 40, "127.0.0.1", payout_currency="EUR")
        self.assertTrue(url.startswith("https://global-stg.transak.com?"))
        with self.assertRaises(ValueError):
            await transak.create_session("0x" + "1" * 40, "127.0.0.1", payout_currency="INVALID")
        self.assertEqual(self.sessions, 1)
