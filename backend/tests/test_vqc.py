import unittest
import numpy as np
from research.vqc_embeddings import ndcg,train,transform,quantum_features


class VQCTests(unittest.TestCase):
    def test_ndcg_perfect_zero_and_reverse(self):
        self.assertEqual(ndcg([3,1,0],[3,1,0]),1)
        self.assertEqual(ndcg([0,0],[1,2]),0)
        self.assertLess(ndcg([3,1,0],[0,1,3]),1)
        with self.assertRaises(ValueError):ndcg([1],[float('nan')])

    def test_circuit_expectations_and_training_dimensions(self):
        values=np.stack(quantum_features()(np.zeros((2,4)),np.zeros((2,4,2))),axis=1)
        np.testing.assert_allclose(values,np.ones((2,8)),atol=1e-9)
        rng=np.random.default_rng(13);training=rng.normal(size=(10,384));heldout=rng.normal(size=(3,384))
        original=training.copy();model=train(training,epochs=2)
        np.testing.assert_array_equal(training,original)
        self.assertLessEqual(min(model["loss_trace"]),model["loss_trace"][0])
        for mode in ("trained","untrained","classical"):
            output=transform(heldout,model,mode)
            self.assertEqual(output.shape,(3,384))
            np.testing.assert_allclose(np.linalg.norm(output,axis=1),1,atol=1e-8)
        with self.assertRaises(ValueError):train(np.ones((8,383)))
