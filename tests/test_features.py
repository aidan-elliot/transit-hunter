import numpy as np

from transit_hunter.features import bls_search, diagnostic_features, fold_phase, folded_views


def injected_transit_curve(period: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(4000)
    time = np.linspace(0.0, 30.0, 6_000)
    phase = fold_phase(time, period, 0.4)
    flux = np.ones_like(time) + rng.normal(0.0, 0.0004, size=len(time))
    flux[np.abs(phase) < 0.02] -= 0.012
    return time, flux


def test_bls_recovers_injected_period_and_builds_fixed_views() -> None:
    time, flux = injected_transit_curve()
    candidate = bls_search(time, flux, np.linspace(2.7, 3.3, 121), duration_fraction=0.04)
    global_view, local_view = folded_views(time, flux, candidate)

    assert abs(candidate.period - 3.0) < 0.03
    assert candidate.depth > 0
    assert candidate.snr > 5
    assert global_view.shape == (201,)
    assert local_view.shape == (101,)


def test_diagnostics_are_finite_and_count_observed_transits() -> None:
    time, flux = injected_transit_curve()
    candidate = bls_search(time, flux, np.linspace(2.8, 3.2, 81), duration_fraction=0.04)
    diagnostics = diagnostic_features(time, flux, candidate)

    assert diagnostics["observed_transits"] >= 8
    assert all(np.isfinite(value) for value in diagnostics.values())


def test_diagnostics_include_sector_consistency() -> None:
    time, flux = injected_transit_curve()
    candidate = bls_search(time, flux, np.linspace(2.8, 3.2, 81), duration_fraction=0.04)
    sectors = np.where(time < 15, 1, 2)
    diagnostics = diagnostic_features(time, flux, candidate, sector_labels=sectors)

    assert diagnostics["sector_to_sector_depth_std"] >= 0
