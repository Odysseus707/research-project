import pytest
import pandas as pd
import networkx as nx
from src.alg.random_select import random_select_fast
from src.environment_tools import get_modalities_at_timestamp, random_env
from src.alg.random_select import random_algorithm
from src.system import Env, Node, Request


@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")


def test_random_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    output = random_algorithm(env, seed=42)
    assert isinstance(output, dict)
    for req_idx, res in output.items():
        request = next(req for req in env.requests if req.idx == req_idx)
        assert "selected_nodes" in res
        assert isinstance(res["selected_nodes"], list)
        assert "modality_assignment" in res
        assert isinstance(res["modality_assignment"], dict)

        assigned_modalities = set(res["modality_assignment"].keys())
        assert assigned_modalities.issubset(request.needed_modalities)

        for modality, node_idx in res["modality_assignment"].items():
            assert node_idx in res["selected_nodes"]
            node = next(node for node in env.nodes if node.idx == node_idx)
            assert modality in get_modalities_at_timestamp(node, request.timestamp)


def test_random_select_fast_retries_until_timestamp_match():
    node_1 = Node(
        idx=1,
        data=pd.DataFrame(
            {
                "date": [1, 2],
                "temp_max": [10.0, float("nan")],
                "temp_min": [float("nan"), float("nan")],
                "wind": [float("nan"), 3.0],
                "precipitation": [float("nan"), float("nan")],
            }
        ),
    )
    node_2 = Node(
        idx=2,
        data=pd.DataFrame(
            {
                "date": [1, 2],
                "temp_max": [float("nan"), float("nan")],
                "temp_min": [1.0, 2.0],
                "wind": [float("nan"), float("nan")],
                "precipitation": [0.4, float("nan")],
            }
        ),
    )
    topo = nx.Graph()
    topo.add_node(0, type="orchestrator")
    topo.add_node(1, type="worker")
    topo.add_node(2, type="worker")
    topo.add_edges_from([(0, 1), (0, 2)])

    env = Env(
        nodes=[node_1, node_2],
        topo=topo,
        timestamps=[1, 2],
        modalities=["temp_max", "temp_min", "wind", "precipitation"],
        requests=[
            Request(
                idx=0,
                node_idx=1,
                timestamp=2,
                included_modalities={"wind"},
                calculation_type="weather",
            )
        ],
    )

    output = random_select_fast(env, seed=7)
    request_output = output[0]

    assert request_output["modality_assignment"] == {
        "temp_min": 2,
    }
    assert set(request_output["selected_nodes"]) == {2}
    assert "temp_max" not in get_modalities_at_timestamp(node_1, timestamp=2)
    assert "temp_min" in get_modalities_at_timestamp(node_2, timestamp=2)
