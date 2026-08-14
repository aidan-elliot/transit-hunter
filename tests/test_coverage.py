import pandas as pd

from transit_hunter.coverage import build_coverage_manifest


def test_coverage_queries_each_tic_once_and_expands_results_to_tois() -> None:
    calls: list[int] = []

    def search(tic_id: int) -> dict[str, object]:
        calls.append(tic_id)
        return {"coverage_status": "available", "product_count": 2, "sectors": "TESS Sector 1"}

    labels = pd.DataFrame({"toi": ["1.01", "1.02", "2.01"], "tid": [10, 10, 20]})
    manifest = build_coverage_manifest(labels, search=search)

    assert calls == [10, 20]
    assert manifest["toi"].tolist() == ["1.01", "1.02", "2.01"]
    assert manifest["product_count"].tolist() == [2, 2, 2]


def test_coverage_records_query_errors_without_dropping_tois() -> None:
    labels = pd.DataFrame({"toi": ["1.01"], "tid": [10]})

    def failing_search(_: int) -> dict[str, object]:
        raise RuntimeError("MAST unavailable")

    manifest = build_coverage_manifest(labels, search=failing_search)

    assert manifest.loc[0, "coverage_status"] == "query_error"
    assert "RuntimeError" in manifest.loc[0, "error"]
