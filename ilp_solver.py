import pulp
import networkx as nx

# ILP solver for the node selection problem


def solve_ilp(nodes, global_features, tree, greed_param=0.5):
    """
    nodes: list of Node objects (must have .node_id and .features)
    features_clean: set/list of all required features (modalities)
    tree: networkx graph (root is 0)
    greed_param: g in the objective
    """
    V = [node.node_id for node in nodes]
    features_clean = [f for f in global_features if f != "weather"]
    M = set(features_clean)
    # Build Sv for each node
    Sv = {node.node_id: set(node.features) for node in nodes}
    # All edges in the tree
    E = list(tree.edges())
    # Cost for each edge (set to 1 for each hop)
    ce = {e: 1 for e in E}

    # Decision variables
    prob = pulp.LpProblem("NodeSelectionILP", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("x", V, cat="Binary")  # 1 if node v is selected
    y = pulp.LpVariable.dicts(
        "y", E, cat="Binary"
    )  # 1 if edge e is selected (part of path to root)

    # Objective: max sum_v g*|Sv|*xv - (1-g)*sum_e ce*ye
    prob += pulp.lpSum([greed_param * len(Sv[v]) * x[v] for v in V]) - pulp.lpSum(
        [(1 - greed_param) * ce[e] * y[e] for e in E]
    )

    # Constraint: union of selected Sv covers all M
    for m in M:
        prob += pulp.lpSum([x[v] for v in V if m in Sv[v]]) >= 1

    # Constraint: xv <= ye for all e in path(v, 0)
    for v in V:
        if v == 0:
            continue
        path = nx.shortest_path(tree, source=0, target=v)
        edges_in_path = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        for e in edges_in_path:
            prob += x[v] <= y[e]

    prob.writeLP("ILP_Model.lp")

    # Binary constraints are already set by cat='Binary'
    # Solve
    prob.solve()

    selected_nodes = [v for v in V if pulp.value(x[v]) > 0.5]
    selected_edges = [e for e in E if pulp.value(y[e]) > 0.5]
    return selected_nodes, selected_edges, prob


# selected_nodes, selected_edges, prob = solve_ilp(env.nodes, env.global_features, env.tree, greed_param=0.5)
# print(selected_nodes)
