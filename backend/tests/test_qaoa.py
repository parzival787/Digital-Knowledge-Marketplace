import unittest
import numpy as np
from research.qaoa_pricing import circuit_for, demand_revenue, optimize_prices


class QAOATests(unittest.TestCase):
    def test_zero_angles_uniform_and_one_qubit_known_optimum(self):
        circuit=circuit_for([0,1])
        np.testing.assert_allclose(circuit(np.zeros((1,2))),[0.5,0.5],atol=1e-10)
        # For Hc=diag(0,1), gamma=pi/2, beta=-pi/4 maps |+> to |0>.
        np.testing.assert_allclose(circuit(np.array([[np.pi/2,-np.pi/4]])),[1,0],atol=1e-10)

    def test_seeded_results_normalize_and_respect_feasible_grid(self):
        a=optimize_prices([1,4,2],seed=9,depth=1,evaluations=30,shots=500)
        b=optimize_prices([1,4,2],seed=9,depth=1,evaluations=30,shots=500)
        self.assertEqual(a,b)
        self.assertAlmostEqual(sum(a["probabilities"]),1)
        self.assertEqual(sum(a["counts"]),500)
        self.assertIn(a["price_index"],(0,1,2,None))
        self.assertLessEqual(a["selected_revenue"],a["optimal_revenue"])

    def test_invalid_inputs_and_fee_application(self):
        gross=demand_revenue([10],30,5,100,0)
        net=demand_revenue([10],30,5,100,500)
        np.testing.assert_allclose(net,gross*.95)
        for costs in ([1,2,3],[1,float('nan')]):
            with self.assertRaises(ValueError): circuit_for(costs)
        with self.assertRaises(ValueError): optimize_prices([0,0])
        with self.assertRaises(ValueError): demand_revenue([0],30,5,100)
