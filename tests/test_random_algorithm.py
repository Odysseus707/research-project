import pytest
import pandas as pd
import networkx as nx
import time
from src.environment_tools import random_env
from src.alg.random_select import random_algorithm


@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")


def test_random_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    start = time.perf_counter()
    output = random_algorithm(env, env.requests, seed=42)
    elapsed = time.perf_counter() - start
    results = {}
    for request in env.requests:
        res = output[request.idx]
        assert "selected_nodes" in res and "cost" in res
        assert isinstance(res["selected_nodes"], list)
        assert isinstance(res["cost"], float)
        results[request.idx] = {
            "time_taken": elapsed,
            "cost": res["cost"],
            "selected_nodes": res["selected_nodes"],
        }
    print(results)
