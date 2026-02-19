import pandas as pd
import random
from node import Node
from orchestrator import Orchestrator
from orchestrator import build_graph
import matplotlib.pyplot as plt
import networkx as nx

# Load Seattle dataset
df = pd.read_csv("seattle-weather.csv")

global_features = ["precipitation", "temp_max", "temp_min", "wind"]

n_samples = len(df)
n_nodes = 32

nodes = []

for i in range(n_nodes):
    owned = random.sample(
        global_features,
        random.randint(1, len(global_features))
    )
    nodes.append(Node(i, owned, n_samples))

orch = Orchestrator(nodes, global_features)

d_conn, d_bytes = orch.dumb_strategy()
s_conn, s_bytes = orch.smart_strategy()

p_values = [0.1, 0.2, 0.3, 0.4, 0.5]

costs = []
total_hops_list = []

for p in p_values:
    G = build_graph(n_nodes, p)

    total_bytes, weighted_cost, total_hops = \
        orch.smart_strategy_with_graph(G)

    costs.append(weighted_cost / 1e6)
    total_hops_list.append(total_hops)

print("Dumb Strategy")
print("Connections:", d_conn)
print("Total MB:", d_bytes / 1e6)

print("\nSmart Strategy")
print("Connections:", s_conn)
print("Total MB:", s_bytes / 1e6)

strategies = ["Dumb", "Smart"]
connections = [d_conn, s_conn]
mb_transferred = [d_bytes / 1e6, s_bytes / 1e6]

plt.figure()
plt.bar(strategies, mb_transferred)
plt.title("Total Communication (MB)")
plt.ylabel("MB Transferred")
plt.show()

plt.figure()
plt.bar(strategies, connections)
plt.title("Total Connections")
plt.ylabel("Number of Connections")
plt.show()

plt.figure()
plt.plot(p_values, costs)
plt.xlabel("Erdos-Renyi p")
plt.ylabel("Weighted Communication (MB * hops)")
plt.title("Communication vs Connectivity")
plt.show()

plt.figure()
plt.plot(p_values, total_hops_list)
plt.xlabel("Erdos-Renyi p")
plt.ylabel("Average Hops")
plt.title("Average Hops vs Connectivity")
plt.show()