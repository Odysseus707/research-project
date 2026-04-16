from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import pulp

from src.environment_tools import get_modalities_at_timestamp
from src.system import Env, Request


@dataclass(frozen=True)
class ExactCoverColumn:
    node_idx: int
    modalities: tuple[str, ...]
    cost: float


def _build_exact_cover_columns(
    env: Env,
    request: Request,
) -> list[ExactCoverColumn]:
    needed_modalities = set(request.needed_modalities)
    modalities_data_size = getattr(env, "modalities_data_size", None) or {
        modality: 1.0 for modality in needed_modalities
    }
    activation_costs = getattr(env, "node_activation_costs", None) or {
        node.idx: 1.0 for node in env.nodes
    }

    columns = []
    for node in env.nodes:
        available_modalities = sorted(
            get_modalities_at_timestamp(node, request.timestamp) & needed_modalities
        )
        if not available_modalities:
            continue

        for subset_size in range(1, len(available_modalities) + 1):
            for subset in combinations(available_modalities, subset_size):
                transfer_cost = sum(
                    env.shortest_paths.get(node.idx, 1)
                    * modalities_data_size.get(modality, 1.0)
                    for modality in subset
                )
                columns.append(
                    ExactCoverColumn(
                        node_idx=node.idx,
                        modalities=subset,
                        cost=activation_costs.get(node.idx, 1.0) + transfer_cost,
                    )
                )

    return columns


def solve_ilp(env: Env) -> dict:
    """
    For each request in env.requests, solve the weighted exact-cover ILP and
    return a dict mapping request.idx to the selected node set and the
    modality-to-node assignment.
    """
    results = {}
    for request in env.requests:
        needed_modalities = sorted(request.needed_modalities)
        if not needed_modalities:
            results[request.idx] = {
                "selected_nodes": [],
                "modality_assignment": {},
            }
            continue

        columns = _build_exact_cover_columns(env, request)
        cover_union = {
            modality for column in columns for modality in column.modalities
        }
        if set(needed_modalities) - cover_union:
            results[request.idx] = {
                "selected_nodes": [],
                "modality_assignment": {},
            }
            continue

        prob = pulp.LpProblem("WeightedExactCoverILP", pulp.LpMinimize)
        column_ids = list(range(len(columns)))
        z_i = pulp.LpVariable.dicts("z", column_ids, cat="Binary")

        prob += pulp.lpSum(z_i[idx] * columns[idx].cost for idx in column_ids)

        for modality in needed_modalities:
            prob += pulp.lpSum(
                z_i[idx]
                for idx, column in enumerate(columns)
                if modality in column.modalities
            ) == 1

        for node in env.nodes:
            prob += pulp.lpSum(
                z_i[idx]
                for idx, column in enumerate(columns)
                if column.node_idx == node.idx
            ) <= 1

        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[prob.status] != "Optimal":
            results[request.idx] = {
                "selected_nodes": [],
                "modality_assignment": {},
            }
            continue

        chosen_columns = [
            columns[idx] for idx in column_ids if pulp.value(z_i[idx]) > 0.5
        ]
        selected_nodes = sorted({column.node_idx for column in chosen_columns})
        modality_assignment = {}
        for column in chosen_columns:
            for modality in column.modalities:
                modality_assignment[modality] = column.node_idx

        results[request.idx] = {
            "selected_nodes": selected_nodes,
            "modality_assignment": modality_assignment,
        }
    return results
