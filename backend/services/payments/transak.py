"""Transak staging wallet-funding sessions; never a marketplace payment confirmation."""
import hashlib
import asyncio
import logging
import ipaddress
import json
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Literal
import os
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from services.auth import ORIGIN, current_user, wallet_user, throttle
from services.content_security import seal, unseal, master_key
from services.pgvector_client import get_conn

router = APIRouter(prefix="/api/payments/transak", tags=["Sandbox funding"])


async def setup_transak():
    conn = await get_conn()
    try:
        await conn.execute("""
            ALTER TABLE app_users ADD COLUMN IF NOT EXISTS payout_currency TEXT NOT NULL DEFAULT 'USDC';
            CREATE TABLE IF NOT EXISTS transak_staging_tokens (
                credential_hash TEXT PRIMARY KEY, ciphertext BYTEA NOT NULL,
                wrapped_key TEXT NOT NULL, expires_at DOUBLE PRECISION NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transak_staging_orders (
                order_id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
                wallet_address TEXT NOT NULL, receipt JSONB NOT NULL,
                checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            ALTER TABLE transak_staging_orders ADD COLUMN IF NOT EXISTS next_check_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
            ALTER TABLE transak_staging_orders ADD COLUMN IF NOT EXISTS refresh_error TEXT;
            CREATE INDEX IF NOT EXISTS transak_orders_recheck ON transak_staging_orders(next_check_at);
            CREATE INDEX IF NOT EXISTS transak_orders_account ON transak_staging_orders(user_id,checked_at DESC)
        """)
    finally:
        await conn.close()


def configuration():
    key = (os.getenv("TRANSAK_STAGING_API_KEY") or os.getenv("transak_api_key", "")).strip()
    secret = (os.getenv("TRANSAK_STAGING_API_SECRET") or os.getenv("transak_api_secret", "")).strip()
    if not key or not secret:
        raise ValueError("Transak staging credentials are not configured")
    master_key()
    return key, secret


async def provider_json(client, url, method="POST", **kwargs):
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        data = response.json()["data"]
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        # Provider bodies and request headers can contain credentials and session URLs.
        raise ValueError("Transak staging request failed. Check credentials and partner IP/domain allowlists.") from None


async def access_token(conn, client, key, secret, fingerprint, row):
    if row and row["expires_at"] > time.time() + 60:
        token = unseal(row["ciphertext"], row["wrapped_key"], fingerprint).decode()
    else:
        data = await provider_json(client, "https://api-stg.transak.com/partners/api/v2/refresh-token",
                                   headers={"api-secret": secret}, json={"apiKey": key})
        token, expiry = data.get("accessToken"), data.get("expiresAt")
        if not isinstance(token, str) or not token or not isinstance(expiry, (float, int)) or not time.time() + 60 < expiry < time.time() + 366 * 86400:
            raise ValueError("Transak returned an invalid token expiry")
        ciphertext, wrapped = seal(token.encode(), fingerprint)
        await conn.execute("""INSERT INTO transak_staging_tokens VALUES ($1,$2,$3,$4)
            ON CONFLICT (credential_hash) DO UPDATE SET ciphertext=$2, wrapped_key=$3, expires_at=$4
            """, fingerprint, ciphertext, wrapped, float(expiry))
    return token


async def create_session(wallet, user_ip, payout_currency=None):
    if payout_currency is not None and payout_currency not in ("USD", "EUR", "INR", "IDR"):
        raise ValueError("Unsupported payout currency preference")
    key, secret = configuration()
    ipaddress.ip_address(user_ip)
    params = {"apiKey": key, "referrerDomain": ORIGIN,
              "redirectURL": ORIGIN + ("/account" if payout_currency else "/funding")}
    if payout_currency:
        params.update(productsAvailed="SELL", fiatCurrency=payout_currency)
    else:
        params.update(productsAvailed="BUY", cryptoCurrencyCode="USDC", network="polygon",
                      walletAddress=wallet, disableWalletAddressForm=True)
    fingerprint = hashlib.sha256((key + ":" + secret).encode()).hexdigest()
    conn = await get_conn()
    try:
        async with conn.transaction():
            # Refresh invalidates the previous token; serialize across backend workers.
            await conn.execute("SELECT pg_advisory_xact_lock(80002,7320)")
            row = await conn.fetchrow("SELECT * FROM transak_staging_tokens WHERE credential_hash=$1", fingerprint)
            async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
                token = await access_token(conn, client, key, secret, fingerprint, row)
                data = await provider_json(client, "https://api-gateway-stg.transak.com/api/v2/auth/session",
                    headers={"access-token": token, "x-api-key": key, "x-user-ip": user_ip},
                    json={"widgetParams": params})
                url = data.get("widgetUrl", "")
                parsed = urlsplit(url)
                if parsed.scheme != "https" or parsed.netloc != "global-stg.transak.com" or not parsed.query:
                    raise ValueError("Transak returned an unexpected staging URL")
                return url
    finally:
        await conn.close()


@router.get("/status")
async def status(response: Response, user=Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    try:
        configuration()
        configured = True
    except ValueError:
        configured = False
    return {"configured": configured, "environment": "staging", "grants_access": False}


@router.post("/session")
async def session(request: Request, response: Response, user=Depends(wallet_user)):
    response.headers["Cache-Control"] = "no-store"
    await throttle(request, "transak-session:" + str(user["id"]))
    try:
        url = await create_session(user["wallet_address"], request.client.host if request.client else "")
    except Exception:
        raise HTTPException(503, "Transak sandbox is unavailable. Check staging credentials, content key and provider IP/domain allowlists.") from None
    return {"widget_url": url, "environment": "staging", "expires_in_seconds": 300, "grants_access": False}


class OrderLookup(BaseModel):
    order_id: UUID


def verified_order(data, order_id, wallet):
    if (str(data.get("_id")) != order_id
            or str(data.get("walletAddress", "")).lower() != wallet.lower()
            or data.get("isBuyOrSell") != "BUY"
            or data.get("network") != "polygon"
            or data.get("cryptoCurrency") != "USDC"):
        raise ValueError("Order does not match your verified wallet and the sandbox funding route")
    status = data.get("status")
    currency = data.get("fiatCurrency")
    if not isinstance(status, str) or not re.fullmatch(r"[A-Z_]{1,64}", status):
        raise ValueError("Invalid provider status")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Invalid provider currency")
    result = {"order_id": order_id, "status": status, "fiat_currency": currency,
              "environment": "staging", "grants_access": False}
    for source, target in (("fiatAmount", "fiat_amount"), ("amountPaid", "amount_paid"),
                           ("totalFeeInFiat", "provider_fee"), ("cryptoAmount", "crypto_amount")):
        value = data.get(source)
        if value is None:
            result[target] = None
            continue
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError("Invalid provider amount") from None
        if (not amount.is_finite() or not 0 <= amount <= Decimal("1000000000000")
                or amount.as_tuple().exponent < -18):
            raise ValueError("Invalid provider amount")
        result[target] = format(amount, "f")
    # Do not trust provider links or pretend a dummy hash is a chain receipt.
    tx = data.get("transactionHash")
    result["transaction_hash"] = tx if isinstance(tx, str) and re.fullmatch(r"0x[a-fA-F0-9]{64}", tx) else None
    return result


def reconcile_receipt(previous, current):
    """Unordered provider observations cannot silently undo terminal evidence."""
    current = {**current, "verification_state": "provider_verified"}
    if not previous:
        return current
    old, new = previous["status"], current["status"]
    terminal = {"COMPLETED", "REFUNDED", "FAILED", "CANCELLED", "EXPIRED"}
    stable_fields = ("fiat_currency", "fiat_amount", "crypto_amount", "amount_paid", "provider_fee", "transaction_hash")
    changed_completion = old == "COMPLETED" and new == "COMPLETED" and any(
        previous.get(field) != current.get(field) for field in stable_fields)
    if (previous.get("verification_state") == "review_required" or changed_completion or
            old in terminal and new != old and not (old == "COMPLETED" and new == "REFUNDED")):
        # Keep original evidence; a later completion after failure is a late-payment
        # conflict, not permission to settle or unlock a knowledge asset.
        return {**previous, "verification_state": "review_required", "observed_status": new}
    return current


async def refresh_order(order_id, user):
    key, secret = configuration()
    fingerprint = hashlib.sha256((key + ":" + secret).encode()).hexdigest()
    conn = await get_conn()
    try:
        async with conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock(80002,7320)")
            existing = await conn.fetchrow("SELECT user_id,receipt FROM transak_staging_orders WHERE order_id=$1", UUID(order_id))
            if existing and existing["user_id"] != user["id"]:
                raise ValueError("Order belongs to a different account")
            row = await conn.fetchrow("SELECT * FROM transak_staging_tokens WHERE credential_hash=$1", fingerprint)
            async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
                token = await access_token(conn, client, key, secret, fingerprint, row)
                data = await provider_json(client, "https://api-stg.transak.com/partners/api/v2/order/" + order_id,
                    method="GET", headers={"access-token": token, "x-api-key": key})
            receipt = verified_order(data, order_id, user["wallet_address"])
            receipt = reconcile_receipt(json.loads(existing["receipt"]) if existing else None, receipt)
            await conn.execute("""INSERT INTO transak_staging_orders(order_id,user_id,wallet_address,receipt)
                VALUES ($1,$2,$3,$4) ON CONFLICT (order_id) DO UPDATE SET receipt=$4,checked_at=NOW()
                """, UUID(order_id), user["id"], user["wallet_address"], json.dumps(receipt))
            await conn.execute("""UPDATE transak_staging_orders SET refresh_error=NULL,
                next_check_at=NOW()+INTERVAL '5 minutes' WHERE order_id=$1""", UUID(order_id))
            return receipt
    finally:
        await conn.close()


@router.post("/orders/refresh")
async def check_order(body: OrderLookup, request: Request, user=Depends(wallet_user)):
    await throttle(request, "transak-status:" + str(user["id"]))
    try:
        return await refresh_order(str(body.order_id), user)
    except Exception:
        raise HTTPException(503, "Could not verify this sandbox order. Check the order ID, wallet and provider availability.") from None


@router.get("/orders")
async def orders(user=Depends(current_user)):
    conn = await get_conn()
    try:
        rows = await conn.fetch("""SELECT receipt,checked_at,refresh_error FROM transak_staging_orders
            WHERE user_id=$1 ORDER BY checked_at DESC LIMIT 50""", user["id"])
        return {"orders": [{**json.loads(row["receipt"]), "checked_at": row["checked_at"].isoformat(),
                            "refresh_error": row["refresh_error"]} for row in rows]}
    finally:
        await conn.close()


async def reconcile_saved_orders():
    """Read-only provider polling. Claim batches durably across backend workers."""
    configuration()
    conn = await get_conn()
    try:
        async with conn.transaction():
            rows = await conn.fetch("""SELECT o.order_id,o.user_id,o.wallet_address,o.checked_at
                FROM transak_staging_orders o JOIN app_users u ON u.id=o.user_id
                WHERE o.next_check_at<=NOW() AND lower(u.wallet_address)=lower(o.wallet_address)
                AND COALESCE(o.receipt->>'verification_state','')<>'review_required'
                AND o.receipt->>'status'<>'REFUNDED'
                ORDER BY o.next_check_at LIMIT 5 FOR UPDATE OF o SKIP LOCKED""")
            for row in rows:
                await conn.execute("UPDATE transak_staging_orders SET next_check_at=NOW()+INTERVAL '5 minutes' WHERE order_id=$1", row["order_id"])
    finally:
        await conn.close()
    for row in rows:
        try:
            await refresh_order(str(row["order_id"]), {"id":row["user_id"], "wallet_address":row["wallet_address"]})
        except Exception:
            conn = await get_conn()
            try:
                await conn.execute("UPDATE transak_staging_orders SET refresh_error=$2 WHERE order_id=$1 AND checked_at=$3",
                    row["order_id"], "Automatic provider refresh failed; saved evidence is unchanged. Retry later.", row["checked_at"])
            finally:
                await conn.close()


async def reconciliation_worker():
    while True:
        try:
            await reconcile_saved_orders()
        except Exception:
            logging.getLogger(__name__).warning("Transak saved-order reconciliation unavailable; retrying later")
        await asyncio.sleep(60)


class PayoutPreference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: Literal["USDC", "USD", "EUR", "INR", "IDR"]


@router.get("/payout-preference")
async def payout_preference(user=Depends(current_user)):
    conn = await get_conn()
    try:
        currency = await conn.fetchval("SELECT payout_currency FROM app_users WHERE id=$1", user["id"])
        return {"currency": currency, "environment": "staging",
                "automatic_payout_enabled": False}
    finally:
        await conn.close()


@router.put("/payout-preference")
async def save_payout_preference(body: PayoutPreference, user=Depends(current_user)):
    conn = await get_conn()
    try:
        await conn.execute("UPDATE app_users SET payout_currency=$1 WHERE id=$2", body.currency, user["id"])
    finally:
        await conn.close()
    return {"currency": body.currency, "environment": "staging", "automatic_payout_enabled": False}


@router.post("/payout-session")
async def payout_session(request: Request, user=Depends(wallet_user)):
    await throttle(request, "transak-payout:" + str(user["id"]))
    preference = await payout_preference(user)
    if preference["currency"] == "USDC":
        raise HTTPException(409, "Choose a fiat withdrawal preference first. USDC wallet payments do not require an off-ramp.")
    try:
        url = await create_session(user["wallet_address"], request.client.host if request.client else "",
                                   payout_currency=preference["currency"])
    except Exception:
        raise HTTPException(503, "Transak sandbox withdrawal is unavailable. SELL must be enabled by the provider and the selected currency must be supported.") from None
    return {"widget_url": url, "environment": "staging", "grants_access": False,
            "automatic_payout_enabled": False, "expires_in_seconds": 300}
