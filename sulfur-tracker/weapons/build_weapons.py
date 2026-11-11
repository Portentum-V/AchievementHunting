"""Build weapons-data.js for the SULFUR weapon table from the installed game.

The game keeps one WeaponSO asset per weapon in its startup Addressables
bundle. This script reads those assets through game_files.py, takes English
names and melee descriptions from the game's localization table, and
exports each weapon's inventory icon to icons/. It writes
window.SULFUR_WEAPONS for index.html. Rerun it after a game update.

    py -m pip install UnityPy dnfile
    py -I build_weapons.py [path to the SULFUR install folder]

Without a path, it finds SULFUR through Steam's library folders.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))  # -I leaves the script folder off the path
from game_files import WIKI_SEARCH, Game, game_dir  # noqa: E402

OUT = HERE / "weapons-data.js"
ICONS = HERE / "icons"

# WeaponTypes enum name -> type label in the table, in display order.
TYPES = {
    "Pistol": "Pistol", "Revolver": "Revolver", "SMG": "SMG", "AssaultRifle": "Assault rifle",
    "LMG": "LMG", "Shotgun": "Shotgun", "Rifle": "Rifle", "Sniper": "Sniper rifle",
    "Bow": "Bow", "Melee": "Melee",
}
# Throwables (grenades, jars, knives) are left out on purpose.

# Hardcoded in the game's C#, not stored in any asset:
# WeaponTypeDataExt.GetDamageMultiplier scales caliber damage by weapon type.
TYPE_DAMAGE = {"AssaultRifle": 1.2, "Revolver": 1.6, "Rifle": 2.0, "Sniper": 2.0}
# ItemStats.SetProjectileAmountFromDefault fires 3 projectiles for the Augusta.
PELLETS = {"Weapon_Augusta": 3}
# Holdable.cs: move speed multiplier for each HoldableWeightClass.
WEIGHT_SPEED = {"Knife": 1.0, "Pistol": 0.95, "SMG": 0.88, "Rifle": 0.8, "Sniper": 0.75, "Bigga": 0.65}


def clip_length(clip):
    m = clip.read_typetree()["m_MuscleClip"]
    return m["m_StopTime"] - m["m_StartTime"]


def reload_time(bundle, animator, mag, per_round):
    """Approximate reload seconds, from the clips the weapon's Animator plays.

    The game ends a reload on animation events, so clip length is the best
    figure the files give. One reload cycle is start + reload + stop clip,
    from a partly full magazine. A gun that loads one round at a time with a
    short round clip (pump shotguns, some revolvers) repeats it per round.
    Returns None when no clip name says reload.
    """
    ctl = bundle.get(animator, animator.read_typetree()["m_Controller"])
    if ctl is None:
        return None
    t = ctl.read_typetree()
    ptrs = t.get("m_AnimationClips") or [c["m_OverrideClip"] for c in t.get("m_Clips", [])]
    clips, empty = {}, {}
    for p in ptrs:
        c = bundle.get(ctl, p)
        name = c and c.read_typetree()["m_Name"].split(".")[-1].split("_", 1)[-1]
        if not name or "reload" not in name.lower() or "cancel" in name.lower():
            continue
        pool = empty if "empty" in name.lower() else clips
        pool[name] = max(pool.get(name, 0), clip_length(c))
    clips = clips or empty  # some guns only have a from-empty clip
    if not clips:
        return None
    pick = lambda pat: max([v for k, v in clips.items() if re.match(pat, k, re.I)] or [0])
    start, stop = pick("startreload"), pick("stopreload")
    main = max([v for k, v in clips.items() if not re.match("(start|stop)reload", k, re.I)] or [0])
    if per_round and start and main <= 1 and not any("clip" in k.lower() for k in clips):
        return round(start + main * mag + stop, 2)
    return round(start + main + stop, 2)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    game = bundle = Game(game_dir())
    E, lang = game.enums, game.lang
    calibers = {t["id"]: t for t in (o.read_typetree() for o in game.scripts("CaliberType"))}

    ICONS.mkdir(exist_ok=True)
    weapons, skipped = [], []
    for o in bundle.scripts("WeaponSO"):
        t = o.read_typetree()
        wtype = E["WeaponTypes"].get(t["weaponType"], "None")
        key = t["m_Name"]
        if wtype not in TYPES or t["deprecated"] or t["excludeFromDatabase"] or key.endswith("NotUse"):
            if wtype != "Throwable":
                skipped.append(key)
            continue
        name = game.name(t)
        attrs = {E["ItemAttributes"].get(a["attribute"], a["attribute"]): a["value"] for a in t["baseAttributes"]}
        cal = calibers.get(t["caliber"])

        # ItemStats.SetDamageAmountFromDefault and ItemDescription's damage line.
        if t["overrideDamage"] or not cal:
            per = t["overrideDamage"]
        else:
            per = cal["baseDamage"] * TYPE_DAMAGE.get(wtype, 1.0) * t["damageMultiplier"]
        pellets = PELLETS.get(key, cal["numberOfProjectiles"] if cal else 1)
        per = int(round(per, 3))  # the game truncates a float32 product
        dmg = str(per)
        if pellets > 1:
            dmg += f"x{pellets}"
        if t["iMaxAmmoPerShot"] > 1:
            dmg += f"x{t['iMaxAmmoPerShot']}"

        melee = wtype == "Melee"
        # The prefab carries the Weapon component (round-by-round loading), one
        # WeaponAttachmentVisual per attachment it can show, and the Animator
        # whose clips time the reload.
        # Weapon.UpdateKickStrength: kick = KickMultiplier (1 at base) x the
        # weapon's kick power for its own caliber.
        recoil = next((k["KickPower"] for k in t["kickPower"] if k["Caliber"] == t["caliber"]), None)
        reload = None
        per_round = False
        slots, animators = set(), []
        prefab = bundle.get(o, t["prefab"])
        for c in bundle.components(prefab) if prefab else []:
            if c.type.name == "Animator":
                animators.append(c)
            elif c.type.name == "MonoBehaviour":
                ct = c.read_typetree()
                if bundle.cls(c) == "WeaponAttachmentVisual" and ct.get("attachmentDefinition", {}).get("m_PathID"):
                    slots.add(ct.get("attachmentSlot"))
                elif "bulletsPerReload" in ct:
                    # Weapon.cs: rounds added per reload cycle; 0 means a full magazine.
                    per_round = ct["bulletsPerReload"] == 1 < t["iAmmoMax"]
        for a in [] if melee else animators:
            reload = reload_time(bundle, a, t["iAmmoMax"], per_round)
            if reload:
                break

        icon = game.save_icon(t["id"]["value"], ICONS)
        img = icon and f"icons/{icon}"

        size = t["inventorySize"]
        w = {
            "name": name, "type": TYPES[wtype], "url": WIKI_SEARCH + name.replace(" ", "+"), "img": img,
            "quality": game.quality(t),
            "ammo": None if melee or not cal else cal["label"],
            "mode": None if melee else ("Automatic" if attrs.get("FullAuto", 0) > 0 else "Semi-Automatic"),
            "dmg": dmg, "dmgN": per * pellets * max(1, t["iMaxAmmoPerShot"]),
            "rpm": None if melee else t["rpm"],
            "mag": None if melee else t["iAmmoMax"],
            "spread": None if melee else attrs.get("Spread"),
            "recoil": None if melee or recoil is None else round(recoil, 2),
            "dur": int(t["maxDurability"]),
            "weight": round((1 - WEIGHT_SPEED[E["HoldableWeightClass"][t["weightClass"]]]) * 100),
            "sell": game.sell(t),
            "grid": f"{size['x']}x{size['y']}", "cells": size["x"] * size["y"],
            "slots": (len(slots) + 1) if slots else None,  # + the Insurance slot every gun has
            "reload": reload,
            "notes": [lang[f"Items/{key}_description"].strip()] if melee and lang.get(f"Items/{key}_description") else None,
        }
        weapons.append(w)

    order = list(TYPES.values())
    weapons.sort(key=lambda w: w["name"].lower())
    data = {"source": "SULFUR game files", "version": game.version, "built": date.today().isoformat(),
            "types": [x for x in order if any(w["type"] == x for w in weapons)], "weapons": weapons}
    OUT.write_text(
        "// Generated by build_weapons.py from the installed SULFUR game files. Do not edit by hand.\n"
        "window.SULFUR_WEAPONS = " + json.dumps(data, ensure_ascii=False, indent=0) + ";\n",
        encoding="utf-8")
    print(f"{len(weapons)} weapons -> {OUT.name}, icons -> {ICONS.name}/")
    print("skipped (deprecated or unused):", ", ".join(sorted(skipped)) or "none")
    for field in ("reload", "recoil", "slots", "img"):
        miss = [w["name"] for w in weapons if w[field] is None and w["type"] != "Melee"]
        print(f"no {field}:", ", ".join(miss) or "none")


if __name__ == "__main__":
    main()
