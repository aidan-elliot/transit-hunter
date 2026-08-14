"""Checkpointed, bounded-concurrency SPOC coverage audit."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from transit_hunter.coverage import search_spoc_coverage
from transit_hunter.eligibility import evaluate_eligibility

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "data/interim/coverage_tic_checkpoint.csv"


def query(tic_id: int) -> dict[str, object]:
    last_error = "unknown query failure"
    for attempt in range(4):
        try:
            return {"tid": tic_id, **search_spoc_coverage(tic_id), "error": ""}
        except Exception as error:  # noqa: BLE001 - remote failures must be recorded.
            last_error = f"{type(error).__name__}: {error}"
            if attempt < 3:
                time.sleep(2 ** (attempt + 1))
    return {
        "tid": tic_id,
        "coverage_status": "query_error",
        "product_count": 0,
        "sectors": "",
        "error": last_error,
    }


def main() -> None:
    labels_path = ROOT / "data/metadata/labels_snapshot.csv"
    labels = pd.read_csv(labels_path, dtype={"toi": str})
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    completed: dict[int, dict[str, object]] = {}
    if CHECKPOINT.exists():
        for row in pd.read_csv(CHECKPOINT).to_dict("records"):
            if row["coverage_status"] != "query_error":
                completed[int(row["tid"])] = row
    tic_ids = sorted(set(labels["tid"].astype(int)) - set(completed))
    print(f"Resuming with {len(completed)} complete; {len(tic_ids)} TICs remaining.", flush=True)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(query, tic_id): tic_id for tic_id in tic_ids}
        for count, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            completed[int(result["tid"])] = result
            if count % 25 == 0 or count == len(tic_ids):
                pd.DataFrame(completed.values()).sort_values("tid").to_csv(CHECKPOINT, index=False)
                print(
                    f"Completed {len(completed)}/{len(completed) + len(tic_ids) - count}",
                    flush=True,
                )

    tic_frame = pd.DataFrame(completed.values())
    coverage = labels[["toi", "tid"]].merge(tic_frame, on="tid", how="left", validate="many_to_one")
    coverage = coverage.sort_values("toi", kind="stable").reset_index(drop=True)
    metadata_dir = ROOT / "data/metadata"
    coverage.to_csv(metadata_dir / "coverage_manifest.csv", index=False)
    evaluate_eligibility(labels, coverage).to_csv(metadata_dir / "eligible_tois.csv", index=False)
    print(coverage["coverage_status"].value_counts(dropna=False).to_string(), flush=True)


if __name__ == "__main__":
    main()
