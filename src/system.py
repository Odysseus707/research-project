import dataclasses
import typing as t

import networkx as nx
import pandas as pd

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
    data: pd.DataFrame
    # to track which needed modalities are present in this node's data
    flag: dict[T:bool]

    @property
    def timestamps(self) -> list[int]:
        ts = self.data.timestamp.unique()
        ts = ts.tolist()
        ts = sorted(ts)
        return ts

    @property
    def modalities(self) -> list[T]:
        df = self.data
        columns_without_modalities = df.loc[:, df.notna().any(axis=0)]
        return columns_without_modalities


@dataclasses.dataclass
class Request:
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
    # orchestator: Orchestrator
    topo: nx.Graph
    timestamps: list[int]
    modalities: list[T]
    modalities_weights: dict[T, float]
    shortest_paths: dict[int, int] = dataclasses.field(init=False, default=None)
    orchestrator_idx: int = 0  # TODO: Turn this into a constant for clarity.

    def __post_init__(self):
        self.shortest_paths = {}
        cloud_node = [node for node in self.topo.nodes() if node.type == "orchestrator"]
        for node in self.topo.nodes():
            if node not in self.nodes:
                continue

            self.shortest_paths[node] = nx.shortest_path_length(
                self.topo,
                source=cloud_node,
                target=node,
            )

    # TODO:  we need a mapping between calculation_types and needed modalities
