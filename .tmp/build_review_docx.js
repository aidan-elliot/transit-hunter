const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, LevelFormat, BorderStyle,
  WidthType, ShadingType, PageNumber
} = require('./docx-review-tool/node_modules/docx');

const outputPath = 'C:\\Users\\aidan\\OneDrive\\Documents\\ChatGPT\\Final Project - PHY4000\\Reducing_false_positives_PHY4000_Review_Report.docx';

const navy = '17365D';
const blue = 'D9EAF7';
const pale = 'F3F6F9';
const green = 'E2F0D9';
const amber = 'FFF2CC';
const red = 'FCE4D6';
const border = { style: BorderStyle.SINGLE, size: 4, color: 'B7C9D6' };
const borders = { top: border, bottom: border, left: border, right: border };

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, line: 276 },
    alignment: opts.alignment,
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italics, size: opts.size })],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { after: 80, line: 276 },
    children: [new TextRun(text)],
  });
}

function issue(severity, location, description, sourceSays, paperSays, action) {
  const shade = severity === 'CRITICAL' ? red : severity === 'MODERATE' ? amber : pale;
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1500, 7860],
    rows: [
      new TableRow({ children: [
        new TableCell({ borders, width: { size: 1500, type: WidthType.DXA }, shading: { fill: shade, type: ShadingType.CLEAR }, margins: { top: 100, bottom: 100, left: 120, right: 120 }, children: [para(severity, { bold: true, after: 0 })] }),
        new TableCell({ borders, width: { size: 7860, type: WidthType.DXA }, margins: { top: 100, bottom: 100, left: 120, right: 120 }, children: [
          para(location, { bold: true, after: 60 }),
          para(description, { after: 60 }),
          para(`Requirement/source: ${sourceSays}`, { italics: true, after: 40 }),
          para(`Draft: ${paperSays}`, { italics: true, after: 40 }),
          para(`Recommended action: ${action}`, { after: 0 }),
        ] }),
      ] }),
    ],
  });
}

function cell(text, width, fill, bold = false) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 90, bottom: 90, left: 110, right: 110 },
    children: [para(text, { bold, after: 0 })],
  });
}

const scoreRows = [
  ['Content and scientific quality', '40', '36', 'Strong question, honest interpretation, real-data experiment; deductions for baseline design and uncertainty framing.'],
  ['Course alignment and professor feedback', '20', '20', 'The light-to-measurement-to-selection-effects-to-populations chain is explicit and sustained.'],
  ['Effort and reproducibility', '20', '18', 'Exceptional artifact trail and leakage controls; exact run revision/provenance statement needs correction.'],
  ['Grammar and presentation', '10', '9', 'Professional and readable; some dense methods prose and figure-layout issues remain.'],
  ['References and source integrity', '10', '9', 'High-quality primary/official sources with complete matching; a few technical claims could use direct citations.'],
  ['Total', '100', '92', 'A-range draft, subject to the instructor\'s actual grading scale and rubric.'],
];

const scoreTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2450, 850, 850, 5210],
  rows: [
    new TableRow({ children: [cell('Category', 2450, navy, true), cell('Max', 850, navy, true), cell('Score', 850, navy, true), cell('Rationale', 5210, navy, true)] }),
    ...scoreRows.map((r, i) => new TableRow({ children: [cell(r[0], 2450, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1), cell(r[1], 850, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1), cell(r[2], 850, i === scoreRows.length - 1 ? blue : undefined, true), cell(r[3], 5210, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1)] })),
  ],
});

const feedbackRows = [
  ['Preserve the approved two-stage pipeline', 'Meets', 'Sections 4.2-4.3 implement a global/local CNN followed by a diagnostic classifier; Figure 3 traces the full pipeline.'],
  ['Keep the report an astronomy investigation, not only an ML report', 'Meets strongly', 'Sections 2, 7, and 8 explain transit physics, false-positive mechanisms, observational limits, and catalogue interpretation.'],
  ['Connect results to exoplanet prevalence and planetary populations', 'Meets strongly', 'The explanatory statement and Section 8 connect completeness and reliability to occurrence-rate inference and planetary populations.'],
  ['Keep selection effects visible', 'Meets', 'Sections 3, 7, and 8 discuss catalogue maturity, product availability, cadence, geometry, instrument sensitivity, and follow-up selection.'],
  ['Make the link in the introduction, discussion, conclusion, and one-paragraph statement', 'Meets', 'The connection appears at lines 20, 24-32, 220-230, and 232-238. The required statement is one solid paragraph.'],
  ['Use careful candidate-vetting language', 'Meets strongly', 'The report repeatedly states that scores rank known candidates and do not confirm or statistically validate planets.'],
  ['Use frozen labels and target-level leakage controls', 'Meets strongly', 'The retrieval date, label policy, hashes, TIC-grouped temporal split, zero crossings, and cross-fitting are documented.'],
  ['Provide the planned comparison and figures', 'Mostly meets', 'Metrics, confusion matrices, curves, pipeline, learning curves, and failure cases are present. A true BLS-only baseline and a raw-light-curve/BLS illustration are missing.'],
];

const feedbackTable = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2800, 1450, 5110],
  rows: [
    new TableRow({ children: [cell('Professor/review condition', 2800, navy, true), cell('Finding', 1450, navy, true), cell('Evidence and qualification', 5110, navy, true)] }),
    ...feedbackRows.map((r) => new TableRow({ children: [cell(r[0], 2800), cell(r[1], 1450, r[1].startsWith('Meets') ? green : amber, true), cell(r[2], 5110)] })),
  ],
});

const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 140 }, children: [new TextRun({ text: 'Reducing false positives in TESS transit-candidate vetting', bold: true, size: 34, color: navy })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 260 }, children: [new TextRun({ text: 'Academic Review, Critique, and Mock Grade', bold: true, size: 26 })] }),
  para('Review date: August 14, 2026', { alignment: AlignmentType.CENTER, after: 40 }),
  para('Draft reviewed: PHY4000_Final_Report_Draft.md', { alignment: AlignmentType.CENTER, after: 260 }),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Executive verdict')] }),
  para('This is a strong A-range course-project draft. It answers a focused scientific question with real TESS data, reports an unfavourable trade-off rather than hiding it, and connects the technical pipeline to PHY4000 more effectively than most machine-learning astronomy projects do. The professor\'s main request was to keep the broader significance visible beside the technical work. The draft clearly meets that request in the explanatory statement, introduction, astronomical-significance section, and conclusion.'),
  para('The central revision is conceptual precision: Stage 2 did not deliver an across-the-board improvement. It improved ranking and false-positive rejection at the chosen operating point, but it barely changed precision and materially reduced recall and F1. The conclusion should therefore call the hypothesis partially supported, not open with an unqualified “yes.”'),
  para('Mock grade: 92/100 (A range) after normal finalization. If submitted exactly as the present Markdown file, the unresolved placeholders, non-accepted file type, missing page numbers, and unrendered Mermaid diagram would lower the practical submission grade and could create avoidable compliance problems.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Mock grade')] }),
  scoreTable,
  para('This scoring model is an informed mock rubric based on the Learner’s Manual categories and the professor’s proposal feedback. It is not the instructor’s official weighting.', { italics: true, after: 200 }),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Does the report explain the course connection understandably?')] }),
  para('Yes. The report builds a coherent chain that a non-specialist can follow:'),
  bullet('Week 4: distant objects are understood through information carried by light.'),
  bullet('Week 6: telescopes and detectors turn changing brightness into a time series or light curve.'),
  bullet('Week 10: periodic brightness dips can indicate transits, but geometry, sensitivity, and impostors shape what surveys detect.'),
  bullet('The project: BLS, phase folding, a CNN, and diagnostic features convert those measurements into a ranked candidate list.'),
  bullet('Scientific consequence: false positives affect catalogue reliability, missed planets affect completeness, and both affect inferences about planet occurrence and planetary populations.'),
  bullet('Week 13: a candidate is not a confirmed planet, and a potentially habitable world is not evidence of life.'),
  para('That chain is accurate, relevant, and understandable. It does not force a superficial Big Bang or dark-matter connection onto an exoplanet project. It uses the course’s broader observational-astronomy theme and the explicitly allowed exoplanet topic. The strongest passage is Section 8, especially the explanation that 17 fewer accepted false positives and 19 fewer accepted confirmed planets cannot be reduced to one universal definition of “better.”'),
  para('The one weakness is continuity. Sections 4 through 6 become technically dense, so a general PHY4000 reader can temporarily lose the astronomical thread. One plain-language sentence after each major methods/results subsection would keep the connection visible throughout, for example: “Astronomically, this step tests whether the light-curve shape alone contains enough evidence to separate likely transits from impostors.”'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Professor feedback compliance')] }),
  feedbackTable,

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Critical issues before submission')] }),
  issue('CRITICAL', 'Identification block and final file', 'The current draft still contains three placeholders and is a Markdown file. The manual requires learner identification at the top, page numbers, an accepted Word/PDF-type format, and a filename containing the learner name and assignment.', 'Learner’s Manual, p. 10: accepted formats are .doc, .docx, .odt, .pdf, or .rtf; the first page must identify the learner and assignment; pages must be numbered.', 'Lines 2, 4, and 7 still say “Insert”; the file is PHY4000_Final_Report_Draft.md.', 'Fill all three fields, export to DOCX or PDF, add page numbers, render every figure, and use a final filename such as ElliotA_Final_Project_PHY4000.docx.'),
  issue('CRITICAL', 'Generative AI declaration and course-policy ambiguity', 'The report includes a good disclosure, which satisfies the specific declaration instruction on p. 15. However, p. 7 also says use of ChatGPT is plagiarism unless there is a valid reason or defence. The manual is internally inconsistent enough that written instructor confirmation is prudent.', 'Learner’s Manual, pp. 7 and 15: AI use is treated as plagiarism without a valid reason/defence, while declared and credited use is explicitly contemplated later.', 'Lines 244-246 transparently declare Codex’s role and state that the author reviewed and owns the final argument.', 'Keep the declaration and ask the professor to confirm that this disclosed use is acceptable before submission. Do not rely on p. 15 alone when p. 7 creates a zero/F risk.'),
  issue('MODERATE', 'Reproducibility statement, line 242', 'The run manifest records HEAD fe45cc4, but that commit does not contain scripts/run_real_experiments.py or data/metadata/dataset_manifest.json. The manifest also does not record whether the working tree was dirty. Therefore, “produced ... at Git revision fe45cc4” implies a stronger reproducibility guarantee than the repository currently proves.', 'Reproducibility requires the cited revision to contain the code and inputs needed to reproduce the run, or the report must clearly describe uncommitted state.', '“The sealed experiment was produced by scripts/run_real_experiments.py at Git revision fe45cc4...”', 'Point to a committed release that contains the exact run script, manifests, and artifacts, or rewrite this as “the run recorded repository HEAD fe45cc4 while later commits preserve the executable script and artifacts.” Ideally rerun or create a release manifest that records git dirty status and hashes the script itself.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Technical and argument critique')] }),
  issue('MODERATE', 'Conclusion, line 234', 'The opening “The answer is yes” is too categorical for the reported result. Stage 2 reduced FPR and raised ranking AUCs, but recall fell from 0.851 to 0.716, F1 fell from 0.690 to 0.647, and precision rose only from 0.580 to 0.591.', 'The primary question asks whether diagnostics improve false-positive rejection while retaining useful recall. The result supports only part of that proposition.', '“The answer is yes, with an important qualification.”', 'Replace with “The hypothesis was partially supported: Stage 2 improved ranking and false-positive rejection, but the validation-selected threshold did not preserve the intended recall on the temporal test set.”'),
  issue('MODERATE', 'Table 2 and Sections 4.2/6.1', 'The table presents four experiment rows, but the BLS/diagnostic baseline and diagnostics-only rows are numerically and methodologically identical. There are only three distinct fitted comparisons, and there is no isolated BLS-only baseline.', 'The earlier review recommended a simple BLS-feature baseline, CNN-only, diagnostics-only, and combined model to make the ablation interpretable.', '“The BLS/diagnostic baseline and the diagnostics-only Stage 2 row are identical...”', 'Either add a genuinely narrower BLS-only baseline or remove the duplicate row and explicitly describe the experiment as three distinct models. Do not let four rows visually imply four independent conditions.'),
  issue('MODERATE', 'Results and limitations, Sections 6-7', 'Precision and PR-AUC depend on class prevalence. The sealed test set is nearly balanced at 141 CP and 144 FP/FA, which is not the prevalence of an operational all-star or raw-TCE search. The report discusses selection effects but does not directly connect test prevalence to the reported precision.', 'Metric values conditioned on a curated candidate sample should not be generalized to a different candidate base rate.', 'The report calls precision the proportion of accepted candidates that are positive, but does not state that the 0.591 value is conditional on the test-set class mix.', 'Add one sentence: “Because the sealed test set is nearly balanced and consists of labelled TOIs, its precision and PR-AUC should not be transferred to an unfiltered TESS population with a different positive prevalence.”'),
  issue('MODERATE', 'Model uncertainty, Sections 4.2 and 5', 'The selected CNN is the best of three validation seeds, while the reported test metrics and Stage 2 comparison use only that selected model. The grouped bootstrap measures test-sample uncertainty conditional on the trained models; it does not include training-seed variability.', 'A model-selection result should distinguish sampling uncertainty from training/model uncertainty.', 'Figure 2 reports seed variation, but the limitations do not explain what the bootstrap leaves out.', 'State this limitation explicitly. If time permits, score all three Stage 1 seeds and their corresponding Stage 2 models on the sealed test once under a predeclared aggregation rule, or report the single-seed design as exploratory.'),
  issue('MODERATE', 'Reliability diagram, lines 194-198', 'The calibration conclusion is directionally reasonable, but the plot contains only 285 test records divided into quantile bins and shows no confidence bands or bin counts.', 'A calibration plot without uncertainty is descriptive, especially on a modest sample.', '“Both curves deviate from the diagonal, especially in bins supported by fewer observations.”', 'Call the plot descriptive, report the binning rule and counts, and avoid implying precise calibration differences. The phrase about fewer observations is also odd for quantile bins, which should have roughly similar counts.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Figures and presentation')] }),
  bullet('Figure 3 is Mermaid source, not a portable figure. It must be rendered to SVG or PNG before Word/PDF export.'),
  bullet('The professor/review plan called for a representative raw and phase-folded light curve. Figure 9 shows only folded global/local views. Add one compact raw -> cleaned/flattened -> BLS periodogram -> phase-folded example.'),
  bullet('Stage 1 and Stage 2 PR/ROC curves are in separate figures. Overlaying the models on shared PR and ROC axes would make the comparison immediate and reduce repetition.'),
  bullet('Figure 9 is extremely tall. At normal page width, six rows will be difficult to read. Split it into false positives and false negatives, use landscape orientation, or move the full gallery to an appendix while keeping two representative cases in the body.'),
  bullet('Figure 1 would communicate the temporal design better with vertical lines marking the train/validation and validation/test cut dates.'),
  bullet('The tables are clear and the confusion matrices are readable. Figure captions generally state the takeaway rather than merely naming the axes, which directly follows the earlier review guidance.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Citation and source integrity')] }),
  para('No fabricated or obviously mismatched references were found. This is one of the draft’s strongest areas.'),
  bullet('The reference list contains 18 entries, and all 18 are cited in the body. No unmatched in-text citation was found.'),
  bullet('Ten journal DOI records were independently matched to the stated titles, including the TESS mission paper, Sullivan false-positive simulations, Shallue and Vanderburg, Yu et al., ExoMiner, ExoMiner++, Bryson occurrence-rate reliability, the TOI catalogue, BLS, and the precision-recall paper.'),
  bullet('The Week 4, Week 6, Week 10, and Week 13 claims were checked against the supplied course PDFs. The draft accurately uses the course material on light, time monitoring/light curves, transits, observational limits, and the distinction between habitability and life.'),
  bullet('NASA Exoplanet Archive, NASA/HEASARC, MAST/STScI, and the Lightkurve software record are appropriate official or primary sources.'),
  bullet('A few technical claims would benefit from a direct citation: the odd/even and secondary-eclipse vetting discussion, the V-shaped-event interpretation, and the formal distinction between candidate vetting and statistical validation.'),
  para('There is no stated minimum number of references in the manual. Eighteen well-chosen references are more than adequate; adding low-value sources would weaken rather than strengthen the paper.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Wording, structure, and repetition')] }),
  bullet('The prose is polished, grammatically strong, and unusually candid about limitations.'),
  bullet('Define SPOC at first use and attach “(TFOPWG)” when first spelling out the TESS Follow-up Observing Program Working Group. PR-AUC and ROC-AUC should also be expanded in the abstract for a general course reader.'),
  bullet('The exact 17-false-positive/19-true-positive trade-off appears in the abstract, results, significance section, and conclusion. Most repetition is functional, but one occurrence could be shortened if page count becomes an issue.'),
  bullet('The report is 6,269 words. The course sets no length requirement, so this is not noncompliant, but Sections 4-6 could be tightened slightly for a broad cosmology-course audience.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Positive observations')] }),
  bullet('The report uses candidate-vetting language consistently and explicitly rejects confirmation/validation claims.'),
  bullet('The frozen catalogue snapshot, label policy, checksum, access date, target-grouped temporal split, zero TIC crossings, and cross-fitted Stage 2 training are all reported clearly.'),
  bullet('The sealed-test result is not cherry-picked into a success story. The loss of 19 true positives and the recall failure are placed beside the FPR improvement.'),
  bullet('The report distinguishes ranking metrics from a thresholded operating point and explains why accuracy is not the main measure.'),
  bullet('The astronomical significance section is specific: it explains reliability, completeness, occurrence inference, follow-up resource allocation, and the limits of the current experiment.'),
  bullet('The reference strategy is high quality and appropriately weighted toward primary papers, official mission/data documentation, and supplied course material.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Priority revision order')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Resolve the AI-policy ambiguity with the professor and retain the disclosure.')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Rewrite the conclusion as partial support and add the prevalence-dependent metric limitation.')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Correct the reproducibility revision statement and decide whether to add a true BLS-only baseline or remove the duplicate row.')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Render the pipeline, add a raw/BLS/folded example, and redesign the comparative curves/error gallery for page readability.')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Add the training-uncertainty and calibration-plot qualifications, then define remaining acronyms.')] }),
  new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [new TextRun('Fill identifiers, export to Word/PDF, add page numbers, verify every image after export, and use a compliant filename.')] }),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Final assessment')] }),
  para('The report does properly tie the technical work to the course concepts, and it does so in an understandable and scientifically responsible way. The connection is not decorative: the model’s false positives and false negatives are explicitly translated into reliability, completeness, selection effects, follow-up decisions, and limits on planetary-population inference. That is exactly the bridge the professor requested.'),
  para('With the priority revisions above, this should be a persuasive final project. The largest threat is not the science or the writing; it is avoidable submission and provenance ambiguity. Fix those items, preserve the report’s honest treatment of the recall trade-off, and the work should remain solidly in the A range.'),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 22, color: '202020' } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 30, bold: true, color: navy }, paragraph: { spacing: { before: 260, after: 140 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 25, bold: true, color: navy }, paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 260 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 260 }, spacing: { after: 90, line: 276 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1440, bottom: 1080, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: navy, space: 1 } }, children: [new TextRun({ text: 'PHY4000 Final Project Review', size: 18, color: '555555' })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Page ', size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  process.stdout.write(outputPath);
});
