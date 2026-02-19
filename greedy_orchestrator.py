import networkx as nx

class GreedyOrchestrator:
    def __init__(self, nodes, global_features, bytes_per_value=8):
        self.nodes = nodes
        self.global_features = global_features
        self.bytes_per_value = bytes_per_value

    def run(self, G, greed):
        total_hops = 0
        total_bytes = 0
        total_features_acquired = 0

        for node in self.nodes:

            missing = node.missing_features(self.global_features)

            for feature in missing:

                best_choice = None
                best_utility = float("-inf")

                for other in self.nodes:
                    if other.node_id == node.node_id:
                        continue

                    if feature not in other.owned_features:
                        continue

                    try:
                        hops = nx.shortest_path_length(
                            G,
                            node.node_id,
                            other.node_id
                        )
                    except nx.NetworkXNoPath:
                        continue

                    benefit = node.n_samples
                    hop_cost = hops

                    utility = greed * benefit - (1 - greed) * hop_cost

                    if utility > best_utility:
                        best_utility = utility
                        best_choice = (hops, benefit)

                if best_choice and best_utility > 0:
                    hops, benefit = best_choice

                    bytes_needed = benefit * self.bytes_per_value

                    total_hops += hops
                    total_bytes += bytes_needed
                    total_features_acquired += benefit

        return total_hops, total_bytes, total_features_acquired