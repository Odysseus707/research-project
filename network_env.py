import networkx as nx
import logging
from node import Node
from orchestrator import Orchestrator


class networkENV:
    def __init__(
        self,
        num_nodes=7,
        branching_factor=2,
        global_features=None,
        global_timestamps=None,
    ):
        self.num_nodes = num_nodes
        self.branching_factor = branching_factor
        self.global_features = global_features or [
            "precipitation",
            "temp_max",
            "temp_min",
            "wind",
        ]
        self.global_timestamps = global_timestamps or [f"t{i}" for i in range(10)]
        self.tree = None
        self.nodes = []
        self.orchestrator = None
        self._setup_logging()
        self._generate_tree()
        self._setup_nodes_and_orchestrator()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[logging.FileHandler("logs.log", mode="a")],
        )
        self.logger = logging.getLogger("networkENV")

    def _generate_tree(self):
        self.tree = nx.balanced_tree(r=self.branching_factor, h=self._get_tree_height())
        self.logger.info(
            f"Tree generated with branching_factor={self.branching_factor}, height={self._get_tree_height()}, total_nodes={self.tree.number_of_nodes()}"
        )

    def _get_tree_height(self):
        # Calculate minimum height needed for at least num_nodes
        h = 0
        while (self.branching_factor ** (h + 1) - 1) // (
            self.branching_factor - 1
        ) < self.num_nodes:
            h += 1
        return h

    def _setup_nodes_and_orchestrator(self):
        # Assign Node objects to all nodes except root (0)
        self.nodes = [
            Node(node_id=i, features=[], timestamps=[])
            for i in range(1, self.tree.number_of_nodes())
        ]
        # Orchestrator is at root (0), pass the tree for BFS/utility logic
        self.orchestrator = Orchestrator(
            nodes=self.nodes, global_features=self.global_features, tree=self.tree
        )


# Example usage (remove or comment out in production)
if __name__ == "__main__":
    env = networkENV(num_nodes=10, branching_factor=3)
    from node import assign_data

    assign_data(env.nodes)
    # Log a sample node's data for verification
    env.logger.info(f"Sample node 1 data: {env.nodes[0].data}")
