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
    alg_output = proposed_algorithm(env)
    assert isinstance(alg_output, dict)
    for req_idx, res in alg_output.items():
        assert "selected_nodes" in res
        assert isinstance(res["selected_nodes"], list)
    print(alg_output)
