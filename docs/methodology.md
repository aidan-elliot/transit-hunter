# Methodology

The core experiment has two stages. Stage 1 classifies global and local phase-folded light-curve views. Stage 2 adds BLS and folded-curve diagnostics to determine whether false positives can be rejected more effectively than by transit shape alone.

For each retained TIC, query only SPOC 120-second TESS light curves. Apply Lightkurve's default quality mask; remove invalid points and extreme outliers; normalize and flatten long-term trends; run BLS; match the strongest candidate to the known TOI period for construction; and generate global, local, and feature views. The formal pipeline must use BLS-derived candidate parameters rather than the catalogue ephemeris.

The initial baseline is a logistic regression or random forest over BLS diagnostics. The primary Stage 1 model is a CNN with global and local inputs. An LSTM and compact Transformer are architecture comparisons. Stage 2 uses period, depth, duration, BLS power/SNR, observed-transit count, odd/even difference, secondary eclipse evidence, symmetry, and sector consistency; centroid signals are an optional extension.

Partitions are chronological, using older labelled TOIs for training, later labels for validation, and the newest mature labels for a final test. TIC groups never cross partitions. Still-unlabelled new data is reserved for a live demonstration, not a labelled score.
