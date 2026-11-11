"""Build recipes-data.js for the SULFUR recipe calculator from the installed game.

The game's RecipeDatabase lists every cooking recipe with exact ingredients:
one recipe per combination, so Mushroom Soup alone has over 150. This script
folds recipes that differ in one ingredient into a single recipe with a
"one of these" slot, which keeps every combination and adds none. It reads
item names, effects, sizes, and sell values the way the in-game tooltip
shows them, flags recipes whose ingredients do not fit a 3x3 stove, and
exports icons to icons/. Scroll recipes go to ../scrolls/ instead. It writes
window.SULFUR_RECIPES for index.html. Rerun it after a game update.

    py -m pip install UnityPy dnfile
    py -I build_recipes.py [path to the SULFUR install folder]
"""
import collections
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))  # -I leaves the script folder off the path
from game_files import Game, game_dir  # noqa: E402

OUT = HERE / "recipes-data.js"
ICONS = HERE / "icons"
# CraftingStation slots: the Wood Stove is 4x4; fire barrels, pots, and the
# steamer are 3x3. Learned recipes quick-cook from the backpack at any stove.
SMALL, BIG = (3, 3), (4, 4)
# RecipeData.Types. Several game classes name an enum Types, so spell it out.
# The cooking stations take generic and cooking recipes; the Scholar takes
# enchantment recipes.
RECIPE_TYPES = {0: "generic", 1: "cooking", 2: "enchantment"}


def fits(shapes, size):
    """True when the item rectangles pack into the grid; items may rotate."""
    w, h = size
    if sum(a * b for a, b in shapes) > w * h:
        return False
    grid = [[False] * w for _ in range(h)]
    shapes = sorted(shapes, key=lambda s: -s[0] * s[1])

    def place(i):
        if i == len(shapes):
            return True
        a, b = shapes[i]
        for sw, sh in {(a, b), (b, a)}:
            for y in range(h - sh + 1):
                for x in range(w - sw + 1):
                    if all(not grid[y + dy][x + dx] for dy in range(sh) for dx in range(sw)):
                        for dy in range(sh):
                            for dx in range(sw):
                                grid[y + dy][x + dx] = True
                        if place(i + 1):
                            return True
                        for dy in range(sh):
                            for dx in range(sw):
                                grid[y + dy][x + dx] = False
        return False

    return place(0)


def fold(recipes):
    """Merge recipes that match except for which item fills one slot.

    A recipe is (output, quantity, slots); a slot is (items, count). Two
    recipes with the same other slots and the same count in the differing
    slot merge into one slot that takes any of their items. Merging only
    recipes that agree everywhere else keeps the set of combinations exact.
    """
    key = lambda slots: tuple(sorted((tuple(sorted(a)), q) for a, q in slots))
    while True:
        index = collections.defaultdict(list)
        for n, (out, qty, slots) in enumerate(recipes):
            for i, (_, q) in enumerate(slots):
                index[(out, qty, key(slots[:i] + slots[i + 1:]), q)].append((n, i))
        used, merged = set(), []
        for _, hits in sorted(index.items(), key=lambda kv: -len(kv[1])):
            hits = [(n, i) for n, i in hits if n not in used]
            if len(hits) < 2:
                continue
            n0, i0 = hits[0]
            out, qty, slots = recipes[n0]
            slots = list(slots)
            slots[i0] = (frozenset().union(*(recipes[n][2][i][0] for n, i in hits)), slots[i0][1])
            merged.append((out, qty, tuple(slots)))
            used.update(n for n, _ in hits)
        if not merged:
            return recipes
        recipes = [r for n, r in enumerate(recipes) if n not in used] + merged


def group_label(members):
    """'Any flesh (6)' when every name ends in the same word, else the names."""
    last = {m.split()[-1].lower() for m in members}
    if len(last) == 1 and len(members) > 2:
        return f"Any {last.pop()} ({len(members)})"
    if len(members) <= 3:
        return " or ".join(members)
    return f"Any of {len(members)}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    game = Game(game_dir())
    E = game.enums
    rdb = next(o.read_typetree() for o in game.scripts("RecipeDatabase"))["recipes"]
    rtype = RECIPE_TYPES

    raw, skipped = [], collections.Counter()
    for r in rdb:
        kind = rtype.get(r["type"], "generic")
        out = r["createsItem"]["value"]
        if kind == "enchantment" or not out or out not in game.items:
            continue
        if not r["canBeCrafted"]:
            skipped[game.name(game.items[out])] += 1
            continue
        need = collections.Counter()
        for x in r["itemsNeeded"]:
            if x["item"]["value"] in game.items:
                need[x["item"]["value"]] += x["quantity"]
        if need:
            raw.append((out, r["quantityCreated"], tuple(sorted((frozenset([k]), q) for k, q in need.items()))))
    raw = list(dict.fromkeys(raw))
    folded = fold(raw)

    ICONS.mkdir(exist_ok=True)
    ids = {out for out, _, _ in folded} | {i for _, _, s in folded for items, _ in s for i in items}
    names = {i: game.name(game.items[i]) for i in ids}
    items = {}
    for i in sorted(ids, key=lambda i: names[i].lower()):
        t = game.items[i]
        effects, heal = game.consume_effects(t)
        use = E["UseType"].get(t["useType"])
        kind = ("throwable" if t["_class"] == "WeaponSO" and E["WeaponTypes"].get(t.get("weaponType")) == "Throwable"
                else "consumable" if use == "Consumable" else "scroll" if use == "Enchantment" else "misc")
        info = {"grid": game.grid(t), "kind": kind, "sell": game.sell(t), "quality": game.quality(t)}
        if effects:
            info["effects"] = effects
        if heal:
            info["heal"] = round(heal, 1) if heal % 1 else int(heal)
        icon = game.save_icon(i, ICONS)
        if icon:
            info["img"] = "icons/" + icon
        items[names[i]] = info

    groups, group_ids, recipes = {}, {}, []
    for out, qty, slots in sorted(folded, key=lambda r: (names[r[0]].lower(), -r[1])):
        ins, shapes = [], []
        for members, q in sorted(slots, key=lambda s: (len(s[0]) > 1, sorted(names[m] for m in s[0]))):
            ms = sorted((names[m] for m in members), key=str.lower)
            sizes = [tuple(map(int, items[m]["grid"].split("x"))) for m in ms]
            # The largest member decides whether the slot fits.
            shapes += [max(sizes, key=lambda s: s[0] * s[1])] * q
            if len(ms) == 1:
                ins.append({"n": ms[0], "q": q})
                continue
            gid = group_ids.setdefault(tuple(ms), f"g{len(group_ids) + 1}")
            groups[gid] = {"members": ms, "label": group_label(ms), "img": items[ms[0]].get("img")}
            ing = {"g": gid, "q": q, "opts": ms, "label": groups[gid]["label"]}
            if q > 1:
                ing["same"] = True  # the game lists mixed fillings as their own recipes
            ins.append(ing)
        row = {"out": names[out], "qty": qty, "ins": ins}
        if not fits(shapes, BIG):
            row["flag"], row["note"] = "quickcook", "The ingredients do not fit even a 4x4 stove: learn it another way, then quick-cook it"
        elif not fits(shapes, SMALL):
            row["flag"], row["note"] = "big", "The ingredients fit only a 4x4 Wood Stove; once learned, quick-cook it at any stove"
        recipes.append(row)

    data = {"source": "SULFUR game files", "version": game.version, "built": date.today().isoformat(),
            "items": items, "groups": groups, "recipes": recipes}
    OUT.write_text(
        "// Generated by build_recipes.py from the installed SULFUR game files. Do not edit by hand.\n"
        "window.SULFUR_RECIPES = " + json.dumps(data, ensure_ascii=False, indent=0, sort_keys=True) + ";\n",
        encoding="utf-8")
    print(f"{len(raw)} cooking recipes folded to {len(recipes)} for {len({r['out'] for r in recipes})} outputs, "
          f"{len(items)} items, {len(groups)} groups -> {OUT.name}")
    print("skipped as not craftable:", ", ".join(f"{n} ({k})" for n, k in skipped.items()) or "none")
    print("flags:", dict(collections.Counter(r.get("flag") for r in recipes)))
    print("no icon:", ", ".join(n for n, i in items.items() if "img" not in i) or "none")


if __name__ == "__main__":
    main()
