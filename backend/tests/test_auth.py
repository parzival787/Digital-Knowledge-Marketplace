"""Account boundary checks using disposable PostgreSQL schemas and simulated RPC."""
import uuid
import unittest
from unittest.mock import patch

import httpx
from dotenv import load_dotenv
from eth_account import Account
from eth_account.messages import encode_defunct

load_dotenv()
from services import auth, pgvector_client as db
from services.payments import service
import main


class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.schema = "auth_test_" + uuid.uuid4().hex
        self.connect = db.get_conn
        conn = await self.connect()
        await conn.execute(f'CREATE SCHEMA "{self.schema}"')
        await conn.close()

        async def connect():
            conn = await self.connect()
            await conn.execute(f'SET search_path TO "{self.schema}", public')
            return conn

        self.isolated = connect
        for module in (db, auth, service, main):
            mock = patch.object(module, "get_conn", connect)
            mock.start()
            self.addCleanup(mock.stop)
        await db.setup_tables()
        await auth.setup_auth()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://localhost:8000", headers={"origin": auth.ORIGIN, "x-dkm-request": "1"})
        self.wallet = Account.create()

    async def asyncTearDown(self):
        await self.client.aclose()
        conn = await self.connect()
        await conn.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
        await conn.close()

    async def signup(self, username="alice"):
        response = await self.client.post("/api/auth/signup", json={"username": username, "password": "correct horse battery staple"})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    async def verify(self, wallet=None):
        wallet = wallet or self.wallet
        challenge = await self.client.post("/api/auth/wallet/challenge")
        message = challenge.json()["message"]
        proof = {"address": wallet.address, "signature": wallet.sign_message(encode_defunct(text=message)).signature.hex()}
        response = await self.client.post("/api/auth/wallet/verify", json=proof)
        return response, proof

    async def test_sessions_csrf_passwords_and_logout(self):
        self.assertEqual((await self.client.get("/api/account/dashboard")).status_code, 401)
        invalid = await self.client.post("/api/auth/signup", json={"username": "alice", "password": "shortsecret"})
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn("shortsecret", invalid.text)
        user = await self.signup()
        self.assertIsNone(user["wallet_address"])
        cookie = self.client.cookies.get(auth.COOKIE)
        conn = await self.isolated()
        row = await conn.fetchrow("SELECT password_hash FROM app_users WHERE id=$1", user["id"])
        self.assertNotIn("correct horse", row["password_hash"])
        self.assertEqual(await conn.fetchval("SELECT token_hash FROM app_sessions"), auth.digest(cookie))
        await conn.close()
        self.assertEqual((await self.client.post("/api/auth/logout", headers={"origin": "https://attacker.invalid"})).status_code, 403)
        self.assertEqual((await self.client.post("/api/auth/logout", headers={"x-dkm-request": ""})).status_code, 403)
        self.assertEqual((await self.client.get("/api/auth/me")).status_code, 200)
        self.assertEqual((await self.client.post("/api/auth/logout")).status_code, 200)
        self.client.cookies.set(auth.COOKIE, cookie)
        self.assertEqual((await self.client.get("/api/auth/me")).status_code, 401)
        self.client.cookies.clear()
        wrong = await self.client.post("/api/auth/login", json={"username": "alice", "password": "incorrect password"})
        self.assertEqual(wrong.status_code, 401)
        login = await self.client.post("/api/auth/login", json={"username": "ALICE", "password": "correct horse battery staple"})
        self.assertEqual(login.status_code, 200)
        self.assertIn("HttpOnly", login.headers["set-cookie"])
        self.assertIn("SameSite=strict", login.headers["set-cookie"])
        conn = await self.isolated()
        await conn.execute("UPDATE app_sessions SET expires_at=NOW()-INTERVAL '1 second'")
        await conn.close()
        self.assertEqual((await self.client.get("/api/auth/me")).status_code, 401)

    async def test_wallet_proof_replay_and_account_isolation(self):
        alice = await self.signup()
        unverified = await self.client.post("/api/payments/create", json={"token_id": 1, "buyer_address": self.wallet.address})
        self.assertEqual(unverified.status_code, 403)
        response, proof = await self.verify()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((await self.client.post("/api/auth/wallet/verify", json=proof)).status_code, 400)
        response, _ = await self.verify(Account.create())
        self.assertEqual(response.status_code, 409)
        conn = await self.isolated()
        await conn.execute("INSERT INTO knowledge_assets(vector_id,token_id,price_usdc,user_id,file_cid,metadata_cid) VALUES ('owned',1,5,$1,'file','meta')", alice["id"])
        await conn.close()
        spoof = await self.client.post("/api/payments/create", json={"token_id": 1, "buyer_address": Account.create().address})
        self.assertEqual(spoof.status_code, 403)
        created = await self.client.post("/api/payments/create", json={"token_id": 1, "buyer_address": self.wallet.address, "payment_method": "mock"})
        self.assertEqual(created.status_code, 200, created.text)
        order_id = created.json()["order"]["order_id"]
        self.assertNotIn("settlement_raw_tx", created.text)
        self.assertEqual((await self.client.get("/api/account/dashboard")).json()["assets"][0]["vector_id"], "owned")
        await self.client.post("/api/auth/logout")
        await self.signup("bob")
        response, _ = await self.verify()
        self.assertEqual(response.status_code, 409)
        response, _ = await self.verify(Account.create())
        self.assertEqual(response.status_code, 200)
        for suffix, method in [("", "GET"), ("/confirm", "POST"), ("/settle", "POST")]:
            response = await self.client.request(method, f"/api/payments/{order_id}{suffix}")
            self.assertEqual(response.status_code, 404, response.text)
        dashboard = (await self.client.get("/api/account/dashboard")).json()
        self.assertEqual(dashboard, {"assets": [], "orders": []})
        self.assertEqual((await self.client.post("/api/assets/owned/link-token", json={"token_id": 1})).status_code, 404)

    async def test_link_checks_content_and_access_uses_session_wallet(self):
        user = await self.signup()
        await self.verify()
        conn = await self.isolated()
        await conn.execute("INSERT INTO knowledge_assets(vector_id,user_id,file_cid,metadata_cid,price_usdc) VALUES ('upload',$1,'file','meta',5)", user["id"])
        await conn.close()
        asset = {"creator": self.wallet.address, "ipfs_cid": "wrong", "metadata_cid": "meta", "price_usdc": 5000000, "active": True}
        with patch.object(main, "get_knowledge_asset", return_value=asset):
            self.assertEqual((await self.client.post("/api/assets/upload/link-token", json={"token_id": 1})).status_code, 403)
            asset["ipfs_cid"] = "file"
            self.assertEqual((await self.client.post("/api/assets/upload/link-token", json={"token_id": 1})).status_code, 200)
            self.assertEqual((await self.client.post("/api/assets/upload/link-token", json={"token_id": 2})).status_code, 409)
            with patch.object(main, "has_purchased", return_value=False) as purchased, patch.object(main, "get_purchase_count", return_value=0):
                response = await self.client.get("/api/assets/1/access?wallet_address=0x0000000000000000000000000000000000000001")
                self.assertEqual(response.status_code, 200)
                purchased.assert_called_with(1, self.wallet.address)
                self.assertTrue(response.json()["access_granted"])

    async def test_expired_wrong_proof_and_rate_limit(self):
        await self.signup()
        response = await self.client.post("/api/auth/wallet/challenge")
        other = Account.create()
        proof = {"address": self.wallet.address, "signature": other.sign_message(encode_defunct(text=response.json()["message"])).signature.hex()}
        self.assertEqual((await self.client.post("/api/auth/wallet/verify", json=proof)).status_code, 400)
        conn = await self.isolated()
        await conn.execute("UPDATE app_sessions SET challenge_expires=NOW()-INTERVAL '1 second'")
        await conn.execute("UPDATE auth_attempts SET attempts=50")
        await conn.close()
        self.assertEqual((await self.client.post("/api/auth/wallet/verify", json=proof)).status_code, 400)
        self.assertEqual((await self.client.post("/api/auth/login", json={"username": "alice", "password": "correct horse battery staple"})).status_code, 429)

    async def test_upload_form_and_returned_id_belong_to_account(self):
        import json
        user = await self.signup()
        await self.verify()
        files = {"file": ("example.txt", b"document content " * 20, "text/plain")}
        invalid = await self.client.post("/api/upload-ipfs", files=files, data={"metadata_json": "[]"})
        self.assertEqual(invalid.status_code, 422)
        meta = {"title": "Example", "summary": "Example document", "tags": ["test"], "domain": "other", "recommended_price_usdc": 7, "quality_score": 0.8}
        original_client = httpx.AsyncClient
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"data": {"cid": "test-cid"}}))
        with patch.dict("os.environ", {"PINATA_JWT": "test-only"}), patch.object(main, "generate_embedding", return_value=[0.1]*384), patch.object(main.fraud_detector, "check_upload", return_value={"is_fraud": False}), patch.object(main.httpx, "AsyncClient", side_effect=lambda **kwargs: original_client(transport=transport, **kwargs)):
            response = await self.client.post("/api/upload-ipfs", files=files, data={"metadata_json": json.dumps(meta)})
        self.assertEqual(response.status_code, 200, response.text)
        conn = await self.isolated()
        row = await conn.fetchrow("SELECT * FROM knowledge_assets WHERE vector_id=$1", response.json()["vector_id"])
        await conn.close()
        self.assertEqual(row["title"], "Example")
        self.assertEqual(row["price_usdc"], 7)
        self.assertEqual(row["user_id"], user["id"])

    async def test_google_code_flow_creates_and_reuses_separate_account(self):
        from urllib.parse import urlparse, parse_qs, urlencode
        import hashlib
        import base64
        original_client = httpx.AsyncClient
        expected_verifier = None
        profile = {"sub": "google-subject-123", "email_verified": True, "given_name": "Alice"}
        def provider(request):
            if request.url.path == "/token":
                params = parse_qs(request.content.decode())
                self.assertEqual(params["code_verifier"][0], expected_verifier)
                self.assertEqual(params["redirect_uri"][0], "http://localhost:8000/api/auth/google/callback")
                return httpx.Response(200, json={"access_token": "test-token"})
            self.assertEqual(str(request.url), "https://openidconnect.googleapis.com/v1/userinfo")
            self.assertEqual(request.headers["authorization"], "Bearer test-token")
            return httpx.Response(200, json=profile)
        config = {"GOOGLE_CLIENT_ID": "test-client", "GOOGLE_CLIENT_SECRET": "test-secret", "GOOGLE_REDIRECT_URI": "http://localhost:8000/api/auth/google/callback"}
        password_user = await self.signup("alice")
        await self.client.post("/api/auth/logout")
        with patch.dict("os.environ", config):
            for _ in range(2):
                start = await self.client.post("/api/auth/google/start")
                params = parse_qs(urlparse(start.json()["url"]).query)
                self.assertEqual(params["code_challenge_method"], ["S256"])
                conn = await self.isolated()
                expected_verifier = await conn.fetchval("SELECT verifier FROM google_auth_flows WHERE state_hash=$1", auth.digest(params["state"][0]))
                await conn.close()
                challenge = base64.urlsafe_b64encode(hashlib.sha256(expected_verifier.encode()).digest()).decode().rstrip("=")
                self.assertEqual(params["code_challenge"], [challenge])
                callback = "/api/auth/google/callback?" + urlencode({"code": "code", "state": params["state"][0]})
                with patch.object(auth.httpx, "AsyncClient", side_effect=lambda **kw: original_client(transport=httpx.MockTransport(provider), **kw)):
                    response = await self.client.get(callback)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], auth.ORIGIN + "/account")
                me = (await self.client.get("/api/auth/me")).json()
                self.assertNotEqual(me["id"], password_user["id"])
                self.assertTrue(me["username"].startswith("alice_"))
                self.assertIn("google_error", (await self.client.get(callback)).headers["location"])
                await self.client.post("/api/auth/logout")
            conn = await self.isolated()
            self.assertEqual(await conn.fetchval("SELECT COUNT(*) FROM app_users WHERE google_sub=$1", profile["sub"]), 1)
            await conn.close()
            rejected = await self.client.post("/api/auth/login", json={"username": me["username"], "password": "correct horse battery staple"})
            self.assertEqual(rejected.status_code, 401)

    async def test_asset_details_only_returns_catalog_fields(self):
        conn = await self.isolated()
        await conn.execute("INSERT INTO knowledge_assets(vector_id,metadata_cid,title,summary,domain,tags) VALUES ('catalog','safe-cid','Research guide','A readable description','science',ARRAY['research'])")
        await conn.close()
        with patch.object(main, "get_knowledge_asset", return_value={"metadata_cid": "safe-cid"}):
            response = await self.client.get("/api/assets/1/details")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"title": "Research guide", "summary": "A readable description", "domain": "science", "tags": ["research"]})
        filtered = main.asset_description({"title": "Guide", "summary": {"blake3_hash": "secret"}, "file_cid": "raw-id", "blake3_hash": "raw-hash", "tags": ["topic", 123]})
        self.assertEqual(set(filtered), {"title", "summary", "domain", "tags"})
        self.assertNotIn("secret", str(filtered))
        self.assertEqual(filtered["tags"], ["topic"])

    async def test_google_rejects_missing_config_state_cookie_expiry_and_unverified_identity(self):
        from urllib.parse import urlparse, parse_qs
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": "", "GOOGLE_REDIRECT_URI": ""}):
            self.assertFalse((await self.client.get("/api/auth/methods")).json()["google"])
            self.assertEqual((await self.client.post("/api/auth/google/start")).status_code, 503)
        config = {"GOOGLE_CLIENT_ID": "test-client", "GOOGLE_CLIENT_SECRET": "test-secret", "GOOGLE_REDIRECT_URI": "http://localhost:8000/api/auth/google/callback"}
        original_client = httpx.AsyncClient
        with patch.dict("os.environ", config):
            start = await self.client.post("/api/auth/google/start")
            state = parse_qs(urlparse(start.json()["url"]).query)["state"][0]
            cookie = self.client.cookies.get(auth.OAUTH_COOKIE)
            self.client.cookies.clear()
            self.assertIn("google_error", (await self.client.get(f"/api/auth/google/callback?state={state}&code=test")).headers["location"])
            self.client.cookies.set(auth.OAUTH_COOKIE, cookie)
            conn = await self.isolated()
            await conn.execute("UPDATE google_auth_flows SET expires_at=NOW()-INTERVAL '1 second'")
            await conn.close()
            self.assertIn("google_error", (await self.client.get(f"/api/auth/google/callback?state={state}&code=test")).headers["location"])
            self.client.cookies.clear()
            start = await self.client.post("/api/auth/google/start")
            state = parse_qs(urlparse(start.json()["url"]).query)["state"][0]
            transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"access_token": "token"} if r.url.path == "/token" else {"sub": "123", "email_verified": False}))
            with patch.object(auth.httpx, "AsyncClient", side_effect=lambda **kw: original_client(transport=transport, **kw)):
                response = await self.client.get(f"/api/auth/google/callback?state={state}&code=test")
            self.assertIn("google_error", response.headers["location"])
            self.assertEqual((await self.client.get("/api/auth/me")).status_code, 401)


if __name__ == "__main__":
    unittest.main()
