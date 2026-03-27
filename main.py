import random
import time
from network_env import networkENV
from node import assign_data

def main():
	# Initialize environment (loads nodes and orchestrator)
	env = networkENV(num_nodes=100, branching_factor=2)
	assign_data(env.nodes)

	# Simulate a request from a random node
	random_node = random.choice(env.nodes)
	# Pick a random timestamp from the node's timestamps
	if random_node.timestamps:
		timestamp = random.choice(list(random_node.timestamps))
	else:
		timestamp = None
	present_modalities = set(random_node.features)

	msg1 = f"Simulating request from node {random_node.node_id} at timestamp {timestamp}"
	print(msg1)
	env.logger.info(msg1)
	start_time = time.time()
	env.orchestrator.handle_request(random_node.node_id, timestamp, present_modalities)
	# Prediction is now handled inside orchestrator.handle_request
	elapsed = time.time() - start_time
	msg2 = f"Request fulfilled in {elapsed:.6f} seconds."
	print(msg2)
	env.logger.info(msg2)

if __name__ == "__main__":
	main()
