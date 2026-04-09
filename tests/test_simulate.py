import unittest
import networkx as nx
import pandas as pd
from src.system import Env, Node, Request
from src.environment_tools import simulate
from src.alg.proposed import proposed_algorithm
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp

class TestSimulate(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        import networkx as nx
        from src.environment_tools import random_env
        # Load the real seattle-weather.csv dataset
        df = pd.read_csv("seattle-weather.csv")
        # Use a simple graph for the test
        G = nx.path_graph(3)
        self.env = random_env(df, G, alpha=1e5, seed=42)


    def _check_simulate_output(self, results):
        self.assertIsInstance(results, dict)
        self.assertIn("results", results)
        self.assertIn("time_taken", results)
        self.assertIn("fairness_index", results)
        for req_idx, res in results["results"].items():
            self.assertIn("selected_nodes", res)
            self.assertIn("cost", res)

    def test_simulate_proposed(self):
        results = simulate(self.env, proposed_algorithm)
        print("\n[Simulate Output - Proposed Algorithm]\n", results)
        self._check_simulate_output(results)

    def test_simulate_random(self):
        results = simulate(self.env, random_algorithm)
        print("\n[Simulate Output - Random Algorithm]\n", results)
        self._check_simulate_output(results)

    def test_simulate_ilp(self):
        # Wrap solve_ilp to match the interface (env, requests)
        def ilp_wrapper(env, requests):
            # For each request, run solve_ilp on a temp env with only needed modalities
            out = {}
            for req in requests:
                # Create a shallow copy of env with only needed modalities for this request
                temp_env = env
                temp_env.modalities = list(req.needed_modalities)
                out[req.idx] = solve_ilp(temp_env)
            return out
        results = simulate(self.env, ilp_wrapper)
        print("\n[Simulate Output - ILP Algorithm]\n", results)
        self._check_simulate_output(results)

if __name__ == "__main__":
    unittest.main()
