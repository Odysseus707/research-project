import unittest
import networkx as nx
import pandas as pd
from src.system import Env, Node, Request
from src.environment_tools import simulate
from src.alg.proposed import proposed_algorithm
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp
import pandas as pd
import networkx as nx
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
        self.assertIn("qos_overall", results)
        for req_idx, res in results["results"].items():
            self.assertIn("selected_nodes", res)
            self.assertIsInstance(res["selected_nodes"], list)
            self.assertIn("cost", res)
            self.assertIsInstance(res["cost"], (int, float))
            self.assertIn("qos", res)
            self.assertIsInstance(res["qos"], bool)

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
