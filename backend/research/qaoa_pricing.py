"""Small-grid QAOA pricing simulation with explicit synthetic demand assumptions."""
import numpy as np
import pennylane as qml
from scipy.optimize import minimize
from scipy.special import expit


def demand_revenue(prices, willingness, temperature, visitors, platform_bps=500):
    """Expected seller revenue under a stipulated logistic demand curve, not live FX."""
    values = np.asarray([willingness, temperature, visitors, platform_bps], dtype=float)
    prices = np.asarray(prices, dtype=float)
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(prices)) or np.any(prices <= 0):
        raise ValueError("Finite positive prices and demand parameters required")
    if not 1 <= willingness <= 100 or not 0 < temperature <= 100 or not 0 < visitors <= 1e6 or not 0 <= platform_bps <= 1000:
        raise ValueError("Demand parameters outside experiment bounds")
    return prices * expit((willingness - prices) / temperature) * visitors * (1 - platform_bps / 10000)


def circuit_for(costs):
    costs = np.asarray(costs, dtype=float)
    if costs.ndim != 1 or len(costs) < 2 or len(costs) > 256 or len(costs) & (len(costs)-1) or not np.all(np.isfinite(costs)):
        raise ValueError("Cost diagonal must have 2^n finite entries, n=1..8")
    wires = range(int(np.log2(len(costs))))
    device = qml.device("default.qubit", wires=len(wires), shots=None)

    @qml.qnode(device)
    def circuit(parameters):
        for wire in wires:
            qml.Hadamard(wires=wire)
        for gamma, beta in parameters:
            qml.DiagonalQubitUnitary(np.exp(-1j * gamma * costs), wires=wires)
            for wire in wires:
                qml.RX(2 * beta, wires=wire)
        return qml.probs(wires=wires)
    return circuit


def optimize_prices(revenue, *, seed=7, depth=2, evaluations=80, shots=2048):
    revenue = np.asarray(revenue, dtype=float)
    if revenue.ndim != 1 or not 2 <= len(revenue) <= 100 or not np.all(np.isfinite(revenue)) or np.any(revenue < 0) or revenue.max() <= 0:
        raise ValueError("Expected 2..100 nonnegative feasible price revenues")
    if not 1 <= depth <= 4 or not 10 <= evaluations <= 1000 or not 1 <= shots <= 100000:
        raise ValueError("Experiment budget outside bounds")
    n = int(np.ceil(np.log2(len(revenue))))
    # Invalid binary states have a positive penalty; feasible states minimize -revenue.
    costs = np.full(2**n, 2.0)
    costs[:len(revenue)] = -revenue / revenue.max()
    circuit = circuit_for(costs)
    rng = np.random.default_rng(seed)
    initial = rng.uniform(0, np.pi, size=(depth,2))
    trace = []
    def loss(flat):
        expected = float(np.dot(circuit(flat.reshape(depth,2)), costs))
        trace.append(expected)
        return expected
    fitted = minimize(loss, initial.ravel(), method="COBYLA", options={"maxiter":evaluations,"rhobeg":0.5,"tol":1e-5})
    probabilities = np.asarray(circuit(fitted.x.reshape(depth,2)), dtype=float)
    probabilities = np.maximum(probabilities,0); probabilities /= probabilities.sum()
    counts = rng.multinomial(shots, probabilities)
    feasible = counts[:len(revenue)]
    # Modal feasible sampled state, not oracle cherry-picking the best observed price.
    selected = int(np.argmax(feasible)) if feasible.sum() else None
    return {"price_index":selected,"parameters":fitted.x.reshape(depth,2).tolist(),
        "probabilities":probabilities.tolist(),"counts":counts.tolist(),"loss_trace":trace,
        "expected_revenue":float(np.dot(probabilities[:len(revenue)],revenue)),
        "feasible_probability":float(probabilities[:len(revenue)].sum()),
        "selected_revenue":float(revenue[selected]) if selected is not None else 0.0,
        "optimal_revenue":float(revenue.max()),"optimal_price_index":int(np.argmax(revenue)),
        "optimizer_success":bool(fitted.success),"optimizer_message":str(fitted.message),
        "evaluations":len(trace),"qubits":n,"depth":depth,"shots":shots,"seed":seed}
