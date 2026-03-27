import logging
from model import SimpleWeatherModel
import networkx as nx
import joblib

class Orchestrator:
    def __init__(self, nodes, global_features, tree=None, greed_param=0.5):
        self.nodes = nodes
        self.global_features = global_features
        self.tree = tree  # networkx graph
        self.g = greed_param  # greed parameter for utility
        self.logger = logging.getLogger("Orchestrator")
        # Initialize and load the neural network model for weather calculation
        self.weather_model = SimpleWeatherModel()
        try:
            self.weather_model.load("weather_model.joblib")
            self.label_encoder = joblib.load("weather_label_encoder.joblib")
        except Exception as e:
            self.logger.warning(f"Could not load trained model or label encoder: {e}")
            self.label_encoder = None

    def predict_weather(self, timestamp):
        """
        Gather feature values for the given timestamp from all nodes and predict weather.
        """
        feature_order = ["precipitation", "temp_max", "temp_min", "wind"]
        feature_values = {f: None for f in feature_order}
        for node in self.nodes:
            if timestamp in node.data:
                for f in node.data[timestamp]:
                    if f in feature_values and feature_values[f] is None:
                        feature_values[f] = node.data[timestamp][f]
        features = [feature_values[f] if feature_values[f] is not None else 0.0 for f in feature_order]
        import numpy as np
        if not self.weather_model.is_trained or self.label_encoder is None:
            self.logger.warning("Weather model or label encoder not loaded.")
            return None
        X = np.array(features).reshape(1, -1)
        pred = self.weather_model.predict(X)
        return self.label_encoder.inverse_transform(pred)[0]

    def handle_request(self, requesting_node_id, timestamp, present_modalities):
        """
        requesting_node_id: int (node id of requester)
        timestamp: any (not used in this logic yet)
        present_modalities: set of modalities the node already has
        """
        required_modalities = set(self.global_features)
        missing_modalities = required_modalities - set(present_modalities)
        if not missing_modalities:
            self.logger.info(f"Node {requesting_node_id} already has all modalities.")
            return []

        # BFS from orchestrator (root=0) to find nodes with missing modalities
        candidates = []
        for node in self.nodes:
            node_modalities = getattr(node, 'features', set())
            overlap = missing_modalities & set(node_modalities)
            if overlap:
                s_v = len(overlap)
                if self.tree is not None:
                    try:
                        h_v = nx.shortest_path_length(self.tree, source=0, target=node.node_id)
                    except Exception:
                        h_v = float('inf')
                else:
                    h_v = 1
                utility = self.g * s_v - (1 - self.g) * h_v
                candidates.append({
                    'node_id': node.node_id,
                    'modalities': overlap,
                    'score': s_v,
                    'hops': h_v,
                    'utility': utility
                })
        # Log all candidate nodes and their scores
        self.logger.info("Candidate nodes and scores:")
        for cand in candidates:
            self.logger.info(f"Node {cand['node_id']}: modalities={cand['modalities']}, score={cand['score']}, hops={cand['hops']}, utility={cand['utility']}")

        # Greedy selection: pick nodes to cover all missing modalities, maximizing utility
        selected_nodes = []
        covered = set()
        candidates = sorted(candidates, key=lambda x: -x['utility'])
        path_log = []
        for cand in candidates:
            if not (cand['modalities'] - covered):
                continue
            selected_nodes.append(cand)
            covered.update(cand['modalities'])
            path_log.append(f"Selected node {cand['node_id']} (covers {cand['modalities']}, hops={cand['hops']}, utility={cand['utility']})")
            if covered >= missing_modalities:
                break
        self.logger.info(f"Selection path: {' -> '.join(path_log) if path_log else 'No nodes selected'}")
        self.logger.info(f"Orchestrator selected nodes: {[c['node_id'] for c in selected_nodes]} to cover modalities: {missing_modalities}")
        # Predict weather using gathered feature values for the timestamp
        if timestamp:
            weather_pred = self.predict_weather(timestamp)
            if weather_pred:
                msg_pred = f"Predicted weather: {weather_pred}"
                print(msg_pred)
                self.logger.info(msg_pred)
        return selected_nodes