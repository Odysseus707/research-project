import pulp
import networkx as nx
import logging

# ILP solver for the node selection problem



def solve_ilp(nodes, global_features, tree, modalities_weights=None):
    """
    ILP: minimize sum_{v,m} x_vm * cost_vm
    subject to:
        sum_v x_vm = 1 for all m
        x_vm <= I(m in m_v)
        x_vm in {0,1}
    where cost_vm = hops * size(m)
    """
    if modalities_weights is None:
        modalities_weights = {m: 1.0 for m in global_features if m != "weather"}
    V = [node.node_id for node in nodes]
    features_clean = [f for f in global_features if f != "weather"]
    M = set(features_clean)
    Sv = {node.node_id: set(node.features) for node in nodes}
    # Decision variables: x_vm = 1 if node v provides modality m
    prob = pulp.LpProblem("NodeModalitySelectionILP", pulp.LpMinimize)
    x_vm = pulp.LpVariable.dicts("x", ((v, m) for v in V for m in M), cat="Binary")

    # Precompute hops from orchestrator (0) to each node
    hops = {}
    for v in V:
        if v == 0:
            hops[v] = 0
        else:
            hops[v] = nx.shortest_path_length(tree, source=0, target=v)

    # Objective: minimize sum_{v,m} x_vm * cost_vm
    prob += pulp.lpSum([
        x_vm[(v, m)] * hops[v] * modalities_weights.get(m, 1.0)
        for v in V for m in M
    ])

    # Constraint: for each modality, sum_v x_vm = 1 (each modality must be covered)
    for m in M:
        prob += pulp.lpSum([x_vm[(v, m)] for v in V]) == 1

    # Constraint: x_vm <= I(m in Sv[v])
    for v in V:
        for m in M:
            if m not in Sv[v]:
                prob += x_vm[(v, m)] == 0

    prob.writeLP("ILP_Model.lp")
    prob.solve()

    selected = [(v, m) for v in V for m in M if pulp.value(x_vm[(v, m)]) > 0.5]
    selected_nodes = set(v for v, m in selected)

    # Logging
    logger = logging.getLogger("ILP Solver")
    logger.info(f"ILP selected nodes: {list(selected_nodes)}")
    logger.info(f"ILP assignments (node, modality): {selected}")

    # Log objective value and basic stats
    obj_val = pulp.value(prob.objective)
    logger.info(f"ILP Objective value: {obj_val}")
    try:
        logger.info(f"Solver status: {pulp.LpStatus[prob.status]}")
    except Exception:
        pass

    return list(selected_nodes), selected, prob


# selected_nodes, selected_edges, prob = solve_ilp(env.nodes, env.global_features, env.tree, greed_param=0.5)
# print(selected_nodes)
