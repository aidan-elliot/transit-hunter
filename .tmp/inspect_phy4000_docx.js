const fs = require('fs');
const JSZip = require('./docx-review-tool/node_modules/jszip');

const crypto = require('crypto');
const filePath = 'C:\\Users\\aidan\\OneDrive\\Documents\\ChatGPT\\Final Project - PHY4000\\ElliotA_Final_Project_PHY4000_Final.docx';
const pipelinePath = 'C:\\Users\\aidan\\OneDrive\\Documents\\ChatGPT\\Final Project - PHY4000\\report-assets\\pipeline_diagram.png';

(async () => {
  const zip = await JSZip.loadAsync(fs.readFileSync(filePath));
  const documentXml = await zip.file('word/document.xml').async('string');
  const footerXml = await zip.file('word/footer1.xml').async('string');
  const text = documentXml
    .replace(/<w:tab\s*\/>/g, '\t')
    .replace(/<\/w:p>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
  const media = Object.keys(zip.files).filter((name) => name.startsWith('word/media/') && !zip.files[name].dir);
  const checks = [
    'Aidan Elliot',
    '041080471',
    'August 14, 2026',
    'transit-hunter.aidanelliot.com',
    'Reducing false positives in TESS transit-candidate vetting',
    'Explanatory statement connecting the project to PHY4000',
    'The hypothesis was partially supported.',
    'Generative AI use declaration',
    'Bryson, S.',
    'Yu, L.',
  ];
  console.log(`Characters of extracted document text: ${text.length}`);
  console.log(`Embedded media files: ${media.length}`);
  console.log(`Page-number field present: ${footerXml.includes('PAGE')}`);
  for (const item of checks) console.log(`${text.includes(item) ? 'PASS' : 'FAIL'}: ${item}`);
  console.log(`Reference DOI links in text: ${(text.match(/https:\/\/doi\.org\//g) || []).length}`);
  console.log(`Course section removed: ${!text.includes('Course section')}`);
  const hash = (data) => crypto.createHash('sha256').update(data).digest('hex');
  const pipelineHash = hash(fs.readFileSync(pipelinePath));
  let pipelineEmbedded = false;
  for (const name of media) {
    const data = await zip.file(name).async('nodebuffer');
    if (hash(data) === pipelineHash) pipelineEmbedded = true;
  }
  console.log(`Exact PNG pipeline embedded: ${pipelineEmbedded}`);
})();
