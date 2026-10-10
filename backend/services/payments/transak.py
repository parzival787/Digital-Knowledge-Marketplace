"""Transak staging wallet-funding sessions; never a marketplace payment confirmation."""
import hashlib
import ipaddress
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


async def provider_json(client, url, **kwargs):
    try:
        response = await client.post(url, **kwargs)
        response.raise_for_status()
        data = response.json()["data"]
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        # Provider bodies and request headers can contain credentials and session URLs.
        raise ValueError("Transak staging request failed. Check credentials and partner IP/domain allowlists.") from None


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
