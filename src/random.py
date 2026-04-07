from __future__ import annotations

import typing as t

import networkx as nx
import numpy as np
import pandas as pd

from .system import Env, Node

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

    return Env(
        nodes=workers,
        # orchestator=orchestrator,
        topo=tree,
        timestamps=timestamps,
        modalities=modalities,
    )
