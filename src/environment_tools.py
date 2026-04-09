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
            client_idx = client_dir.argmax()
            partitions[client_idx].loc[i, m] = getattr(row, m)

    # Generate and apply a mask per partition
    for client in partitions:
        mask = generate_modality_mask(len(modalities), rng)
        for m_idx, m in enumerate(modalities):
            if mask[m_idx] == 0:
                partitions[client][m] = np.nan

    return partitions


def create_tree(g: nx.Graph, orchestrator_idx: int | None = None):
    if orchestrator_idx is None:
        orchestrator_idx = 0

    tree = nx.bfs_tree(g, source=orchestrator_idx)

    for node, node_data in tree.nodes(data=True):
        if node == orchestrator_idx:
            node_data["type"] = "orchestrator"
        elif nx.degree(g, node) > 1:
            node_data["type"] = "forwarder"
        else:
            node_data["type"] = "worker"

    return tree


def generate_request(env: Env, num_requests_per_node: int = 2):
    requests = []
    idx = 0
    rng = create_rng()
    for node in env.nodes:
        node_df = node.data
        available_timestamps = node_df["date"].dropna().unique()
        for _ in range(num_requests_per_node):
            if len(available_timestamps) == 0:
                continue
            timestamp = rng.choice(available_timestamps)
            # Get modalities present (non-NaN) at this timestamp for this node
            row = node_df[node_df["date"] == timestamp]
            present_modalities = (
                [
                    m
                    for m in env.modalities
                    if m in row.columns and not pd.isna(row.iloc[0][m])
                ]
                if not row.empty
                else []
            )
            # Randomly select a subset of present modalities to include
            num_modalities = rng.integers(0, len(present_modalities) + 1)
            if num_modalities > 0 and present_modalities:
                included_modalities = set(
                    rng.choice(present_modalities, size=num_modalities, replace=False)
                )
            else:
                included_modalities = set()
            req = Request(
                node_idx=node.idx,
                idx=idx,
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


def simulate(env: Env, algorithm):
    results = {}
    start_time = time.time()
    alg_output = algorithm(env, env.requests)
    elapsed_time = time.time() - start_time
    node_selection_counts = {node.idx: 0 for node in env.nodes}
    for request in env.requests:
        output = alg_output.get(request.idx, {})
        selected_nodes = output.get("selected_nodes", [])
        cost_val = output.get("cost")
        for node_idx in selected_nodes:
            if node_idx in node_selection_counts:
                node_selection_counts[node_idx] += 1
        results[request.idx] = {
            "selected_nodes": selected_nodes,
            "cost": cost_val if cost_val is not None else 0,
        }
    # Compute Jain's Fairness Index
    selection_array = np.array(list(node_selection_counts.values()))
    numerator = selection_array.sum() ** 2
    denominator = len(selection_array) * (selection_array**2).sum()
    fairness_index = 1.0 if denominator == 0 else numerator / denominator
    return {
        "results": results,
        "time_taken": elapsed_time,
        "fairness_index": fairness_index,
    }
