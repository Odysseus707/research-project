import networkx as nx

class GreedyOrchestrator:
    def __init__(self, nodes, global_features, global_timestamps, bytes_per_value=8):
        self.nodes = nodes
        self.global_features = global_features
        self.global_timestamps = global_timestamps
        self.bytes_per_value = bytes_per_value

    def run(self, G, greed):

        total_hops = 0
        total_bytes = 0

        for node in self.nodes:

            for feature in self.global_features:

                remaining = node.missing_timestamps(
                    feature,
                    self.global_timestamps
                )

                if not remaining:
                    continue

                original_missing = len(remaining)

                while remaining:

                    best_choice = None
                    best_utility = float("-inf")

                    for other in self.nodes:

                        if other.node_id == node.node_id:
                            continue

                        other_data = other.owned_data.get(feature, set())
                        overlap = remaining.intersection(other_data)

                        if not overlap:
                            continue

                        try:
                            hops = nx.shortest_path_length(
                                G,
                                node.node_id,
                                other.node_id
                            )
                        except nx.NetworkXNoPath:
                            continue

                        coverage = len(overlap)

                        utility = (
                            greed * coverage
                            - (1 - greed) * hops
                        )

                        if utility > best_utility:
                            best_utility = utility
                            best_choice = (other, overlap, hops)

                    if best_choice and best_utility > 0:

                        other, overlap, hops = best_choice

                        node.add_data(feature, overlap)

                        remaining -= overlap

                        total_hops += hops
                        total_bytes += len(overlap) * self.bytes_per_value

                    else:
                        break

        # compute global coverage
        total_possible = (
            len(self.nodes)
            * len(self.global_features)
            * len(self.global_timestamps)
        )

        total_owned = 0

        for node in self.nodes:
            for f in self.global_features:
                total_owned += len(
                    node.owned_data.get(f, set())
                )

        coverage_ratio = total_owned / total_possible

        return total_hops, total_bytes, coverage_ratio