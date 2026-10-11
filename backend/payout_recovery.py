"""Local operator inspection/resolution; no money movement or entitlement changes."""
import argparse
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()
from services.payments.payouts import get_conn, digest, resolve_payout


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list', 'accept-observation'])
    parser.add_argument('--payout')
    parser.add_argument('--digest')
    parser.add_argument('--reason', default='')
    args = parser.parse_args()
    if args.action == 'accept-observation':
        if not args.payout or not args.digest:
            parser.error('--payout and --digest are required')
        await resolve_payout(args.payout, args.digest, args.reason)
        print('Observation accepted with database-authenticated operator audit; no funds or access changed.')
    else:
        conn = await get_conn()
        try:
            for row in await conn.fetch("SELECT id,receipt,observed FROM seller_payouts WHERE state='review_required' ORDER BY created_at LIMIT 100"):
                observed = json.loads(row['observed'])
                print(json.dumps({'payout':str(row['id']), 'digest':digest(observed), 'previous':json.loads(row['receipt']) if row['receipt'] else None, 'observed':observed}))
        finally:
            await conn.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        raise SystemExit('Payout recovery failed; no resolution confirmed. Check binding, evidence digest and database permissions.') from None
