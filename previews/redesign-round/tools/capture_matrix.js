/* Captures every layout x theme, and proves the markup is identical across themes.
 *
 *   npm i playwright-core          (once, anywhere on NODE_PATH)
 *   node capture_matrix.js         (from previews/redesign-round/tools)
 *
 * Output: shots/<layout>__<theme>.png, shots/extra__*.png, shots/dom-report.json
 * "identical markup" = sha1 of #app.innerHTML is the same for all 11 themes of a layout.
 */
const { chromium } = require("playwright-core");
const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROUND = path.resolve(__dirname, "..");
const SHOTS = path.join(ROUND, "shots");
const exe = process.env.CHROME || os.homedir().split(String.fromCharCode(92)).join("/") + "/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe";
const url = (l, t) => "file:///" + ROUND.split(String.fromCharCode(92)).join("/").replace(/ /g, "%20") + `/layout-${l}.html?theme=${t}&embed=1`;

const THEMES = fs.readdirSync(path.join(ROUND, "themes")).filter((f) => f.endsWith(".css")).map((f) => f.slice(0, -4)).sort();
const LAYOUTS = ["a", "b", "c", "d"];
// The default view of each layout, plus one interaction that makes the IA visible.
const OPEN = { a: [], b: [".la-card >> nth=5"], c: [".la-row >> nth=1"], d: [] };

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const b = await chromium.launch({ executablePath: exe });
  const report = { themes: THEMES, layouts: {} };
  for (const l of LAYOUTS) {
    const hashes = {}, errors = {};
    for (const t of THEMES) {
      const p = await b.newPage({ viewport: { width: 1360, height: 820 } });
      const errs = [];
      p.on("pageerror", (e) => errs.push(String(e)));
      await p.goto(url(l, t));
      await p.waitForSelector('body[data-ready="1"]', { timeout: 20000 });
      for (const sel of OPEN[l]) { await p.click(sel); await p.waitForTimeout(80); }
      await p.waitForTimeout(250);
      hashes[t] = crypto.createHash("sha1").update(await p.evaluate(() => document.getElementById("app").innerHTML)).digest("hex").slice(0, 12);
      errors[t] = errs;
      await p.screenshot({ path: path.join(SHOTS, `${l}__${t}.png`) });
      await p.close();
    }
    const uniq = [...new Set(Object.values(hashes))];
    report.layouts[l] = { identicalAcrossThemes: uniq.length === 1, distinctMarkups: uniq.length, hashes, jsErrors: Object.values(errors).flat().length };
    console.log(`layout ${l}: ${THEMES.length} themes, distinct #app markups = ${uniq.length}, js errors = ${report.layouts[l].jsErrors}`);
  }

  // Extra views (Genius / Settings / console) on one theme, for the IA discussion.
  const extras = [
    ["a", "genius", ['[data-k="genius"]']], ["b", "genius", ['[data-k="genius"]']], ["b", "settings", ['[data-k="settings"]']],
    ["c", "genius", ['[data-k="genius"]']], ["d", "console", ['[data-k="console"]']],
    ["a", "settings", ['[data-act="settings"]']], ["a", "diag", ['[data-act="diag"]']], ["a", "settings-themes-open", ['[data-act="settings"]', '[data-act="toggle-themes"]']], ["a", "console", ['[data-act="console"]']], ["a", "filter-setwide", ['[data-k="set"]']], ["c", "targets-diag", ['[data-act="diag"]']], ["b", "targets-pop", ['[data-act="tgt"]']],
  ];
  for (const [l, name, steps] of extras) {
    const p = await b.newPage({ viewport: { width: 1360, height: 820 } });
    await p.goto(url(l, "risograph-art-studio"));
    await p.waitForSelector('body[data-ready="1"]');
    for (const s of steps) { await p.click(s); await p.waitForTimeout(120); }
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(SHOTS, `extra__${l}-${name}.png`) });
    await p.close();
  }
  await b.close();
  fs.writeFileSync(path.join(SHOTS, "dom-report.json"), JSON.stringify(report, null, 1));
  const bad = Object.entries(report.layouts).filter(([, v]) => !v.identicalAcrossThemes || v.jsErrors);
  if (bad.length) { console.error("FAIL:", bad.map(([k]) => k).join(",")); process.exit(1); }
  console.log("PASS: markup identical across all themes for every layout");
})();
