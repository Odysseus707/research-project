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


def partition_dataset(
    dataset: pd.DataFrame,
    num_nodes: int,
    time_alpha: float,
    modality_alpha: float,
    seed: Generator | int | None = None,
) -> dict[int, pd.DataFrame]:
    rng = create_rng(seed)

    partitions = {}

    return partitions


def random_env(
    dataset: pd.DataFrame,
    num_nodes: int,
    topo: nx.Graph,
    seed: Generator | int | None = None,
) -> Env:
    rng = create_rng(seed)

    nodes = []
    for idx in range(num_nodes):
        node_modalities = ...
        node_timestamps = ...
        node_data = dataset
        nodes.append(Node(idx=idx, data=node_data))

    orchestrator = ...
    topo = topo
    timestamps = ...  # TODO: Get these from the dataframe itself
    modalities = ...  # TODO: Get these from the dataframe itself or via arg
    ...

    return Env(
        nodes=nodes,
        orchestator=orchestrator,
        topo=topo,
        timestamps=timestamps,
        modalities=modalities,
    )
