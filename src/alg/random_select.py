from __future__ import annotations

from src.system import Env
from src.environment_tools import create_rng, get_modalities_at_timestamp


def cost(hops: int, weight_m: float) -> float:
    return hops * weight_m


def random_algorithm(
    env: Env, seed: int | None = None
) -> dict:
    rng = create_rng(seed)
    results = {}
    for request in env.requests:
        needed = set(request.needed_modalities)
        selected_nodes = set()
        node_list = rng.permutation(list(env.nodes)).tolist()
        while needed:
            found = False
            for node in node_list:
                present_modalities = get_modalities_at_timestamp(node, request.timestamp)
                new_modalities = needed & present_modalities
                if new_modalities:
                    selected_nodes.add(node.idx)
                    needed -= new_modalities
                    found = True
                    break
            if not found:
                break
            node_list = rng.permutation(list(env.nodes)).tolist()
        results[request.idx] = {"selected_nodes": list(selected_nodes)}
    return results
