import networkx as nx
import os
import logging

class GreedyOrchestrator:
    def __init__(self, nodes, global_features, global_timestamps, bytes_per_value=8):
        self.nodes = nodes
        self.global_features = global_features
        self.global_timestamps = global_timestamps
        self.bytes_per_value = bytes_per_value
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

    def _configure_logger(self, verbose, log_file):
        self.logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if log_file:
            directory = os.path.dirname(log_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode="w")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def run(self, G, greed, verbose=True, log_file=None):
        """
        Run iterative node collaboration using Section 3.5-style node selection:
        for each modality m, choose exactly one supplier v that maximizes
            x_v^m [lambda * s_v - (1-lambda) * h_v]
        where x_v^m in {0, 1} and sum_v x_v^m = 1.
        """
        if not (0.0 <= greed <= 1.0):
            raise ValueError("lambda/greed must be within [0, 1].")

        self._configure_logger(verbose=verbose, log_file=log_file)
        self.logger.info("Starting orchestration with lambda=%.3f", greed)

        total_hops = 0
        total_bytes = 0

        node_stats = {
            node.node_id: {
                "bytes_received": 0,
                "bytes_sent": 0,
                "hops_used": 0
            }
            for node in self.nodes
        }

        # ---------------------------
        # Iterative rounds
        # ---------------------------
        round_num = 0
        while True:
            round_num += 1
            transfers_this_round = 0

            self.logger.info("======== ROUND %d ========", round_num)

            # Iterate over nodes
            for node in self.nodes:

                # Pre-transfer state
                pre_features = set(node.features)
                pre_timestamps = set(node.timestamps)
                missing_features = node.missing_features(self.global_features)
                needed_features = set(missing_features)

                self.logger.info("Node %s", node.node_id)
                self.logger.info("PRE-TRANSFER FEATURES: %s", sorted(pre_features))
                self.logger.debug("PRE-TRANSFER TIMESTAMPS: %s", sorted(pre_timestamps))
                self.logger.info("NEEDED FEATURES: %s", sorted(needed_features))

                if not needed_features or not pre_timestamps:
                    self.logger.info("Nothing needed, skipping.")
                    continue

                selected_transfers = []
                utility_details = []

                # Section 3.5: one selected supplier per modality.
                for modality in sorted(needed_features):
                    best_for_modality = None
                    best_utility = float("-inf")

                    for other in self.nodes:
                        if other.node_id == node.node_id:
                            continue
                        if modality not in other.features:
                            continue

                        try:
                            hops = nx.shortest_path_length(
                                G,
                                node.node_id,
                                other.node_id
                            )
                        except nx.NetworkXNoPath:
                            continue

                        timestamp_overlap = pre_timestamps.intersection(other.timestamps)
                        if not timestamp_overlap:
                            continue

                        score = len(timestamp_overlap)
                        utility = greed * score - (1 - greed) * hops

                        utility_details.append({
                            "modality": modality,
                            "supplier": other.node_id,
                            "timestamps": sorted(timestamp_overlap),
                            "score": score,
                            "hops": hops,
                            "utility": utility,
                        })

                        if utility > best_utility:
                            best_utility = utility
                            best_for_modality = (other, modality, timestamp_overlap, hops, utility)

                    if best_for_modality and best_utility > 0:
                        selected_transfers.append(best_for_modality)

                self.logger.info("UTILITY CALCULATIONS:")
                for detail in utility_details:
                    self.logger.info(
                        "Modality=%s | Supplier=%s | Timestamps=%s | Score=%d | Hops=%d | Utility=%.3f",
                        detail["modality"],
                        detail["supplier"],
                        detail["timestamps"],
                        detail["score"],
                        detail["hops"],
                        detail["utility"],
                    )

                if selected_transfers:
                    transferred_features = set()
                    transferred_timestamps = set()

                    for other, modality, timestamp_overlap, hops, utility in selected_transfers:
                        transferred_features.add(modality)
                        transferred_timestamps.update(timestamp_overlap)

                        bytes_transferred = len(timestamp_overlap) * self.bytes_per_value
                        total_hops += hops
                        total_bytes += bytes_transferred

                        node_stats[node.node_id]["bytes_received"] += bytes_transferred
                        node_stats[node.node_id]["hops_used"] += hops
                        node_stats[other.node_id]["bytes_sent"] += bytes_transferred

                        self.logger.info(
                            "SELECTED | Modality=%s | Supplier Node=%s | Timestamps=%s | Hops=%d | Utility=%.3f",
                            modality,
                            other.node_id,
                            sorted(timestamp_overlap),
                            hops,
                            utility,
                        )

                    node.add_data(transferred_features, transferred_timestamps)
                    transfers_this_round += len(selected_transfers)

                    self.logger.info("Transferred Features: %s", sorted(transferred_features))
                    self.logger.debug("Transferred Timestamps: %s", sorted(transferred_timestamps))
                    self.logger.info("POST-TRANSFER FEATURES: %s", sorted(node.features))
                    self.logger.debug("POST-TRANSFER TIMESTAMPS: %s", sorted(node.timestamps))
                else:
                    self.logger.info("No beneficial supplier found.")

            # Stop if no transfers occurred in this round
            if transfers_this_round == 0:
                self.logger.info("No transfers in round %d. Converged.", round_num)
                break

        self.logger.info("Finished orchestration | total_hops=%d | total_bytes=%d", total_hops, total_bytes)

        return total_hops, total_bytes, node_stats