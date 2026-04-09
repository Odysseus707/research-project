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
    output = random_algorithm(env, seed=42)
    assert isinstance(output, dict)
    for req_idx, res in output.items():
        assert "selected_nodes" in res
        assert isinstance(res["selected_nodes"], list)
    print(output)
