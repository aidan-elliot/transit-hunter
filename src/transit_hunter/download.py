"""Lightkurve download helpers for the project's fixed SPOC 120-second product."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def search_spoc_two_minute_lightcurves(tic_id: int):
    """Query only SPOC 120-second TESS light curves for one TIC ID."""
    import lightkurve as lk

    return lk.search_lightcurve(
        target=f"TIC {tic_id}", mission="TESS", author="SPOC", exptime=120
    )


def download_spoc_two_minute_lightcurves(tic_id: int, download_dir: Path):
    """Download only the queried SPOC 120-second products for one TIC."""
    result = search_spoc_two_minute_lightcurves(tic_id)
    return result.download_all(download_dir=str(download_dir), quality_bitmask="default")


def lightcurve_arrays(lightcurve) -> tuple[np.ndarray, np.ndarray]:
    """Convert a Lightkurve object to finite NumPy arrays without retaining units."""
    time = np.asarray(getattr(lightcurve.time, "value", lightcurve.time), dtype=float)
    flux = np.asarray(getattr(lightcurve.flux, "value", lightcurve.flux), dtype=float)
    return time, flux


def load_tic_arrays(tic_id: int, download_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Download and concatenate all available SPOC two-minute curves for one TIC."""
    collection = download_spoc_two_minute_lightcurves(tic_id, download_dir)
    if collection is None or len(collection) == 0:
        raise FileNotFoundError(f"No SPOC 120-second light curves are available for TIC {tic_id}.")
    arrays = [lightcurve_arrays(lightcurve) for lightcurve in collection]
    time = np.concatenate([item[0] for item in arrays])
    flux = np.concatenate([item[1] for item in arrays])
    return time, flux


def load_tic_arrays_with_sectors(tic_id: int, download_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return concatenated arrays plus a sector label per cadence for consistency diagnostics."""
    collection = download_spoc_two_minute_lightcurves(tic_id, download_dir)
    if collection is None or len(collection) == 0:
        raise FileNotFoundError(f"No SPOC 120-second light curves are available for TIC {tic_id}.")
    arrays = [lightcurve_arrays(lightcurve) for lightcurve in collection]
    sectors = [
        np.full(len(time), getattr(lightcurve, "sector", index), dtype=int)
        for index, (lightcurve, (time, _)) in enumerate(zip(collection, arrays, strict=True))
    ]
    return (
        np.concatenate([item[0] for item in arrays]),
        np.concatenate([item[1] for item in arrays]),
        np.concatenate(sectors),
    )
