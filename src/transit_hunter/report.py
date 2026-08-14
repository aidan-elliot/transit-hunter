"""Generate report-ready result summaries from frozen experiment outputs."""

from __future__ import annotations

import json
from pathlib import Path


def write_results_summary(
    *,
    stage1_metrics_path: Path,
    stage2_metrics_path: Path,
    fpr_difference: tuple[float, float, float],
    output_path: Path,
) -> Path:
    """Write a concise, data-grounded result summary for the final report draft."""
    stage1 = json.loads(stage1_metrics_path.read_text(encoding="utf-8"))
    stage2 = json.loads(stage2_metrics_path.read_text(encoding="utf-8"))
    point, lower, upper = fpr_difference
    s1, s2 = stage1["test"], stage2["test"]
    text = f"""# Two-stage pipeline results summary

## Pre-registered comparison

The operating thresholds were selected on the validation partition at a target recall of {stage1['target_recall']:.2f}; the temporal test set was then evaluated without retuning.

| Model | Test PR-AUC | Test ROC-AUC | Recall | Precision | False-positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 | {s1['pr_auc']:.3f} | {s1['roc_auc']:.3f} | {s1['recall']:.3f} | {s1['precision']:.3f} | {s1['false_positive_rate']:.3f} |
| Stage 1 + Stage 2 | {s2['pr_auc']:.3f} | {s2['roc_auc']:.3f} | {s2['recall']:.3f} | {s2['precision']:.3f} | {s2['false_positive_rate']:.3f} |

At the validation-selected operating threshold, the Stage 2 minus Stage 1 false-positive-rate difference was {point:.3f} (TIC-grouped bootstrap 95% interval {lower:.3f} to {upper:.3f}). Negative values favour the two-stage pipeline.

## Interpretation boundaries

These values assess discrimination among the frozen, eligible TOI records. They do not constitute a validation of newly discovered planets. The final discussion must connect improved false-positive handling to reliable estimates of exoplanet occurrence while describing catalogue, cadence, and selection limitations.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path
