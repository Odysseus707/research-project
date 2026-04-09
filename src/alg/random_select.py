from __future__ import annotations

import typing as t
import networkx as nx
from src.system import Node, Env, Request
from src.environment_tools import create_rng


def cost(hops: int, weight_m: float) -> float:
    return hops * weight_m


def random_algorithm(
    env: Env, requests: list[Request], seed: int | None = None
) -> dict:
    rng = create_rng(seed)
    G = env.topo
    orchestrator_idx = 0
    modalities_data_size = getattr(env, "modalities_data_size", {})
    results = {}
    for request in requests:
        needed = set(request.needed_modalities)
        selected_nodes = set()
        total_cost = 0.0
        node_list = list(env.nodes)
        node_list = rng.permutation(node_list).tolist()
        while needed:
            found = False
            for node in node_list:
                node_modalities = set(node.modalities)
                new_modalities = needed & node_modalities
                if new_modalities:
                    selected_nodes.add(node.idx)
                    hops = nx.shortest_path_length(
                        G, source=orchestrator_idx, target=node.idx
                    )
                    for m in new_modalities:
                        w = modalities_data_size.get(m, 1.0)
                        total_cost += cost(hops, w)
                    needed -= new_modalities
                    found = True
                    break
            if not found:
                break
            node_list = rng.permutation(node_list).tolist()
        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "cost": total_cost,
        }
    return results
