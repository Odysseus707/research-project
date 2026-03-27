import argparse
import os
import random

import matplotlib.pyplot as plt
import networkx as nx

from node import create_nodes
from greedy_orchestrator import GreedyOrchestrator


def build_args():
    parser = argparse.ArgumentParser(description="Run node selection simulation.")
    parser.add_argument("--lambda-value", type=float, default=0.7, help="Lambda in [0,1] for utility.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--nodes", type=int, default=32, help="Number of nodes.")
    parser.add_argument("--timestamps", type=int, default=400, help="Number of timestamps.")
    parser.add_argument("--edge-probability", type=float, default=0.3, help="ER graph edge probability.")
    parser.add_argument("--quiet", action="store_true", help="Disable verbose orchestrator console logs.")
    parser.add_argument("--log-path", default="node_transfers_log.txt", help="Path to orchestration log file.")
    return parser.parse_args()


def ensure_connected_graph(n_nodes, edge_probability):
    while True:
        graph = nx.erdos_renyi_graph(n_nodes, edge_probability)
        if nx.is_connected(graph):
            return graph


def main():
    args = build_args()
    if not (0.0 <= args.lambda_value <= 1.0):
        raise ValueError("--lambda-value must be between 0 and 1.")

    random.seed(args.seed)

    global_timestamps = set(range(args.timestamps))
    global_features = ["precipitation", "temp_max", "temp_min", "wind"]

    nodes = create_nodes(args.nodes, global_features, global_timestamps)
    graph = ensure_connected_graph(args.nodes, args.edge_probability)

    orchestrator = GreedyOrchestrator(nodes, global_features, global_timestamps)
    total_hops, total_bytes, node_stats = orchestrator.run(
        graph,
        args.lambda_value,
        verbose=not args.quiet,
        log_file=args.log_path,
    )

    print(f"\nLambda: {args.lambda_value}")
    print(f"Total Hops: {total_hops}")
    print(f"Total Bytes: {total_bytes}")
    print(f"Transfer log saved to {args.log_path}")

    os.makedirs("results", exist_ok=True)

    station_ids = list(node_stats.keys())
    bytes_received = [node_stats[i]["bytes_received"] / 1e3 for i in station_ids]
    bytes_sent = [node_stats[i]["bytes_sent"] / 1e3 for i in station_ids]
    hops_used = [node_stats[i]["hops_used"] for i in station_ids]

    plt.figure(figsize=(12, 5))
    plt.bar(station_ids, bytes_received, color="skyblue")
    plt.xlabel("Station ID")
    plt.ylabel("Bytes Received (KB)")
    plt.title(f"Bytes Received per Station (p={args.edge_probability}, lambda={args.lambda_value})")
    plt.tight_layout()
    plt.savefig("results/bytes_received_per_station.png")
    plt.show()

    plt.figure(figsize=(12, 5))
    plt.bar(station_ids, bytes_sent, color="lightgreen")
    plt.xlabel("Station ID")
    plt.ylabel("Bytes Sent (KB)")
    plt.title(f"Bytes Sent per Station (p={args.edge_probability}, lambda={args.lambda_value})")
    plt.tight_layout()
    plt.savefig("results/bytes_sent_per_station.png")
    plt.show()

    plt.figure(figsize=(12, 5))
    plt.bar(station_ids, hops_used, color="salmon")
    plt.xlabel("Station ID")
    plt.ylabel("Total Hops Used")
    plt.title(f"Hops per Station (p={args.edge_probability}, lambda={args.lambda_value})")
    plt.tight_layout()
    plt.savefig("results/hops_per_station.png")
    plt.show()


if __name__ == "__main__":
    main()