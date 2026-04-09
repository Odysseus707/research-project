from src.environment_tools import generate_graph, create_tree


def test_generate_graph_respects_requested_node_count():
    topology_types = [
        "star",
        "barabasi_albert",
        "erdos_renyi",
        "m_ary_tree",
        "dorogovtsev_goltsev_mendes",
        "complete",
        "balanced_tree",
    ]

    for topology_type in topology_types:
        graph = generate_graph(10, topology_type, seed=42)
        assert graph.number_of_nodes() == 10


def test_create_tree_covers_all_generated_nodes():
    topology_types = [
        "star",
        "barabasi_albert",
        "erdos_renyi",
        "m_ary_tree",
        "dorogovtsev_goltsev_mendes",
        "complete",
        "balanced_tree",
    ]

    for topology_type in topology_types:
        graph = generate_graph(10, topology_type, seed=42)
        tree = create_tree(graph)
        assert tree.number_of_nodes() == graph.number_of_nodes()
