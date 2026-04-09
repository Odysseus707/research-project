"""
# The `main.py` file should not be in the `src/` directory.

progress_bar = tqdm(total=...)

for num_requests in [10, 100, 1000, ...]:
    for num_nodes in [10, 20, 30, ...]:
        for data_uniformity in [0.1, 0.2, ...]:
            for seed in [1, 2, 3, ...]:
                rng = create_rng(seed)
                env = create_env(rng)
                for alg in [proposed_algorithm, random_algorithm]:
                    simulate(env, alg)  # TODO: Implement this first.
"""


import pandas as pd
import networkx as nx
from tqdm import tqdm
from src.environment_tools import random_env, simulate, create_rng, generate_graph, create_tree
from src.alg.proposed import proposed_algorithm
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp
import json
import time


# Load dataset
DATA_PATH = "seattle-weather.csv"
df = pd.read_csv(DATA_PATH)

# Experiment parameters
test_grid = {
    "num_requests_per_node": [10, 50, 100],
    "num_nodes": [10, 20, 50, 100, 200],
    "data_uniformity": [1, 1e2, 1e5],
    "seed": list(range(1, 3)),
    "topology_type": [
        "star",
#        "barabasi_albert",
#        "erdos_renyi",
#        "m_ary_tree",
#        "dorogovtsev_goltsev_mendes",
#        "complete",
#        "balanced_tree",
    ],
}

algorithms = {
    "proposed": proposed_algorithm,
    "random": random_algorithm,
    "ilp": solve_ilp,
}

results = []

total = (
    len(test_grid["num_requests_per_node"])
    * len(test_grid["num_nodes"])
    * len(test_grid["data_uniformity"])
    * len(test_grid["seed"])
    * len(test_grid["topology_type"])
    * len(algorithms)
)

start_time = time.time()
with tqdm(total=total, desc="Experiment Grid") as pbar:
    for num_requests in test_grid["num_requests_per_node"]:
        for num_nodes in test_grid["num_nodes"]:
            for alpha in test_grid["data_uniformity"]:
                for seed in test_grid["seed"]:
                    for topology_type in test_grid["topology_type"]:
                        G = generate_graph(num_nodes, topology_type, seed=seed)
                        tree = create_tree(G)
                        env = random_env(df, G, alpha=alpha, seed=seed)
                        env.requests = env.requests[: num_requests * num_nodes]
                        for alg_name, alg in algorithms.items():
                            sim_result = simulate(env, alg)
                            for req in env.requests:
                                req_result = sim_result["results"].get(req.idx, {})
                                selected_nodes = req_result.get("selected_nodes", [])
                                results.append(
                                    {
                                        "algorithm": alg_name,
                                        "num_requests": num_requests,
                                        "num_nodes": num_nodes,
                                        "data_uniformity": alpha,
                                        "seed": seed,
                                        "topology_type": topology_type,
                                        "request_idx": req.idx,
                                        "node_idx": req.node_idx,
                                        "timestamp": req.timestamp,
                                        "included_modalities": list(
                                            req.included_modalities
                                        ),
                                        "needed_modalities": list(
                                            req.needed_modalities
                                        ),
                                        "selected_nodes": selected_nodes,
                                        "cost": req_result.get("cost"),
                                        "qos": req_result.get("qos"),
                                    }
                                )
                            pbar.update(1)

# Save results to CSV
csv_path = "experiment_results.csv"
with open(csv_path, "w") as f:
    # Write test grid and algorithms info as a header
    f.write("# Experiment Test Grid:\n")
    f.write(json.dumps(test_grid, indent=2) + "\n")
    f.write("# Algorithms Tested:\n")
    f.write(json.dumps(list(algorithms.keys()), indent=2) + "\n\n")
    # Write CSV header and data
    pd.DataFrame(results).to_csv(f, index=False)

end_time = time.time()
elapsed = end_time - start_time
print(f"Experiment complete. Results saved to {csv_path}.")
print(f"Total experiment time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
