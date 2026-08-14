"""Baseline, view-based Stage 1, diagnostic Stage 2, and optional PyTorch CNN models."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import read_sample

STAGE2_FEATURES = (
    "period",
    "duration",
    "depth",
    "power",
    "snr",
    "observed_transits",
    "odd_even_depth_difference",
    "secondary_eclipse_depth",
    "transit_symmetry_difference",
    "sector_to_sector_depth_std",
)


def logistic_pipeline(seed: int = 4000) -> Pipeline:
    """Return the project's interpretable, class-balanced classifier pipeline."""
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=seed)),
        ]
    )


def fit_feature_baseline(
    features: pd.DataFrame, labels: pd.Series | np.ndarray, *, seed: int = 4000
) -> Pipeline:
    """Fit the non-deep-learning BLS/diagnostic baseline on explicitly supplied features."""
    if features.empty:
        raise ValueError("Baseline requires at least one feature column.")
    target = np.asarray(labels, dtype=int)
    if len(target) != len(features) or len(np.unique(target)) != 2:
        raise ValueError("Baseline requires matching binary labels with both classes present.")
    model = logistic_pipeline(seed)
    model.fit(features, target)
    return model


def view_matrix(sample_paths: Iterable[Path]) -> np.ndarray:
    """Flatten global/local phase views for a portable non-CNN Stage 1 comparator."""
    vectors = []
    for path in sample_paths:
        sample = read_sample(Path(path))
        vectors.append(np.concatenate([sample["global_view"], sample["local_view"]]))
    if not vectors:
        raise ValueError("At least one sample is required to build a view matrix.")
    return np.vstack(vectors)


def fit_view_classifier(sample_paths: Iterable[Path], labels: pd.Series | np.ndarray, *, seed: int = 4000) -> Pipeline:
    """Fit a linear Stage 1 comparator on global + local transit-shape views.

    This is a validated CPU fallback and sanity baseline. The primary Stage 1 CNN is
    supplied by :func:`build_two_view_cnn` when PyTorch is available.
    """
    return fit_feature_baseline(pd.DataFrame(view_matrix(sample_paths)), labels, seed=seed)


def fit_stage2_classifier(
    diagnostics: pd.DataFrame,
    stage1_scores: np.ndarray,
    labels: pd.Series | np.ndarray,
    *,
    seed: int = 4000,
) -> Pipeline:
    """Fit the Stage 2 diagnostic classifier using a Stage 1 score plus diagnostics."""
    missing = set(STAGE2_FEATURES).difference(diagnostics.columns)
    if missing:
        raise ValueError(f"Diagnostics are missing Stage 2 features: {sorted(missing)}")
    stage1_scores = np.asarray(stage1_scores, dtype=float)
    if len(stage1_scores) != len(diagnostics):
        raise ValueError("stage1_scores must match the number of diagnostic rows.")
    features = diagnostics.loc[:, list(STAGE2_FEATURES)].copy()
    features.insert(0, "stage1_score", stage1_scores)
    return fit_feature_baseline(features, labels, seed=seed)


def stage2_feature_frame(diagnostics: pd.DataFrame, stage1_scores: np.ndarray) -> pd.DataFrame:
    """Construct the exact feature order expected by a Stage 2 classifier."""
    missing = set(STAGE2_FEATURES).difference(diagnostics.columns)
    if missing:
        raise ValueError(f"Diagnostics are missing Stage 2 features: {sorted(missing)}")
    frame = diagnostics.loc[:, list(STAGE2_FEATURES)].copy()
    frame.insert(0, "stage1_score", np.asarray(stage1_scores, dtype=float))
    return frame


def save_model(model: Pipeline, path: Path) -> None:
    """Persist a fitted scikit-learn model for later evaluation or demonstration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def build_two_view_cnn(global_length: int = 201, local_length: int = 101):
    """Construct the primary two-branch PyTorch Stage 1 CNN on compatible systems."""
    try:
        import torch
        from torch import nn
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError(
            "Stage 1 CNN requires PyTorch. Use a supported x86_64/Apple Silicon environment "
            "or run the validated view-classifier fallback."
        ) from error

    class TwoViewCNN(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.global_branch = nn.Sequential(
                nn.Conv1d(1, 16, kernel_size=5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                nn.Conv1d(16, 32, kernel_size=5, padding=2), nn.ReLU(), nn.AdaptiveAvgPool1d(8),
            )
            self.local_branch = nn.Sequential(
                nn.Conv1d(1, 16, kernel_size=5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                nn.Conv1d(16, 32, kernel_size=5, padding=2), nn.ReLU(), nn.AdaptiveAvgPool1d(8),
            )
            self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(32 * 8 * 2, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))

        def forward(self, global_view, local_view):
            if global_view.shape[-1] != global_length or local_view.shape[-1] != local_length:
                raise ValueError("Input views do not match the configured global/local lengths.")
            return self.classifier(torch.cat([self.global_branch(global_view), self.local_branch(local_view)], dim=1))

    return TwoViewCNN()


def build_two_view_lstm(global_length: int = 201, local_length: int = 101):
    """Construct the planned compact global/local LSTM architecture."""
    try:
        import torch
        from torch import nn
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError("LSTM comparison requires PyTorch.") from error

    class TwoViewLSTM(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.global_lstm = nn.LSTM(1, 32, batch_first=True)
            self.local_lstm = nn.LSTM(1, 32, batch_first=True)
            self.classifier = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

        def forward(self, global_view, local_view):
            if global_view.shape[-1] != global_length or local_view.shape[-1] != local_length:
                raise ValueError("Input views do not match the configured global/local lengths.")
            _, (global_hidden, _) = self.global_lstm(global_view.transpose(1, 2))
            _, (local_hidden, _) = self.local_lstm(local_view.transpose(1, 2))
            return self.classifier(torch.cat([global_hidden[-1], local_hidden[-1]], dim=1))

    return TwoViewLSTM()


def build_two_view_transformer(global_length: int = 201, local_length: int = 101):
    """Construct the planned compact global/local Transformer comparison model."""
    try:
        import torch
        from torch import nn
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError("Transformer comparison requires PyTorch.") from error

    class TwoViewTransformer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Linear(1, 32)
            layer = nn.TransformerEncoderLayer(d_model=32, nhead=4, dim_feedforward=64, dropout=0.1, batch_first=True)
            self.global_encoder = nn.TransformerEncoder(layer, num_layers=2)
            self.local_encoder = nn.TransformerEncoder(layer, num_layers=2)
            self.classifier = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2), nn.Linear(32, 1))

        def _encode(self, values, encoder):
            return encoder(self.embedding(values.transpose(1, 2))).mean(dim=1)

        def forward(self, global_view, local_view):
            if global_view.shape[-1] != global_length or local_view.shape[-1] != local_length:
                raise ValueError("Input views do not match the configured global/local lengths.")
            return self.classifier(torch.cat([self._encode(global_view, self.global_encoder), self._encode(local_view, self.local_encoder)], dim=1))

    return TwoViewTransformer()


def build_two_view_model(architecture: str, global_length: int = 201, local_length: int = 101):
    """Select a comparable two-view deep-learning architecture by explicit name."""
    builders = {"cnn": build_two_view_cnn, "lstm": build_two_view_lstm, "transformer": build_two_view_transformer}
    try:
        return builders[architecture.lower()](global_length, local_length)
    except KeyError as error:
        raise ValueError(f"Unsupported architecture {architecture!r}; choose cnn, lstm, or transformer.") from error


def train_two_view_cnn(
    train_global: np.ndarray,
    train_local: np.ndarray,
    train_labels: np.ndarray,
    validation_global: np.ndarray,
    validation_local: np.ndarray,
    validation_labels: np.ndarray,
    *,
    epochs: int = 40,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    patience: int = 6,
    seed: int = 4000,
    architecture: str = "cnn",
):
    """Train the primary CNN with validation PR-AUC early stopping.

    This routine is deliberately isolated from the CPU fallback. It requires PyTorch
    and returns the best model state plus an epoch-level history suitable for a report.
    """
    try:
        import torch
        from sklearn.metrics import average_precision_score
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError("CNN training requires PyTorch and scikit-learn.") from error
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    train_labels = np.asarray(train_labels, dtype=np.float32)
    validation_labels = np.asarray(validation_labels, dtype=np.float32)
    if len(np.unique(train_labels)) != 2 or len(np.unique(validation_labels)) != 2:
        raise ValueError("Both train and validation labels must contain both classes.")
    model = build_two_view_model(architecture, train_global.shape[-1], train_local.shape[-1])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    positive_weight = (train_labels == 0).sum() / max((train_labels == 1).sum(), 1)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(positive_weight, dtype=torch.float32, device=device))
    optimiser = torch.optim.Adam(model.parameters(), lr=learning_rate)
    dataset = TensorDataset(
        torch.tensor(train_global, dtype=torch.float32).unsqueeze(1),
        torch.tensor(train_local, dtype=torch.float32).unsqueeze(1),
        torch.tensor(train_labels, dtype=torch.float32),
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=torch.Generator().manual_seed(seed))
    validation_global_tensor = torch.tensor(validation_global, dtype=torch.float32, device=device).unsqueeze(1)
    validation_local_tensor = torch.tensor(validation_local, dtype=torch.float32, device=device).unsqueeze(1)
    history: list[dict[str, float]] = []
    best_state, best_score, stale_epochs = None, -np.inf, 0
    for epoch in range(1, epochs + 1):
        model.train()
        losses = []
        for global_batch, local_batch, label_batch in loader:
            global_batch, local_batch, label_batch = global_batch.to(device), local_batch.to(device), label_batch.to(device)
            optimiser.zero_grad()
            loss = loss_fn(model(global_batch, local_batch).squeeze(1), label_batch)
            loss.backward()
            optimiser.step()
            losses.append(float(loss.item()))
        model.eval()
        with torch.no_grad():
            validation_scores = torch.sigmoid(model(validation_global_tensor, validation_local_tensor).squeeze(1)).cpu().numpy()
        pr_auc = float(average_precision_score(validation_labels, validation_scores))
        history.append({"epoch": float(epoch), "train_loss": float(np.mean(losses)), "validation_pr_auc": pr_auc})
        if pr_auc > best_score:
            best_score, stale_epochs = pr_auc, 0
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break
    assert best_state is not None
    model.load_state_dict(best_state)
    model.eval()
    return model, pd.DataFrame(history)


def initialize_transfer_learning(model, checkpoint_path: Path, *, freeze_feature_extractors: bool = True):
    """Load a compatible Kepler pretraining checkpoint for TESS fine-tuning.

    The caller must document cadence/preprocessing differences and retain the source
    dataset manifest. ``strict=False`` permits replacing the final classifier head.
    """
    try:
        import torch
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError("Transfer learning requires PyTorch.") from error
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    state = checkpoint.get("model_state_dict", checkpoint)
    missing, unexpected = model.load_state_dict(state, strict=False)
    if freeze_feature_extractors:
        for name, parameter in model.named_parameters():
            if "classifier" not in name:
                parameter.requires_grad = False
    return {"missing_keys": list(missing), "unexpected_keys": list(unexpected)}


def predict_two_view_cnn(model, global_views: np.ndarray, local_views: np.ndarray) -> np.ndarray:
    """Return Stage 1 CNN probabilities in evaluation mode."""
    try:
        import torch
    except ImportError as error:  # pragma: no cover - platform dependent.
        raise RuntimeError("CNN prediction requires PyTorch.") from error
    device = next(model.parameters()).device
    with torch.no_grad():
        scores = torch.sigmoid(
            model(
                torch.tensor(global_views, dtype=torch.float32, device=device).unsqueeze(1),
                torch.tensor(local_views, dtype=torch.float32, device=device).unsqueeze(1),
            ).squeeze(1)
        )
    return scores.detach().cpu().numpy()
