"""Expose fixed, locally generated experiment evidence without executing training."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from services.auth import current_user

router=APIRouter(prefix="/api/research",tags=["Research evidence"])
RESULTS=Path(__file__).resolve().parents[2]/"research_results"


def load_result(filename):
    path=RESULTS/filename
    if not path.is_file() or path.stat().st_size>4_000_000:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        return None


@router.get("/results")
async def results(user=Depends(current_user)):
    pricing=load_result("qaoa_pricing.json")
    embedding=load_result("vqc_embeddings.json")
    return {"environment":"local_simulation", "changes_marketplace_prices":False,
        "changes_production_search":False,
        "pricing": {"summary":pricing["summary"],"dataset":pricing["dataset"],
            "samples":[{"asset_id":row["asset_id"],"qaoa_price":row["qaoa_price"],"classical_price":row["classical_price"],
                        "exact_price":row["exact_price"]} for row in pricing["assets"][:8]]} if pricing else None,
        "embeddings":{"summary":embedding["summary"],"dataset":embedding["dataset"],
            "training":embedding["training"],"training_seconds":embedding["training_seconds"],
            "initial_loss":embedding["loss_trace"][0],"best_loss":min(embedding["loss_trace"]),
            "qubits":embedding["qubits"],"output_dimensions":embedding["output_dimensions"]} if embedding else None}
