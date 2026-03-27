import random

class Node:
    def __init__(self, node_id, features, timestamps):
        self.node_id = node_id
        self.features = set(features)
        self.timestamps = set(timestamps)

    def missing_features(self, global_features):
        return set(global_features) - self.features

    def missing_timestamps(self, global_timestamps):
        return set(global_timestamps) - self.timestamps

    def add_data(self, new_features, new_timestamps):
        self.features.update(new_features)
        self.timestamps.update(new_timestamps)


def create_nodes(n_nodes, global_features, global_timestamps):
    nodes = []

    for i in range(n_nodes):

        features = random.sample(
            global_features,
            random.randint(1, len(global_features))
        )

        timestamps = set(random.sample(
            list(global_timestamps),
            random.randint(
                int(0.3 * len(global_timestamps)),
                len(global_timestamps)
            )
        ))

        nodes.append(Node(i, features, timestamps))

    return nodes