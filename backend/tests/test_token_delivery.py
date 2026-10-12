import unittest
from copy import deepcopy
from types import SimpleNamespace
from web3.datastructures import AttributeDict
from hexbytes import HexBytes
from services.payments.token_delivery import TRNSK, TRANSFER, verify_delivery


class DeliveryTests(unittest.TestCase):
    def test_canonical_delivery_amount_recipient_network_and_reorg(self):
        tx, block = HexBytes("0x"+"11"*32), HexBytes("0x"+"22"*32)
        recipient = "0x"+"33"*20
        log = {"address":TRNSK,"topics":[TRANSFER,bytes(32),int(recipient,16).to_bytes(32)],
               "data":(10**19+1).to_bytes(32),"blockHash":block,"transactionHash":tx}
        receipt = AttributeDict({"status":1,"transactionHash":tx,"blockHash":block,"blockNumber":10,"logs":[log]})
        eth = SimpleNamespace(chain_id=80002,block_number=11,get_block=lambda _:SimpleNamespace(hash=block),
                              get_transaction_receipt=lambda _:receipt)
        w3 = SimpleNamespace(eth=eth)
        result = verify_delivery(w3, tx.to_0x_hex(), recipient, 10**19+1)
        self.assertEqual(result["amount_base_units"],str(10**19+1))
        self.assertFalse(result["grants_access"])
        for required, target in [(10**19+2,recipient),(1,"0x"+"44"*20)]:
            with self.assertRaises(ValueError):verify_delivery(w3,tx.to_0x_hex(),target,required)
        for field,value in [("chain_id",1),("block_number",10)]:
            old=getattr(eth,field);setattr(eth,field,value)
            with self.assertRaises(ValueError):verify_delivery(w3,tx.to_0x_hex(),recipient,1)
            setattr(eth,field,old)
        for field, value in [("status",0),("transactionHash",HexBytes(bytes(32)))]:
            changed = dict(receipt); changed[field] = value
            eth.get_transaction_receipt = lambda _, changed=changed: AttributeDict(changed)
            with self.assertRaises(ValueError): verify_delivery(w3,tx.to_0x_hex(),recipient,1)
        for field, value in [("address","0x"+"55"*20),("removed",True),
                             ("transactionHash",HexBytes(bytes(32))),("data",b"short")]:
            changed = dict(receipt); changed["logs"] = [{**log,field:value}]
            eth.get_transaction_receipt = lambda _, changed=changed: AttributeDict(changed)
            with self.assertRaises(ValueError): verify_delivery(w3,tx.to_0x_hex(),recipient,1)
        eth.get_transaction_receipt = lambda _: receipt
        for value in [None,"", "0x123"]:
            with self.assertRaises(ValueError): verify_delivery(w3,value,recipient,1)
        eth.get_block=lambda _:SimpleNamespace(hash=bytes(32))
        with self.assertRaises(ValueError):verify_delivery(w3,tx.to_0x_hex(),recipient,1)
