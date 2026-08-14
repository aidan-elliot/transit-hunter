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
  elements.visitorDetail.textContent = "Answer hidden";
  elements.modelDecision.textContent = modelCall(item.stage2);
  elements.modelDetail.textContent = `Stage 1: ${stage1Call} · Stage 2 score: ${item.stage2.toFixed(3)}`;
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
  elements.visitorDecision.textContent = selectedGuess === "planet" ? "Planet candidate" : "False positive";
  elements.visitorDetail.textContent = humanCorrect ? "Matches catalogue" : "Does not match catalogue";
  elements.catalogueDecision.textContent = isPlanet ? "Confirmed planet" : "False positive";
  elements.catalogueDetail.textContent = modelCorrect ? "Model matches this outcome" : "Model does not match this outcome";
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
    elements.context.textContent = "Compare the full phase curve with the transit window. Choose a classification before revealing the catalogue outcome.";
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

  function drawFlare(overlap, edgeBoost, planetPosition) {
    context.clearRect(0, 0, width, height);
    const sourceX = width * .5;
    const sourceY = height * .5;
    const scale = Math.min(width, height);
    const visibility = .18 + (1 - overlap) * .82;
    const intensity = Math.min(1.3, visibility * 1.08 + edgeBoost * .44);

    context.save();
    context.globalCompositeOperation = "screen";

    drawRadial(sourceX, sourceY, scale * .52, [
      [0, `rgba(255,255,251,${.52 * intensity})`],
      [.06, `rgba(255,247,210,${.36 * intensity})`],
      [.22, `rgba(255,195,78,${.19 * intensity})`],
      [.54, `rgba(221,104,18,${.07 * intensity})`],
      [1, "rgba(0,0,0,0)"],
    ]);

    drawRadial(sourceX, sourceY, scale * .095, [
      [0, `rgba(255,255,255,${.86 * intensity})`],
      [.1, `rgba(255,253,232,${.62 * intensity})`],
      [.48, `rgba(255,207,96,${.2 * intensity})`],
      [1, "rgba(0,0,0,0)"],
    ]);

    context.save();
    context.filter = `blur(${Math.max(8, scale * .03)}px)`;
    const broadStreak = context.createLinearGradient(0, sourceY, width, sourceY);
    broadStreak.addColorStop(0, "rgba(0,0,0,0)");
    broadStreak.addColorStop(.12, `rgba(225,141,35,${.06 * intensity})`);
    broadStreak.addColorStop(.3, `rgba(245,165,51,${.2 * intensity})`);
    broadStreak.addColorStop(.5, `rgba(255,235,174,${.62 * intensity})`);
    broadStreak.addColorStop(.7, `rgba(245,165,51,${.2 * intensity})`);
    broadStreak.addColorStop(.88, `rgba(225,141,35,${.06 * intensity})`);
    broadStreak.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = broadStreak;
    context.fillRect(0, sourceY - scale * .048, width, scale * .096);
    context.restore();

    const streak = context.createLinearGradient(0, sourceY, width, sourceY);
    streak.addColorStop(0, "rgba(0,0,0,0)");
    streak.addColorStop(.18, `rgba(218,135,31,${.08 * intensity})`);
    streak.addColorStop(.32, `rgba(230,150,42,${.24 * intensity})`);
    streak.addColorStop(.43, `rgba(255,205,101,${.5 * intensity})`);
    streak.addColorStop(.46, `rgba(255,221,134,${.65 * intensity})`);
    streak.addColorStop(.495, `rgba(255,252,225,${.72 * intensity})`);
    streak.addColorStop(.5, `rgba(255,255,255,${.94 * intensity})`);
    streak.addColorStop(.505, `rgba(255,252,225,${.72 * intensity})`);
    streak.addColorStop(.54, `rgba(255,221,134,${.65 * intensity})`);
    streak.addColorStop(.57, `rgba(255,205,101,${.5 * intensity})`);
    streak.addColorStop(.68, `rgba(230,150,42,${.24 * intensity})`);
    streak.addColorStop(.82, `rgba(218,135,31,${.08 * intensity})`);
    streak.addColorStop(1, "rgba(0,0,0,0)");
    context.save();
    context.shadowBlur = Math.max(12, scale * .03);
    context.shadowColor = `rgba(255,194,78,${.62 * intensity})`;
    context.fillStyle = streak;
    context.fillRect(0, sourceY - 1.8, width, 3.6);
    context.restore();

    const chromaticStreak = context.createLinearGradient(width * .16, sourceY, width * .84, sourceY);
    chromaticStreak.addColorStop(0, "rgba(0,0,0,0)");
    chromaticStreak.addColorStop(.42, `rgba(119,104,255,${.2 * intensity})`);
    chromaticStreak.addColorStop(.5, `rgba(255,235,179,${.34 * intensity})`);
    chromaticStreak.addColorStop(.58, `rgba(255,158,65,${.18 * intensity})`);
    chromaticStreak.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = chromaticStreak;
    context.fillRect(width * .16, sourceY + 1.65, width * .68, .8);

    const glint = context.createLinearGradient(sourceX, sourceY - scale * .12, sourceX, sourceY + scale * .12);
    glint.addColorStop(0, "rgba(0,0,0,0)");
    glint.addColorStop(.44, `rgba(255,239,191,${.07 * intensity})`);
    glint.addColorStop(.5, `rgba(255,255,248,${.46 * intensity})`);
    glint.addColorStop(.56, `rgba(255,239,191,${.07 * intensity})`);
    glint.addColorStop(1, "rgba(0,0,0,0)");
    context.fillStyle = glint;
    context.fillRect(sourceX - .65, sourceY - scale * .12, 1.3, scale * .24);

    const axisX = width * -.12;
    const axisY = height * .085;
    [
      { distance: -.9, radius: .022, color: [255, 232, 164], alpha: .22, ring: false },
      { distance: 1.25, radius: .044, color: [255, 192, 79], alpha: .2, ring: false },
      { distance: 2.35, radius: .074, color: [129, 111, 255], alpha: .18, ring: true },
      { distance: 3.45, radius: .052, color: [255, 180, 62], alpha: .18, ring: true },
      { distance: 4.35, radius: .027, color: [255, 235, 183], alpha: .2, ring: false },
    ].forEach((ghost) => {
      const x = sourceX + axisX * ghost.distance;
      const y = sourceY + axisY * ghost.distance;
      const [red, green, blue] = ghost.color;
      const alpha = ghost.alpha * intensity;
      const stops = ghost.ring
        ? [[0, "rgba(0,0,0,0)"], [.42, `rgba(${red},${green},${blue},${alpha * .08})`], [.68, `rgba(${red},${green},${blue},${alpha})`], [.78, `rgba(${red},${green},${blue},${alpha * .42})`], [1, "rgba(0,0,0,0)"]]
        : [[0, `rgba(${red},${green},${blue},${alpha})`], [.22, `rgba(${red},${green},${blue},${alpha * .52})`], [1, "rgba(0,0,0,0)"]];
      drawRadial(x, y, scale * ghost.radius, stops);
    });

    if (edgeBoost > .015) {
      const side = planetPosition < .5 ? -1 : 1;
      const contactX = sourceX + side * scale * starRadius;
      const contactIntensity = edgeBoost * (.35 + (1 - overlap) * .65);
      drawRadial(contactX, sourceY, scale * .052, [
        [0, `rgba(255,255,255,${.76 * contactIntensity})`],
        [.1, `rgba(255,238,174,${.54 * contactIntensity})`],
        [.36, `rgba(255,178,55,${.16 * contactIntensity})`],
        [1, "rgba(0,0,0,0)"],
      ]);
      const contactStreak = context.createLinearGradient(contactX - scale * .11, sourceY, contactX + scale * .11, sourceY);
      contactStreak.addColorStop(0, "rgba(0,0,0,0)");
      contactStreak.addColorStop(.5, `rgba(255,248,215,${.7 * contactIntensity})`);
      contactStreak.addColorStop(1, "rgba(0,0,0,0)");
      context.fillStyle = contactStreak;
      context.fillRect(contactX - scale * .11, sourceY - .7, scale * .22, 1.4);
    }

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
    drawFlare(overlap, edgeBoost, x);
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
