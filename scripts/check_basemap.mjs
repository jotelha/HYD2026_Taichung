// Smoke test for the English basemap on the Boba Index map (index.html) (run by the "Check basemap" workflow).
//
// Loads the page in headless Chromium with network access, waits for the OpenFreeMap vector basemap,
// then reports: which basemap is up (vector or the raster fallback), how far the basemap sits from the
// svg overlay at a known point, and which labels are drawn in English or fall back to the local name.
// Screenshots of the three themes go to check-basemap/.
//
// Usage: node scripts/check_basemap.mjs http://localhost:8000/
// Exits non-zero if the vector basemap does not start or is misaligned by more than 2 px.

import { chromium } from "playwright";
import fs from "node:fs";

const url = process.argv[2] || "http://localhost:8000/";
const OUT = "check-basemap";
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  // runners have no GPU: let WebGL fall back to SwiftShader
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(url, { waitUntil: "load" });

const mode = await page.waitForFunction(
  () => ["vector", "raster"].includes(window.__hydBasemap?.mode) && window.__hydBasemap.mode,
  null, { timeout: 30000 },
).then((h) => h.jsonValue()).catch(() => "timeout");
console.log(`basemap mode: ${mode}`);
if (mode !== "vector") {
  console.log(await page.evaluate(() => document.querySelector("#osm-msg")?.textContent));
  await page.screenshot({ path: `${OUT}/fallback.png` });
  await browser.close();
  process.exit(1);
}

const idle = () => page.evaluate(() => new Promise((resolve) => {
  const m = window.__hydBasemap.map;
  if (m.loaded()) resolve(); else m.once("idle", resolve);
  setTimeout(resolve, 15000);
}));

// compare the Feng Chia market marker in the svg with MapLibre's projection of its coordinates
const alignment = () => page.evaluate(() => {
  const m = window.__hydBasemap.map;
  const c = document.querySelector("#vmap").getBoundingClientRect();
  const s = document.querySelector("#map").getBoundingClientRect();
  const FENGJIA = [120.6459734, 24.1780635]; // centre of OSM way 450771065, as in the market tooltip
  const g = [...document.querySelectorAll("#g-mkt > g")].find((el) => /Fengjia Night Market/.test(el.textContent));
  const t = g.getAttribute("transform").match(/translate\(([-\d.]+) ([-\d.]+)\)/);
  const p = m.project(FENGJIA);
  return Math.hypot(c.left + p.x - (s.left + +t[1]), c.top + p.y - (s.top + +t[2]));
});

const labels = () => page.evaluate(() => {
  const m = window.__hydBasemap.map;
  const symbolLayers = m.getStyle().layers.filter((l) => l.type === "symbol").map((l) => l.id);
  const seen = new Map();
  for (const f of m.queryRenderedFeatures({ layers: symbolLayers })) {
    const p = f.properties;
    if (!p.name) continue;
    const en = p["name:en"] || (p.name_en && p.name_en !== p.name ? p.name_en : null);
    seen.set(p.name, en);
  }
  const all = [...seen.entries()];
  return {
    total: all.length,
    english: all.filter(([, en]) => en).length,
    sampleEnglish: all.filter(([, en]) => en).slice(0, 15).map(([zh, en]) => `${en} (${zh})`),
    sampleLocalOnly: all.filter(([, en]) => !en).slice(0, 10).map(([zh]) => zh),
  };
});

let worst = 0;
for (const [name, act] of [
  ["overview", null],
  ["central-district", () => page.click(".legend-dist >> nth=0")],
  ["feng-chia", () => page.click('[data-nm="0"]')],
]) {
  if (act) { await act(); await page.waitForTimeout(800); }
  await idle();
  const off = await alignment();
  worst = Math.max(worst, off);
  const l = await labels();
  console.log(`\n[${name}] zoom ${(await page.evaluate(() => window.__hydBasemap.map.getZoom())).toFixed(2)}, ` +
    `alignment ${off.toFixed(2)} px, labels ${l.english}/${l.total} in English`);
  console.log(`  English: ${l.sampleEnglish.join(" | ")}`);
  console.log(`  local name only: ${l.sampleLocalOnly.join(" | ")}`);
  for (const theme of ["light", "white", "dark"]) {
    await page.click(`[data-theme-set="${theme}"]`);
    await page.waitForTimeout(200);
    await page.screenshot({ path: `${OUT}/${name}-${theme}.png` });
  }
}

console.log(`\nworst alignment: ${worst.toFixed(2)} px; page errors: ${JSON.stringify(errors)}`);
await browser.close();
process.exit(worst > 2 || errors.length ? 1 : 0);
