import networkx as nx

def build_graph(n, p):
    G = nx.erdos_renyi_graph(n, p)
    return G


class Orchestrator:
    def __init__(self, nodes, global_features):
        self.nodes = nodes
        self.global_features = global_features

    def dumb_strategy(self):
        total_bytes = 0
        total_connections = 0

        for node in self.nodes:
            for other in self.nodes:
                if node.node_id == other.node_id:
                    continue

                total_connections += 1
                total_bytes += node.transfer_cost(other.owned_features)

        return total_connections, total_bytes

    def smart_strategy(self):
        total_bytes = 0
        total_connections = 0

        for node in self.nodes:
            missing = node.missing_features(self.global_features)

            for other in self.nodes:
                if node.node_id == other.node_id:
                    continue

                useful = missing.intersection(other.owned_features)

                if useful:
                    total_connections += 1
                    total_bytes += node.transfer_cost(useful)

        return total_connections, total_bytes
    
    def smart_strategy_with_graph(self, G):
        total_bytes = 0
        total_weighted_cost = 0
        total_hops = 0
        request_count = 0

        for node in self.nodes:
            missing = node.missing_features(self.global_features)

            for feature in missing:
                # find nodes that own this feature
                owners = [
                    other for other in self.nodes
                    if feature in other.owned_features
                    and other.node_id != node.node_id
                ]

                if not owners:
                    continue

                # choose closest owner
                min_hop = float("inf")
                best_owner = None

                for owner in owners:
                    try:
                        hop = nx.shortest_path_length(
                            G, node.node_id, owner.node_id
                        )
                        if hop < min_hop:
                            min_hop = hop
                            best_owner = owner
                    except nx.NetworkXNoPath:
                        continue

                if best_owner is None:
                    continue

                bytes_needed = node.transfer_cost([feature])

                total_bytes += bytes_needed
                total_weighted_cost += bytes_needed * min_hop
                total_hops += min_hop
                request_count += 1

        avg_hops = total_hops / request_count if request_count else 0

        return total_bytes, total_weighted_cost, total_hops