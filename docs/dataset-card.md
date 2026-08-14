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
