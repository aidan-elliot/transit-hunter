"""Deterministic cleaning and flattening for one TESS light curve."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import median_filter


@dataclass(frozen=True)
class ProcessedLightCurve:
    """Finite, time-ordered, unit-median light-curve arrays."""

    time: np.ndarray
    flux: np.ndarray
    trend: np.ndarray
    input_points: int
    retained_points: int


def clean_lightcurve(time: np.ndarray, flux: np.ndarray, sigma: float = 8.0) -> tuple[np.ndarray, np.ndarray]:
    """Remove invalid points and robustly clip isolated extreme flux outliers."""
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if time.shape != flux.shape:
        raise ValueError("time and flux must have the same shape.")
    valid = np.isfinite(time) & np.isfinite(flux)
    time, flux = time[valid], flux[valid]
    if len(time) < 10:
        raise ValueError("At least ten finite cadence points are required.")
    ordering = np.argsort(time, kind="stable")
    time, flux = time[ordering], flux[ordering]
    median = np.median(flux)
    mad = np.median(np.abs(flux - median))
    robust_sigma = 1.4826 * mad
    if robust_sigma > 0:
        keep = np.abs(flux - median) <= sigma * robust_sigma
        time, flux = time[keep], flux[keep]
    if len(time) < 10:
        raise ValueError("Outlier filtering left fewer than ten cadence points.")
    return time, flux


def flatten_lightcurve(flux: np.ndarray, window_points: int = 301) -> tuple[np.ndarray, np.ndarray]:
    """Divide flux by a robust long-timescale median trend."""
    flux = np.asarray(flux, dtype=float)
    if flux.ndim != 1 or len(flux) < 10:
        raise ValueError("flatten_lightcurve requires a one-dimensional curve of at least ten points.")
    window_points = min(window_points, len(flux) if len(flux) % 2 else len(flux) - 1)
    window_points = max(3, window_points | 1)
    trend = median_filter(flux, size=window_points, mode="nearest")
    fallback = np.median(flux)
    trend = np.where(np.isfinite(trend) & (np.abs(trend) > np.finfo(float).eps), trend, fallback)
    flattened = flux / trend
    flattened /= np.median(flattened)
    return flattened, trend


def preprocess_lightcurve(
    time: np.ndarray, flux: np.ndarray, *, sigma: float = 8.0, window_points: int = 301
) -> ProcessedLightCurve:
    """Clean and flatten an array representation of a single light curve."""
    input_points = len(time)
    clean_time, clean_flux = clean_lightcurve(time, flux, sigma=sigma)
    flattened, trend = flatten_lightcurve(clean_flux, window_points=window_points)
    return ProcessedLightCurve(
        time=clean_time,
        flux=flattened,
        trend=trend,
        input_points=input_points,
        retained_points=len(clean_time),
    )
