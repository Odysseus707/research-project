from __future__ import annotations

import typing as t
import networkx as nx


from system import Node, Env, Request


def cost(hops: int, weight_m: float) -> float:
    """The total cost of completing a data transfer.

    Args:
        hops (int): The number of hops needed to transfer the modality from its source to the cloud.
        weight_m (float): The data size of this modality (i.e., cost for one hop).

    Returns:
        The total cost of completing a transfer.
    """
    return hops * weight_m


def proposed_algorithm(
    env: Env,
    requests: list[Request],
) -> dict[tuple[int, int], bool]:

    for request in requests:
        included_modalities = request.included_modalities
        remaining_modalities: set = Request.needed_modalities - included_modalities

        selected_nodes = set()
        total_cost = 0.0
        G = env.topo
        orchestrator_idx = 0

        # For each needed modality, find the best node
        for modality in remaining_modalities:
            best_node = None
            best_cost = float("inf")

            for node in env.nodes:
                if modality in node.modalities:
                    hops = nx.shortest_path_length(
                        G,
                        source=orchestrator_idx,
                        target=node.idx,
                    )
                    w = env.modalities_weights.get(modality, 1.0)
                    c = cost(hops, w)
                    if c < best_cost:
                        best_cost = c
                        best_node = node.idx

            if best_node is not None:
                selected_nodes.add(best_node)
                total_cost += best_cost

        return list(selected_nodes), total_cost
