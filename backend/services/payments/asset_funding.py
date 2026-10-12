"""Listing-bound staging funding. Delivery and a subsequent purchase are separate."""
import asyncio
import json
import time
from decimal import Decimal, localcontext
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field
from services import blockchain
from services.auth import wallet_user, throttle
from services.pgvector_client import get_conn
from . import transak, transak_discovery
from .quotes import purchase_terms
from .market_profiles import parse_units
from .token_delivery import TRNSK, verify_delivery


async def setup_funding():
    conn = await get_conn()
    try:
        await conn.execute("""CREATE TABLE IF NOT EXISTS asset_funding (
            id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
            customer_reference UUID NOT NULL UNIQUE, wallet TEXT NOT NULL,
            terms JSONB NOT NULL, quote JSONB NOT NULL, provider_order UUID UNIQUE,
            state TEXT NOT NULL DEFAULT 'quoted', delivery JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
            CREATE INDEX IF NOT EXISTS funding_account ON asset_funding(user_id,created_at DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS funding_delivery_evidence_tx ON asset_funding
                ((COALESCE(delivery->>'transaction_hash',delivery#>>'{previous_verified_delivery,transaction_hash}')));
            DROP INDEX IF EXISTS funding_delivery_tx""")
    finally:
        await conn.close()


def nominal(units):
    with localcontext() as ctx:
        ctx.prec = 100
        return format(Decimal(units) / Decimal(10)**18, "f")


def public(row):
    return {"id": str(row["id"]), "terms": json.loads(row["terms"]), "quote": json.loads(row["quote"]),
            "state": row["state"], "provider_order": str(row["provider_order"]) if row["provider_order"] else None,
            "delivery": json.loads(row["delivery"]) if row["delivery"] else None, "grants_access": False}


class FundingRequest(BaseModel):
    token_id: int = Field(gt=0)
    fiat_currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_method: str = Field(pattern=r"^[a-z0-9_]{1,80}$")


async def funding_quote(body, user, ip):
    terms = await asyncio.to_thread(purchase_terms, body.token_id, user["wallet_address"])
    if terms["payment_token"].lower() != TRNSK.lower() or terms["decimals"] != 18:
        raise ValueError("This listing does not accept Transak staging TRNSK")
    quote = await transak_discovery.quote(ip, "BUY", body.fiat_currency, body.payment_method,
                                          nominal(terms["buyer_token_total_base_units"]))
    if parse_units(quote["cryptoAmount"], 18) < int(terms["buyer_token_total_base_units"]):
        raise ValueError("Quoted output cannot fund this listing")
    conn = await get_conn()
    try:
        row = await conn.fetchrow("""INSERT INTO asset_funding(id,user_id,customer_reference,wallet,terms,quote)
            VALUES ($1,$2,$3,$4,$5,$6) RETURNING *""", uuid4(), user["id"], uuid4(), user["wallet_address"], json.dumps(terms), json.dumps(quote))
        return public(row)
    finally:
        await conn.close()


async def funding_session(identifier, user, ip):
    conn = await get_conn()
    try:
        async with conn.transaction():
            row = await conn.fetchrow("SELECT * FROM asset_funding WHERE id=$1 AND user_id=$2 FOR UPDATE", identifier, user["id"])
            if not row or row["state"] != "quoted" or row["wallet"].lower() != user["wallet_address"].lower():
                raise ValueError("Funding session unavailable or already opened")
            terms, quote = json.loads(row["terms"]), json.loads(row["quote"])
            if time.time() > quote["fetched_at"] + quote["freshness_seconds"]:
                raise ValueError("Funding quote expired; request and review a new quote")
            fresh_terms = await asyncio.to_thread(purchase_terms, int(terms["token_id"]), user["wallet_address"])
            if fresh_terms != terms:
                raise ValueError("Listing changed; review a new quote")
            fresh = await transak_discovery.quote(ip, "BUY", quote["fiatCurrency"], quote["paymentMethod"], nominal(terms["buyer_token_total_base_units"]))
            if any(fresh[key] != quote[key] for key in ("fiatAmount", "cryptoAmount", "totalFee", "fees", "conversionPrice")):
                raise ValueError("Provider quote changed; review a new quote")
            await conn.execute("UPDATE asset_funding SET state='session_requested',updated_at=NOW() WHERE id=$1", identifier)
        # Persist the attempt before contacting the provider; an uncertain response cannot create a second session.
        url = await transak.create_session(user["wallet_address"], ip, partner_order=identifier,
                                          partner_customer=row["customer_reference"], reviewed_quote=quote)
        return {"widget_url": url, "id": str(identifier), "grants_access": False}
    finally:
        await conn.close()


async def reconcile_funding(conn, data, receipt, user):
    reference = data.get("partnerOrderId")
    try:
        identifier = UUID(str(reference))
    except (ValueError, TypeError):
        return receipt
    row = await conn.fetchrow("SELECT * FROM asset_funding WHERE id=$1 FOR UPDATE", identifier)
    if not row:
        return receipt
    terms, quote = json.loads(row["terms"]), json.loads(row["quote"])
    if (row["user_id"] != user["id"] or row["wallet"].lower() != user["wallet_address"].lower()
            or data.get("partnerCustomerId") != str(row["customer_reference"])
            or row["provider_order"] and str(row["provider_order"]) != receipt["order_id"]):
        raise ValueError("Funding account/order binding mismatch")
    state = "provider_verified"
    delivery = {"chain_delivery_state": "chain_delivery_unverified", "grants_access": False}
    if (row["state"] == "review_required" or receipt["verification_state"] == "review_required"
            or receipt["fiat_currency"] != quote["fiatCurrency"] or Decimal(receipt["fiat_amount"] or "-1") != Decimal(quote["fiatAmount"])):
        state = "review_required"
    elif receipt["status"] == "COMPLETED":
        try:
            required = int(terms["buyer_token_total_base_units"])
            output = parse_units(receipt["crypto_amount"], 18)
            if output < required:
                raise ValueError("Provider output is insufficient for this listing")
            required = max(required, output)
            delivery = await asyncio.to_thread(verify_delivery, blockchain.w3, receipt["transaction_hash"], row["wallet"], required)
            state = "wallet_funded"
        except Exception:
            pass
    previous = json.loads(row["delivery"]) if row["delivery"] else {}
    if delivery["chain_delivery_state"] != "verified":
        evidence = previous if previous.get("chain_delivery_state") == "verified" else previous.get("previous_verified_delivery")
        if evidence:
            delivery["previous_verified_delivery"] = evidence
    await conn.execute("""UPDATE asset_funding SET provider_order=$2,state=$3,delivery=$4,updated_at=NOW() WHERE id=$1""",
                       identifier, UUID(receipt["order_id"]), state, json.dumps(delivery))
    return {**receipt, "funding_id": str(identifier), "asset_token_id": terms["token_id"],
            "requested_crypto": "USDC", "actual_delivery_token": TRNSK,
            "funding_state": state, **delivery}


@transak.router.post("/asset-funding")
async def create(body: FundingRequest, request: Request, user=Depends(wallet_user)):
    await throttle(request, "funding-quote:" + str(user["id"]))
    try:
        return await funding_quote(body, user, request.client.host if request.client else "")
    except Exception:
        raise HTTPException(409, "Could not quote this listing and funding method. Check current availability and provider limits.") from None


@transak.router.post("/asset-funding/{identifier}/session")
async def session(identifier: UUID, request: Request, user=Depends(wallet_user)):
    await throttle(request, "funding-session:" + str(user["id"]))
    try:
        return await funding_session(identifier, user, request.client.host if request.client else "")
    except Exception:
        raise HTTPException(409, "Session unavailable: quote expired, changed, already opened, or provider unavailable. Review a new quote before funding.") from None


@transak.router.get("/asset-funding")
async def history(user=Depends(wallet_user)):
    conn = await get_conn()
    try:
        return {"funding": [public(row) for row in await conn.fetch("SELECT * FROM asset_funding WHERE user_id=$1 ORDER BY created_at DESC LIMIT 50", user["id"])]}
    finally:
        await conn.close()
