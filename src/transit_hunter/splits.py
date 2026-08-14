"""Temporal split construction that never separates TOIs from the same TIC."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


def make_temporal_grouped_split(
    samples: pd.DataFrame,
    *,
    group_column: str = "tid",
    time_column: str = "toi_created",
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> pd.DataFrame:
    """Assign chronological train/validation/test partitions by group maximum date.

    A group's latest TOI creation date determines its partition. This conservative rule
    prevents a star that gains a later TOI from leaking across the temporal boundary.
    """
    required = {"toi", group_column, time_column}
    missing = required.difference(samples.columns)
    if missing:
        raise ValueError(f"Samples are missing required columns: {sorted(missing)}")
    if samples["toi"].duplicated().any():
        raise ValueError("TOI identifiers must be unique before splitting.")
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("Split fractions must each be between zero and one.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError(
            "train_fraction + validation_fraction must leave a non-empty test fraction."
        )

    output = samples.copy()
    output[time_column] = pd.to_datetime(output[time_column], errors="coerce", utc=True)
    if output[group_column].isna().any() or output[time_column].isna().any():
        raise ValueError(
            f"{group_column} and {time_column} must be present and parseable for all samples."
        )
    group_dates = (
        output.groupby(group_column, as_index=False)[time_column]
        .max()
        .rename(columns={time_column: "group_latest_labelled_at"})
        .sort_values(["group_latest_labelled_at", group_column], kind="stable")
        .reset_index(drop=True)
    )
    group_count = len(group_dates)
    if group_count < 3:
        raise ValueError(
            "At least three TIC groups are required for train/validation/test partitions."
        )
    train_end = math.floor(group_count * train_fraction)
    validation_end = math.floor(group_count * (train_fraction + validation_fraction))
    if train_end == 0 or validation_end <= train_end or validation_end >= group_count:
        raise ValueError("Fractions do not yield non-empty train, validation, and test partitions.")

    group_dates["split"] = "test"
    group_dates.loc[: train_end - 1, "split"] = "train"
    group_dates.loc[train_end : validation_end - 1, "split"] = "validation"
    output = output.merge(group_dates, on=group_column, how="left", validate="many_to_one")
    return output.sort_values("toi", kind="stable").reset_index(drop=True)


def split_summary(assignments: pd.DataFrame, group_column: str = "tid") -> dict[str, object]:
    """Summarise partitions and fail if a group appears in more than one split."""
    required = {"split", group_column, "toi"}
    missing = required.difference(assignments.columns)
    if missing:
        raise ValueError(f"Assignments are missing required columns: {sorted(missing)}")
    crossing = assignments.groupby(group_column)["split"].nunique()
    if (crossing > 1).any():
        raise ValueError("At least one TIC crosses partitions.")
    summary: dict[str, object] = {"groups_crossing_partitions": 0, "partitions": {}}
    for split, frame in assignments.groupby("split", sort=False):
        details: dict[str, object] = {
            "toi_count": len(frame),
            "tic_count": int(frame[group_column].nunique()),
            "group_latest_start": frame["group_latest_labelled_at"].min().isoformat(),
            "group_latest_end": frame["group_latest_labelled_at"].max().isoformat(),
        }
        if "label" in frame:
            details["class_counts"] = {
                str(key): int(value)
                for key, value in frame["label"].value_counts().sort_index().items()
            }
        summary["partitions"][str(split)] = details
    return summary


def write_split_artifacts(
    assignments: pd.DataFrame, output_dir: Path, group_column: str = "tid"
) -> tuple[Path, Path]:
    """Save assignments and an auditable summary for a frozen eligible population."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assignment_path = output_dir / "split_assignments.csv"
    manifest_path = output_dir / "split_manifest.json"
    assignments.to_csv(assignment_path, index=False)
    manifest_path.write_text(
        json.dumps(split_summary(assignments, group_column), indent=2) + "\n", encoding="utf-8"
    )
    return assignment_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a TIC-grouped temporal split.")
    parser.add_argument(
        "--input", type=Path, required=True, help="Eligible TOI CSV containing toi_created."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/metadata"))
    parser.add_argument("--train-fraction", type=float, default=0.70)
    parser.add_argument("--validation-fraction", type=float, default=0.15)
    args = parser.parse_args()
    samples = pd.read_csv(args.input)
    if "is_eligible" not in samples:
        raise ValueError("Split input must contain the frozen is_eligible decision.")
    eligible = samples["is_eligible"].astype(str).str.lower().isin({"true", "1"})
    samples = samples.loc[eligible].copy()
    assignments = make_temporal_grouped_split(
        samples,
        train_fraction=args.train_fraction,
        validation_fraction=args.validation_fraction,
    )
    assignment_path, manifest_path = write_split_artifacts(assignments, args.output_dir)
    print(f"Wrote {assignment_path} and {manifest_path}")


if __name__ == "__main__":
    main()
