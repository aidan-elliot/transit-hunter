"""Validation-only thresholding, temporal-test metrics, and report-ready figures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class BinaryMetrics:
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    specificity: float
    false_positive_rate: float
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int
    threshold: float


def evaluate_scores(labels: np.ndarray, scores: np.ndarray, threshold: float = 0.5) -> BinaryMetrics:
    """Compute discrimination and operating-point metrics for binary prediction scores."""
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if labels.shape != scores.shape or len(labels) == 0 or len(np.unique(labels)) != 2:
        raise ValueError("Evaluation requires matching non-empty binary labels and scores.")
    if not np.all(np.isfinite(scores)) or not 0 <= threshold <= 1:
        raise ValueError("Scores must be finite and threshold must lie in [0, 1].")
    prediction = (scores >= threshold).astype(int)
    tn, fp, fn, tp = (int(value) for value in confusion_matrix(labels, prediction, labels=[0, 1]).ravel())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return BinaryMetrics(
        roc_auc=float(roc_auc_score(labels, scores)),
        pr_auc=float(average_precision_score(labels, scores)),
        precision=precision,
        recall=recall,
        specificity=specificity,
        false_positive_rate=1 - specificity,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        true_positives=tp,
        threshold=float(threshold),
    )


def threshold_at_recall(labels: np.ndarray, scores: np.ndarray, target_recall: float) -> float:
    """Choose an operating threshold on validation data that reaches target recall."""
    labels, scores = np.asarray(labels, dtype=int), np.asarray(scores, dtype=float)
    _precision, recall, thresholds = precision_recall_curve(labels, scores)
    valid = np.flatnonzero(recall[:-1] >= target_recall)
    if len(valid) == 0:
        raise ValueError("Target recall cannot be reached by these validation scores.")
    # Highest threshold at/above target recall minimizes false positives on validation.
    return float(thresholds[valid[-1]])


def grouped_bootstrap_fpr_difference(
    labels: np.ndarray,
    stage1_scores: np.ndarray,
    stage2_scores: np.ndarray,
    groups: np.ndarray,
    *,
    threshold: float,
    stage2_threshold: float | None = None,
    iterations: int = 1_000,
    seed: int = 4000,
) -> tuple[float, float, float]:
    """Return point estimate and 95% TIC-grouped bootstrap interval for ΔFPR.

    Negative values favour Stage 2 because they mean fewer false positives were accepted.
    """
    labels = np.asarray(labels, dtype=int)
    stage1_scores, stage2_scores, groups = map(np.asarray, (stage1_scores, stage2_scores, groups))
    if not (len(labels) == len(stage1_scores) == len(stage2_scores) == len(groups)):
        raise ValueError("Labels, scores, and groups must have matching lengths.")
    stage2_threshold = threshold if stage2_threshold is None else stage2_threshold
    unique_groups = np.unique(groups)
    rng = np.random.default_rng(seed)

    def difference(indices: np.ndarray) -> float:
        negatives = labels[indices] == 0
        if not np.any(negatives):
            return np.nan
        stage1_fpr = np.mean(stage1_scores[indices][negatives] >= threshold)
        stage2_fpr = np.mean(stage2_scores[indices][negatives] >= stage2_threshold)
        return float(stage2_fpr - stage1_fpr)

    point = difference(np.arange(len(labels)))
    draws = []
    for _ in range(iterations):
        chosen = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == group) for group in chosen])
        value = difference(indices)
        if np.isfinite(value):
            draws.append(value)
    if not draws:
        raise ValueError("Bootstrap samples contained no negative examples.")
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(point), float(low), float(high)


def write_evaluation_figures(labels: np.ndarray, scores: np.ndarray, output_dir: Path, stem: str) -> tuple[Path, Path]:
    """Save ROC and precision-recall curves for one validation/test score vector."""
    output_dir.mkdir(parents=True, exist_ok=True)
    labels, scores = np.asarray(labels, dtype=int), np.asarray(scores, dtype=float)
    fpr, tpr, _ = roc_curve(labels, scores)
    precision, recall, _ = precision_recall_curve(labels, scores)
    roc_path, pr_path = output_dir / f"{stem}_roc.png", output_dir / f"{stem}_pr.png"
    for x, y, xlabel, ylabel, path in (
        (fpr, tpr, "False positive rate", "True positive rate", roc_path),
        (recall, precision, "Recall", "Precision", pr_path),
    ):
        figure, axis = plt.subplots(figsize=(5, 4))
        axis.plot(x, y, linewidth=2)
        axis.set(xlabel=xlabel, ylabel=ylabel, xlim=(0, 1), ylim=(0, 1))
        axis.grid(alpha=0.25)
        figure.tight_layout()
        figure.savefig(path, dpi=160)
        plt.close(figure)
    return roc_path, pr_path


def metrics_dict(metrics: BinaryMetrics) -> dict[str, float | int]:
    """Convert typed metrics to JSON-ready primitive values."""
    return asdict(metrics)
