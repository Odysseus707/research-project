# Distributed Node Selection & Weather Prediction

## Overview
This project simulates a distributed network of nodes, each holding a subset of weather features (e.g., temperature, wind, precipitation) for various timestamps. The goal is to select a minimal set of nodes to cover all required features for weather prediction, using different selection strategies.

## Main Flow
1. **Network Setup**: The environment (`networkENV`) builds a tree-structured network of nodes, each assigned random features and timestamps.
2. **Data Assignment**: Each node receives real or synthetic weather data for its features and timestamps.
3. **Node Selection**: The orchestrator selects nodes to cover all required features using one of three methods:
	- **Greedy (Algorithmic)**: Selects nodes based on a utility function (features provided vs. hops from root).
	- **Random**: Randomly picks nodes that provide new features until all are covered.
	- **ILP (Optimal)**: Uses Integer Linear Programming to find the smallest set of nodes covering all features.
4. **Weather Prediction**: Selected node data is used by a neural network model to predict the weather label.
5. **Benchmarking**: The runtime of each method is compared and visualized.

## Key Files
- `main.py`: Entry point; runs a sample request and selection.
- `network_env.py`: Sets up the network, nodes, and orchestrator.
- `node.py`: Node class and data assignment utilities.
- `orchestrator.py`: Implements greedy, random, and prediction logic.
- `ilp_solver.py`: ILP-based optimal node selection.
- `compare_runtimes.py`: Benchmarks and plots runtimes for all methods.
- `model.py`, `train_model.py`: Neural network model for weather prediction.

## How to Run
1. Install requirements (see your environment setup).
2. Run `python main.py` to simulate a single request.
3. Run `python compare_runtimes.py` to benchmark all selection methods and generate a runtime comparison plot.

## Project Idea
Efficiently select distributed data sources (nodes) to cover all required features for a prediction task, comparing fast heuristics (greedy, random) with optimal (ILP) selection, and use the selected data for machine learning-based weather prediction.