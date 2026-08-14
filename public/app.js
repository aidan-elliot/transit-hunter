let cases = [
  { toi: "5133.01", row: 0, label: "FP", stage1: 0.719, stage2: 0.745 },
  { toi: "6711.01", row: 1, label: "FP", stage1: 0.667, stage2: 0.731 },
  { toi: "6693.01", row: 2, label: "FP", stage1: 0.663, stage2: 0.727 },
  { toi: "5616.01", row: 3, label: "CP", stage1: 0.225, stage2: 0.194 },
  { toi: "6383.01", row: 4, label: "CP", stage1: 0.276, stage2: 0.206 },
  { toi: "5747.01", row: 5, label: "CP", stage1: 0.217, stage2: 0.208 },
];

const thresholds = { stage1: 0.345, stage2: 0.343 };
const elements = {
  caseId: document.querySelector("#case-id"), casePosition: document.querySelector("#case-position"), context: document.querySelector("#case-context"), evidenceNote: document.querySelector("#evidence-note"), source: document.querySelector("#source-status"), global: document.querySelector("#global-curve"), local: document.querySelector("#local-curve"), human: document.querySelector("#human-panel"), choices: document.querySelectorAll("[data-guess]"), revealGrid: document.querySelector("#reveal-grid"), visitor: document.querySelector("#visitor-verdict"), visitorDecision: document.querySelector("#visitor-decision"), visitorDetail: document.querySelector("#visitor-detail"), modelDecision: document.querySelector("#model-decision"), modelDetail: document.querySelector("#model-detail"), catalogue: document.querySelector("#catalogue-verdict"), catalogueDecision: document.querySelector("#catalogue-decision"), catalogueDetail: document.querySelector("#catalogue-detail"), nextRow: document.querySelector("#next-row"), revealAnswer: document.querySelector("#reveal-answer"), nextCase: document.querySelector("#next-case"),
};
let currentIndex = 0;
let selectedGuess = null;

function cropCurve(image, row, column) {
  const x = column === "global" ? 100 : 892;
  const y = 58 + row * 400;
  image.style.width = "231.884%";
  image.style.left = `${(-x / 690) * 100}%`;
  image.style.top = "0";
  image.style.transform = `translateY(${(-y / 2400) * 100}%)`;
}
function renderCurve(image, values, row, column) {
  if (!values) {
    image.src = "./assets/error_gallery.png";
    cropCurve(image, row, column);
    return;
  }
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const padding = Math.max((maximum - minimum) * 0.12, 0.00001);
  const low = minimum - padding;
  const high = maximum + padding;
  const path = values.map((value, index) => {
    const x = 28 + (index / (values.length - 1)) * 604;
    const y = 190 - ((value - low) / (high - low)) * 158;
    return `${index ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 220" role="img" aria-label="Folded relative-flux light curve"><rect width="660" height="220" fill="white"/><g stroke="#c8c9c5" stroke-width="1"><path d="M28 32H632M28 111H632M28 190H632"/></g><path d="M28 32V190H632" fill="none" stroke="#172343" stroke-width="1.25"/><path d="${path}" fill="none" stroke="#d65a47" stroke-width="2.2"/></svg>`;
  image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  image.style.width = "100%";
  image.style.left = "0";
  image.style.top = "0";
  image.style.transform = "none";
}
function modelCall(value) { return value >= thresholds.stage2 ? "Likely a planet" : "Likely not a planet"; }
function resetCase() {
  const item = cases[currentIndex]; selectedGuess = null;
  elements.caseId.textContent = `TOI ${item.toi}`;
  elements.casePosition.textContent = `Case ${currentIndex + 1} of ${cases.length}`;
  renderCurve(elements.global, item.globalView, item.row, "global");
  renderCurve(elements.local, item.localView, item.row, "local");
  elements.choices.forEach((button) => { button.classList.remove("selected"); button.disabled = false; });
  elements.human.classList.remove("correct-guess", "incorrect-guess");
  elements.visitor.classList.remove("correct-guess", "incorrect-guess");
  elements.human.hidden = false; elements.revealGrid.hidden = true; elements.catalogue.hidden = true; elements.nextRow.hidden = true; elements.nextCase.hidden = true; elements.revealAnswer.hidden = false;
}
function showModel() {
  const item = cases[currentIndex]; const stage1Call = item.stage1 >= thresholds.stage1 ? "promotes" : "rejects";
  elements.visitorDecision.textContent = selectedGuess === "planet" ? "Likely a planet" : selectedGuess === "not-planet" ? "Likely not a planet" : "Not sure";
  elements.visitorDetail.textContent = "Your call is locked in. The catalogue outcome stays hidden for now.";
  elements.modelDecision.textContent = modelCall(item.stage2);
  elements.modelDetail.textContent = `Stage 1 ${stage1Call} this candidate (score ${item.stage1.toFixed(3)}). Stage 2 score: ${item.stage2.toFixed(3)}.`;
  elements.revealGrid.hidden = false; elements.nextRow.hidden = false;
}
function showCatalogue() {
  const item = cases[currentIndex]; const isPlanet = item.label === "CP";
  const humanCorrect = (selectedGuess === "planet" && isPlanet) || (selectedGuess === "not-planet" && !isPlanet);
  if (selectedGuess === "unsure") {
    elements.visitorDecision.textContent = "No call made";
    elements.visitorDetail.textContent = "This was a sensible difficult-case choice. See the frozen catalogue outcome alongside the model's result.";
  } else if (humanCorrect) {
    elements.visitorDecision.textContent = "Correct — good call";
    elements.visitorDetail.textContent = "You identified this candidate’s catalogue outcome from the curve pair.";
    elements.human.classList.add("correct-guess"); elements.visitor.classList.add("correct-guess");
  } else {
    elements.visitorDecision.textContent = "Not this time";
    elements.visitorDetail.textContent = "This is a subtle case; compare the curve pair with the catalogue result.";
    elements.human.classList.add("incorrect-guess"); elements.visitor.classList.add("incorrect-guess");
  }
  elements.catalogueDecision.textContent = isPlanet ? "Confirmed planet" : "False positive";
  elements.catalogueDetail.textContent = "This deliberately selected hard case was also misclassified by the two-stage model.";
  elements.catalogue.hidden = false; elements.revealAnswer.hidden = true; elements.nextCase.hidden = false;
}
elements.choices.forEach((button) => button.addEventListener("click", () => {
  selectedGuess = button.dataset.guess;
  elements.choices.forEach((item) => { item.classList.toggle("selected", item === button); item.disabled = true; }); showModel();
}));
elements.revealAnswer.addEventListener("click", showCatalogue);
elements.nextCase.addEventListener("click", () => { currentIndex = (currentIndex + 1) % cases.length; resetCase(); document.querySelector("#lab").scrollIntoView({ behavior: "smooth", block: "start" }); });
resetCase();

async function loadRepresentativeCases() {
  try {
    const dataUrl = new URL("data/representative_cases.json", window.location.href);
    const response = await fetch(dataUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status} at ${dataUrl.pathname}`);
    const payload = await response.json();
    if (!Array.isArray(payload.cases) || payload.cases.length === 0) throw new Error("The data file has no cases");
    cases = payload.cases.map((item) => ({
      toi: item.toi, label: item.label === 1 ? "CP" : "FP", stage1: item.stage1Score,
      stage2: item.stage2Score, globalView: item.globalView, localView: item.localView,
    }));
    currentIndex = 0;
    elements.source.textContent = "Representative test sample · 13 cases";
    elements.context.textContent = "A deterministic, outcome-stratified sample from the sealed temporal test set.";
    elements.evidenceNote.textContent = "These 13 real curve pairs are selected to mirror the full Stage 2 test outcome mix: 8 correct predictions and 5 errors.";
    resetCase();
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unknown loading error";
    elements.source.textContent = "Error-gallery fallback · 6 cases";
    elements.context.textContent = `Representative data could not load (${detail}). Showing documented error-gallery cases instead.`;
    elements.evidenceNote.textContent = "Every displayed curve is a documented model error from the project’s error gallery, not a representative performance sample.";
  }
}
loadRepresentativeCases();
