import numpy as np
import pytest

from transit_hunter.preprocess import preprocess_lightcurve


def test_preprocessing_sorts_removes_invalid_points_and_normalizes() -> None:
    time = np.array([3.0, 1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0])
    flux = np.array([1.0, 1.0, 1.0, 1.0, np.nan, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 20.0])

    processed = preprocess_lightcurve(time, flux, window_points=5)

    assert np.all(np.diff(processed.time) > 0)
    assert np.all(np.isfinite(processed.flux))
    assert np.isclose(np.median(processed.flux), 1.0)
    assert processed.retained_points < processed.input_points


def test_preprocessing_rejects_mismatched_arrays() -> None:
    with pytest.raises(ValueError, match="same shape"):
        preprocess_lightcurve(np.arange(10), np.arange(9))
