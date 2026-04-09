import pytest
import pandas as pd
import networkx as nx

from src.system import Env
from src.environment_tools import random_env, create_tree


@pytest.fixture
def dataset() -> pd.DataFrame:
    return pd.read_csv("seattle-weather.csv")


def test_random_env(dataset):
    graph = nx.erdos_renyi_graph(10, 0.3, seed=42)
    tree = create_tree(graph)
    env = random_env(dataset, tree, seed=42)
    assert isinstance(env, Env)
    print(env)
