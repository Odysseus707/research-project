from __future__ import annotations

import typing as t

from src.system import Env
from src.environment_tools import create_rng, get_modalities_at_timestamp


def cost(hops: int, weight_m: float) -> float:
    return hops * weight_m


def random_algorithm(env: Env, seed: int | None = None) -> dict:
    rng = create_rng(seed)
    results = {}
    for request in env.requests:
        needed = set(request.needed_modalities)
        selected_nodes = set()
        modality_assignment = {}
        node_list = rng.permutation(list(env.nodes)).tolist()
        while needed:
            found = False
            for node in node_list:
                present_modalities = get_modalities_at_timestamp(
                    node, request.timestamp
                )
                new_modalities = needed & present_modalities
                if new_modalities:
                    selected_nodes.add(node.idx)
                    for modality in new_modalities:
                        modality_assignment[modality] = node.idx
                    needed -= new_modalities
                    found = True
                    break
            if not found:
                break
            node_list = rng.permutation(list(env.nodes)).tolist()
        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }
    return results


def _build_modality_provider_lookup(env: Env) -> dict[str, list[int]]:
    providers: dict[str, list[int]] = {}
    for node in env.nodes:
        for modality in node.modalities:
            providers.setdefault(modality, []).append(node.idx)
    return providers


def random_select_fast(env: Env, seed: int | None = None) -> dict[t.Any, dict]:
    rng = create_rng(seed)
    results = {}
    modality_providers = _build_modality_provider_lookup(env)
    node_by_idx = {node.idx: node for node in env.nodes}

    for request in env.requests:
        selected_nodes = set()
        modality_assignment = {}

        for modality in request.needed_modalities:
            candidate_nodes = modality_providers.get(modality, [])
            if not candidate_nodes:
                continue

            for node_idx in rng.permutation(candidate_nodes).tolist():
                node = node_by_idx[node_idx]
                present_modalities = get_modalities_at_timestamp(node, request.timestamp)
                if modality not in present_modalities:
                    continue
                selected_nodes.add(node_idx)
                modality_assignment[modality] = node_idx
                break

        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }

    return results
