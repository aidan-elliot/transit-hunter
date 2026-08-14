"""Grouped temporal experiment orchestration for baseline and Stage 2 models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from .evaluate import (
    evaluate_scores,
    grouped_bootstrap_fpr_difference,
    threshold_at_recall,
    write_evaluation_figures,
)
from .models import fit_feature_baseline, fit_stage2_classifier, save_model, stage2_feature_frame
from .provenance import write_run_manifest


@dataclass(frozen=True)
class TrainedExperiment:
    model_path: Path
    metrics_path: Path
    threshold: float


@dataclass(frozen=True)
class TwoStageExperiment:
    stage1_model_path: Path
    stage2_model_path: Path
    summary_path: Path


def _partition(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    subset = frame.loc[frame["split"].eq(split)].copy()
    if subset.empty:
        raise ValueError(f"No rows belong to the {split!r} split.")
    return subset


def cross_fitted_feature_scores(
    features: pd.DataFrame, labels: pd.Series | np.ndarray, groups: pd.Series | np.ndarray, *, folds: int = 5, seed: int = 4000
) -> np.ndarray:
    """Generate TIC-grouped out-of-fold scores for honest Stage 2 training inputs."""
    labels, groups = np.asarray(labels, dtype=int), np.asarray(groups)
    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        raise ValueError("Cross-fitting requires at least two TIC groups.")
    splitter = GroupKFold(n_splits=min(folds, len(unique_groups)))
    scores = np.full(len(features), np.nan, dtype=float)
    for train_index, held_out_index in splitter.split(features, labels, groups):
        model = fit_feature_baseline(features.iloc[train_index], labels[train_index], seed=seed)
        scores[held_out_index] = model.predict_proba(features.iloc[held_out_index])[:, 1]
    if not np.all(np.isfinite(scores)):
        raise RuntimeError("Cross-fitting did not produce a score for every training sample.")
    return scores


def train_feature_experiment(
    frame: pd.DataFrame,
    *,
    feature_columns: list[str],
    output_dir: Path,
    config_paths: list[Path],
    input_paths: list[Path],
    target_recall: float = 0.90,
    seed: int = 4000,
) -> TrainedExperiment:
    """Fit a baseline on train, choose a threshold on validation, and score sealed test."""
    required = {"label", "split", *feature_columns}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Experiment frame is missing columns: {sorted(missing)}")
    train, validation, test = (_partition(frame, split) for split in ("train", "validation", "test"))
    model = fit_feature_baseline(train.loc[:, feature_columns], train["label"], seed=seed)
    validation_scores = model.predict_proba(validation.loc[:, feature_columns])[:, 1]
    threshold = threshold_at_recall(validation["label"], validation_scores, target_recall)
    test_scores = model.predict_proba(test.loc[:, feature_columns])[:, 1]
    metrics = {
        "target_recall": target_recall,
        "threshold_selected_on_validation": threshold,
        "validation": asdict(evaluate_scores(validation["label"], validation_scores, threshold)),
        "test": asdict(evaluate_scores(test["label"], test_scores, threshold)),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path, metrics_path = output_dir / "model.joblib", output_dir / "metrics.json"
    save_model(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_run_manifest(
        output_dir,
        command="train_feature_experiment",
        config_paths=config_paths,
        input_paths=input_paths,
        seed=seed,
    )
    return TrainedExperiment(model_path=model_path, metrics_path=metrics_path, threshold=threshold)


def train_stage2_experiment(
    frame: pd.DataFrame,
    *,
    stage1_score_column: str,
    output_dir: Path,
    config_paths: list[Path],
    input_paths: list[Path],
    target_recall: float = 0.90,
    seed: int = 4000,
) -> TrainedExperiment:
    """Train/evaluate Stage 2 with its Stage 1 scores fixed before the test split."""
    required = {"label", "split", stage1_score_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Stage 2 frame is missing columns: {sorted(missing)}")
    train, validation, test = (_partition(frame, split) for split in ("train", "validation", "test"))
    model = fit_stage2_classifier(train, train[stage1_score_column], train["label"], seed=seed)
    validation_features = stage2_feature_frame(validation, validation[stage1_score_column])
    validation_scores = model.predict_proba(validation_features)[:, 1]
    threshold = threshold_at_recall(validation["label"], validation_scores, target_recall)
    test_scores = model.predict_proba(stage2_feature_frame(test, test[stage1_score_column]))[:, 1]
    metrics = {
        "target_recall": target_recall,
        "threshold_selected_on_validation": threshold,
        "validation": asdict(evaluate_scores(validation["label"], validation_scores, threshold)),
        "test": asdict(evaluate_scores(test["label"], test_scores, threshold)),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path, metrics_path = output_dir / "stage2_model.joblib", output_dir / "stage2_metrics.json"
    save_model(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_run_manifest(
        output_dir,
        command="train_stage2_experiment",
        config_paths=config_paths,
        input_paths=input_paths,
        seed=seed,
    )
    return TrainedExperiment(model_path=model_path, metrics_path=metrics_path, threshold=threshold)


def train_two_stage_feature_experiment(
    frame: pd.DataFrame,
    *,
    stage1_feature_columns: list[str],
    group_column: str,
    output_dir: Path,
    config_paths: list[Path],
    input_paths: list[Path],
    target_recall: float = 0.90,
    seed: int = 4000,
) -> TwoStageExperiment:
    """Run the primary ablation with cross-fitted Stage 1 scores and a sealed test set.

    The Stage 1 model is fit on training rows only. Its training scores are produced
    out-of-fold by TIC, preventing Stage 2 from learning from in-sample Stage 1 errors.
    Validation scores choose separate equal-recall operating thresholds; temporal test
    records are scored only after both models and thresholds are fixed.
    """
    required = {"label", "split", group_column, *stage1_feature_columns}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Two-stage frame is missing columns: {sorted(missing)}")
    train, validation, test = (_partition(frame, split) for split in ("train", "validation", "test"))
    train_features = train.loc[:, stage1_feature_columns]
    train_stage1_scores = cross_fitted_feature_scores(train_features, train["label"], train[group_column], seed=seed)
    stage1 = fit_feature_baseline(train_features, train["label"], seed=seed)
    validation_stage1_scores = stage1.predict_proba(validation.loc[:, stage1_feature_columns])[:, 1]
    test_stage1_scores = stage1.predict_proba(test.loc[:, stage1_feature_columns])[:, 1]
    stage1_threshold = threshold_at_recall(validation["label"], validation_stage1_scores, target_recall)

    stage2 = fit_stage2_classifier(train, train_stage1_scores, train["label"], seed=seed)
    validation_stage2_scores = stage2.predict_proba(stage2_feature_frame(validation, validation_stage1_scores))[:, 1]
    test_stage2_scores = stage2.predict_proba(stage2_feature_frame(test, test_stage1_scores))[:, 1]
    stage2_threshold = threshold_at_recall(validation["label"], validation_stage2_scores, target_recall)
    stage1_test_metrics = evaluate_scores(test["label"], test_stage1_scores, stage1_threshold)
    stage2_test_metrics = evaluate_scores(test["label"], test_stage2_scores, stage2_threshold)
    difference = grouped_bootstrap_fpr_difference(
        test["label"], test_stage1_scores, test_stage2_scores, test[group_column],
        threshold=stage1_threshold, stage2_threshold=stage2_threshold, iterations=1_000, seed=seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    stage1_path, stage2_path = output_dir / "stage1_model.joblib", output_dir / "stage2_model.joblib"
    save_model(stage1, stage1_path)
    save_model(stage2, stage2_path)
    stage1_metrics_path, stage2_metrics_path = output_dir / "stage1_metrics.json", output_dir / "stage2_metrics.json"
    stage1_metrics_path.write_text(json.dumps({"target_recall": target_recall, "threshold": stage1_threshold, "test": asdict(stage1_test_metrics)}, indent=2) + "\n", encoding="utf-8")
    stage2_metrics_path.write_text(json.dumps({"target_recall": target_recall, "threshold": stage2_threshold, "test": asdict(stage2_test_metrics)}, indent=2) + "\n", encoding="utf-8")
    (output_dir / "stage_comparison.json").write_text(json.dumps({"stage2_minus_stage1_fpr": difference}, indent=2) + "\n", encoding="utf-8")
    write_evaluation_figures(test["label"], test_stage1_scores, output_dir, "stage1_test")
    write_evaluation_figures(test["label"], test_stage2_scores, output_dir, "stage2_test")
    write_run_manifest(
        output_dir,
        command="train_two_stage_feature_experiment",
        config_paths=config_paths,
        input_paths=input_paths,
        seed=seed,
    )
    return TwoStageExperiment(stage1_model_path=stage1_path, stage2_model_path=stage2_path, summary_path=output_dir / "stage_comparison.json")
