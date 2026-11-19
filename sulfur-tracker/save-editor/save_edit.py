"""Edit a SULFUR save: amulet charge, ammo, and the items in the backpack and stashes.

A save slot is %USERPROFILE%\\AppData\\LocalLow\\Perfect Random\\Sulfur\\
Sulfur_SaveSlot_<n>.sss: gzip around the JSON that Unity's JsonUtility writes,
with no checksum. Every command that changes a save is a dry run until you
add --apply. Before it writes, the script copies the save to backups/ and
refuses to run while the game is open: the game holds the save in memory
during play and overwrites the file each time it saves. It reads the file
only when you pick a slot, so at the main menu an edit is safe; add
--game-open there to skip the check.

    py -m pip install UnityPy dnfile          # once, for item names
    py -I save_edit.py slots
    py -I save_edit.py -s 3 show
    py -I save_edit.py -s 3 amulet 5 --apply
    py -I save_edit.py -s 3 ammo 9mm 900 --apply             # carried
    py -I save_edit.py -s 3 ammo all max --apply             # fill to the backpack caps
    py -I save_edit.py -s 3 ammo all 5000 --stash --apply    # stored at the church
    py -I save_edit.py -s 3 stamps +20 --apply                # or a number: stamps 50
    py -I save_edit.py -s 3 grid backpack                   # draw the grid
    py -I save_edit.py -s 3 items backpack                  # list it, numbered
    py -I save_edit.py find milk
    py -I save_edit.py find --types                          # the item types
    py -I save_edit.py find -t attachment                     # every attachment
    py -I save_edit.py find scope -t attachment
    py -I save_edit.py -s 3 add stash "Low Fat Milk" --count 2 --apply
    py -I save_edit.py -s 3 remove backpack 4 7 --apply
    py -I save_edit.py -s 3 move backpack 4 wardrobe --apply
    py -I save_edit.py -s 3 convert backpack "Health Potion" --type food --apply
    py -I save_edit.py -s 3 convert all "Health Potion" --type food --apply   # one per cell
    py -I save_edit.py -s 3 restock --apply      # food to potions, repair, ammo, 3 kits, fill gaps
    py -I save_edit.py -s 3 repair all --apply                   # every grid
    py -I save_edit.py -s 3 repair backpack 0 4 --apply
    py -I save_edit.py -s 3 endless escape --apply               # next level-up deals only Escape
    py -I save_edit.py -s 3 leave-endless --apply                # end a run, start at the church
    py -I save_edit.py -s 3 revert                              # list restore points
    py -I save_edit.py -s 3 revert 2 --apply                    # put point 2 back
    py -I save_edit.py -s 1 loadout save main-kit               # what slot 1 has equipped
    py -I save_edit.py -s 3 loadout apply main-kit --apply      # equip copies in slot 3
    py -I save_edit.py -s 3 loadout save fridge-food fridge     # a container's contents
    py -I save_edit.py -s 3 loadout apply fridge-food --replace --to delete --apply
    py -I save_edit.py loadout list

The first command that needs item names reads them from the installed game
and caches them in item-cache.json; the cache rebuilds after a game update.
"""
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
SAVES = Path(os.environ["USERPROFILE"]) / "AppData" / "LocalLow" / "Perfect Random" / "Sulfur"
BACKUPS = HERE / "backups"
CACHE = HERE / "item-cache.json"
BOM = b"\xef\xbb\xbf"

# WorldResources ids, with the game's caps (WorldResource assets in the
# startup bundle). The game splits carried ammo above the backpack cap off
# when it loads, and picks the amulet's art by charge, so charge must stay 0-5.
AMMO = {  # alias: (id, name, backpack cap)
    "9mm": (1, "9mm", 2500),
    "12ga": (2, "12 gauge", 700),
    "50bmg": (3, ".50 BMG", 700),
    "556": (4, "5.56", 2000),
    "762": (5, "7.62", 1000),
    "energy": (6, "Energy cell", 1200),
}
AMULET, CHURCH_COLLECTION, SULF, STAMP = 7, 8, 9, 10
AMULET_MAX = 5
STASH_MAX = 999999

# Item grids. The backpack is the non-equipped part of INVENTORY (InventoryUI
# bagSpaceSize); each church stash saves under "Stash" or "Stash_<id>" with
# the size its PlayerStash component sets.
GRIDS = {
    "backpack": (None, 7, 9),
    "stash": ("Stash", 12, 14),
    "suitcase": ("Stash_Suitcase", 10, 6),
    "toilet": ("Stash_Toilet", 2, 14),
    "sideboard": ("Stash_Sideboard", 13, 8),
    "snakebasket": ("Stash_SnakeBasket", 8, 12),
    "safe": ("Stash_Safe", 10, 10),
    "wardrobe": ("Stash_Wardrobe", 13, 14),
    "fridge": ("Stash_Fridge", 8, 14),
    "coffin": ("Stash_Coffin", 10, 14),
    "guncabinet": ("Stash_GunCabinet", 9, 13),
    "weaponrack0": ("Stash_WeaponRack0", 14, 7),
    "weaponrack1": ("Stash_WeaponRack1", 14, 7),
    "weaponrack2": ("Stash_WeaponRack2", 14, 7),
}
INVENTORY_SLOTS = ["Head", "Torso", "LeftFoot", "RightFoot", "Weapon0", "Weapon1", "Gadget0", "Gadget1",
                   "Gadget2", "None", "BasicMelee", "Amulet", "Passive0", "Passive1", "Passive2", "Passive3"]
DURABILITY, MAX_DURABILITY, EXPERIENCE = 11, 21, 13  # ItemAttributes ids
NO_DURABILITY_SLOTS = {"Amulet", "BasicMelee", "Gadget", "PassiveEnhancements"}
# The SlotType an equipment slot takes (EquipmentManager.GetFreeSlotOfType).
# Gadget slots also take any consumable, as PaperdollSlot allows.
SLOT_TYPE = {"Head": "Head", "Torso": "Torso", "LeftFoot": "Feet", "RightFoot": "Feet",
             "Weapon0": "Weapon", "Weapon1": "Weapon", "Gadget0": "Gadget", "Gadget1": "Gadget",
             "Gadget2": "Gadget", "BasicMelee": "BasicMelee", "Amulet": "Amulet",
             "Passive0": "PassiveEnhancements", "Passive1": "PassiveEnhancements",
             "Passive2": "PassiveEnhancements", "Passive3": "PassiveEnhancements"}
LOADOUTS = HERE / "loadouts"


# ---------- save files ----------

def slot_path(slot):
    return SAVES / f"Sulfur_SaveSlot_{slot}.sss"


def load(slot):
    path = slot_path(slot)
    if not path.exists():
        sys.exit(f"No save in slot {slot} ({path.name}).")
    raw = gzip.decompress(path.read_bytes())
    return json.loads(raw.decode("utf-8-sig")), raw.startswith(BOM)


def game_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Sulfur.exe", "/NH"],
                         capture_output=True, text=True).stdout
    return "sulfur.exe" in out.lower()


def save(a, data, bom):
    slot = a.slot
    if not a.apply:
        print("\nDry run: nothing written. Add --apply to save the change.")
        return
    if game_running():
        if not a.game_open:
            sys.exit("SULFUR is running. Quit to the main menu, then add --game-open, or quit the game.\n"
                     "Mid-run, the game overwrites the slot at its next save and the edit is lost.")
        print("SULFUR is running: writing anyway (--game-open). Pick the slot from the menu to load the edit.")
    path = slot_path(slot)
    BACKUPS.mkdir(exist_ok=True)
    backup = BACKUPS / f"{path.stem}-{datetime.now():%Y-%m-%d_%H-%M-%S}.sss"
    shutil.copy2(path, backup)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    tmp = path.with_suffix(".sss.tmp")
    tmp.write_bytes(gzip.compress((BOM if bom else b"") + text.encode("utf-8")))
    load_check = json.loads(gzip.decompress(tmp.read_bytes()).decode("utf-8-sig"))
    assert load_check == data, "the written save does not read back the same"
    os.replace(tmp, path)
    print(f"\nSaved slot {slot}. The previous save is in backups/{backup.name}.")


# ---------- item names ----------

CACHE_FORMAT = 4  # bump when items_db adds a field, so old caches rebuild

# Item types for find --type, from the game's own fields: the item class,
# UseType, SlotType, the Organ tag, and whether a recipe takes the item.
TYPES = {
    "weapon": "guns and two-handed melee weapons",
    "melee": "the basic melee slot: Bo, Katana, and the like",
    "throwable": "grenades, mines, throwing knives",
    "gadget": "gadget-slot tools such as the Fishing Rod",
    "armor": "head, torso, and feet",
    "trinket": "passive enhancements such as the Fancy Watch",
    "attachment": "weapon attachments",
    "scroll": "elemental scrolls",
    "oil": "weapon oils",
    "food": "food, drink, and medicine",
    "recipe": "recipe books that teach a dish",
    "organ": "organs and flesh from enemies",
    "material": "other cooking and crafting ingredients",
    "loot": "other loot, mostly to sell",
    "tool": "repair kits and chamber chisels",
    "key": "keys",
    "furniture": "church furniture and stations",
    "ammo": "ammo pickups",
    "currency": "money pickups",
}
TYPE_GROUPS = {"crafting": {"organ", "material"}, "gear": {"weapon", "melee", "armor", "trinket", "gadget"}}

# A 256-color terminal color per type. Related types share a hue family:
# reds and orange for weapons, blues for gear, greens for food.
TYPE_COLORS = {
    "weapon": 196, "melee": 203, "throwable": 208,
    "armor": 33, "gadget": 44, "attachment": 111, "trinket": 177,
    "scroll": 129, "oil": 220,
    "food": 82, "recipe": 151, "organ": 205, "material": 137,
    "loot": 180, "tool": 109, "key": 231, "furniture": 101, "ammo": 245, "currency": 226,
}
COLOR = False  # main() turns it on for a terminal that shows color


def enable_color(off):
    """Turn color on when stdout is a terminal, unless --no-color or NO_COLOR says not to."""
    global COLOR
    if off or os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return
    if os.name == "nt":  # the Windows console needs virtual terminal mode for color codes
        import ctypes
        k = ctypes.windll.kernel32
        h, mode = k.GetStdHandle(-11), ctypes.c_uint32()
        if not k.GetConsoleMode(h, ctypes.byref(mode)) or not k.SetConsoleMode(h, mode.value | 4):
            return
    COLOR = True


def paint(text, kind):
    """text in the color of item type kind, when color is on."""
    code = TYPE_COLORS.get(kind)
    return f"\x1b[38;5;{code}m{text}\x1b[0m" if COLOR and code else text


def shown(db, rec, width=None):
    """An item's name for display: cut and padded to width, then colored by type."""
    name = item_name(db, rec)
    if width:
        name = f"{name[:width]:<{width}}"
    v = db.get(rec["id"]["value"])
    return paint(name, v and v["type"])


def type_key(db, recs):
    """One line naming the types present, each in its color."""
    kinds = {db[r["id"]["value"]]["type"] for r in recs if r["id"]["value"] in db}
    return "  ".join(paint(t, t) for t in TYPES if t in kinds)


def item_type(t, E, ingredients, enchants):
    """One of TYPES for an item definition."""
    cls, use = t["_class"], E["UseType"].get(t.get("useType"))
    slot = E["SlotType"].get(t.get("slotType"))
    if cls in ("AmmoSO", "CurrencySO"):
        return "ammo" if cls == "AmmoSO" else "currency"
    if cls == "WeaponSO":
        return {"Gadget": "throwable", "BasicMelee": "melee"}.get(slot, "weapon")
    if use == "Equippable":
        return {"Gadget": "gadget", "PassiveEnhancements": "trinket"}.get(slot, "armor")
    if use == "Enchantment":
        ench = enchants.get(t["appliesEnchantment"]["value"]) or {}
        return "scroll" if ench.get("IsElemental") else "oil"
    if use == "Consumable":
        return "recipe" if t.get("recipesTaughtOnConsume") else "food"
    if use == "Attachment":
        return "attachment"
    if use in ("ItemRepair", "ItemConsumable"):
        return "tool"
    if use == "Key":
        return "key"
    if use == "Storage":
        return "furniture"
    if t.get("itemTags", 0) & next(b for b, v in E["ItemTag"].items() if v == "Organ"):
        return "organ"
    return "material" if t["id"]["value"] in ingredients else "loot"


def items_db():
    """Item id -> name, type, size, and durability, cached from the installed game."""
    sys.path.insert(0, str(HERE.parent))  # -I leaves the script folder off the path
    from game_files import Game, game_dir, game_version  # noqa: E402
    root = game_dir([])
    version = game_version(root / "Sulfur_Data")
    if CACHE.exists():
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        if cached.get("version") == version and cached.get("format") == CACHE_FORMAT:
            return {int(k): v for k, v in cached["items"].items()}
    print("Reading item names from the game files (once per game version)...", file=sys.stderr)
    game = Game(root)
    E = game.enums
    defs = dict(game.items)
    for cls in ("AmuletDefinition", "CurrencySO", "AmmoSO"):
        for o in game.scripts(cls):
            t = o.read_typetree()
            t["_class"] = cls
            defs[t["id"]["value"]] = t
    rdb = next(o.read_typetree() for o in game.scripts("RecipeDatabase"))["recipes"]
    ingredients = {x["item"]["value"] for r in rdb if r["canBeCrafted"] for x in r["itemsNeeded"]}
    db = {}
    for i, t in defs.items():
        s = t["inventorySize"]
        slot = E["SlotType"].get(t.get("slotType"))
        db[i] = {
            "name": game.name(t), "key": t["m_Name"], "w": s["x"], "h": s["y"],
            "type": item_type(t, E, ingredients, game.enchants),
            "slot": slot, "use": E["UseType"].get(t.get("useType")),
            "maxDurability": t.get("maxDurability", 1000.0),
            "hasDurability": E["UseType"].get(t.get("useType")) == "Equippable" and slot not in NO_DURABILITY_SLOTS,
            "addable": not t.get("deprecated") and not t.get("excludeFromDatabase"),
        }
    CACHE.write_text(json.dumps({"version": version, "format": CACHE_FORMAT, "items": db},
                                ensure_ascii=False, indent=0), encoding="utf-8")
    return db


def find_items(db, query, addable=False, types=None):
    """Items whose name or id matches; an exact name or id wins outright.

    types limits the search to a set of TYPES; an empty query then lists
    every item of those types.
    """
    q = (query or "").strip().lower()
    pool = {i: v for i, v in db.items() if (v["addable"] or not addable) and (not types or v.get("type") in types)}
    if not q:
        return sorted(pool, key=lambda i: pool[i]["name"].lower())
    if q.isdigit() and int(q) in pool:
        return [int(q)]
    exact = [i for i, v in pool.items() if q in (v["name"].lower(), v["key"].lower())]
    if exact:
        return exact
    return sorted((i for i, v in pool.items() if q in v["name"].lower() or q in v["key"].lower()),
                  key=lambda i: pool[i]["name"].lower())


def item_name(db, rec):
    v = db.get(rec["id"]["value"])
    return v["name"] if v else f"item {rec['id']['value']}"


# ---------- resources ----------

def entries(data, key):
    return data[key].setdefault("resourceEntries", [])


def get_res(data, key, rid):
    return next((e["amount"] for e in entries(data, key) if e["id"] == rid), 0)


def set_res(data, key, rid, amount):
    es = entries(data, key)
    for e in es:
        if e["id"] == rid:
            e["amount"] = amount
            return
    es.append({"id": rid, "amount": amount})
    es.sort(key=lambda e: e["id"])


# ---------- grids ----------

def grid_items(data, grid):
    """The list that holds a grid's items; the backpack shares INVENTORY with equipped items."""
    key = GRIDS[grid][0]
    if key is None:
        return data["INVENTORY"]
    stash = data["STASH"]
    if key not in stash["_keys"]:
        stash["_keys"].append(key)
        stash["_values"].append({"list": []})
    return stash["_values"][stash["_keys"].index(key)]["list"]


def shown_grids(data):
    """The backpack and every stash the save has."""
    return [g for g, (key, _, _) in GRIDS.items() if key is None or key in data["STASH"]["_keys"]]


def on_grid(rec):
    return not rec["equipped"]


def free_spot(items, w, h, gw, gh):
    """The first free (x, y, rotated) for a w x h item, or None.

    The game counts rows from the bottom: y = 0 is the bottom row, and an
    item covers rows y to y + height - 1 upward. The search goes the way the
    grid reads on screen: top row first, left to right.
    """
    used = set()
    for r in items:
        if on_grid(r):
            x, y = r["position"]
            used.update((x + dx, y + dy) for dx in range(r["xSize"]) for dy in range(r["ySize"]))
    for top in range(gh - 1, -1, -1):
        for x in range(gw):
            for sw, sh, rot in ((w, h, False), (h, w, True)):
                if rot and w == h:
                    continue
                y = top - sh + 1
                if y >= 0 and x + sw <= gw and not any((x + dx, y + dy) in used
                                                       for dx in range(sw) for dy in range(sh)):
                    return x, y, rot
    return None


def attr(rec, aid):
    return next((a for a in rec["attributes"].get("itemAttributes", []) if a["id"] == aid), None)


def durability_text(rec):
    cur, mx = attr(rec, DURABILITY), attr(rec, MAX_DURABILITY)
    if not cur:
        return ""
    return f"{cur['value']['BaseValue']:.0f}/{mx['value']['BaseValue']:.0f}" if mx else f"{cur['value']['BaseValue']:.0f}"


def new_record(item_id, info, x, y, rotated):
    w, h = (info["h"], info["w"]) if rotated else (info["w"], info["h"])
    a = lambda aid, v: {"id": aid, "value": {"BaseValue": float(v), "statModifiers": []}}
    attrs = [a(EXPERIENCE, 0), a(MAX_DURABILITY, info["maxDurability"])]
    if info["hasDurability"]:
        attrs.insert(0, a(DURABILITY, info["maxDurability"]))
    return {"id": {"value": item_id}, "attachmentIds": [], "enchantmentIds": [], "caliberId": 0, "boughtFor": 0,
            "inventorySlot": 0, "position": [x, y], "quantity": 1, "xSize": w, "ySize": h, "currentAmmo": 0,
            "equipped": False, "selected": False, "rotated": rotated, "attributes": {"itemAttributes": attrs},
            "identifier": "", "attachments": [], "enchantments": [], "caliber": ""}


def pick(items, which):
    """Item indexes from 'all' or numbers, as the items command lists them."""
    if which == ["all"]:
        return list(range(len(items)))
    try:
        idx = sorted({int(w) for w in which})
    except ValueError:
        sys.exit("Give item numbers from the items command, or all.")
    bad = [i for i in idx if not 0 <= i < len(items)]
    if bad:
        sys.exit(f"No item number {bad[0]} in that grid; it has 0 to {len(items) - 1}.")
    return idx


# ---------- commands ----------

def cmd_slots(a):
    for p in sorted(SAVES.glob("Sulfur_SaveSlot_*.sss")):
        if "-BACKUP" in p.name:
            continue
        d, _ = load(p.stem.rsplit("_", 1)[1])
        print(f"slot {p.stem.rsplit('_', 1)[1]}: saved {datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}, "
              f"{d['PLAYTIME'] / 3600:.1f} h played, difficulty {d['DIFFICULTY']}, "
              f"{len(d['CHECKPOINTS']['values'])} checkpoints")


def cmd_show(a):
    d, _ = load(a.slot)
    print(f"Slot {a.slot}: {d['PLAYTIME'] / 3600:.1f} h played, difficulty {d['DIFFICULTY']}")
    print(f"Amulet charge: {get_res(d, 'WORLD_RESOURCES_STASH', AMULET)}/{AMULET_MAX}")
    print(f"Sulf: {get_res(d, 'WORLD_RESOURCES', SULF)} carried, {get_res(d, 'WORLD_RESOURCES_STASH', SULF)} stored;"
          f" stamps: {get_res(d, 'WORLD_RESOURCES_STASH', STAMP)}")
    print("Ammo        carried (cap)   stored")
    for alias, (rid, name, cap) in AMMO.items():
        print(f"  {alias:<8} {get_res(d, 'WORLD_RESOURCES', rid):>7} ({cap:>4})  {get_res(d, 'WORLD_RESOURCES_STASH', rid):>7}")
    print("Grids")
    stash_keys = set(d["STASH"]["_keys"])
    for g, (key, w, h) in GRIDS.items():
        if key is not None and key not in stash_keys:
            continue
        items = grid_items(d, g)
        n = sum(on_grid(r) for r in items)
        cells = sum(r["xSize"] * r["ySize"] for r in items if on_grid(r))
        eq = len(items) - n
        print(f"  {g:<12} {n:>3} items, {cells}/{w * h} cells used" + (f", {eq} equipped" if eq else ""))


def cmd_items(a):
    d, _ = load(a.slot)
    db = items_db()
    for g in [a.grid] if a.grid else shown_grids(d):
        items = grid_items(d, g)
        print(f"{g} ({GRIDS[g][1]}x{GRIDS[g][2]}):")
        for n, r in enumerate(items):
            where = f"equipped: {INVENTORY_SLOTS[r['inventorySlot']]}" if r["equipped"] else \
                f"at {r['position'][0]},{r['position'][1]}{' rotated' if r['rotated'] else ''}"
            extra = [f"{r['xSize']}x{r['ySize']}", where]
            if durability_text(r):
                extra.append("durability " + durability_text(r))
            if r["enchantmentIds"] or r["attachmentIds"]:
                extra.append(f"{len(r['attachmentIds'])} attachments, {len(r['enchantmentIds'])} enchantments")
            print(f"  {n:>3}  {shown(db, r)}  ({', '.join(extra)})")


def draw(items, gw, gh, marks=False, kinds=None):
    """The grid as text: item numbers (or x) in filled cells, a dot in free ones.

    Rows print top to bottom as the game shows them, so the top row is the
    highest y; the row labels are the y the save uses. kinds, a type per
    item, colors each item's cells.
    """
    kinds = kinds or [None] * len(items)
    cells = [[None] * gw for _ in range(gh)]
    for n, r in enumerate(items):
        if on_grid(r):
            x, y = r["position"]
            for dy in range(r["ySize"]):
                for dx in range(r["xSize"]):
                    if 0 <= x + dx < gw and 0 <= y + dy < gh:
                        cells[y + dy][x + dx] = n
    w = max(len(str(gw - 1)), 1 if marks else len(str(len(items) - 1)))
    lines = [" " * 3 + " ".join(f"{x:>{w}}" for x in range(gw))]
    for y, row in reversed(list(enumerate(cells))):
        lines.append(f"{y:>2} " + " ".join(
            f"{'.':>{w}}" if c is None else paint(f"{'x' if marks else c:>{w}}", kinds[c]) for c in row))
    free = sum(c is None for row in cells for c in row)
    return "\n".join(lines), free


def cmd_grid(a):
    d, _ = load(a.slot)
    db = items_db()
    for g in [a.grid] if a.grid else shown_grids(d):
        _, gw, gh = GRIDS[g]
        items = grid_items(d, g)
        kinds = [(db.get(r["id"]["value"]) or {}).get("type") for r in items]
        text, free = draw(items, gw, gh, a.x, kinds)
        print(f"{g} ({gw}x{gh}, {free} free cells):\n{text}")
        placed = [r for r in items if on_grid(r)]
        if COLOR and placed:
            print("   " + type_key(db, placed))
        if not a.x:
            # A legend in three columns, so a full stash stays on screen.
            names = [f"{n:>3} {shown(db, r, 22)}" for n, r in enumerate(items) if on_grid(r)]
            for i in range(0, len(names), 3):
                print("  " + "  ".join(names[i:i + 3]))
        print()


def cmd_find(a):
    db = items_db()
    if a.types:
        for t, what in TYPES.items():
            print(f"  {paint(f'{t:<11}', t)} {sum(v['type'] == t and v['addable'] for v in db.values()):>4}  {what}")
        print("  " + "; ".join(f"{g} = {' + '.join(sorted(ts))}" for g, ts in TYPE_GROUPS.items()))
        return
    if not a.query and not a.type:
        sys.exit("Give a name to search for, --type to list a kind of item, or --types for the list of kinds.")
    types = TYPE_GROUPS.get(a.type, {a.type}) if a.type else None
    hits = find_items(db, a.query, addable=not a.everything, types=types)
    limit = len(hits) if a.all else 60
    for i in hits[:limit]:
        v = db[i]
        label = paint(f"{v['name']:<34} {v['type']:<10}", v["type"])
        print(f"  {i:>5}  {label} {v['w']}x{v['h']}{'' if v['addable'] else '  not addable'}")
    more = f", first {limit} shown; add --all for every one" if len(hits) > limit else ""
    print(f"{len(hits)} match{'es' if len(hits) != 1 else ''}{more}")


def cmd_amulet(a):
    if not 0 <= a.charge <= AMULET_MAX:
        sys.exit(f"Amulet charge runs from 0 to {AMULET_MAX}; a higher value breaks the amulet's art when the save loads.")
    d, bom = load(a.slot)
    print(f"Amulet charge: {get_res(d, 'WORLD_RESOURCES_STASH', AMULET)} -> {a.charge}")
    set_res(d, "WORLD_RESOURCES_STASH", AMULET, a.charge)
    save(a, d, bom)


def amount_arg(v):
    """An ammo amount: a whole number, or max for the backpack or stash cap."""
    if v.lower() == "max":
        return "max"
    try:
        return int(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{v!r} is not a number or max")


def set_ammo(d, kinds, amount, stash=False):
    """Set each caliber in kinds to amount (a number or "max"), carried or stored."""
    key, where = ("WORLD_RESOURCES_STASH", "stored") if stash else ("WORLD_RESOURCES", "carried")
    for alias in kinds:
        rid, name, cap = AMMO[alias]
        limit = STASH_MAX if stash else cap
        n = limit if amount == "max" else amount
        if n > limit:
            print(f"  {name}: {n} is over the {where} cap of {limit}; using {limit}.")
            n = limit
        print(f"{name} {where}: {get_res(d, key, rid)} -> {n}")
        set_res(d, key, rid, max(0, n))


def cmd_ammo(a):
    d, bom = load(a.slot)
    set_ammo(d, list(AMMO) if a.caliber == "all" else [a.caliber], a.amount, a.stash)
    save(a, d, bom)


def cmd_stamps(a):
    """Set the stamps at the church: a number, or +N / -N to add or take away.

    The game spends stamps from the stash (EntityStats.GetStamps and the
    dialog checks read WORLD_RESOURCES_STASH); cards add them to the carried
    count, which moves to the stash at the church.
    """
    d, bom = load(a.slot)
    have = get_res(d, "WORLD_RESOURCES_STASH", STAMP)
    try:
        n = have + int(a.amount) if a.amount[0] in "+-" else int(a.amount)
    except ValueError:
        sys.exit(f"{a.amount!r} is not a number; give N, +N, or -N.")
    n = min(max(0, n), STASH_MAX)
    print(f"Stamps stored: {have} -> {n}")
    set_res(d, "WORLD_RESOURCES_STASH", STAMP, n)
    save(a, d, bom)


def resolve_item(db, query):
    """The one addable item a name or id names, as (id, info); exits when it names none or several."""
    hits = find_items(db, query, addable=True)
    if len(hits) != 1:
        if not hits:
            sys.exit(f'No addable item matches "{query}". Try the find command.')
        names = "\n".join(f"  {i:>5}  {db[i]['name']}" for i in hits[:20])
        sys.exit(f'"{query}" matches {len(hits)} items; give the exact name or the id:\n{names}')
    return hits[0], db[hits[0]]


def cmd_add(a):
    d, bom = load(a.slot)
    db = items_db()
    item_id, info = resolve_item(db, a.item)
    _, gw, gh = GRIDS[a.grid]
    items = grid_items(d, a.grid)
    for n in range(a.count):
        spot = free_spot(items, info["w"], info["h"], gw, gh)
        if not spot:
            sys.exit(f"{a.grid} has no free {info['w']}x{info['h']} space for copy {n + 1}; nothing changed.")
        items.append(new_record(item_id, info, *spot))
        print(f"Add {paint(info['name'], info['type'])} to {a.grid} at {spot[0]},{spot[1]}{' rotated' if spot[2] else ''}")
    save(a, d, bom)


def cmd_remove(a):
    d, bom = load(a.slot)
    db = items_db()
    items = grid_items(d, a.grid)
    for i in reversed(pick(items, a.which)):
        print(f"Remove {shown(db, items[i])} from {a.grid}")
        del items[i]
    save(a, d, bom)


def cmd_move(a):
    d, bom = load(a.slot)
    db = items_db()
    src, dst = grid_items(d, a.grid), grid_items(d, a.to)
    _, gw, gh = GRIDS[a.to]
    for i in reversed(pick(src, a.which)):
        r = src[i]
        info = db.get(r["id"]["value"], {"w": r["xSize"], "h": r["ySize"]})
        w, h = (info["h"], info["w"]) if r["rotated"] else (info["w"], info["h"])
        spot = free_spot(dst if dst is not src else [x for x in dst if x is not r], w, h, gw, gh)
        if not spot:
            sys.exit(f"{a.to} has no free space for {item_name(db, r)}; nothing changed.")
        x, y, rot = spot
        del src[i]
        r.update(position=[x, y], rotated=r["rotated"] != rot, equipped=False, selected=False, inventorySlot=0,
                 xSize=h if rot else w, ySize=w if rot else h)
        dst.append(r)
        print(f"Move {shown(db, r)} from {a.grid} to {a.to} at {x},{y}{' rotated' if r['rotated'] else ''}")
    save(a, d, bom)


def tiles(x, y, fw, fh, w, h, fill):
    """Spots for a w x h item inside the fw x fh footprint at x, y: every one, or the top-left one.

    Returns (x, y, rotated) tuples in the orientation that fits the most.
    """
    best = []
    for sw, sh, rot in ((w, h, False), (h, w, True)):
        if rot and w == h:
            continue
        spots = [(x + i * sw, y + fh - (j + 1) * sh, rot)  # top row first, as the grid reads
                 for j in range(fh // sh) for i in range(fw // sw)]
        if len(spots) > len(best):
            best = spots
    return best if fill else best[:1]


def convert_items(d, db, grids, target, which=("all",), types=None, fill=True):
    """Swap the chosen items in grids for target, in the space each one used.

    Returns (old items swapped, new items made).
    """
    info = db[target]
    made = gone = 0
    for g in grids:
        _, gw, gh = GRIDS[g]
        items = grid_items(d, g)
        chosen = [i for i in pick(items, list(which))
                  if on_grid(items[i]) and items[i]["id"]["value"] != target
                  and (not types or (db.get(items[i]["id"]["value"]) or {}).get("type") in types)]
        old = [items[i] for i in chosen]
        for i in reversed(chosen):
            del items[i]
        spill = 0
        for r in old:
            x, y = r["position"]
            spots = tiles(x, y, r["xSize"], r["ySize"], info["w"], info["h"], fill)
            if not spots:  # the new item is bigger than the old one: put it anywhere free
                spill += 1
                spot = free_spot(items, info["w"], info["h"], gw, gh)
                if not spot:
                    sys.exit(f"{g} has no room for {info['name']} in place of {item_name(db, r)}; nothing changed.")
                spots = [spot]
            for spot in spots:
                items.append(new_record(target, info, *spot))
            made += len(spots)
            gone += 1
            print(f"{g}: {shown(db, r)} at {x},{y} -> {len(spots)} {paint(info['name'], info['type'])}")
        if spill:
            print(f"  {spill} did not fit in the old item's space and went to the first free spot.")
    return gone, made


def cmd_convert(a):
    """Swap items for another item, each in the space the old one used."""
    d, bom = load(a.slot)
    db = items_db()
    target, info = resolve_item(db, a.item)
    if not a.which and not a.type:
        sys.exit("Say which items to convert: item numbers, all, or --type (such as --type food).")
    if a.grid == "all" and a.which:
        sys.exit("convert all takes no item numbers; name a grid to convert single items.")
    types = TYPE_GROUPS.get(a.type, {a.type}) if a.type else None
    grids = shown_grids(d) if a.grid == "all" else [a.grid]
    gone, made = convert_items(d, db, grids, target, a.which or ["all"], types, not a.one)
    if not gone:
        sys.exit("No items match; nothing changed.")
    print(f"\n{gone} item{'s' if gone != 1 else ''} -> {made} {info['name']}")
    save(a, d, bom)


def cmd_repair(a):
    """Repair items by number in one grid, a whole grid, or every grid (repair all)."""
    d, bom = load(a.slot)
    db = items_db()
    which = a.which or ["all"]
    if a.grid == "all" and which != ["all"]:
        sys.exit("repair all takes no item numbers; name a grid to repair single items.")
    repair_items(d, db, shown_grids(d) if a.grid == "all" else [a.grid], which)
    save(a, d, bom)


def repair_items(d, db, grids, which=("all",)):
    """Set durability to full on the chosen items in grids; returns how many it repaired."""
    which = list(which)
    fixed = 0
    for g in grids:
        items = grid_items(d, g)
        for i in pick(items, which):
            r = items[i]
            cur, mx = attr(r, DURABILITY), attr(r, MAX_DURABILITY)
            if not cur or not mx:
                if which != ["all"]:
                    print(f"{shown(db, r)} has no durability; skipped.")
                continue
            if cur["value"]["BaseValue"] < mx["value"]["BaseValue"]:
                print(f"Repair {shown(db, r)} in {g}: {durability_text(r)} -> full")
                cur["value"]["BaseValue"] = mx["value"]["BaseValue"]
                fixed += 1
    print(f"{fixed} item{'s' if fixed != 1 else ''} to repair." if fixed else "Nothing needs repair.")
    return fixed


def top_up(d, db, grid, item_id, want=None):
    """Add item_id to grid until it holds want of them, or until no space is left (want None).

    Returns how many it added.
    """
    info = db[item_id]
    name = paint(info["name"], info["type"])
    _, gw, gh = GRIDS[grid]
    items = grid_items(d, grid)
    have = sum(r["id"]["value"] == item_id for r in items if on_grid(r))
    added = 0
    while want is None or have + added < want:
        spot = free_spot(items, info["w"], info["h"], gw, gh)
        if not spot:
            break
        items.append(new_record(item_id, info, *spot))
        added += 1
    if want is None:
        print(f"{grid}: +{added} {name}" if added else f"{grid}: no free space left")
    elif have + added < want:
        print(f"{grid}: {have} {name}, +{added}; no room for {want - have - added} more")
    else:
        print(f"{grid}: {have} {name}" + (f", +{added}" if added else " already"))
    return added


HOTBAR = ["Gadget0", "Gadget1", "Gadget2"]  # the gadget slots, on keys 3, 4, and 5


def fill_hotbar(d, db, item_id, info):
    """Equip item_id in each empty gadget slot; returns how many it filled."""
    if not fits_slot(info, "Gadget0"):
        sys.exit(f"{info['name']} does not go in a gadget slot; nothing changed.")
    inv = grid_items(d, "backpack")
    taken = {r["inventorySlot"] for r in inv if r["equipped"]}
    filled = 0
    for key, slot in zip((3, 4, 5), HOTBAR):
        sid = INVENTORY_SLOTS.index(slot)
        if sid in taken:
            held = next(r for r in inv if r["equipped"] and r["inventorySlot"] == sid)
            print(f"  key {key}: {shown(db, held)} (kept)")
            continue
        rec = new_record(item_id, info, 0, 0, False)
        rec.update(equipped=True, inventorySlot=sid, position=[])
        inv.append(rec)
        filled += 1
        print(f"  key {key}: {paint(info['name'], info['type'])} (new)")
    return filled


CARD_CACHE = HERE / "card-cache.json"
ESCAPE_CARD = "Card_Escape"  # the card whose event is TravelBackToChurch


def cards_db():
    """Endless card key -> name, weight, and event, for the cards the game deals.

    FloatingCardManager deals from CardRewardDatabase.allCards, weighted, and
    only the cards whose key is in implementedCardKeys. The database sits in
    the endlessmode bundle; the list is cached in card-cache.json per game version.
    """
    sys.path.insert(0, str(HERE.parent))
    from game_files import game_dir, game_version  # noqa: E402
    root = game_dir([])
    version = game_version(root / "Sulfur_Data")
    if CARD_CACHE.exists():
        cached = json.loads(CARD_CACHE.read_text(encoding="utf-8"))
        if cached.get("version") == version:
            return cached["cards"]
    import UnityPy
    print("Reading the Endless cards from the game files (once per game version)...", file=sys.stderr)
    aa = root / "Sulfur_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"
    env = UnityPy.load(*(str(next(aa.glob(f"*{part}*.bundle"))) for part in ("_monoscripts_", "endlessmode_assets_all")))
    by_id = {o.path_id: o for o in env.objects}
    events = ["None", "ExplosiveBarrels", "EnemiesDropFood", "TravelBackToChurch", "PassForStamps", "Reroll",
              "RepairAll", "InfiniteAmmo", "Indestructible", "Bonanza", "MeleeXPBonus"]  # CardEventType
    db = None
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if "implementedCardKeys" in t and "allCards" in t:
                db = t
                break
    if db is None:
        sys.exit("No Endless card database in the game files; the game's layout may have changed.")
    live = set(db["implementedCardKeys"])
    cards = {}
    for e in db["allCards"]:
        o = by_id.get(e["card"]["m_PathID"])
        if o is None:
            continue
        c = o.read_typetree()
        if c["cardKey"] in live:
            cards[c["cardKey"]] = {"name": c["displayName"], "weight": e["weight"],
                                   "event": events[c["eventType"]] if c["eventType"] < len(events) else str(c["eventType"])}
    CARD_CACHE.write_text(json.dumps({"version": version, "cards": cards}, indent=0), encoding="utf-8")
    return cards


def cmd_endless(a):
    """Show an Endless run's card state, or change it: banish all but Escape, or set rerolls."""
    d, bom = load(a.slot)
    e = d.get("ENDLESS_RESUME") or {}
    if not e.get("isValid"):
        sys.exit(f"Slot {a.slot} has no Endless run in progress.")
    cards = cards_db()
    banned, used = set(e.get("banishedCardKeys") or []), set(e.get("selectedOneTimeUsed") or [])
    pool = {k: c for k, c in cards.items() if k not in banned and k not in used}
    total = sum(c["weight"] for c in pool.values())
    print(f"Endless run: stage {e['currentStage']}, loop {e['loopCount']}, card level {e['currentCardLevel']};"
          f" {e['rerollsRemaining']} rerolls, {e['banishesRemaining']} banishes left")
    esc = pool.get(ESCAPE_CARD)
    print(f"Card pool: {len(pool)} of {len(cards)} cards, {len(banned)} banished."
          + (f" Escape (back to church): weight {esc['weight']} of {total}, {esc['weight'] / total:.0%} a card"
             if esc else " Escape is not in the pool."))
    if a.action == "show":
        return
    if a.action == "escape":
        if ESCAPE_CARD in banned or ESCAPE_CARD in used:
            sys.exit("Escape is banished or used in this run; the game cannot deal it again.")
        new = sorted(k for k in cards if k != ESCAPE_CARD and k not in used)
        print(f"Banish {len(set(new) - banned)} more cards: every card but Escape. The next level-up deals"
              " Escape, plus the Skip and Reroll cards.")
        e["banishedCardKeys"] = sorted(banned | set(new))
    elif a.action in ("rerolls", "banishes"):
        if a.amount is None:
            sys.exit(f"Say how many {a.action}: endless {a.action} N")
        field = a.action + "Remaining"  # rerollsRemaining, banishesRemaining
        print(f"{a.action.capitalize()}: {e[field]} -> {a.amount}")
        e[field] = max(0, a.amount)
    save(a, d, bom)


def cmd_leave_endless(a):
    """End an Endless run the way the Travel Back to Church card does, keeping what you carry.

    The card calls EndlessModeManager.OnTravelBackToChurch: PlayerProgress
    clears the resume state (RESUME_ENVIRONMENT None, RESUME_LEVEL_INDEX -1,
    no saved buffs or stats) and the run state (a new EndlessRunSaveData,
    every field at its default). On the next load the game finds no resume
    state and starts at the church. Inventory, stash, and resources stay.
    """
    d, bom = load(a.slot)
    e = d.get("ENDLESS_RESUME") or {}
    if not e.get("isValid"):
        sys.exit(f"Slot {a.slot} has no Endless run in progress; nothing to do.")
    print(f"Endless run: stage {e['currentStage']}, loop {e['loopCount']}, burst {e['currentBurstIndex']},"
          f" card level {e['currentCardLevel']}, {len(e.get('permanentModifiers', []))} card upgrades")
    blank = lambda v: False if isinstance(v, bool) else type(v)()  # each field's C# default
    d["ENDLESS_RESUME"] = {k: blank(v) for k, v in e.items()}
    d["RESUME_ENVIRONMENT"], d["RESUME_LEVEL_INDEX"] = 0, -1
    d["RESUME_BUFFS"], d["RESUME_STATS"] = [], []
    print("Ends the run and starts the slot at the church, with the backpack as last saved.")
    print("The run's card upgrades end, as they do when you take the church card. The Endless")
    print("records (best stage, wave, level) keep their old values; the game updates them only in a run.")
    save(a, d, bom)


RESTOCK_SWAP =("food", "organ")  # the item types restock swaps for potions


def cmd_restock(a):
    """Ready the backpack for a run: food and organs to potions, repair, ammo, kits, then potions in every gap.

    The food and organs, potions included, come out first and the kits go
    in before the potions, so the kits get room and the potions fill the rest.
    """
    d, bom = load(a.slot)
    db = items_db()
    potion, info = resolve_item(db, a.item)
    items = grid_items(d, "backpack")
    kind = lambda r: (db.get(r["id"]["value"]) or {}).get("type")
    food = [r for r in items if on_grid(r) and (kind(r) in RESTOCK_SWAP or r["id"]["value"] == potion)]
    counts = {t: sum(kind(r) == t and r["id"]["value"] != potion for r in food) for t in RESTOCK_SWAP}
    eaten = sum(counts.values())
    items[:] = [r for r in items if not any(r is f for f in food)]
    print(f"-- Out of the backpack: {counts['food']} food, {counts['organ']} organs,"
          f" {len(food) - eaten} {info['name']} (refilled below)")
    print("\n-- Repair, every grid")
    repair_items(d, db, shown_grids(d))
    print("\n-- Ammo to the backpack caps")
    set_ammo(d, list(AMMO), "max")
    if a.hotbar.lower() != "none":
        print("\n-- Empty hotbar slots (keys 3-5)")
        fill_hotbar(d, db, *resolve_item(db, a.hotbar))
    if a.kits:
        print(f"\n-- Keep {a.kits} repair kits")
        top_up(d, db, "backpack", resolve_item(db, "Repair Kit")[0], a.kits)
    print(f"\n-- Fill free space with {info['name']}")
    top_up(d, db, "backpack", potion)
    print(f"{info['name']}: {len(food) - eaten} -> {sum(r['id']['value'] == potion for r in items if on_grid(r))}")
    save(a, d, bom)


def restore_points(slot):
    """Every earlier copy of a slot, newest first, with copies of the same save merged.

    Three places keep copies: this script's backups/ (taken before each edit
    or revert), the game's Sulfur_SaveSlot_<n>-BACKUP.sss, and the game's
    RollingBackups/ folder. A file's modified time is when the game saved it;
    the script copies backups with their times kept.
    """
    sources = [(p, "editor backup") for p in BACKUPS.glob(f"Sulfur_SaveSlot_{slot}-*.sss")]
    sources += [(SAVES / f"Sulfur_SaveSlot_{slot}-BACKUP.sss", "game backup")]
    sources += [(p, "game rolling backup") for p in (SAVES / "RollingBackups").glob(f"Sulfur_SaveSlot_{slot}-BACKUP_*.sss")]
    points = {}
    for path, kind in sources:
        if not path.exists():
            continue
        try:
            raw = gzip.decompress(path.read_bytes())
            data = json.loads(raw.decode("utf-8-sig"))
        except (OSError, ValueError):
            print(f"  skipped {path.name}: it does not read as a save")
            continue
        key = json.dumps(data, sort_keys=True)
        p = points.setdefault(key, {"data": data, "bom": raw.startswith(BOM), "kinds": set(), "files": [],
                                    "time": path.stat().st_mtime})
        p["kinds"].add(kind)
        p["files"].append(path)
        p["time"] = min(p["time"], path.stat().st_mtime)
    return sorted(points.values(), key=lambda p: -p["time"])


def describe(d):
    """One line on where a save stands: playtime, backpack, and any run in progress."""
    e = d.get("ENDLESS_RESUME") or {}
    if e.get("isValid"):
        where = f"in an Endless run (stage {e.get('currentStage')}, health {e.get('playerHealth', 0):.0f})"
    elif d.get("RESUME_ENVIRONMENT"):
        where = "mid-run"
    else:
        where = "at the church"
    return (f"{d['PLAYTIME'] / 3600:.2f} h, {where}, {len(d['INVENTORY'])} backpack items, "
            f"amulet {get_res(d, 'WORLD_RESOURCES_STASH', AMULET)}/{AMULET_MAX}")


def cmd_revert(a):
    """List the restore points for a slot, or put one back."""
    current, _ = load(a.slot)
    now = json.dumps(current, sort_keys=True)
    points = restore_points(a.slot)
    if a.point is None:
        print(f"Slot {a.slot} now: {describe(current)}")
        if not points:
            print("No restore points.")
            return
        print("Restore points, newest first:")
        for n, p in enumerate(points, 1):
            same = "  (same as now)" if json.dumps(p["data"], sort_keys=True) == now else ""
            print(f"  {n:>2}  {datetime.fromtimestamp(p['time']):%Y-%m-%d %H:%M:%S}  {describe(p['data'])}{same}")
            print(f"      {', '.join(sorted(p['kinds']))}: {', '.join(f.name for f in p['files'])}")
        print(f"\nTo put one back: save_edit.py -s {a.slot} revert N --apply")
        return
    if not 1 <= a.point <= len(points):
        sys.exit(f"No restore point {a.point}; slot {a.slot} has 1 to {len(points)}. Run revert without a number to list them.")
    p = points[a.point - 1]
    print(f"Slot {a.slot} now:      {describe(current)}")
    print(f"Revert to point {a.point}: {describe(p['data'])}  (saved {datetime.fromtimestamp(p['time']):%Y-%m-%d %H:%M:%S})")
    if json.dumps(p["data"], sort_keys=True) == now:
        print("That is the save the slot holds now; nothing to do.")
        return
    if (p["data"].get("ENDLESS_RESUME") or {}).get("isValid"):
        print("Note: this save has an Endless run in progress. The game resumes it on load and spawns enemies at once.")
    save(a, p["data"], p["bom"])


# ---------- loadouts ----------
#
# A loadout is loadouts/<name>.json: a set of equipped items, or the contents
# of one container. "loadout save" writes each item's full record, so a copy
# keeps its enchantments, attachments, durability, and loaded ammo. A
# hand-written entry can name an item instead, and then gets a new copy at
# full durability:
#
#   {"kind": "equipped", "items": [{"slot": "Weapon0", "item": "Wyatt PULSAR"},
#                                  {"slot": "Head", "item": "Titanium Helmet"}]}
#   {"kind": "container", "grid": "stash", "items": [{"item": "Repair Kit", "count": 3}]}
#
# Applying a loadout adds copies of its items; it does not take them from
# anywhere. The amulet never goes in a loadout: a save holds one.

def loadout_path(name):
    if not name.replace("-", "").replace("_", "").isalnum():
        sys.exit("Name a loadout with letters, numbers, - and _ only.")
    return LOADOUTS / f"{name}.json"


def read_loadout(name):
    path = loadout_path(name)
    if not path.exists():
        have = ", ".join(p.stem for p in sorted(LOADOUTS.glob("*.json"))) or "none yet"
        sys.exit(f'No loadout "{name}". Loadouts: {have}.')
    return json.loads(path.read_text(encoding="utf-8"))


def entry_record(db, entry):
    """The saved record an entry stands for: its own copy, or a new item by name or id."""
    if "record" in entry:
        return json.loads(json.dumps(entry["record"]))
    hits = find_items(db, str(entry["item"]), addable=True)
    if len(hits) != 1:
        sys.exit(f'Loadout item "{entry["item"]}" matches {len(hits)} items; use the exact name or the id.')
    return new_record(hits[0], db[hits[0]], 0, 0, False)


def fits_slot(info, slot):
    want = SLOT_TYPE[slot]
    return info.get("slot") == want or (want == "Gadget" and info.get("use") == "Consumable")


def place(items, rec, gw, gh, prefer=None):
    """Put a record on a grid: at prefer when that spot is free, else the first free spot."""
    # A saved size is already swapped when the item is rotated; free_spot wants the unrotated one.
    w, h = (rec["ySize"], rec["xSize"]) if rec.get("rotated") else (rec["xSize"], rec["ySize"])
    spot = None
    if prefer and len(prefer) == 2:
        x, y = prefer
        used = {(r["position"][0] + dx, r["position"][1] + dy) for r in items if on_grid(r)
                for dx in range(r["xSize"]) for dy in range(r["ySize"])}
        if x + rec["xSize"] <= gw and y + rec["ySize"] <= gh and \
                not any((x + dx, y + dy) in used for dx in range(rec["xSize"]) for dy in range(rec["ySize"])):
            spot = (x, y, bool(rec.get("rotated")))
    if spot is None:
        spot = free_spot(items, w, h, gw, gh)
        if not spot:
            return False
    x, y, rot = spot
    rec.update(position=[x, y], rotated=rot, xSize=h if rot else w, ySize=w if rot else h,
               equipped=False, selected=False, inventorySlot=0)
    items.append(rec)
    return True


def cmd_loadout(a):
    getattr(sys.modules[__name__], "loadout_" + a.action)(a)


def loadout_list(a):
    files = sorted(LOADOUTS.glob("*.json"))
    if not files:
        print("No loadouts yet. Make one with: save_edit.py -s N loadout save NAME [equipped|GRID]")
    for f in files:
        L = json.loads(f.read_text(encoding="utf-8"))
        where = "equipped items" if L["kind"] == "equipped" else f"a {L.get('grid', 'container')} container"
        n = sum(e.get("count", 1) for e in L["items"])
        print(f"  {f.stem:<20} {n:>3} items, {where}" + (f"  (from {L['from']})" if L.get("from") else ""))


def loadout_show(a):
    L = read_loadout(a.name)
    db = items_db()
    print(f"{a.name}: {L['kind']}" + (f" for {L.get('grid')}" if L["kind"] == "container" else "")
          + (f", saved from {L['from']} on {L.get('saved', '?')}" if L.get("from") else ""))
    for e in L["items"]:
        rec = entry_record(db, e)
        extra = [f"durability {durability_text(rec)}"] if durability_text(rec) else []
        if rec["enchantmentIds"] or rec["attachmentIds"]:
            extra.append(f"{len(rec['attachmentIds'])} attachments, {len(rec['enchantmentIds'])} enchantments")
        head = f"{e['slot']:<10} " if L["kind"] == "equipped" else f"{e.get('count', 1):>3}x "
        print(f"  {head}{shown(db, rec)}" + (f"  ({', '.join(extra)})" if extra else ""))


def loadout_delete(a):
    path = loadout_path(a.name)
    if not path.exists():
        sys.exit(f'No loadout "{a.name}".')
    path.unlink()
    print(f'Deleted loadout "{a.name}".')


def loadout_save(a):
    d, _ = load(a.slot)
    db = items_db()
    path = loadout_path(a.name)
    if path.exists() and not a.force:
        sys.exit(f'Loadout "{a.name}" exists. Add --force to replace it.')
    src = a.source or "equipped"
    if src == "equipped":
        recs = [r for r in d["INVENTORY"] if r["equipped"] and INVENTORY_SLOTS[r["inventorySlot"]] != "Amulet"]
        entries = [{"slot": INVENTORY_SLOTS[r["inventorySlot"]], "name": item_name(db, r), "record": r} for r in recs]
        L = {"kind": "equipped"}
    else:
        recs = [r for r in grid_items(d, src) if on_grid(r)]
        entries = [{"name": item_name(db, r), "record": r} for r in recs]
        L = {"kind": "container", "grid": src}
    if not entries:
        sys.exit(f"Slot {a.slot} has nothing {'equipped' if src == 'equipped' else 'in ' + src} to save.")
    L.update({"from": f"slot {a.slot} {src}", "saved": datetime.now().strftime("%Y-%m-%d %H:%M"), "items": entries})
    LOADOUTS.mkdir(exist_ok=True)
    path.write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f'Saved {len(entries)} items as loadout "{a.name}" ({path.relative_to(HERE)}).')
    for e in entries:
        print(f"  {e.get('slot', ''):<10} {shown(db, e['record'])}" if "slot" in e else f"  {shown(db, e['record'])}")


def loadout_apply(a):
    """Equip a loadout's items, or fill a container with them; displaced items move to --to."""
    L = read_loadout(a.name)
    d, bom = load(a.slot)
    db = items_db()
    to = a.to
    dest = None if to == "delete" else grid_items(d, to)
    _, tw, th = GRIDS[to] if to != "delete" else (None, 0, 0)

    def displace(rec, why):
        if dest is None:
            print(f"  Delete {shown(db, rec)} ({why})")
            return
        if not place(dest, rec, tw, th):
            sys.exit(f"{to} has no room for {item_name(db, rec)}; nothing changed. Pick another --to grid, or --to delete.")
        print(f"  Move {shown(db, rec)} ({why}) to {to} at {rec['position'][0]},{rec['position'][1]}")

    if L["kind"] == "equipped":
        inv = d["INVENTORY"]
        if dest is inv:
            sys.exit("Equipped items share the backpack's list; use --to with a stash, or --to delete.")
        for e in L["items"]:
            slot = e["slot"]
            if slot not in SLOT_TYPE or slot == "Amulet":
                sys.exit(f'Loadout slot "{slot}" is not one a loadout can set.')
            rec = entry_record(db, e)
            info = db.get(rec["id"]["value"], {})
            if not fits_slot(info, slot):
                sys.exit(f"{item_name(db, rec)} does not go in the {slot} slot; nothing changed.")
            sid = INVENTORY_SLOTS.index(slot)
            for old in [r for r in inv if r["equipped"] and r["inventorySlot"] == sid]:
                inv.remove(old)
                displace(old, f"was in {slot}")
            rec.update(equipped=True, inventorySlot=sid, position=[], selected=bool(rec.get("selected")))
            inv.append(rec)
            print(f"Equip {shown(db, rec)} in {slot}")
        # The game holds one item in hand: keep the last one the loadout marks, else the first weapon.
        held = [r for r in inv if r["equipped"] and r.get("selected")]
        for r in held[:-1]:
            r["selected"] = False
        if not held:
            weapon = next((r for r in inv if r["equipped"] and INVENTORY_SLOTS[r["inventorySlot"]].startswith("Weapon")), None)
            if weapon:
                weapon["selected"] = True
    else:
        target = a.grid or L.get("grid")
        if target not in GRIDS:
            sys.exit("Name the grid to fill: save_edit.py -s N loadout apply NAME GRID")
        if dest is not None and to == target:
            sys.exit(f"--to cannot be the grid you fill ({target}); pick another grid, or --to delete.")
        items = grid_items(d, target)
        _, gw, gh = GRIDS[target]
        if a.replace:
            for old in [r for r in items if on_grid(r)]:
                items.remove(old)
                displace(old, f"was in {target}")
        for e in L["items"]:
            for _ in range(e.get("count", 1)):
                rec = entry_record(db, e)
                prefer = rec.get("position") if "record" in e and a.replace else None
                if not place(items, rec, gw, gh, prefer):
                    sys.exit(f"{target} has no room for {item_name(db, rec)}; nothing changed. Try --replace.")
                print(f"Add {shown(db, rec)} to {target} at {rec['position'][0]},{rec['position'][1]}")
    save(a, d, bom)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    # --slot goes before the command (save_edit.py -s 3 items) or after it. The
    # command's copy defaults to SUPPRESS so it does not wipe a slot given first.
    p.add_argument("--slot", "-s", type=int, metavar="N", help="save slot number")
    p.add_argument("--no-color", action="store_true", help="plain text: no item type colors (or set NO_COLOR)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def slot(s):
        s.add_argument("--slot", "-s", type=int, metavar="N", default=argparse.SUPPRESS, help="save slot number")
        s.set_defaults(needs_slot=True)
    grid = lambda s, name="grid", **kw: s.add_argument(name, choices=GRIDS, **kw)
    def apply(s):
        s.add_argument("--apply", action="store_true", help="write the change (default: dry run)")
        s.add_argument("--game-open", action="store_true",
                       help="write while SULFUR runs; safe only at the main menu, not mid-run")

    sub.add_parser("slots", help="list the save slots")
    s = sub.add_parser("show", help="amulet, money, ammo, and grid space"); slot(s)
    s = sub.add_parser("items", help="list the items in a grid, numbered"); slot(s); grid(s, nargs="?")
    s = sub.add_parser("grid", help="draw a grid: each cell shows the item number in it"); slot(s)
    grid(s, nargs="?"); s.add_argument("--x", action="store_true", help="mark filled cells with x instead")
    s = sub.add_parser("find", help="search items by name, id, or type")
    s.add_argument("query", nargs="?", help="part of a name, or an id")
    s.add_argument("--type", "-t", choices=[*TYPES, *TYPE_GROUPS], help="only items of this type")
    s.add_argument("--types", action="store_true", help="list the types and how many items each has")
    s.add_argument("--all", action="store_true", help="show every match, not the first 60")
    s.add_argument("--everything", action="store_true", help="include items the game no longer uses")
    s = sub.add_parser("amulet", help="set the amulet charge"); slot(s)
    s.add_argument("charge", type=int); apply(s)
    s = sub.add_parser("ammo", help="set ammo, carried or stored"); slot(s)
    s.add_argument("caliber", choices=list(AMMO) + ["all"])
    s.add_argument("amount", type=amount_arg, help="a number, or max for the cap")
    s.add_argument("--stash", action="store_true", help="set the church stash instead of the backpack"); apply(s)
    s = sub.add_parser("stamps", help="set the stamps stored at the church"); slot(s)
    s.add_argument("amount", help="a number, or +N / -N to add or take away"); apply(s)
    s = sub.add_parser("add", help="add an item at the first free spot"); slot(s); grid(s)
    s.add_argument("item", help="item name or id"); s.add_argument("--count", type=int, default=1); apply(s)
    s = sub.add_parser("remove", help="delete items by number"); slot(s); grid(s)
    s.add_argument("which", nargs="+", help="item numbers from the items command, or all"); apply(s)
    s = sub.add_parser("move", help="move items to another grid"); slot(s); grid(s)
    s.add_argument("which", nargs="+"); grid(s, "to"); apply(s)
    s = sub.add_parser("repair", help="set durability to full: repair all, a grid, or items by number"); slot(s)
    s.add_argument("grid", choices=["all", *GRIDS], help="a grid, or all for every grid")
    s.add_argument("which", nargs="*", help="item numbers (default: the whole grid)"); apply(s)
    s = sub.add_parser("convert", help="swap items for another item, in the same space"); slot(s)
    s.add_argument("grid", choices=["all", *GRIDS], help="a grid, or all for every grid")
    s.add_argument("item", help="the item to turn them into: name or id")
    s.add_argument("which", nargs="*", help="item numbers, or all (default with --type: the whole grid)")
    s.add_argument("--type", "-t", choices=[*TYPES, *TYPE_GROUPS], help="only items of this type")
    s.add_argument("--one", action="store_true",
                   help="one new item per old item (default: fill the old space, so a 1x2 food becomes two 1x1 potions)"); apply(s)
    s = sub.add_parser("restock", help="food and organs to potions, repair all, max ammo, repair kits, potions in free space")
    slot(s)
    s.add_argument("--kits", type=int, default=3, metavar="N", help="keep N repair kits in the backpack (default 3; 0 skips)")
    s.add_argument("--item", default="Health Potion", help="what food turns into and gaps fill with (default Health Potion)")
    s.add_argument("--hotbar", default="First Aid Kit", metavar="ITEM",
                   help="what goes in empty gadget slots, keys 3-5 (default First Aid Kit; none skips)")
    apply(s)
    s = sub.add_parser("leave-endless", help="end an Endless run and start at the church, as the church card does")
    slot(s); apply(s)
    s = sub.add_parser("endless", help="an Endless run's cards: show, deal only Escape, or set rerolls and banishes"); slot(s)
    s.add_argument("action", nargs="?", default="show", choices=["show", "escape", "rerolls", "banishes"],
                   help="show (default); escape banishes every card but Escape; rerolls or banishes sets how many are left")
    s.add_argument("amount", type=int, nargs="?", help="the count, for rerolls or banishes"); apply(s)
    s = sub.add_parser("revert", help="list a slot's restore points, or put one back"); slot(s)
    s.add_argument("point", type=int, nargs="?", help="restore point number from the list"); apply(s)

    s = sub.add_parser("loadout", help="save equipped items or a container as a loadout, and apply it")
    lo = s.add_subparsers(dest="action", required=True)
    lo.add_parser("list", help="list the loadouts")
    x = lo.add_parser("show", help="the items in a loadout"); x.add_argument("name")
    x = lo.add_parser("delete", help="delete a loadout"); x.add_argument("name")
    x = lo.add_parser("save", help="save what a slot has equipped, or a container, as a loadout"); slot(x)
    x.add_argument("name"); x.add_argument("source", nargs="?", choices=["equipped", *GRIDS],
                                           help="equipped (default) or a grid")
    x.add_argument("--force", action="store_true", help="replace a loadout with the same name")
    x = lo.add_parser("apply", help="equip a loadout, or fill a container with it"); slot(x)
    x.add_argument("name"); x.add_argument("grid", nargs="?", choices=GRIDS,
                                           help="the grid to fill (default: the one it was saved from)")
    x.add_argument("--replace", action="store_true", help="empty the container first")
    x.add_argument("--to", default="stash", choices=["delete", *GRIDS],
                   help="where displaced items go (default: stash; delete discards them)")
    apply(x)

    a = p.parse_args()
    enable_color(a.no_color)
    if getattr(a, "needs_slot", False) and a.slot is None:
        p.error(f"{a.cmd} needs a save slot: save_edit.py -s N {a.cmd} ...")
    globals()["cmd_" + a.cmd.replace("-", "_")](a)


if __name__ == "__main__":
    main()
