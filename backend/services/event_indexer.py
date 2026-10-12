"""Incremental confirmed-market history. Stop on reorg; never silently count stale events."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends
from web3 import Web3
from web3._utils.events import get_event_data
from eth_utils import event_abi_to_log_topic
from services.auth import current_user
from services.pgvector_client import get_conn
from services import blockchain

ABIS=json.loads(Path(__file__).with_name('chain_event_abis.json').read_text())
NAMES={'AssetListed','ListingCancelled','PurchaseCompleted','AuctionCreated','BidPlaced','AuctionEnded','RefundWithdrawn'}
EVENTS={Web3.to_hex(event_abi_to_log_topic(e)):e for e in ABIS['marketplace'] if e.get('type')=='event' and e['name'] in NAMES}
router=APIRouter(prefix='/api/account/indexed-activity',tags=['Confirmed activity'])


async def setup_indexer():
    conn=await get_conn()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chain_sync (
                market TEXT PRIMARY KEY, deployment_block BIGINT NOT NULL, next_block BIGINT NOT NULL,
                checkpoint_hash TEXT, state TEXT NOT NULL DEFAULT 'backfilling', error TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS market_events (
                market TEXT NOT NULL REFERENCES chain_sync(market), tx_hash TEXT NOT NULL,
                log_index INT NOT NULL, block_number BIGINT NOT NULL, block_hash TEXT NOT NULL,
                kind TEXT NOT NULL, args JSONB NOT NULL, accounting JSONB,
                PRIMARY KEY(market,tx_hash,log_index)
            );
            CREATE INDEX IF NOT EXISTS market_events_block ON market_events(market,block_number);
            CREATE INDEX IF NOT EXISTS market_events_kind ON market_events(kind,block_number DESC);
            CREATE INDEX IF NOT EXISTS market_events_args ON market_events USING GIN(args);
            ALTER TABLE market_events ADD COLUMN IF NOT EXISTS recording_evidence_id UUID;
            ALTER TABLE market_events ADD COLUMN IF NOT EXISTS recording_checked_at TIMESTAMPTZ;
            ALTER TABLE chain_sync ADD COLUMN IF NOT EXISTS page_size INT NOT NULL DEFAULT 10;
            ALTER TABLE chain_sync ADD COLUMN IF NOT EXISTS failures INT NOT NULL DEFAULT 0;
            ALTER TABLE chain_sync ADD COLUMN IF NOT EXISTS retry_after TIMESTAMPTZ;
        """)
    finally: await conn.close()


def first_code_block(w3,address,head):
    if not w3.eth.get_code(address,head): raise ValueError('Configured marketplace has no code')
    low,high=0,head
    while low<high:
        middle=(low+high)//2
        if w3.eth.get_code(address,middle): high=middle
        else: low=middle+1
    return low


def normalized(value):
    if isinstance(value,dict): return {k:normalized(v) for k,v in value.items()}
    if isinstance(value,(bytes,bytearray)): return Web3.to_hex(value)
    if isinstance(value,int): return str(value)
    if isinstance(value,(list,tuple)): return [normalized(v) for v in value]
    return value.lower() if isinstance(value,str) and Web3.is_address(value) else value


def sale_accounting(w3,market,event):
    args=event['args'];block=event['blockNumber']
    if event['event']=='AuctionEnded' and int(args['winner'],16)==0: return None
    if event['event'] not in ('PurchaseCompleted','AuctionEnded'): return None
    receipt=w3.eth.get_transaction_receipt(event['transactionHash'])
    if receipt.status!=1 or receipt.blockHash!=event['blockHash']: raise ValueError('Sale receipt not canonical')
    # Historical payout events, not today's adjustable fee or royalty settings.
    splitter_address=market.functions.royaltySplitter().call(block_identifier=block)
    splitter=w3.eth.contract(address=splitter_address,abi=ABIS['splitter'])
    from web3.logs import DISCARD
    def payouts(name):
        return [r['args'] for r in getattr(splitter.events,name)().process_receipt(receipt,errors=DISCARD)
                if r['address'].lower()==splitter_address.lower()]
    totals=payouts('RoyaltyDistributed'); seller=payouts('SellerPaid')
    if len(totals)!=1 or len(seller)!=1: return None
    gross=int(args['amount']); fees=payouts('PlatformFeePaid'); royalties=payouts('RecipientPaid')
    # ABI field names are taken from the compiled source, never guessed fee percentages.
    amount=lambda r:int(r['amount'])
    fee=sum(map(amount,fees)); royalty=sum(map(amount,royalties)); net=amount(seller[0])
    if gross!=fee+royalty+net: raise ValueError('Payout accounting does not balance')
    token=market.functions.usdc().call(block_identifier=block)
    return {'gross':str(gross),'platform_fee':str(fee),'royalties':str(royalty),'seller_net':str(net),
            'seller':seller[0]['seller'].lower(),'token':token.lower(),'chain_id':80002}


def fetch_page(address,start,end):
    w3=blockchain.w3
    if w3.eth.chain_id!=80002: raise ValueError('Wrong chain')
    market=w3.eth.contract(address=Web3.to_checksum_address(address),abi=ABIS['marketplace'])
    before=w3.eth.get_block(end).hash
    logs=w3.eth.get_logs({'address':market.address,'fromBlock':start,'toBlock':end,'topics':[list(EVENTS)]})
    rows=[]
    for log in sorted(logs,key=lambda row:(row['blockNumber'],row['logIndex'])):
        if log.get('removed') or w3.eth.get_block(log['blockNumber']).hash!=log['blockHash']:
            raise ValueError('Event block changed')
        event=get_event_data(w3.codec,EVENTS[Web3.to_hex(log['topics'][0])],log)
        args=normalized(dict(event['args']))
        if event['event']=='PurchaseCompleted':
            from web3.logs import DISCARD
            receipt=w3.eth.get_transaction_receipt(log['transactionHash'])
            funded=[e['args'] for e in market.events.FundedPurchase().process_receipt(receipt,errors=DISCARD)
                    if e['address'].lower()==market.address.lower() and e['args']['listingId']==event['args']['listingId']]
            if funded:
                if len(funded)!=1:raise ValueError('Ambiguous funded purchase')
                args['funding_reference']=Web3.to_hex(funded[0]['paymentReference'])
        if event['event']=='AuctionCreated':
            auction_id=market.functions.tokenToAuction(event['args']['tokenId']).call(block_identifier=log['blockNumber'])
            if auction_id:
                auction=market.functions.auctions(auction_id).call(block_identifier=log['blockNumber'])
                args.update(seller=auction[4].lower(),auctionId=str(auction_id))
        if event['event'] in ('BidPlaced','AuctionEnded'):
            transaction=w3.eth.get_transaction(log['transactionHash'])
            if transaction['to'] and transaction['to'].lower()==market.address.lower():
                function,inputs=market.decode_function_input(transaction['input'])
                if function.fn_name in ('placeBid','endAuction'):
                    auction_id=inputs['auctionId']
                    auction=market.functions.auctions(auction_id).call(block_identifier=log['blockNumber'])
                    if auction[0]!=event['args']['tokenId']:raise ValueError('Auction event identity mismatch')
                    args.update(auctionId=str(auction_id),seller=auction[4].lower())
        if event['event']=='ListingCancelled':
            listing=market.functions.listings(event['args']['listingId']).call(block_identifier=log['blockNumber'])
            args.update(seller=listing[2].lower(),tokenId=str(listing[0]))
        accounting=sale_accounting(w3,market,event)
        if accounting: args['seller']=accounting['seller']
        rows.append({'tx_hash':Web3.to_hex(log['transactionHash']),'log_index':log['logIndex'],
            'block_number':log['blockNumber'],'block_hash':Web3.to_hex(log['blockHash']),
            'kind':event['event'],'args':args,'accounting':accounting})
    if w3.eth.get_block(end).hash!=before: raise ValueError('Page changed during ingestion')
    return rows,Web3.to_hex(before)


async def sync_market(address):
    address=address.lower();conn=await get_conn()
    try:
        if not await conn.fetchval('SELECT pg_try_advisory_lock(hashtext($1),7323)',address): return
        w3=blockchain.w3
        if await asyncio.to_thread(lambda:w3.eth.chain_id)!=80002: raise ValueError('Wrong chain')
        head=max(0,await asyncio.to_thread(lambda:w3.eth.block_number)-2)
        cursor=await conn.fetchrow('SELECT * FROM chain_sync WHERE market=$1',address)
        if not cursor:
            start=await asyncio.to_thread(first_code_block,w3,Web3.to_checksum_address(address),head)
            await conn.execute('INSERT INTO chain_sync(market,deployment_block,next_block) VALUES ($1,$2,$2)',address,start)
            cursor=await conn.fetchrow('SELECT * FROM chain_sync WHERE market=$1',address)
        if cursor['state']=='review_required': return
        if cursor['retry_after'] and cursor['retry_after'] > datetime.now(timezone.utc): return
        start=cursor['next_block']
        if cursor['checkpoint_hash']:
            actual=await asyncio.to_thread(w3.eth.get_block,start-1)
            if Web3.to_hex(actual.hash)!=cursor['checkpoint_hash']:
                await conn.execute("UPDATE chain_sync SET state='review_required',error='Canonical checkpoint changed; rebuild history before using totals' WHERE market=$1",address)
                return
        if start>head: return
        maximum=max(1,min(10000,int(os.getenv('RPC_LOG_PAGE_SIZE','2000'))))
        page_size=max(1,min(maximum,cursor['page_size']))
        end=min(head,start+page_size-1)
        rows,checkpoint=await asyncio.to_thread(fetch_page,address,start,end)
        async with conn.transaction():
            for row in rows:
                if row['kind']=='BidPlaced' and row['args'].get('auctionId'):
                    previous=await conn.fetchval("""SELECT args FROM market_events WHERE market=$1 AND kind='BidPlaced'
                        AND args->>'auctionId'=$2 AND (block_number,log_index)<($3,$4)
                        ORDER BY block_number DESC,log_index DESC LIMIT 1""",address,row['args']['auctionId'],row['block_number'],row['log_index'])
                    if previous:
                        previous=json.loads(previous)
                        row['args'].update(outbid_wallet=previous['bidder'],outbid_amount=previous['amount'])
                await conn.execute('INSERT INTO market_events(market,tx_hash,log_index,block_number,block_hash,kind,args,accounting) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT DO NOTHING',address,
                    row['tx_hash'],row['log_index'],row['block_number'],row['block_hash'],row['kind'],json.dumps(row['args']),
                    json.dumps(row['accounting']) if row['accounting'] else None)
            await conn.execute("UPDATE chain_sync SET next_block=$2,checkpoint_hash=$3,state=$4,error=NULL,updated_at=NOW(),page_size=$5,failures=0,retry_after=NULL WHERE market=$1",address,end+1,checkpoint,'synced' if end==head else 'backfilling',min(maximum,page_size*2))
    except Exception:
        await conn.execute("""UPDATE chain_sync SET error='Indexer unavailable; checkpoint preserved',updated_at=NOW(),
            page_size=GREATEST(1,page_size/2), failures=LEAST(failures+1,10),
            retry_after=NOW()+make_interval(secs=>LEAST(300,30*power(2,LEAST(failures,4)))::double precision)
            WHERE market=$1""",address)
        raise
    finally: await conn.close()


async def rebuild_market(address):
    """Rebuild only derived history; no purchase, asset or entitlement writes."""
    conn=await get_conn()
    try:
        async with conn.transaction():
            await conn.execute('SELECT pg_advisory_xact_lock(hashtext($1),7323)',address.lower())
            await conn.execute('DELETE FROM market_events WHERE market=$1',address.lower())
            await conn.execute("UPDATE chain_sync SET next_block=deployment_block,checkpoint_hash=NULL,state='backfilling',error=NULL,failures=0,retry_after=NULL WHERE market=$1",address.lower())
    finally: await conn.close()


async def index_worker():
    while True:
        try:
            markets=await asyncio.to_thread(blockchain.entitlement_markets)
        except Exception:
            markets=[]
            logging.getLogger(__name__).warning('Market configuration unavailable; retrying later')
        for market in markets:
            try: await sync_market(market.address)
            except Exception: logging.getLogger(__name__).warning('Market index unavailable; checkpoint retained')
        from services.payments.recording_sources import queue_indexed_sales, queue_verified_refunds
        for queue in (queue_indexed_sales,queue_verified_refunds):
            try: await queue()
            except Exception: logging.getLogger(__name__).warning('Sale evidence queue unavailable; no recording claimed')
        await asyncio.sleep(30)


@router.get('')
async def history(user=Depends(current_user)):
    wallet=(user.get('wallet_address') or '').lower()
    markets=[m.address.lower() for m in await asyncio.to_thread(blockchain.entitlement_markets)]
    conn=await get_conn()
    try:
        cursors=await conn.fetch('SELECT * FROM chain_sync WHERE market=ANY($1::text[])',markets)
        healthy={c['market'] for c in cursors if c['state']!='review_required' and not c['error']}
        rows=await conn.fetch("""SELECT * FROM market_events WHERE market=ANY($1::text[]) AND
            (args->>'buyer'=$2 OR args->>'seller'=$2 OR args->>'winner'=$2 OR args->>'bidder'=$2 OR args->>'outbid_wallet'=$2)
            ORDER BY block_number DESC,log_index DESC LIMIT 200""",list(healthy),wallet) if wallet else []
        totals=await conn.fetch("""SELECT accounting->>'token' token,
            SUM((accounting->>'gross')::numeric) gross,SUM((accounting->>'platform_fee')::numeric) fee,
            SUM((accounting->>'royalties')::numeric) royalties,SUM((accounting->>'seller_net')::numeric) net
            FROM market_events WHERE market=ANY($1::text[]) AND accounting->>'seller'=$2 GROUP BY accounting->>'token'""",list(healthy),wallet) if wallet else []
        return {'coverage':[dict(c) for c in cursors], 'lifetime_complete':False,
            'notice':'Confirmed indexed range only. Backfill and RPC availability determine coverage; totals exclude sales without verified payout events.',
            'events':[{'market':r['market'],'kind':r['kind'],'block':r['block_number'],'tx_hash':r['tx_hash'],
                       'log_index':r['log_index'],'args':json.loads(r['args']),'accounting':json.loads(r['accounting']) if r['accounting'] else None} for r in rows],
            'totals':[{k:str(v) for k,v in dict(r).items()} for r in totals]}
    finally: await conn.close()
