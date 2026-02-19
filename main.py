import pandas as pd
import random
from node import Node
from node import create_nodes
from orchestrator import Orchestrator
from orchestrator import build_graph
from greedy_orchestrator import GreedyOrchestrator
import matplotlib.pyplot as plt
import networkx as nx

# Load Seattle dataset
df = pd.read_csv("seattle-weather.csv")

global_features = ["precipitation", "temp_max", "temp_min", "wind"]

n_samples = len(df)
n_nodes = 32

p_values = [0.1, 0.2, 0.3, 0.4, 0.5]
greed_values = [0.0, 0.25, 0.5, 0.75, 1.0]

hop_results = {}
byte_results = {}

for g in greed_values:
    hop_curve = []
    byte_curve = []

    for p in p_values:
        nodes = create_nodes(n_nodes, global_features, n_samples)
        G = nx.erdos_renyi_graph(n_nodes, p)

        orch = GreedyOrchestrator(nodes, global_features)

        total_hops, total_bytes, _ = orch.run(G, g)

        hop_curve.append(total_hops)
        byte_curve.append(total_bytes / 1e6)

    hop_results[g] = hop_curve
    byte_results[g] = byte_curve

for g in greed_values:
    plt.plot(p_values, hop_results[g])

plt.xlabel("Erdos-Renyi p")
plt.ylabel("Total Hops")
plt.title("Total Hops vs p")
plt.legend([f"g={g}" for g in greed_values])
plt.show()

for g in greed_values:
    plt.plot(p_values, byte_results[g])

plt.xlabel("Erdos-Renyi p")
plt.ylabel("Total Data (MB)")
plt.title("Total Data Transmission vs p")
plt.legend([f"g={g}" for g in greed_values])
plt.show()