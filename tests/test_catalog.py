import pandas as pd
import pytest

from transit_hunter.catalog import (
    REQUIRED_COLUMNS,
    audit_catalogue,
    prepare_supervised_catalogue,
    tap_url,
)


def example_catalogue() -> pd.DataFrame:
    rows = [
        ["100.01", 1, "CP"],
        ["100.02", 1, "FP"],
        ["200.01", 2, "FA"],
        ["300.01", 3, "PC"],
        ["400.01", 4, "APC"],
        ["500.01", 5, "KP"],
    ]
    return pd.DataFrame(
        [dict(zip(REQUIRED_COLUMNS, row + [None] * (len(REQUIRED_COLUMNS) - len(row)))) for row in rows]
    )


def test_label_policy_excludes_unresolved_and_known_planets() -> None:
    supervised, known_planets = prepare_supervised_catalogue(example_catalogue())

    assert supervised[["toi", "label"]].values.tolist() == [["100.01", 1], ["100.02", 0], ["200.01", 0]]
    assert known_planets["toi"].tolist() == ["500.01"]


def test_audit_reports_tic_multiplicity_without_treating_it_as_an_error() -> None:
    catalogue = example_catalogue()
    supervised, _ = prepare_supervised_catalogue(catalogue)
    audit = audit_catalogue(catalogue, supervised)

    assert audit["source_toi_unique"] is True
    assert audit["source_tics_with_multiple_tois"] == 1


def test_missing_column_is_rejected() -> None:
    with pytest.raises(ValueError, match="required columns"):
        prepare_supervised_catalogue(example_catalogue().drop(columns="st_rad"))


def test_tap_url_encodes_adql_and_csv_format() -> None:
    url = tap_url("SELECT toi FROM toi")
    assert "format=csv" in url
    assert "SELECT" in url or "SELECT+" in url or "SELECT%20" in url
