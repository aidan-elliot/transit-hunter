import pandas as pd

from transit_hunter.eligibility import eligibility_summary, evaluate_eligibility


def test_eligibility_requires_coverage_and_finite_ephemeris() -> None:
    labels = pd.DataFrame(
        {
            "toi": ["1.01", "2.01", "3.01", "4.01"],
            "tid": [1, 2, 3, 4],
            "pl_orbper": [3.0, None, 5.0, 4.0],
            "pl_tranmid": [100.0, 101.0, None, 102.0],
            "label": [1, 0, 0, 1],
        }
    )
    coverage = pd.DataFrame(
        {
            "toi": ["1.01", "2.01", "3.01", "4.01"],
            "tid": [1, 2, 3, 4],
            "coverage_status": ["available", "available", "available", "not_found"],
        }
    )

    result = evaluate_eligibility(labels, coverage)

    assert result["is_eligible"].tolist() == [True, False, False, False]
    assert "tid" in result and "tid_x" not in result and "tid_y" not in result
    assert eligibility_summary(result) == {
        "coverage_not_found": 1,
        "eligible": 1,
        "invalid_or_missing_orbital_period": 1,
        "invalid_or_missing_transit_midpoint": 1,
    }
