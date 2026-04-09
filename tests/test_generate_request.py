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
    node_map = {node.idx: node for node in env.nodes}
    for req in requests:
        # Node index must be valid
        assert req.node_idx in node_map
        node = node_map[req.node_idx]
        # Included modalities must match those present in node's data at that timestamp
        node_df = node.data
        row = node_df[node_df["date"] == req.timestamp]
        if not row.empty:
            present_modalities = set(row[node.modalities].dropna(axis=1, how='all').columns)
        else:
            present_modalities = set()
        assert req.included_modalities == present_modalities
        assert isinstance(req.included_modalities, set)
        assert req.idx >= 0
    print("Sample requests:", requests[:6])
