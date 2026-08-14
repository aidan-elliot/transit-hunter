"""Apply transparent pre-processing eligibility rules before data partitioning."""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COVERAGE_COLUMNS = ("toi", "coverage_status")


def evaluate_eligibility(labels: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    """Attach a deterministic inclusion decision and one exclusion reason to every TOI.

    The function does not query MAST. Coverage must already have been recorded, which
    makes the population selected for training inspectable and repeatable.
    """
    required_labels = {"toi", "tid", "pl_orbper", "pl_tranmid", "label"}
    missing_labels = required_labels.difference(labels.columns)
    missing_coverage = set(REQUIRED_COVERAGE_COLUMNS).difference(coverage.columns)
    if missing_labels or missing_coverage:
        raise ValueError(
            f"Missing labels columns: {sorted(missing_labels)}; "
            f"missing coverage columns: {sorted(missing_coverage)}"
        )
    if labels["toi"].duplicated().any() or coverage["toi"].duplicated().any():
        raise ValueError("TOI identifiers must be unique in labels and coverage tables.")

    output = labels.copy()
    output["toi"] = output["toi"].astype("string")
    coverage = coverage.copy()
    coverage["toi"] = coverage["toi"].astype("string")
    output = output.merge(coverage, on="toi", how="left", validate="one_to_one")
    status = output["coverage_status"].fillna("missing").astype(str)
    period = pd.to_numeric(output["pl_orbper"], errors="coerce")
    midpoint = pd.to_numeric(output["pl_tranmid"], errors="coerce")

    reasons = np.select(
        [
            status.ne("available"),
            ~np.isfinite(period) | period.le(0),
            ~np.isfinite(midpoint),
        ],
        [
            "coverage_" + status,
            "invalid_or_missing_orbital_period",
            "invalid_or_missing_transit_midpoint",
        ],
        default="eligible",
    )
    output["eligibility_reason"] = reasons
    output["is_eligible"] = output["eligibility_reason"].eq("eligible")
    return output.sort_values("toi", kind="stable").reset_index(drop=True)


def eligibility_summary(eligibility: pd.DataFrame) -> dict[str, int]:
    """Return reproducible counts by inclusion/exclusion reason."""
    if "eligibility_reason" not in eligibility:
        raise ValueError("Eligibility table is missing eligibility_reason.")
    return {
        str(reason): int(count)
        for reason, count in eligibility["eligibility_reason"].value_counts().sort_index().items()
    }
