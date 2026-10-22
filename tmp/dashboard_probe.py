import asyncio
import httpx
from eth_account import Account
from eth_account.messages import encode_defunct

async def main():
    async with httpx.AsyncClient(base_url='http://localhost:8000',headers={'origin':'http://localhost:3000','x-dkm-request':'1'},timeout=120) as client:
        response=await client.post('/api/auth/signup',json={'username':'codex_ui_probe_20261011b','password':'Disposable-demo-only-2026!'})
        assert response.status_code==200, response.status_code
        wallet=Account.create()
        challenge=(await client.post('/api/auth/wallet/challenge')).json()['message']
        verified=await client.post('/api/auth/wallet/verify',json={'address':wallet.address,'signature':wallet.sign_message(encode_defunct(text=challenge)).signature.hex()})
        assert verified.status_code==200, verified.status_code
        for path in ('/api/account/dashboard','/api/account/reviews','/api/payments/transak/payouts','/api/payments/recordings','/api/account/positions','/api/account/indexed-activity'):
            result=await client.get(path)
            print(path,result.status_code,flush=True)
            assert result.status_code==200
        print('Disposable local UI account prepared; no funds or provider payments.',flush=True)

asyncio.run(main())
