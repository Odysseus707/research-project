from __future__ import annotations

import typing as t

import networkx as nx
import numpy as np
import pandas as pd
import time

from .system import Env, Node, Request
from src.alg.proposed import cost

if t.TYPE_CHECKING:
    from numpy.random import Generator


def create_rng(seed: Generator | int | None = None) -> Generator:
    match seed:
        case np.random.Generator():
            return seed
        case int():
            return np.random.default_rng(seed)
        case None:
            return np.random.default_rng()
        case _:
            raise ValueError("Illegal value for argument `seed`.")


def generate_modality_mask(num_modalities, rng, decay_probs=[1.0, 0.5, 0.1, 0.01]):
    mask = np.zeros(num_modalities, dtype=int)
    remaining = set(range(num_modalities))
    for p in decay_probs:
        if not remaining:
            break
        idx = rng.choice(list(remaining))
        if rng.random() < p:
            mask[idx] = 1
            remaining.remove(idx)
    return mask


def partition_dataset(
    dataset: pd.DataFrame,
    num_nodes: int,
    alpha: float = 1e5,
    # time_alpha: float,
    # modality_alpha: float,
    seed: Generator | int | None = None,
) -> dict[int, pd.DataFrame]:
    rng = create_rng(seed)
    modalities = [col for col in dataset.columns if col not in ("date", "weather")]
    partitions = {client: pd.DataFrame(dataset["date"]) for client in range(num_nodes)}

    for client in partitions:
        for m in modalities:
            partitions[client][m] = pd.Series(dtype=float)

    client_alpha = rng.dirichlet([alpha] * num_nodes)
    for i, row in enumerate(dataset.itertuples()):
        for m in modalities:
            client_dir = rng.dirichlet(client_alpha)
            client_idx = np.argmax(client_dir)
            partitions[client_idx].loc[i, m] = getattr(row, m)

    # Generate and apply a mask per partition
    for client in partitions:
        mask = generate_modality_mask(len(modalities), rng)
        for m_idx, m in enumerate(modalities):
            if mask[m_idx] == 0:
                partitions[client][m] = np.nan

    return partitions


def generate_graph(num_nodes: int, topology_type: str, seed: int = None):
    if topology_type == "star":
        return nx.star_graph(num_nodes)
    elif topology_type == "barabasi_albert":
        # m must be >= 1 and < num_nodes
        m = min(2, max(1, num_nodes // 10))
        return nx.barabasi_albert_graph(num_nodes, m, seed=seed)
    elif topology_type == "erdos_renyi":
        # p chosen so graph is likely connected but not complete
        p = min(0.1 + 10 / num_nodes, 0.5)
        return nx.erdos_renyi_graph(num_nodes, p, seed=seed)
    elif topology_type == "m_ary_tree":
        # m chosen so tree is not too shallow or deep
        m = min(3, max(2, num_nodes // 20))
        h = int(np.log(num_nodes) / np.log(m + 1))
        return nx.balanced_tree(m, h)
    elif topology_type == "dorogovtsev_goltsev_mendes":
        # This graph requires n >= 3
        n = max(num_nodes, 3)
        return nx.dorogovtsev_goltsev_mendes_graph(n)
    elif topology_type == "complete":
        return nx.complete_graph(num_nodes)
    elif topology_type == "balanced_tree":
        # r and h chosen to get close to num_nodes
        r = min(3, max(2, num_nodes // 20))
        h = int(np.log(num_nodes) / np.log(r + 1))
        return nx.balanced_tree(r, h)
    else:
        raise ValueError(f"Unknown topology_type: {topology_type}")


def create_tree(g: nx.Graph, orchestrator_idx: int | None = None):
    if orchestrator_idx is None:
        orchestrator_idx = 0

    tree = nx.bfs_tree(g, source=orchestrator_idx)

    for node in tree.nodes():
        if node == orchestrator_idx:
            tree.nodes[node]["type"] = "orchestrator"
        elif tree.out_degree(node) == 0:
            tree.nodes[node]["type"] = "worker"
        else:
            tree.nodes[node]["type"] = "forwarder"

    return tree


def generate_request(env: Env, num_requests_per_node: int = 2):
    requests = []
    idx = 0
    rng = create_rng()
    for node in env.nodes:
        available_timestamps = (
            node.timestamps
        )  # Use property: only timestamps with at least one modality present
        for _ in range(num_requests_per_node):
            if len(available_timestamps) == 0:
                continue
            timestamp = rng.choice(available_timestamps)
            # Get modalities present (non-NaN) at this timestamp for this node
            node_df = node.data
            row = node_df[node_df["date"] == timestamp]
            if not row.empty:
                present_modalities = set(
                    row[node.modalities].dropna(axis=1, how="all").columns
                )
            else:
                present_modalities = set()
            included_modalities = present_modalities
            req = Request(
                idx=idx,
                node_idx=node.idx,
                timestamp=timestamp,
                included_modalities=included_modalities,
                calculation_type="weather",
            )
            requests.append(req)
            idx += 1
    return requests


def random_env(
    dataset: pd.DataFrame,
    graph: nx.Graph,
    alpha: float = 1e5,
    seed: Generator | int | None = None,
) -> Env:
    rng = create_rng(seed)
    tree = create_tree(graph)

    worker_node_ids = filter(
        lambda node: tree.nodes[node]["type"] == "worker",
        tree.nodes(),
    )
    worker_node_ids = list(worker_node_ids)

    num_workers = len(worker_node_ids)
    if num_workers < 2:
        raise ValueError(
            f"random_env: At least 2 worker nodes are required, but got {num_workers}. Check your graph topology and node labeling."
        )

    node_partitioned_data = partition_dataset(
        dataset, num_nodes=num_workers, alpha=alpha
    )

    worker_id_to_dataset_id = {
        worker_id: dataset_id
        for (dataset_id, worker_id) in zip(
            node_partitioned_data.keys(), worker_node_ids
        )
    }

    workers: list[Node] = []
    for worker_id in worker_node_ids:
        dataset_id = worker_id_to_dataset_id[worker_id]
        worker_data = node_partitioned_data[dataset_id]
        workers.append(
            Node(
                idx=worker_id,
                data=worker_data,
            )
        )

    sample_data = next(iter(node_partitioned_data.values()))
    timestamps = sample_data.date.tolist()
    modalities = sample_data.columns.tolist()
    for non_modality in ("date", "weather"):
        try:
            modalities.remove(non_modality)
        except ValueError:
            pass

    # Generate requests for the environment
    env = Env(
        nodes=workers,
        topo=tree,
        timestamps=timestamps,
        modalities=modalities,
    )
    env.requests = generate_request(env)
    return env


def compute_cost(env: Env, selected_nodes: list[int], request: Request) -> float:
    total_cost = 0.0
    for node_idx in selected_nodes:
        hops = env.shortest_paths.get(node_idx, 1)
        for m in request.needed_modalities:
            w = env.modalities_data_size.get(m, 1.0)
            total_cost += hops * w
    return total_cost


def compute_fairness(env: Env, all_selected_nodes: list[list[int]]) -> float:
    node_selection_counts = {node.idx: 0 for node in env.nodes}
    for selected in all_selected_nodes:
        for node_idx in selected:
            if node_idx in node_selection_counts:
                node_selection_counts[node_idx] += 1
    selection_array = np.array(list(node_selection_counts.values()))
    numerator = selection_array.sum() ** 2
    denominator = len(selection_array) * (selection_array**2).sum()
    return 1.0 if denominator == 0 else numerator / denominator


def compute_qos(env: Env, request: Request, selected_nodes: list[int]) -> bool:
    # Start with included modalities
    present_modalities = set(request.included_modalities)
    for node in env.nodes:
        if node.idx in selected_nodes:
            node_df = node.data
            row = node_df[node_df["date"] == request.timestamp]
            if not row.empty:
                present_modalities |= set(
                    row[node.modalities].dropna(axis=1, how="all").columns
                )
    needed = request.needed_modalities
    missing = needed - present_modalities
    return len(missing) == 0


def simulate(env: Env, algorithm):
    results = {}
    start_time = time.time()
    alg_output = algorithm(env)
    elapsed_time = time.time() - start_time
    qos_list = []
    # Extract all selected_nodes directly from alg_output for fairness computation
    all_selected_nodes = [
        output.get("selected_nodes", []) for output in alg_output.values()
    ]
    for request in env.requests:
        output = alg_output.get(request.idx, {})
        selected_nodes = output.get("selected_nodes", [])
        cost_val = compute_cost(env, selected_nodes, request)
        qos = compute_qos(env, request, selected_nodes)
        qos_list.append(qos)
        results[request.idx] = {
            "selected_nodes": selected_nodes,
            "cost": cost_val,
            "qos": qos,
        }
    fairness_index = compute_fairness(env, all_selected_nodes)
    return {
        "results": results,
        "time_taken": elapsed_time,
        "fairness_index": fairness_index,
        "qos_overall": sum(qos_list) / len(qos_list) if qos_list else 0.0,
    }
