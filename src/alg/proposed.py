from __future__ import annotations

import typing as t
import networkx as nx


from src.system import Node, Env, Request


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
        for modality in needed:
            best_node = None
            best_cost = float("inf")
            for node in env.nodes:
                if modality in node.modalities:
                    hops = env.shortest_paths.get(node.idx, 1)
                    w = env.modalities_data_size.get(modality, 1.0)
                    c = hops * w
                    if c < best_cost:
                        best_cost = c
                        best_node = node.idx
            if best_node is not None:
                selected_nodes.add(best_node)
        results[request.idx] = {"selected_nodes": list(selected_nodes)}
    return results
