"""Train and evaluate the frozen real-data baseline, CNN, and diagnostic stage."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from transit_hunter.data import read_sample
from transit_hunter.evaluate import (
    evaluate_scores,
    grouped_bootstrap_fpr_difference,
    threshold_at_recall,
    write_evaluation_figures,
)
from transit_hunter.models import (
    STAGE2_FEATURES,
    fit_feature_baseline,
    fit_stage2_classifier,
    predict_two_view_cnn,
    stage2_feature_frame,
    train_two_view_cnn,
)
from transit_hunter.provenance import write_run_manifest
from transit_hunter.report import write_results_summary

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/spoc_2min_v1"
RUN = ROOT / "reports/runs/real_spoc_2min_v1"
SEEDS = (4000, 4001, 4002)
TARGET_RECALL = 0.90


def normalize_view(values: np.ndarray) -> np.ndarray:
    median = np.median(values, axis=1, keepdims=True)
    scale = 1.4826 * np.median(np.abs(values - median), axis=1, keepdims=True)
    scale = np.where(scale > np.finfo(np.float32).eps, scale, 1.0)
    return ((values - median) / scale).astype(np.float32)


def load_frame() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    manifest = pd.read_csv(DATA / "samples_manifest.csv", dtype={"toi": str})
    if len(manifest) != 1812 or not manifest["status"].eq("built").all():
        raise ValueError("Experiments require all 1,812 frozen samples to be built.")
    rows, global_views, local_views = [], [], []
    for record in manifest.itertuples(index=False):
        sample = read_sample(ROOT / Path(record.sample_path))
        rows.append(
            {**sample["metadata"], **sample["diagnostics"], "sample_path": record.sample_path}
        )
        global_views.append(sample["global_view"])
        local_views.append(sample["local_view"])
    frame = pd.DataFrame(rows)
    forbidden = {"pl_orbper", "pl_tranmid", "catalogue_period", "catalogue_midpoint"}
    if forbidden.intersection(frame.columns):
        raise ValueError("Catalogue ephemerides appeared in the formal experiment frame.")
    return frame, normalize_view(np.stack(global_views)), normalize_view(np.stack(local_views))


def inner_split(
    indices: np.ndarray, labels: np.ndarray, groups: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    splitter = GroupShuffleSplit(n_splits=20, test_size=0.15, random_state=seed)
    for train_rel, validation_rel in splitter.split(indices, labels[indices], groups[indices]):
        train_idx, validation_idx = indices[train_rel], indices[validation_rel]
        if len(np.unique(labels[train_idx])) == 2 and len(np.unique(labels[validation_idx])) == 2:
            return train_idx, validation_idx
    raise ValueError("Could not create a binary, TIC-grouped inner validation split.")


def train_cnn(
    global_views: np.ndarray,
    local_views: np.ndarray,
    labels: np.ndarray,
    train_idx: np.ndarray,
    validation_idx: np.ndarray,
    seed: int,
):
    return train_two_view_cnn(
        global_views[train_idx],
        local_views[train_idx],
        labels[train_idx],
        global_views[validation_idx],
        local_views[validation_idx],
        labels[validation_idx],
        epochs=40,
        batch_size=64,
        learning_rate=1e-3,
        patience=6,
        seed=seed,
    )


def metrics_payload(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, object]:
    return asdict(evaluate_scores(labels, scores, threshold))


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    frame, global_views, local_views = load_frame()
    labels = frame["label"].to_numpy(dtype=int)
    groups = frame["tid"].to_numpy()
    train_idx = np.flatnonzero(frame["split"].eq("train"))
    validation_idx = np.flatnonzero(frame["split"].eq("validation"))
    test_idx = np.flatnonzero(frame["split"].eq("test"))
    diagnostics = list(STAGE2_FEATURES)

    # Baseline: BLS-derived diagnostics only; threshold fixed on validation.
    baseline = fit_feature_baseline(frame.loc[train_idx, diagnostics], labels[train_idx], seed=4000)
    baseline_validation = baseline.predict_proba(frame.loc[validation_idx, diagnostics])[:, 1]
    baseline_threshold = threshold_at_recall(
        labels[validation_idx], baseline_validation, TARGET_RECALL
    )
    baseline_test = baseline.predict_proba(frame.loc[test_idx, diagnostics])[:, 1]
    baseline_metrics = {
        "target_recall": TARGET_RECALL,
        "threshold_selected_on_validation": baseline_threshold,
        "validation": metrics_payload(
            labels[validation_idx], baseline_validation, baseline_threshold
        ),
        "test": metrics_payload(labels[test_idx], baseline_test, baseline_threshold),
    }
    joblib.dump(baseline, RUN / "baseline_model.joblib")
    (RUN / "baseline_metrics.json").write_text(json.dumps(baseline_metrics, indent=2) + "\n")

    # Three-seed Stage 1 validation study. Test remains unscored until selection.
    seed_rows, seed_models = [], {}
    for seed in SEEDS:
        model, history = train_cnn(
            global_views, local_views, labels, train_idx, validation_idx, seed
        )
        validation_scores = predict_two_view_cnn(
            model, global_views[validation_idx], local_views[validation_idx]
        )
        score = float(average_precision_score(labels[validation_idx], validation_scores))
        seed_rows.append({"seed": seed, "validation_pr_auc": score, "epochs": len(history)})
        seed_models[seed] = (model, validation_scores)
        history.to_csv(RUN / f"stage1_history_seed_{seed}.csv", index=False)
        torch.save(model.state_dict(), RUN / f"stage1_seed_{seed}.pt")
    seed_table = pd.DataFrame(seed_rows).sort_values("seed")
    seed_table.to_csv(RUN / "stage1_seed_stability.csv", index=False)
    selected_seed = int(
        seed_table.sort_values(["validation_pr_auc", "seed"], ascending=[False, True]).iloc[0][
            "seed"
        ]
    )
    stage1, stage1_validation = seed_models[selected_seed]
    stage1_threshold = threshold_at_recall(labels[validation_idx], stage1_validation, TARGET_RECALL)

    # TIC-grouped outer cross-fitting; each outer model uses a grouped inner split
    # for early stopping, so held-out scores never tune their own model.
    oof_scores = np.full(len(train_idx), np.nan)
    outer = GroupKFold(n_splits=3)
    for fold, (outer_train_rel, held_out_rel) in enumerate(
        outer.split(train_idx, labels[train_idx], groups[train_idx]), start=1
    ):
        outer_train = train_idx[outer_train_rel]
        held_out = train_idx[held_out_rel]
        fit_idx, inner_validation = inner_split(outer_train, labels, groups, 5000 + fold)
        fold_model, fold_history = train_cnn(
            global_views, local_views, labels, fit_idx, inner_validation, 5000 + fold
        )
        oof_scores[held_out_rel] = predict_two_view_cnn(
            fold_model, global_views[held_out], local_views[held_out]
        )
        fold_history.to_csv(RUN / f"stage1_crossfit_fold_{fold}_history.csv", index=False)
    if not np.all(np.isfinite(oof_scores)):
        raise RuntimeError("Cross-fitting did not produce every Stage 1 training score.")

    # Stage 2 is fitted before the sealed test is scored.
    stage2 = fit_stage2_classifier(frame.loc[train_idx], oof_scores, labels[train_idx], seed=4000)
    stage2_validation = stage2.predict_proba(
        stage2_feature_frame(frame.loc[validation_idx], stage1_validation)
    )[:, 1]
    stage2_threshold = threshold_at_recall(labels[validation_idx], stage2_validation, TARGET_RECALL)
    diagnostics_only = fit_feature_baseline(
        frame.loc[train_idx, diagnostics], labels[train_idx], seed=4000
    )
    diagnostics_validation = diagnostics_only.predict_proba(frame.loc[validation_idx, diagnostics])[
        :, 1
    ]
    diagnostics_threshold = threshold_at_recall(
        labels[validation_idx], diagnostics_validation, TARGET_RECALL
    )

    # Model and threshold choices are fixed above; score the sealed test once.
    stage1_test = predict_two_view_cnn(stage1, global_views[test_idx], local_views[test_idx])
    stage2_test = stage2.predict_proba(stage2_feature_frame(frame.loc[test_idx], stage1_test))[:, 1]
    diagnostics_test = diagnostics_only.predict_proba(frame.loc[test_idx, diagnostics])[:, 1]
    stage1_metrics = {
        "target_recall": TARGET_RECALL,
        "selected_seed_on_validation": selected_seed,
        "threshold": stage1_threshold,
        "validation": metrics_payload(labels[validation_idx], stage1_validation, stage1_threshold),
        "test": metrics_payload(labels[test_idx], stage1_test, stage1_threshold),
    }
    stage2_metrics = {
        "target_recall": TARGET_RECALL,
        "threshold": stage2_threshold,
        "validation": metrics_payload(labels[validation_idx], stage2_validation, stage2_threshold),
        "test": metrics_payload(labels[test_idx], stage2_test, stage2_threshold),
    }
    diagnostics_metrics = {
        "target_recall": TARGET_RECALL,
        "threshold": diagnostics_threshold,
        "validation": metrics_payload(
            labels[validation_idx], diagnostics_validation, diagnostics_threshold
        ),
        "test": metrics_payload(labels[test_idx], diagnostics_test, diagnostics_threshold),
    }
    (RUN / "stage1_metrics.json").write_text(json.dumps(stage1_metrics, indent=2) + "\n")
    (RUN / "stage2_metrics.json").write_text(json.dumps(stage2_metrics, indent=2) + "\n")
    (RUN / "diagnostics_only_metrics.json").write_text(
        json.dumps(diagnostics_metrics, indent=2) + "\n"
    )
    torch.save(stage1.state_dict(), RUN / "stage1_selected.pt")
    joblib.dump(stage2, RUN / "stage2_model.joblib")
    joblib.dump(diagnostics_only, RUN / "diagnostics_only_model.joblib")

    difference = grouped_bootstrap_fpr_difference(
        labels[test_idx],
        stage1_test,
        stage2_test,
        groups[test_idx],
        threshold=stage1_threshold,
        stage2_threshold=stage2_threshold,
        iterations=2_000,
        seed=4000,
    )
    comparison = {
        "stage2_minus_stage1_fpr": difference,
        "selected_on_validation_only": True,
        "stage2_training_stage1_scores": "3-fold TIC-grouped out-of-fold CNN scores",
    }
    (RUN / "stage_comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
    scores = frame.loc[:, ["toi", "tid", "split", "label", "disposition"]].copy()
    scores["stage1_score"] = np.nan
    scores["stage2_score"] = np.nan
    scores.loc[train_idx, "stage1_score"] = oof_scores
    scores.loc[validation_idx, "stage1_score"] = stage1_validation
    scores.loc[test_idx, "stage1_score"] = stage1_test
    scores.loc[validation_idx, "stage2_score"] = stage2_validation
    scores.loc[test_idx, "stage2_score"] = stage2_test
    scores.to_csv(RUN / "stage_scores.csv", index=False)
    for stem, values in (
        ("baseline_test", baseline_test),
        ("stage1_test", stage1_test),
        ("stage2_test", stage2_test),
    ):
        write_evaluation_figures(labels[test_idx], values, RUN, stem)
    write_results_summary(
        stage1_metrics_path=RUN / "stage1_metrics.json",
        stage2_metrics_path=RUN / "stage2_metrics.json",
        fpr_difference=difference,
        output_path=ROOT / "reports/results_summary.md",
    )
    write_run_manifest(
        RUN,
        command="scripts/run_real_experiments.py",
        config_paths=[ROOT / "configs/experiment.yaml", ROOT / "configs/models.yaml"],
        input_paths=[
            ROOT / "data/metadata/dataset_manifest.json",
            DATA / "samples_manifest.csv",
        ],
        seed=4000,
    )
    print(json.dumps({"selected_seed": selected_seed, **comparison}, indent=2))


if __name__ == "__main__":
    main()
