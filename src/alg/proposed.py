from __future__ import annotations

import typing as t

from src.environment_tools import get_modalities_at_timestamp
from src.system import Env


def cost(hops: int, weight_m: float) -> float:
    """The total transfer cost of completing a modality transfer."""
    return hops * weight_m


def _select_greedy_with_activation_cost(
    env: Env,
    availability_by_request: dict[t.Any, dict[int, set[str]]],
) -> dict:
    results = {}

    for request in env.requests:
        remaining = set(request.needed_modalities)
        selected_nodes = set()
        modality_assignment = {}
        available_modalities_by_node = availability_by_request[request.idx]

        while remaining:
            best_node = None
            best_cover: set[str] = set()
            best_ratio = float("inf")
            best_incremental_cost = float("inf")

            for node in env.nodes:
                cover = remaining & available_modalities_by_node.get(node.idx, set())
                if not cover:
                    continue

                incremental_cost = sum(
                    cost(
                        env.shortest_paths.get(node.idx, 1),
                        env.modalities_data_size.get(modality, 1.0),
                    )
                    for modality in cover
                )
                if node.idx not in selected_nodes:
                    incremental_cost += env.node_activation_costs.get(node.idx, 1.0)

                ratio = incremental_cost / len(cover)
                if best_node is None or (
                    ratio,
                    incremental_cost,
                    node.idx,
                ) < (
                    best_ratio,
                    best_incremental_cost,
                    best_node,
                ):
                    best_node = node.idx
                    best_cover = cover
                    best_ratio = ratio
                    best_incremental_cost = incremental_cost

            if best_node is None:
                break

            selected_nodes.add(best_node)
            for modality in sorted(best_cover):
                modality_assignment[modality] = best_node
            remaining -= best_cover

        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }

    return results


def proposed_algorithm(env: Env) -> dict:
    availability_by_request = {
        request.idx: {
            node.idx: get_modalities_at_timestamp(node, request.timestamp)
            for node in env.nodes
        }
        for request in env.requests
    }
    return _select_greedy_with_activation_cost(env, availability_by_request)


def _build_timestamp_availability_lookup(
    env: Env,
) -> dict[t.Any, dict[int, set[str]]]:
    availability_by_timestamp: dict[t.Any, dict[int, set[str]]] = {}

    for node in env.nodes:
        modality_columns = [
            col for col in node.data.columns if col not in ("date", "weather")
        ]
        if not modality_columns:
            continue

        for row in node.data.itertuples(index=False):
            timestamp = row.date
            row_values = row._asdict()
            present_modalities = {
                modality
                for modality in modality_columns
                if row_values[modality] == row_values[modality]
            }
            availability_by_timestamp.setdefault(timestamp, {})[node.idx] = (
                present_modalities
            )

    return availability_by_timestamp


def proposed_algorithm_fast(env: Env) -> dict:
    availability_by_timestamp = _build_timestamp_availability_lookup(env)
    availability_by_request = {
        request.idx: {
            node.idx: availability_by_timestamp.get(request.timestamp, {}).get(
                node.idx, set()
            )
            for node in env.nodes
        }
        for request in env.requests
    }
    return _select_greedy_with_activation_cost(env, availability_by_request)
