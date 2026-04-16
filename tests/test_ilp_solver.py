import pytest
import pandas as pd
import networkx as nx
from src.environment_tools import compute_cost, get_modalities_at_timestamp, random_env
from src.alg.ilp_solver import ExactCoverColumn, _build_exact_cover_columns, solve_ilp
from src.alg.proposed import proposed_algorithm
from src.system import Env, Node, Request

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


def _build_activation_coupling_env(activation_cost: float) -> Env:
    node_shared = Node(
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
    node_max = Node(
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
    node_min = Node(
        idx=3,
        data=pd.DataFrame(
            {
                "date": [1],
                "temp_max": [float("nan")],
                "temp_min": [4.0],
                "wind": [float("nan")],
                "precipitation": [float("nan")],
            }
        ),
    )
    topo = nx.Graph()
    topo.add_node(0, type="orchestrator")
    topo.add_node(10, type="forwarder")
    topo.add_node(1, type="worker")
    topo.add_node(2, type="worker")
    topo.add_node(3, type="worker")
    topo.add_edges_from([(0, 10), (10, 1), (0, 2), (0, 3)])

    return Env(
        nodes=[node_shared, node_max, node_min],
        topo=topo,
        timestamps=[1],
        modalities=["temp_max", "temp_min", "wind", "precipitation"],
        node_activation_costs={1: activation_cost, 2: activation_cost, 3: activation_cost},
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


def test_ilp_with_zero_activation_cost_matches_legacy_optimum():
    env = _build_activation_coupling_env(activation_cost=0.0)

    output = solve_ilp(env)[0]

    assert output["modality_assignment"] == {"temp_max": 2, "temp_min": 3}
    assert set(output["selected_nodes"]) == {2, 3}


def test_ilp_prefers_fewer_nodes_when_activation_cost_is_positive():
    env = _build_activation_coupling_env(activation_cost=3.0)

    output = solve_ilp(env)[0]

    assert output["modality_assignment"] == {"temp_max": 1, "temp_min": 1}
    assert output["selected_nodes"] == [1]
    assert compute_cost(
        env,
        env.requests[0],
        modality_assignment=output["modality_assignment"],
        selected_nodes=output["selected_nodes"],
    ) == 7.0


def _build_exact_cover_counterexample_env() -> Env:
    node_pair = Node(
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
    node_all = Node(
        idx=3,
        data=pd.DataFrame(
            {
                "date": [1],
                "temp_max": [8.0],
                "temp_min": [4.0],
                "wind": [3.0],
                "precipitation": [float("nan")],
            }
        ),
    )
    topo = nx.Graph()
    topo.add_node(0, type="orchestrator")
    topo.add_node(1, type="worker")
    topo.add_node(10, type="forwarder")
    topo.add_node(3, type="worker")
    topo.add_edges_from([(0, 1), (0, 10), (10, 3)])

    return Env(
        nodes=[node_pair, node_all],
        topo=topo,
        timestamps=[1],
        modalities=["temp_max", "temp_min", "wind", "precipitation"],
        node_activation_costs={1: 3.0, 3: 3.0},
        requests=[
            Request(
                idx=0,
                node_idx=1,
                timestamp=1,
                included_modalities={"precipitation"},
                calculation_type="weather",
            )
        ],
    )


def test_exact_cover_columns_are_nonempty_and_timestamp_feasible():
    env = _build_exact_cover_counterexample_env()

    columns = _build_exact_cover_columns(env, env.requests[0])

    assert columns
    assert all(isinstance(column, ExactCoverColumn) for column in columns)
    assert all(column.modalities for column in columns)
    node_map = {node.idx: node for node in env.nodes}
    for column in columns:
        timestamp_modalities = get_modalities_at_timestamp(
            node_map[column.node_idx], env.requests[0].timestamp
        )
        assert set(column.modalities) <= timestamp_modalities


def test_exact_cover_reconstructs_assignment_and_nodes():
    env = _build_exact_cover_counterexample_env()

    output = solve_ilp(env)[0]

    assert set(output["modality_assignment"]) == set(env.requests[0].needed_modalities)
    assert output["selected_nodes"] == sorted(
        set(output["modality_assignment"].values())
    )


def test_ilp_exact_cover_can_beat_proposed_greedy():
    env = _build_exact_cover_counterexample_env()

    ilp_output = solve_ilp(env)[0]
    proposed_output = proposed_algorithm(env)[0]

    ilp_cost = compute_cost(
        env,
        env.requests[0],
        modality_assignment=ilp_output["modality_assignment"],
        selected_nodes=ilp_output["selected_nodes"],
    )
    proposed_cost = compute_cost(
        env,
        env.requests[0],
        modality_assignment=proposed_output["modality_assignment"],
        selected_nodes=proposed_output["selected_nodes"],
    )

    assert ilp_output["modality_assignment"] == {
        "temp_max": 3,
        "temp_min": 3,
        "wind": 3,
    }
    assert proposed_output["modality_assignment"] == {
        "temp_max": 1,
        "temp_min": 1,
        "wind": 3,
    }
    assert ilp_cost == 9.0
    assert proposed_cost == 10.0
    assert ilp_cost < proposed_cost
