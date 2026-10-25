import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from services.pgvector_client import get_conn

async def main():
    conn=await get_conn()
    try:
        async with conn.transaction():
            row=await conn.fetchrow('SELECT id,wallet_address FROM app_users WHERE username=$1 FOR UPDATE','codex_ui_probe_20261011b')
            assert row and row['wallet_address'].lower()=='0xf95c90497c91bb98253e2e818ac54a4d62bd046f'
            await conn.execute('DELETE FROM app_sessions WHERE user_id=$1',row['id'])
            result=await conn.execute('DELETE FROM app_users WHERE id=$1',row['id'])
            assert result=='DELETE 1'
        print('Removed only the disposable dashboard account and its sessions.')
    finally:await conn.close()

asyncio.run(main())
