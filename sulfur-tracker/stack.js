// Totals SULFUR stat modifiers the way the game stacks them, for the oils and
// gear pages. The game's CharacterStat.CalculateFinalValue sorts a stat's
// modifiers by type, then: flat values (type 100) add to the base, percent-add
// values (200) sum into one multiplier, clamped to 0.01x-10x, and each
// percent-mult value (300) multiplies on its own. The total is shown as the
// tooltip would show one modifier: a flat change, a percent change, or both.
window.SulfurStack = (() => {
  const num = v => { const r = Math.round(v * 100) / 100; return String(r === 0 ? 0 : r); };
  const sign = v => (v >= 0 ? "+" : "");

  // The total of one attribute's modifiers: flat sum, percent factor, and how
  // many modifiers went in.
  function total(list) {
    let flat = 0, add = 0, mult = 1, hasFlat = false, hasPct = false;
    for (const m of list) {
      if (m.t === 200) { add += m.v; hasPct = true; }
      else if (m.t === 300) { mult *= 1 + m.v; hasPct = true; }
      else { flat += m.v; hasFlat = true; }
    }
    const clamped = 1 + add < 0.01 || 1 + add > 10;
    const factor = Math.min(Math.max(1 + add, 0.01), 10) * mult;
    return { flat, factor, hasFlat, hasPct, clamped, n: list.length };
  }

  const flatText = (v, info) =>
    (info.factor ? "x" + num(v) : info.pct ? sign(v) + num(v * 100) + "%" : sign(v) + num(v) + (info.unit || "")) + (info.unitName || "");

  // mods: [{a: attribute key, v: value, t: modType}]; attrs: key -> label, dir,
  // and format flags. Returns one row per attribute, in first-seen order:
  // {a, text, kind, n, flat, factor, clamped}.
  function combine(mods, attrs) {
    const by = new Map();
    for (const m of mods) {
      if (!by.has(m.a)) by.set(m.a, []);
      by.get(m.a).push(m);
    }
    const rows = [];
    for (const [a, list] of by) {
      const info = attrs[a] || { label: a, dir: 0 };
      const s = total(list);
      const pct = s.factor - 1;
      let text, net;
      if (info.bool) {
        text = info.label; net = 1;
      } else {
        const flatNet = s.hasFlat ? Math.sign(Math.round(s.flat * 1e4)) : 0;
        const pctNet = s.hasPct ? Math.sign(Math.round(pct * 1e4)) : 0;
        net = !s.hasPct ? flatNet : !s.hasFlat ? pctNet : flatNet === pctNet || !pctNet ? flatNet : !flatNet ? pctNet : 0;
        if (info.inc) text = net > 0 ? info.inc : net < 0 ? info.dec : info.label + ": no change";
        else {
          const parts = [];
          if (s.hasFlat) parts.push(flatText(s.flat, info));
          if (s.hasPct) parts.push(sign(pct) + num(pct * 100) + "%");
          text = `${info.label}: ${parts.join(", then ")}`;
        }
      }
      const kind = !info.dir || !net ? "side" : net * info.dir > 0 ? "good" : "bad";
      rows.push({ a, text, kind, n: s.n, flat: s.flat, factor: s.factor, clamped: s.clamped });
    }
    return rows;
  }

  return { combine };
})();
