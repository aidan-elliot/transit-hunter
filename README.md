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

The next implemented step is an auditable eligibility and temporal-split foundation. `transit_hunter.coverage` queries each TIC once for SPOC 120-second availability without downloading FITS products; `transit_hunter.eligibility` records every inclusion/exclusion reason; and `transit_hunter.splits` places whole TIC groups into chronological partitions. Each later training run must write a manifest with hashes of its configuration and inputs using `transit_hunter.provenance`.

Do not create `split_assignments.csv` from the complete label catalogue yet: first build and freeze the light-curve coverage/eligibility manifest.

The complete runtime needs Lightkurve/Astropy/PyTorch; see [runtime compatibility](docs/runtime-compatibility.md) for the current Windows ARM64 limitation and a compatible-environment command sequence.

## Planned workflow

1. Download only SPOC 2-minute light curves for TIC IDs in the frozen catalogue.
2. Clean, flatten, and search each curve with BLS; make global, local, and diagnostic samples.
3. Establish BLS-feature baseline models, then a global + local CNN.
4. Compare LSTM and compact Transformer variants.
5. Evaluate a diagnostic second stage using temporal, TIC-grouped partitions.

See [docs/dataset-card.md](docs/dataset-card.md), [docs/methodology.md](docs/methodology.md), and [docs/references.bib](docs/references.bib).

For the exact command order and report evidence map, see [docs/execution-guide.md](docs/execution-guide.md) and [docs/report-outline.md](docs/report-outline.md).
