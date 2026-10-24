"""Read-only, block-pinned migration inventory. Does not deploy or mutate contracts."""
import asyncio
import json
import os
import re
from datetime import datetime,timezone
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from web3 import Web3
from services import blockchain
from services.event_indexer import ABIS,normalized
from services.pgvector_client import get_conn


async def main():
    w3=blockchain.w3
    if w3.eth.chain_id!=80002: raise ValueError('Unexpected chain')
    block=w3.eth.block_number-2;header=w3.eth.get_block(block)
    root=Path(__file__).resolve().parents[1]
    frontend=(root/'frontend/contracts/addresses/index.ts').read_text()
    frontend_current=re.search(r'Marketplace:\s*"(0x[0-9a-fA-F]{40})"',frontend).group(1).lower()
    legacy_text=frontend.split('export const LEGACY_MARKETPLACES',1)[1]
    frontend_legacy=set(a.lower() for a in re.findall(r'0x[0-9a-fA-F]{40}',legacy_text))
    markets=blockchain.entitlement_markets()
    backend_legacy={m.address.lower() for m in markets[1:]}
    aligned=frontend_current==markets[0].address.lower() and frontend_legacy==backend_legacy
    if not aligned: raise ValueError('Frontend/backend marketplace configuration mismatch')
    conn=await get_conn()
    try:
        wallets={r['wallet_address'].lower() for r in await conn.fetch('SELECT wallet_address FROM app_users WHERE wallet_address IS NOT NULL')}
        cursors=[dict(r) for r in await conn.fetch('SELECT market,deployment_block,next_block,state FROM chain_sync')]
        events=await conn.fetch('SELECT args FROM market_events')
        for row in events:
            args=json.loads(row['args'])
            for field in ('buyer','bidder','seller','winner'):
                if args.get(field) and int(args[field],16):wallets.add(args[field])
    finally:await conn.close()
    result={'captured_at':datetime.now(timezone.utc).isoformat(),'chain_id':80002,'block':block,
        'block_hash':Web3.to_hex(header.hash),'knowledge_asset':os.environ['KNOWLEDGE_ASSET_ADDRESS'],
        'frontend_backend_match':aligned,'legacy_marketplaces':sorted(backend_legacy),'markets':[],
        'index_coverage':cursors,'all_historical_buyers_enumerated':False,
        'limitation':'Entitlement mappings cannot enumerate unknown buyers; indexed history must finish before migration sign-off. This inventory includes known account/event/auction wallets.',
        'deployment_authorized':False}
    for configured in markets:
        market=w3.eth.contract(address=configured.address,abi=ABIS['marketplace'])
        call=lambda name,*args:getattr(market.functions,name)(*args).call(block_identifier=block)
        if call('knowledgeAsset').lower()!=result['knowledge_asset'].lower():raise ValueError('KnowledgeAsset mismatch')
        listings=[];auctions=[];tokens=set()
        listing_count=call('totalListingsCreated');auction_count=call('totalAuctionsCreated')
        if listing_count>10000 or auction_count>10000:raise ValueError('Inventory needs paginated operator run')
        for i in range(1,listing_count+1):
            row=call('listings',i);tokens.add(row[0]);wallets.add(row[2].lower())
            listings.append({'id':i,'token_id':str(row[0]),'price':str(row[1]),'seller':row[2],'sale_type':row[3],
                             'active':row[4],'seller_cancellation_required_before_relisting':bool(row[4])})
        for i in range(1,auction_count+1):
            row=call('auctions',i);tokens.add(row[0]);wallets.add(row[4].lower())
            bids=call('getAuctionBids',i)
            for bid in bids:wallets.add(bid[1].lower())
            auctions.append({'id':i,'token_id':str(row[0]),'reserve':str(row[1]),'highest_bid':str(row[2]),
                'highest_bidder':row[3],'seller':row[4],'active':row[5],'finalized':row[6],
                'start_time':row[7],'end_time':row[8],'ended_unfinalized':not row[6] and row[8]<=header.timestamp,
                'bids':[{'amount':str(b[0]),'bidder':b[1],'timestamp':b[2]} for b in bids]})
        wallets.discard('0x'+'0'*40)
        entitlements=[]
        for token in sorted(tokens):
            for wallet in sorted(wallets):
                count=call('purchaseCount',token,Web3.to_checksum_address(wallet))
                if count:entitlements.append({'token_id':str(token),'buyer':wallet,'purchase_count':str(count),'has_purchased':call('hasPurchased',token,Web3.to_checksum_address(wallet))})
        refunds=[{'wallet':wallet,'amount':str(call('pendingRefunds',Web3.to_checksum_address(wallet)))} for wallet in sorted(wallets)]
        result['markets'].append({'address':market.address,'splitter':call('royaltySplitter'),'token':call('usdc'),
            'listings':listings,'auctions':auctions,'known_entitlements':entitlements,'refund_balances':refunds})
    if w3.eth.get_block(block).hash!=header.hash:raise ValueError('Snapshot reorganized')
    output=root/'migration_inventory.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'snapshot':output.name,'block':block,'markets':len(result['markets']),
                      'listings':sum(len(m['listings']) for m in result['markets']),
                      'auctions':sum(len(m['auctions']) for m in result['markets']),'configuration_match':aligned}))


if __name__=='__main__':
    try:asyncio.run(main())
    except Exception:raise SystemExit('Inventory failed safely; no deployment approved. Check chain compatibility and index availability.') from None
