const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, ImageRun, ExternalHyperlink, VerticalAlign,
  PageBreak, TabStopType, TabStopPosition, UnderlineType
} = require('./docx-review-tool/node_modules/docx');

const projectDir = 'C:\\Users\\aidan\\OneDrive\\Documents\\ChatGPT\\Final Project - PHY4000';
const inputPath = path.join(projectDir, 'PHY4000_Final_Report_Draft.md');
const outputPath = path.join(projectDir, 'ElliotA_Final_Project_PHY4000_Final.docx');
const pipelinePng = path.join(projectDir, 'report-assets', 'pipeline_diagram.png');

const navy = '7C2D12';
const midBlue = 'D97706';
const lightBlue = 'FDE68A';
const paleBlue = 'FFF8E7';
const paleYellow = 'FFF1B8';
const grey = '6B4A32';
const tableBorder = { style: BorderStyle.SINGLE, size: 4, color: 'E6A23C' };
const borders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function normalizeText(text) {
  return text
    .replace(/\\_/g, '_')
    .replace(/\$R_p\$/g, 'Rₚ')
    .replace(/\$R_\\star\$/g, 'R★')
    .replace(/\$/g, '');
}

function inlineRuns(text, base = {}) {
  text = normalizeText(text);
  const runs = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|<https?:\/\/[^>]+>|https?:\/\/[^\s]+)/g;
  let last = 0;
  let match;
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) runs.push(new TextRun({ text: text.slice(last, match.index), ...base }));
    const token = match[0];
    if (token.startsWith('**')) {
      runs.push(new TextRun({ text: token.slice(2, -2), bold: true, ...base }));
    } else if (token.startsWith('`')) {
      runs.push(new TextRun({ text: token.slice(1, -1), font: 'Consolas', size: 19, color: '2F4858', ...base }));
    } else if (token.startsWith('*')) {
      runs.push(new TextRun({ text: token.slice(1, -1), italics: true, ...base }));
    } else {
      let link = token.startsWith('<') ? token.slice(1, -1) : token;
      let trailing = '';
      while (/[.,;)]$/.test(link)) {
        trailing = link.slice(-1) + trailing;
        link = link.slice(0, -1);
      }
      runs.push(new ExternalHyperlink({
        link,
        children: [new TextRun({ text: link, color: 'C2410C', underline: { type: UnderlineType.SINGLE, color: 'C2410C' }, ...base })],
      }));
      if (trailing) runs.push(new TextRun({ text: trailing, ...base }));
    }
    last = re.lastIndex;
  }
  if (last < text.length) runs.push(new TextRun({ text: text.slice(last), ...base }));
  return runs.length ? runs : [new TextRun({ text, ...base })];
}

function bodyParagraph(text, opts = {}) {
  return new Paragraph({
    alignment: opts.alignment ?? AlignmentType.JUSTIFIED,
    spacing: { before: opts.before ?? 0, after: opts.after ?? 130, line: opts.line ?? 300 },
    indent: opts.indent,
    keepNext: opts.keepNext,
    keepLines: opts.keepLines,
    children: inlineRuns(text, opts.run ?? {}),
  });
}

function pngDimensions(filePath) {
  const data = fs.readFileSync(filePath);
  if (data.toString('ascii', 1, 4) !== 'PNG') throw new Error(`Not a PNG: ${filePath}`);
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) };
}

function scaledDimensions(filePath, maxWidth = 600, maxHeight = 690) {
  const { width, height } = pngDimensions(filePath);
  const scale = Math.min(maxWidth / width, maxHeight / height, 1);
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}

function imageParagraph(filePath, alt, figureHint = '') {
  const ext = path.extname(filePath).slice(1).toLowerCase();
  const dims = ext === 'svg' ? { width: 600, height: 350 } : scaledDimensions(filePath);
  const transparentPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64');
  const imageOptions = {
    type: ext,
    data: fs.readFileSync(filePath),
    transformation: dims,
    altText: { title: figureHint || alt, description: alt, name: figureHint || 'Report figure' },
  };
  if (ext === 'svg') imageOptions.fallback = { type: 'png', data: transparentPng };
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 80 },
    keepNext: true,
    children: [new ImageRun(imageOptions)],
  });
}

function captionParagraph(text) {
  const clean = text.replace(/^\*/, '').replace(/\*$/, '');
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 180, line: 260 },
    keepLines: true,
    children: [new TextRun({ text: clean, italics: true, size: 19, color: grey })],
  });
}

function identityCell(label, value, highlight = false) {
  return new TableCell({
    borders: noBorders,
    width: { size: 4680, type: WidthType.DXA },
    shading: highlight ? { fill: paleYellow, type: ShadingType.CLEAR } : undefined,
    margins: { top: 35, bottom: 35, left: 70, right: 70 },
    children: [new Paragraph({
      spacing: { after: 0 },
      children: [new TextRun({ text: `${label}: `, bold: true, size: 20, color: navy }), new TextRun({ text: value, size: 20 })],
    })],
  });
}

function buildIdentityBlock() {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [4680, 4680],
    rows: [
      new TableRow({ children: [identityCell('Learner', 'Aidan Elliot'), identityCell('Student ID', '041080471')] }),
      new TableRow({ children: [identityCell('Course', 'PHY4000 - Black Holes, Big Bangs and the Cosmos'), identityCell('Assignment', 'Final Project')] }),
      new TableRow({ children: [identityCell('Instructor', 'Dr. Asghar Gill'), identityCell('Due date', 'August 14, 2026')] }),
      new TableRow({ children: [identityCell('Repository', 'github.com/aidan-elliot/transit-hunter'), identityCell('Supplementary website', 'transit-hunter.aidanelliot.com')] }),
    ],
  });
}

function markdownCells(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((v) => v.trim());
}

function tableFromMarkdown(lines) {
  const rows = lines.filter((_, i) => i !== 1).map(markdownCells);
  const cols = rows[0].length;
  let widths;
  if (cols === 6) widths = [1550, 950, 1150, 700, 800, 4210];
  else if (cols === 11) widths = [2200, 716, 716, 716, 716, 716, 716, 716, 716, 716, 716];
  else widths = Array(cols).fill(Math.floor(9360 / cols));
  widths[widths.length - 1] += 9360 - widths.reduce((a, b) => a + b, 0);

  const tableRows = rows.map((cells, rowIndex) => new TableRow({
    tableHeader: rowIndex === 0,
    cantSplit: true,
    children: cells.map((raw, colIndex) => {
      const bold = rowIndex === 0 || /\*\*/.test(raw);
      const text = raw.replace(/\*\*/g, '');
      return new TableCell({
        borders,
        width: { size: widths[colIndex], type: WidthType.DXA },
        shading: rowIndex === 0 ? { fill: navy, type: ShadingType.CLEAR } : (rowIndex % 2 === 0 ? { fill: paleBlue, type: ShadingType.CLEAR } : undefined),
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 65, bottom: 65, left: 65, right: 65 },
        children: [new Paragraph({
          alignment: colIndex === 0 || (cols === 6 && colIndex === 5) ? AlignmentType.LEFT : AlignmentType.CENTER,
          spacing: { after: 0, line: 230 },
          children: [new TextRun({ text, bold, size: cols > 8 ? 15 : 18, color: rowIndex === 0 ? 'FFFFFF' : '202020' })],
        })],
      });
    }),
  }));

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: tableRows,
  });
}

function heading(text, level, options = {}) {
  return new Paragraph({
    heading: level,
    pageBreakBefore: options.pageBreakBefore,
    keepNext: true,
    children: [new TextRun(text)],
  });
}

const markdown = fs.readFileSync(inputPath, 'utf8').replace(/\r\n/g, '\n');
const allLines = markdown.split('\n');
const firstTitle = allLines.findIndex((line) => line.startsWith('# '));
const lines = allLines.slice(firstTitle);
const children = [buildIdentityBlock()];

let inMermaid = false;
let paragraphBuffer = [];
let referencesMode = false;

function flushParagraph() {
  if (!paragraphBuffer.length) return;
  const text = paragraphBuffer.join(' ').trim();
  paragraphBuffer = [];
  if (!text) return;
  if (referencesMode) {
    children.push(new Paragraph({
      alignment: AlignmentType.LEFT,
      spacing: { after: 130, line: 300 },
      indent: { hanging: 720 },
      children: inlineRuns(text),
    }));
  } else if (/^\*Figure \d/.test(text)) {
    children.push(captionParagraph(text));
  } else {
    children.push(bodyParagraph(text));
  }
}

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];

  if (line === '```mermaid') {
    flushParagraph();
    inMermaid = true;
    continue;
  }
  if (inMermaid) {
    if (line === '```') {
      children.push(imageParagraph(pipelinePng, 'Flowchart of the implemented two-stage TESS candidate-vetting pipeline', 'Figure 3'));
      inMermaid = false;
    }
    continue;
  }

  if (line === '$$') {
    flushParagraph();
    const equation = lines[++i];
    i++; // closing $$
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 80, after: 160 },
      children: [new TextRun({ text: equation.includes('delta') ? 'δ ≈ (Rₚ / R★)²' : normalizeText(equation), italics: true, size: 24 })],
    }));
    continue;
  }

  if (line.startsWith('|')) {
    flushParagraph();
    const tableLines = [];
    while (i < lines.length && lines[i].startsWith('|')) tableLines.push(lines[i++]);
    i--;
    children.push(tableFromMarkdown(tableLines));
    children.push(new Paragraph({ spacing: { after: 100 }, children: [] }));
    continue;
  }

  const imageMatch = line.match(/^!\[([^\]]+)\]\(([^)]+)\)$/);
  if (imageMatch) {
    flushParagraph();
    const filePath = path.resolve(projectDir, imageMatch[2]);
    const nextCaption = lines.slice(i + 1, i + 4).find((v) => /^\*Figure/.test(v));
    const hint = nextCaption ? nextCaption.replace(/^\*/, '').split('.')[0] : 'Report figure';
    children.push(imageParagraph(filePath, imageMatch[1], hint));
    continue;
  }

  if (line.startsWith('# ')) {
    flushParagraph();
    const title = line.slice(2);
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 260, after: 100, line: 320 },
      keepNext: true,
      border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: midBlue, space: 8 } },
      children: [new TextRun({ text: title, bold: true, size: 36, color: navy })],
    }));
    continue;
  }

  if (line.startsWith('## ')) {
    flushParagraph();
    const text = line.slice(3);
    referencesMode = text === 'References';
    children.push(heading(text, HeadingLevel.HEADING_1, { pageBreakBefore: referencesMode }));
    continue;
  }

  if (line.startsWith('### ')) {
    flushParagraph();
    children.push(heading(line.slice(4), HeadingLevel.HEADING_2));
    continue;
  }

  if (line.trim() === '') {
    flushParagraph();
    continue;
  }

  if (/^\*Figure \d/.test(line)) {
    flushParagraph();
    children.push(captionParagraph(line));
    continue;
  }

  // Subtitle immediately after the main title.
  if (/^\*\*A two-stage/.test(line)) {
    flushParagraph();
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
      children: [new TextRun({ text: line.replace(/\*\*/g, ''), bold: true, italics: true, size: 23, color: grey })],
    }));
    continue;
  }

  paragraphBuffer.push(line.trim());
}
flushParagraph();

const doc = new Document({
  creator: 'Aidan Elliot',
  title: 'Reducing false positives in TESS transit-candidate vetting',
  subject: 'PHY4000 Final Project',
  description: 'A two-stage BLS, convolutional neural network, and diagnostic-feature pipeline',
  styles: {
    default: { document: { run: { font: 'Arial', size: 22, color: '202020' }, paragraph: { spacing: { line: 300, after: 130 } } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 29, bold: true, color: navy }, paragraph: { spacing: { before: 300, after: 130 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 25, bold: true, color: midBlue }, paragraph: { spacing: { before: 230, after: 110 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1440, bottom: 1080, left: 1440, header: 500, footer: 500 },
      },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: 'Page ', size: 18, color: grey }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: grey })],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  process.stdout.write(outputPath);
});
