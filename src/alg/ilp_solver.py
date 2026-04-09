
import pulp
import networkx as nx
import numpy as np
import pandas as pd
from src.system import Node, Env, Request

# ILP solver for the node selection problem



def solve_ilp(env: Env) -> dict:
    """
    For each request in env.requests, solve the ILP and return a dict mapping
    request.idx to the selected node set and the modality-to-node assignment.
    """
    results = {}
    for request in env.requests:
        nodes = env.nodes
        modalities = list(request.needed_modalities)
        V = [node.idx for node in nodes]
        M = set(modalities)
        # For each node, determine which modalities it has at the request timestamp (vectorized)
        Sv = {}
        for node in nodes:
            node_df = node.data
            row = node_df[node_df["date"] == request.timestamp]
            if not row.empty:
                present_modalities = set(row[node.modalities].dropna(axis=1, how='all').columns)
            else:
                present_modalities = set()
            # Only keep modalities that are needed for this request
            Sv[node.idx] = present_modalities & M
        modalities_data_size = getattr(env, "modalities_data_size", None)
        if modalities_data_size is None:
            modalities_data_size = {m: 1.0 for m in modalities}
        prob = pulp.LpProblem("NodeModalitySelectionILP", pulp.LpMinimize)
        x_vm = pulp.LpVariable.dicts("x", ((v, m) for v in V for m in M), cat="Binary")
        hops = env.shortest_paths
        # Objective: minimize sum_{v,m} x_vm * cost_vm
        prob += pulp.lpSum(
            [
                x_vm[(v, m)] * hops.get(v, 1) * modalities_data_size.get(m, 1.0)
                for v in V
                for m in M
            ]
        )
        # Each modality must be covered
        for m in M:
            prob += pulp.lpSum([x_vm[(v, m)] for v in V]) == 1
        # Only allow nodes that have the modality
        for v in V:
            for m in M:
                if m not in Sv[v]:
                    prob += x_vm[(v, m)] == 0
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        selected = [(v, m) for v in V for m in M if pulp.value(x_vm[(v, m)]) > 0.5]
        selected_nodes = set(v for v, m in selected)
        modality_assignment = {m: v for v, m in selected}
        results[request.idx] = {
            "selected_nodes": list(selected_nodes),
            "modality_assignment": modality_assignment,
        }
    return results


# selected_nodes, selected_edges, prob = solve_ilp(env.nodes, env.global_features, env.tree, greed_param=0.5)
# print(selected_nodes)
