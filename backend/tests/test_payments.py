r"""Run: venv\Scripts\python.exe -m unittest tests.test_payments -v.

Uses a disposable PostgreSQL schema; never changes existing asset/payment rows.
"""
import asyncio
import uuid
import unittest
import os
import hashlib
import hmac
import httpx
from unittest.mock import AsyncMock, patch

from dotenv import load_dotenv

load_dotenv()

from services import pgvector_client as db
from services.payments import service
from services.payments import settlement
from services.payments.razorpay_provider import RazorpayProvider
from services.payments.models import CreatePaymentRequest, PaymentMethod, PaymentStatus


class PaymentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        environment = patch.dict(os.environ, {"RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": ""})
        environment.start()
        self.addCleanup(environment.stop)
        self.schema = "payment_test_" + uuid.uuid4().hex
        self.connect = db.get_conn
        conn = await self.connect()
        try:
            await conn.execute(f'CREATE SCHEMA "{self.schema}"')
        finally:
            await conn.close()

        async def isolated_connection():
            conn = await self.connect()
            await conn.execute(f'SET search_path TO "{self.schema}", public')
            return conn

        self.db_patch = patch.object(db, "get_conn", isolated_connection)
        self.service_patch = patch.object(service, "get_conn", isolated_connection, create=True)
        self.db_patch.start()
        self.service_patch.start()
        self.settlement_patch = patch.object(settlement, "get_conn", isolated_connection)
        self.settlement_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.service_patch.stop)
        self.addCleanup(self.settlement_patch.stop)
        self.isolated_connection = isolated_connection
        await db.setup_tables()
        conn = await isolated_connection()
        try:
            await conn.execute(
                "INSERT INTO knowledge_assets (vector_id, token_id, price_usdc) VALUES ($1, 1, 5)",
                str(uuid.uuid4()),
            )
        finally:
            await conn.close()
        self.request = CreatePaymentRequest(
            token_id=1, buyer_address="0x0000000000000000000000000000000000000001"
        )

    async def asyncTearDown(self):
        conn = await self.connect()
        try:
            await conn.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
        finally:
            await conn.close()

    async def test_restart_and_concurrent_confirmation(self):
        order = await service.PaymentService().create_order(self.request)
        self.assertEqual(order.amount_usdc, 5)
        self.assertEqual(order.status, PaymentStatus.PENDING)
        workers = [service.PaymentService(), service.PaymentService()]
        for worker in workers:
            saved = await worker.get_order(order.order_id)
            self.assertEqual(saved, order)
        provider = workers[0].providers[PaymentMethod.MOCK]
        verify = AsyncMock(wraps=provider.verify_payment)
        for worker in workers:
            worker.providers[PaymentMethod.MOCK].verify_payment = verify
        results = await asyncio.gather(*(w.confirm_order(order.order_id) for w in workers))
        self.assertEqual(verify.await_count, 1)
        self.assertEqual(results[0], results[1])
        saved = await service.PaymentService().get_order(order.order_id)
        self.assertEqual(saved.status, PaymentStatus.PROVIDER_CONFIRMED)
        self.assertTrue(saved.provider_payment_id)
        self.assertIsNone(saved.settlement_tx_hash)
        conn = await self.isolated_connection()
        try:
            row = await conn.fetchrow("SELECT created_at, updated_at FROM payment_orders WHERE order_id=$1", order.order_id)
            self.assertGreaterEqual(row["updated_at"], row["created_at"])
        finally:
            await conn.close()

    async def test_concurrent_checkout_creation_reuses_one_provider_order(self):
        workers = [service.PaymentService(), service.PaymentService()]
        from services.payments.mock_provider import MockPaymentProvider
        provider = MockPaymentProvider()
        create = AsyncMock(wraps=provider.create_payment)
        provider.create_payment = create
        for worker in workers:
            worker.providers[PaymentMethod.CARD] = provider
        request = self.request.model_copy(update={"payment_method": PaymentMethod.CARD})
        orders = await asyncio.gather(*(worker.create_order(request, user_id=123) for worker in workers))
        self.assertEqual(orders[0].order_id, orders[1].order_id)
        self.assertEqual(create.await_count, 1)

    def test_settlement_verifies_hash_receipt_depth_sender_and_call(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from web3 import Web3
        from services.payments.models import PaymentOrder
        raw = "0xabcd"
        account = SimpleNamespace(address="payer")
        market = Mock(address="market")
        market.encode_abi.return_value = "0x1234"
        w3 = Mock()
        receipt = SimpleNamespace(status=1, blockNumber=100, blockHash=bytes(32), transactionHash=Web3.keccak(hexstr="0xabcd"))
        w3.eth.get_block.return_value = SimpleNamespace(hash=bytes(32))
        w3.eth.get_transaction_receipt.return_value = receipt
        w3.eth.block_number = 100
        w3.eth.get_transaction.return_value = {"to": "market", "from": "payer", "input": bytes.fromhex("1234")}
        order = PaymentOrder(order_id="example", token_id=1, buyer_address=self.request.buyer_address,
            amount_usdc=5, payment_method=PaymentMethod.CARD, status=PaymentStatus.SETTLEMENT_PENDING,
            chain_id=80002, marketplace_address="market", listing_id=1,
            settlement_tx_hash=Web3.to_hex(Web3.keccak(hexstr=raw)))
        with patch.object(settlement, "connection", return_value=(w3, account, market)):
            self.assertEqual(settlement.broadcast_and_verify(order, raw), "pending")
            w3.eth.block_number = 101
            self.assertEqual(settlement.broadcast_and_verify(order, raw), "settled")
            receipt.status = 0
            self.assertEqual(settlement.broadcast_and_verify(order, raw), "reverted")
            w3.eth.block_number = 100
            self.assertEqual(settlement.broadcast_and_verify(order, raw), "pending")
            w3.eth.block_number = 101
            receipt.status = 1
            w3.eth.get_transaction.return_value["from"] = "attacker"
            with self.assertRaises(ValueError):
                settlement.broadcast_and_verify(order, raw)
            with self.assertRaises(ValueError):
                settlement.broadcast_and_verify(order, "0x12")

    async def test_invalid_and_failed_orders(self):
        worker = service.PaymentService()
        self.assertIsNone(await worker.get_order("missing"))
        with self.assertRaises(ValueError):
            await worker.confirm_order("missing")
        with self.assertRaises(ValueError):
            await worker.create_order(self.request.model_copy(update={"token_id": 999}))
        with self.assertRaises(ValueError):
            await worker.create_order(self.request.model_copy(update={"payment_method": PaymentMethod.CARD}))
        order = await worker.create_order(self.request)
        worker.providers[PaymentMethod.MOCK].verify_payment = AsyncMock(return_value={"success": False})
        failed = await worker.confirm_order(order.order_id)
        self.assertEqual(failed.status, PaymentStatus.FAILED)
        self.assertEqual(await service.PaymentService().get_order(order.order_id), failed)
        self.assertIsNone(failed.settlement_tx_hash)
        with self.assertRaises(ValueError):
            await worker.confirm_order(order.order_id)

    async def test_settlement_checkpoint_and_retry(self):
        worker = service.PaymentService()
        order = await worker.create_order(self.request)
        await worker.confirm_order(order.order_id)
        with self.assertRaises(ValueError):
            await settlement.settle_order(order.order_id)  # Mock must never spend funds.
        conn = await self.isolated_connection()
        try:
            await conn.execute("UPDATE payment_orders SET payment_method='card' WHERE order_id=$1", order.order_id)
        finally:
            await conn.close()
        with patch.object(settlement, "prepare", return_value=("0x123", "0xabc")) as prepare, \
             patch.object(settlement, "broadcast_and_verify", side_effect=[TimeoutError(), "settled"]) as broadcast, \
             patch.object(settlement, "has_entitlement", return_value=True):
            pending = await settlement.settle_order(order.order_id)
            self.assertEqual(pending.status, PaymentStatus.SETTLEMENT_PENDING)
            self.assertEqual(pending.settlement_tx_hash, "0x123")
            fresh = await service.PaymentService().get_order(order.order_id)
            self.assertNotIn("settlement_raw_tx", fresh.model_dump())
            # Browser polling cannot bypass the durable 30-second retry spacing.
            throttled = await settlement.settle_order(order.order_id)
            self.assertEqual(throttled.status, PaymentStatus.SETTLEMENT_PENDING)
            self.assertEqual(broadcast.call_count, 1)
            conn = await self.isolated_connection()
            await conn.execute("UPDATE payment_orders SET settlement_last_attempt_at=NOW()-INTERVAL '31 seconds' WHERE order_id=$1", order.order_id)
            await conn.close()
            granted = await settlement.settle_order(order.order_id)
            self.assertEqual(granted.status, PaymentStatus.ENTITLEMENT_GRANTED)
            self.assertEqual(prepare.call_count, 1)
            self.assertEqual(broadcast.call_count, 2)
            await settlement.settle_order(order.order_id)
            self.assertEqual(broadcast.call_count, 2)

    async def test_chain_success_without_entitlement_stays_settled(self):
        worker = service.PaymentService()
        order = await worker.create_order(self.request)
        conn = await self.isolated_connection()
        try:
            await conn.execute("UPDATE payment_orders SET payment_method='card', status='PROVIDER_CONFIRMED', provider_payment_id='pay_test' WHERE order_id=$1", order.order_id)
        finally:
            await conn.close()
        with patch.object(settlement, "prepare", return_value=("0x123", "0xabc")), \
             patch.object(settlement, "broadcast_and_verify", return_value="settled"), \
             patch.object(settlement, "has_entitlement", return_value=False):
            result = await settlement.settle_order(order.order_id)
            self.assertEqual(result.status, PaymentStatus.SETTLED)

    async def test_razorpay_signature_capture_and_quote(self):
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_example", "RAZORPAY_KEY_SECRET": "test-secret", "RAZORPAY_TEST_INR_PER_USDC": "85.50"}):
            provider = RazorpayProvider()
            quote = provider.quote(5)
        self.assertEqual(quote["fiat_amount"], 42750)
        order = (await service.PaymentService().create_order(self.request)).model_copy(update={
            **quote, "provider_order_id": "order_example", "payment_method": PaymentMethod.CARD,
        })
        confirmation = {"razorpay_order_id": "order_example", "razorpay_payment_id": "pay_example",
                        "razorpay_signature": hmac.new(b"test-secret", b"order_example|pay_example", hashlib.sha256).hexdigest()}
        payload = {"order_id": "order_example", "amount": 42750, "currency": "INR", "status": "authorized"}
        client = httpx.AsyncClient
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        with patch("services.payments.razorpay_provider.httpx.AsyncClient", side_effect=lambda **kw: client(transport=transport, **kw)):
            result = await provider.verify_payment(order, confirmation)
            self.assertTrue(result["pending"])
            self.assertFalse(result["success"])
            payload["status"] = "captured"
            self.assertTrue((await provider.verify_payment(order, confirmation))["success"])
            payload["amount"] = 1
            with self.assertRaises(ValueError):
                await provider.verify_payment(order, confirmation)
            with self.assertRaises(ValueError):
                await provider.verify_payment(order, {**confirmation, "razorpay_signature": "0" * 64})

    async def test_recovery_budget_and_refund_are_durable(self):
        from services.payments import recovery
        order = await service.PaymentService().create_order(self.request)
        conn = await self.isolated_connection()
        await conn.execute("UPDATE payment_orders SET payment_method='card', status='PROVIDER_CONFIRMED', provider_payment_id='pay_test', settlement_attempts=20 WHERE order_id=$1", order.order_id)
        await conn.close()
        with patch.object(settlement, "prepare") as prepare:
            results = await asyncio.gather(*(settlement.settle_order(order.order_id) for _ in range(8)), return_exceptions=True)
            self.assertTrue(any(not isinstance(value, Exception) and value.recovery_status == "REVIEW_REQUIRED" for value in results))
            prepare.assert_not_called()
            await settlement.reconcile_payments()
            prepare.assert_not_called()
        with patch.object(recovery, "verify_refund", new=AsyncMock(side_effect=ValueError("Not processed"))):
            with self.assertRaises(ValueError):
                await recovery.recover(order.order_id, "record-refund", "Provider refund inspected", "rfnd_test")
        self.assertEqual((await service.PaymentService().get_order(order.order_id)).recovery_status, "REVIEW_REQUIRED")
        async def refund_with_concurrent_settlement(*args):
            with self.assertRaises(ValueError):
                await settlement.settle_order(order.order_id)
        with patch.object(recovery, "verify_refund", new=AsyncMock(side_effect=refund_with_concurrent_settlement)):
            refunded = await recovery.recover(order.order_id, "record-refund", "Full provider refund verified", "rfnd_test")
        self.assertEqual(refunded.recovery_status, "REFUNDED")
        self.assertEqual(refunded.refund_id, "rfnd_test")
        with self.assertRaises(ValueError):
            await recovery.recover(order.order_id, "resume", "Cannot resume refunded order")
        with patch.object(settlement, "prepare") as prepare:
            await settlement.settle_order(order.order_id)
            prepare.assert_not_called()
        conn = await self.isolated_connection()
        self.assertEqual(await conn.fetchval("SELECT COUNT(*) FROM payment_recovery_events WHERE order_id=$1", order.order_id), 1)
        await conn.close()

    async def test_recovery_timeout_keeps_signed_transaction(self):
        order = await service.PaymentService().create_order(self.request)
        conn = await self.isolated_connection()
        await conn.execute("UPDATE payment_orders SET payment_method='card', status='SETTLEMENT_PENDING', provider_payment_id='pay_test', settlement_raw_tx='0xabc', settlement_tx_hash='0x123', settlement_started_at=NOW()-INTERVAL '16 minutes' WHERE order_id=$1", order.order_id)
        await conn.close()
        with patch.object(settlement, "broadcast_and_verify") as broadcast:
            held = await settlement.settle_order(order.order_id)
            self.assertEqual(held.recovery_status, "REVIEW_REQUIRED")
            self.assertEqual(held.settlement_tx_hash, "0x123")
            broadcast.assert_not_called()
        conn = await self.isolated_connection()
        self.assertEqual(await conn.fetchval("SELECT settlement_raw_tx FROM payment_orders WHERE order_id=$1", order.order_id), "0xabc")
        await conn.close()

    def test_refund_rejects_pending_successful_and_shallow_receipts(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from web3 import Web3
        from services.payments.recovery import require_refundable
        from services.payments.models import PaymentOrder
        order = PaymentOrder(order_id="test", token_id=1, buyer_address=self.request.buyer_address,
            amount_usdc=5, payment_method=PaymentMethod.CARD, status=PaymentStatus.SETTLEMENT_PENDING,
            chain_id=80002, marketplace_address="market", settlement_tx_hash=Web3.to_hex(Web3.keccak(hexstr="0xabcd")))
        w3 = Mock()
        receipt = SimpleNamespace(status=1, blockNumber=100, blockHash=bytes(32), transactionHash=Web3.keccak(hexstr="0xabcd"))
        w3.eth.get_block.return_value = SimpleNamespace(hash=bytes(32))
        w3.eth.get_transaction_receipt.return_value = receipt
        w3.eth.block_number = 101
        with patch.object(settlement, "connection", return_value=(w3, None, SimpleNamespace(address="market"))):
            with self.assertRaises(ValueError):
                require_refundable(order, "0xabcd")
            receipt.status = 0
            w3.eth.block_number = 100
            with self.assertRaises(ValueError):
                require_refundable(order, "0xabcd")
            w3.eth.block_number = 101
            require_refundable(order, "0xabcd")
            from web3.exceptions import TransactionNotFound
            w3.eth.get_transaction_receipt.side_effect = TransactionNotFound("Not found")
            with self.assertRaises(TransactionNotFound):
                require_refundable(order, "0xabcd")

    async def test_refund_checks_provider_amount_identity_and_status(self):
        from services.payments.recovery import verify_refund
        order = (await service.PaymentService().create_order(self.request)).model_copy(update={
            "provider_payment_id": "pay_test", "provider_order_id": "order_test", "fiat_amount": 40000, "fiat_currency": "INR"})
        refund = dict(id="rfnd_test", payment_id="pay_test", status="processed", amount=40000, currency="INR")
        payment = dict(id="pay_test", order_id="order_test", status="refunded", amount=40000, amount_refunded=40000, currency="INR")
        client = httpx.AsyncClient
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json=refund if "/refunds/" in request.url.path else payment))
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_example", "RAZORPAY_KEY_SECRET": "test-secret"}), \
             patch("services.payments.recovery.httpx.AsyncClient", side_effect=lambda **kw: client(transport=transport, **kw)):
            await verify_refund(order, "rfnd_test")
            for field, value in [("status", "pending"), ("amount", 39999), ("payment_id", "pay_other"), ("currency", "USD")]:
                original = refund[field]
                refund[field] = value
                with self.assertRaises(ValueError):
                    await verify_refund(order, "rfnd_test")
                refund[field] = original
            payment["order_id"] = "order_other"
            with self.assertRaises(ValueError):
                await verify_refund(order, "rfnd_test")

    async def test_operator_role_records_session_identity_and_cannot_rewrite_audit(self):
        from pathlib import Path
        import asyncpg
        role = "recovery_test_" + uuid.uuid4().hex
        conn = await self.isolated_connection()
        order = await service.PaymentService().create_order(self.request)
        actor = await conn.fetchval("SELECT SESSION_USER")
        template = Path(__file__).resolve().parents[1].joinpath("operator_roles.sql").read_text(encoding="utf-8")
        template = template.replace("dkm_recovery_operator", role).replace("SCHEMA public", f'SCHEMA "{self.schema}"').replace("public.", f'"{self.schema}".')
        try:
            await conn.execute(template)
            await conn.execute(f'SET ROLE "{role}"')
            await conn.execute("INSERT INTO payment_recovery_events(order_id,action,reason) VALUES($1,'hold','Testing individual session attribution')", order.order_id)
            self.assertEqual(await conn.fetchval("SELECT actor FROM payment_recovery_events WHERE order_id=$1", order.order_id), actor)
            with self.assertRaises(asyncpg.InsufficientPrivilegeError):
                await conn.execute("UPDATE payment_recovery_events SET actor='forged'")
            with self.assertRaises(asyncpg.InsufficientPrivilegeError):
                await conn.execute("UPDATE payment_orders SET settlement_raw_tx='forged'")
            with self.assertRaises(asyncpg.InsufficientPrivilegeError):
                await conn.execute("INSERT INTO payment_recovery_events(order_id,action,reason,actor) VALUES($1,'hold','Forged actor','forged')", order.order_id)
        finally:
            await conn.execute("RESET ROLE")
            if await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname=$1", role):
                await conn.execute(f'DROP OWNED BY "{role}"')
                await conn.execute(f'DROP ROLE "{role}"')
            await conn.close()

    def test_wallet_validation(self):
        for address in ("no-wallet", "0x" + "0" * 40):
            with self.assertRaises(ValueError):
                CreatePaymentRequest(token_id=1, buyer_address=address)

    async def test_mined_revert_requires_explicit_retry(self):
        order = await service.PaymentService().create_order(self.request)
        conn = await self.isolated_connection()
        try:
            await conn.execute("UPDATE payment_orders SET payment_method='card', status='PROVIDER_CONFIRMED', provider_payment_id='pay_test' WHERE order_id=$1", order.order_id)
        finally:
            await conn.close()
        with patch.object(settlement, "prepare", side_effect=[("0x1", "0xaa"), ("0x2", "0xbb")]) as prepare, \
             patch.object(settlement, "broadcast_and_verify", side_effect=["reverted", "reverted", "settled"]), \
             patch.object(settlement, "has_entitlement", return_value=True):
            failed = await settlement.settle_order(order.order_id)
            self.assertEqual(failed.status, PaymentStatus.FAILED)
            self.assertEqual(failed.settlement_tx_hash, "0x1")
            await settlement.reconcile_payments()
            self.assertEqual(prepare.call_count, 1)  # Background reconciliation must not spend gas again.
            held = await settlement.settle_order(order.order_id)
            self.assertEqual(held.recovery_status, "REVIEW_REQUIRED")
            from services.payments.recovery import recover
            await recover(order.order_id, "resume", "Listing and funding checked by operator")
            retried = await settlement.settle_order(order.order_id)
            self.assertEqual(retried.status, PaymentStatus.ENTITLEMENT_GRANTED)
            self.assertEqual(retried.settlement_tx_hash, "0x2")

    async def test_bad_callback_does_not_poison_pending_order(self):
        worker = service.PaymentService()
        order = await worker.create_order(self.request)
        worker.providers[PaymentMethod.MOCK].verify_payment = AsyncMock(side_effect=ValueError("Invalid signature"))
        with self.assertRaises(ValueError):
            await worker.confirm_order(order.order_id)
        self.assertEqual((await worker.get_order(order.order_id)).status, PaymentStatus.PENDING)

    async def test_webhook_checks_raw_body_signature(self):
        import main
        from fastapi import HTTPException
        from starlette.requests import Request
        body = b'{"event":"payment.authorized"}'

        def request(signature):
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            return Request({"type": "http", "headers": [(b"x-razorpay-signature", signature)]}, receive)

        with patch.dict(os.environ, {"RAZORPAY_WEBHOOK_SECRET": "webhook-test-secret"}):
            with self.assertRaises(HTTPException) as invalid:
                await main.razorpay_webhook(request(b"invalid"))
            self.assertEqual(invalid.exception.status_code, 400)
            signature = hmac.new(b"webhook-test-secret", body, hashlib.sha256).hexdigest().encode()
            self.assertEqual(await main.razorpay_webhook(request(signature)), {"received": True})


if __name__ == "__main__":
    unittest.main()
