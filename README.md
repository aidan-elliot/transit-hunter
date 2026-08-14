# Transit Hunter

Transit Hunter is a reproducible TESS transit-vetting project. Its core question is whether a second diagnostic stage rejects false positives more effectively than a transit-shape classifier alone.

## First milestone: a frozen label catalogue

The initial dataset has one row per TESS Object of Interest (TOI), using NASA Exoplanet Archive's live `toi` table.

- Positive: `CP` (confirmed planet)
- Negative: `FP` (false positive) and `FA` (false alarm)
- Excluded from the supervised dataset: `PC`, `APC`, `KP`, and unrecognised dispositions

`data/metadata/` contains the exact ADQL query, its raw CSV response, a supervised `labels_snapshot.csv`, and a JSON manifest with its SHA-256 hash. The snapshot records the retrieval date rather than presenting a mutable catalogue as a static source.

To reproduce or refresh it:

```powershell
python -m pip install -e ".[dev]"
transit-hunter-freeze-catalog --retrieved-on 2026-08-13
```

Or open [notebooks/00_catalog_audit.ipynb](notebooks/00_catalog_audit.ipynb). The notebook downloads the current table, applies the label policy, audits TOI/TIC identity relationships, and writes a new frozen snapshot.

## Reproducible run foundation

The implemented real-data foundation is an auditable eligibility and temporal-split pipeline. `transit_hunter.coverage` queries each TIC once for SPOC 120-second availability without downloading FITS products; `transit_hunter.eligibility` records every inclusion/exclusion reason; and `transit_hunter.splits` places whole TIC groups into chronological partitions. Each later training run must write a manifest with hashes of its configuration and inputs using `transit_hunter.provenance`.

The frozen split was created only after the SPOC coverage and eligibility manifests: 1,812 eligible TOIs across 1,691 TICs, partitioned into 1,240 train, 287 validation, and 285 sealed test records.

The complete runtime was validated on Windows x64 with Python 3.11; see [runtime compatibility](docs/runtime-compatibility.md).

## Completed real-data workflow

1. Download only SPOC 2-minute light curves for TIC IDs in the frozen catalogue.
2. Clean, flatten, and search each curve with BLS; make global, local, and diagnostic samples.
3. Establish BLS-feature baseline models, then a global + local CNN.
4. Compare LSTM and compact Transformer variants.
5. Evaluate a diagnostic second stage using temporal, TIC-grouped partitions.

See [docs/dataset-card.md](docs/dataset-card.md), [docs/methodology.md](docs/methodology.md), and [docs/references.bib](docs/references.bib).

For the exact command order and report evidence map, see [docs/execution-guide.md](docs/execution-guide.md) and [docs/report-outline.md](docs/report-outline.md).

## Real result

The selected two-view CNN and diagnostic Stage 2 were tuned on validation only and evaluated once on the sealed temporal test set. Stage 2 reduced accepted false positives from 87 to 70 (FPR difference -0.118; TIC-grouped bootstrap 95% interval -0.184 to -0.053), while test recall declined from 0.851 to 0.716. See `reports/results_summary.md` for the required interpretation and limitations.

```powershell
python scripts/audit_coverage_resumable.py
python -m transit_hunter.splits --input data/metadata/eligible_tois.csv
python scripts/build_real_dataset.py
python scripts/run_real_experiments.py
python scripts/generate_real_report_artifacts.py
```
