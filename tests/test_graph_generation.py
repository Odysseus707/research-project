from src.environment_tools import generate_graph, create_tree


def test_generate_graph_respects_requested_node_count():
    for branching_factor in (2, 3):
        graph = generate_graph(10, branching_factor=branching_factor, seed=42)
        assert graph.number_of_nodes() == 10


def test_create_tree_covers_all_generated_nodes():
    for branching_factor in (2, 3):
        graph = generate_graph(10, branching_factor=branching_factor, seed=42)
        tree = create_tree(graph)
        assert tree.number_of_nodes() == graph.number_of_nodes()
