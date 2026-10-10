"""Transak staging wallet-funding sessions; never a marketplace payment confirmation."""
import hashlib
import ipaddress
import json
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID
from pydantic import BaseModel
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
            CREATE TABLE IF NOT EXISTS transak_staging_tokens (
                credential_hash TEXT PRIMARY KEY, ciphertext BYTEA NOT NULL,
                wrapped_key TEXT NOT NULL, expires_at DOUBLE PRECISION NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transak_staging_orders (
                order_id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
                wallet_address TEXT NOT NULL, receipt JSONB NOT NULL,
                checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
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


async def create_session(wallet, user_ip):
    key, secret = configuration()
    ipaddress.ip_address(user_ip)
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
                    json={"widgetParams": {"apiKey": key, "referrerDomain": ORIGIN,
                        "productsAvailed": "BUY", "cryptoCurrencyCode": "USDC", "network": "polygon",
                        "walletAddress": wallet, "disableWalletAddressForm": True,
                        "redirectURL": ORIGIN + "/funding"}})
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


async def refresh_order(order_id, user):
    key, secret = configuration()
    fingerprint = hashlib.sha256((key + ":" + secret).encode()).hexdigest()
    conn = await get_conn()
    try:
        async with conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock(80002,7320)")
            existing = await conn.fetchrow("SELECT user_id FROM transak_staging_orders WHERE order_id=$1", UUID(order_id))
            if existing and existing["user_id"] != user["id"]:
                raise ValueError("Order belongs to a different account")
            row = await conn.fetchrow("SELECT * FROM transak_staging_tokens WHERE credential_hash=$1", fingerprint)
            async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
                token = await access_token(conn, client, key, secret, fingerprint, row)
                data = await provider_json(client, "https://api-stg.transak.com/partners/api/v2/order/" + order_id,
                    method="GET", headers={"access-token": token, "x-api-key": key})
            receipt = verified_order(data, order_id, user["wallet_address"])
            await conn.execute("""INSERT INTO transak_staging_orders(order_id,user_id,wallet_address,receipt)
                VALUES ($1,$2,$3,$4) ON CONFLICT (order_id) DO UPDATE SET receipt=$4,checked_at=NOW()
                """, UUID(order_id), user["id"], user["wallet_address"], json.dumps(receipt))
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
        rows = await conn.fetch("""SELECT receipt,checked_at FROM transak_staging_orders
            WHERE user_id=$1 ORDER BY checked_at DESC LIMIT 50""", user["id"])
        return {"orders": [{**json.loads(row["receipt"]), "checked_at": row["checked_at"].isoformat()} for row in rows]}
    finally:
        await conn.close()
