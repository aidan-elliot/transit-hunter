# Runtime compatibility

## Proven x64 execution (2026-08-14)

The complete workflow was run on Windows x64 with Python 3.11.9. The editable development install succeeded with Lightkurve 2.6.0, Astropy 8.0.1, pandas 2.3.3, and CPU PyTorch 2.13.0. The frozen real-data run built all 1,812 eligible samples and trained the baseline, Stage 1 CNN, and Stage 2 classifier. See `reports/runs/real_spoc_2min_v1/run_manifest.json` and `requirements-lock.txt`.

## Historical ARM64 limitation

The project requires Lightkurve, Astropy, and PyTorch for the complete telescope-data and CNN workflow. The earlier Windows ARM64 Python environment can run NumPy, SciPy, scikit-learn, Matplotlib, the BLS implementation, baseline models, Stage 2, and all synthetic validation tests.

That ARM64 environment could not install the full astronomy/CNN stack: Lightkurve 2.6 requires `pandas < 3`, but no compatible Windows ARM64 pandas-2 wheel is available; its Astropy dependency also needs `pyerfa`, for which this environment lacks a binary wheel. PyTorch publishes no compatible package for this interpreter.

Use a supported x86_64 Linux/macOS/Windows environment with Python 3.11 and install the locked project dependencies there before running:

```bash
python -m pip install -e ".[dev]"
python -m transit_hunter.coverage --labels data/metadata/labels_snapshot.csv
```

Do not replace Lightkurve with a mixed-cadence data source to work around this limitation. The frozen catalogue, coverage/split logic, preprocessing, BLS, baseline, Stage 2, and report layers remain portable and tested.
