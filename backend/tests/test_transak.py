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
        await transak.setup_transak()
        self.refreshes = 0
        self.sessions = 0
        self.bad_url = False
        self.fail = False
        self.token_expired = False
        async def handler(request):
            if self.fail:
                return httpx.Response(401, json={"error": "test-secret"})
            if "refresh-token" in request.url.path:
                self.refreshes += 1
                return httpx.Response(200, json={"data": {"accessToken": "secret-token", "expiresAt": time.time() + (-1 if self.token_expired else 3600)}})
            import json
            body = json.loads(request.content)["widgetParams"]
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
