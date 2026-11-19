"""Build oils-data.js for the SULFUR weapon oil page from the installed game.

Weapon oils are the enchantments that are not elemental: drag one onto a
weapon to change its stats. Most trade a benefit for a drawback. This script
reads every oil and the weapon modifiers it applies, the way the in-game
tooltip shows them, and marks each line as a benefit or a drawback. The
game tags each oil with its main effect, such as Spread or Multishot; the
page groups oils by that tag. A few oils have no tag and go under the tag
of their first benefit.
It exports icons to icons/ and writes window.SULFUR_OILS for index.html.

    py -m pip install UnityPy dnfile
    py -I build_oils.py [path to the SULFUR install folder]
"""
import collections
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))  # -I leaves the script folder off the path
from game_files import WIKI_SEARCH, Game, game_dir  # noqa: E402

OUT = HERE / "oils-data.js"
ICONS = HERE / "icons"

# Which way each weapon attribute helps the player: +1 when more is better,
# -1 when less is better, 0 when it is neither (a side effect, such as
# heavier bullets). A boolean attribute that switches something off counts
# as a drawback when the oil sets it.
DIRECTION = {
    "Damage": 1, "CritChance": 1, "ProjectileAmount": 1, "RPM": 1, "ReloadSpeed": 1, "MaxDurability": 1,
    "ProjectileTimeScale": 1, "ProjectileScale": 1, "ProjectileBounce": 1, "ProjectilePenetration": 1,
    "KnockbackPower": 1, "ProjectileForce": 1, "ItemStat_MoveSpeed": 1, "ItemStat_JumpPower": 1,
    "ItemStat_LootChanceMultiplier": 1, "AimMovingBonus": 1, "EnchantmentAddRandomOilAttributes": 1,
    "Spread": -1, "KickMultiplier": -1, "ConsumeAmmoChance": -1, "DurabilityLoss": -1,
    "EnchantmentDurabilityCost": -1, "ConsumeExtraAmmoChance": -1,
    "DisableADS": -1, "DisableLootOrgans": -1, "DisableLootMoney": -1,
    "ProjectileMass": 0, "ProjectileDrag": 0, "ProjectileBounciness": 0, "ProjectileBehaviourTimeout": 0,
}
# The game tags each oil with its main effect (the ItemTag enum's Oil* flags).
# These are the page's groups, in order, with the name each gets.
TAG_GROUPS = [
    ("OilDamagePercentage", "Damage %"), ("OilDamageFlat", "Flat damage"), ("OilCritChance", "Crit chance"),
    ("OilMultishot", "Multishot"), ("OilRPM", "Fire rate"), ("OilReload", "Reload"), ("OilRecycle", "Ammo saving"),
    ("OilSpread", "Spread"), ("OilRecoil", "Recoil"), ("OilDurability", "Durability"),
    ("OilTravelTime", "Bullet speed"), ("OilMuzzleVelocity", "Muzzle velocity"), ("OilSize", "Bullet size"),
    ("OilBounce", "Bounce"), ("OilPenetration", "Penetration"), ("OilKnockback", "Knockback"),
    ("OilWeight", "Bullet weight"),
]
TAG_NAME = dict(TAG_GROUPS)
# For the few oils without a tag: the tag that an attribute's line points to.
# Damage splits by modifier type: 100 adds flat damage, 200 and 300 a percent.
ATTR_TAG = {
    "CritChance": "OilCritChance", "ProjectileAmount": "OilMultishot", "RPM": "OilRPM",
    "ReloadSpeed": "OilReload", "ConsumeAmmoChance": "OilRecycle", "Spread": "OilSpread",
    "KickMultiplier": "OilRecoil", "MaxDurability": "OilDurability", "DurabilityLoss": "OilDurability",
    "NoExtraDurabilityCost": "OilDurability", "ProjectileTimeScale": "OilTravelTime",
    "ProjectileForce": "OilMuzzleVelocity", "ProjectileScale": "OilSize", "ProjectileBounce": "OilBounce",
    "ProjectilePenetration": "OilPenetration", "KnockbackPower": "OilKnockback", "ProjectileMass": "OilWeight",
}
RANDOM, NO_EFFECT = "Mystery", "No listed effect"


def group_of(item, lines, tags):
    """The oil's group: its game tag, or for an untagged oil, the tag of its first benefit."""
    own = [TAG_NAME[v] for b, v in tags.items() if item["itemTags"] & b and v in TAG_NAME]
    if own:
        return own[0], True
    if any(l["key"] == "EnchantmentAddRandomOilAttributes" for l in lines):
        return RANDOM, False
    first = next((l for l in lines if l["kind"] == "good"), lines[0] if lines else None)
    if not first:
        return NO_EFFECT, False
    if first["key"] == "Damage":
        return TAG_NAME["OilDamageFlat" if first["modType"] == 100 else "OilDamagePercentage"], False
    return TAG_NAME.get(ATTR_TAG.get(first["key"]), NO_EFFECT), False


# Developer test items the game still ships; they are in no loot table.
TEST_OILS = {"Enchantment_TestOil", "Enchantment_TestOil2"}


def effect(line):
    """'good', 'bad', or 'side' for one tooltip line."""
    if line["key"] == "NoExtraDurabilityCost":
        return "good"
    d = DIRECTION.get(line["key"])
    if d is None or d == 0:
        return "side"
    return "good" if (line["value"] > 0) == (d > 0) else "bad"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    game = Game(game_dir())
    E = game.enums
    ICONS.mkdir(exist_ok=True)

    oils, unknown, untagged, attrs = [], collections.Counter(), 0, {}
    for i, t in game.items.items():
        if E["UseType"].get(t["useType"]) != "Enchantment" or t["deprecated"] or t["excludeFromDatabase"]                 or t["m_Name"] in TEST_OILS:
            continue
        ench, lines = game.enchant_lines(t)
        if not ench or ench["IsElemental"]:
            continue
        for line in lines:
            line["kind"] = effect(line)
            if line["key"] not in DIRECTION and line["key"] != "NoExtraDurabilityCost":
                unknown[line["key"]] += 1
            if line["key"] not in attrs:
                if line["attribute"] is None:  # the "no extra durability cost" line
                    attrs[line["key"]] = {"label": line["text"], "bool": True, "dir": 1}
                else:
                    attrs[line["key"]] = {**game.item_attr_info(line["attribute"]), "dir": DIRECTION.get(line["key"], 0)}
        group, tagged = group_of(t, lines, E["ItemTag"])
        untagged += not tagged
        icon = game.save_icon(i, ICONS)
        oils.append({
            "name": game.name(t), "key": t["m_Name"], "url": WIKI_SEARCH + game.name(t).replace(" ", "+"),
            "img": icon and "icons/" + icon, "quality": game.quality(t), "sell": game.sell(t), "grid": game.grid(t),
            "group": group, "effects": [{"text": l["text"], "kind": l["kind"]} for l in lines],
            # The raw modifiers, for the page to total several oils: attribute, value, modType.
            "mods": [{"a": l["key"], "v": 1 if l["value"] is None else l["value"], "t": l["modType"] or 100} for l in lines],
            "flavor": game.text(f"Items/{t['m_Name']}_flavor"),
        })

    order = [name for _, name in TAG_GROUPS] + [RANDOM, NO_EFFECT]
    data = {"source": "SULFUR game files", "version": game.version, "built": date.today().isoformat(),
            "groups": [g for g in order if any(o["group"] == g for o in oils)],
            "attrs": attrs,
            "oils": sorted(oils, key=lambda o: (o["name"].lower(), o["key"]))}
    OUT.write_text(
        "// Generated by build_oils.py from the installed SULFUR game files. Do not edit by hand.\n"
        "window.SULFUR_OILS = " + json.dumps(data, ensure_ascii=False, indent=0) + ";\n",
        encoding="utf-8")
    groups = collections.Counter(o["group"] for o in oils)
    print(f"{len(oils)} oils -> {OUT.name}, icons -> {ICONS.name}/")
    print("groups:", {g: groups[g] for g in data["groups"]})
    print(f"{untagged} oils have no game tag and are grouped by their first benefit")
    print("attributes with no direction (marked side effects):", dict(unknown) or "none")
    print("no icon:", ", ".join(o["name"] for o in oils if not o["img"]) or "none")


if __name__ == "__main__":
    main()
