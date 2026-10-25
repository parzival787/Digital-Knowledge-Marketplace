# VQC embedding benchmark

Measured local statevector simulation on an authored corpus; no quantum advantage claim.

| Split | Original MiniLM | PCA4 + expansion | Untrained VQC + expansion | Trained VQC + expansion |
| --- | --- | --- | --- | --- |
| validation | 0.915266 | 0.654188 | 0.534822 | 0.611822 |
| test | 0.905296 | 0.702724 | 0.605030 | 0.609317 |

## Method and limits

Training fits PCA4 and scaling on 64 training documents. Angle encoding uses arctan-scaled PCA features; two layers of RY/RZ and ring CNOT gates yield four Z and four adjacent ZZ expectations. Adam optimizes training-document cosine Gram alignment for 40 epochs. Ridge expansion restores 384 dimensions.
Original 384D embeddings, PCA4/ridge and untrained-circuit/ridge baselines use identical documents, queries and labels. Expansion is trained on document vectors only. Validation/test topics are disjoint query sets; no test query, relevance label or test metric enters training or parameter selection.
All 96 documents form the retrieval corpus; 32 document variants are excluded from model fitting. Query topics also occur in training documents, so this is in-domain retrieval, not unseen-topic generalization. Labels are authored topic/domain rules (3/1/0), not independent human judgments. Query wording overlaps document subjects; scores can overestimate realistic retrieval quality.
Results apply only to this small controlled benchmark. A four-component bottleneck discards information; worse VQC scores must be reported. No production vectors or search behavior were replaced.
Training took 1.027 seconds; loss 0.485185 -> 0.098681. Per-query rankings, labels, training split, runtimes and trace are retained in vqc_embeddings.json; fitted arrays are in vqc_model.npz.

Reference: https://arxiv.org/abs/2001.03622
