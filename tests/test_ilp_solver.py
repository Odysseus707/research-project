import pytest
import pandas as pd
import networkx as nx
from src.environment_tools import get_modalities_at_timestamp, random_env
from src.alg.ilp_solver import solve_ilp

@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")

def test_ilp_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    output = solve_ilp(env)
    assert isinstance(output, dict)
    for req_idx, res in output.items():
        request = next(req for req in env.requests if req.idx == req_idx)
        assert "selected_nodes" in res
        assert isinstance(res["selected_nodes"], list)
        assert "modality_assignment" in res
        assert isinstance(res["modality_assignment"], dict)
        assert set(res["modality_assignment"].keys()) == set(request.needed_modalities)

        for modality, node_idx in res["modality_assignment"].items():
            assert node_idx in res["selected_nodes"]
            node = next(node for node in env.nodes if node.idx == node_idx)
            assert modality in get_modalities_at_timestamp(node, request.timestamp)
