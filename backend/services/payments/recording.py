"""Durable audit-only registry jobs. No public evidence submission or entitlement writes."""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
from pathlib import Path
from uuid import UUID, uuid4

from eth_abi import encode
from fastapi import APIRouter, Depends
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound
from services.auth import current_user
from services.content_security import master_key
from services.pgvector_client import get_conn
from .settlement import confirmed_receipt

router = APIRouter(prefix='/api/payments/recordings', tags=['Audit recording'])
ABI = json.loads(Path(__file__).with_name('receipt_registry_abi.json').read_text())
PAYMENT_TYPES = ['address','uint256','address','address','bytes32','uint256','bytes32','uint256','bytes32','bytes32']
FIELDS = ['assetContract','tokenId','buyer','seller','paymentCurrency','paymentAmount','payoutCurrency','payoutAmount','providerReference','evidenceHash']


async def setup_recording():
    conn = await get_conn()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_evidence (
                id UUID PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES app_users(id),
                source_commitment TEXT NOT NULL UNIQUE, sandbox BOOLEAN NOT NULL,
                payment JSONB NOT NULL, evidence JSONB NOT NULL, salt BYTEA NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS receipt_jobs (
                id UUID PRIMARY KEY, evidence_id UUID NOT NULL REFERENCES payment_evidence(id),
                reversal_status INT NOT NULL DEFAULT 0 CHECK(reversal_status IN (0,2,3)),
                evidence_hash TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'verified',
                chain_id BIGINT, registry TEXT, signer TEXT, raw_tx TEXT, tx_hash TEXT,
                block_number BIGINT, block_hash TEXT, error TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(evidence_id,reversal_status)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS receipt_one_reversal ON receipt_jobs(evidence_id) WHERE reversal_status<>0;
            CREATE INDEX IF NOT EXISTS receipt_job_state ON receipt_jobs(state,updated_at);
            CREATE INDEX IF NOT EXISTS evidence_account ON payment_evidence(user_id,created_at DESC);
        """)
    finally:
        await conn.close()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def commitment(provider, reference):
    return '0x' + hmac.new(master_key(), b'dkm:provider:sandbox:v1:' + provider.encode() + b':' + reference.encode(), hashlib.sha256).hexdigest()


def payment_tuple(payment):
    return tuple(bytes.fromhex(payment[k][2:]) if typ=='bytes32' else int(payment[k]) if typ=='uint256' else payment[k]
                 for k,typ in zip(FIELDS,PAYMENT_TYPES))


def payment_hash(payment):
    return Web3.to_hex(Web3.keccak(encode(['('+','.join(PAYMENT_TYPES)+')'], [payment_tuple(payment)])))


async def enqueue_verified(user_id, provider, reference, terms, proof):
    """Internal adapter boundary: proof must already be verified by provider AND chain adapters."""
    if provider not in ('razorpay_test', 'amoy_marketplace') or set(terms) != set(FIELDS[:8]):
        raise ValueError('Unsupported evidence source/fields')
    if set(proof) != {'chain_id','transaction_hash','block_hash','block_number'} or proof['chain_id'] != 80002:
        raise ValueError('Canonical sandbox settlement proof required')
    if type(proof['block_number']) is not int or proof['block_number'] < 0:
        raise ValueError('Invalid proof block')
    for key in ('transaction_hash','block_hash'):
        if not isinstance(proof[key],str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',proof[key]):
            raise ValueError('Invalid proof hash')
    for key in ('assetContract','buyer','seller'):
        if not Web3.is_address(terms[key]) or int(terms[key],16)==0:
            raise ValueError('Invalid public address')
    if terms['buyer'].lower()==terms['seller'].lower() or any(type(terms[k]) is not int or not 0<terms[k]<2**256 for k in ('tokenId','paymentAmount','payoutAmount')):
        raise ValueError('Invalid parties/amounts')
    for key in ('paymentCurrency','payoutCurrency'):
        if not isinstance(terms[key], str) or not terms[key].startswith('0x') or len(bytes.fromhex(terms[key][2:]))!=32 or int(terms[key],16)==0:
            raise ValueError('Invalid denomination commitment')
    source = commitment(provider, reference)
    conn = await get_conn()
    try:
        async with conn.transaction():
            await conn.execute('SELECT pg_advisory_xact_lock(80002,7322)')
            existing = await conn.fetchrow('SELECT * FROM payment_evidence WHERE source_commitment=$1', source)
            if existing:
                old = json.loads(existing['payment'])
                if existing['user_id']!=user_id or any(old[k]!=terms[k] for k in terms) or json.loads(existing['evidence'])!=proof:
                    raise ValueError('Conflicting immutable evidence')
                return existing['id']
            salt = os.urandom(32)
            evidence_hash = Web3.to_hex(Web3.keccak(salt+canonical(proof)))
            payment = {**terms,'providerReference':source,'evidenceHash':evidence_hash}
            identifier = uuid4()
            await conn.execute('INSERT INTO payment_evidence(id,user_id,source_commitment,sandbox,payment,evidence,salt) VALUES ($1,$2,$3,true,$4,$5,$6)',
                               identifier,user_id,source,json.dumps(payment),json.dumps(proof),salt)
            await conn.execute('INSERT INTO receipt_jobs(id,evidence_id,evidence_hash) VALUES ($1,$2,$3)', uuid4(),identifier,evidence_hash)
            return identifier
    finally:
        await conn.close()


async def enqueue_reversal(evidence_id, status, provider_reference):
    """Internal verified-full-reversal adapter only; no HTTP endpoint accepts assertions."""
    if status not in (2,3):
        raise ValueError('Only full refund/chargeback supported')
    evidence_hash = commitment('reversal:'+str(status), provider_reference)
    conn = await get_conn()
    try:
        async with conn.transaction():
            row = await conn.fetchrow('SELECT * FROM payment_evidence WHERE id=$1 FOR UPDATE', evidence_id)
            if not row: raise ValueError('Original evidence missing')
            previous = await conn.fetchrow('SELECT * FROM receipt_jobs WHERE evidence_id=$1 AND reversal_status<>0',evidence_id)
            if previous:
                if previous['reversal_status']!=status or previous['evidence_hash']!=evidence_hash:
                    raise ValueError('Conflicting reversal')
                return previous['id']
            job_id = uuid4()
            await conn.execute('INSERT INTO receipt_jobs(id,evidence_id,reversal_status,evidence_hash) VALUES ($1,$2,$3,$4)',job_id,evidence_id,status,evidence_hash)
            return job_id
    finally:
        await conn.close()


def connection():
    if os.getenv('RECEIPT_RECORDING_ENABLED') != 'true':
        raise ValueError('Recorder disabled')
    key = os.environ['RECEIPT_RECORDER_PRIVATE_KEY']
    w3 = Web3(Web3.HTTPProvider(os.environ['BLOCKCHAIN_RPC_URL'], request_kwargs={'timeout':15}, exception_retry_configuration=None))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if w3.eth.chain_id != 80002: raise ValueError('Only Amoy sandbox recording supported')
    account = w3.eth.account.from_key(key)
    if os.getenv('SETTLEMENT_PRIVATE_KEY') and account.address == w3.eth.account.from_key(os.environ['SETTLEMENT_PRIVATE_KEY']).address:
        raise ValueError('Recorder must be separate from settlement signer')
    registry = w3.eth.contract(address=Web3.to_checksum_address(os.environ['PAYMENT_RECEIPT_REGISTRY_ADDRESS']),abi=ABI)
    if not w3.eth.get_code(registry.address) or not registry.functions.sandbox().call() or not registry.functions.hasRole(Web3.keccak(text='RECORDER_ROLE'),account.address).call():
        raise ValueError('Registry sandbox or recorder role mismatch')
    return w3,account,registry


def call_for(registry, job, payment):
    ref = Web3.keccak(text='dkm:receipt:v1:'+str(job['evidence_id']))
    if job['reversal_status']:
        return registry.functions.recordReversal(ref,job['reversal_status'],bytes.fromhex(job['evidence_hash'][2:]))
    return registry.functions.recordPayment(ref,payment_tuple(payment))


def prepare(job,payment):
    w3,account,registry = connection()
    tx = call_for(registry,job,payment).build_transaction({'from':account.address,'chainId':80002,
        'nonce':w3.eth.get_transaction_count(account.address,'pending'),'gasPrice':w3.eth.gas_price})
    signed = account.sign_transaction(tx)
    return {'chain_id':80002,'registry':registry.address,'signer':account.address,
            'tx_hash':Web3.to_hex(signed.hash),'raw_tx':Web3.to_hex(signed.raw_transaction)}


def validate_source(proof):
    from services import blockchain
    w3=blockchain.w3
    if w3.eth.chain_id!=proof['chain_id']: raise ValueError('Source chain changed')
    try:
        receipt=w3.eth.get_transaction_receipt(proof['transaction_hash'])
    except TransactionNotFound as exc:
        raise ValueError('Original payment disappeared') from exc
    if (receipt.status!=1 or receipt.blockNumber!=proof['block_number']
            or Web3.to_hex(receipt.blockHash)!=proof['block_hash']
            or not confirmed_receipt(w3,proof['transaction_hash'],receipt)):
        raise ValueError('Original payment is no longer confirmed')


def verify_or_broadcast(job,payment):
    w3,account,registry = connection()
    if job['chain_id']!=80002 or job['registry']!=registry.address or job['signer']!=account.address:
        raise ValueError('Recorder deployment changed; review required')
    if Web3.to_hex(Web3.keccak(hexstr=job['raw_tx'])).lower()!=job['tx_hash'].lower():
        raise ValueError('Checkpoint hash mismatch')
    from eth_account._utils.legacy_transactions import Transaction
    from hexbytes import HexBytes
    unsigned = Transaction.from_bytes(HexBytes(job['raw_tx'])).as_dict()
    expected = call_for(registry,job,payment)._encode_transaction_data()
    if (w3.eth.account.recover_transaction(job['raw_tx'])!=account.address
            or (unsigned['v']-35)//2 != 80002 or unsigned['value']!=0
            or Web3.to_checksum_address(unsigned['to'])!=registry.address
            or Web3.to_hex(unsigned['data']).lower()!=expected.lower()):
        raise ValueError('Signed checkpoint does not match the audit job')
    try:
        receipt = w3.eth.get_transaction_receipt(job['tx_hash'])
    except TransactionNotFound:
        if job['state']=='recorded': raise ValueError('Recorded transaction disappeared')
        try: w3.eth.get_transaction(job['tx_hash'])
        except TransactionNotFound: w3.eth.send_raw_transaction(job['raw_tx'])
        return None
    if not confirmed_receipt(w3,job['tx_hash'],receipt): return None
    tx = w3.eth.get_transaction(job['tx_hash'])
    if tx['to']!=registry.address or tx['from']!=account.address or Web3.to_hex(tx['input']).lower()!=expected.lower() or tx.get('value',0)!=0:
        raise ValueError('Recording transaction identity mismatch')
    if receipt.status!=1: raise ValueError('Recorder transaction reverted')
    from web3.logs import DISCARD
    event = registry.events.PaymentReversed() if job['reversal_status'] else registry.events.PaymentRecorded()
    events = [e for e in event.process_receipt(receipt,errors=DISCARD) if e['address'].lower()==registry.address.lower()]
    ref = Web3.keccak(text='dkm:receipt:v1:'+str(job['evidence_id']))
    matches = [e['args'] for e in events if e['args']['paymentRef']==ref]
    if len(matches)!=1: raise ValueError('Missing or duplicate registry event')
    args=matches[0]
    if job['reversal_status']:
        if args['status']!=job['reversal_status'] or Web3.to_hex(args['evidenceHash'])!=job['evidence_hash']:
            raise ValueError('Wrong reversal evidence')
    elif Web3.to_hex(args['paymentHash'])!=payment_hash(payment) or dict(args['payment'])!=dict(zip(FIELDS,payment_tuple(payment))):
        raise ValueError('Wrong recorded payment evidence')
    stored=registry.functions.records(ref).call(block_identifier=receipt.blockNumber)
    if Web3.to_hex(stored[0])!=payment_hash(payment) or stored[1]!=(job['reversal_status'] or 1):
        raise ValueError('Registry state mismatch')
    return {'block_number':receipt.blockNumber,'block_hash':Web3.to_hex(receipt.blockHash)}


async def record_job(job_id):
    conn = await get_conn()
    try:
        if not await conn.fetchval('SELECT pg_try_advisory_lock(80002,7321)'): return
        row=await conn.fetchrow('SELECT j.*,e.payment,e.evidence FROM receipt_jobs j JOIN payment_evidence e ON e.id=j.evidence_id WHERE j.id=$1',UUID(str(job_id)))
        if not row or row['state']=='review_required': return
        job=dict(row); payment=json.loads(row['payment'])
        await conn.execute('UPDATE receipt_jobs SET updated_at=NOW() WHERE id=$1',job['id'])
        if job['reversal_status'] and not await conn.fetchval("SELECT EXISTS(SELECT 1 FROM receipt_jobs WHERE evidence_id=$1 AND reversal_status=0 AND state='recorded')",job['evidence_id']): return
        try:
            await asyncio.to_thread(validate_source,json.loads(row['evidence']))
            if not job['raw_tx']:
                if await conn.fetchval("SELECT EXISTS(SELECT 1 FROM receipt_jobs WHERE raw_tx IS NOT NULL AND state<>'recorded' AND id<>$1)",job['id']):
                    await conn.execute('UPDATE receipt_jobs SET updated_at=NOW() WHERE id=$1',job['id'])
                    return
                checkpoint=await asyncio.to_thread(prepare,job,payment)
                await conn.execute("UPDATE receipt_jobs SET state='recording',chain_id=$2,registry=$3,signer=$4,tx_hash=$5,raw_tx=$6,updated_at=NOW() WHERE id=$1",job['id'],*[checkpoint[k] for k in ('chain_id','registry','signer','tx_hash','raw_tx')])
                job.update(checkpoint)
            result=await asyncio.to_thread(verify_or_broadcast,job,payment)
            if result:
                await conn.execute("UPDATE receipt_jobs SET state='recorded',block_number=$2,block_hash=$3,error=NULL,updated_at=NOW() WHERE id=$1",job['id'],result['block_number'],result['block_hash'])
            elif job['state']=='recorded':
                raise ValueError('Recorded transaction no longer confirmed')
            else:
                await conn.execute('UPDATE receipt_jobs SET updated_at=NOW(),error=NULL WHERE id=$1',job['id'])
        except ValueError:
            await conn.execute("UPDATE receipt_jobs SET state='review_required',error='Recording evidence or configuration needs operator review',updated_at=NOW() WHERE id=$1",job['id'])
        except Exception:
            await conn.execute("UPDATE receipt_jobs SET error='Recorder temporarily unavailable; checkpoint preserved',updated_at=NOW() WHERE id=$1",job['id'])
    finally:
        await conn.close()


async def recording_worker():
    while True:
        try:
            conn=await get_conn()
            try:
                rows=await conn.fetch("SELECT id FROM receipt_jobs WHERE state<>'review_required' ORDER BY updated_at LIMIT 5")
            finally: await conn.close()
            for row in rows: await record_job(row['id'])
        except Exception:
            logging.getLogger(__name__).warning('Audit recorder unavailable; retrying later')
        await asyncio.sleep(60)


@router.get('')
async def history(user=Depends(current_user)):
    conn=await get_conn()
    try:
        rows=await conn.fetch("""SELECT j.id,j.state,j.tx_hash,j.error,j.reversal_status,e.payment,e.created_at
            FROM receipt_jobs j JOIN payment_evidence e ON e.id=j.evidence_id
            WHERE e.user_id=$1 OR lower(e.payment->>'seller')=lower($2::text)
            ORDER BY e.created_at DESC LIMIT 100""",user['id'],user.get('wallet_address'))
        return {'audit_only':True,'enabled':os.getenv('RECEIPT_RECORDING_ENABLED')=='true','records':[
            {'id':str(r['id']),'state':r['state'],'tx_hash':r['tx_hash'],'error':r['error'],
             'reversal_status':r['reversal_status'],'token_id':json.loads(r['payment'])['tokenId'],'sandbox':True} for r in rows]}
    finally: await conn.close()
