import numpy as np

class Node:
    def __init__(self, node_id, owned_features, n_samples):
        self.node_id = node_id
        self.owned_features = set(owned_features)
        self.n_samples = n_samples

    def missing_features(self, global_features):
        return set(global_features) - self.owned_features

    def transfer_cost(self, features, bytes_per_value=8):
        return len(features) * self.n_samples * bytes_per_value