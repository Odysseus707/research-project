import pytest
import pandas as pd
import networkx as nx
from src.environment_tools import random_env, generate_request


def test_generate_request_basic():
    dataset = pd.read_csv("seattle-weather.csv")
    tree = nx.star_graph(5)
    env = random_env(dataset, tree, seed=123)
    requests = generate_request(env, num_requests_per_node=3)
    # Check that requests are generated
    assert isinstance(requests, list)
    assert len(requests) == len(env.nodes) * 3
    # Check that each request has a valid node_idx and timestamp
    node_idxs = {node.idx for node in env.nodes}
    for req in requests:
        assert req.node_idx in node_idxs
        assert req.timestamp in env.timestamps
        assert isinstance(req.included_modalities, set)
        assert req.idx >= 0
    print("Sample requests:", requests[:2])
