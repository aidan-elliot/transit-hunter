# Transit Hunter implementation plan

## Objective and final deliverables

**Primary research question:** Does a diagnostic second-stage classifier reduce false-positive acceptance more effectively than a Stage 1 model that sees only transit-shape views?

The graded deliverable is a research report in PDF or Word format. The repository is its reproducibility record. The final submission therefore needs:

1. a frozen TOI label snapshot and full provenance;
2. a reproducible pipeline that makes one model-ready sample per eligible TOI;
3. baseline, Stage 1, and Stage 2 experiments evaluated on a held-out temporal test set;
4. figures, tables, and a brief explanatory statement linking the results to cosmology and exoplanet prevalence;
5. correct, verifiable references and a public repository link.

The approved proposal, assignment instructions, and instructor feedback are preserved in `sources/`. The feedback adds one non-negotiable reporting requirement: cosmological significance must remain visible alongside the machine-learning work.

## Study design decisions to lock before model work

| Decision | Rule |
| --- | --- |
| Unit of analysis | One TOI (one transit-like signal) per sample. |
| Core labels | `CP` is positive; `FP` and `FA` are negative. `PC`, `APC`, and `KP` are excluded from supervised training. |
| Telescope product | Only SPOC 120-second TESS light curves for the core experiment. No mixing with 20-second or FFI products. |
| Eligible population | The subset of labelled TOIs with usable SPOC 2-minute coverage after deterministic data-quality checks. Eligibility must be recorded before splitting. |
| Grouping | All TOIs for the same TIC stay in one partition. TIC IDs may legitimately map to multiple TOIs. |
| Split | Chronological using `toi_created`, with TIC grouping. Oldest labels train, later labels validate, newest mature labels test. |
| Leakage control | Catalogue period/midpoint can help debugging and candidate matching, but must not be model input or define final inference features. Formal samples use BLS-derived candidate parameters. |
| Main comparison | Same Stage 1 candidate set; compare Stage 1 alone against Stage 1 + Stage 2 at a validation-selected operating threshold. |
| Test discipline | The temporal test set is sealed until pipeline and thresholds are chosen. |

## Work packages and acceptance gates

### 0. Environment, configuration, and run tracking

**Implement**

- Create a Python 3.11 virtual environment and install the locked project dependencies.
- Add a lock file or fully pinned requirements export after the environment is proven to work.
- Add `configs/experiment.yaml` for shared random seed, directories, data version, device, and evaluation threshold policy.
- Add a small `RunManifest` utility that records git revision, configuration hash, package versions, input catalogue hash, run time, and output paths.
- Add `make`/PowerShell task aliases or documented commands for `catalog`, `pilot`, `build-dataset`, `train-baseline`, `train-stage1`, `train-stage2`, and `evaluate`.

**Acceptance gate**

- A clean environment can run `pytest -q` and the catalogue audit from the stored raw CSV.
- Every generated experiment folder contains a machine-readable run manifest.

### 1. Catalogue eligibility and temporal split

**Implement**

- Extend `catalog.py` with deterministic date parsing, source-row validation, and a saved eligibility table.
- Implement `splits.py` and `configs/split.yaml` so boundaries are selected from mature labels only, not hard-coded before inspection.
- Produce a candidate availability manifest by querying each supervised TIC for SPOC 120-second coverage without downloading full sectors.
- Define a pre-processing eligibility policy: valid TOI/TIC IDs, finite period and midpoint, at least one usable sector, minimum point/transit count, and no unrecoverable BLS failure.
- Freeze `eligible_tois.csv`, `split_assignments.csv`, and their hashes in `data/metadata/`.

**Checks**

- TOI IDs are unique in every saved table.
- No TIC crosses train/validation/test.
- Class counts, TIC counts, date ranges, and excluded-reason counts are reported by partition.
- The plan names the final temporal boundaries and documents why the test labels are mature.

**Notebook/outputs**

- Extend `00_catalog_audit.ipynb` with availability and split-audit cells.
- Add `reports/figures/catalogue_timeline.png` and `reports/tables/split_summary.csv`.

### 2. Light-curve acquisition and pilot quality assurance

**Implement**

- Expand `download.py` to query and download only SPOC 120-second light curves for explicitly listed TIC IDs.
- Cache files under `data/raw/` using a stable TIC/sector filename scheme; never bulk-download sectors.
- Save `download_manifest.csv` with TOI, TIC, sector, cadence, product author, URL/identifier, status, byte count, and failure reason.
- Add retries with bounded backoff and a resume mode; treat unavailable data as an eligibility result, not a silent failure.
- Start with a stratified pilot (for example 20 CP, 20 FP/FA, spread across time and magnitude) before the full catalogue.

**Checks**

- Confirm every retained pilot file is SPOC, 120-second cadence, and uses Lightkurve's default quality mask.
- Plot raw and quality-filtered light curves for representative CP, FP, and FA cases.
- Record download rate, failure reasons, sectors per TOI, and disk use.

**Notebook/outputs**

- Implement `01_lightcurve_sanity_check.ipynb`.
- Save a short pilot audit and representative figures to `reports/`.

### 3. Deterministic preprocessing and BLS candidate construction

**Implement**

- Implement `preprocess.py` functions for quality masking, NaN removal, robust outlier handling, normalization, and long-term trend flattening.
- Implement `features.py` functions to stitch eligible sectors, create a BLS period grid, find BLS candidates, phase-fold, and bin views.
- Keep catalogue ephemerides in a diagnostics-only column. During debugging, calculate BLS-to-catalogue period agreement; during formal construction, retain the BLS-derived period, epoch, depth, duration, and power as the candidate inputs.
- Establish fixed global and local view resolutions, phase windows, binning rules, missing-bin fill policy, and feature schema in `configs/dataset.yaml`.
- Serialize each sample in a versioned, compact format (for example `.npz` plus a metadata row), not an opaque notebook-only object.

**Diagnostic features for Stage 2**

- BLS period, depth, duration, and power/SNR;
- observed-transit count and sector-to-sector consistency;
- odd/even depth difference;
- secondary-eclipse depth/significance;
- transit symmetry;
- optional centroid-shift features only when target-pixel data is explicitly requested and available.

**Checks**

- Unit-test every transform with synthetic transit/no-transit curves.
- Verify all output arrays are finite, fixed-shape, and associated with a single TOI.
- Compare BLS period recovery to catalogue period only as a diagnostic; report recovery rate by class and do not pass the catalogue period to a model.
- Visually inspect at least 10 examples per class before full processing.

**Notebook/outputs**

- Implement `02_preprocessing_and_bls.ipynb`.
- Save a dataset card update, feature schema, processing manifest, and representative global/local plots.

### 4. Full dataset build and audit

**Implement**

- Run the validated pipeline over all eligible TOIs partition by partition.
- Keep raw FITS ignored; track only metadata, hashes, configuration, and release-managed processed artefacts.
- Generate `dataset_manifest.json` containing the source catalogue hash, processing-config hash, number of input sectors, number of produced samples, failure reasons, array schema, and split counts.
- Add `data.py` or an equivalent dataset reader with no random transformation in evaluation mode.

**Acceptance gate**

- Every train/validation/test record has exactly one split and one model-ready sample or a documented exclusion reason.
- No raw filename, TIC, TOI, or processing artefact appears in more than one partition.
- A fresh reader can load every sample and reproduce summary statistics from the manifest.

### 5. Non-deep-learning baseline

**Implement**

- Implement standardisation, imputation policy, and a logistic-regression baseline on BLS/diagnostic features.
- Add a random-forest baseline only if it is treated as a secondary comparison, with hyperparameters selected on validation data.
- Implement `train.py` to fit only on training TICs and write fitted transforms/checkpoints to the run directory.
- Implement `evaluate.py` to report ROC-AUC, PR-AUC, precision, recall, F1, specificity, confusion matrix, and false-positive rate.

**Acceptance gate**

- Baseline results are reported separately for validation and sealed test data.
- The report includes class prevalence and a precision-recall curve; ROC-AUC alone is insufficient for the imbalanced problem.
- All thresholds are selected on validation data and copied unchanged to the test evaluation.

**Notebook/outputs**

- Implement `03_baseline.ipynb`.
- Save `baseline_metrics.json`, confusion matrices, ROC and precision-recall figures, and feature-coefficient/importances table.

### 6. Stage 1 transit-shape model

**Implement**

- Implement a compact two-input PyTorch CNN: one branch for the global phase view and one for the local view, merged before classification.
- Define deterministic normalization, class weighting or a training-only sampler, early stopping, checkpoint selection by validation PR-AUC, and fixed seeds.
- Add model-shape/unit tests and a CPU smoke-test run on a small subset.
- Keep the CNN architecture modest and document parameter count, epochs, optimiser, learning-rate schedule, and hardware.

**Acceptance gate**

- The model can overfit a tiny controlled subset as a pipeline sanity check, then produce stable validation results across at least three seeds.
- Training/validation curves show no unexplained leakage or divergence.
- The final Stage 1 checkpoint and its exact configuration are saved.

**Notebook/outputs**

- Implement `04_stage1_models.ipynb` for CNN training and its planned LSTM/Transformer comparison.
- Save learning curves, saliency/occlusion examples if feasible, and the Stage 1 candidate scores used by Stage 2.

### 7. Stage 2 diagnostic classifier and ablation

**Implement**

- Define Stage 2 inputs as Stage 1 score plus diagnostics computed without catalogue ephemeris leakage.
- Train a transparent initial classifier (logistic regression or calibrated gradient-boosted tree) before considering a more complex architecture.
- Calibrate Stage 1 and Stage 2 probabilities on validation data if calibration changes operational thresholding.
- Compare, on the same held-out records:
  1. BLS-feature baseline;
  2. Stage 1 only;
  3. Stage 2 diagnostics only;
  4. Stage 1 score + Stage 2 diagnostics;
  5. optional no-odd/even and no-secondary-eclipse ablations.

**Primary success criterion**

- At the validation-selected Stage 1 recall target, Stage 1 + Stage 2 lowers false-positive acceptance on the temporal test set relative to Stage 1 alone. Report the absolute count/rate change and uncertainty, not only a percentage improvement.

**Statistical reporting**

- Use TIC-grouped bootstrap confidence intervals for the primary rate difference.
- Separate FP and FA subgroup results where sample sizes allow.
- Report failures and ambiguous cases with representative light curves rather than hiding them.

**Notebook/outputs**

- Implement `05_stage2_ablation.ipynb`.
- Save an ablation table, operating-point table, reliability/calibration plot, and error-analysis gallery.

### 8. Architecture and transfer-learning extensions

These are extensions, not blockers for the core result.

- Compare LSTM and compact Transformer with the same data split, input views, preprocessing version, seed protocol, and validation tuning budget as the CNN.
- Attempt Kepler-to-TESS transfer learning only after a successful core TESS model. Document differences in cadence, label definitions, and preprocessing; never merge Kepler and TESS samples without an explicit domain-shift analysis.
- Add centroid shifts only after the non-pixel Stage 2 ablation is complete, because target-pixel acquisition substantially increases data and implementation complexity.

**Acceptance gate**

- Each extension answers one pre-stated question and cannot displace the core two-stage result if incomplete.

### 9. Final evaluation, report, and reproducibility release

**Report structure**

1. Abstract and research question.
2. Cosmological context: transit detections, false positives, and how reliable occurrence estimates inform the prevalence of planetary systems.
3. Data provenance, label policy, eligibility, and temporal TIC-grouped split.
4. Methods: preprocessing, BLS, model architectures, and leakage controls.
5. Results: baseline, Stage 1, Stage 2, primary ablation, confidence intervals, and error analysis.
6. Discussion: interpretation, limitations, selection effects, cadence/data-availability limits, and implications for exoplanet population studies.
7. Brief explanatory statement explicitly connecting the work to PHY4000 themes.
8. References and repository link.

**Reproducibility checklist**

- A fresh user can recreate the frozen catalogue from the saved raw response and query.
- Every result links to one run manifest, config file, dataset manifest, checkpoint, and figure script/notebook.
- The README documents the full command order and hardware/runtime expectations.
- All citations resolve to genuine source material and are checked against `docs/references.bib` before submission.
- Generate the final PDF/Word report only after checking figure labels, units, class definitions, date ranges, and references.

## Recommended execution order

```text
catalogue snapshot (complete)
        ↓
coverage manifest + grouped temporal split
        ↓
small stratified download/preprocessing pilot
        ↓
fixed sample schema + full eligible dataset build
        ↓
BLS baseline → Stage 1 CNN → Stage 2 ablation
        ↓
architecture comparison / transfer learning (time permitting)
        ↓
sealed temporal test → report and reproducibility release
```

## Definition of done

The project is complete when the report can truthfully state the result of the primary Stage 1-versus-Stage 1-plus-Stage 2 comparison on a pre-defined temporal, TIC-grouped test set; the repository can reproduce the result from its manifests and configuration; limitations and failed cases are reported; and the cosmological significance is explicitly discussed.
