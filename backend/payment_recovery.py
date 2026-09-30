"""Run from backend: python payment_recovery.py --help. Restricted operator host only."""
import argparse
import asyncio
from dotenv import load_dotenv

load_dotenv()
from services import pgvector_client as db
from services.payments.recovery import recover


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "hold", "resume", "record-refund"])
    parser.add_argument("--order")
    parser.add_argument("--reason", default="")
    parser.add_argument("--refund-id")
    args = parser.parse_args()
    if args.action == "list":
        conn = await db.get_conn()
        try:
            rows = await conn.fetch("""SELECT order_id, status, recovery_status, settlement_attempts
                FROM payment_orders WHERE recovery_status='REVIEW_REQUIRED' ORDER BY created_at LIMIT 100""")
            for row in rows:
                print(dict(row))
        finally:
            await conn.close()
    else:
        if not args.order:
            parser.error("--order is required")
        order = await recover(args.order, args.action, args.reason, args.refund_id)
        print(f"{order.order_id}: {order.recovery_status or order.status.value}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        # SDK exceptions may contain credentials in RPC URLs. Never print them.
        raise SystemExit(f"Recovery failed ({type(exc).__name__}); no success confirmed. Check policy and provider/chain status.") from None
