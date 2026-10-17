"""Build weapons-data.js for the SULFUR weapon table from sulfur.wiki.gg.

Each weapon page on the wiki opens with an Item Infobox that holds its stats
and sell value. This script reads every page in the weapon categories through
the MediaWiki API, adds icon URLs, and fills attachment slots and reload
time from sulfurbuild.com where the wiki leaves them out. The wiki wins
wherever both list a value. Neither source gives weapon quality: the wiki
lists no quality per weapon, and sulfurbuild marks every weapon "rare". It writes
window.SULFUR_WEAPONS for index.html. Rerun it after a game update.

    py -I build_weapons.py
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://sulfur.wiki.gg/api.php"
WIKI = "https://sulfur.wiki.gg/wiki/"
BUILD = "https://www.sulfurbuild.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
OUT = Path(__file__).with_name("weapons-data.js")

# Category on the wiki -> type label in the table, in display order.
TYPES = [
    ("Pistols", "Pistol"), ("Revolvers", "Revolver"), ("Submachine Guns", "SMG"),
    ("Assault Rifles", "Assault rifle"), ("Light Machine Guns", "LMG"),
    ("Shotguns", "Shotgun"), ("Rifles", "Rifle"), ("Sniper Rifles", "Sniper rifle"),
    ("Melee Weapons", "Melee"),
]
# Throwables (grenades, jars, knives) are left out on purpose.
# The wiki writes the same fire mode several ways.
MODES = {"Auto": "Automatic", "Full": "Automatic", "Semi": "Semi-Automatic", "Semi-automatic": "Semi-Automatic"}


def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def api(params):
    params = {**params, "format": "json", "formatversion": "2"}
    return json.loads(fetch(API + "?" + urllib.parse.urlencode(params)))


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
    return texts


def icons(names):
    urls = {}
    for batch in chunks(sorted(names)):
        r = api({"action": "query", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": "96",
                 "titles": "|".join("File:" + n + ".png" for n in batch)})
        norm = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
        for p in r["query"].get("pages", []):
            ii = p.get("imageinfo")
            if ii:
                title = norm.get(p["title"], p["title"])
                urls[title.split(":", 1)[1][:-4]] = ii[0].get("thumburl") or ii[0]["url"]
    return urls


def plain(v):
    """Wikitext value -> plain text: links to labels, entities decoded, tags dropped."""
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"<sup>.*?</sup>", "", v)
    v = re.sub(r"<br\s*/?>", "\n", v)
    v = re.sub(r"<[^>]+>", "", v)
    return html.unescape(v).replace("×", "x").strip()


def infobox(text):
    m = re.search(r"\{\{\s*Item[ _]Infobox(.*?)\n\}\}", text, re.S | re.I)
    if not m:
        return None
    box = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"\s*\|\s*(\w+)\s*=\s*(.*)", line)
        if kv and kv.group(2).strip():
            box[kv.group(1)] = kv.group(2).strip()
    return box


def num(v):
    try:
        f = float(plain(v).replace(",", ""))
        return int(f) if f.is_integer() else f
    except (ValueError, AttributeError):
        return None


def damage_total(text):
    """'40x8' -> 320, '40x8(x1-8)' -> 320, '>=600' -> 600, '???' -> None."""
    nums = re.findall(r"\d+(?:\.\d+)?", text.split("(")[0])
    if not nums:
        return None
    total = 1.0
    for n in nums:
        total *= float(n)
    return int(total) if total.is_integer() else round(total, 1)


def sulfurbuild():
    """Name -> {slots, reload, href} from sulfurbuild.com item pages."""
    listing = fetch(BUILD + "/weapons")
    links = {}
    for href, name in re.findall(r'<a class="flex items-start gap-3" href="(/items/[^"]+)">.*?<h3[^>]*>(.*?)</h3>',
                                 listing, re.S):
        links[html.unescape(name)] = href
    extra = {}
    for name, href in sorted(links.items()):
        page = fetch(BUILD + href)
        stats = dict((html.unescape(a), html.unescape(b)) for a, b in
                     re.findall(r"<dt[^>]*>(.*?)</dt><dd[^>]*>(.*?)</dd>", page))
        extra[name] = {
            "slots": num(stats.get("Slots", "")),
            "reload": num(stats.get("Reload", "").rstrip("s")),
            "href": BUILD + href,
        }
        time.sleep(0.3)
    return extra


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cls = {}
    for cat, label in TYPES:
        r = api({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat,
                 "cmlimit": "500", "cmnamespace": "0"})
        for m in r["query"]["categorymembers"]:
            cls.setdefault(m["title"], label)
    texts = page_texts(cls)
    imgs = icons(cls)
    extra = sulfurbuild()

    weapons, missing = [], []
    for name in sorted(cls, key=str.lower):
        box = infobox(texts.get(name, ""))
        if box is None:
            missing.append(name)
            continue
        dmg = plain(box.get("Damage") or box.get("MainDmg") or "")
        grid = re.findall(r"\d+", box.get("GridSize", ""))
        w = {
            "name": name, "type": cls[name], "url": WIKI + name.replace(" ", "_"),
            "img": imgs.get(name), "kind": box.get("kind", ""),
            "ammo": plain(box.get("Ammo", "")) or None,
            "mode": MODES.get(plain(box.get("Mode", "")), plain(box.get("Mode", ""))) or None,
            "dmg": dmg or None, "dmgN": damage_total(dmg) if dmg else None,
            "rpm": num(box.get("RPM", "")), "mag": num(box.get("Mag", "")),
            "spread": num(box.get("Spread", "")), "recoil": num(box.get("Recoil", "")),
            "dur": num(box.get("Durability", "")), "weight": num(box.get("Weight", "")),
            "sell": num(box.get("SellVal", "")),
            "grid": "x".join(grid) if len(grid) == 2 else None,
            "cells": int(grid[0]) * int(grid[1]) if len(grid) == 2 else None,
            "soldBy": [s for s in plain(box.get("SoldBy", "")).split("\n") if s] or None,
        }
        notes = []
        if "SecondaryDmg" in box:
            notes.append("Secondary " + plain(box["SecondaryDmg"]))
        for stance, word in (("M", "Main"), ("S", "Secondary")):
            if stance + "Parries" in box:
                count = box.get(stance + "ParryCount")
                notes.append(f"{word} parries {count + ' ' if count else ''}"
                             f"{plain(box[stance + 'Parries']).lower()}")
            if stance + "Stun" in box:
                notes.append(word + " stuns")
            if stance + "Bleed" in box:
                notes.append(word + " bleeds")
        w["notes"] = notes or None
        x = extra.get(name, {})
        w["slots"] = x.get("slots")
        w["reload"] = num(box.get("RldSpeed", "").rstrip("s")) or x.get("reload")
        if w["sell"] is None and name in extra:
            missing.append(name + " (no sell value)")
        weapons.append(w)

    data = {"source": WIKI + "Weapons", "extraSource": BUILD + "/weapons",
            "built": date.today().isoformat(), "types": [t for _, t in TYPES], "weapons": weapons}
    OUT.write_text(
        "// Generated by build_weapons.py from sulfur.wiki.gg (CC BY-SA) and sulfurbuild.com."
        " Do not edit by hand.\n"
        "window.SULFUR_WEAPONS = " + json.dumps(data, ensure_ascii=False, indent=0) + ";\n",
        encoding="utf-8")
    noextra = sorted(w["name"] for w in weapons if w["name"] not in extra)
    print(f"{len(weapons)} weapons -> {OUT.name}")
    print("no infobox or sell value:", ", ".join(missing) or "none")
    print("not on sulfurbuild:", ", ".join(noextra) or "none")
    print("no icon:", ", ".join(sorted(w["name"] for w in weapons if not w["img"])) or "none")


if __name__ == "__main__":
    main()
