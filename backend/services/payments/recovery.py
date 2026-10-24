"""Operator-only recovery. No refund submission and no transaction broadcasting."""
import asyncio
import re

import httpx
from web3 import Web3

from services import pgvector_client as db
from . import settlement
from .models import PaymentOrder, PaymentStatus
from .razorpay_provider import RazorpayProvider


def require_refundable(order, raw):
    if order.status not in (PaymentStatus.PROVIDER_CONFIRMED, PaymentStatus.FAILED, PaymentStatus.SETTLEMENT_PENDING):
        raise ValueError("Settled or unverified orders cannot be refunded through this tool")
    if not raw and not order.settlement_tx_hash:
        return
    if not raw or not order.settlement_tx_hash:
        raise ValueError("Incomplete transaction record requires investigation")
    w3, _, market = settlement.connection()
    if order.chain_id != 80002 or order.marketplace_address != market.address:
        raise ValueError("Deployment mismatch")
    if Web3.to_hex(Web3.keccak(hexstr=raw)).lower() != order.settlement_tx_hash.lower():
        raise ValueError("Transaction record mismatch")
    receipt = w3.eth.get_transaction_receipt(order.settlement_tx_hash)
    if receipt.status != 0 or not settlement.confirmed_receipt(w3, order.settlement_tx_hash, receipt):
        raise ValueError("Only a confirmed mined revert is eligible; pending or successful transactions must not be refunded")


async def verify_refund(order, refund_id):
    provider = RazorpayProvider()
    if not provider.key.startswith("rzp_test_") or not provider.secret:
        raise ValueError("Recovery requires Razorpay test credentials")
    if not re.fullmatch(r"rfnd_[A-Za-z0-9]{1,95}", refund_id):
        raise ValueError("Invalid refund ID")
    if not re.fullmatch(r"pay_[A-Za-z0-9]{1,96}", order.provider_payment_id or ""):
        raise ValueError("Invalid stored payment ID")
    async with httpx.AsyncClient(timeout=20, auth=(provider.key, provider.secret)) as client:
        response = await client.get(f"https://api.razorpay.com/v1/refunds/{refund_id}")
        response.raise_for_status()
        refund = response.json()
        response = await client.get(f"https://api.razorpay.com/v1/payments/{order.provider_payment_id}")
        response.raise_for_status()
        payment = response.json()
    if not order.fiat_amount or (
        refund.get("id") != refund_id or refund.get("payment_id") != order.provider_payment_id
        or refund.get("status") != "processed" or refund.get("amount") != order.fiat_amount
        or refund.get("currency") != order.fiat_currency
        or payment.get("id") != order.provider_payment_id or payment.get("order_id") != order.provider_order_id
        or payment.get("amount") != order.fiat_amount or payment.get("currency") != order.fiat_currency
        or payment.get("amount_refunded") != order.fiat_amount or payment.get("status") != "refunded"
    ):
        raise ValueError("Provider has not verified a matching full refund")


async def recover(order_id, action, reason, refund_id=None):
    if action not in ("hold", "resume", "record-refund") or not 10 <= len(reason.strip()) <= 500:
        raise ValueError("Choose a valid action and provide a 10–500 character audit reason")
    conn = await db.get_conn()
    try:
        if not await conn.fetchval("SELECT pg_try_advisory_lock(80002, 7319)"):
            raise ValueError("Settlement is running; retry shortly")
        async with conn.transaction():
            row = await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1 FOR UPDATE", order_id)
            if not row:
                raise ValueError("Order not found")
            order = PaymentOrder.model_validate(dict(row))
            if order.payment_method not in ("upi", "card") or not order.provider_payment_id:
                raise ValueError("Only verified fiat payments can enter recovery")
            if order.recovery_status == "REFUNDED" or order.status == PaymentStatus.ENTITLEMENT_GRANTED:
                raise ValueError("This order is already complete")
            if action == "hold":
                await conn.execute("UPDATE payment_orders SET recovery_status='REVIEW_REQUIRED', error='Payment needs operator review. Do not pay again; settlement is paused.' WHERE order_id=$1", order_id)
            else:
                if order.recovery_status != "REVIEW_REQUIRED":
                    raise ValueError("Hold the order before recovery")
                if action == "resume":
                    await conn.execute("""UPDATE payment_orders SET recovery_status=NULL, error=NULL,
                        settlement_attempts=0, settlement_started_at=NULL, settlement_last_attempt_at=NULL
                        WHERE order_id=$1""", order_id)
                else:
                    await asyncio.to_thread(require_refundable, order, row["settlement_raw_tx"])
                    await verify_refund(order, refund_id or "")
                    await conn.execute("UPDATE payment_orders SET recovery_status='REFUNDED', refund_id=$2, error=NULL WHERE order_id=$1", order_id, refund_id)
            await conn.execute("UPDATE payment_orders SET updated_at=clock_timestamp() WHERE order_id=$1", order_id)
            await conn.execute("INSERT INTO payment_recovery_events(order_id, action, reason) VALUES($1,$2,$3)", order_id, action, reason.strip())
            return PaymentOrder.model_validate(dict(await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1", order_id)))
    finally:
        await conn.close()
