import time
import matplotlib.pyplot as plt
from network_env import networkENV
from node import assign_data
from ilp_solver import solve_ilp

# For reproducibility
import random
random.seed(42)

# Parameters
branching_factor = 2
greed_param = 0.5
node_counts = [10, 20, 40, 60, 80, 100]


orchestrator_times = []
ilp_times = []
random_times = []


for num_nodes in node_counts:
    # Setup environment
    env = networkENV(num_nodes=num_nodes, branching_factor=branching_factor)
    assign_data(env.nodes)
    # Orchestrator timing (Greedy)
    random_node = random.choice(env.nodes)
    timestamp = random.choice(list(random_node.timestamps)) if random_node.timestamps else None
    present_modalities = set(random_node.features)
    start = time.time()
    env.orchestrator.handle_request(random_node.node_id, timestamp, present_modalities)
    orchestrator_times.append(time.time() - start)
    # ILP timing
    start = time.time()
    solve_ilp(env.nodes, env.global_features, env.tree, greed_param=greed_param)
    ilp_times.append(time.time() - start)
    # Random method timing
    start = time.time()
    env.orchestrator.handle_request_with_random(present_modalities)
    random_times.append(time.time() - start)

# Plotting
plt.figure(figsize=(8, 5))
plt.plot(node_counts, orchestrator_times, marker='o', label='Orchestrator (Greedy)')
plt.plot(node_counts, ilp_times, marker='s', label='ILP Solver')
plt.plot(node_counts, random_times, marker='^', label='Random Orchestrator')
plt.xlabel('Number of Nodes in Tree')
plt.ylabel('Time to Solve (seconds)')
plt.title('Orchestrator (Greedy) vs ILP vs Random Runtime')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('runtime_comparison.png')
plt.show()
