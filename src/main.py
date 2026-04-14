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
from tqdm import tqdm
from src.environment_tools import random_env, simulate, generate_graph
from src.alg.proposed import proposed_algorithm, proposed_algorithm_fast
from src.alg.random_select import random_algorithm
from src.alg.ilp_solver import solve_ilp
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Load dataset
DATA_PATH = "seattle-weather.csv"
df = pd.read_csv(DATA_PATH)

# Experiment parameters
test_grid = {
    "num_requests_per_node": [10, 100],
    "num_nodes": [10, 20, 50, 100, 200],
    "data_uniformity": [1, 1e2, 1e5],
    "seed": list(range(1, 2)),
    "balanced_tree_branching_factor": [2, 10],
}

TOPOLOGY_TYPE = "balanced_tree"

algorithms = {
    "proposed": proposed_algorithm,
    "proposed_fast": proposed_algorithm_fast,
    "random": random_algorithm,
    "ilp": solve_ilp,
}
algorithm_order = {name: idx for idx, name in enumerate(algorithms.keys())}
RESULTS_DIR = Path("results")


def _build_run_prefix() -> str:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"balanced_tree_algorithm_comparison_{timestamp}"


def _run_experiment(
    num_requests: int,
    num_nodes: int,
    alpha: float,
    seed: int,
    balanced_tree_branching_factor: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    graph = generate_graph(
        num_nodes,
        branching_factor=balanced_tree_branching_factor,
        seed=seed,
    )
    env = random_env(df, graph, alpha=alpha, seed=seed)
    env.requests = env.requests[: num_requests * num_nodes]
    request_rows = [
        {
            "request_idx": req.idx,
            "node_idx": req.node_idx,
            "timestamp": req.timestamp,
            "included_modalities": list(req.included_modalities),
            "needed_modalities": list(req.needed_modalities),
        }
        for req in env.requests
    ]

    simulation_results = {}
    for alg_name, algorithm in algorithms.items():
        simulation_results[alg_name] = simulate(env, algorithm)

    return simulation_results, request_rows


def run_experiments() -> None:
    results = []
    run_prefix = _build_run_prefix()
    total_jobs = (
        len(test_grid["num_requests_per_node"])
        * len(test_grid["num_nodes"])
        * len(test_grid["data_uniformity"])
        * len(test_grid["seed"])
        * len(test_grid["balanced_tree_branching_factor"])
    )

    start_time = time.time()
    futures = {}

    with ProcessPoolExecutor(max_workers=4) as executor:
        with tqdm(
            total=total_jobs,
            desc="Running Experiments",
            unit="job",
            mininterval=0.1,
        ) as pbar:
            pbar.refresh()

            for num_requests in test_grid["num_requests_per_node"]:
                for num_nodes in test_grid["num_nodes"]:
                    for alpha in test_grid["data_uniformity"]:
                        for seed in test_grid["seed"]:
                            for balanced_tree_branching_factor in test_grid[
                                "balanced_tree_branching_factor"
                            ]:
                                future = executor.submit(
                                    _run_experiment,
                                    num_requests,
                                    num_nodes,
                                    alpha,
                                    seed,
                                    balanced_tree_branching_factor,
                                )
                                futures[future] = (
                                    num_requests,
                                    num_nodes,
                                    alpha,
                                    seed,
                                    balanced_tree_branching_factor,
                                )

            for future in as_completed(futures):
                (
                    num_requests,
                    num_nodes,
                    alpha,
                    seed,
                    balanced_tree_branching_factor,
                ) = futures[future]
                simulation_results, request_rows = future.result()

                for alg_name, sim_result in simulation_results.items():
                    for req in request_rows:
                        req_result = sim_result["results"].get(req["request_idx"], {})
                        selected_nodes = req_result.get("selected_nodes", [])
                        modality_assignment = req_result.get("modality_assignment", {})
                        results.append(
                            {
                                "algorithm": alg_name,
                                "num_requests": num_requests,
                                "num_nodes": num_nodes,
                                "data_uniformity": alpha,
                                "seed": seed,
                                "topology_type": TOPOLOGY_TYPE,
                                "balanced_tree_branching_factor": (
                                    balanced_tree_branching_factor
                                ),
                                "request_idx": req["request_idx"],
                                "node_idx": req["node_idx"],
                                "timestamp": req["timestamp"],
                                "included_modalities": req["included_modalities"],
                                "needed_modalities": req["needed_modalities"],
                                "selected_nodes": selected_nodes,
                                "modality_assignment": modality_assignment,
                                "cost": req_result.get("cost"),
                                "successful_calculation": req_result.get(
                                    "successful_calculation"
                                ),
                                "missing_modalities": req_result.get(
                                    "missing_modalities"
                                ),
                                "time_taken": sim_result.get("time_taken"),
                                "fairness_index": sim_result.get("fairness_index"),
                                "successful_calculation_overall": sim_result.get(
                                    "successful_calculation_overall"
                                ),
                                "failed_calculation_count": sim_result.get(
                                    "failed_calculation_count"
                                ),
                                "failed_calculations": sim_result.get(
                                    "failed_calculations"
                                ),
                            }
                        )
                pbar.update(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / f"{run_prefix}_experiment_results.csv"
    test_grid_path = RESULTS_DIR / f"{run_prefix}_test_grid.txt"
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df["algorithm_order"] = results_df["algorithm"].map(algorithm_order)
        results_df = results_df.sort_values(
            by=[
                "num_requests",
                "num_nodes",
                "data_uniformity",
                "seed",
                "topology_type",
                "balanced_tree_branching_factor",
                "request_idx",
                "algorithm_order",
            ],
            kind="stable",
        ).drop(columns=["algorithm_order"])

    experiment_config = {
        **test_grid,
        "topology_type": TOPOLOGY_TYPE,
    }

    results_df.to_csv(csv_path, index=False)

    with open(test_grid_path, "w") as f:
        f.write("Experiment Test Grid\n")
        f.write(json.dumps(experiment_config, indent=2) + "\n\n")
        f.write("Algorithms Tested\n")
        f.write(json.dumps(list(algorithms.keys()), indent=2) + "\n")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Experiment complete. Results saved to {csv_path}.")
    print(f"Test grid saved to {test_grid_path}.")
    print(f"Total experiment time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")


if __name__ == "__main__":
    run_experiments()
