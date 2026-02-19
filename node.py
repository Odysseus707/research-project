import numpy as np
import random

class Node:
    def __init__(self, node_id, owned_features, n_samples):
        self.node_id = node_id
        self.owned_features = set(owned_features)
        self.n_samples = n_samples

    def missing_features(self, global_features):
        return set(global_features) - self.owned_features


def create_nodes(n_nodes, global_features, n_samples):
    nodes = []

    for i in range(n_nodes):
        owned = random.sample(
            global_features,
            random.randint(1, len(global_features))
        )

        nodes.append(
            Node(
                node_id=i,
                owned_features=owned,
                n_samples=n_samples
            )
        )

    return nodes