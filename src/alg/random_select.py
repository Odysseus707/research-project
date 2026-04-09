from __future__ import annotations

import typing as t
import networkx as nx
from src.system import Node, Env, Request
from src.environment_tools import create_rng


def cost(hops: int, weight_m: float) -> float:
    return hops * weight_m


def random_algorithm(
    env: Env, seed: int | None = None
    ) -> dict:
        rng = create_rng(seed)
        G = env.topo
        orchestrator_idx = 0
        modalities_data_size = getattr(env, "modalities_data_size", {})
        results = {}
        for request in env.requests:
            needed = set(request.needed_modalities)
            selected_nodes = set()
            node_list = list(env.nodes)
            node_list = rng.permutation(node_list).tolist()
            while needed:
                found = False
                for node in node_list:
                    node_modalities = set(node.modalities)
                    new_modalities = needed & node_modalities
                    if new_modalities:
                        selected_nodes.add(node.idx)
                        needed -= new_modalities
                        found = True
                        break
                if not found:
                    break
                node_list = rng.permutation(node_list).tolist()
            results[request.idx] = {
                "selected_nodes": list(selected_nodes)
            }
        return results
