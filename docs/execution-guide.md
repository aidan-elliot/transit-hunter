# Execution guide

## Compatible environment

Run the full TESS/CNN workflow on a Python 3.11 environment that supports Lightkurve, Astropy, and PyTorch:

```bash
python -m pip install -e ".[dev]"
python -m transit_hunter.catalog --raw-csv data/metadata/toi_catalogue_raw_2026-08-13.csv --retrieved-on 2026-08-13
python -m transit_hunter.coverage --labels data/metadata/labels_snapshot.csv
python -m transit_hunter.splits --input data/metadata/eligible_tois.csv
```

Before downloading the full catalogue, run the stratified pilot from notebook 01 and inspect its products. `coverage` performs metadata searches only; `download.load_tic_arrays()` downloads the fixed SPOC 120-second product when called by a dataset loader.

## Correct experiment order

1. Freeze coverage and eligibility outputs.
2. Freeze TIC-grouped temporal assignments using the eligible table only.
3. Build samples into a versioned `data/processed/` release and retain `samples_manifest.csv`.
4. Construct a diagnostic table from saved samples; join labels and frozen split assignments by TOI.
5. Train the baseline and Stage 1 on train only; tune thresholds on validation only.
6. Cross-fit Stage 1 training scores before fitting Stage 2; call `train_two_stage_feature_experiment()` to enforce that discipline.
7. Generate test figures and the result summary only after model/threshold choices are fixed.

## Local validation completed here

This Windows ARM64 workspace cannot install the Lightkurve/Astropy/PyTorch stack; see `runtime-compatibility.md`. The portable pipeline components run here with synthetic tests: preprocessing, injected-transit BLS recovery, sample serialization, grouped splits, baseline/Stage 2 training, bootstrap evaluation, figures, provenance, and report summary generation.
