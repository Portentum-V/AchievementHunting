// Compare a rebuilt guide with a reference guide for the same game.
// Usage: node compare_guides.js <reference guide.js> <rebuilt guide.js> <list.json>
// Used to test the skill: rebuild a game that already has a checked guide,
// then compare. Accuracy needs a judge agent; this script measures coverage.
const fs = require("fs");
const vm = require("vm");

const load = p => {
  const ctx = { window: {} };
  vm.runInNewContext(fs.readFileSync(p, "utf8"), ctx, { filename: p });
  return ctx.window.GUIDE;
};
const [refPath, newPath, listPath] = process.argv.slice(2);
const ref = load(refPath), neu = load(newPath);
const list = JSON.parse(fs.readFileSync(listPath, "utf8"));
const remaining = list.achievements.filter(a => !a.unlocked).map(a => a.api.toLowerCase());

const words = t => (Array.isArray(t) ? t.join(" ") : t || "").split(/\s+/).filter(Boolean).length;
const stats = g => {
  const a = g.achievements || {};
  const tipped = remaining.filter(k => a[k]?.tip);
  const w = remaining.map(k => words(a[k]?.tip));
  return {
    "keys": Object.keys(a).length,
    "remaining with a tip": `${tipped.length}/${remaining.length}`,
    "words per remaining tip (mean)": (w.reduce((s, x) => s + x, 0) / Math.max(1, w.length)).toFixed(0),
    "checklists": Object.values(a).filter(x => x.steps).length,
    "checklist items": Object.values(a).reduce((s, x) => s + (x.steps?.length || 0), 0),
    "categories": (g.categories || []).length,
    "flags": Object.keys(g.flags || {}).join(", ") || "none",
    "highlight": g.highlight?.flag || "default",
  };
};
const rs = stats(ref), ns = stats(neu);
console.log(`${"metric".padEnd(32)} ${"reference".padEnd(28)} rebuilt`);
for (const k of Object.keys(rs)) console.log(`${k.padEnd(32)} ${String(rs[k]).padEnd(28)} ${ns[k]}`);

// Remaining achievements where the rebuild says much less than the reference.
const thin = remaining
  .map(k => ({ k, r: words(ref.achievements[k]?.tip), n: words(neu.achievements?.[k]?.tip) }))
  .filter(x => x.r >= 20 && x.n < x.r / 2)
  .sort((a, b) => (b.r - b.n) - (a.r - a.n));
console.log(`\nRemaining tips under half the reference length: ${thin.length}`);
for (const x of thin.slice(0, 15)) console.log(`  ${x.k}: ${x.n} words vs ${x.r}`);
const lostSteps = remaining.filter(k => ref.achievements[k]?.steps && !neu.achievements?.[k]?.steps);
console.log(`Checklists in the reference but not the rebuild: ${lostSteps.join(", ") || "none"}`);
