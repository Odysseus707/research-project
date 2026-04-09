import pulp
import networkx as nx
import numpy as np

# ILP solver for the node selection problem


def solve_ilp(env):
    """
    ILP: minimize sum_{v,m} x_vm * cost_vm
    subject to:
        sum_v x_vm = 1 for all m
        x_vm <= I(m in m_v)
        x_vm in {0,1}
    where cost_vm = hops * size(m)
    Returns a dict: {"selected_nodes": [...], "selected": {...}, "cost": ...}
    """
    nodes = env.nodes
    modalities = [m for m in env.modalities if m != "weather"]
    V = [node.idx for node in nodes]
    M = set(modalities)
    Sv = {node.idx: set(getattr(node, "modalities", [])) for node in nodes}
    modalities_data_size = getattr(env, "modalities_data_size", None)
    if modalities_data_size is None:
        modalities_data_size = {m: 1.0 for m in modalities}
    prob = pulp.LpProblem("NodeModalitySelectionILP", pulp.LpMinimize)
    x_vm = pulp.LpVariable.dicts("x", ((v, m) for v in V for m in M), cat="Binary")
    # Use env.shortest_paths for hops
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
    prob.writeLP("ILP_Model.lp")
    prob.solve()
    selected = [(v, m) for v in V for m in M if pulp.value(x_vm[(v, m)]) > 0.5]
    selected_nodes = set(v for v, m in selected)
    total_cost = pulp.value(prob.objective)
    return {
        "selected_nodes": list(selected_nodes),
        "cost": total_cost,
    }


# selected_nodes, selected_edges, prob = solve_ilp(env.nodes, env.global_features, env.tree, greed_param=0.5)
# print(selected_nodes)
