"""Generate report-ready tables and figures from the sealed real experiment."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.calibration import calibration_curve
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from transit_hunter.data import read_sample
from transit_hunter.models import build_two_view_cnn
from transit_hunter.report import write_results_summary

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reports/runs/real_spoc_2min_v1"
DATA = ROOT / "data/processed/spoc_2min_v1"


def metric(name: str) -> dict[str, object]:
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main() -> None:
    splits = pd.read_csv(ROOT / "data/metadata/split_assignments.csv", dtype={"toi": str})
    split_table = (
        splits.groupby("split")
        .agg(
            toi_count=("toi", "size"),
            tic_count=("tid", "nunique"),
            positive_count=("label", "sum"),
            earliest_group_date=("group_latest_labelled_at", "min"),
            latest_group_date=("group_latest_labelled_at", "max"),
        )
        .reset_index()
    )
    split_table["negative_count"] = split_table["toi_count"] - split_table["positive_count"]
    split_table.to_csv(RUN / "split_summary.csv", index=False)

    dates = pd.to_datetime(splits["toi_created"], utc=True)
    fig, axis = plt.subplots(figsize=(9, 4))
    for label, color in ((0, "#d95f02"), (1, "#1b9e77")):
        values = dates[splits["label"].eq(label)]
        axis.hist(values, bins=35, alpha=0.65, label="CP" if label else "FP/FA", color=color)
    axis.set(
        xlabel="TOI creation date", ylabel="Eligible TOIs", title="Frozen eligible TOI timeline"
    )
    axis.legend()
    fig.tight_layout()
    fig.savefig(RUN / "catalogue_timeline.png", dpi=180)
    plt.close(fig)

    baseline, stage1, stage2, diagnostics = (
        metric("baseline_metrics.json"),
        metric("stage1_metrics.json"),
        metric("stage2_metrics.json"),
        metric("diagnostics_only_metrics.json"),
    )
    ablation_rows = []
    for model_name, payload in (
        ("BLS/diagnostic baseline", baseline),
        ("Stage 1 global/local CNN", stage1),
        ("Stage 2 diagnostics only", diagnostics),
        ("Stage 1 score + Stage 2 diagnostics", stage2),
    ):
        ablation_rows.append({"model": model_name, **payload["test"]})
    pd.DataFrame(ablation_rows).to_csv(RUN / "ablation_table.csv", index=False)
    pd.DataFrame(
        [
            {
                "model": name,
                "validation_threshold": payload.get(
                    "threshold", payload.get("threshold_selected_on_validation")
                ),
                "validation_recall": payload["validation"]["recall"],
                "test_recall": payload["test"]["recall"],
                "test_false_positives": payload["test"]["false_positives"],
                "test_false_positive_rate": payload["test"]["false_positive_rate"],
            }
            for name, payload in (("baseline", baseline), ("stage1", stage1), ("stage2", stage2))
        ]
    ).to_csv(RUN / "operating_points.csv", index=False)

    scores = pd.read_csv(RUN / "stage_scores.csv", dtype={"toi": str})
    test = scores.loc[scores["split"].eq("test")].copy()
    for name, payload in (("stage1", stage1), ("stage2", stage2)):
        threshold = payload["threshold"]
        predicted = test[f"{name}_score"].ge(threshold).astype(int)
        fig, axis = plt.subplots(figsize=(4.5, 4))
        ConfusionMatrixDisplay(
            confusion_matrix(test["label"], predicted, labels=[0, 1]),
            display_labels=["FP/FA", "CP"],
        ).plot(ax=axis, colorbar=False)
        axis.set_title(f"{name.title()} sealed temporal test")
        fig.tight_layout()
        fig.savefig(RUN / f"{name}_test_confusion.png", dpi=180)
        plt.close(fig)

    fig, axis = plt.subplots(figsize=(5, 4))
    for name in ("stage1", "stage2"):
        observed, predicted = calibration_curve(
            test["label"], test[f"{name}_score"], n_bins=10, strategy="quantile"
        )
        axis.plot(predicted, observed, marker="o", label=name.title())
    axis.plot([0, 1], [0, 1], "--", color="black", alpha=0.6)
    axis.set(
        xlabel="Mean predicted probability", ylabel="Observed CP fraction", title="Test reliability"
    )
    axis.legend()
    fig.tight_layout()
    fig.savefig(RUN / "stage_reliability.png", dpi=180)
    plt.close(fig)

    histories = sorted(RUN.glob("stage1_history_seed_*.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for path in histories:
        history = pd.read_csv(path)
        seed = path.stem.rsplit("_", 1)[-1]
        axes[0].plot(history["epoch"], history["train_loss"], label=seed)
        axes[1].plot(history["epoch"], history["validation_pr_auc"], label=seed)
    axes[0].set(xlabel="Epoch", ylabel="Training loss")
    axes[1].set(xlabel="Epoch", ylabel="Validation PR-AUC")
    axes[1].legend(title="Seed")
    fig.tight_layout()
    fig.savefig(RUN / "stage1_learning_curves.png", dpi=180)
    plt.close(fig)

    subgroup_rows = []
    for disposition, subset in test.loc[test["label"].eq(0)].groupby("disposition"):
        subgroup_rows.append(
            {
                "disposition": disposition,
                "count": len(subset),
                "stage1_accepted": int(subset["stage1_score"].ge(stage1["threshold"]).sum()),
                "stage2_accepted": int(subset["stage2_score"].ge(stage2["threshold"]).sum()),
            }
        )
    pd.DataFrame(subgroup_rows).to_csv(RUN / "negative_subgroup_results.csv", index=False)

    # Representative errors selected deterministically by score extremity.
    false_positive = test.loc[
        test["label"].eq(0) & test["stage2_score"].ge(stage2["threshold"])
    ].nlargest(3, "stage2_score")
    false_negative = test.loc[
        test["label"].eq(1) & test["stage2_score"].lt(stage2["threshold"])
    ].nsmallest(3, "stage2_score")
    gallery = pd.concat(
        [
            false_positive.assign(error_type="false_positive"),
            false_negative.assign(error_type="false_negative"),
        ]
    )
    gallery.to_csv(RUN / "error_gallery_manifest.csv", index=False)
    fig, axes = plt.subplots(len(gallery), 2, figsize=(10, 2.5 * len(gallery)))
    for axes_row, row in zip(np.atleast_2d(axes), gallery.itertuples(index=False), strict=True):
        sample = read_sample(DATA / f"toi_{row.toi}.npz")
        axes_row[0].plot(sample["global_view"])
        axes_row[1].plot(sample["local_view"])
        axes_row[0].set_title(f"TOI {row.toi} {row.error_type}: global")
        axes_row[1].set_title(f"Stage 2={row.stage2_score:.3f}: local")
    fig.tight_layout()
    fig.savefig(RUN / "error_gallery.png", dpi=160)
    plt.close(fig)

    model = build_two_view_cnn()
    model.load_state_dict(
        torch.load(RUN / "stage1_selected.pt", map_location="cpu", weights_only=True)
    )
    model_card = {
        "architecture": "two-branch 1D CNN",
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "selected_seed": stage1["selected_seed_on_validation"],
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cross_fitting": "3-fold TIC-grouped outer folds with grouped inner early-stopping validation",
        "formal_feature_leakage_check": "catalogue period/midpoint absent",
    }
    (RUN / "model_card.json").write_text(json.dumps(model_card, indent=2) + "\n")
    joblib.load(RUN / "baseline_model.joblib")  # verify persisted model is readable
    comparison = json.loads((RUN / "stage_comparison.json").read_text())
    write_results_summary(
        stage1_metrics_path=RUN / "stage1_metrics.json",
        stage2_metrics_path=RUN / "stage2_metrics.json",
        fpr_difference=tuple(comparison["stage2_minus_stage1_fpr"]),
        output_path=ROOT / "reports/results_summary.md",
    )
    print(json.dumps(model_card, indent=2))


if __name__ == "__main__":
    main()
