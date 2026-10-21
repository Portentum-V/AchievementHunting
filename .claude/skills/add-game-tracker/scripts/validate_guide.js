// Check a tracker guide against the Steam achievement list.
// Usage: node validate_guide.js <game>-tracker/guide.js <list.json from pull_game.py>
// Prints PASS or FAIL. Errors fail the check; warnings do not.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const [guidePath, listPath] = process.argv.slice(2);
if (!guidePath || !listPath) {
  console.log("usage: node validate_guide.js <guide.js> <list.json>");
  process.exit(2);
}
const src = fs.readFileSync(guidePath, "utf8");
const errors = [];
const warn = [];

const nonAscii = [...new Set([...src.matchAll(/[^\x00-\x7f]/g)].map(m => m[0]))];
if (nonAscii.length) errors.push(`non-ASCII characters: ${nonAscii.join(" ")}`);

// The repo is public: the guide must not name the user's account.
try {
  const acct = JSON.parse(fs.readFileSync(path.join(process.env.APPDATA, "steam-achievements", "account.json"), "utf8"));
  for (const v of [acct.steamid, acct.username])
    if (v && src.toLowerCase().includes(String(v).toLowerCase())) errors.push("guide contains the user's SteamID or username");
} catch { warn.push("account.json not readable; skipped the account-leak check"); }

const ctx = { window: {} };
vm.runInNewContext(src, ctx, { filename: guidePath });
const g = ctx.window.GUIDE;
if (!g) { console.log("FAIL: window.GUIDE not set"); process.exit(1); }

const list = JSON.parse(fs.readFileSync(listPath, "utf8"));
if (String(g.appid) !== String(list.appid)) errors.push(`appid ${g.appid} != ${list.appid}`);
for (const f of ["title", "subtitle", "credit", "categories", "achievements"])
  if (!g[f]) errors.push(`missing field: ${f}`);
if (g.titleAccent && !String(g.title).includes(g.titleAccent)) errors.push("titleAccent is not part of title");
if (g.utilities !== undefined && !Array.isArray(g.utilities)) errors.push("utilities is not an array");
for (const u of Array.isArray(g.utilities) ? g.utilities : []) {
  if (!u || !u.label || !u.href) { errors.push("utility needs label and href"); continue; }
  if (/^[a-z][a-z0-9+.-]*:/i.test(u.href) && !/^https:/i.test(u.href))
    errors.push(`utility ${u.label}: href must be relative or https`);
  else if (!/^https:/i.test(u.href) && !fs.existsSync(path.join(path.dirname(guidePath), u.href.split(/[?#]/)[0])))
    errors.push(`utility ${u.label}: ${u.href} does not exist`);
}

const byKey = Object.fromEntries(list.achievements.map(a => [a.api.toLowerCase(), a]));
const keys = Object.keys(g.achievements || {});
const missing = Object.keys(byKey).filter(k => !keys.includes(k));
const extra = keys.filter(k => !(k in byKey));
if (missing.length) errors.push(`missing from guide: ${missing.join(", ")}`);
if (extra.length) errors.push(`not on Steam: ${extra.join(", ")}`);

const cats = new Set((g.categories || []).map(c => c[0]));
const flags = new Set(Object.keys(g.flags || {}));
const perCat = {};
const noTipRemaining = [];
for (const [k, a] of Object.entries(g.achievements || {})) {
  if (!cats.has(a.cat)) errors.push(`${k}: unknown cat ${a.cat}`);
  perCat[a.cat] = (perCat[a.cat] || 0) + 1;
  if (a.flag && !flags.has(a.flag)) errors.push(`${k}: unknown flag ${a.flag}`);
  if (a.steps && !Array.isArray(a.steps)) errors.push(`${k}: steps is not an array`);
  if (a.tip && !(typeof a.tip === "string" || Array.isArray(a.tip))) errors.push(`${k}: tip must be a string or an array`);
  if (!a.tip && byKey[k] && !byKey[k].unlocked) noTipRemaining.push(k);
  // missable: a string naming the deadline, or false for "checked, not missable".
  if (a.missable !== undefined && a.missable !== false && !(typeof a.missable === "string" && a.missable.trim()))
    errors.push(`${k}: missable must be a non-empty string naming the deadline, or false`);
  // A tip that warns of a lockout but has no `missable` field is probably a missed mark.
  const tipText = [].concat(a.tip || []).join(" ");
  const risky = /point of no return|\bmissable\b|for good|permanent|locks? (you )?out|cannot (go|come) back|new (game|save)|reload|restart/i;
  const cleared = /(not|never|none (are|is)|nothing[^.]*) missable/i;
  if (a.missable === undefined && risky.test(tipText) && !cleared.test(tipText))
    warn.push(`${k}: tip mentions a lockout but has no missable field; set a deadline, or missable: false`);
}
if (noTipRemaining.length) errors.push(`remaining achievements without a tip: ${noTipRemaining.join(", ")}`);
// The missables audit is mandatory: the summary shows on the page and proves every entry was checked.
if (!(typeof g.missables === "string" && g.missables.trim()))
  errors.push("missing missables: a one-line summary of what is missable, or that nothing is");
for (const c of cats) if (!perCat[c]) warn.push(`empty category: ${c}`);
for (const [, f] of Object.entries(g.flags || {}))
  if (!["accent", "accent2"].includes(f.tone)) errors.push(`flag tone must be accent or accent2: ${f.label}`);
if (g.highlight && !flags.has(g.highlight.flag)) errors.push(`highlight flag ${g.highlight.flag} is not defined`);
// colors are optional (the template has defaults), but a new game should pick its own.
if (!g.colors) warn.push("no colors: the page uses the template defaults");
else for (const mode of ["light", "dark"])
  if (!g.colors[mode]?.accent || !g.colors[mode]?.accent2) errors.push(`colors.${mode} needs accent and accent2`);

const remaining = list.achievements.filter(a => !a.unlocked).length;
const checklists = Object.values(g.achievements || {}).filter(a => a.steps).length;
console.log(`${g.title}: ${keys.length}/${list.achievements.length} keys, ${remaining} remaining, ${checklists} checklists`);
console.log("categories:", (g.categories || []).map(c => `${c[1]} (${perCat[c[0]] || 0})`).join(", "));
console.log("flags:", [...flags].join(", ") || "none", "| highlight:", g.highlight?.flag || "default (rarest remaining)");
const missKeys = Object.entries(g.achievements || {}).filter(([, a]) => a.missable).map(([k]) => k);
console.log(`missables (${missKeys.length}):`, missKeys.join(", ") || "none");
warn.forEach(w => console.log("WARN", w));
errors.forEach(e => console.log("ERROR", e));
console.log(errors.length ? "FAIL" : "PASS");
process.exit(errors.length ? 1 : 0);
