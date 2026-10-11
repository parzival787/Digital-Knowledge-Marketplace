"""Account-scoped current positions, independently of historical indexing."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from web3 import Web3
from . import blockchain
from .auth import wallet_user
from .event_indexer import ABIS

router=APIRouter(prefix='/api/account/positions',tags=['Account'])


def snapshot(wallet, page):
    w3=blockchain.w3
    if w3.eth.chain_id!=80002: raise ValueError('Unexpected chain')
    wallet=Web3.to_checksum_address(wallet)
    block=max(0,w3.eth.block_number-2);header=w3.eth.get_block(block)
    asset=w3.eth.contract(address=blockchain.knowledge_asset.address,abi=[
        {'type':'function','name':'totalMinted','stateMutability':'view','inputs':[],
         'outputs':[{'name':'','type':'uint256'}]}])
    minted=asset.functions.totalMinted().call(block_identifier=block)
    start=page*10+1;end=start+10
    result={'block':block,'page':page,'has_more':minted>=end,'entitlements':[],'listings':[],'auctions':[],'refunds':[]}
    for configured in blockchain.entitlement_markets():
        market=w3.eth.contract(address=configured.address,abi=ABIS['marketplace'])
        call=lambda name,*args:getattr(market.functions,name)(*args).call(block_identifier=block)
        if call('knowledgeAsset').lower()!=asset.address.lower(): raise ValueError('Registry mismatch')
        address=market.address
        for token in range(start,min(end,minted+1)):
            if call('hasPurchased',token,wallet):
                result['entitlements'].append({'market':address,'token_id':str(token),'purchase_count':str(call('purchaseCount',token,wallet))})
        for kind,count_name in (('listings','totalListingsCreated'),('auctions','totalAuctionsCreated')):
            count=call(count_name);result['has_more'] |= count>=end
            for identifier in range(start,min(end,count+1)):
                row=call(kind,identifier)
                if kind=='listings' and row[2].lower()==wallet.lower():
                    result[kind].append({'market':address,'id':str(identifier),'token_id':str(row[0]),'amount':str(row[1]),'active':row[4]})
                elif kind=='auctions' and wallet.lower() in (row[3].lower(),row[4].lower()):
                    result[kind].append({'market':address,'id':str(identifier),'token_id':str(row[0]),'amount':str(row[2]),
                        'role':'seller' if row[4].lower()==wallet.lower() else 'highest bidder',
                        'state':'finalized' if row[6] else 'awaiting finalization' if row[8]<=header.timestamp else 'active'})
        result['refunds'].append({'market':address,'amount':str(call('pendingRefunds',wallet))})
    if w3.eth.get_block(block).hash!=header.hash: raise ValueError('Snapshot changed')
    return result


@router.get('')
async def positions(page:int=Query(0,ge=0,le=100000),user=Depends(wallet_user)):
    try: return await asyncio.to_thread(snapshot,user['wallet_address'],page)
    except Exception: raise HTTPException(503,'Could not verify current positions. Retry when the blockchain connection recovers.') from None
