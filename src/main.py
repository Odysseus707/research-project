"""
# The `main.py` file should not be in the `src/` directory.
for num_requests in [10, 100, 1000, ...]:
    for num_nodes in [10, 20, 30, ...]:
        for data_uniformity in [0.1, 0.2, ...]:
            for seed in [1, 2, 3, ...]:
                rng = create_rng(seed)
                env = create_env(rng)
                for alg in [proposed_algorithm, random_algorithm]:
                    simulate(env, alg)

"""
