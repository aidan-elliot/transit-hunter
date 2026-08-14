import json

import numpy as np
import pandas as pd

from transit_hunter.models import STAGE2_FEATURES
from transit_hunter.train import (
    train_feature_experiment,
    train_stage2_experiment,
    train_two_stage_feature_experiment,
)


def experiment_frame() -> pd.DataFrame:
    rng = np.random.default_rng(77)
    rows = []
    for split, count in (("train", 60), ("validation", 30), ("test", 30)):
        labels = np.array([0, 1] * (count // 2))
        for index, label in enumerate(labels):
            row = {
                "toi": f"{split}-{index}",
                "tid": f"{split}-tic-{index // 2}",
                "split": split,
                "label": label,
                "stage1_score": np.clip(0.25 + 0.55 * label + rng.normal(0, 0.1), 0, 1),
                "period": rng.uniform(1, 10),
                "duration": rng.uniform(0.02, 0.2),
                "depth": 0.001 + 0.01 * label + rng.normal(0, 0.0005),
                "power": 2 + 8 * label + rng.normal(0, 0.5),
                "snr": 2 + 8 * label + rng.normal(0, 0.5),
                "observed_transits": rng.integers(3, 12),
                "odd_even_depth_difference": 0.004 * (1 - label) + rng.normal(0, 0.0002),
                "secondary_eclipse_depth": 0.003 * (1 - label) + rng.normal(0, 0.0002),
                "transit_symmetry_difference": 0.002 * (1 - label) + rng.normal(0, 0.0002),
                "sector_to_sector_depth_std": rng.uniform(0, 0.001),
            }
            rows.append(row)
    return pd.DataFrame(rows)


def test_training_uses_validation_threshold_and_writes_auditable_outputs(tmp_path) -> None:
    frame = experiment_frame()
    config, input_file = tmp_path / "config.yaml", tmp_path / "features.csv"
    config.write_text("seed: 4000\n", encoding="utf-8")
    frame.to_csv(input_file, index=False)
    baseline = train_feature_experiment(
        frame,
        feature_columns=list(STAGE2_FEATURES),
        output_dir=tmp_path / "baseline",
        config_paths=[config],
        input_paths=[input_file],
        target_recall=0.8,
    )
    stage2 = train_stage2_experiment(
        frame,
        stage1_score_column="stage1_score",
        output_dir=tmp_path / "stage2",
        config_paths=[config],
        input_paths=[input_file],
        target_recall=0.8,
    )

    assert baseline.model_path.exists() and stage2.model_path.exists()
    metrics = json.loads(stage2.metrics_path.read_text(encoding="utf-8"))
    assert metrics["target_recall"] == 0.8
    assert (stage2.metrics_path.parent / "run_manifest.json").exists()


def test_two_stage_orchestrator_cross_fits_training_scores_by_tic(tmp_path) -> None:
    frame = experiment_frame()
    config, input_file = tmp_path / "config.yaml", tmp_path / "features.csv"
    config.write_text("seed: 4000\n", encoding="utf-8")
    frame.to_csv(input_file, index=False)

    result = train_two_stage_feature_experiment(
        frame,
        stage1_feature_columns=list(STAGE2_FEATURES),
        group_column="tid",
        output_dir=tmp_path / "two-stage",
        config_paths=[config],
        input_paths=[input_file],
        target_recall=0.8,
    )

    comparison = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert result.stage1_model_path.exists() and result.stage2_model_path.exists()
    assert len(comparison["stage2_minus_stage1_fpr"]) == 3
    assert (result.summary_path.parent / "stage1_test_roc.png").exists()
