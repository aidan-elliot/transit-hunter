# Dataset card: frozen TESS TOI labels

## Purpose

This catalogue is the label source for a binary transit-vetting experiment, not a discovery catalogue. Each record represents one TESS Object of Interest (TOI), a transit-like signal associated with a TESS Input Catalog (TIC) target.

## Source and snapshot policy

The source is NASA Exoplanet Archive's live `toi` table. The project stores the ADQL query, raw CSV response, retrieval date, and SHA-256 in `data/metadata/`. The online TOI table is updated roughly weekly, so results must always name the specific snapshot used.

## Label policy

| TFOPWG disposition | Dataset treatment |
| --- | --- |
| `CP` | positive, label `1` |
| `FP`, `FA` | negative, label `0` |
| `PC`, `APC` | excluded: unresolved |
| `KP` | separate file: different discovery history |

## Splitting rule

TOIs from one TIC must remain together in a single partition. A TIC can have more than one TOI, so TIC IDs are not expected to be unique across signal rows. The audit instead verifies unique TOI IDs and reports TIC multiplicity.

## Intended use and limits

This dataset supports comparative classification research. It does not validate new planets and must not be used as the sole basis for scientific claims about an individual candidate. The labels inherit archive and follow-up selection effects.

## Frozen SPOC 2-minute release (2026-08-14)

The supervised snapshot contains 2,099 TOIs across 1,976 TICs. The SPOC 120-second metadata audit found coverage for 1,834 TOIs; 265 had no product. Twenty-two covered rows lacked a valid orbital period required by the pre-declared eligibility audit, leaving 1,812 eligible TOIs across 1,691 TICs.

The TIC-grouped temporal split contains 1,240 train, 287 validation, and 285 sealed test TOIs. All 1,812 eligible records produced one finite model-ready sample with a 201-bin global view, 101-bin local view, and BLS-derived diagnostics. Catalogue period and midpoint are not formal model inputs. The first acquisition pass recorded 124 transient network failures; all recovered on the manifested retry.

Raw SPOC FITS products are target-specific, cached under ignored storage, and are not part of the repository release. `data/metadata/dataset_manifest.json`, `data/processed/spoc_2min_v1/samples_manifest.csv`, and the run manifest define the reproducible release.
