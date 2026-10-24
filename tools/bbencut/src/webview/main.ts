// Webview UI for BBenCut -- Step 3 of the approved plan. Much simpler than
// Breakdowns' dialog: pick a cut procedure, edit its README-documented
// parameters (see the plan's parameter table -- only the fields the
// original BBenCut UI actually exposed; everything else stays at its coded
// default), set Total/Loop length in beats, then Apply computes the cut
// sequence client-side (reusing slicer.ts + the ported bbcut/* algorithms
// unchanged) and posts pure JSON back to the host. No LOM/OSC work happens
// here, and nothing is placed into Live yet -- that's Step 4/5.
import type { AlgorithmId, BBenCutContext, BBenCutRequest } from "../protocol.js";
import { generateCutSequence, mapToSliceDefinitions } from "../slicer.js";
import {
  BBCutProc11,
  ChooseCutProc,
  ChooseBlockProc,
  WarpCutProc1,
  SQPusher1,
  SQPusher2,
  CageCut,
  TimelineCut,
  BBCPPermute,
  ThrashCutProc1,
  type BBCutProc,
} from "../bbcut/index.js";

// ---- host bridge -----------------------------------------------------------
// window.liveActionsSend, injected by breakdowns_window.py (shared host for
// all webview tools), forwards a raw JSON string to window.pywebview.api.receive.
// NOT window.chrome.webview.postMessage -- that's pywebview's own internal
// js_api channel on the Windows edgechromium backend; hijacking it corrupts
// pywebview's own call protocol (see breakdowns_window.py's on_loaded).
type Outgoing = { method: "close_and_send"; params: [string | null] };
interface LiveBridge {
  webkit?: { messageHandlers?: { live?: { postMessage(m: Outgoing): void } } };
  liveActionsSend?: (raw: string) => void;
}
function send(payload: string | null): void {
  const w = window as unknown as LiveBridge;
  const msg: Outgoing = { method: "close_and_send", params: [payload] };
  if (w.webkit?.messageHandlers?.live) w.webkit.messageHandlers.live.postMessage(msg);
  else if (w.liveActionsSend) w.liveActionsSend(JSON.stringify(msg));
}

// ---- state -----------------------------------------------------------------
const ctx: BBenCutContext = (window as unknown as { __CTX__?: BBenCutContext }).__CTX__ ?? {
  hasClip: false,
  totalLengthBeats: 16,
  loopLengthBeats: 4,
};

// ---- per-algorithm parameter spec ------------------------------------------
// Only fields BBenCut-src\README.md's own tables document as user-facing.
// Everything else is a function-typed field in the ported TS and stays at
// its coded default, matching how the original UI worked.
interface ParamField {
  key: string;
  label: string;
  default: number;
  step: number;
}
interface AlgorithmSpec {
  label: string;
  params: ParamField[];
  build(p: Record<string, number>): BBCutProc;
}

const ALGORITHMS: Record<AlgorithmId, AlgorithmSpec> = {
  BBCutProc11: {
    label: "BBCutProc11 (Classic)",
    params: [
      { key: "sdiv", label: "Subdivisions", default: 8, step: 1 },
      { key: "repeatschance", label: "Repeats chance", default: 0.2, step: 0.05 },
      { key: "repeatsspeed", label: "Repeats speed", default: 2, step: 1 },
      { key: "repeatsarea", label: "Repeats area", default: 0.5, step: 0.05 },
    ],
    build: (p) =>
      new BBCutProc11({
        sdiv: p.sdiv,
        repeatschance: p.repeatschance,
        repeatsspeed: p.repeatsspeed,
        repeatsarea: p.repeatsarea,
      }),
  },
  ChooseCutProc: {
    label: "ChooseCutProc",
    params: [
      { key: "rollchance", label: "Roll chance", default: 0.1, step: 0.05 },
      { key: "rollallowed", label: "Roll allowed (beats)", default: 2.0, step: 0.25 },
    ],
    build: (p) =>
      new ChooseCutProc({ rollchance: p.rollchance, rollallowed: p.rollallowed }),
  },
  ChooseBlockProc: {
    label: "ChooseBlockProc",
    params: [],
    build: () => new ChooseBlockProc(),
  },
  WarpCutProc1: {
    label: "WarpCutProc1",
    params: [
      { key: "straightChance", label: "Straight chance", default: 0.5, step: 0.05 },
      { key: "arithmeticChance", label: "Arithmetic chance", default: 0.7, step: 0.05 },
      { key: "accelChance", label: "Accel chance", default: 0.6, step: 0.05 },
      { key: "accelFactor", label: "Accel factor", default: 0.9, step: 0.01 },
    ],
    build: (p) =>
      new WarpCutProc1({
        probs: [p.straightChance, p.arithmeticChance, p.accelChance],
        accel: p.accelFactor,
      }),
  },
  SQPusher1: {
    label: "SQPusher1",
    params: [
      { key: "activity", label: "Activity", default: 0.1, step: 0.05 },
      { key: "fillfreq", label: "Fill frequency (phrases)", default: 4, step: 1 },
      { key: "fillscramble", label: "Fill scramble", default: 0.0, step: 0.05 },
    ],
    build: (p) =>
      new SQPusher1({ activity: p.activity, fillfreq: p.fillfreq, fillscramble: p.fillscramble }),
  },
  SQPusher2: {
    label: "SQPusher2 (Data)",
    params: [
      { key: "scramble", label: "Scramble", default: 0.0, step: 0.05 },
      { key: "quant", label: "Quantise", default: 0.0, step: 0.05 },
    ],
    build: (p) => new SQPusher2({ scramble: p.scramble, quant: p.quant }),
  },
  CageCut: {
    label: "CageCut (Cage)",
    params: [],
    build: () => new CageCut(),
  },
  TimelineCut: {
    label: "TimelineCut",
    params: [],
    build: () => new TimelineCut(),
  },
  BBCPPermute: {
    label: "BBCPPermute",
    params: [{ key: "subdivfunc", label: "Subdivisions", default: 8, step: 1 }],
    build: (p) => new BBCPPermute({ subdivfunc: p.subdivfunc }),
  },
  ThrashCutProc1: {
    label: "ThrashCutProc1",
    params: [
      { key: "kickoffset", label: "Kick offset (beats)", default: 0.0, step: 0.05 },
      { key: "snareoffset", label: "Snare offset (beats)", default: 0.125, step: 0.05 },
      { key: "stopchance", label: "Stop chance", default: 0.125, step: 0.05 },
    ],
    build: (p) =>
      new ThrashCutProc1({
        kickoffset: p.kickoffset,
        snareoffset: p.snareoffset,
        stopchance: p.stopchance,
      }),
  },
};

const ALGORITHM_ORDER: AlgorithmId[] = [
  "BBCutProc11",
  "ChooseCutProc",
  "ChooseBlockProc",
  "WarpCutProc1",
  "SQPusher1",
  "SQPusher2",
  "CageCut",
  "TimelineCut",
  "BBCPPermute",
  "ThrashCutProc1",
];

let currentAlgorithm: AlgorithmId = "BBCutProc11";
let currentParams: Record<string, number> = {};

function resetParamsForAlgorithm(id: AlgorithmId): void {
  currentParams = {};
  for (const f of ALGORITHMS[id].params) currentParams[f.key] = f.default;
}
resetParamsForAlgorithm(currentAlgorithm);

// ---- DOM ---------------------------------------------------------------
function el<T extends HTMLElement>(id: string): T {
  const found = document.getElementById(id);
  if (!found) throw new Error(`missing #${id}`);
  return found as T;
}

function renderParamFields(): void {
  const host = el<HTMLDivElement>("paramFields");
  host.innerHTML = "";
  const spec = ALGORITHMS[currentAlgorithm];
  if (spec.params.length === 0) {
    const p = document.createElement("div");
    p.className = "no-params";
    p.textContent = "No user parameters for this procedure.";
    host.appendChild(p);
    return;
  }
  for (const field of spec.params) {
    const row = document.createElement("div");
    row.className = "field-row";
    const label = document.createElement("label");
    label.textContent = field.label;
    label.htmlFor = `field-${field.key}`;
    const input = document.createElement("input");
    input.type = "number";
    input.id = `field-${field.key}`;
    input.step = String(field.step);
    input.value = String(currentParams[field.key] ?? field.default);
    input.addEventListener("input", () => {
      const v = parseFloat(input.value);
      currentParams[field.key] = Number.isFinite(v) ? v : field.default;
    });
    row.appendChild(label);
    row.appendChild(input);
    host.appendChild(row);
  }
}

function populateAlgorithmSelect(): void {
  const sel = el<HTMLSelectElement>("algorithm");
  sel.innerHTML = "";
  for (const id of ALGORITHM_ORDER) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = ALGORITHMS[id].label;
    sel.appendChild(opt);
  }
  sel.value = currentAlgorithm;
  sel.addEventListener("change", () => {
    currentAlgorithm = sel.value as AlgorithmId;
    resetParamsForAlgorithm(currentAlgorithm);
    renderParamFields();
  });
}

/** MIN_CLIP_BEATS floor, matching slicer.ts -- a loop shorter than this can't
 *  hold a single real clip, and a non-positive total would make
 *  generateCutSequence's while loop never advance. */
const MIN_LOOP_BEATS = 0.25;

function applyRequest(): BBenCutRequest {
  const rawTotal = parseFloat(el<HTMLInputElement>("totalLength").value);
  const totalLengthBeats = Number.isFinite(rawTotal) && rawTotal > 0 ? rawTotal : ctx.totalLengthBeats;
  const rawLoop = parseFloat(el<HTMLInputElement>("loopLength").value);
  const loopLengthBeats =
    Number.isFinite(rawLoop) && rawLoop >= MIN_LOOP_BEATS ? rawLoop : Math.max(MIN_LOOP_BEATS, ctx.loopLengthBeats);
  if (currentAlgorithm === "WarpCutProc1" && typeof currentParams.accelFactor === "number") {
    // Geometric roll spacing needs 0 < accel < 1; a boundary or out-of-range
    // value degenerates the roll durations instead of producing a real error.
    currentParams.accelFactor = Math.min(0.99, Math.max(0.01, currentParams.accelFactor));
  }
  const spec = ALGORITHMS[currentAlgorithm];
  const proc = spec.build(currentParams);
  const blocks = generateCutSequence(proc, totalLengthBeats, loopLengthBeats);
  const { slices, rollGroups } = mapToSliceDefinitions(
    blocks,
    0, // clipStartTime -- honest 0 default; real Arrangement placement is Step 4/5
    0, // clipLoopStart
    loopLengthBeats,
    ctx.filePath ?? "",
  );
  return {
    algorithm: currentAlgorithm,
    params: { ...currentParams },
    totalLengthBeats,
    loopLengthBeats,
    slices,
    rollGroups,
  };
}

function init(): void {
  el<HTMLDivElement>("clipChip").textContent = ctx.hasClip
    ? ctx.clipName ?? "clip"
    : "no clip context yet";
  el<HTMLInputElement>("totalLength").value = String(ctx.totalLengthBeats);
  el<HTMLInputElement>("loopLength").value = String(ctx.loopLengthBeats);

  populateAlgorithmSelect();
  renderParamFields();

  el<HTMLButtonElement>("cancel").addEventListener("click", () => send(null));
  el<HTMLButtonElement>("apply").addEventListener("click", () => {
    const req = applyRequest();
    send(JSON.stringify(req));
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") send(null);
  });
}

init();
