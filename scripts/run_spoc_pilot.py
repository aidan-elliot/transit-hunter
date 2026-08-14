"""Run a minimal real-data SPOC 120-second quality-assurance pilot."""

from __future__ import annotations

import json
from pathlib import Path

import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from transit_hunter.data import build_sample_from_arrays
from transit_hunter.preprocess import preprocess_lightcurve

ROOT = Path(__file__).resolve().parents[1]
PILOT_TOIS = ("141.01", "1250.01", "589.01")


def _values(column) -> np.ndarray:
    return np.asarray(getattr(column, "value", column), dtype=float)


def main() -> None:
    candidates = pd.read_csv(ROOT / "data/metadata/labels_snapshot.csv", dtype={"toi": str})
    selected = candidates.loc[candidates["toi"].isin(PILOT_TOIS)].copy()
    raw_dir = ROOT / "data/raw/pilot"
    sample_dir = ROOT / "data/processed/pilot"
    figure_dir = ROOT / "reports/figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for row in selected.itertuples(index=False):
        result = lk.search_lightcurve(
            target=f"TIC {int(row.tid)}", mission="TESS", author="SPOC", exptime=120
        )
        try:
            if len(result) == 0:
                raise FileNotFoundError("No SPOC 120-second product")
            product = result[0]
            raw = product.download(download_dir=str(raw_dir), quality_bitmask=None)
            filtered = product.download(download_dir=str(raw_dir), quality_bitmask="default")
            if raw is None or filtered is None:
                raise RuntimeError("Lightkurve returned no downloaded light curve")
            raw_time, raw_flux = _values(raw.time), _values(raw.flux)
            time, flux = _values(filtered.time), _values(filtered.flux)
            processed = preprocess_lightcurve(time, flux)
            sample_path, metadata = build_sample_from_arrays(
                toi=row.toi,
                time=time,
                flux=flux,
                output_dir=sample_dir,
                metadata={"tid": int(row.tid), "disposition": row.tfopwg_disp},
            )
            candidate = metadata["candidate"]
            period_ratio = float(candidate["period"]) / float(row.pl_orbper)
            recovered = min(abs(period_ratio - factor) for factor in (0.5, 1.0, 2.0)) <= 0.05

            fig, axes = plt.subplots(2, 2, figsize=(12, 7))
            axes[0, 0].plot(raw_time, raw_flux, ".", ms=0.5)
            axes[0, 0].set_title("Raw (quality_bitmask=None)")
            axes[0, 1].plot(time, flux, ".", ms=0.5)
            axes[0, 1].set_title("SPOC default quality mask")
            axes[1, 0].plot(processed.time, processed.flux, ".", ms=0.5)
            axes[1, 0].set_title("Cleaned and flattened")
            with np.load(sample_path, allow_pickle=False) as sample:
                axes[1, 1].plot(sample["global_view"], label="global")
                axes[1, 1].plot(
                    np.linspace(0, len(sample["global_view"]) - 1, len(sample["local_view"])),
                    sample["local_view"],
                    label="local",
                )
            axes[1, 1].set_title(f"BLS global/local views; P={candidate['period']:.3f} d")
            axes[1, 1].legend()
            fig.suptitle(f"TOI {row.toi} / TIC {int(row.tid)} / {row.tfopwg_disp}")
            fig.tight_layout()
            fig.savefig(figure_dir / f"pilot_toi_{row.toi}.png", dpi=160)
            plt.close(fig)

            rows.append(
                {
                    "toi": row.toi,
                    "tid": int(row.tid),
                    "disposition": row.tfopwg_disp,
                    "status": "passed",
                    "author": str(filtered.author),
                    "cadence_seconds": float(filtered.meta.get("TIMEDEL", np.nan)) * 86400,
                    "sector": int(filtered.sector),
                    "raw_points": len(raw_time),
                    "quality_filtered_points": len(time),
                    "preprocessed_points": processed.retained_points,
                    "catalogue_period_diagnostic": float(row.pl_orbper),
                    "bls_period": float(candidate["period"]),
                    "bls_snr": float(candidate["snr"]),
                    "period_or_harmonic_recovered_5pct": recovered,
                    "sample_path": str(sample_path.relative_to(ROOT)),
                    "failure_reason": "",
                }
            )
        except Exception as error:  # noqa: BLE001 - every pilot failure belongs in the manifest.
            rows.append(
                {
                    "toi": row.toi,
                    "tid": int(row.tid),
                    "disposition": row.tfopwg_disp,
                    "status": "failed",
                    "failure_reason": f"{type(error).__name__}: {error}",
                }
            )

    manifest = pd.DataFrame(rows)
    manifest.to_csv(ROOT / "data/metadata/pilot_download_manifest.csv", index=False)
    passed = manifest.loc[manifest["status"].eq("passed")]
    audit = {
        "selected_tois": len(manifest),
        "passed": len(passed),
        "failed": int(manifest["status"].eq("failed").sum()),
        "all_spoc": bool(passed["author"].eq("SPOC").all()) if len(passed) else False,
        "all_120_second": bool(np.allclose(passed["cadence_seconds"], 120, atol=1))
        if len(passed)
        else False,
        "all_views_built": bool(passed["sample_path"].ne("").all()) if len(passed) else False,
        "bls_period_or_harmonic_recovery_rate": float(
            passed["period_or_harmonic_recovered_5pct"].mean()
        )
        if len(passed)
        else None,
        "note": "Catalogue ephemerides are used only for the reported BLS recovery diagnostic.",
    }
    (ROOT / "reports/pilot_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    if len(passed) != len(manifest) or not audit["all_spoc"] or not audit["all_120_second"]:
        raise SystemExit("Pilot acceptance gate failed; inspect pilot_download_manifest.csv")


if __name__ == "__main__":
    main()
