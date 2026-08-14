# Two-stage pipeline results summary

## Pre-registered comparison

The operating thresholds were selected on the validation partition at a target recall of 0.90; the temporal test set was then evaluated without retuning.

| Model | Test PR-AUC | Test ROC-AUC | Recall | Precision | F1 | False-positive rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage 1 | 0.664 | 0.689 | 0.851 | 0.580 | 0.690 | 0.604 |
| Stage 1 + Stage 2 | 0.719 | 0.711 | 0.716 | 0.591 | 0.647 | 0.486 |

At the validation-selected operating threshold, the Stage 2 minus Stage 1 false-positive-rate difference was -0.118 (TIC-grouped bootstrap 95% interval -0.184 to -0.053). Negative values favour the two-stage pipeline.

This is 17 fewer accepted false positives (87 to 70) on the sealed test set. Test recall also changed from 0.851 to 0.716, despite equal target recall on validation, so the false-positive improvement must be interpreted with this temporal-generalisation trade-off.

## Interpretation boundaries

These values assess discrimination among the frozen, eligible TOI records. They do not constitute a validation of newly discovered planets. The final discussion must connect improved false-positive handling to reliable estimates of exoplanet occurrence while describing catalogue, cadence, and selection limitations.

## Cosmological relevance

Reliable false-positive control supports less biased estimates of planet occurrence and the prevalence of planetary systems, quantities that inform how common planetary environments are in the Galaxy. This experiment improves candidate-vetting evidence; it does not itself measure an occurrence rate or establish a new planet.

## Limitations

The result is conditional on the frozen TOI labels, availability of SPOC 120-second products, the deterministic preprocessing/BLS configuration, and temporal catalogue shift. The lower Stage 2 test recall shows that equal validation recall did not transfer perfectly to the newest labels. TOI catalogue labels and selection effects are not a random sample of all stars or transiting planets, and no individual model score is a discovery or validation claim.
