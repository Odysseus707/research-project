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
class Orchestrator:
    ...


@dataclasses.dataclass
class Request:
    timestamp: int
    included_modalities: set[T]
    # TODO: requested_calculation_type


@dataclasses.dataclass
class Env:
    nodes: list[Node]
    orchestator: Orchestrator
    topo: nx.Graph
    timestamps: list[int]
    modalities: list[T]

    # TODO:  we need a mapping between calculation_types and needed modalities
