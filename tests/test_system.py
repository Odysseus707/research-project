import pytest
import pandas as pd
import networkx as nx

from src.system import Env
from src.environment_tools import random_env


@pytest.fixture
def dataset() -> pd.DataFrame:
    return pd.read_csv("seattle-weather.csv")


def test_random_env(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    assert isinstance(env, Env)
    print(env)
