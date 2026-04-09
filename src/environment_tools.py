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


def generate_graph(num_nodes: int, topology_type: str, seed: int = None):
    if num_nodes < 1:
        raise ValueError("num_nodes must be at least 1.")

    if topology_type == "star":
        return nx.star_graph(max(0, num_nodes - 1))
    elif topology_type == "barabasi_albert":
        # m must be >= 1 and < num_nodes
        m = min(2, max(1, num_nodes // 10))
        return nx.barabasi_albert_graph(num_nodes, m, seed=seed)
    elif topology_type == "erdos_renyi":
        # p chosen so graph is likely connected but not complete
        p = min(0.1 + 10 / num_nodes, 0.5)
        return nx.erdos_renyi_graph(num_nodes, p, seed=seed)
    elif topology_type == "m_ary_tree":
        m = min(3, max(2, num_nodes // 20))
        h = 0
        graph = nx.balanced_tree(m, h)
        while graph.number_of_nodes() < num_nodes:
            h += 1
            graph = nx.balanced_tree(m, h)
        return _resize_graph(graph, num_nodes)
    elif topology_type == "dorogovtsev_goltsev_mendes":
        generation = 0
        graph = nx.dorogovtsev_goltsev_mendes_graph(generation)
        while graph.number_of_nodes() < num_nodes:
            generation += 1
            graph = nx.dorogovtsev_goltsev_mendes_graph(generation)
        return _resize_graph(graph, num_nodes)
    elif topology_type == "complete":
        return nx.complete_graph(num_nodes)
    elif topology_type == "balanced_tree":
        r = min(3, max(2, num_nodes // 20))
        h = 0
        graph = nx.balanced_tree(r, h)
        while graph.number_of_nodes() < num_nodes:
            h += 1
            graph = nx.balanced_tree(r, h)
        return _resize_graph(graph, num_nodes)
    else:
        raise ValueError(f"Unknown topology_type: {topology_type}")


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


def compute_cost(env: Env, selected_nodes: list[int], request: Request) -> float:
    """
    Compute the total communication cost for fulfilling a request.
    For each selected node, multiplies the number of hops from the root to the node
    by the data size weight for each needed modality, summed over all selected nodes and modalities.
    """
    total_cost = 0.0
    for node_idx in selected_nodes:
        hops = env.shortest_paths.get(node_idx, 1)
        for m in request.needed_modalities:
            w = env.modalities_data_size.get(m, 1.0)
            total_cost += hops * w
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
        cost_val = compute_cost(env, selected_nodes, request)
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
