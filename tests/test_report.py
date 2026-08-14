import json

from transit_hunter.report import write_results_summary


def test_results_summary_uses_metrics_and_bootstrap_interval(tmp_path) -> None:
    metrics = {
        "target_recall": 0.9,
        "test": {"pr_auc": 0.8, "roc_auc": 0.9, "recall": 0.9, "precision": 0.7, "false_positive_rate": 0.2},
    }
    stage1, stage2 = tmp_path / "stage1.json", tmp_path / "stage2.json"
    stage1.write_text(json.dumps(metrics), encoding="utf-8")
    stage2.write_text(json.dumps({**metrics, "test": {**metrics["test"], "false_positive_rate": 0.1}}), encoding="utf-8")

    output = write_results_summary(
        stage1_metrics_path=stage1,
        stage2_metrics_path=stage2,
        fpr_difference=(-0.1, -0.2, -0.01),
        output_path=tmp_path / "summary.md",
    )

    assert output.exists()
    assert "-0.100" in output.read_text(encoding="utf-8")
