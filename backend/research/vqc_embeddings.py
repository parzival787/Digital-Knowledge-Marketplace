"""Train a small quantum feature map on training embeddings only, then expand to 384D."""
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sklearn.decomposition import PCA


def normalize(values):
    values = np.asarray(values,dtype=float)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("Expected a finite matrix")
    norms = np.linalg.norm(values,axis=1,keepdims=True)
    return values / np.maximum(norms,1e-12)


def quantum_features():
    device=qml.device("default.qubit",wires=4,shots=None)
    @qml.qnode(device,interface="autograd",diff_method="backprop")
    def circuit(angles,weights):
        for wire in range(4): qml.RY(angles[:,wire],wires=wire)
        for layer in weights:
            for wire in range(4):
                qml.RY(layer[wire,0],wires=wire)
                qml.RZ(layer[wire,1],wires=wire)
            for wire in range(4): qml.CNOT(wires=[wire,(wire+1)%4])
        return [qml.expval(qml.PauliZ(w)) for w in range(4)] + [qml.expval(qml.PauliZ(w) @ qml.PauliZ((w+1)%4)) for w in range(4)]
    return circuit


def decoder(features,targets):
    design=np.column_stack((features,np.ones(len(features))))
    regularizer=np.eye(design.shape[1])*.01;regularizer[-1,-1]=0
    return np.linalg.solve(design.T @ design + regularizer,design.T @ targets)


def expand(features,weights):
    return normalize(np.column_stack((features,np.ones(len(features)))) @ weights)


def train(training,seed=31,epochs=40):
    training=normalize(training)
    if training.shape[1] != 384 or len(training)<8 or not 1<=epochs<=200:
        raise ValueError("Need at least eight 384D training vectors and a bounded epoch budget")
    pca=PCA(n_components=4,svd_solver="full")
    compressed=pca.fit_transform(training)
    scale=np.maximum(compressed.std(axis=0),1e-6)
    angles=pnp.array(np.arctan(compressed/scale),requires_grad=False)
    target=pnp.array(training @ training.T,requires_grad=False)
    weights=pnp.array(np.random.default_rng(seed).normal(0,.2,(2,4,2)),requires_grad=True)
    initial=np.asarray(weights).copy()
    circuit=quantum_features()
    def loss(parameters):
        features=pnp.stack(circuit(angles,parameters),axis=1)
        unit=features / pnp.sqrt(pnp.sum(features**2,axis=1,keepdims=True)+1e-9)
        return pnp.mean((unit @ unit.T-target)**2)
    optimizer=qml.AdamOptimizer(stepsize=.04)
    trace=[float(loss(weights))]
    best=np.asarray(weights).copy();best_loss=trace[0]
    for _ in range(epochs):
        weights=optimizer.step(loss,weights)
        measured=float(loss(weights));trace.append(measured)
        if measured<best_loss:best=np.asarray(weights).copy();best_loss=measured
    trained=np.stack(circuit(angles,best),axis=1)
    untrained=np.stack(circuit(angles,initial),axis=1)
    return {"mean":pca.mean_,"components":pca.components_,"scale":scale,"weights":best,"initial_weights":initial,
        "decoder":decoder(trained,training),"initial_decoder":decoder(untrained,training),
        "classical_decoder":decoder(compressed,training),"loss_trace":np.asarray(trace)}


def transform(vectors,model,mode="trained"):
    vectors=normalize(vectors)
    if vectors.shape[1]!=384 or mode not in ("trained","untrained","classical"):
        raise ValueError("Expected 384D vectors and a known transform")
    compressed=(vectors-model["mean"]) @ model["components"].T
    if mode=="classical":return expand(compressed,model["classical_decoder"])
    weights=model["weights"] if mode=="trained" else model["initial_weights"]
    features=np.stack(quantum_features()(np.arctan(compressed/model["scale"]),weights),axis=1)
    return expand(features,model["decoder"] if mode=="trained" else model["initial_decoder"])


def ndcg(relevance,scores,k=10):
    relevance=np.asarray(relevance,dtype=float);scores=np.asarray(scores,dtype=float)
    if relevance.ndim!=1 or relevance.shape!=scores.shape or not np.all(np.isfinite(relevance)) or not np.all(np.isfinite(scores)) or np.any(relevance<0) or k<1:
        raise ValueError("Invalid relevance/scores")
    discounts=np.log2(np.arange(min(k,len(scores)))+2)
    order=np.argsort(-scores,kind="stable")[:k]
    ideal=np.sort(relevance)[::-1][:k]
    maximum=np.sum((2**ideal-1)/discounts)
    return float(np.sum((2**relevance[order]-1)/discounts)/maximum) if maximum else 0.0
