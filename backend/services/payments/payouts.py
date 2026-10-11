"""Account-bound SELL evidence. A payout observation never grants asset access."""
import hashlib
import json
from uuid import UUID, uuid4

import httpx
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from services.auth import current_user, throttle
from services.payments import transak
from services.pgvector_client import get_conn


async def setup_payouts():
    conn = await get_conn()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS seller_payouts (
                id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
                customer_reference UUID NOT NULL UNIQUE, currency TEXT NOT NULL,
                provider_order UUID UNIQUE, receipt JSONB, observed JSONB,
                state TEXT NOT NULL DEFAULT 'pending_verification',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), checked_at TIMESTAMPTZ,
                next_check_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), error TEXT
            );
            CREATE INDEX IF NOT EXISTS payout_account ON seller_payouts(user_id,created_at DESC);
            CREATE INDEX IF NOT EXISTS payout_recheck ON seller_payouts(next_check_at);
            CREATE TABLE IF NOT EXISTS payout_observations (
                payout_id UUID NOT NULL REFERENCES seller_payouts(id), digest TEXT NOT NULL,
                evidence JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY(payout_id,digest)
            );
            CREATE TABLE IF NOT EXISTS payout_resolutions (
                id BIGSERIAL PRIMARY KEY, payout_id UUID NOT NULL REFERENCES seller_payouts(id),
                observation_digest TEXT NOT NULL, operator TEXT NOT NULL DEFAULT SESSION_USER, reason TEXT NOT NULL,
                previous JSONB, accepted JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
    finally:
        await conn.close()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


async def create_payout(user, ip, currency):
    payout_id, customer = uuid4(), uuid4()
    conn = await get_conn()
    try:
        await conn.execute("INSERT INTO seller_payouts(id,user_id,customer_reference,currency) VALUES ($1,$2,$3,$4)",
                           payout_id, user['id'], customer, currency)
        try:
            return await transak.create_session(user['wallet_address'], ip, payout_currency=currency,
                                                partner_order=payout_id, partner_customer=customer)
        except Exception:
            await conn.execute("UPDATE seller_payouts SET error='Session creation failed; no payout verified' WHERE id=$1", payout_id)
            raise
    finally:
        await conn.close()


def verified_sell(data, payout, order_id):
    if (str(data.get('_id')) != str(order_id) or data.get('isBuyOrSell') != 'SELL'
            or data.get('partnerOrderId') != str(payout['id'])
            or data.get('partnerCustomerId') != str(payout['customer_reference'])):
        raise ValueError('SELL account references do not match')
    result = transak.normalized_order(data, str(order_id))
    result['direction'] = 'SELL'
    # No wallet comparison: SELL walletAddress is a provider deposit destination.
    if result['status'] == 'COMPLETED' and (result['fiat_amount'] is None or result['crypto_amount'] is None):
        raise ValueError('Completed payout amounts missing')
    return result


async def refresh_payout(payout_id, order_id, user_id):
    key, secret = transak.configuration()
    fingerprint = hashlib.sha256((key + ':' + secret).encode()).hexdigest()
    conn = await get_conn()
    try:
        async with conn.transaction():
            await conn.execute('SELECT pg_advisory_xact_lock(80002,7320)')
            payout = await conn.fetchrow('SELECT * FROM seller_payouts WHERE id=$1 AND user_id=$2 FOR UPDATE', UUID(str(payout_id)), user_id)
            if not payout or (payout['provider_order'] and payout['provider_order'] != UUID(str(order_id))):
                raise ValueError('Payout account/order mismatch')
            token_row = await conn.fetchrow('SELECT * FROM transak_staging_tokens WHERE credential_hash=$1', fingerprint)
            async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
                token = await transak.access_token(conn, client, key, secret, fingerprint, token_row)
                data = await transak.provider_json(client, 'https://api-stg.transak.com/partners/api/v2/order/' + str(order_id),
                    method='GET', headers={'access-token':token, 'x-api-key':key})
            observed = verified_sell(data, payout, order_id)
            previous = json.loads(payout['receipt']) if payout['receipt'] else None
            receipt = transak.reconcile_receipt(previous, observed)
            conflict = (payout['state'] == 'review_required' or observed['fiat_currency'] != payout['currency']
                        or receipt['verification_state'] == 'review_required')
            if conflict:
                receipt = previous
            state = 'review_required' if conflict else 'verified'
            await conn.execute('INSERT INTO payout_observations VALUES ($1,$2,$3,NOW()) ON CONFLICT DO NOTHING',
                               payout['id'], digest(observed), json.dumps(observed))
            await conn.execute("""UPDATE seller_payouts SET provider_order=$2,receipt=$3,observed=$4,
                state=$5,checked_at=NOW(),next_check_at=NOW()+INTERVAL '5 minutes',error=NULL WHERE id=$1""",
                payout['id'], UUID(str(order_id)), json.dumps(receipt) if receipt else None, json.dumps(observed), state)
            return {'state':state, 'receipt':receipt, 'grants_access':False}
    finally:
        await conn.close()


async def resolve_payout(payout_id, expected_digest, reason):
    """Local operator CLI only; compare-and-set against the exact sanitized observation."""
    if not 10 <= len(reason.strip()) <= 1000:
        raise ValueError('Meaningful audit reason required')
    conn = await get_conn()
    try:
        async with conn.transaction():
            row = await conn.fetchrow('SELECT * FROM seller_payouts WHERE id=$1 FOR UPDATE', UUID(str(payout_id)))
            if not row or row['state'] != 'review_required' or not row['observed']:
                raise ValueError('No pending conflict')
            evidence = json.loads(row['observed'])
            if digest(evidence) != expected_digest or evidence['fiat_currency'] != row['currency']:
                raise ValueError('Evidence changed or currency mismatch; cannot override binding')
            await conn.execute('INSERT INTO payout_resolutions(payout_id,observation_digest,reason,previous,accepted) VALUES ($1,$2,$3,$4,$5)',
                               row['id'], expected_digest, reason, row['receipt'], row['observed'])
            accepted = {**evidence, 'verification_state':'provider_verified'}
            await conn.execute("UPDATE seller_payouts SET receipt=$2,state='verified',next_check_at=NOW() WHERE id=$1", row['id'], json.dumps(accepted))
    finally:
        await conn.close()


async def reconcile_payouts():
    conn = await get_conn()
    try:
        async with conn.transaction():
            rows = await conn.fetch("""SELECT id,provider_order,user_id FROM seller_payouts
                WHERE provider_order IS NOT NULL AND state<>'review_required' AND next_check_at<=NOW()
                ORDER BY next_check_at LIMIT 5 FOR UPDATE SKIP LOCKED""")
            for row in rows:
                await conn.execute("UPDATE seller_payouts SET next_check_at=NOW()+INTERVAL '5 minutes' WHERE id=$1", row['id'])
        for row in rows:
            try:
                await refresh_payout(row['id'], row['provider_order'], row['user_id'])
            except Exception:
                await conn.execute("UPDATE seller_payouts SET error='Provider verification unavailable; saved evidence preserved' WHERE id=$1", row['id'])
    finally:
        await conn.close()


class PayoutLookup(BaseModel):
    model_config = ConfigDict(extra='forbid')
    order_id: UUID


@transak.router.post('/payouts/{payout_id}/refresh')
async def refresh(payout_id: UUID, body: PayoutLookup, request: Request, user=Depends(current_user)):
    await throttle(request, 'payout-refresh:' + str(user['id']))
    try:
        return await refresh_payout(payout_id, body.order_id, user['id'])
    except Exception:
        raise HTTPException(503, 'Could not verify seller binding, currency or provider evidence; no payout completion claimed') from None


@transak.router.get('/payouts')
async def history(user=Depends(current_user)):
    conn = await get_conn()
    try:
        rows = await conn.fetch('SELECT * FROM seller_payouts WHERE user_id=$1 ORDER BY created_at DESC LIMIT 100', user['id'])
        return {'payouts':[{'id':str(r['id']), 'currency':r['currency'], 'order_id':str(r['provider_order']) if r['provider_order'] else None,
            'state':r['state'], 'receipt':json.loads(r['receipt']) if r['receipt'] else None,
            'error':r['error'], 'checked_at':r['checked_at'].isoformat() if r['checked_at'] else None} for r in rows]}
    finally:
        await conn.close()
