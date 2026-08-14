import pandas as pd

from transit_hunter.splits import make_temporal_grouped_split, split_summary


def test_temporal_split_keeps_tics_together_and_uses_latest_group_date() -> None:
    samples = pd.DataFrame(
        {
            "toi": ["1.01", "1.02", "2.01", "3.01", "4.01"],
            "tid": [10, 10, 20, 30, 40],
            "toi_created": ["2020-01-01", "2022-01-01", "2021-01-01", "2023-01-01", "2024-01-01"],
            "label": [1, 0, 1, 0, 1],
        }
    )

    assignments = make_temporal_grouped_split(samples, train_fraction=0.25, validation_fraction=0.50)

    assert assignments.groupby("tid")["split"].nunique().max() == 1
    assert assignments.loc[assignments["tid"] == 10, "split"].unique().tolist() == ["validation"]
    summary = split_summary(assignments)
    assert summary["groups_crossing_partitions"] == 0
    assert set(summary["partitions"]) == {"train", "validation", "test"}
