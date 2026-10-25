"""SELL only verified TRNSK sale proceeds; provider completion never changes access."""
import asyncio
import json
import time
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field
from services import blockchain, event_indexer
from services.auth import wallet_user, throttle
from services.pgvector_client import get_conn
from . import transak, transak_discovery
from .asset_funding import nominal
from .token_delivery import TRNSK, verify_delivery


class SaleQuote(BaseModel):
    market: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
    transaction_hash: str = Field(pattern=r"^0x[a-fA-F0-9]{64}$")
    log_index: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_method: str = Field(pattern=r"^[a-z0-9_]{1,80}$")


async def verified_sale(conn, body, wallet):
    markets = await asyncio.to_thread(blockchain.entitlement_markets)
    if body.market.lower() not in {m.address.lower() for m in markets}:
        raise ValueError("Unknown sale marketplace")
    row = await conn.fetchrow("""SELECT e.* FROM market_events e JOIN chain_sync c ON c.market=e.market
        WHERE e.market=$1 AND e.tx_hash=$2 AND e.log_index=$3 AND c.state<>'review_required' AND c.error IS NULL""",
        body.market.lower(), body.transaction_hash.lower(), body.log_index)
    if not row or not row['accounting']:
        raise ValueError("Sale is not indexed and verified")
    rows, _ = await asyncio.to_thread(event_indexer.fetch_page, body.market, row['block_number'], row['block_number'])
    event = next((e for e in rows if e['tx_hash'].lower()==body.transaction_hash.lower() and e['log_index']==body.log_index), None)
    if not event or event['block_hash'] != row['block_hash'] or event['accounting'] != json.loads(row['accounting']):
        raise ValueError("Sale evidence changed")
    accounting=event['accounting']
    if accounting['seller'].lower()!=wallet.lower() or accounting['token'].lower()!=TRNSK.lower() or int(accounting['seller_net'])<=0:
        raise ValueError("Sale has no eligible TRNSK proceeds for this wallet")
    return {'market':body.market.lower(),'transaction_hash':body.transaction_hash.lower(),'log_index':body.log_index,
            'block_hash':row['block_hash'],'seller':wallet,'token':TRNSK,'amount_base_units':accounting['seller_net']}


async def create_quote(body, user, ip):
    conn=await get_conn()
    try:
        terms=await verified_sale(conn,body,user['wallet_address'])
        quote=await transak_discovery.quote(ip,'SELL',body.currency,body.payment_method,nominal(terms['amount_base_units']))
        reference=f"{body.market.lower()}:{body.transaction_hash.lower()}:{body.log_index}"
        async with conn.transaction():
            await conn.execute('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',reference)
            previous=await conn.fetchrow('SELECT * FROM seller_payouts WHERE sale_reference=$1 FOR UPDATE',reference)
            if previous and (previous['user_id']!=user['id'] or previous['state']!='quoted'):
                raise ValueError('Sale already has a payout attempt; verify its status first')
            identifier=previous['id'] if previous else uuid4()
            await conn.execute("""INSERT INTO seller_payouts(id,user_id,customer_reference,currency,sale_reference,sale_terms,quote,state)
                VALUES ($1,$2,$3,$4,$5,$6,$7,'quoted') ON CONFLICT(id) DO UPDATE SET currency=$4,sale_terms=$6,quote=$7""",
                identifier,user['id'],uuid4(),body.currency,reference,json.dumps(terms),json.dumps(quote))
        return {'id':str(identifier),'terms':terms,'quote':quote,'grants_access':False}
    finally:await conn.close()


async def open_session(identifier,user,ip):
    conn=await get_conn()
    try:
        async with conn.transaction():
            row=await conn.fetchrow('SELECT * FROM seller_payouts WHERE id=$1 AND user_id=$2 FOR UPDATE',identifier,user['id'])
            if not row or row['state']!='quoted' or not row['sale_terms']:
                raise ValueError('Payout unavailable or already opened')
            terms,quote=json.loads(row['sale_terms']),json.loads(row['quote'])
            if terms['seller'].lower()!=user['wallet_address'].lower() or time.time()>quote['fetched_at']+quote['freshness_seconds']:
                raise ValueError('Payout quote expired or wallet changed')
            body=SaleQuote(market=terms['market'],transaction_hash=terms['transaction_hash'],log_index=terms['log_index'],currency=row['currency'],payment_method=quote['paymentMethod'])
            if await verified_sale(conn,body,user['wallet_address'])!=terms:
                raise ValueError('Sale changed')
            fresh=await transak_discovery.quote(ip,'SELL',row['currency'],quote['paymentMethod'],nominal(terms['amount_base_units']))
            if any(fresh[k]!=quote[k] for k in ('fiatAmount','cryptoAmount','totalFee','fees','conversionPrice')):
                raise ValueError('Payout quote changed; review again')
            await conn.execute("UPDATE seller_payouts SET state='pending_verification' WHERE id=$1",identifier)
        url=await transak.create_session(user['wallet_address'],ip,payout_currency=row['currency'],
            partner_order=identifier,partner_customer=row['customer_reference'],reviewed_quote=quote)
        return {'widget_url':url,'environment':'staging','automatic_payout_enabled':False,'grants_access':False}
    finally:await conn.close()


async def outgoing_delivery(data,receipt,terms):
    if receipt['status']=='COMPLETED':
        try:
            return await asyncio.to_thread(verify_delivery,blockchain.w3,receipt['transaction_hash'],data.get('walletAddress'),
                                           int(terms['amount_base_units']),terms['seller'])
        except Exception:pass
    return {'chain_delivery_state':'chain_delivery_unverified','grants_access':False}


@transak.router.post('/sale-payouts/quote')
async def create(body:SaleQuote,request:Request,user=Depends(wallet_user)):
    await throttle(request,'sale-payout:'+str(user['id']))
    try:return await create_quote(body,user,request.client.host if request.client else '')
    except Exception:raise HTTPException(409,'Sale proceeds or provider payout quote could not be verified. Check sale history and provider support.') from None


@transak.router.post('/sale-payouts/{identifier}/session')
async def session(identifier:UUID,request:Request,user=Depends(wallet_user)):
    await throttle(request,'sale-payout-session:'+str(user['id']))
    try:return await open_session(identifier,user,request.client.host if request.client else '')
    except Exception:raise HTTPException(409,'Payout session unavailable or quote changed. Review the sale and quote again; do not repeat a pending payout.') from None
