import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import { createIcons, Play, RotateCcw, Plus, Download, Trash2 } from "lucide";
import Papa from "papaparse";
import { Engine, names } from "./engine";
import type { Estimate, Scenario } from "./engine";
import "./workbench.css";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <header class="topbar"><a class="wordmark" href="./">SN <span>RESEARCH / 07</span></a><a href="https://github.com/Sushant-Nemade/boston-housing-workbench">Source & releases</a></header>
  <main>
    <section class="heading"><div><p class="eyebrow">1970 CENSUS ERA / HISTORICAL BENCHMARK</p><h1>Boston Housing</h1></div><div class="dataset-mark"><strong>506</strong><span>historical tracts<br>11 retained inputs</span></div></section>
    <figure class="skyline"><img class="panorama" src="./boston.jpg" alt="Boston Back Bay skyline across the Charles River from Longfellow Bridge, photographed in 2017" width="1400" height="560"><figcaption>Boston, 2017. Context photograph, not training data. <a href="https://commons.wikimedia.org/wiki/File:Boston_skyline_from_Longfellow_Bridge_September_2017_panorama_2.jpg">King of Hearts / CC BY-SA 4.0</a></figcaption></figure>
    <p class="scope-warning"><strong>Historical research only.</strong> Tract medians, not individual homes or current prices. Not for appraisal, lending, buying, selling, or housing allocation.</p>
    <div class="tabs" role="tablist" aria-label="Research views">
      <button role="tab" id="estimate-tab" aria-controls="estimate-panel" aria-selected="true">Estimate</button>
      <button role="tab" id="evidence-tab" aria-controls="evidence-panel" aria-selected="false" tabindex="-1">Evidence</button>
      <button role="tab" id="scenarios-tab" aria-controls="scenarios-panel" aria-selected="false" tabindex="-1">Scenarios</button>
      <button role="tab" id="scope-tab" aria-controls="scope-panel" aria-selected="false" tabindex="-1">Scope & provenance</button>
    </div>
    <p id="status" role="status">Loading verified model...</p><button id="retry" hidden>Retry model</button>
    <section role="tabpanel" id="estimate-panel" aria-labelledby="estimate-tab" class="estimate-layout">
      <form id="inputs"><div class="section-title"><h2>Tract profile</h2><button type="button" class="icon-button" id="reset" aria-label="Reset inputs" title="Reset inputs"><i data-lucide="rotate-ccw"></i></button></div><div id="fields" class="fields"></div><button id="run" class="primary" disabled><i data-lucide="play"></i>Run estimate</button></form>
      <div class="result-area"><p class="eyebrow">MODEL ESTIMATE / HISTORICAL USD</p><output id="estimate">--</output><p>Median owner-occupied value per tract</p><div class="band-label"><strong id="band">--</strong><span>Nominal 90% historical residual band</span></div><canvas id="interval-chart" width="900" height="260" aria-label="Estimate and historical residual band, on the dataset's 5 to 50 thousand dollar range"></canvas><p class="muted">The $50,000 ceiling is a dataset cap, not a market maximum. This band is not an individual prediction guarantee.</p><div class="actions"><button id="save" disabled><i data-lucide="plus"></i>Save scenario</button><button id="download" disabled><i data-lucide="download"></i>Export estimate</button></div><div class="csv-section"><h3>Batch scenarios</h3><div class="actions"><label class="file-label">CSV file<input id="csv-file" type="file" accept=".csv,text/csv"></label><button id="template">CSV template</button></div><p id="csv-status" role="status"></p><button id="batch-download" hidden><i data-lucide="download"></i>Export batch</button></div></div>
    </section>
    <section role="tabpanel" id="evidence-panel" aria-labelledby="evidence-tab" hidden><h2>Untouched test evidence</h2><p class="muted">102 held-out rows. Random split, not spatial validation. Units below are historical dollars.</p><div class="metrics"><div><span>Model MAE</span><strong id="test-mae">--</strong></div><div><span>Median baseline MAE</span><strong id="baseline-mae">--</strong></div><div><span>Historical band coverage</span><strong id="coverage">--</strong></div><div><span>Test R-squared</span><strong id="r2">--</strong></div></div><h3>Mean absolute error comparison</h3><canvas id="evidence-chart" width="1000" height="280" aria-label="Actual held-out model error compared with the training-median baseline"></canvas><dl id="evaluation-details"></dl></section>
    <section role="tabpanel" id="scenarios-panel" aria-labelledby="scenarios-tab" hidden><div class="section-title"><h2>Saved scenarios</h2><button id="clear"><i data-lucide="trash-2"></i>Clear saved</button></div><p id="saved-status">Saved inputs stay in this browser.</p><div class="table-scroll"><table id="saved"><thead><tr><th>Scenario</th><th>Average rooms</th><th>Historical estimate</th><th>Historical band</th></tr></thead><tbody></tbody></table></div></section>
    <section role="tabpanel" id="scope-panel" aria-labelledby="scope-tab" hidden><h2>Scope & provenance</h2><ul id="limitations"></ul><h3>Dataset</h3><p>Harrison and Rubinfeld, 1978, <em>Hedonic housing prices and the demand for clean air</em>. <a href="https://www.openml.org/d/531">OpenML 531, version 1</a>. Publisher license label: "Public" (nonstandard). No CC license or commercial-use certification is asserted. Raw source data are not vendored.</p><h3>Excluded inputs</h3><p>B (engineered race variable) and LSTAT (socioeconomic-status field) are excluded. Remaining inputs and the target may still encode historic discrimination. Removing two fields does not establish fairness.</p><h3>Source lineage</h3><p>GPLv3 adaptation of <a href="https://github.com/KalyanM45/House-Price-Prediction/tree/61515c0c4e70fca380728d8752048d38e48eeefa">KalyanM45 / House-Price-Prediction</a>, discovered through AI-Project-Gallery. Untrusted upstream pickle artifacts are never executed.</p><p><a href="./report.json">Full model report</a> / <a href="./licenses.json">Third-party notices</a> / <a href="./LICENSE">GPLv3</a></p><p class="hash" id="hash"></p></section>
    <footer>Boston Housing Research Workbench <span>Historical evidence. Explicit limits.</span></footer>
  </main>`;

const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const money = (value: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value * 1000);
const icons = () => createIcons({ icons: { Play, RotateCcw, Plus, Download, Trash2 } });
const storageKey = "boston-housing-research-scenarios-v1";
let engine: Engine | undefined, current: Estimate | undefined, saved: Scenario[] = [], batch: Estimate[] = [];
const status = (message: string) => { element("status").textContent = message; };

function exportCsv(filename: string, rows: Estimate[]) {
  const data = rows.map((row) => ({ scope: "HISTORICAL TRACT MEDIAN - NOT CURRENT VALUE", ...row.input,
    estimate_historical_usd: (row.estimate_kusd * 1000).toFixed(2), lower_historical_usd: (row.lower_kusd * 1000).toFixed(2), upper_historical_usd: (row.upper_kusd * 1000).toFixed(2), model_sha256: row.model_sha256 }));
  download(filename, Papa.unparse(data, { escapeFormulae: true }));
}

function download(filename: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function context(id: string) {
  const canvas = element<HTMLCanvasElement>(id), ctx = canvas.getContext("2d")!;
  ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.font = "22px IBM Plex Sans";
  return { canvas, ctx };
}

function drawEstimate(result: Estimate) {
  const { ctx } = context("interval-chart"), position = (value: number) => 70 + (value - 5) / 45 * 760;
  ctx.strokeStyle = "#c9d2ce"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(70, 170); ctx.lineTo(830, 170); ctx.stroke();
  ctx.fillStyle = "#d5e9dd"; ctx.fillRect(position(result.lower_kusd), 85, position(result.upper_kusd) - position(result.lower_kusd), 70);
  ctx.fillStyle = "#176445"; ctx.fillRect(position(result.estimate_kusd) - 3, 60, 6, 110);
  ctx.fillStyle = "#414a45"; ctx.textAlign = "center";
  for (const tick of [5, 20, 35, 50]) ctx.fillText(`$${tick}k`, position(tick), 220);
}

function drawEvidence() {
  if (!engine) return;
  const { ctx } = context("evidence-chart"), evaluation = engine.report.evaluation;
  const maximum = Math.max(evaluation.median_baseline.mae_kusd, evaluation.test.mae_kusd) * 1.15;
  for (const [index, [label, value, color]] of [["Model", evaluation.test.mae_kusd, "#176445"], ["Baseline", evaluation.median_baseline.mae_kusd, "#a74b52"]].entries()) {
    const y = 40 + index * 110; ctx.fillStyle = "#303832"; ctx.fillText(String(label), 10, y + 34);
    ctx.fillStyle = String(color); ctx.fillRect(150, y, Number(value) / maximum * 650, 54);
    ctx.fillStyle = "#303832"; ctx.fillText(money(Number(value)), 820, y + 34);
  }
}

async function renderSaved() {
  const body = element<HTMLTableSectionElement>("saved").querySelector("tbody")!;
  body.replaceChildren();
  if (!engine || !saved.length) { element("saved-status").textContent = "No saved scenarios. Saved inputs stay in this browser."; return; }
  for (const [index, result] of (await engine.predict(saved)).entries()) {
    const row = body.insertRow();
    for (const value of [`Scenario ${index + 1}`, result.input.RM.toFixed(2), money(result.estimate_kusd), `${money(result.lower_kusd)} - ${money(result.upper_kusd)}`]) row.insertCell().textContent = value;
  }
  element("saved-status").textContent = `${saved.length}/20 scenarios. Recomputed with the currently verified model.`;
}

function persistSaved() {
  try { localStorage.setItem(storageKey, JSON.stringify(saved)); }
  catch { status("Browser storage unavailable; scenarios remain in memory for this session."); }
}

function resetInputs() {
  if (!engine) return;
  for (const name of names) element<HTMLInputElement>(name).value = String(engine.report.features[name].default);
}

async function load() {
  element("retry").hidden = true; status("Loading verified model...");
  try {
    engine = await Engine.load();
    const fields = element("fields"); fields.replaceChildren();
    for (const name of names) {
      const spec = engine.report.features[name], label = document.createElement("label"), text = document.createElement("span"), unit = document.createElement("small"), input = document.createElement("input");
      text.textContent = spec.label; unit.textContent = spec.unit; input.id = name; input.name = name; input.type = "number"; input.required = true;
      input.min = String(spec.min); input.max = String(spec.max); input.step = name === "CHAS" || name === "RAD" ? "1" : "any";
      label.append(text, input, unit); fields.append(label);
    }
    resetInputs();
    const evaluation = engine.report.evaluation;
    element("test-mae").textContent = money(evaluation.test.mae_kusd); element("baseline-mae").textContent = money(evaluation.median_baseline.mae_kusd);
    element("coverage").textContent = `${(evaluation.interval_coverage * 100).toFixed(1)}%`; element("r2").textContent = evaluation.test.r2.toFixed(3);
    element("evaluation-details").textContent = `Train ${engine.report.splits.train.rows} / calibration ${engine.report.splits.calibration.rows} / test ${engine.report.splits.test.rows}. Five-fold training-only model selection. Selected: ${engine.report.model}. ${evaluation.capped_test_rows} top-coded test labels. ONNX parity error: ${money(evaluation.onnx_max_error_kusd)} (under $0.02).`;
    const limitations = element("limitations"); limitations.replaceChildren();
    for (const line of engine.report.limitations) { const item = document.createElement("li"); item.textContent = line; limitations.append(item); }
    element("hash").textContent = `MODEL SHA-256 ${engine.report.model_sha256}`;
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored && stored.length <= 50000) {
        const parsed: unknown = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length <= 20) saved = parsed.map((input) => engine!.validate(input));
      }
    } catch { saved = []; status("Invalid stored inputs were ignored."); }
    element<HTMLButtonElement>("run").disabled = false;
    drawEvidence(); await renderSaved(); status("Verified model ready / inputs stay in this browser");
  } catch (error) { status(error instanceof Error ? error.message : "Unable to load verified model"); element("retry").hidden = false; }
}

element("inputs").addEventListener("submit", async (event) => {
  event.preventDefault(); if (!engine) return;
  const run = element<HTMLButtonElement>("run"); run.disabled = true;
  try {
    const input = Object.fromEntries(names.map((name) => [name, Number(element<HTMLInputElement>(name).value)]));
    current = (await engine.predict([input]))[0];
    element("estimate").textContent = money(current.estimate_kusd); element("estimate").setAttribute("data-value", String(current.estimate_kusd));
    element("band").textContent = `${money(current.lower_kusd)} - ${money(current.upper_kusd)}`;
    drawEstimate(current); element<HTMLButtonElement>("save").disabled = false; element<HTMLButtonElement>("download").disabled = false;
    status("Historical estimate complete. Not a current property valuation.");
  } catch (error) { status(error instanceof Error ? error.message : "Invalid scenario"); }
  finally { run.disabled = false; }
});
element("reset").addEventListener("click", resetInputs);
element("retry").addEventListener("click", () => void load());
element("save").addEventListener("click", async () => { if (!current) return; if (saved.length >= 20) { status("20-scenario limit reached; clear saved scenarios first."); return; } saved.push(current.input); persistSaved(); await renderSaved(); status("Scenario saved in this browser."); });
element("clear").addEventListener("click", async () => { saved = []; persistSaved(); await renderSaved(); });
element("download").addEventListener("click", () => { if (current) exportCsv("boston-historical-estimate.csv", [current]); });
element("template").addEventListener("click", () => { if (engine) download("boston-scenario-template.csv", Papa.unparse([Object.fromEntries(names.map((name) => [name, engine!.report.features[name].default]))])); });
element("batch-download").addEventListener("click", () => exportCsv("boston-historical-batch.csv", batch));
element("csv-file").addEventListener("change", async () => {
  const file = element<HTMLInputElement>("csv-file").files?.[0]; batch = []; element("batch-download").hidden = true;
  if (!file || !engine) return;
  try {
    if (file.size > 100000) throw new Error("CSV exceeds 100 KB limit");
    const parsed = Papa.parse<Record<string, string>>(await file.text(), { header: true, skipEmptyLines: "greedy" });
    if (parsed.errors.length || parsed.meta.fields?.join() !== names.join()) throw new Error(`CSV must have exactly these ordered columns: ${names.join(",")}`);
    if (!parsed.data.length || parsed.data.length > 100) throw new Error("CSV must contain 1-100 rows");
    const inputs = parsed.data.map((row) => Object.fromEntries(names.map((name) => { if (!row[name]?.trim()) throw new Error(`Missing ${name}`); return [name, Number(row[name])]; })));
    batch = await engine.predict(inputs); element("csv-status").textContent = `${batch.length} historical scenarios calculated.`; element("batch-download").hidden = false;
  } catch (error) { element("csv-status").textContent = error instanceof Error ? error.message : "Invalid CSV"; }
});

const tabs = [...document.querySelectorAll<HTMLButtonElement>("[role=tab]")];
function selectTab(tab: HTMLButtonElement) {
  for (const candidate of tabs) { const active = candidate === tab; candidate.setAttribute("aria-selected", String(active)); candidate.tabIndex = active ? 0 : -1; element(candidate.getAttribute("aria-controls")!).hidden = !active; }
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (event) => {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault(); selectTab(tabs[next]); tabs[next].focus();
  });
});
icons(); void load();