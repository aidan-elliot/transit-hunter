# Graph Report - public  (2026-08-14)

## Corpus Check
- Corpus is ~19,427 words - fits in a single context window. You may not need a graph.

## Summary
- 43 nodes · 74 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 91% EXTRACTED · 8% INFERRED · 1% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Demo State and Verdicts
- False-Negative Gallery
- Light-Curve Rendering
- Project and Research
- False-Positive Gallery
- Interactive Case Review
- Folded Signal Views
- Stage-Two Scores

## God Nodes (most connected - your core abstractions)
1. `Transit Classification Error Gallery` - 12 edges
2. `Global Time-Series View` - 7 edges
3. `Local Time-Series View` - 7 edges
4. `renderCurve()` - 5 edges
5. `Transit Hunter` - 5 edges
6. `Interactive Candidate-Vetting Demo` - 5 edges
7. `False Positive Classification` - 5 edges
8. `False Negative Classification` - 5 edges
9. `Two-Stage Neural Network` - 4 edges
10. `TOI 5133.01 (false positive, Stage 2 = 0.745)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Stage 2 Score Separation Between Error Classes` --conceptually_related_to--> `False Positive Classification`  [INFERRED]
  assets/error_gallery.png → assets/error_gallery.png  _Bridges community 4 → community 7_
- `Stage 2 Score Separation Between Error Classes` --conceptually_related_to--> `False Negative Classification`  [INFERRED]
  assets/error_gallery.png → assets/error_gallery.png  _Bridges community 1 → community 7_
- `Transit Hunter` --references--> `Interactive Candidate-Vetting Demo`  [EXTRACTED]
  index.html → index.html  _Bridges community 3 → community 5_
- `Two-Stage Neural Network` --references--> `Folded TESS Light Curves`  [EXTRACTED]
  index.html → index.html  _Bridges community 3 → community 6_
- `Interactive Candidate-Vetting Demo` --references--> `Representative TOI Case`  [EXTRACTED]
  index.html → index.html  _Bridges community 5 → community 6_

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Candidate Verdict Comparison** — public_index_human_candidate_classification, public_index_model_verdict, public_index_catalogue_outcome [EXTRACTED 1.00]
- **Dual-Scale Light-Curve Inspection** — public_index_representative_toi_case, public_index_global_folded_view, public_index_local_transit_window, public_index_human_candidate_classification [EXTRACTED 1.00]
- **False Positive Example Cohort** — public_assets_error_gallery_false_positive, public_assets_error_gallery_toi_5133_01, public_assets_error_gallery_toi_6711_01, public_assets_error_gallery_toi_6693_01 [EXTRACTED 1.00]
- **False Negative Example Cohort** — public_assets_error_gallery_false_negative, public_assets_error_gallery_toi_5616_01, public_assets_error_gallery_toi_6383_01, public_assets_error_gallery_toi_5747_01 [EXTRACTED 1.00]

## Communities (8 total, 1 thin omitted)

### Community 0 - "Demo State and Verdicts"
Cohesion: 0.25
Nodes (5): cases, elements, modelCall(), showModel(), thresholds

### Community 1 - "False-Negative Gallery"
Cohesion: 0.57
Nodes (7): Transit Classification Error Gallery, False Negative Classification, Global Time-Series View, TOI 5616.01 (false negative, Stage 2 = 0.194), TOI 5747.01 (false negative, Stage 2 = 0.208), TOI 6383.01 (false negative, Stage 2 = 0.206), Unlabeled Near-Unity Time-Series Metric (likely normalized flux)

### Community 2 - "Light-Curve Rendering"
Cohesion: 0.40
Nodes (6): cropCurve(), curveDataUri(), loadRepresentativeCases(), renderCurve(), resetCase(), updateHeroCurve()

### Community 3 - "Project and Research"
Cohesion: 0.40
Nodes (6): Held-Out Catalogue Observations, Transit Hunter Results Summary, TESS Candidate Vetting, Transit Hunter, Transit Hunter GitHub Repository, Two-Stage Neural Network

### Community 4 - "False-Positive Gallery"
Cohesion: 0.60
Nodes (5): False Positive Classification, Local Time-Series View, TOI 5133.01 (false positive, Stage 2 = 0.745), TOI 6693.01 (false positive, Stage 2 = 0.727), TOI 6711.01 (false positive, Stage 2 = 0.731)

### Community 5 - "Interactive Case Review"
Cohesion: 1.00
Nodes (4): Catalogue Outcome, Human Candidate Classification, Interactive Candidate-Vetting Demo, Model Verdict

### Community 6 - "Folded Signal Views"
Cohesion: 0.83
Nodes (4): Folded TESS Light Curves, Global Folded Light-Curve View, Local Transit-Window View, Representative TOI Case

## Ambiguous Edges - Review These
- `Transit Classification Error Gallery` → `Unlabeled Near-Unity Time-Series Metric (likely normalized flux)`  [AMBIGUOUS]
  assets/error_gallery.png · relation: references

## Knowledge Gaps
- **7 isolated node(s):** `cases`, `thresholds`, `elements`, `Held-Out Catalogue Observations`, `Transit Hunter Results Summary` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Transit Classification Error Gallery` and `Unlabeled Near-Unity Time-Series Metric (likely normalized flux)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `Transit Hunter` connect `Project and Research` to `Interactive Case Review`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Interactive Candidate-Vetting Demo` connect `Interactive Case Review` to `Project and Research`, `Folded Signal Views`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Transit Classification Error Gallery` connect `False-Negative Gallery` to `False-Positive Gallery`, `Stage-Two Scores`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `cases`, `thresholds`, `elements` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._