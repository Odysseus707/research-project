import pytest
import pandas as pd
import networkx as nx
from src.environment_tools import get_modalities_at_timestamp, random_env
from src.alg.proposed import proposed_algorithm, proposed_algorithm_fast
from src.system import Env, Node, Request


@pytest.fixture
def dataset():
    return pd.read_csv("seattle-weather.csv")


def test_proposed_algorithm(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)
    alg_output = proposed_algorithm(env)
    assert isinstance(alg_output, dict)
    for req_idx, res in alg_output.items():
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


def test_proposed_algorithm_fast_matches_proposed(dataset):
    tree = nx.star_graph(10)
    env = random_env(dataset, tree, seed=42)

    original_output = proposed_algorithm(env)
    fast_output = proposed_algorithm_fast(env)

    assert fast_output == original_output


def test_proposed_algorithm_returns_timestamp_feasible_assignments():
    node_1 = Node(
        idx=1,
        data=pd.DataFrame(
            {
                "date": [1],
                "temp_max": [10.0],
                "temp_min": [5.0],
                "wind": [float("nan")],
                "precipitation": [float("nan")],
            }
        ),
    )
    node_2 = Node(
        idx=2,
        data=pd.DataFrame(
            {
                "date": [1],
                "temp_max": [9.0],
                "temp_min": [float("nan")],
                "wind": [float("nan")],
                "precipitation": [float("nan")],
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
        timestamps=[1],
        modalities=["temp_max", "temp_min", "wind", "precipitation"],
        requests=[
            Request(
                idx=0,
                node_idx=2,
                timestamp=1,
                included_modalities=set(),
                calculation_type="temperature",
            )
        ],
    )

    output = proposed_algorithm(env)[0]
    for modality, node_idx in output["modality_assignment"].items():
        node = next(node for node in env.nodes if node.idx == node_idx)
        assert modality in get_modalities_at_timestamp(node, timestamp=1)
