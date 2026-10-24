"""Read-only chain ingestion and optional rebuild of derived event history."""
import argparse
import asyncio
from dotenv import load_dotenv
load_dotenv()
from services import event_indexer as index


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pages',type=int,default=1)
    parser.add_argument('--rebuild-market')
    args=parser.parse_args()
    if not 1<=args.pages<=10000: parser.error('pages must be 1..10000')
    await index.setup_indexer()
    markets=[m.address for m in index.blockchain.entitlement_markets()]
    if args.rebuild_market:
        if args.rebuild_market.lower() not in [m.lower() for m in markets]: parser.error('Only configured markets may be rebuilt')
        await index.rebuild_market(args.rebuild_market)
    for _ in range(args.pages):
        for market in markets: await index.sync_market(market)
    conn=await index.get_conn()
    try:
        for row in await conn.fetch('SELECT market,deployment_block,next_block,state,error FROM chain_sync'):
            print(dict(row))
    finally: await conn.close()


if __name__=='__main__':
    try: asyncio.run(main())
    except Exception: raise SystemExit('History sync unavailable; checkpoint preserved. No blockchain state was changed.') from None
