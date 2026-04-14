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
```
venv/bin/python -m src.main
```
3. Generate comparison plots from `experiment_results.csv` with:
```
MPLCONFIGDIR=/tmp/matplotlib XDG_CACHE_HOME=/tmp/cache venv/bin/python -m src.visualize

```
4. Run `python compare_runtimes.py` to benchmark all selection methods and generate a runtime comparison plot.


## Running Unit Tests
This project uses `pytest` for unit testing. If you are using a virtual environment (recommended), activate it first:

```
source venv/bin/activate
```

To run all tests, use:

```
venv/bin/python -m pytest -v
```

To run a specific test file (for example, `test_proposed.py`):

```
venv/bin/python -m pytest -v tests/test_proposed.py
```

This approach ensures that tests run with the correct Python environment and dependencies, and avoids PYTHONPATH issues.

To run main.py

venv/bin/python -m src.main

## Running Experiments on Chameleon Cloud
To SSH into Chameleon Cloud instance and run experiments, follow these steps:

Ensure private key is downloaded to local machine. For example, key.pem.

Open a terminal on local machine.

Use the following SSH command to connect:

```
ssh -i /Users/vivekrai/Downloads/key.pem cc@129.114.109.220
```

cc is the default username for Chameleon Cloud Ubuntu images.
129.114.109.220 is the floating IP address of your instance.

If need to delete the project instance on server, run this on ssh'd in server:

```
rm -rf /home/cc/your_project_folder
```

Now if you want to upload your files, from the local machine run this on the local machine (not server side):

rsync -av --exclude-from='.gitignore' -e "ssh -i /Users/vivekrai/Downloads/key.pem" . cc@129.114.109.220:/home/cc/your_project_folder

Then run this to craete venv, and download all modules from requirements.txt:

cd ~/your_project_folder
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

To save stuff like outputs from server to local, run this on local:

scp -i /Users/vivekrai/Downloads/key.pem -r cc@129.114.109.220:/home/cc/your_project_folder/plots "/Users/vivekrai/Desktop/CS597 S2/Prototype"


## Project Idea
Efficiently select distributed data sources (nodes) to cover all required features for a prediction task, comparing fast heuristics (greedy, random) with optimal (ILP) selection, and use the selected data for machine learning-based weather prediction.
