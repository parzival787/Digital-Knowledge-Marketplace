"""Run from backend: python -m research.run_pricing. No DB, secrets or network."""
import json
import time
from pathlib import Path
from importlib.metadata import version
import numpy as np
from scipy.optimize import minimize_scalar
from .qaoa_pricing import demand_revenue, optimize_prices


def main():
    rng = np.random.default_rng(20261011)
    prices = np.arange(1,101)
    rows = []
    for index in range(64):
        asset = {"asset_id":f"synthetic-{index+1:03}", "willingness":float(rng.uniform(10,100)),
                 "temperature":float(rng.uniform(3,18)), "visitors":int(rng.integers(50,501)),
                 "reference_price":int(rng.integers(1,101))}
        started = time.perf_counter()
        revenue = demand_revenue(prices,asset["willingness"],asset["temperature"],asset["visitors"])
        exact_index = int(np.argmax(revenue))
        exact_seconds = time.perf_counter()-started
        started = time.perf_counter()
        classical = minimize_scalar(lambda p:-float(demand_revenue([p],asset["willingness"],asset["temperature"],asset["visitors"])[0]),
                                    bounds=(1,100),method="bounded")
        adjacent = np.clip([int(np.floor(classical.x)),int(np.ceil(classical.x))],1,100)
        classical_price = int(adjacent[np.argmax(revenue[adjacent-1])])
        classical_seconds = time.perf_counter()-started
        started = time.perf_counter()
        qaoa = optimize_prices(revenue,seed=1000+index)
        qaoa_seconds = time.perf_counter()-started
        uniform_counts = np.random.default_rng(1000+index).multinomial(qaoa["shots"],np.full(100,0.01))
        uniform_price = int(np.argmax(uniform_counts))+1
        rows.append({**asset,"qaoa":qaoa,"qaoa_price":qaoa["price_index"]+1 if qaoa["price_index"] is not None else None,
            "exact_price":exact_index+1,"classical_price":classical_price,"uniform_price":uniform_price,
            "reference_revenue":float(revenue[asset["reference_price"]-1]),"classical_revenue":float(revenue[classical_price-1]),
            "uniform_revenue":float(revenue[uniform_price-1]),"qaoa_seconds":qaoa_seconds,
            "classical_seconds":classical_seconds,"exact_seconds":exact_seconds})
        if (index+1)%16==0: print(f"Pricing benchmark: {index+1}/64",flush=True)
    summary = {"assets":len(rows),"mean_qaoa_relative_gap":float(np.mean([1-r["qaoa"]["selected_revenue"]/r["qaoa"]["optimal_revenue"] for r in rows])),
        "mean_qaoa_feasible_probability":float(np.mean([r["qaoa"]["feasible_probability"] for r in rows])),
        "qaoa_exact_price_matches":sum(r["qaoa_price"]==r["exact_price"] for r in rows),
        "classical_exact_price_matches":sum(r["classical_price"]==r["exact_price"] for r in rows)}
    for method in ("qaoa","classical","reference","uniform"):
        summary[f"mean_{method}_revenue"] = float(np.mean([r["qaoa"]["selected_revenue"] if method=="qaoa" else r[f"{method}_revenue"] for r in rows]))
    for method in ("qaoa","classical","exact"):
        summary[f"mean_{method}_seconds"] = float(np.mean([r[f"{method}_seconds"] for r in rows]))
    out=Path(__file__).resolve().parents[2]/"research_results"
    out.mkdir(exist_ok=True)
    result={"environment":"classical statevector simulator, not quantum hardware","dataset":"64 seeded synthetic demand curves, not actual asset sales",
        "dataset_seed":20261011,"price_grid_usdc":[1,100],"platform_fee_bps":500,"royalty_assumption":"none",
        "versions":{k:version(k) for k in ("pennylane","numpy","scipy")},"summary":summary,"assets":rows}
    (out/"qaoa_pricing.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
    lines=["# QAOA pricing benchmark", "", "Measured local simulation; no marketplace prices or payments changed.",
           "Synthetic logistic demand is an experimental assumption, not observed revenue.","", "| Metric | Result |","| --- | --- |"]
    lines += [f"| {key} | {value:.6f} |" if isinstance(value,float) else f"| {key} | {value} |" for key,value in summary.items()]
    lines += ["", "## Method and limitations", "", "64 assets; 100 integer price choices; 7 qubits; QAOA depth 2; COBYLA up to 80 objective evaluations; 2048 seeded samples per asset.",
        "The cost Hamiltonian is diagonal negative normalized expected seller revenue, with invalid binary-state penalty 2. RX mixers alternate with cost unitaries. Selection is the most frequent feasible sampled state (ties choose the lower price).",
        "Classical baseline uses bounded scalar optimization and adjacent integer prices; exhaustive search supplies the exact oracle. The uniform baseline has the same sample count. Random reference prices are not the project's LLM recommendations.",
        "This small smooth independent-price problem favors classical optimization. Full diagonal construction and simulator costs are exponential; no scalable quantum oracle, hardware speedup or quantum advantage is claimed.",
        "Parameters, probabilities, counts, traces, per-asset results and runtime are in qaoa_pricing.json. Budget exhaustion is recorded rather than mislabelled convergence.",
        "", "References: https://arxiv.org/abs/1411.4028 and https://docs.pennylane.ai/en/stable/code/api/pennylane.DiagonalQubitUnitary.html"]
    (out/"QAOA_PRICING_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()
