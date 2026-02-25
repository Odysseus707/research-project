import random

class Node:
    def __init__(self, node_id, owned_data):
        self.node_id = node_id
        self.owned_data = owned_data  # dict: feature -> set(timestamps)

    def missing_timestamps(self, feature, global_timestamps):
        owned = self.owned_data.get(feature, set())
        return global_timestamps - owned

    def add_data(self, feature, timestamps):
        if feature not in self.owned_data:
            self.owned_data[feature] = set()
        self.owned_data[feature].update(timestamps)


def create_nodes(n_nodes, global_features, global_timestamps):
    nodes = []

    for i in range(n_nodes):

        owned_data = {}

        # each node randomly owns some features
        owned_features = random.sample(
            global_features,
            random.randint(1, len(global_features))
        )

        for f in owned_features:
            # randomly own some timestamps for that feature
            ts_subset = set(random.sample(
                list(global_timestamps),
                random.randint(
                    int(0.3 * len(global_timestamps)),
                    len(global_timestamps)
                )
            ))
            owned_data[f] = ts_subset

        nodes.append(Node(i, owned_data))

    return nodes