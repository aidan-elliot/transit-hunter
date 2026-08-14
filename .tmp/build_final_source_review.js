const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, LevelFormat, BorderStyle,
  WidthType, ShadingType, PageNumber, PageOrientation
} = require('./docx-review-tool/node_modules/docx');

const outputPath = 'C:\\Users\\aidan\\OneDrive\\Documents\\ChatGPT\\Final Project - PHY4000\\PHY4000_Final_Report_Source_Audit_and_Mock_Grade.docx';

const navy = '17365D';
const blue = 'D9EAF7';
const green = 'E2F0D9';
const amber = 'FFF2CC';
const pale = 'F4F6F8';
const border = { style: BorderStyle.SINGLE, size: 4, color: 'B7C9D6' };
const borders = { top: border, bottom: border, left: border, right: border };

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 110, line: 270 },
    alignment: opts.alignment,
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italics, size: opts.size, color: opts.color })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { after: 75, line: 270 },
    children: [new TextRun(text)],
  });
}

function cell(text, width, fill, bold = false) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 90, right: 90 },
    children: [para(text, { bold, after: 0, size: 18 })],
  });
}

const sourceRows = [
  ['Bryson et al. (2020)', 'Peer-reviewed AJ research; DOI 10.3847/1538-3881/abb316 matched.', 'Directly supports the need to account for reliability when inferring Kepler occurrence rates.', 'PASS - primary, highly relevant'],
  ['Gill (2026a), Light and Matter', 'Instructor-provided PHY4000 course slides; supplied PDF checked.', 'Accurately supports the claim that information about distant objects is read from light.', 'PASS - appropriate course source'],
  ['Gill (2026b), Telescopes', 'Instructor-provided PHY4000 course slides; supplied PDF checked.', 'Accurately supports time monitoring and light curves as sequences of brightness measurements.', 'PASS - appropriate course source'],
  ['Gill (2026c), Other Planetary Systems', 'Instructor-provided PHY4000 course slides; supplied PDF checked.', 'Accurately supports transit dips, TESS/Kepler, and observational incompleteness.', 'PASS - appropriate course source'],
  ['Gill (2026d), Life in the Universe', 'Instructor-provided PHY4000 course slides; supplied PDF checked.', 'Accurately supports the distinction between potential habitability and evidence of life.', 'PASS - appropriate course source'],
  ['Guerrero et al. (2021)', 'Peer-reviewed ApJS catalogue paper; DOI 10.3847/1538-4365/abefe1 matched.', 'Directly supports the TESS Objects of Interest catalogue and candidate-disposition context.', 'PASS - primary, highly relevant'],
  ['Kovacs et al. (2002)', 'Peer-reviewed Astronomy & Astrophysics methods paper; DOI 10.1051/0004-6361:20020802 matched.', 'Foundational source for Box Least Squares transit searches.', 'PASS - primary, foundational'],
  ['Lightkurve Collaboration et al. (2018)', 'Astrophysics Source Code Library software record; matches Lightkurve\'s official recommended citation.', 'Appropriate attribution for the software used to search for and access TESS light curves.', 'PASS - authoritative software citation'],
  ['NASA Exoplanet Archive (2025)', 'Official NASA/IPAC living documentation; title and disposition definitions checked.', 'Directly supports TOI column meanings and CP/FP/FA label definitions.', 'PASS - authoritative official source'],
  ['NASA/HEASARC TESS documentation (n.d.)', 'Official NASA mission documentation; retrieval date supplied.', 'Supports SPOC processing, calibrated photometry, transit-search products, and archiving to MAST.', 'PASS - authoritative official source'],
  ['Ricker et al. (2015)', 'Peer-reviewed JATIS TESS mission paper; DOI 10.1117/1.JATIS.1.1.014003 matched.', 'Primary mission-design source for TESS. Crossref records an October 2014 online date, while 2015 is the conventional volume citation; this is not a credibility problem.', 'PASS - primary; minor date nuance'],
  ['Saito & Rehmsmeier (2015)', 'Peer-reviewed PLOS ONE methods paper; DOI 10.1371/journal.pone.0118432 matched.', 'Directly supports emphasizing precision-recall analysis for imbalanced classification.', 'PASS - primary, directly relevant'],
  ['Shallue & Vanderburg (2018)', 'Peer-reviewed AJ research; DOI 10.3847/1538-3881/aa9e09 matched.', 'Appropriate AstroNet/deep-learning precedent for transit-candidate classification.', 'PASS - primary, highly relevant'],
  ['STScI MAST TESS Data Products (n.d.)', 'Official archive documentation from the Space Telescope Science Institute; retrieval date supplied.', 'Supports the availability and nature of TESS light-curve and validation data products.', 'PASS - authoritative official source'],
  ['Sullivan et al. (2015)', 'Peer-reviewed ApJ simulations paper; DOI 10.1088/0004-637X/809/1/77 matched.', 'Directly supports discussion of TESS planet detections and astrophysical false positives.', 'PASS - primary, highly relevant'],
  ['Valizadegan et al. (2022)', 'Peer-reviewed ApJ ExoMiner paper; DOI 10.3847/1538-4357/ac4399 matched.', 'Appropriate comparison for expert-inspired diagnostic inputs and explainable vetting.', 'PASS - primary, highly relevant'],
  ['Valizadegan et al. (2025)', 'Peer-reviewed AJ ExoMiner++ paper; DOI 10.3847/1538-3881/ae03a4 matched.', 'Current and directly relevant comparison for enhanced vetting of two-minute TESS candidates.', 'PASS - primary, highly relevant'],
  ['Yu et al. (2019)', 'Peer-reviewed AJ TESS vetting paper; DOI 10.3847/1538-3881/ab21d6 matched.', 'Direct precedent for automated TESS candidate triage and vetting.', 'PASS - primary, highly relevant'],
];

const sourceTable = new Table({
  width: { size: 12960, type: WidthType.DXA },
  columnWidths: [2100, 3500, 5000, 2360],
  rows: [
    new TableRow({ tableHeader: true, children: [
      cell('Source', 2100, navy, true),
      cell('Credibility and metadata check', 3500, navy, true),
      cell('Claim/relevance check', 5000, navy, true),
      cell('Verdict', 2360, navy, true),
    ]}),
    ...sourceRows.map((r, i) => new TableRow({ children: [
      cell(r[0], 2100, i % 2 ? pale : undefined, true),
      cell(r[1], 3500, i % 2 ? pale : undefined),
      cell(r[2], 5000, i % 2 ? pale : undefined),
      cell(r[3], 2360, r[3].includes('minor') ? amber : green, true),
    ]})),
  ],
});

const scoreRows = [
  ['Completion of approved project', '30', '28', 'The approved two-stage pipeline, real TESS data, controlled comparisons, and substantive results are present. The baseline table still represents only three distinct fitted conditions.'],
  ['Scientific and methodological quality', '30', '27', 'Strong leakage controls, sealed test, multiple metrics, bootstrap interval, and candid error analysis. The conclusion is slightly too categorical and uncertainty is conditional on one selected training run.'],
  ['Course relevance and professor feedback', '20', '20', 'The report repeatedly connects light, telescopes, transits, selection effects, false positives, prevalence, and planetary-population inference. This directly fulfills the professor\'s only requested emphasis.'],
  ['References and evidence integrity', '15', '14', 'All 18 references are real, credible, cited, and relevant. A few technical vetting statements would benefit from a direct source.'],
  ['Presentation and submission readiness', '5', '3', 'Professional prose and strong figures, but identifiers remain placeholders, Mermaid must be rendered, a raw-to-folded light-curve figure is missing, and Markdown is not the accepted final submission format.'],
  ['Total', '100', '92', 'A-range content draft. This assumes normal finalization to a compliant Word/PDF submission.'],
];

const scoreTable = new Table({
  width: { size: 12960, type: WidthType.DXA },
  columnWidths: [3150, 900, 900, 8010],
  rows: [
    new TableRow({ tableHeader: true, children: [cell('Category', 3150, navy, true), cell('Max', 900, navy, true), cell('Score', 900, navy, true), cell('Rationale', 8010, navy, true)] }),
    ...scoreRows.map((r, i) => new TableRow({ children: [
      cell(r[0], 3150, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1),
      cell(r[1], 900, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1),
      cell(r[2], 900, i === scoreRows.length - 1 ? blue : undefined, true),
      cell(r[3], 8010, i === scoreRows.length - 1 ? blue : undefined, i === scoreRows.length - 1),
    ]})),
  ],
});

const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: 'PHY4000 Final Report', bold: true, size: 34, color: navy })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 220 }, children: [new TextRun({ text: 'Final Source Audit, Professor-Style Feedback, and Mock Grade', bold: true, size: 25 })] }),
  para('Review date: August 14, 2026', { alignment: AlignmentType.CENTER, after: 35 }),
  para('Draft reviewed: PHY4000_Final_Report_Draft.md', { alignment: AlignmentType.CENTER, after: 240 }),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Bottom line')] }),
  para('The reference audit passes. All 18 bibliography entries are real, credible, relevant to the sentence or section in which they are used, and appropriate for this report. The journal references match their DOI metadata; the institutional web references are official NASA, IPAC, HEASARC, or STScI pages; the Lightkurve entry follows the project\'s recommended software citation; and the four course references accurately represent the supplied PHY4000 slides. No fabricated, materially incorrect, or claim-mismatched reference was found.'),
  para('The draft also fulfills the professor\'s initial feedback unusually well. The technical pipeline remains an astronomy investigation: it begins with information carried by light, moves through telescope time-series measurements and transit geometry, and ends with reliability, completeness, selection effects, occurrence rates, and the limits of planetary-population inference. A general PHY4000 reader can understand why the false-positive/false-negative trade-off matters scientifically.'),
  para('Mock grade: 92/100 (A range) as a content draft, assuming the remaining placeholders and final-format requirements are resolved before submission.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Source-audit method')] }),
  bullet('Matched every DOI-based reference to its title, author list, journal, year/volume, and article number in scholarly metadata.'),
  bullet('Checked the NASA Exoplanet Archive, NASA/HEASARC, STScI/MAST, and official Lightkurve pages for authority and relevance.'),
  bullet('Checked each course-slide claim against the supplied Week 4, Week 6, Week 10, and Week 13 PDFs.'),
  bullet('Checked that all 18 listed references appear in the report body and that none is merely decorative.'),
  bullet('Compared each source with the actual claim it is being asked to support, not only with the report topic in general.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Every-source credibility and relevance audit')] }),
  sourceTable,

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Reference-integrity conclusion')] }),
  para('No reference should be removed for credibility reasons. The mix is strong: ten peer-reviewed journal papers, four instructor-provided course sources, three official NASA/STScI documentation sources, and one authoritative software citation. There is no stated numerical minimum in the assignment material, and 18 focused references are sufficient. Adding sources only to increase the count would not improve the report.'),
  para('The Ricker et al. TESS mission paper has a minor date nuance: Crossref records an online publication date in October 2014, while the journal volume is conventionally cited as 2015. The report\'s 2015 citation is standard and does not need to be treated as an error.'),
  para('Three technical statements could still be strengthened with one additional direct vetting source: the use of odd/even depths, secondary eclipses, and V-shaped events as warning diagnostics; the distinction between candidate vetting and statistical validation; and any stronger claim about calibration. These are evidence-strength improvements, not corrections to bad references.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Professor feedback loop-back')] }),
  para('Initial feedback: preserve the ambitious but appropriate two-stage pipeline and keep cosmological significance visible alongside the technical work, especially through exoplanet prevalence and what the results imply about the universe.'),
  bullet('Two-stage design: met. Stage 1 classifies global/local transit shapes; Stage 2 adds diagnostic information and explicitly tests false-positive rejection.'),
  bullet('Astronomy first: met strongly. The report explains transit physics, light curves, impostors, telescope products, and observational limits before treating the models.'),
  bullet('Broader significance: met strongly. The introduction, explanatory statement, Section 8, and conclusion connect catalogue reliability and completeness to occurrence-rate and population inference.'),
  bullet('Understandability: met. The report translates 17 fewer accepted false positives and 19 fewer accepted confirmed planets into a real scientific trade-off rather than presenting only abstract metrics.'),
  bullet('Scientific restraint: met strongly. The system is described as candidate vetting and ranking; the report does not claim that the model confirms planets or proves habitability or life.'),
  para('Verdict: the professor\'s main suggestion is not merely mentioned once; it is integrated into the report\'s central argument. This is one of the strongest parts of the draft.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Remaining substantive issues')] }),
  bullet('Change the conclusion from an unqualified "The answer is yes" to "The hypothesis was partially supported." Stage 2 improved PR-AUC, ROC-AUC, and false-positive rejection, but recall and F1 declined.'),
  bullet('Clarify that the reported precision and PR-AUC are conditional on a nearly balanced, labelled TOI test set and should not be transferred directly to an unfiltered TESS population.'),
  bullet('Correct or qualify the exact Git-revision claim. The recorded revision does not itself contain every script and manifest now used to explain the run, and the run manifest does not record dirty working-tree state.'),
  bullet('Either add a true BLS-only baseline or remove the duplicate BLS/diagnostics row. The table currently displays four rows but only three distinct fitted conditions.'),
  bullet('State that the grouped bootstrap measures test-sample uncertainty conditional on the selected trained models; it does not include training-seed uncertainty.'),
  bullet('Treat the 285-record calibration plot as descriptive and report the binning/counts; it is not strong evidence of precise calibration differences.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Presentation and submission issues')] }),
  bullet('Fill learner number, course section, and due date.'),
  bullet('Render the Mermaid pipeline to an image before export.'),
  bullet('Add one representative raw-to-cleaned-to-BLS-to-phase-folded light-curve figure, as anticipated in the approved report plan.'),
  bullet('Consider overlaying Stage 1 and Stage 2 ROC/PR curves and resizing or splitting the tall error gallery for readability.'),
  bullet('Export to DOCX or PDF, add page numbers, and use a filename containing the learner name and assignment. Markdown is a drafting format, not an accepted final submission format.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Mock grade')] }),
  scoreTable,
  para('This is an informed mock assessment based on the assignment brief, Learner\'s Manual, approved proposal, professor feedback, and the evidence in the report. It is not the instructor\'s official rubric or grade.', { italics: true, after: 200 }),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Mock professor feedback')] }),
  para('Hi Aidan,'),
  para('This is an ambitious, substantial, and impressively well-documented final project. You followed through on the approved two-stage design using real TESS light curves, and you did not reduce the project to a machine-learning demonstration. The report clearly explains how telescope measurements of changing light become candidate signals, why eclipsing binaries and instrumental effects complicate that evidence, and how false positives and missed planets affect what can responsibly be inferred about exoplanet prevalence and planetary populations. That directly addresses my suggestion that the broader significance remain visible alongside the technical work.'),
  para('A particular strength is your handling of the result. Stage 2 reduced false-positive acceptance and improved the ranking metrics, but it also lost confirmed planets at the selected threshold. Reporting both sides of that outcome shows scientific maturity. Your frozen catalogue snapshot, target-level temporal split, zero target crossings, sealed test set, and explicit distinction between vetting and confirmation also make the work credible and appropriately cautious.'),
  para('Before submitting, I would revise the conclusion to say that the hypothesis was partially supported, clarify that precision depends on the class balance of this curated TOI sample, and correct the reproducibility statement about the exact Git revision. I would also remove the duplicate baseline row unless you add a genuinely separate BLS-only comparison. Finally, complete the identification fields, render the remaining diagram, add the representative raw/phase-folded light-curve figure, and submit a paginated Word or PDF file.'),
  para('Your source work is excellent. The references are real, authoritative, and directly relevant, with a strong balance of primary research, official mission/archive documentation, software citation, and course material. Overall, this is A-range work. Mock grade: 92%.'),

  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('Final verdict')] }),
  para('The report is scientifically credible, well sourced, candid about trade-offs, and strongly tied to PHY4000. Its largest remaining risks are presentation/provenance details and a few statements that overstate what the experiment proves. Addressing those items would make a mock grade around 95% defensible; as currently drafted, 92% is the fairer estimate.'),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 21, color: '202020' } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 28, bold: true, color: navy }, paragraph: { spacing: { before: 250, after: 125 }, outlineLevel: 0 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 250 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 15840, height: 12240, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 900, right: 1080, bottom: 900, left: 1080 },
      },
    },
    headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: navy, space: 1 } }, children: [new TextRun({ text: 'PHY4000 Final Source Audit and Mock Grade', size: 17, color: '555555' })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Page ', size: 17 }), new TextRun({ children: [PageNumber.CURRENT], size: 17 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  process.stdout.write(outputPath);
});
