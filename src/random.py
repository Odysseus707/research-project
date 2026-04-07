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
        case Generator():
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
    time_alpha: float,
    modality_alpha: float,
    seed: Generator | int | None = None,
) -> dict[int, pd.DataFrame]:
    rng = create_rng(seed)
    modalities = [col for col in dataset.columns if col not in ("date", "weather")]
    num_modalities = len(modalities)
    partitions = {client: pd.DataFrame(dataset["date"]) for client in range(num_nodes)}
    for client in partitions:
        for m in modalities:
            partitions[client][m] = pd.Series(dtype=float)

    client_alpha = rng.dirichlet([100000.0] * num_nodes)
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
    num_nodes: int,
    graph: nx.Graph,
    seed: Generator | int | None = None,
) -> Env:
    rng = create_rng(seed)
    tree = create_tree(graph)

    nodes = []
    for node_idx, node_data in tree.nodes(data=True):
        if node_data["type"] != "worker":
            continue

        node_modalities = ...
        node_timestamps = ...
        node_dataset = partition_data(dataset, ...)
        nodes.append(Node(idx=node_idx, data=node_dataset))

    # orchestrator = ...
    timestamps = ...  # TODO: Get these from the dataframe itself
    modalities = ...  # TODO: Get these from the dataframe itself or via arg

    return Env(
        nodes=nodes,
        # orchestator=orchestrator,
        topo=tree,
        timestamps=timestamps,
        modalities=modalities,
    )
