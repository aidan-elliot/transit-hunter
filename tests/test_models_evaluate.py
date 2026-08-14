import numpy as np
import pandas as pd
import pytest

from transit_hunter.evaluate import (
    evaluate_scores,
    grouped_bootstrap_fpr_difference,
    threshold_at_recall,
    write_evaluation_figures,
)
from transit_hunter.models import (
    STAGE2_FEATURES,
    build_two_view_cnn,
    fit_feature_baseline,
    fit_stage2_classifier,
    stage2_feature_frame,
)


def diagnostic_frame(size: int = 40) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(9)
    labels = np.array([0, 1] * (size // 2))
    frame = pd.DataFrame(
        {
            "period": rng.uniform(1, 8, size),
            "duration": rng.uniform(0.03, 0.2, size),
            "depth": 0.002 + labels * 0.01 + rng.normal(0, 0.0005, size),
            "power": 3 + labels * 8 + rng.normal(0, 0.5, size),
            "snr": 3 + labels * 8 + rng.normal(0, 0.5, size),
            "observed_transits": rng.integers(3, 12, size),
            "odd_even_depth_difference": (1 - labels) * 0.004 + rng.normal(0, 0.0002, size),
            "secondary_eclipse_depth": (1 - labels) * 0.003 + rng.normal(0, 0.0002, size),
            "transit_symmetry_difference": (1 - labels) * 0.002 + rng.normal(0, 0.0002, size),
            "sector_to_sector_depth_std": rng.uniform(0, 0.001, size),
        }
    )
    return frame, labels


def test_baseline_and_stage2_fit_and_score() -> None:
    diagnostics, labels = diagnostic_frame()
    baseline = fit_feature_baseline(diagnostics.loc[:, list(STAGE2_FEATURES)], labels)
    stage1_scores = baseline.predict_proba(diagnostics.loc[:, list(STAGE2_FEATURES)])[:, 1]
    stage2 = fit_stage2_classifier(diagnostics, stage1_scores, labels)
    stage2_scores = stage2.predict_proba(stage2_feature_frame(diagnostics, stage1_scores))[:, 1]

    assert stage1_scores.shape == labels.shape
    assert stage2_scores.shape == labels.shape
    assert evaluate_scores(labels, stage2_scores).pr_auc > 0.9


def test_evaluation_threshold_bootstrap_and_figures(tmp_path) -> None:
    labels = np.array([0, 0, 0, 1, 1, 1, 0, 1])
    stage1 = np.array([0.8, 0.7, 0.1, 0.9, 0.8, 0.7, 0.6, 0.9])
    stage2 = np.array([0.3, 0.2, 0.1, 0.9, 0.8, 0.7, 0.2, 0.9])
    groups = np.array([1, 1, 2, 3, 3, 4, 5, 6])
    threshold = threshold_at_recall(labels, stage1, 0.75)
    metrics = evaluate_scores(labels, stage2, threshold)
    point, low, high = grouped_bootstrap_fpr_difference(labels, stage1, stage2, groups, threshold=threshold, iterations=100)
    roc_path, pr_path = write_evaluation_figures(labels, stage2, tmp_path, "stage2")

    assert 0 <= threshold <= 1
    assert metrics.false_positives <= 1
    assert point <= 0
    assert low <= high
    assert roc_path.exists() and pr_path.exists()


def test_cnn_dependency_guard_is_actionable_when_torch_is_unavailable() -> None:
    try:
        import torch  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="PyTorch"):
            build_two_view_cnn()
