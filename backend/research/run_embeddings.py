"""Controlled authored-corpus retrieval experiment; no user content or secrets."""
import json
import time
import hashlib
from pathlib import Path
from importlib.metadata import version
import numpy as np
from sentence_transformers import SentenceTransformer
from .vqc_embeddings import train,transform,ndcg

TOPICS={
 "science":["stellar spectra and galaxy redshift","protein folding and amino acid structures","earthquake wave propagation","chemical reaction rates and catalysts"],
 "finance":["household budgeting and saving","bond yields and interest rates","company cash flow statements","insurance claim risk estimation"],
 "healthcare":["diabetes glucose monitoring","vaccine cold chain storage","cardiac ultrasound diagnosis","hospital appointment scheduling"],
 "technology":["database query indexes","wireless network packet routing","image segmentation neural networks","software memory allocation"],
 "social":["urban migration census patterns","classroom attendance and learning","public transport accessibility","language preservation and oral history"],
 "agriculture":["soil nitrogen and crop yield","drip irrigation water efficiency","orchard pest identification","seed germination temperature"],
 "environment":["river microplastic pollution","forest biodiversity surveys","solar panel energy output","coastal erosion monitoring"],
 "other":["museum artifact cataloguing","music rhythm annotation","sports motion analysis","historical manuscript transcription"],
}


def corpus():
    docs=[];queries=[]
    for domain,topics in TOPICS.items():
        for index,topic in enumerate(topics):
            key=domain+str(index)
            for variant,template in enumerate([
                "A dataset on {topic}. It includes measurements, annotated observations, units, collection dates and a data dictionary for reproducible analysis.",
                "Research methods for {topic}: experimental design, measurement protocol, uncertainty estimates, validation examples and documented limitations.",
                "An educational guide to {topic}, with worked examples, interpretation of results, practical exercises and references for further study."]):
                docs.append({"id":key+f"-{variant}","domain":domain,"topic":key,"text":template.format(topic=topic),"training":variant<2})
            queries.append({"id":key,"domain":domain,"topic":key,"text":f"Find knowledge resources about {topic} with examples and reliable observations.","split":"validation" if index%2==0 else "test"})
    return docs,queries


def main():
    docs,queries=corpus()
    # Use the project's cached model, with no network dependency or private uploads.
    embedder=SentenceTransformer("all-MiniLM-L6-v2",local_files_only=True)
    vectors=embedder.encode([d["text"] for d in docs],normalize_embeddings=True)
    query_vectors=embedder.encode([q["text"] for q in queries],normalize_embeddings=True)
    training_ids=[i for i,d in enumerate(docs) if d["training"]]
    started=time.perf_counter();model=train(vectors[training_ids]);training_seconds=time.perf_counter()-started
    rows=[];runtimes={};scores_by_mode={}
    for mode in ("original","classical","untrained","trained"):
        started=time.perf_counter()
        a,b=(vectors,query_vectors) if mode=="original" else (transform(vectors,model,mode),transform(query_vectors,model,mode))
        scores_by_mode[mode]=b @ a.T;runtimes[mode]=time.perf_counter()-started
    for i,query in enumerate(queries):
        labels=[3 if doc["topic"]==query["topic"] else 1 if doc["domain"]==query["domain"] else 0 for doc in docs]
        rows.append({**query,"relevance":labels,"ndcg_at_10":{mode:ndcg(labels,scores[i]) for mode,scores in scores_by_mode.items()},
                     "ranked_document_ids":{mode:[docs[j]["id"] for j in np.argsort(-scores[i],kind="stable")[:10]] for mode,scores in scores_by_mode.items()}})
    summary={split:{mode:float(np.mean([r["ndcg_at_10"][mode] for r in rows if r["split"]==split])) for mode in scores_by_mode} for split in ("validation","test")}
    out=Path(__file__).resolve().parents[2]/"research_results";out.mkdir(exist_ok=True)
    np.savez_compressed(out/"vqc_model.npz",**model)
    data={"environment":"PennyLane default.qubit classical simulation; no quantum hardware","dataset":"96 authored documents and 32 authored queries; controlled topic labels, not human relevance judgments",
        "training":"64 document vectors only; no query vectors, relevance labels or test scores used in fitting",
        "training_document_ids":[docs[i]["id"] for i in training_ids],"queries_used_for_training":[],
        "seed":31,"epochs":40,"qubits":4,"layers":2,"compressed_dimensions":4,"quantum_features":8,"output_dimensions":384,
        "embedding_model":"all-MiniLM-L6-v2","versions":{k:version(k) for k in ("pennylane","numpy","scikit-learn","sentence-transformers")},
        "model_sha256":hashlib.sha256((out/"vqc_model.npz").read_bytes()).hexdigest(),"training_seconds":training_seconds,"transform_seconds":runtimes,
        "loss_trace":model["loss_trace"].tolist(),"summary":summary,"documents":docs,"queries":rows}
    (out/"vqc_embeddings.json").write_text(json.dumps(data,indent=2,allow_nan=False),encoding="utf-8")
    lines=["# VQC embedding benchmark","","Measured local statevector simulation on an authored corpus; no quantum advantage claim.",
        "","| Split | Original MiniLM | PCA4 + expansion | Untrained VQC + expansion | Trained VQC + expansion |","| --- | --- | --- | --- | --- |"]
    lines += ["| "+split+" | "+" | ".join(f"{values[m]:.6f}" for m in ("original","classical","untrained","trained"))+" |" for split,values in summary.items()]
    lines += ["","## Method and limits","", "Training fits PCA4 and scaling on 64 training documents. Angle encoding uses arctan-scaled PCA features; two layers of RY/RZ and ring CNOT gates yield four Z and four adjacent ZZ expectations. Adam optimizes training-document cosine Gram alignment for 40 epochs. Ridge expansion restores 384 dimensions.",
        "Original 384D embeddings, PCA4/ridge and untrained-circuit/ridge baselines use identical documents, queries and labels. Expansion is trained on document vectors only. Validation/test topics are disjoint query sets; no test query, relevance label or test metric enters training or parameter selection.",
        "All 96 documents form the retrieval corpus; 32 document variants are excluded from model fitting. Query topics also occur in training documents, so this is in-domain retrieval, not unseen-topic generalization. Labels are authored topic/domain rules (3/1/0), not independent human judgments. Query wording overlaps document subjects; scores can overestimate realistic retrieval quality.",
        "Results apply only to this small controlled benchmark. A four-component bottleneck discards information; worse VQC scores must be reported. No production vectors or search behavior were replaced.",
        f"Training took {training_seconds:.3f} seconds; loss {model['loss_trace'][0]:.6f} -> {min(model['loss_trace']):.6f}. Per-query rankings, labels, training split, runtimes and trace are retained in vqc_embeddings.json; fitted arrays are in vqc_model.npz.",
        "", "Reference: https://arxiv.org/abs/2001.03622"]
    (out/"VQC_EMBEDDINGS_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":main()
