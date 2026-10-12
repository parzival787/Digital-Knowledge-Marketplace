"""Read-only staging coverage probe; emits only sanitized route metadata."""
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"))
from services.payments.transak_discovery import discover, quote


async def main():
    try:
        result = await discover("127.0.0.1")
        public = {"verified": True, "environment": "staging", "checked_at": result["checked_at"],
                  "fiat": [c for c in result["fiat"] if c["symbol"] in ("INR", "USD", "EUR", "IDR")],
                  "sandbox_route": [c for c in result["crypto"] if c["symbol"] == "USDC" and c["network"] == "polygon"],
                  "limitation": "Runtime lookup using localhost IP; final user eligibility and hosted checkout still require verification."}
        try:
            public["buy_quote_probe"] = await quote("127.0.0.1", "BUY", "USD", "credit_debit_card", "10")
        except Exception as exc:
            public["buy_quote_probe"] = {"verified": False, "error_type": type(exc).__name__}
    except Exception as exc:
        public = {"verified": False, "error_type": type(exc).__name__, "environment": "staging"}
    print(json.dumps(public, indent=2))
    Path(__file__).resolve().parents[1].joinpath("transak_coverage_evidence.json").write_text(json.dumps(public, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
