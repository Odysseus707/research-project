import random
import csv
class Node:
    def __init__(self, node_id, features, timestamps, data=None):
        self.node_id = node_id
        self.features = set(features)
        self.timestamps = set(timestamps)
        # data: {timestamp: set(features)}
        self.data = data if data is not None else {}

    def missing_features(self, global_features):
        return set(global_features) - self.features

    def missing_timestamps(self, global_timestamps):
        return set(global_timestamps) - self.timestamps

    def add_data(self, new_features, new_timestamps):
        self.features.update(new_features)
        self.timestamps.update(new_timestamps)



def create_nodes(n_nodes, global_features, global_timestamps, n_timestamps_per_node=20, max_features_per_timestamp=2):
    """
    Each node gets ~20 random timestamps, and for each timestamp, at most 2 random features.
    Returns a list of Node objects with .data = {timestamp: set(features)}
    """
    # Remove 'weather' if present
    features_clean = [f for f in global_features if f != 'weather']
    nodes = []
    for i in range(n_nodes):
        timestamps = random.sample(list(global_timestamps), min(n_timestamps_per_node, len(global_timestamps)))
        feats = set(random.sample(features_clean, min(max_features_per_timestamp, len(features_clean))))
        data = {t: set(feats) for t in timestamps}
        nodes.append(Node(i, feats, set(timestamps), data=data))
    return nodes

def assign_data(nodes, csv_path="seattle-weather.csv", n_timestamps_per_node=20, max_features_per_timestamp=2):
    """
    Assigns sparse data to a list of Node objects using real timestamps and features from a CSV file.
    Each node gets ~20 random timestamps, and for each timestamp, at most 2 random features.
    """
    # Read the CSV to get timestamps, features, and values
    with open(csv_path, newline="") as csvfile:
        reader = list(csv.DictReader(csvfile))
        all_timestamps = [row["date"] for row in reader]
        features = [f for f in reader[0].keys() if f not in ("date", "weather")]

    n_nodes = len(nodes)
    from random import sample
    for i, node in enumerate(nodes):
        node_timestamps = sample(all_timestamps, min(n_timestamps_per_node, len(all_timestamps)))
        feats = set(sample(features, min(max_features_per_timestamp, len(features))))
        data = {}
        for t in node_timestamps:
            # Find the row for this timestamp
            row = next((r for r in reader if r["date"] == t), None)
            if row:
                # Store only the selected features and their values (as float)
                data[t] = {f: float(row[f]) for f in feats}
        node.features = feats
        node.timestamps = set(node_timestamps)
        node.data = data