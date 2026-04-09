import pandas as pd

from src.environment_tools import partition_dataset


def test_partition_dataset_respects_modality_support():
    dataset = pd.read_csv("seattle-weather.csv").head(25)
    partitions = partition_dataset(dataset, num_nodes=4, seed=123)
    modalities = [col for col in dataset.columns if col not in ("date", "weather")]

    assert len(partitions) == 4

    for partition in partitions.values():
        for modality in modalities:
            assigned_rows = partition[modality].notna()
            if assigned_rows.any():
                pd.testing.assert_series_equal(
                    partition.loc[assigned_rows, modality].reset_index(drop=True),
                    dataset.loc[assigned_rows, modality].reset_index(drop=True),
                    check_names=False,
                )

    for modality in modalities:
        total_assigned = sum(partition[modality].notna().sum() for partition in partitions.values())
        assert total_assigned == dataset[modality].notna().sum()
        assert any(partition[modality].notna().any() for partition in partitions.values())
