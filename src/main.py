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
from src.environment_tools import random_env, simulate, create_rng
from src.alg.proposed import proposed_algorithm
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp
import json


# Load dataset
DATA_PATH = "seattle-weather.csv"
df = pd.read_csv(DATA_PATH)

# Experiment parameters
test_grid = {
    "num_requests_per_node": [10, 50, 100],
    "num_nodes": [10, 20, 50, 100, 200],
    "data_uniformity": [1, 1e2, 1e5],
    "seed": list(range(1, 3)),
}

algorithms = {
    "proposed": proposed_algorithm,
    "random": random_algorithm,
    "ilp": lambda env, reqs: {r.idx: solve_ilp(env) for r in reqs},
}

results = []
total = (
    len(test_grid["num_requests_per_node"])
    * len(test_grid["num_nodes"])
    * len(test_grid["data_uniformity"])
    * len(test_grid["seed"])
    * len(algorithms)
)

with tqdm(total=total, desc="Experiment Grid") as pbar:
    for num_requests in test_grid["num_requests_per_node"]:
        for num_nodes in test_grid["num_nodes"]:
            for alpha in test_grid["data_uniformity"]:
                for seed in test_grid["seed"]:
                    # Create a simple path graph for demo
                    G = nx.path_graph(num_nodes)
                    env = random_env(df, G, alpha=alpha, seed=seed)
                    env.requests = env.requests[: num_requests * num_nodes]
                    for alg_name, alg in algorithms.items():
                        sim_result = simulate(env, alg)
                        results.append(
                            {
                                "algorithm": alg_name,
                                "num_requests": num_requests,
                                "num_nodes": num_nodes,
                                "data_uniformity": alpha,
                                "seed": seed,
                                **sim_result,
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
print(f"Experiment complete. Results saved to {csv_path}.")
