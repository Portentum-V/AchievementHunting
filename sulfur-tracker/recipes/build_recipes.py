"""Build recipes-data.js for the SULFUR recipe calculator from sulfur.wiki.gg.

Every page that uses Template:Recipe_row holds its recipes as rows of
ingredient slots (i1..i8, with iNQty) and a resultQty. This script reads those
rows through the MediaWiki API, adds each item's grid size and icon URL, and
writes window.SULFUR_RECIPES for index.html. Rerun it after a game update.

    py -I build_recipes.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://sulfur.wiki.gg/api.php"
WIKI = "https://sulfur.wiki.gg/wiki/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
OUT = Path(__file__).with_name("recipes-data.js")

# The wiki has a few misspelled parameter names; read them as the real ones.
KEY_FIXES = {"Qry": "Qty"}
RESULT_KEY_FIXES = {"reaultQty": "resultQty"}


def api(params):
    params = {**params, "format": "json", "formatversion": "2"}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def chunks(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def page_texts(titles):
    texts = {}
    for batch in chunks(sorted(titles)):
        r = api({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "titles": "|".join(batch), "redirects": "1"})
        for p in r["query"].get("pages", []):
            if "revisions" in p:
                texts[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        for rd in r["query"].get("redirects", []):
            if rd["to"] in texts:
                texts[rd["from"]] = texts[rd["to"]]
    return texts


def templates(text, name):
    """Yield the body of each {{name ...}} call, with nested braces kept."""
    pat = re.compile(r"\{\{\s*" + name.replace(" ", r"[ _]") + r"\s*(?=[|}\n])", re.I)
    for m in pat.finditer(text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text.startswith("{{", i):
                depth, i = depth + 1, i + 2
            elif text.startswith("}}", i):
                depth, i = depth - 1, i + 2
            else:
                i += 1
        yield m.start(), text[m.end():i - 2]


def params(body):
    """Split a template body on top-level pipes into a dict."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "[["):
            depth, cur, i = depth + 1, cur + two, i + 2
            continue
        if two in ("}}", "]]"):
            depth, cur, i = max(0, depth - 1), cur + two, i + 2
            continue
        if body[i] == "|" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += body[i]
        i += 1
    parts.append(cur)
    out = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def plain(s):
    """Strip wiki markup down to readable text."""
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<br\s*/?>", " / ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&times;", "x").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def note_kind(note):
    low = note.lower()
    if "cannot be cooked manually" in low or "quick-cook" in low:
        return "quickcook"
    if "4x4" in low and "only get" in low:
        return "cap3"  # a smaller stove still cooks it, but yields at most 3
    if "4x4" in low:
        return "big"  # the ingredients fit only on a 4x4 stove
    return "note"


def group_rules(ing, members, items):
    """Turn an "Any ..." label into the members allowed and how to pick them.

    opts:  the members that may fill the slot.
    same:  every unit in the slot is the same member ("Any same skin").
    uniq:  every unit is a different member ("Three Different Mushrooms").
    other: the members differ from the recipe's other ingredients ("Any other nut").
    """
    label = ing.get("label", "").lower()
    opts = list(members)
    named = [m for m in members if m.lower() in label]
    if named and "except" not in label and "any" not in label and "all" not in label:
        opts = named
    ex = re.search(r"except(.*)$", label)
    if ex:
        clause = ex.group(1)
        opts = [m for m in opts if m.lower() not in clause and m.split()[0].lower() not in clause]
    if "1x1" in label:
        opts = [m for m in opts if items.get(m, {}).get("grid") == "1x1"]
    ing["opts"] = opts
    if "same" in label:
        ing["same"] = True
    if "different" in label or "types" in label:
        ing["uniq"] = True
    if "other" in label:
        ing["other"] = True


def parse_recipes(title, text):
    start = text.find("== Recipes ==")
    if start < 0:
        start = 0
    end = re.search(r"^==[^=].*==\s*$", text[start + 13:], re.M)
    section_text = text[start:start + 13 + end.start()] if end else text[start:]
    # Markers that apply to the rows after them: subheadings, note rows, table edges.
    marks = []
    for m in re.finditer(r"^===+\s*(.+?)\s*===+\s*$", section_text, re.M):
        marks.append((m.start(), "heading", plain(m.group(1))))
    for m in re.finditer(r"colspan=\d+[^|\n]*\|([^\n]+)", section_text):
        marks.append((m.start(), "note", plain(m.group(1)).strip("⚠ ").strip()))
    for m in re.finditer(r"^\{\|", section_text, re.M):
        marks.append((m.start(), "table", ""))
    marks.sort()
    rows = []
    for pos, body in templates(section_text, "Recipe row"):
        heading, note = "", ""
        for mpos, kind, val in marks:
            if mpos > pos:
                break
            if kind == "heading":
                heading, note = val, ""
            elif kind == "table":
                note = ""
            else:
                note = val
        p = {RESULT_KEY_FIXES.get(k, k): v for k, v in params(body).items()}
        ins = []
        for n in range(1, 9):
            name = p.get(f"i{n}", "").strip()
            label = plain(p.get(f"i{n}Label", ""))
            if name == "(blank)" or not (name or label):
                continue
            qty = p.get(f"i{n}Qty") or p.get(f"i{n}Qry") or "1"
            ing = {"q": int(re.sub(r"\D", "", qty) or 1)}
            name = plain(name)
            if name.startswith(":Category:") or name.startswith("Category:"):
                ing["g"] = name.split("Category:", 1)[1]
            elif not name:
                # A label with no item ("Any Seasoning"): a group with no category link.
                ing["g"] = re.sub(r"^any\s+", "", label, flags=re.I).strip()
                ing["adhoc"] = True
            else:
                ing["n"] = name
            if label:
                ing["label"] = label
            if p.get(f"i{n}Filename"):
                ing["file"] = p[f"i{n}Filename"].strip()
            ins.append(ing)
        if not ins:
            continue
        ins.reverse()  # the wiki lists i1 last; show it first
        row = {"out": plain(p.get("result") or title),
               "qty": int(re.sub(r"\D", "", p.get("resultQty", "1")) or 1),
               "ins": ins}
        if heading:
            row["section"] = heading
        if note:
            row["note"] = note
            row["flag"] = note_kind(note)
        rows.append(row)
    return rows


def infobox(text):
    for _, body in templates(text, "Item Infobox"):
        return params(body)
    for _, body in templates(text, "Item_Infobox"):
        return params(body)
    return {}


def item_info(text):
    box = infobox(text)
    info = {}
    grid = plain(box.get("GridSize", "")).replace("×", "x").replace(" ", "")
    if grid:
        info["grid"] = grid
    if box.get("kind"):
        info["kind"] = plain(box["kind"]).lower()
    sub = plain(box.get("SubType", ""))
    if sub:
        info["sub"] = sub
    # Effects: the bold "Gives ...", "Removes ..." lines under Description, one per
    # effect. Bottled Water lists three: health, Removes Burning, Removes Poisoned.
    desc = re.search(r"==\s*Description\s*==(.*?)(?=\n==[^=]|\Z)", text, re.S)
    effects = []
    for line in (desc.group(1) if desc else "").splitlines():
        if "'''" not in line:
            continue  # italic flavor text
        line = plain(line).lstrip("*: ").strip()
        if re.match(r"(Gives|Removes|Restores)\b", line):
            effects.append(line.rstrip("."))
    if not effects and box.get("Heal"):
        effects.append("Gives " + plain(box["Heal"]))
    if effects:
        info["effects"] = effects
    heal = re.search(r"(\d+)\s*(?:health|hp)\b", " ".join(effects) or plain(box.get("Heal", "")), re.I)
    if heal:
        info["heal"] = int(heal.group(1))
    sell = re.sub(r"[^\d]", "", box.get("SellVal", ""))
    if sell:
        info["sell"] = int(sell)
    if box.get("image"):
        info["file"] = box["image"].strip()
    return info


def category_members(cat):
    r = api({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat,
             "cmlimit": "500", "cmnamespace": "0"})
    return sorted(m["title"] for m in r["query"]["categorymembers"])


def image_urls(files):
    urls = {}
    for batch in chunks(sorted(files)):
        r = api({"action": "query", "prop": "imageinfo", "iiprop": "url",
                 "iiurlwidth": "64", "titles": "|".join("File:" + f for f in batch)})
        norm = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
        for p in r["query"].get("pages", []):
            ii = p.get("imageinfo")
            if ii:
                title = norm.get(p["title"], p["title"])
                urls[title.split(":", 1)[1]] = ii[0].get("thumburl") or ii[0]["url"]
    return urls


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    r = api({"action": "query", "list": "embeddedin", "eititle": "Template:Recipe_row",
             "eilimit": "500", "einamespace": "0"})
    titles = [p["title"] for p in r["query"]["embeddedin"]]
    texts = page_texts(titles)
    recipes = []
    for t in sorted(texts):
        recipes.extend(parse_recipes(t, texts[t]))

    groups = sorted({i["g"] for r in recipes for i in r["ins"] if "g" in i})
    group_members = {}
    for g in groups:
        members = category_members(g) or category_members(g + "s")
        if not members:
            # No category: the rows' icons name the members, one per row.
            members = sorted({re.sub(r"\.png$", "", i["file"]) for r in recipes for i in r["ins"]
                              if i.get("g") == g and i.get("file")})
            print(f"Group '{g}' has no wiki category; using its row icons: {', '.join(members)}")
        group_members[g] = members
    for r in recipes:
        for i in r["ins"]:
            i.pop("adhoc", None)

    names = {r["out"] for r in recipes} | {i["n"] for r in recipes for i in r["ins"] if "n" in i}
    names |= {m for ms in group_members.values() for m in ms}
    missing = names - set(texts)
    texts.update(page_texts(missing))
    # Pages sometimes write a name in the wrong case ("sugar"); use the page title.
    canon = {t.lower(): t for t in texts}
    for r in recipes:
        r["out"] = canon.get(r["out"].lower(), r["out"])
        for i in r["ins"]:
            if "n" in i:
                i["n"] = canon.get(i["n"].lower(), i["n"])
    names = {canon.get(n.lower(), n) for n in names}
    items = {n: item_info(texts[n]) if n in texts else {} for n in sorted(names)}
    for n, info in items.items():
        if n not in texts:
            info["nopage"] = True
    for r in recipes:
        for i in r["ins"]:
            if "g" in i:
                group_rules(i, group_members[i["g"]], items)

    files = {}
    for n, info in items.items():
        files[n] = info.pop("file", n + ".png")
    for r in recipes:
        for i in r["ins"]:
            if "g" in i and "file" in i:
                f = i.pop("file")
                files["@" + i["g"]] = f if f.endswith(".png") else f + ".png"
            i.pop("file", None)
    urls = image_urls(set(files.values()))
    for n, f in files.items():
        if f in urls:
            if n.startswith("@"):
                continue
            items[n]["img"] = urls[f]
    group_out = {}
    for g in groups:
        f = files.get("@" + g)
        group_out[g] = {"members": group_members[g]}
        if f and f in urls:
            group_out[g]["img"] = urls[f]

    data = {
        "source": WIKI + "Consumables",
        "built": time.strftime("%Y-%m-%d"),
        "items": items,
        "groups": group_out,
        "recipes": recipes,
    }
    OUT.write_text(
        "// Generated by build_recipes.py from sulfur.wiki.gg (CC BY-SA). Do not edit by hand.\n"
        "window.SULFUR_RECIPES = " + json.dumps(data, ensure_ascii=False, indent=0, sort_keys=True) + ";\n",
        encoding="utf-8")
    nopage = sorted(n for n, i in items.items() if i.get("nopage"))
    print(f"{len(recipes)} recipes for {len({r['out'] for r in recipes})} outputs, "
          f"{len(items)} items, {len(groups)} groups -> {OUT.name}")
    if nopage:
        print("No wiki page for: " + ", ".join(nopage))


if __name__ == "__main__":
    main()
