"""Bridge reverified indexed sales into audit jobs; never accept wallet funding as a sale."""
import asyncio
import json
import os
import re
import httpx
from web3 import Web3
from services import event_indexer as index
from services.pgvector_client import get_conn
from .recording import enqueue_verified, enqueue_reversal


async def queue_indexed_sales():
    conn=await get_conn()
    try:
        rows=await conn.fetch("""SELECT e.*,u.id AS buyer_user_id FROM market_events e
            JOIN chain_sync c ON c.market=e.market
            JOIN app_users u ON lower(u.wallet_address)=COALESCE(e.args->>'buyer',e.args->>'winner')
            WHERE e.accounting IS NOT NULL AND e.recording_evidence_id IS NULL
            AND c.state<>'review_required' AND c.error IS NULL
            AND e.kind IN ('PurchaseCompleted','AuctionEnded')
            ORDER BY e.recording_checked_at NULLS FIRST,e.block_number LIMIT 5""")
        for row in rows:
            await conn.execute('UPDATE market_events SET recording_checked_at=NOW() WHERE market=$1 AND tx_hash=$2 AND log_index=$3',row['market'],row['tx_hash'],row['log_index'])
            # Re-read the actual canonical event and payout amounts immediately before enqueue.
            fresh,_=await asyncio.to_thread(index.fetch_page,row['market'],row['block_number'],row['block_number'])
            matches=[r for r in fresh if r['tx_hash']==row['tx_hash'] and r['log_index']==row['log_index']]
            if len(matches)!=1 or matches[0]['block_hash']!=row['block_hash'] or matches[0]['accounting']!=json.loads(row['accounting']):
                raise ValueError('Indexed sale evidence changed')
            event=matches[0];args=event['args'];accounting=event['accounting']
            currency=Web3.to_hex(Web3.keccak(text='dkm:currency:v1:eip155:80002/erc20:'+accounting['token']+'/base-units'))
            terms={'assetContract':Web3.to_checksum_address(os.environ['KNOWLEDGE_ASSET_ADDRESS']),
                'tokenId':int(args['tokenId']),'buyer':Web3.to_checksum_address(args.get('buyer') or args['winner']),
                'seller':Web3.to_checksum_address(accounting['seller']),'paymentCurrency':currency,
                'paymentAmount':int(accounting['gross']),'payoutCurrency':currency,'payoutAmount':int(accounting['seller_net'])}
            provider='amoy_marketplace';reference=row['market']+':'+row['tx_hash']+':'+str(row['log_index'])
            if args.get('funding_reference'):
                order=await conn.fetchrow("SELECT * FROM payment_orders WHERE lower(settlement_tx_hash)=$1 AND user_id=$2",row['tx_hash'].lower(),row['buyer_user_id'])
                if not order or order['status']!='ENTITLEMENT_GRANTED' or order['payment_method'] not in ('upi','card') or order['recovery_status']:
                    continue
                if (Web3.to_hex(Web3.keccak(text=order['order_id']))!=args['funding_reference']
                        or order['token_id']!=terms['tokenId'] or order['buyer_address'].lower()!=terms['buyer'].lower()
                        or int(order['payment_amount_base_units'] or order['amount_usdc']*1_000_000)!=terms['paymentAmount'] or order['fiat_currency']!='INR'
                        or (order['payment_token'] or '0x0bd22C54F90E7309dd5e7e73270Ac72d4cD74719').lower()!=accounting['token'].lower()):
                    raise ValueError('Funded order does not match chain sale')
                await verify_saved_capture(order)
                provider='razorpay_test';reference=order['provider_payment_id']
                terms.update(paymentCurrency=Web3.to_hex(Web3.keccak(text='dkm:currency:v1:ISO4217:INR:decimals:2')),
                             paymentAmount=order['fiat_amount'])
            identifier=await enqueue_verified(row['buyer_user_id'],provider,reference,terms,
                {'chain_id':80002,'transaction_hash':row['tx_hash'],'block_hash':row['block_hash'],'block_number':row['block_number']})
            await conn.execute('UPDATE market_events SET recording_evidence_id=$4 WHERE market=$1 AND tx_hash=$2 AND log_index=$3',row['market'],row['tx_hash'],row['log_index'],identifier)
    finally: await conn.close()


async def verify_saved_capture(order):
    payment=await saved_payment(order)
    if payment.get('status')!='captured' or payment.get('amount_refunded',0)!=0:
        raise ValueError('Provider has not confirmed an unreversed capture')


async def saved_payment(order):
    key=os.getenv('RAZORPAY_KEY_ID','');secret=os.getenv('RAZORPAY_KEY_SECRET','')
    payment_id=order['provider_payment_id'] or ''
    if not key.startswith('rzp_test_') or not secret or not re.fullmatch(r'pay_[A-Za-z0-9]{1,96}',payment_id):
        raise ValueError('Test provider configuration required')
    async with httpx.AsyncClient(timeout=20,auth=(key,secret),follow_redirects=False) as client:
        response=await client.get('https://api.razorpay.com/v1/payments/'+payment_id)
        response.raise_for_status();payment=response.json()
    if (payment.get('id')!=payment_id or payment.get('order_id')!=order['provider_order_id']
            or payment.get('amount')!=order['fiat_amount'] or payment.get('currency')!=order['fiat_currency']):
        raise ValueError('Provider payment binding mismatch')
    return payment


async def queue_verified_refunds():
    conn=await get_conn()
    try:
        orders=await conn.fetch("""SELECT p.*,e.recording_evidence_id,e.market,e.tx_hash,e.log_index FROM payment_orders p
            JOIN market_events e ON lower(p.settlement_tx_hash)=e.tx_hash
            JOIN receipt_jobs j ON j.evidence_id=e.recording_evidence_id AND j.reversal_status=0
            WHERE p.payment_method IN ('upi','card') AND j.state='recorded'
            AND NOT EXISTS(SELECT 1 FROM receipt_jobs r WHERE r.evidence_id=j.evidence_id AND r.reversal_status<>0)
            ORDER BY e.recording_checked_at NULLS FIRST LIMIT 5""")
        for order in orders:
            await conn.execute('UPDATE market_events SET recording_checked_at=NOW() WHERE market=$1 AND tx_hash=$2 AND log_index=$3',order['market'],order['tx_hash'],order['log_index'])
            payment=await saved_payment(order)
            if payment.get('status')=='refunded' and payment.get('amount_refunded')==order['fiat_amount']:
                await enqueue_reversal(order['recording_evidence_id'],2,order['provider_payment_id']+':full-refund:'+str(order['fiat_amount']))
    finally:await conn.close()
