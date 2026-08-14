"""Model-ready sample serialization and dataset construction helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .features import bls_search, diagnostic_features, folded_views
from .preprocess import preprocess_lightcurve

CurveLoader = Callable[[pd.Series], tuple[np.ndarray, np.ndarray]]


def _json_default(value: object) -> object:
    """Serialize NumPy/Pandas scalar metadata without weakening sample validation."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Metadata value of type {type(value).__name__} is not JSON serializable.")


def default_period_grid(time: np.ndarray, minimum_period: float = 0.5, points: int = 300) -> np.ndarray:
    """Build an explicit BLS period grid from one curve's observing baseline."""
    time = np.asarray(time, dtype=float)
    baseline = float(np.max(time) - np.min(time))
    maximum_period = min(30.0, baseline / 2)
    if baseline <= 2 * minimum_period or points < 10:
        raise ValueError("Observing baseline is too short for the configured BLS period grid.")
    return np.linspace(minimum_period, maximum_period, points, dtype=float)


def sample_filename(toi: object) -> str:
    """Return a filesystem-safe stable filename for a TOI identifier."""
    return "toi_" + re.sub(r"[^A-Za-z0-9._-]+", "_", str(toi)) + ".npz"


def write_sample(
    path: Path,
    *,
    global_view: np.ndarray,
    local_view: np.ndarray,
    diagnostics: dict[str, float],
    metadata: dict[str, object],
) -> None:
    """Write one portable NPZ sample with arrays, diagnostics, and JSON metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    names = np.array(sorted(diagnostics), dtype=str)
    values = np.array([diagnostics[name] for name in names], dtype=np.float32)
    np.savez_compressed(
        path,
        global_view=np.asarray(global_view, dtype=np.float32),
        local_view=np.asarray(local_view, dtype=np.float32),
        diagnostic_names=names,
        diagnostic_values=values,
        metadata_json=np.array(json.dumps(metadata, sort_keys=True, default=_json_default)),
    )


def read_sample(path: Path) -> dict[str, object]:
    """Load a serialized sample into ordinary arrays and dictionaries."""
    with np.load(path, allow_pickle=False) as data:
        names = data["diagnostic_names"].astype(str)
        values = data["diagnostic_values"].astype(float)
        return {
            "global_view": data["global_view"].astype(np.float32),
            "local_view": data["local_view"].astype(np.float32),
            "diagnostics": dict(zip(names.tolist(), values.tolist(), strict=True)),
            "metadata": json.loads(str(data["metadata_json"].item())),
        }


def build_sample_from_arrays(
    *,
    toi: object,
    time: np.ndarray,
    flux: np.ndarray,
    output_dir: Path,
    period_grid: np.ndarray | None = None,
    sector_labels: np.ndarray | None = None,
    metadata: dict[str, object] | None = None,
) -> tuple[Path, dict[str, object]]:
    """Preprocess, search, fold, and serialize one TOI without catalogue ephemeris inputs."""
    processed = preprocess_lightcurve(time, flux)
    periods = period_grid if period_grid is not None else default_period_grid(processed.time)
    candidate = bls_search(processed.time, processed.flux, periods)
    global_view, local_view = folded_views(processed.time, processed.flux, candidate)
    if sector_labels is not None:
        sector_labels = np.asarray(sector_labels)
        finite_sorted = np.isfinite(np.asarray(time, dtype=float)) & np.isfinite(np.asarray(flux, dtype=float))
        sorted_index = np.argsort(np.asarray(time, dtype=float)[finite_sorted], kind="stable")
        aligned_sectors = sector_labels[finite_sorted][sorted_index]
        # Apply the same robust clipping condition used by clean_lightcurve.
        retained_lookup = np.isin(np.asarray(time, dtype=float)[finite_sorted][sorted_index], processed.time)
        aligned_sectors = aligned_sectors[retained_lookup]
    else:
        aligned_sectors = None
    diagnostics = diagnostic_features(processed.time, processed.flux, candidate, sector_labels=aligned_sectors)
    record = {
        "toi": str(toi),
        "candidate": asdict(candidate),
        "input_points": processed.input_points,
        "retained_points": processed.retained_points,
        **(metadata or {}),
    }
    path = output_dir / sample_filename(toi)
    write_sample(path, global_view=global_view, local_view=local_view, diagnostics=diagnostics, metadata=record)
    return path, record


def build_dataset(
    records: pd.DataFrame,
    curve_loader: CurveLoader,
    output_dir: Path,
    *,
    period_grid_factory: Callable[[np.ndarray], np.ndarray] = default_period_grid,
) -> pd.DataFrame:
    """Build samples and return an auditable success/failure manifest.

    A loader receives one metadata row and returns its concatenated time/flux arrays.
    Failures are persisted as rows instead of silently disappearing from a dataset.
    """
    if "toi" not in records or records["toi"].duplicated().any():
        raise ValueError("Records require unique TOI identifiers.")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, object]] = []
    for _, row in records.iterrows():
        toi = str(row["toi"])
        try:
            loaded_curve = curve_loader(row)
            time, flux = loaded_curve[:2]
            sector_labels = loaded_curve[2] if len(loaded_curve) > 2 else None
            path, metadata = build_sample_from_arrays(
                toi=toi,
                time=time,
                flux=flux,
                output_dir=output_dir,
                period_grid=period_grid_factory(np.asarray(time, dtype=float)[np.isfinite(time)]),
                sector_labels=sector_labels,
                metadata={key: value for key, value in row.to_dict().items() if pd.notna(value)},
            )
            manifest_rows.append(
                {
                    "toi": toi,
                    "status": "built",
                    "sample_path": str(path),
                    "error": "",
                    "candidate_period": metadata["candidate"]["period"],
                    "candidate_snr": metadata["candidate"]["snr"],
                }
            )
        except Exception as error:  # noqa: BLE001 - preserve every per-TOI build failure in the manifest.
            manifest_rows.append(
                {"toi": toi, "status": "failed", "sample_path": "", "error": f"{type(error).__name__}: {error}"}
            )
    manifest = pd.DataFrame(manifest_rows).sort_values("toi", kind="stable").reset_index(drop=True)
    manifest.to_csv(output_dir / "samples_manifest.csv", index=False)
    return manifest


def diagnostic_table(sample_paths: Iterable[Path]) -> pd.DataFrame:
    """Build a feature table from saved samples for baseline/Stage 2 training."""
    rows: list[dict[str, object]] = []
    for path in sample_paths:
        sample = read_sample(Path(path))
        rows.append({**sample["metadata"], **sample["diagnostics"], "sample_path": str(path)})
    return pd.DataFrame(rows)
