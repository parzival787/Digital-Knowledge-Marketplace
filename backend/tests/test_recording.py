import asyncio
import json
import unittest
from unittest.mock import patch
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import MagicMock
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_abi import encode
from eth_utils import event_abi_to_log_topic
from hexbytes import HexBytes
from services.payments import recording
from tests import test_transak


class RecordingTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = test_transak.TransakTests.asyncSetUp
    asyncTearDown = test_transak.TransakTests.asyncTearDown

    async def prepare(self):
        mock=patch.object(recording,'get_conn',self.isolated); mock.start(); self.addCleanup(mock.stop)
        source=patch.object(recording,'validate_source');source.start();self.addCleanup(source.stop)
        await recording.setup_recording()
        self.terms={'assetContract':'0x'+'1'*40,'tokenId':1,'buyer':'0x'+'2'*40,'seller':'0x'+'3'*40,
                    'paymentCurrency':'0x'+'4'*64,'paymentAmount':100,'payoutCurrency':'0x'+'5'*64,'payoutAmount':95}
        self.proof={'chain_id':80002,'transaction_hash':'0x'+'6'*64,'block_hash':'0x'+'7'*64,'block_number':10}
        self.evidence=await recording.enqueue_verified(1,'amoy_marketplace','tx:log',self.terms,self.proof)
        conn=await self.isolated()
        self.job=await conn.fetchval('SELECT id FROM receipt_jobs')
        await conn.close()

    async def test_immutable_duplicate_evidence_and_reversal(self):
        await self.prepare()
        self.assertEqual(await recording.enqueue_verified(1,'amoy_marketplace','tx:log',self.terms,self.proof),self.evidence)
        with self.assertRaises(ValueError):
            await recording.enqueue_verified(2,'amoy_marketplace','tx:log',self.terms,self.proof)
        with self.assertRaises(ValueError):
            await recording.enqueue_verified(1,'mock','tx:log',self.terms,self.proof)
        reversal=await recording.enqueue_reversal(self.evidence,2,'verified-refund')
        self.assertEqual(await recording.enqueue_reversal(self.evidence,2,'verified-refund'),reversal)
        with self.assertRaises(ValueError): await recording.enqueue_reversal(self.evidence,3,'different')
        self.assertEqual((await recording.history({'id':2}))['records'],[])
        rows=(await recording.history({'id':1}))['records']
        self.assertEqual(len(rows),2)
        self.assertEqual(len((await recording.history({'id':2,'wallet_address':self.terms['seller']}))['records']),2)
        with self.assertRaises(ValueError):
            await recording.enqueue_verified(1,'amoy_marketplace','bad-block',self.terms,{**self.proof,'block_number':True})
        self.assertNotIn('raw_tx',str(rows))
        self.assertNotIn('tx:log',str(rows))

    def test_source_must_remain_confirmed_and_canonical(self):
        from services import blockchain
        block_hash=HexBytes('0x'+'7'*64)
        proof={'chain_id':80002,'transaction_hash':'0x'+'6'*64,'block_hash':Web3.to_hex(block_hash),'block_number':10}
        eth=MagicMock();eth.chain_id=80002;eth.block_number=11
        eth.get_block.return_value=AttributeDict({'hash':block_hash})
        eth.get_transaction_receipt.return_value=AttributeDict({'status':1,'blockNumber':10,'blockHash':block_hash,'transactionHash':HexBytes(proof['transaction_hash'])})
        with patch.object(blockchain,'w3',SimpleNamespace(eth=eth)):
            recording.validate_source(proof)
            eth.get_block.return_value=AttributeDict({'hash':HexBytes('0x'+'8'*64)})
            with self.assertRaises(ValueError):recording.validate_source(proof)
            eth.get_transaction_receipt.side_effect=TransactionNotFound('removed')
            with self.assertRaises(ValueError):recording.validate_source(proof)

    async def test_source_reorg_stops_before_signing(self):
        await self.prepare()
        with patch.object(recording,'validate_source',side_effect=ValueError('removed')),patch.object(recording,'prepare') as sign:
            await recording.record_job(self.job)
            sign.assert_not_called()
        conn=await self.isolated()
        row=await conn.fetchrow('SELECT state,raw_tx FROM receipt_jobs WHERE id=$1',self.job)
        self.assertEqual(row['state'],'review_required');self.assertIsNone(row['raw_tx'])
        await conn.close()

    async def test_checkpoint_restart_nonce_serialization_and_reorg(self):
        await self.prepare()
        checkpoint={'chain_id':80002,'registry':'0x'+'8'*40,'signer':'0x'+'9'*40,'tx_hash':'0x'+'a'*64,'raw_tx':'0x1234'}
        calls=[]
        def broadcast(job,payment):
            calls.append(job['raw_tx'])
            raise OSError('secret RPC credential')
        with patch.object(recording,'prepare',return_value=checkpoint) as prepare,patch.object(recording,'verify_or_broadcast',side_effect=broadcast):
            await asyncio.gather(recording.record_job(self.job),recording.record_job(self.job))
            await recording.record_job(self.job)
            self.assertEqual(prepare.call_count,1)
        self.assertTrue(all(raw=='0x1234' for raw in calls))
        conn=await self.isolated()
        row=await conn.fetchrow('SELECT * FROM receipt_jobs WHERE id=$1',self.job)
        self.assertEqual(row['state'],'recording');self.assertNotIn('secret',row['error'])
        await recording.enqueue_verified(1,'amoy_marketplace','second',self.terms,self.proof)
        second=await conn.fetchval('SELECT id FROM receipt_jobs WHERE id<>$1',self.job)
        with patch.object(recording,'prepare') as prepare:
            await recording.record_job(second)
            prepare.assert_not_called()
        with patch.object(recording,'verify_or_broadcast',return_value={'block_number':20,'block_hash':'0x'+'b'*64}):
            await recording.record_job(self.job)
        self.assertEqual(await conn.fetchval('SELECT state FROM receipt_jobs WHERE id=$1',self.job),'recorded')
        with patch.object(recording,'verify_or_broadcast',side_effect=ValueError('reorg')):
            await recording.record_job(self.job)
        self.assertEqual(await conn.fetchval('SELECT state FROM receipt_jobs WHERE id=$1',self.job),'review_required')
        await conn.close()

    def test_payment_hash_commits_to_all_fields(self):
        payment={'assetContract':'0x'+'1'*40,'tokenId':1,'buyer':'0x'+'2'*40,'seller':'0x'+'3'*40,
            'paymentCurrency':'0x'+'4'*64,'paymentAmount':100,'payoutCurrency':'0x'+'5'*64,'payoutAmount':95,
            'providerReference':'0x'+'6'*64,'evidenceHash':'0x'+'7'*64}
        self.assertNotEqual(recording.payment_hash(payment),recording.payment_hash({**payment,'payoutAmount':94}))

    def test_signed_checkpoint_and_emitted_event_verified_before_recorded(self):
        account=Account.create();w3=Web3();address=Web3.to_checksum_address('0x'+'8'*40)
        registry=w3.eth.contract(address=address,abi=recording.ABI)
        payment={'assetContract':'0x'+'1'*40,'tokenId':1,'buyer':'0x'+'2'*40,'seller':'0x'+'3'*40,
            'paymentCurrency':'0x'+'4'*64,'paymentAmount':100,'payoutCurrency':'0x'+'5'*64,'payoutAmount':95,
            'providerReference':'0x'+'6'*64,'evidenceHash':'0x'+'7'*64}
        job={'evidence_id':uuid4(),'reversal_status':0,'evidence_hash':payment['evidenceHash'],
             'chain_id':80002,'registry':address,'signer':account.address,'state':'recording'}
        calldata=recording.call_for(registry,job,payment)._encode_transaction_data()
        signed=account.sign_transaction({'chainId':80002,'nonce':0,'gasPrice':1,'gas':400000,'to':address,'value':0,'data':calldata})
        job.update(tx_hash=Web3.to_hex(signed.hash),raw_tx=Web3.to_hex(signed.raw_transaction))
        block_hash=HexBytes('0x'+'b'*64);ref=Web3.keccak(text='dkm:receipt:v1:'+str(job['evidence_id']))
        event_abi=next(a for a in recording.ABI if a.get('name')=='PaymentRecorded')
        log={'address':address,'topics':[event_abi_to_log_topic(event_abi),ref,HexBytes(encode(['address'],[payment['buyer']])),HexBytes(encode(['address'],[payment['seller']]))],
             'data':HexBytes(encode(['bytes32','('+','.join(recording.PAYMENT_TYPES)+')'],[HexBytes(recording.payment_hash(payment)),recording.payment_tuple(payment)])),
             'blockHash':block_hash,'blockNumber':10,'transactionHash':signed.hash,'transactionIndex':0,'logIndex':0}
        receipt=AttributeDict({'transactionHash':signed.hash,'blockHash':block_hash,'blockNumber':10,'status':1,'logs':[log]})
        eth=MagicMock();eth.account=Account;eth.block_number=11
        eth.get_block.return_value=AttributeDict({'hash':block_hash})
        eth.get_transaction_receipt.return_value=receipt
        eth.get_transaction.return_value={'to':address,'from':account.address,'input':HexBytes(calldata),'value':0}
        functions=SimpleNamespace(recordPayment=registry.functions.recordPayment,recordReversal=registry.functions.recordReversal,records=MagicMock())
        functions.records.return_value.call.return_value=(HexBytes(recording.payment_hash(payment)),1)
        registry.functions=functions
        with patch.object(recording,'connection',return_value=(SimpleNamespace(eth=eth),account,registry)):
            self.assertEqual(recording.verify_or_broadcast(job,payment)['block_number'],10)
            eth.get_transaction_receipt.return_value=AttributeDict({**dict(receipt),'logs':[]})
            with self.assertRaises(ValueError):recording.verify_or_broadcast(job,payment)
            eth.get_transaction_receipt.side_effect=TransactionNotFound('not found')
            job['state']='recorded'
            with self.assertRaises(ValueError):recording.verify_or_broadcast(job,payment)
            eth.send_raw_transaction.assert_not_called()
            job['state']='recording';job['signer']='0x'+'9'*40
            with self.assertRaises(ValueError):recording.verify_or_broadcast(job,payment)
            eth.send_raw_transaction.assert_not_called()
