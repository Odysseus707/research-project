import pytest
import pandas as pd
import networkx as nx
import time
from src.environment_tools import random_env, generate_request
from src.alg.proposed import proposed_algorithm


@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")


def test_proposed_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    start = time.perf_counter()
    alg_output = proposed_algorithm(env, env.requests)
    elapsed = time.perf_counter() - start
    results = {}
    for request in env.requests:
        out = alg_output.get(request.idx, {})
        selected = out.get("selected", {})
        selected_nodes = out.get("selected_nodes", [])
        total_cost = 0
        for (node_idx, modality), selected_flag in selected.items():
            if selected_flag:
                hops = getattr(env, "shortest_paths", None)
                if hops is not None:
                    hops = env.shortest_paths.get(node_idx, 1)
                else:
                    hops = 1
                weight = getattr(env, "modalities_data_size", None)
                if weight is not None:
                    weight = env.modalities_data_size.get(modality, 1.0)
                else:
                    weight = 1.0
                total_cost += hops * weight
        results[request.idx] = {
            "time_taken": elapsed,
            "cost": total_cost,
            "selected_nodes": selected_nodes,
        }
    assert isinstance(results, dict)
    for req_idx, res in results.items():
        assert "time_taken" in res and "cost" in res and "selected_nodes" in res
    print(results)
