import numpy as np
import pandas as pd

from transit_hunter.data import (
    build_dataset,
    build_sample_from_arrays,
    diagnostic_table,
    read_sample,
)
from transit_hunter.features import fold_phase


def synthetic_curve(period: float = 2.5) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    time = np.linspace(0.0, 25.0, 5_000)
    flux = 1.0 + rng.normal(0.0, 0.0005, len(time))
    flux[np.abs(fold_phase(time, period, 0.3)) < 0.02] -= 0.01
    return time, flux


def test_model_ready_sample_round_trip(tmp_path) -> None:
    time, flux = synthetic_curve()
    path, metadata = build_sample_from_arrays(
        toi="100.01",
        time=time,
        flux=flux,
        output_dir=tmp_path,
        period_grid=np.linspace(2.2, 2.8, 81),
        sector_labels=np.where(time < 12.5, 1, 2),
        metadata={"label": 1, "tid": 100},
    )
    sample = read_sample(path)

    assert path.exists()
    assert metadata["candidate"]["snr"] > 3
    assert sample["global_view"].shape == (201,)
    assert sample["local_view"].shape == (101,)
    assert sample["metadata"]["label"] == 1
    assert "sector_to_sector_depth_std" in sample["diagnostics"]
    assert diagnostic_table([path]).loc[0, "toi"] == "100.01"


def test_dataset_manifest_preserves_loader_failures(tmp_path) -> None:
    records = pd.DataFrame({"toi": ["1.01", "2.01"], "label": [1, 0]})
    time, flux = synthetic_curve()

    def loader(row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        if row.toi == "2.01":
            raise RuntimeError("simulated missing product")
        return time, flux

    manifest = build_dataset(
        records,
        loader,
        tmp_path,
        period_grid_factory=lambda _: np.linspace(2.2, 2.8, 81),
    )

    assert manifest["status"].tolist() == ["built", "failed"]
    assert "simulated missing product" in manifest.loc[1, "error"]
    assert (tmp_path / "samples_manifest.csv").exists()
