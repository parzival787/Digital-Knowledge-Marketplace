"""Funded Amoy settlement with a durable signed transaction before broadcast."""
import asyncio
import os
import logging
from datetime import datetime, timezone, timedelta

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound, TimeExhausted

from services.pgvector_client import get_conn
from services.knowledge_asset_abi import KNOWLEDGE_ASSET_ABI
from services.marketplace_abi import MARKETPLACE_ABI
from .models import PaymentMethod, PaymentOrder, PaymentStatus


def function_abi(name, inputs, outputs, state="view"):
    return {"type": "function", "name": name, "stateMutability": state,
            "inputs": [{"name": "", "type": value} for value in inputs],
            "outputs": [{"name": "", "type": value} for value in outputs]}


SETTLEMENT_ABI = MARKETPLACE_ABI + [
    function_abi("tokenToListing", ["uint256"], ["uint256"]),
    function_abi("listings", ["uint256"], ["uint256", "uint256", "address", "uint8", "bool", "uint40"]),
    function_abi("usdc", [], ["address"]),
    function_abi("knowledgeAsset", [], ["address"]),
    function_abi("settledPayments", ["address", "bytes32"], ["bool"]),
    function_abi("buyAssetFor", ["uint256", "address", "uint256", "bytes32"], [], "nonpayable"),
]
TOKEN_ABI = [
    function_abi("balanceOf", ["address"], ["uint256"]),
    function_abi("allowance", ["address", "address"], ["uint256"]),
]


def connection():
    key = os.getenv("SETTLEMENT_PRIVATE_KEY", "")
    if os.getenv("SETTLEMENT_ENABLED") != "true" or not key:
        raise ValueError("Test checkout is unavailable until the settlement wallet and contract are configured")
    w3 = Web3(Web3.HTTPProvider(os.environ["BLOCKCHAIN_RPC_URL"], request_kwargs={"timeout": 15}))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if w3.eth.chain_id != 80002:
        raise ValueError("Settlement is restricted to Polygon Amoy testnet")
    account = w3.eth.account.from_key(key)
    market = w3.eth.contract(address=Web3.to_checksum_address(os.environ["MARKETPLACE_ADDRESS"]), abi=SETTLEMENT_ABI)
    return w3, account, market


def validate_checkout(order: PaymentOrder) -> dict:
    w3, account, market = connection()
    # Reading this new method fails closed on the old deployment.
    market.functions.settledPayments(account.address, bytes(32)).call()
    registry = w3.eth.contract(address=market.functions.knowledgeAsset().call(), abi=KNOWLEDGE_ASSET_ABI)
    asset = registry.functions.getAsset(order.token_id).call()
    if not asset[6]:
        raise ValueError("This asset is inactive")
    listing_id = market.functions.tokenToListing(order.token_id).call()
    listing = market.functions.listings(listing_id).call()
    amount = order.amount_usdc * 1_000_000
    if not listing_id or not listing[4] or listing[3] != 0 or listing[0] != order.token_id:
        raise ValueError("This asset is not available at a fixed price")
    if listing[1] != amount:
        raise ValueError("Database and listing prices differ; the seller must reconcile them before fiat checkout")
    if listing[2].lower() == order.buyer_address.lower():
        raise ValueError("Sellers cannot buy their own asset")
    from services.blockchain import has_purchased
    if has_purchased(order.token_id, order.buyer_address):
        raise ValueError("This wallet already has purchase entitlement")
    token = w3.eth.contract(address=market.functions.usdc().call(), abi=TOKEN_ABI)
    if token.functions.balanceOf(account.address).call() < amount:
        raise ValueError("Settlement wallet has insufficient test USDC")
    if token.functions.allowance(account.address, market.address).call() < amount:
        raise ValueError("Settlement wallet must approve test USDC before enabling checkout")
    return {"listing_id": listing_id, "marketplace_address": market.address, "chain_id": 80002}


def prepare(order: PaymentOrder):
    w3, account, market = connection()
    if order.chain_id != 80002 or order.marketplace_address != market.address:
        raise ValueError("Order belongs to a different deployment; operator review required")
    args = [order.listing_id, order.buyer_address, order.amount_usdc * 1_000_000, Web3.keccak(text=order.order_id)]
    tx = market.functions.buyAssetFor(*args).build_transaction({
        "from": account.address, "chainId": 80002,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "gasPrice": w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    return Web3.to_hex(signed.hash), Web3.to_hex(signed.raw_transaction)


def confirmed_receipt(w3, tx_hash, receipt):
    if w3.eth.block_number < receipt.blockNumber + 1:
        return False
    canonical = w3.eth.get_block(receipt.blockNumber)
    fresh = w3.eth.get_transaction_receipt(tx_hash)
    if (Web3.to_hex(receipt.transactionHash).lower() != tx_hash.lower()
            or fresh.transactionHash != receipt.transactionHash
            or fresh.blockHash != receipt.blockHash or fresh.blockNumber != receipt.blockNumber
            or fresh.status != receipt.status or canonical.hash != receipt.blockHash):
        raise ValueError("Settlement receipt changed or is no longer canonical")
    return True


def broadcast_and_verify(order: PaymentOrder, raw: str):
    w3, account, market = connection()
    if order.chain_id != 80002 or order.marketplace_address != market.address:
        raise ValueError("Settlement deployment changed; operator review required")
    tx_hash = order.settlement_tx_hash
    if Web3.to_hex(Web3.keccak(hexstr=raw)).lower() != tx_hash.lower():
        raise ValueError("Stored settlement transaction does not match its hash")
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except TransactionNotFound:
        try:
            w3.eth.get_transaction(tx_hash)
        except TransactionNotFound:
            w3.eth.send_raw_transaction(raw)
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=15, poll_latency=1)
        except TimeExhausted:
            return "pending"
    if not confirmed_receipt(w3, tx_hash, receipt):
        return "pending"
    expected_data = market.encode_abi("buyAssetFor", args=[
        order.listing_id, order.buyer_address, order.amount_usdc * 1_000_000, Web3.keccak(text=order.order_id)
    ])
    tx = w3.eth.get_transaction(tx_hash)
    if (tx["to"] != market.address or tx["from"] != account.address
            or Web3.to_hex(tx["input"]).lower() != expected_data.lower()):
        raise ValueError("Settlement transaction does not match this order")
    if receipt.status != 1:
        return "reverted"
    return "settled"


def has_entitlement(order: PaymentOrder):
    _, account, market = connection()
    return (market.functions.settledPayments(account.address, Web3.keccak(text=order.order_id)).call()
            and market.functions.hasPurchased(order.token_id, order.buyer_address).call())


async def settle_order(order_id: str) -> PaymentOrder:
    conn = await get_conn()
    try:
        # ponytail: one dedicated signer, serialize nonce allocation across workers;
        # use separate signer queues if settlement throughput becomes significant.
        locked = await conn.fetchval("SELECT pg_try_advisory_lock(80002, 7319)")
        if not locked:
            raise ValueError("Another settlement is running; retry shortly")
        row = await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1", order_id)
        if not row:
            raise ValueError("Payment order not found")
        order = PaymentOrder.model_validate(dict(row))
        if order.payment_method not in (PaymentMethod.UPI, PaymentMethod.CARD):
            raise ValueError("Mock payments never settle on-chain")
        if order.status == PaymentStatus.ENTITLEMENT_GRANTED:
            return order
        if order.recovery_status:
            return order
        if order.status not in (PaymentStatus.PROVIDER_CONFIRMED, PaymentStatus.SETTLEMENT_PENDING, PaymentStatus.SETTLED, PaymentStatus.FAILED):
            raise ValueError("Only provider-confirmed payments can settle")
        if not order.provider_payment_id:
            raise ValueError("Provider payment has not been verified")
        now = datetime.now(timezone.utc)
        started = row["settlement_started_at"]
        # A timeout is uncertainty, never proof that a signed transaction failed.
        if row["settlement_attempts"] >= 20 or (started and now - started >= timedelta(minutes=15)):
            await conn.execute("""
                UPDATE payment_orders SET recovery_status='REVIEW_REQUIRED',
                    error='Payment needs operator review. Do not pay again; settlement is paused.',
                    updated_at=clock_timestamp() WHERE order_id=$1
            """, order_id)
            return PaymentOrder.model_validate(dict(await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1", order_id)))
        last_attempt = row["settlement_last_attempt_at"]
        if last_attempt and now - last_attempt < timedelta(seconds=30):
            return order
        await conn.execute("""
            UPDATE payment_orders SET settlement_attempts=settlement_attempts+1,
                settlement_started_at=COALESCE(settlement_started_at, clock_timestamp()),
                settlement_last_attempt_at=clock_timestamp() WHERE order_id=$1
        """, order_id)
        raw = row["settlement_raw_tx"]
        if order.status == PaymentStatus.FAILED:
            # Only an explicitly requested retry of a proven mined revert may
            # replace a transaction. Failed provider payments never reach here.
            if not raw or await asyncio.to_thread(broadcast_and_verify, order, raw) != "reverted":
                raise ValueError("This failed payment requires operator review")
            await conn.execute("UPDATE payment_orders SET status='PROVIDER_CONFIRMED', settlement_raw_tx=NULL, settlement_tx_hash=NULL WHERE order_id=$1", order_id)
            raw = None
            order.status = PaymentStatus.PROVIDER_CONFIRMED
            order.settlement_tx_hash = None
        try:
            if not raw:
                # Do not allocate another nonce while a previously signed transaction
                # is pending; the same raw transaction can be rebroadcast after a crash.
                pending = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM payment_orders WHERE status='SETTLEMENT_PENDING' AND order_id<>$1)", order_id)
                if pending:
                    raise ValueError("An earlier settlement is pending; reconcile it before retrying")
                tx_hash, raw = await asyncio.to_thread(prepare, order)
                await conn.execute("""
                    UPDATE payment_orders SET status='SETTLEMENT_PENDING',
                        settlement_tx_hash=$2, settlement_raw_tx=$3, error=NULL, updated_at=clock_timestamp()
                    WHERE order_id=$1
                """, order_id, tx_hash, raw)
                order.status = PaymentStatus.SETTLEMENT_PENDING
                order.settlement_tx_hash = tx_hash
            outcome = await asyncio.to_thread(broadcast_and_verify, order, raw)
            if outcome == "reverted":
                # A mined revert consumed the nonce but granted no entitlement.
                await conn.execute("""
                    UPDATE payment_orders SET status='FAILED',
                        recovery_status='REVIEW_REQUIRED',
                        error='Settlement reverted; retry after resolving the listing or funding issue',
                        updated_at=clock_timestamp() WHERE order_id=$1
                """, order_id)
            elif outcome == "pending":
                await conn.execute("UPDATE payment_orders SET status='SETTLEMENT_PENDING', updated_at=clock_timestamp() WHERE order_id=$1", order_id)
            elif outcome == "settled":
                await conn.execute("UPDATE payment_orders SET status='SETTLED', error=NULL, updated_at=clock_timestamp() WHERE order_id=$1", order_id)
                if await asyncio.to_thread(has_entitlement, order):
                    await conn.execute("UPDATE payment_orders SET status='ENTITLEMENT_GRANTED', updated_at=clock_timestamp() WHERE order_id=$1", order_id)
        except Exception:
            # Keep the signed transaction/hash and status for safe reconciliation.
            await conn.execute("UPDATE payment_orders SET error='Settlement could not be verified; retry or request operator review', updated_at=clock_timestamp() WHERE order_id=$1", order_id)
        row = await conn.fetchrow("SELECT * FROM payment_orders WHERE order_id=$1", order_id)
        return PaymentOrder.model_validate(dict(row))
    finally:
        await conn.close()  # Releases the session advisory lock even on cancellation.


async def reconcile_payments():
    conn = await get_conn()
    try:
        rows = await conn.fetch("""
            SELECT order_id FROM payment_orders
            WHERE payment_method IN ('upi', 'card')
              AND status IN ('PROVIDER_CONFIRMED', 'SETTLEMENT_PENDING', 'SETTLED')
              AND recovery_status IS NULL
            ORDER BY CASE WHEN status='SETTLEMENT_PENDING' THEN 0 ELSE 1 END, created_at
            LIMIT 20
        """)
    finally:
        await conn.close()
    for row in rows:
        try:
            await settle_order(row["order_id"])
        except ValueError:
            pass  # Another process owns the signer lock; the next pass retries.


async def settlement_worker():
    while True:
        try:
            await reconcile_payments()
        except Exception:
            # Database/provider outages never discard durable payment state.
            logging.getLogger(__name__).warning("Payment reconciliation is unavailable; retrying in 15 seconds")
        await asyncio.sleep(15)
