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
  home: document.querySelector("#home-screen"),
  demo: document.querySelector("#demo-screen"),
  viewDemo: document.querySelector("#view-demo"),
  backHome: document.querySelector("#back-home"),
  workspace: document.querySelector("#case-workspace"),
  caseId: document.querySelector("#case-id"),
  casePosition: document.querySelector("#case-position"),
  context: document.querySelector("#case-context"),
  source: document.querySelector("#source-status"),
  global: document.querySelector("#global-curve"),
  local: document.querySelector("#local-curve"),
  human: document.querySelector("#human-panel"),
  choices: document.querySelectorAll("[data-guess]"),
  revealStage: document.querySelector("#reveal-stage"),
  verdictGrid: document.querySelector(".verdict-grid"),
  visitor: document.querySelector("#visitor-verdict"),
  visitorDecision: document.querySelector("#visitor-decision"),
  visitorDetail: document.querySelector("#visitor-detail"),
  modelDecision: document.querySelector("#model-decision"),
  modelDetail: document.querySelector("#model-detail"),
  catalogue: document.querySelector("#catalogue-verdict"),
  catalogueDecision: document.querySelector("#catalogue-decision"),
  catalogueDetail: document.querySelector("#catalogue-detail"),
  revealAnswer: document.querySelector("#reveal-answer"),
  nextCase: document.querySelector("#next-case"),
};

let currentIndex = 0;
let selectedGuess = null;

function cropCurve(image, row, column) {
  const x = column === "global" ? 100 : 892;
  const y = 58 + row * 400;
  image.style.width = "231.884%";
  image.style.height = "auto";
  image.style.left = `${(-x / 690) * 100}%`;
  image.style.top = "0";
  image.style.transform = `translateY(${(-y / 2400) * 100}%)`;
}

function curveDataUri(values) {
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
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 220" role="img" aria-label="Folded relative-flux light curve"><defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#c88a13"/><stop offset="1" stop-color="#f7c948"/></linearGradient></defs><rect width="660" height="220" fill="#f8f7f2"/><g stroke="#e5e1d5" stroke-width="1"><path d="M28 32H632M28 111H632M28 190H632"/></g><path d="M28 32V190H632" fill="none" stroke="#817d72" stroke-width="1"/><path d="${path}" fill="none" stroke="url(#g)" stroke-width="2.6"/></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function renderCurve(image, values, row, column) {
  if (!values) {
    image.src = "./assets/error_gallery.png";
    cropCurve(image, row, column);
    return;
  }
  image.src = curveDataUri(values);
  image.style.width = "100%";
  image.style.height = "100%";
  image.style.left = "0";
  image.style.top = "0";
  image.style.transform = "none";
}

function modelCall(value) {
  return value >= thresholds.stage2 ? "Planet candidate" : "False positive";
}

function showScreen(name) {
  const showDemo = name === "demo";
  elements.home.classList.toggle("is-active", !showDemo);
  elements.demo.classList.toggle("is-active", showDemo);
  elements.home.setAttribute("aria-hidden", String(showDemo));
  elements.demo.setAttribute("aria-hidden", String(!showDemo));
  if (showDemo) {
    window.setTimeout(() => elements.choices[0].focus({ preventScroll: true }), 650);
  } else {
    elements.home.scrollTop = 0;
    window.setTimeout(() => elements.viewDemo.focus({ preventScroll: true }), 650);
  }
}

function resetCase() {
  const item = cases[currentIndex];
  selectedGuess = null;
  elements.caseId.textContent = `TOI ${item.toi}`;
  elements.casePosition.textContent = `Case ${currentIndex + 1} of ${cases.length}`;
  renderCurve(elements.global, item.globalView, item.row, "global");
  renderCurve(elements.local, item.localView, item.row, "local");
  elements.choices.forEach((button) => {
    button.classList.remove("selected");
    button.disabled = false;
  });
  elements.human.hidden = false;
  elements.visitor.classList.remove("correct-guess", "incorrect-guess");
  elements.revealStage.hidden = true;
  elements.revealStage.classList.remove("is-entering");
  elements.catalogue.hidden = true;
  elements.verdictGrid.classList.remove("has-catalogue");
  elements.nextCase.hidden = true;
  elements.revealAnswer.hidden = false;
}

function showModel() {
  const item = cases[currentIndex];
  const stage1Call = item.stage1 >= thresholds.stage1 ? "promoted" : "rejected";
  elements.visitorDecision.textContent = selectedGuess === "planet" ? "Planet candidate" : "False positive";
  elements.visitorDetail.textContent = "Locked in - answer hidden";
  elements.modelDecision.textContent = modelCall(item.stage2);
  elements.modelDetail.textContent = `Stage 1 ${stage1Call} | Stage 2 ${item.stage2.toFixed(3)}`;
  elements.human.hidden = true;
  elements.revealStage.hidden = false;
  elements.revealStage.classList.remove("is-entering");
  void elements.revealStage.offsetWidth;
  elements.revealStage.classList.add("is-entering");
}

function showCatalogue() {
  const item = cases[currentIndex];
  const isPlanet = item.label === "CP";
  const modelIsPlanet = item.stage2 >= thresholds.stage2;
  const humanCorrect = (selectedGuess === "planet" && isPlanet) || (selectedGuess === "not-planet" && !isPlanet);
  const modelCorrect = modelIsPlanet === isPlanet;

  elements.visitor.classList.add(humanCorrect ? "correct-guess" : "incorrect-guess");
  elements.visitorDecision.textContent = humanCorrect ? "Correct - good call" : "Not this time";
  elements.visitorDetail.textContent = humanCorrect ? "Your classification matches the catalogue" : "Your classification differs from the catalogue";
  elements.catalogueDecision.textContent = isPlanet ? "Confirmed planet" : "False positive";
  elements.catalogueDetail.textContent = modelCorrect ? "The model also classified this case correctly" : "The model misclassified this case";
  elements.catalogue.hidden = false;
  elements.verdictGrid.classList.add("has-catalogue");
  elements.revealAnswer.hidden = true;
  elements.nextCase.hidden = false;
}

elements.viewDemo.addEventListener("click", () => {
  elements.demo.scrollTop = 0;
  resetCase();
  showScreen("demo");
});
elements.backHome.addEventListener("click", () => showScreen("home"));
elements.choices.forEach((button) => button.addEventListener("click", () => {
  selectedGuess = button.dataset.guess;
  elements.choices.forEach((item) => {
    item.classList.toggle("selected", item === button);
    item.disabled = true;
  });
  showModel();
}));
elements.revealAnswer.addEventListener("click", showCatalogue);
elements.nextCase.addEventListener("click", () => {
  elements.workspace.classList.add("is-changing");
  window.setTimeout(() => {
    currentIndex = (currentIndex + 1) % cases.length;
    resetCase();
    elements.workspace.classList.remove("is-changing");
  }, 280);
});

async function loadRepresentativeCases() {
  try {
    const dataUrl = new URL("data/representative_cases.json", window.location.href);
    const response = await fetch(dataUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (!Array.isArray(payload.cases) || payload.cases.length === 0) throw new Error("No cases in data file");
    cases = payload.cases.map((item) => ({
      toi: item.toi,
      label: item.label === 1 ? "CP" : "FP",
      stage1: item.stage1Score,
      stage2: item.stage2Score,
      globalView: item.globalView,
      localView: item.localView,
    }));
    currentIndex = 0;
    elements.source.textContent = `${cases.length} representative test cases`;
    elements.context.textContent = "Inspect both phase-folded views, then make the call before the model and catalogue are revealed.";
    resetCase();
  } catch (error) {
    const detail = error instanceof Error ? error.message : "unknown error";
    elements.source.textContent = "Documented error-gallery fallback";
    elements.context.textContent = `Representative data could not load (${detail}). Serve the site over HTTP to load the full sample.`;
    resetCase();
  }
}

function initTransitVisual() {
  const visual = document.querySelector(".hero-visual");
  const planet = document.querySelector("#transit-planet");
  const stellarLight = document.querySelector(".stellar-light");
  const fluxLine = document.querySelector("#flux-line");
  const canvas = document.querySelector("#lens-flare-canvas");
  if (!visual || !planet || !stellarLight || !fluxLine || !canvas) return;

  const context = canvas.getContext("2d");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const cycleDuration = 42000;
  const starRadius = .3;
  const planetRadius = .065;
  let frame = 0;
  let width = 0;
  let height = 0;

  function resizeCanvas() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const bounds = visual.getBoundingClientRect();
    width = Math.max(1, bounds.width);
    height = Math.max(1, bounds.height);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function smoothstep(edge0, edge1, value) {
    const amount = Math.min(1, Math.max(0, (value - edge0) / (edge1 - edge0)));
    return amount * amount * (3 - 2 * amount);
  }

  function drawRadial(x, y, radius, stops) {
    const gradient = context.createRadialGradient(x, y, 0, x, y, radius);
    stops.forEach(([offset, color]) => gradient.addColorStop(offset, color));
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fill();
  }

  function drawFlare(overlap, edgeBoost) {
    context.clearRect(0, 0, width, height);
    const sourceX = width * .5;
    const sourceY = height * .5;
    const scale = Math.min(width, height);
    const visibility = Math.max(.06, 1 - overlap * .9);
    const intensity = visibility * (.42 + edgeBoost * .22);

    context.save();
    context.globalCompositeOperation = "screen";

    drawRadial(sourceX, sourceY, scale * .23, [
      [0, `rgba(255,250,224,${.22 * intensity})`],
      [.12, `rgba(255,218,126,${.12 * intensity})`],
      [.45, `rgba(235,156,50,${.045 * intensity})`],
      [1, "rgba(0,0,0,0)"],
    ]);

    const streak = context.createLinearGradient(width * .05, sourceY, width * .95, sourceY);
    streak.addColorStop(0, "rgba(0,0,0,0)");
    streak.addColorStop(.36, `rgba(220,151,50,${.025 * intensity})`);
    streak.addColorStop(.49, `rgba(255,237,184,${.25 * intensity})`);
    streak.addColorStop(.5, `rgba(255,255,245,${.48 * intensity})`);
    streak.addColorStop(.51, `rgba(255,237,184,${.25 * intensity})`);
    streak.addColorStop(.64, `rgba(220,151,50,${.025 * intensity})`);
    streak.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = streak;
    context.fillRect(width * .05, sourceY - .65, width * .9, 1.3);

    const softStreak = context.createLinearGradient(width * .12, sourceY, width * .88, sourceY);
    softStreak.addColorStop(0, "rgba(0,0,0,0)");
    softStreak.addColorStop(.5, `rgba(255,199,89,${.055 * intensity})`);
    softStreak.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = softStreak;
    context.fillRect(width * .12, sourceY - scale * .018, width * .76, scale * .036);

    const glint = context.createLinearGradient(sourceX, sourceY - scale * .07, sourceX, sourceY + scale * .07);
    glint.addColorStop(0, "rgba(0,0,0,0)");
    glint.addColorStop(.5, `rgba(255,247,217,${.14 * intensity})`);
    glint.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = glint;
    context.fillRect(sourceX - .45, sourceY - scale * .07, .9, scale * .14);

    const axisX = width * -.08;
    const axisY = height * .08;
    [
      { distance: 1.7, radius: .018, color: [133, 113, 255], alpha: .065 },
      { distance: 3.25, radius: .029, color: [247, 194, 72], alpha: .045 },
      { distance: -2.4, radius: .013, color: [255, 230, 157], alpha: .055 },
    ].forEach((ghost) => {
      const x = sourceX + axisX * ghost.distance;
      const y = sourceY + axisY * ghost.distance;
      const [red, green, blue] = ghost.color;
      drawRadial(x, y, scale * ghost.radius, [
        [0, `rgba(${red},${green},${blue},${ghost.alpha * intensity})`],
        [.48, `rgba(${red},${green},${blue},${ghost.alpha * .25 * intensity})`],
        [.64, "rgba(0,0,0,0)"],
        [.78, `rgba(${red},${green},${blue},${ghost.alpha * .55 * intensity})`],
        [1, "rgba(0,0,0,0)"],
      ]);
    });

    context.restore();
  }

  function render(position) {
    const x = .5 - .41 * Math.cos(position * Math.PI * 2);
    const distance = Math.abs(x - .5);
    const outerContact = starRadius + planetRadius;
    const innerContact = starRadius - planetRadius;
    const overlap = 1 - smoothstep(innerContact, outerContact, distance);
    const edgeBoost = Math.exp(-Math.pow((distance - starRadius) / .038, 2));
    const dipY = 35 + overlap * 31;

    planet.style.left = `${(x * 100).toFixed(4)}%`;
    stellarLight.style.opacity = `${(1 - overlap * .055).toFixed(4)}`;
    fluxLine.setAttribute("d", `M10 35 C75 35 112 35 140 35 C158 35 165 ${dipY.toFixed(2)} 180 ${dipY.toFixed(2)} C195 ${dipY.toFixed(2)} 202 35 220 35 C248 35 285 35 350 35`);
    drawFlare(overlap, edgeBoost);
  }

  function animate(time) {
    render((time % cycleDuration) / cycleDuration);
    frame = window.requestAnimationFrame(animate);
  }

  resizeCanvas();
  if (reducedMotion) render(.5);
  else frame = window.requestAnimationFrame(animate);
  window.addEventListener("resize", resizeCanvas);
  window.addEventListener("pagehide", () => window.cancelAnimationFrame(frame), { once: true });
}

function initStarfield() {
  const canvas = document.querySelector("#starfield");
  const context = canvas.getContext("2d");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let stars = [];
  let width = 0;
  let height = 0;
  let frame = 0;

  function resize() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const count = Math.min(180, Math.floor((width * height) / 8500));
    stars = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 1.15 + .2,
      alpha: Math.random() * .55 + .18,
      pulse: Math.random() * Math.PI * 2,
      speed: Math.random() * .16 + .025,
    }));
  }

  function draw(time = 0) {
    context.clearRect(0, 0, width, height);
    stars.forEach((star) => {
      if (!reducedMotion) {
        star.y += star.speed;
        if (star.y > height + 2) star.y = -2;
      }
      const alpha = star.alpha + Math.sin(time * .0008 + star.pulse) * .12;
      context.beginPath();
      context.fillStyle = `rgba(205, 224, 255, ${Math.max(.08, alpha)})`;
      context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      context.fill();
    });
    if (!reducedMotion) frame = window.requestAnimationFrame(draw);
  }

  resize();
  draw();
  window.addEventListener("resize", resize);
  window.addEventListener("pagehide", () => window.cancelAnimationFrame(frame), { once: true });
}

resetCase();
loadRepresentativeCases();
initTransitVisual();
initStarfield();
