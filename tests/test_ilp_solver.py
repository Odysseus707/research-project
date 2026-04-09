import pytest
import pandas as pd
import networkx as nx
import time
from src.environment_tools import random_env, generate_request
from src.alg.ilp_solver import solve_ilp

@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")

def test_ilp_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    start = time.perf_counter()
    results = {}
    for request in env.requests:
        # For each request, create a temp env with only needed modalities
        temp_env = env
        temp_env.modalities = list(request.needed_modalities)
        out = solve_ilp(temp_env)
        selected_nodes = out.get("selected_nodes", [])
        cost = out.get("cost", 0)
        results[request.idx] = {
            "time_taken": time.perf_counter() - start,
            "cost": cost,
            "selected_nodes": selected_nodes,
        }
    assert isinstance(results, dict)
    for req_idx, res in results.items():
        assert "time_taken" in res and "cost" in res and "selected_nodes" in res
    print(results)
