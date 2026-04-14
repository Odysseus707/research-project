from __future__ import annotations

import typing as t

import networkx as nx
import numpy as np
import pandas as pd
import time

from .system import Env, Node, Request

if t.TYPE_CHECKING:
    from numpy.random import Generator


def create_rng(seed: Generator | int | None = None) -> Generator:
    match seed:
        case np.random.Generator():
            return seed
        case int():
            return np.random.default_rng(seed)
        case None:
            return np.random.default_rng()
        case _:
            raise ValueError("Illegal value for argument `seed`.")


def generate_modality_mask(num_modalities, rng, decay_probs=[1.0, 0.5, 0.1, 0.01]):
    mask = np.zeros(num_modalities, dtype=int)
    remaining = set(range(num_modalities))
    for p in decay_probs:
        if not remaining:
            break
        idx = rng.choice(list(remaining))
        if rng.random() < p:
            mask[idx] = 1
            remaining.remove(idx)
    return mask


def _generate_partition_masks(
    num_nodes: int,
    num_modalities: int,
    rng,
) -> dict[int, np.ndarray]:
    masks = {
        client: generate_modality_mask(num_modalities, rng)
        for client in range(num_nodes)
    }

    # Ensure every modality is supported by at least one partition.
    for modality_idx in range(num_modalities):
        if any(mask[modality_idx] == 1 for mask in masks.values()):
            continue
        client_idx = int(rng.integers(num_nodes))
        masks[client_idx][modality_idx] = 1

    return masks


def _choose_duplicate_clients(
    eligible_clients: list[int],
    primary_client: int,
    rng,
    duplicate_prob: float,
) -> list[int]:
    duplicate_clients = []
    for client in eligible_clients:
        if client == primary_client:
            continue
        if rng.random() < duplicate_prob:
            duplicate_clients.append(client)
    return duplicate_clients


def partition_dataset(
    dataset: pd.DataFrame,
    num_nodes: int,
    alpha: float = 1e5,
    # time_alpha: float,
    # modality_alpha: float,
    seed: Generator | int | None = None,
) -> dict[int, pd.DataFrame]:
    rng = create_rng(seed)
    modalities = [col for col in dataset.columns if col not in ("date", "weather")]
    partitions = {client: pd.DataFrame(dataset["date"]) for client in range(num_nodes)}
    duplicate_prob = 0.35

    for client in partitions:
        for m in modalities:
            partitions[client][m] = pd.Series(dtype=float)

    partition_masks = _generate_partition_masks(
        num_nodes=num_nodes,
        num_modalities=len(modalities),
        rng=rng,
    )

    for m_idx, modality in enumerate(modalities):
        eligible_clients = [
            client for client, mask in partition_masks.items() if mask[m_idx] == 1
        ]
        modality_probs = rng.dirichlet([alpha] * len(eligible_clients))

        for row_idx, row in enumerate(dataset.itertuples()):
            primary_client = int(rng.choice(eligible_clients, p=modality_probs))
            assigned_clients = [primary_client]
            assigned_clients.extend(
                _choose_duplicate_clients(
                    eligible_clients=eligible_clients,
                    primary_client=primary_client,
                    rng=rng,
                    duplicate_prob=duplicate_prob,
                )
            )

            value = getattr(row, modality)
            for client_idx in assigned_clients:
                partitions[client_idx].loc[row_idx, modality] = value

    return partitions


def generate_graph(
    num_nodes: int,
    branching_factor: int = 2,
    seed: int = None,
):
    if num_nodes < 1:
        raise ValueError("num_nodes must be at least 1.")
    if branching_factor < 2:
        raise ValueError("branching_factor must be at least 2.")

    # Legacy non-tree topology branches were intentionally removed so the
    # experiment suite always evaluates balanced trees only.
    height = 0
    graph = nx.balanced_tree(branching_factor, height)
    while graph.number_of_nodes() < num_nodes:
        height += 1
        graph = nx.balanced_tree(branching_factor, height)

    return _resize_graph(graph, num_nodes)


def _resize_graph(graph: nx.Graph, num_nodes: int, root: int = 0) -> nx.Graph:
    if graph.number_of_nodes() == num_nodes:
        return graph

    if root not in graph:
        root = next(iter(graph.nodes()))

    bfs_order = list(nx.bfs_tree(graph, source=root).nodes())
    selected_nodes = bfs_order[:num_nodes]
    resized = graph.subgraph(selected_nodes).copy()
    mapping = {node: idx for idx, node in enumerate(selected_nodes)}
    return nx.relabel_nodes(resized, mapping)


def create_tree(g: nx.Graph, orchestrator_idx: int | None = None):
    if orchestrator_idx is None:
        orchestrator_idx = 0

    tree = nx.bfs_tree(g, source=orchestrator_idx)

    for node in tree.nodes():
        if node == orchestrator_idx:
            tree.nodes[node]["type"] = "orchestrator"
        elif tree.out_degree(node) == 0:
            tree.nodes[node]["type"] = "worker"
        else:
            tree.nodes[node]["type"] = "forwarder"

    return tree


def get_modalities_at_timestamp(node: Node, timestamp) -> set[str]:
    node_df = node.data
    row = node_df[node_df["date"] == timestamp]
    if row.empty:
        return set()
    return set(row[node.modalities].dropna(axis=1, how="all").columns)


def generate_request(env: Env, num_requests_per_node: int = 2):
    requests = []
    idx = 0
    rng = create_rng()
    for node in env.nodes:
        available_timestamps = (
            node.timestamps
        )  # Use property: only timestamps with at least one modality present
        for _ in range(num_requests_per_node):
            if len(available_timestamps) == 0:
                continue
            timestamp = rng.choice(available_timestamps)
            present_modalities = get_modalities_at_timestamp(node, timestamp)
            included_modalities = present_modalities
            req = Request(
                idx=idx,
                node_idx=node.idx,
                timestamp=timestamp,
                included_modalities=included_modalities,
                calculation_type="weather",
            )
            requests.append(req)
            idx += 1
    return requests


def random_env(
    dataset: pd.DataFrame,
    graph: nx.Graph,
    alpha: float = 1e5,
    seed: Generator | int | None = None,
) -> Env:
    rng = create_rng(seed)
    tree = create_tree(graph)

    worker_node_ids = filter(
        lambda node: tree.nodes[node]["type"] == "worker",
        tree.nodes(),
    )
    worker_node_ids = list(worker_node_ids)

    num_workers = len(worker_node_ids)
    if num_workers < 2:
        raise ValueError(
            f"random_env: At least 2 worker nodes are required, but got {num_workers}. Check your graph topology and node labeling."
        )

    node_partitioned_data = partition_dataset(
        dataset, num_nodes=num_workers, alpha=alpha
    )

    worker_id_to_dataset_id = {
        worker_id: dataset_id
        for (dataset_id, worker_id) in zip(
            node_partitioned_data.keys(), worker_node_ids
        )
    }

    workers: list[Node] = []
    for worker_id in worker_node_ids:
        dataset_id = worker_id_to_dataset_id[worker_id]
        worker_data = node_partitioned_data[dataset_id]
        workers.append(
            Node(
                idx=worker_id,
                data=worker_data,
            )
        )

    sample_data = next(iter(node_partitioned_data.values()))
    timestamps = sample_data.date.tolist()
    modalities = sample_data.columns.tolist()
    for non_modality in ("date", "weather"):
        try:
            modalities.remove(non_modality)
        except ValueError:
            pass

    # Generate requests for the environment
    env = Env(
        nodes=workers,
        topo=tree,
        timestamps=timestamps,
        modalities=modalities,
    )
    env.requests = generate_request(env)
    return env


def compute_cost(
    env: Env,
    request: Request,
    modality_assignment: dict[str, int] | None = None,
    selected_nodes: list[int] | None = None,
) -> float:
    """
    Compute the total communication cost for fulfilling a request.

    This is designed to match the ILP objective as closely as possible:
    each needed modality is charged exactly once, using the node that is
    assigned to provide that modality.

    Example:
    If a request needs {"wind", "temp_max"} and the assignment is
    {"wind": 4, "temp_max": 9}, then the total cost is:
    hops(4) * weight("wind") + hops(9) * weight("temp_max")

    This is different from the older scheme, which charged every selected
    node for every needed modality and could overcount the true transfer cost.

    If no explicit modality assignment is provided, this falls back to the
    cheapest eligible selected node for each modality. That keeps the metric
    aligned with the objective even for algorithms that only return a node set.
    """
    modality_assignment = modality_assignment or {}
    selected_nodes = selected_nodes or []

    total_cost = 0.0
    if modality_assignment:
        for modality in request.needed_modalities:
            node_idx = modality_assignment.get(modality)
            if node_idx is None:
                continue
            hops = env.shortest_paths.get(node_idx, 1)
            weight = env.modalities_data_size.get(modality, 1.0)
            total_cost += hops * weight
        return total_cost

    if not selected_nodes:
        return total_cost

    selected_node_ids = set(selected_nodes)
    for modality in request.needed_modalities:
        best_cost = None
        for node in env.nodes:
            if node.idx not in selected_node_ids:
                continue
            present_modalities = get_modalities_at_timestamp(node, request.timestamp)
            if modality not in present_modalities:
                continue
            hops = env.shortest_paths.get(node.idx, 1)
            weight = env.modalities_data_size.get(modality, 1.0)
            candidate_cost = hops * weight
            if best_cost is None or candidate_cost < best_cost:
                best_cost = candidate_cost
        if best_cost is not None:
            total_cost += best_cost
    return total_cost


def compute_fairness(env: Env, all_selected_nodes: list[list[int]]) -> float:
    """
    Compute the fairness of node selection across all requests using Jain's index.
    Returns 1.0 if all nodes are selected equally often, less if selection is uneven.
    """
    node_selection_counts = {node.idx: 0 for node in env.nodes}
    for selected in all_selected_nodes:
        for node_idx in selected:
            if node_idx in node_selection_counts:
                node_selection_counts[node_idx] += 1
    selection_array = np.array(list(node_selection_counts.values()))
    numerator = selection_array.sum() ** 2
    denominator = len(selection_array) * (selection_array**2).sum()
    return 1.0 if denominator == 0 else numerator / denominator


def compute_successful_calculation(
    env: Env, request: Request, selected_nodes: list[int]
) -> tuple[bool, set[str]]:
    """
    Check if the selected nodes together provide all needed modalities for the request at the required timestamp.
    Returns True if all needed modalities are present, False otherwise.
    """
    gathered_modalities = set(request.included_modalities)
    selected_node_ids = set(selected_nodes)
    for node in env.nodes:
        if node.idx in selected_node_ids:
            gathered_modalities |= get_modalities_at_timestamp(node, request.timestamp)
    needed = request.needed_modalities
    missing = needed - gathered_modalities
    return len(missing) == 0, missing


def compute_qos(env: Env, request: Request, selected_nodes: list[int]) -> bool:
    success, _ = compute_successful_calculation(env, request, selected_nodes)
    return success


def simulate(env: Env, algorithm):
    results = {}
    start_time = time.time()
    alg_output = algorithm(env)
    elapsed_time = time.time() - start_time
    success_list = []
    failed_calculations = []
    # Extract all selected_nodes directly from alg_output for fairness computation
    all_selected_nodes = [
        output.get("selected_nodes", []) for output in alg_output.values()
    ]
    for request in env.requests:
        output = alg_output.get(request.idx, {})
        selected_nodes = output.get("selected_nodes", [])
        modality_assignment = output.get("modality_assignment", {})
        cost_val = compute_cost(
            env,
            request,
            modality_assignment=modality_assignment,
            selected_nodes=selected_nodes,
        )
        success, missing_modalities = compute_successful_calculation(
            env, request, selected_nodes
        )
        success_list.append(success)
        if not success:
            failed_calculations.append(
                {
                    "request_idx": request.idx,
                    "node_idx": request.node_idx,
                    "timestamp": request.timestamp,
                    "missing_modalities": sorted(missing_modalities),
                }
            )
        results[request.idx] = {
            "selected_nodes": selected_nodes,
            "modality_assignment": modality_assignment,
            "cost": cost_val,
            "successful_calculation": success,
            "missing_modalities": sorted(missing_modalities),
        }
    fairness_index = compute_fairness(env, all_selected_nodes)
    return {
        "results": results,
        "time_taken": elapsed_time,
        "fairness_index": fairness_index,
        "successful_calculation_overall": (
            sum(success_list) / len(success_list) if success_list else 0.0
        ),
        "failed_calculations": failed_calculations,
        "failed_calculation_count": len(failed_calculations),
    }
