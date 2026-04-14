from __future__ import annotations

import typing as t
from src.environment_tools import get_modalities_at_timestamp
from src.system import Env


def cost(hops: int, weight_m: float) -> float:
    """The total cost of completing a data transfer.

    Args:
        hops (int): The number of hops needed to transfer the modality from its source to the cloud.
        weight_m (float): The data size of this modality (i.e., cost for one hop).

    Returns:
        The total cost of completing a transfer.
    """
    return hops * weight_m


def proposed_algorithm(env: Env) -> dict:
    results = {}
    for request in env.requests:
        needed = request.needed_modalities
        selected_nodes = set()
        modality_assignment = {}
        available_modalities_by_node = {
            node.idx: get_modalities_at_timestamp(node, request.timestamp)
            for node in env.nodes
        }
        for modality in needed:
            best_node = None
            best_cost = float("inf")
            for node in env.nodes:
                present_modalities = available_modalities_by_node[node.idx]
                if modality not in present_modalities:
                    continue
                hops = env.shortest_paths.get(node.idx, 1)
                w = env.modalities_data_size.get(modality, 1.0)
                c = hops * w
                if c < best_cost:
                    best_cost = c
                    best_node = node.idx
            if best_node is not None:
                selected_nodes.add(best_node)
                modality_assignment[modality] = best_node
        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }
    return results


def _build_best_provider_lookup(env: Env) -> dict[tuple[t.Any, str], int]:
    # Sort once by hop count so the first provider we record is the cheapest one.
    sorted_nodes = sorted(
        env.nodes, key=lambda node: (env.shortest_paths.get(node.idx, 1), node.idx)
    )
    best_provider: dict[tuple[t.Any, str], int] = {}

    for node in sorted_nodes:
        modality_columns = [
            col for col in node.data.columns if col not in ("date", "weather")
        ]
        if not modality_columns:
            continue

        for row in node.data.itertuples(index=False):
            timestamp = row.date
            row_values = row._asdict()
            for modality in modality_columns:
                if row_values.get(modality) is None:
                    continue
                # Pandas stores missing numeric values as NaN, so `value != value`
                # is a cheap null check that avoids repeated dataframe filtering.
                value = row_values[modality]
                if value != value:
                    continue

                key = (timestamp, modality)
                if key not in best_provider:
                    best_provider[key] = node.idx

    return best_provider


def proposed_algorithm_fast(env: Env) -> dict:
    results = {}
    best_provider = _build_best_provider_lookup(env)

    for request in env.requests:
        selected_nodes = set()
        modality_assignment = {}

        for modality in request.needed_modalities:
            best_node = best_provider.get((request.timestamp, modality))
            if best_node is None:
                continue
            selected_nodes.add(best_node)
            modality_assignment[modality] = best_node

        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }

    return results
