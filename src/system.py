import dataclasses
import typing as t

import networkx as nx
import pandas as pd

import functools

T = t.TypeVar("T")


# class ModalityDataFrame(pd.DataFrame):
#     def __init__(
#         self,
#         data=None,
#         index=None,
#         columns=None,
#         dtype=None,
#         copy=None,
#         *,
#         modalities: list[str] | None = None,
#         **kwargs
#     ):
#         super().__init__(data, index, columns, dtype, copy)
#         if modalities is None:
#             self.modalities = self.columns.tolist()
#         else:
#             self.modalities = modalities

#     def modality_frame(self):
#         return self[self.modalities]


@dataclasses.dataclass
class Node:
    idx: int
    data: pd.DataFrame = dataclasses.field(init=True, repr=False)
    # to track which needed modalities are present in this node's data
    # flag: dict[T, bool]

    # TODO: Adjust because I do not think this works since we fix each worker to
    # have the same timestamps. We need to check for if the row contains nothing
    # but NAN values for the modalities.
    @functools.cached_property
    def timestamps(self) -> list[int]:
        ts = self.data.timestamp.unique()
        ts = ts.tolist()
        ts = sorted(ts)
        return ts

    # TODO: Similar to other TODO above.
    @functools.cached_property
    def modalities(self) -> list[T]:
        df = self.data
        columns_without_modalities = df.loc[:, df.notna().any(axis=0)]
        return columns_without_modalities


@dataclasses.dataclass
class Request:
    node_idx: int
    idx: int
    timestamp: int
    included_modalities: set[T]
    calculation_type: str = "weather"  # default type

    @property
    def needed_modalities(self) -> set[T]:
        match self.calculation_type:
            case "weather":
                total_modalities = {"precipitation", "temp_max", "temp_min", "wind"}
            case "temperature":
                total_modalities = {"temp_max", "temp_min"}
            case "wind":
                total_modalities = {"wind"}
            case _:
                total_modalities = set()
        return total_modalities - self.included_modalities


# @dataclasses.dataclass
# class Orchestrator:
#     algorithm: str = "proposed"
#     request: Request = None
#     timestamp: list[int]
#     nodes: list[Node]
#     hops: int = 0
#     nodes_queried: list[int]
#     selected_nodes: list[int]


@dataclasses.dataclass
class Env:
    nodes: list[Node]
    topo: nx.Graph
    timestamps: list[int] = dataclasses.field(init=True, repr=False)
    modalities: list[T] = dataclasses.field(init=True, repr=False)
    # Additional arguments below.
    modalities_data_size: dict[T, float] = dataclasses.field(init=True, default=None)
    shortest_paths: dict[int, int] = dataclasses.field(init=False, default=None)
    orchestrator_idx: int = 0  # TODO: Turn this into a constant for clarity.
    requests: list[Request] = dataclasses.field(init=True, default_factory=list)

    def __post_init__(self):
        # Set the modality data sizes to 1 if not set via the initializer.
        if self.modalities_data_size is None:
            self.modalities_data_size = {}
            for m in self.modalities:
                self.modalities_data_size[m] = 1.0

        # Pre-compute the shortest paths.
        self.shortest_paths = {}
        cloud_node = [
            node
            for node, node_data in self.topo.nodes(data=True)
            if node_data["type"] == "orchestrator"
        ]
        for node in self.topo.nodes():
            if node not in self.nodes:
                continue

            self.shortest_paths[node] = nx.shortest_path_length(
                self.topo,
                source=cloud_node,
                target=node,
            )

    # TODO:  we need a mapping between calculation_types and needed modalities
