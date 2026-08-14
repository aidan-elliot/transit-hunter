"""BLS-like transit search, phase-folded views, and vetting diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class BLSCandidate:
    period: float
    epoch: float
    duration: float
    depth: float
    power: float
    snr: float
    phase_center: float


def fold_phase(time: np.ndarray, period: float, epoch: float) -> np.ndarray:
    """Return phases centred on transit in the half-open interval [-0.5, 0.5)."""
    if not np.isfinite(period) or period <= 0:
        raise ValueError("period must be finite and positive.")
    return np.mod((np.asarray(time, dtype=float) - epoch) / period + 0.5, 1.0) - 0.5


def bin_phase_curve(phase: np.ndarray, flux: np.ndarray, bins: int) -> tuple[np.ndarray, np.ndarray]:
    """Mean-bin a folded curve and fill empty bins with the global median flux."""
    phase = np.asarray(phase, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if phase.shape != flux.shape or bins < 4:
        raise ValueError("phase/flux shapes must match and bins must be at least four.")
    edges = np.linspace(-0.5, 0.5, bins + 1)
    index = np.clip(np.digitize(phase, edges) - 1, 0, bins - 1)
    counts = np.bincount(index, minlength=bins)
    sums = np.bincount(index, weights=flux, minlength=bins)
    fallback = float(np.nanmedian(flux))
    values = np.divide(sums, counts, out=np.full(bins, fallback), where=counts > 0)
    centres = (edges[:-1] + edges[1:]) / 2
    return centres, values


def bls_search(
    time: np.ndarray,
    flux: np.ndarray,
    periods: np.ndarray,
    *,
    duration_fraction: float = 0.04,
    phase_bins: int = 256,
) -> BLSCandidate:
    """Find the strongest box-shaped dimming over an explicit trial-period grid.

    This deterministic, dependency-light implementation is suitable for the project's
    reproducible initial pipeline. Its output is intentionally a candidate rather than
    a planet claim and is validated against synthetic injections in the test suite.
    """
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    periods = np.asarray(periods, dtype=float)
    if len(time) != len(flux) or len(time) < 50:
        raise ValueError("BLS requires matching time/flux arrays with at least 50 points.")
    if np.any(~np.isfinite(time)) or np.any(~np.isfinite(flux)):
        raise ValueError("BLS inputs must be finite after preprocessing.")
    periods = periods[np.isfinite(periods) & (periods > 0)]
    if len(periods) == 0 or not 0 < duration_fraction < 0.25:
        raise ValueError("Supply positive periods and a duration fraction between zero and 0.25.")

    baseline = float(np.median(flux))
    scatter = float(1.4826 * np.median(np.abs(flux - baseline)))
    scatter = max(scatter, np.finfo(float).eps)
    reference_time = float(np.min(time))
    width = max(1, round(phase_bins * duration_fraction))
    best: BLSCandidate | None = None
    for period in periods:
        phase = np.mod((time - reference_time) / period, 1.0)
        bin_index = np.minimum((phase * phase_bins).astype(int), phase_bins - 1)
        counts = np.bincount(bin_index, minlength=phase_bins)
        sums = np.bincount(bin_index, weights=flux, minlength=phase_bins)
        circular_counts = np.concatenate([counts, counts[:width]])
        circular_sums = np.concatenate([sums, sums[:width]])
        window_counts = np.convolve(circular_counts, np.ones(width, dtype=int), mode="valid")[:phase_bins]
        window_sums = np.convolve(circular_sums, np.ones(width), mode="valid")[:phase_bins]
        means = np.divide(window_sums, window_counts, out=np.full(phase_bins, np.inf), where=window_counts > 0)
        start = int(np.argmin(means))
        in_flux = float(means[start])
        depth = baseline - in_flux
        snr = depth * np.sqrt(max(window_counts[start], 1)) / scatter
        candidate = BLSCandidate(
            period=float(period),
            epoch=reference_time + ((start + width / 2) / phase_bins) * float(period),
            duration=float(period * duration_fraction),
            depth=float(depth),
            power=float(max(snr, 0.0)),
            snr=float(snr),
            phase_center=float((start + width / 2) / phase_bins),
        )
        if best is None or candidate.power > best.power:
            best = candidate
    assert best is not None
    return best


def folded_views(
    time: np.ndarray,
    flux: np.ndarray,
    candidate: BLSCandidate,
    *,
    global_bins: int = 201,
    local_bins: int = 101,
    local_duration_multiples: float = 3.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate fixed-size global and local phase-folded model views."""
    phase = fold_phase(time, candidate.period, candidate.epoch)
    _, global_view = bin_phase_curve(phase, flux, global_bins)
    local_half_width = min(0.49, local_duration_multiples * candidate.duration / candidate.period)
    local_phase = phase[np.abs(phase) <= local_half_width]
    local_flux = np.asarray(flux)[np.abs(phase) <= local_half_width]
    if len(local_phase) < 4:
        raise ValueError("Candidate has too few local transit points for a local view.")
    scaled_phase = local_phase / (2 * local_half_width)
    _, local_view = bin_phase_curve(scaled_phase, local_flux, local_bins)
    return global_view.astype(np.float32), local_view.astype(np.float32)


def diagnostic_features(
    time: np.ndarray, flux: np.ndarray, candidate: BLSCandidate, sector_labels: np.ndarray | None = None
) -> dict[str, float]:
    """Calculate Stage 2 diagnostics from BLS-derived candidate parameters only."""
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    phase = fold_phase(time, candidate.period, candidate.epoch)
    half_duration = candidate.duration / candidate.period / 2
    in_transit = np.abs(phase) <= half_duration
    baseline = float(np.median(flux[~in_transit])) if np.any(~in_transit) else float(np.median(flux))
    cycles = np.rint((time - candidate.epoch) / candidate.period).astype(int)
    odd = in_transit & (cycles % 2 != 0)
    even = in_transit & (cycles % 2 == 0)
    odd_depth = baseline - float(np.mean(flux[odd])) if np.any(odd) else 0.0
    even_depth = baseline - float(np.mean(flux[even])) if np.any(even) else 0.0
    secondary = np.abs(np.abs(phase) - 0.5) <= half_duration
    secondary_depth = baseline - float(np.mean(flux[secondary])) if np.any(secondary) else 0.0
    left = in_transit & (phase < 0)
    right = in_transit & (phase >= 0)
    symmetry = abs(
        (float(np.mean(flux[left])) if np.any(left) else baseline)
        - (float(np.mean(flux[right])) if np.any(right) else baseline)
    )
    observed_transits = int(np.unique(cycles[in_transit]).size)
    sector_consistency = 0.0
    if sector_labels is not None:
        sector_labels = np.asarray(sector_labels)
        if sector_labels.shape != time.shape:
            raise ValueError("sector_labels must match time/flux shape.")
        sector_depths = []
        for sector in np.unique(sector_labels):
            sector_mask = sector_labels == sector
            sector_in = sector_mask & in_transit
            sector_out = sector_mask & ~in_transit
            if np.any(sector_in) and np.any(sector_out):
                sector_depths.append(float(np.mean(flux[sector_out]) - np.mean(flux[sector_in])))
        if len(sector_depths) > 1:
            sector_consistency = float(np.std(sector_depths))
    return {
        **asdict(candidate),
        "observed_transits": float(observed_transits),
        "odd_even_depth_difference": float(abs(odd_depth - even_depth)),
        "secondary_eclipse_depth": float(secondary_depth),
        "transit_symmetry_difference": float(symmetry),
        "sector_to_sector_depth_std": sector_consistency,
    }
