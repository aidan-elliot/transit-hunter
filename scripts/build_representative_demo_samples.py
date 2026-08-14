"""Build only the real SPOC samples required by the public demo export.

This intentionally runs on a compatible x64 runner. It downloads the selected
TIC light curves, writes temporary ignored NPZ samples, and leaves the compact
browser data export to ``export_representative_demo.py``.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

from export_representative_demo import QUOTAS, SCORES, outcome
from transit_hunter.data import build_sample_from_arrays
from transit_hunter.download import load_tic_arrays_with_sectors

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data/metadata/split_assignments.csv"
OUTPUT = ROOT / "data/processed/spoc_2min_v1"
RAW = ROOT / "data/raw/representative_demo"


def select_rows() -> list[dict[str, str]]:
    with SCORES.open(newline="", encoding="utf-8") as handle:
        test_rows = [row for row in csv.DictReader(handle) if row["split"] == "test"]
    grouped = {key: [] for key in QUOTAS}
    for row in test_rows:
        grouped[outcome(row)].append(row)

    rng = random.Random(4000)
    selected = []
    for key, quota in QUOTAS.items():
        candidates = sorted(grouped[key], key=lambda row: float(row["toi"]))
        selected.extend(rng.sample(candidates, quota))
    rng.shuffle(selected)
    return selected


def main() -> None:
    with SPLITS.open(newline="", encoding="utf-8") as handle:
        assignments = {row["toi"]: row for row in csv.DictReader(handle)}

    selected = select_rows()
    by_tic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for score_row in selected:
        assignment = assignments.get(score_row["toi"])
        if assignment is None:
            raise KeyError(f"TOI {score_row['toi']} is absent from the frozen split assignments.")
        by_tic[assignment["tid"]].append(assignment)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for index, (tid, rows) in enumerate(sorted(by_tic.items()), start=1):
        print(f"[{index}/{len(by_tic)}] Downloading TIC {tid}", flush=True)
        time, flux, sectors = load_tic_arrays_with_sectors(int(tid), RAW)
        for row in rows:
            build_sample_from_arrays(
                toi=row["toi"],
                time=time,
                flux=flux,
                sector_labels=sectors,
                output_dir=OUTPUT,
                metadata={
                    "tid": int(row["tid"]),
                    "split": row["split"],
                    "label": int(row["label"]),
                    "disposition": row["tfopwg_disp"],
                },
            )
    print(f"Built {len(selected)} representative samples.")


if __name__ == "__main__":
    main()
