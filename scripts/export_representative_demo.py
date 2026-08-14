"""Export a fair, static light-curve sample for the public Transit Hunter demo.

Run this only after the real ``data/processed/spoc_2min_v1`` release has been
rebuilt in the supported x64 Python environment. It selects 13 sealed-test
examples in the same broad outcome proportions as the recorded Stage 2 test
result: 8 correct predictions and 5 errors.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "reports/runs/real_spoc_2min_v1/stage_scores.csv"
SAMPLES = ROOT / "data/processed/spoc_2min_v1"
OUTPUT = ROOT / "public/data/representative_cases.json"
STAGE_1_THRESHOLD = 0.34505078196525574
STAGE_2_THRESHOLD = 0.3425295851252444

# 13 cases: 5 TP, 3 TN, 3 FP, 2 FN. This yields 8/13 correct (61.5%),
# matching the 175/285 (61.4%) Stage 2 sealed-test accuracy to rounding.
QUOTAS = {"TP": 5, "TN": 3, "FP": 3, "FN": 2}


def outcome(row: dict[str, str]) -> str:
    positive = int(row["label"]) == 1
    predicted = float(row["stage2_score"]) >= STAGE_2_THRESHOLD
    if positive and predicted:
        return "TP"
    if not positive and not predicted:
        return "TN"
    if not positive and predicted:
        return "FP"
    return "FN"


def sample_path(toi: str) -> Path:
    return SAMPLES / f"toi_{toi}.npz"


def main() -> None:
    with SCORES.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["split"] == "test"]

    grouped = {key: [] for key in QUOTAS}
    for row in rows:
        grouped[outcome(row)].append(row)

    rng = random.Random(4000)
    selected: list[dict[str, str]] = []
    for key, quota in QUOTAS.items():
        candidates = sorted(grouped[key], key=lambda row: float(row["toi"]))
        if len(candidates) < quota:
            raise RuntimeError(f"Only {len(candidates)} {key} cases available; need {quota}.")
        selected.extend(rng.sample(candidates, quota))
    rng.shuffle(selected)

    cases = []
    missing = []
    for row in selected:
        path = sample_path(row["toi"])
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))
            continue
        with np.load(path, allow_pickle=False) as data:
            cases.append(
                {
                    "toi": row["toi"],
                    "disposition": row["disposition"],
                    "label": int(row["label"]),
                    "stage1Score": round(float(row["stage1_score"]), 6),
                    "stage2Score": round(float(row["stage2_score"]), 6),
                    "stage1Threshold": STAGE_1_THRESHOLD,
                    "stage2Threshold": STAGE_2_THRESHOLD,
                    "outcome": outcome(row),
                    "globalView": np.asarray(data["global_view"], dtype=float).round(7).tolist(),
                    "localView": np.asarray(data["local_view"], dtype=float).round(7).tolist(),
                }
            )
    if missing:
        preview = ", ".join(missing[:3])
        raise FileNotFoundError(f"Representative samples are missing ({len(missing)} total): {preview}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "description": "Deterministic, outcome-stratified sample from the sealed Stage 2 test set.",
        "seed": 4000,
        "quotas": QUOTAS,
        "testOutcomeCounts": {"TP": 101, "TN": 74, "FP": 70, "FN": 40},
        "cases": cases,
    }
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(cases)} representative cases to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
