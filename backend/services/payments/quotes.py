"""Expiring, account-bound purchase reviews. Quotes neither reserve nor grant access."""
import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from web3 import Web3

from services.auth import wallet_user, throttle
from services.pgvector_client import get_conn
from services import blockchain
from .settlement import SETTLEMENT_ABI, function_abi

router = APIRouter(prefix="/api/purchase-quotes", tags=["Purchase review"])
RECIPIENTS_ABI = {"type": "function", "name": "getListingRecipients", "stateMutability": "view",
    "inputs": [{"name": "listingId", "type": "uint256"}], "outputs": [{"name": "", "type": "tuple[]",
    "components": [{"name": "wallet", "type": "address"}, {"name": "shareBps", "type": "uint16"}]}]}


async def setup_quotes():
    conn = await get_conn()
    try:
        await conn.execute("""CREATE TABLE IF NOT EXISTS purchase_quotes (
            id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
            terms JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 minutes'),
            accepted_at TIMESTAMPTZ);
            CREATE INDEX IF NOT EXISTS purchase_quotes_account ON purchase_quotes(user_id,created_at DESC)
        """)
    finally:
        await conn.close()


def accounting(amount, platform_bps, recipients):
    if type(amount) is not int or not 0 < amount < 2**256 or not 0 <= platform_bps <= 1000:
        raise ValueError("Invalid accounting")
    if len(recipients) > 10 or any(not 0 <= share <= 2000 for _, share in recipients) or sum(share for _, share in recipients) > 2000:
        raise ValueError("Invalid royalties")
    fee = amount * platform_bps // 10000
    royalties = [{"wallet": wallet, "share_bps": share, "amount_base_units": str((amount - fee) * share // 10000)} for wallet, share in recipients]
    royalty_total = sum(int(r["amount_base_units"]) for r in royalties)
    return {"asset_price_base_units": str(amount), "buyer_token_total_base_units": str(amount),
        "buyer_dkm_fee_base_units": "0", "seller_gross_base_units": str(amount),
        "platform_fee_bps": platform_bps, "platform_fee_base_units": str(fee),
        "royalties": royalties, "royalty_total_base_units": str(royalty_total),
        "seller_net_base_units": str(amount - fee - royalty_total)}


def purchase_terms(token_id, buyer):
    w3 = blockchain.w3
    if not 0 < token_id < 2**256 or w3.eth.chain_id != 80002:
        raise ValueError("Invalid asset/network")
    block = w3.eth.block_number
    abi = SETTLEMENT_ABI + [RECIPIENTS_ABI, function_abi("royaltySplitter", [], ["address"]), function_abi("paused", [], ["bool"])]
    market = w3.eth.contract(address=blockchain.marketplace.address, abi=abi)
    def read(fn):
        return fn.call(block_identifier=block)
    if read(market.functions.paused()):
        raise ValueError("Marketplace is paused")
    if read(market.functions.knowledgeAsset()).lower() != blockchain.KNOWLEDGE_ASSET_ADDRESS.lower():
        raise ValueError("Registry mismatch")
    registry = w3.eth.contract(address=blockchain.KNOWLEDGE_ASSET_ADDRESS, abi=blockchain.KNOWLEDGE_ASSET_ABI)
    if not read(registry.functions.getAsset(token_id))[6]:
        raise ValueError("Asset is inactive")
    listing_id = read(market.functions.tokenToListing(token_id))
    listing = read(market.functions.listings(listing_id))
    if not listing_id or listing[0] != token_id or listing[3] != 0 or not listing[4] or listing[2].lower() == buyer.lower():
        raise ValueError("Listing unavailable")
    if any(read(old.functions.hasPurchased(token_id, buyer)) for old in blockchain.entitlement_markets()):
        raise ValueError("Existing entitlement")
    token = read(market.functions.usdc())
    erc20 = w3.eth.contract(address=token, abi=[function_abi("decimals", [], ["uint8"])])
    decimals = read(erc20.functions.decimals())
    if decimals != 6:
        raise ValueError("Unsupported payment token decimals")
    splitter_address = read(market.functions.royaltySplitter())
    splitter = w3.eth.contract(address=splitter_address, abi=[function_abi("platformFeeBps", [], ["uint16"])])
    amounts = accounting(listing[1], read(splitter.functions.platformFeeBps()), read(market.functions.getListingRecipients(listing_id)))
    return {"route": "fixed_price", "chain_id": 80002, "marketplace": market.address,
        "asset_contract": registry.address, "token_id": str(token_id), "listing_id": str(listing_id),
        "buyer": buyer, "seller": listing[2], "payment_token": token, "decimals": decimals,
        "splitter": splitter_address, **amounts,
        "funding_amount": None, "provider_fee": None, "fx_spread": None,
        "network_fee": None, "source_gas": None, "payout_quote": None,
        "external_cost_notice": "No funding or payout quote is included. Wallet gas is additional and reviewed before signing.",
        "sandbox_only": True, "reserves_asset": False}


def public_quote(row):
    return {"id": str(row["id"]), "terms": json.loads(row["terms"]),
            "expires_at": row["expires_at"].isoformat(),
            "accepted_at": row["accepted_at"].isoformat() if row["accepted_at"] else None}


async def create_quote(token_id, user):
    terms = await asyncio.to_thread(purchase_terms, token_id, user["wallet_address"])
    conn = await get_conn()
    try:
        terms["seller_payout_preference"] = await conn.fetchval("SELECT payout_currency FROM app_users WHERE lower(wallet_address)=lower($1)", terms["seller"]) or "USDC"
        row = await conn.fetchrow("INSERT INTO purchase_quotes(id,user_id,terms) VALUES ($1,$2,$3) RETURNING *", uuid4(), user["id"], json.dumps(terms))
        return public_quote(row)
    finally:
        await conn.close()


async def accept_quote(quote_id, user):
    conn = await get_conn()
    try:
        async with conn.transaction():
            row = await conn.fetchrow("SELECT * FROM purchase_quotes WHERE id=$1 AND user_id=$2 FOR UPDATE", quote_id, user["id"])
            if not row:
                raise HTTPException(404, "Quote not found")
            if row["expires_at"] <= datetime.now(timezone.utc):
                raise HTTPException(409, "Quote expired. Review a new quote before paying.")
            old = json.loads(row["terms"])
            fresh = await asyncio.to_thread(purchase_terms, int(old["token_id"]), user["wallet_address"])
            fresh["seller_payout_preference"] = await conn.fetchval("SELECT payout_currency FROM app_users WHERE lower(wallet_address)=lower($1)", fresh["seller"]) or "USDC"
            if old != fresh:
                raise HTTPException(409, "Purchase terms changed. Review a new quote before paying.")
            row = await conn.fetchrow("UPDATE purchase_quotes SET accepted_at=COALESCE(accepted_at,NOW()) WHERE id=$1 RETURNING *", quote_id)
            return public_quote(row)
    finally:
        await conn.close()


@router.post("/asset/{token_id}")
async def create(token_id: int, request: Request, user=Depends(wallet_user)):
    await throttle(request, "quote:" + str(user["id"]))
    try:
        return await create_quote(token_id, user)
    except Exception:
        raise HTTPException(409, "Could not quote this listing. Refresh its price, availability and your access before retrying.") from None


@router.post("/{quote_id}/accept")
async def accept(quote_id: UUID, request: Request, user=Depends(wallet_user)):
    await throttle(request, "quote:" + str(user["id"]))
    try:
        return await accept_quote(quote_id, user)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(409, "Could not revalidate the quote. Review again before paying.") from None
