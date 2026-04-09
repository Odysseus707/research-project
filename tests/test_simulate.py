import unittest
import networkx as nx
import pandas as pd
from src.environment_tools import simulate
from src.alg.proposed import proposed_algorithm
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp
from src.environment_tools import random_env

class TestSimulate(unittest.TestCase):
    def setUp(self):
        df = pd.read_csv("seattle-weather.csv")
        G = nx.star_graph(10)
        self.env = random_env(df, G, alpha=1e5, seed=42)


    def _check_simulate_output(self, results):
        self.assertIsInstance(results, dict)
        self.assertIn("results", results)
        self.assertIn("time_taken", results)
        self.assertIn("fairness_index", results)
        self.assertIn("successful_calculation_overall", results)
        self.assertIn("failed_calculations", results)
        self.assertIn("failed_calculation_count", results)
        for req_idx, res in results["results"].items():
            request = next(req for req in self.env.requests if req.idx == req_idx)
            self.assertIn("selected_nodes", res)
            self.assertIsInstance(res["selected_nodes"], list)
            self.assertIn("modality_assignment", res)
            self.assertIsInstance(res["modality_assignment"], dict)
            self.assertIn("cost", res)
            self.assertIsInstance(res["cost"], (int, float))
            self.assertIn("successful_calculation", res)
            self.assertIsInstance(res["successful_calculation"], bool)
            self.assertIn("missing_modalities", res)
            self.assertIsInstance(res["missing_modalities"], list)

            expected_cost = 0.0
            for modality in request.needed_modalities:
                node_idx = res["modality_assignment"].get(modality)
                if node_idx is None:
                    continue
                hops = self.env.shortest_paths.get(node_idx, 1)
                weight = self.env.modalities_data_size.get(modality, 1.0)
                expected_cost += hops * weight
            self.assertEqual(res["cost"], expected_cost)

    def test_simulate_proposed(self):
        results = simulate(self.env, proposed_algorithm)
        print("\n[Simulate Output - Proposed Algorithm]\n", results)
        self._check_simulate_output(results)

    def test_simulate_random(self):
        results = simulate(self.env, random_algorithm)
        print("\n[Simulate Output - Random Algorithm]\n", results)
        self._check_simulate_output(results)

    def test_simulate_ilp(self):
        results = simulate(self.env, solve_ilp)
        print("\n[Simulate Output - ILP Algorithm]\n", results)
        self._check_simulate_output(results)

if __name__ == "__main__":
    unittest.main()
