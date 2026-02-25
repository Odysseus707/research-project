import networkx as nx
import matplotlib.pyplot as plt
import random

from node import create_nodes
from greedy_orchestrator import GreedyOrchestrator


random.seed(42)

n_nodes = 20
n_timestamps = 200  # reduce for speed (can increase later)

global_timestamps = set(range(n_timestamps))
global_features = ["precipitation", "temp_max", "temp_min", "wind"]

p_values = [0.1, 0.2, 0.3, 0.4, 0.5]
greed_values = [0.0, 0.25, 0.5, 0.75, 1.0]

hop_results = {}
byte_results = {}
coverage_results = {}

for g in greed_values:

    hop_curve = []
    byte_curve = []
    coverage_curve = []

    for p in p_values:

        nodes = create_nodes(
            n_nodes,
            global_features,
            global_timestamps
        )

        # ensure connected graph
        while True:
            G = nx.erdos_renyi_graph(n_nodes, p)
            if nx.is_connected(G):
                break

        orch = GreedyOrchestrator(
            nodes,
            global_features,
            global_timestamps
        )

        total_hops, total_bytes, coverage = orch.run(G, g)

        hop_curve.append(total_hops)
        byte_curve.append(total_bytes / 1e6)
        coverage_curve.append(coverage)

    hop_results[g] = hop_curve
    byte_results[g] = byte_curve
    coverage_results[g] = coverage_curve


# Plot Total Hops
plt.figure()
for g in greed_values:
    plt.plot(p_values, hop_results[g])
plt.xlabel("Erdos-Renyi p")
plt.ylabel("Total Hops")
plt.title("Total Hops vs p")
plt.legend([f"g={g}" for g in greed_values])
plt.show()


# Plot Total Bytes
plt.figure()
for g in greed_values:
    plt.plot(p_values, byte_results[g])
plt.xlabel("Erdos-Renyi p")
plt.ylabel("Total Data (MB)")
plt.title("Total Data vs p")
plt.legend([f"g={g}" for g in greed_values])
plt.show()


# Plot Coverage
plt.figure()
for g in greed_values:
    plt.plot(p_values, coverage_results[g])
plt.xlabel("Erdos-Renyi p")
plt.ylabel("Coverage Ratio")
plt.title("Global Coverage vs p")
plt.legend([f"g={g}" for g in greed_values])
plt.show()