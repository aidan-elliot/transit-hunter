"""Query and record SPOC 120-second availability before downloading light curves."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .eligibility import evaluate_eligibility

CoverageSearch = Callable[[int], dict[str, object]]


def search_spoc_coverage(tic_id: int) -> dict[str, object]:
    """Return lightweight SPOC 120-second availability metadata for one TIC.

    Lightkurve is imported lazily so catalogue/split tooling remains usable without
    astronomy dependencies. This performs a metadata query only; it never downloads
    FITS products.
    """
    import lightkurve as lk

    result = lk.search_lightcurve(
        target=f"TIC {tic_id}", mission="TESS", author="SPOC", exptime=120
    )
    product_count = len(result)
    if product_count == 0:
        return {"coverage_status": "not_found", "product_count": 0, "sectors": ""}
    table = result.table.to_pandas()
    mission_values = table.get("mission", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    return {
        "coverage_status": "available",
        "product_count": product_count,
        "sectors": ";".join(sorted(mission_values)),
    }


def build_coverage_manifest(
    labels: pd.DataFrame, search: CoverageSearch = search_spoc_coverage
) -> pd.DataFrame:
    """Query each TIC once and return one availability row per labelled TOI."""
    required = {"toi", "tid"}
    missing = required.difference(labels.columns)
    if missing:
        raise ValueError(f"Labels are missing required columns: {sorted(missing)}")
    if labels["toi"].duplicated().any():
        raise ValueError("TOI identifiers must be unique before querying coverage.")

    tic_results: dict[int, dict[str, object]] = {}
    for tic_id in sorted(labels["tid"].dropna().astype(int).unique()):
        try:
            tic_results[tic_id] = search(tic_id)
        except Exception as error:  # noqa: BLE001 - every per-TIC query failure is an auditable outcome.
            tic_results[tic_id] = {
                "coverage_status": "query_error",
                "product_count": 0,
                "sectors": "",
                "error": f"{type(error).__name__}: {error}",
            }

    requested_at = datetime.now(UTC).isoformat()
    records: list[dict[str, object]] = []
    for row in labels[["toi", "tid"]].itertuples(index=False):
        result = tic_results.get(int(row.tid), {"coverage_status": "missing_tic", "product_count": 0, "sectors": ""})
        records.append(
            {
                "toi": str(row.toi),
                "tid": int(row.tid),
                "coverage_status": str(result.get("coverage_status", "query_error")),
                "product_count": int(result.get("product_count", 0)),
                "sectors": str(result.get("sectors", "")),
                "error": str(result.get("error", "")),
                "queried_at_utc": requested_at,
            }
        )
    return pd.DataFrame(records).sort_values("toi", kind="stable").reset_index(drop=True)


def main() -> None:
    """Create coverage and provisional eligibility CSVs without downloading FITS files."""
    parser = argparse.ArgumentParser(description="Audit SPOC 120-second coverage for a frozen TOI snapshot.")
    parser.add_argument("--labels", type=Path, default=Path("data/metadata/labels_snapshot.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/metadata"))
    args = parser.parse_args()
    labels = pd.read_csv(args.labels)
    coverage = build_coverage_manifest(labels)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    coverage_path = output_dir / "coverage_manifest.csv"
    eligibility_path = output_dir / "eligible_tois.csv"
    coverage.to_csv(coverage_path, index=False)
    evaluate_eligibility(labels, coverage).to_csv(eligibility_path, index=False)
    print(f"Wrote {coverage_path} and {eligibility_path}")


if __name__ == "__main__":
    main()
