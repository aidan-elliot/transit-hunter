"""Resumable target-specific construction of the frozen real SPOC dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from transit_hunter.data import build_sample_from_arrays
from transit_hunter.download import load_tic_arrays_with_sectors

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/processed/spoc_2min_v1"
MANIFEST = OUTPUT / "samples_manifest.csv"


def main() -> None:
    records = pd.read_csv(ROOT / "data/metadata/split_assignments.csv", dtype={"toi": str})
    if len(records) != 1812 or not records["toi"].is_unique:
        raise ValueError("Expected the frozen 1,812-row eligible split population.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    completed: dict[str, dict[str, object]] = {}
    if MANIFEST.exists():
        completed = {
            str(row["toi"]): row
            for row in pd.read_csv(MANIFEST, dtype={"toi": str}).to_dict("records")
        }
    remaining = records.loc[~records["toi"].isin(completed)].copy()
    print(f"Resuming with {len(completed)} complete; {len(remaining)} TOIs remaining.", flush=True)
    for tic_index, (tid, tic_rows) in enumerate(remaining.groupby("tid", sort=True), start=1):
        try:
            time, flux, sectors = load_tic_arrays_with_sectors(int(tid), ROOT / "data/raw")
            load_error = None
        except Exception as error:  # noqa: BLE001 - every acquisition failure is manifested.
            load_error = f"{type(error).__name__}: {error}"
        for _, row in tic_rows.iterrows():
            toi = str(row["toi"])
            if load_error is not None:
                result = {
                    "toi": toi,
                    "tid": int(tid),
                    "split": row["split"],
                    "status": "failed",
                    "sample_path": "",
                    "error": load_error,
                }
            else:
                try:
                    path, metadata = build_sample_from_arrays(
                        toi=toi,
                        time=time,
                        flux=flux,
                        sector_labels=sectors,
                        output_dir=OUTPUT,
                        metadata={
                            "tid": int(tid),
                            "split": row["split"],
                            "label": int(row["label"]),
                            "disposition": row["tfopwg_disp"],
                        },
                    )
                    result = {
                        "toi": toi,
                        "tid": int(tid),
                        "split": row["split"],
                        "status": "built",
                        "sample_path": str(path.relative_to(ROOT)),
                        "error": "",
                        "candidate_period": metadata["candidate"]["period"],
                        "candidate_snr": metadata["candidate"]["snr"],
                        "input_points": metadata["input_points"],
                        "retained_points": metadata["retained_points"],
                    }
                except Exception as error:  # noqa: BLE001 - every processing failure is manifested.
                    result = {
                        "toi": toi,
                        "tid": int(tid),
                        "split": row["split"],
                        "status": "failed",
                        "sample_path": "",
                        "error": f"{type(error).__name__}: {error}",
                    }
            completed[toi] = result
        pd.DataFrame(completed.values()).sort_values("toi", kind="stable").to_csv(
            MANIFEST, index=False
        )
        if tic_index % 10 == 0:
            built = sum(row["status"] == "built" for row in completed.values())
            print(
                f"TIC groups processed: {tic_index}; TOIs built: {built}/{len(completed)}",
                flush=True,
            )
    print(pd.read_csv(MANIFEST)["status"].value_counts().to_string(), flush=True)


if __name__ == "__main__":
    main()
