"""Read SULFUR's installed game files: the shared code behind the SULFUR builders.

build_weapons.py, build_recipes.py, and build_scrolls.py import this module.
It finds the game through Steam, reads enum names from the game's DLLs with
dnfile, opens the startup Addressables bundle with UnityPy, and turns item
definitions into the same text the in-game tooltip shows.

    py -m pip install UnityPy dnfile
"""
import math
import re
import sys
import winreg
from pathlib import Path

import dnfile
import UnityPy

APP_ID = "2124120"
WIKI_SEARCH = "https://sulfur.wiki.gg/index.php?search="


def game_dir(argv=None):
    """The SULFUR install folder: the first argument, or found through Steam."""
    argv = sys.argv if argv is None else argv
    if len(argv) > 1:
        return Path(argv[1])
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
        steam = Path(winreg.QueryValueEx(k, "SteamPath")[0])
    vdf = (steam / "steamapps" / "libraryfolders.vdf").read_text(encoding="utf-8")
    for lib in re.findall(r'"path"\s+"([^"]+)"', vdf):
        apps = Path(lib.replace("\\\\", "\\")) / "steamapps"
        if (apps / f"appmanifest_{APP_ID}.acf").exists():
            return apps / "common" / "SULFUR"
    sys.exit("SULFUR not found in any Steam library. Pass the install folder as an argument.")


def enums(managed):
    """Enum type name -> {value: member name}, from the game's own assemblies."""
    out = {}
    for dll in ("PerfectRandom.Sulfur.Core.dll", "PerfectRandom.Sulfur.Gameplay.dll"):
        md = dnfile.dnPE(str(managed / dll)).net.mdtables
        consts = {}
        for c in md.Constant.rows:
            if c.Parent.table and c.Parent.table.name == "Field":
                v = c.Value
                consts[c.Parent.row_index] = v if isinstance(v, (bytes, int)) else bytes(v.value)
        for t in md.TypeDef.rows:
            try:
                if not t.Extends.row or str(t.Extends.row.TypeName) != "Enum":
                    continue
            except AttributeError:
                continue
            vals = {}
            for f in t.FieldList:
                v = consts.get(f.row_index)
                if v is not None:
                    vals[v if isinstance(v, int) else int.from_bytes(v, "little", signed=True)] = str(f.row.Name)
            out[str(t.TypeName)] = vals
    return out


class Game:
    """The startup bundle, enums, and English text of one SULFUR install."""

    def __init__(self, root):
        data = Path(root) / "Sulfur_Data"
        self.enums = enums(data / "Managed")
        aa = data / "StreamingAssets" / "aa" / "StandaloneWindows64"
        names = {p.name: p for p in aa.glob("*.bundle")}
        pick = lambda part: next(p for n, p in names.items() if part in n)
        self.env = UnityPy.load(str(pick("_monoscripts_")), str(pick("onstartup_assets_all")))
        self.objs = {(o.assets_file.name, o.path_id): o for o in self.env.objects}
        self._cls = {}
        self.by_class = {}
        for o in self.env.objects:
            if o.type.name == "MonoBehaviour":
                self.by_class.setdefault(self.cls(o), []).append(o)
        self.lang = {}
        for o in self.scripts("LanguageSourceAsset"):
            src = o.read_typetree()["mSource"]
            en = [l["Name"] for l in src["mLanguages"]].index("English")
            for term in src["mTerms"]:
                self.lang.setdefault(term["Term"], term["Languages"][en])
        self.items = {}  # item id -> ItemDefinition or WeaponSO typetree
        self.item_obj = {}
        for cls in ("ItemDefinition", "WeaponSO"):
            for o in self.scripts(cls):
                t = o.read_typetree()
                t["_class"] = cls
                self.items[t["id"]["value"]] = t
                self.item_obj[t["id"]["value"]] = o
        self.item_attrs = {t["id"]: t for t in (o.read_typetree() for o in self.scripts("ItemAttribute"))}
        self.entity_attrs = {t["id"]: t for t in (o.read_typetree() for o in self.scripts("EntityAttribute"))}
        self.enchants = {}
        for o in self.scripts("EnchantmentDefinition"):
            t = o.read_typetree()
            self.enchants[t["id"]["value"] if isinstance(t["id"], dict) else t["id"]] = t

    def cls(self, o):
        key = (o.assets_file.name, o.path_id)
        if key not in self._cls:
            try:
                self._cls[key] = o.read(check_read=False).m_Script.read().m_ClassName
            except Exception:
                self._cls[key] = None
        return self._cls[key]

    def get(self, o, ptr):
        if not ptr or ptr["m_PathID"] == 0 or ptr["m_FileID"] != 0:
            return None
        return self.objs.get((o.assets_file.name, ptr["m_PathID"]))

    def scripts(self, name):
        return self.by_class.get(name, [])

    def components(self, go, out=None):
        """Every component on a GameObject and its children."""
        out = [] if out is None else out
        for c in go.read_typetree()["m_Component"]:
            co = self.get(go, c["component"])
            if co is None:
                continue
            out.append(co)
            if co.type.name in ("Transform", "RectTransform"):
                for ch in co.read_typetree()["m_Children"]:
                    tr = self.get(co, ch)
                    child = tr and self.get(tr, tr.read_typetree()["m_GameObject"])
                    if child:
                        self.components(child, out)
        return out

    # ---------- item text ----------

    def name(self, item):
        """The English display name, as the game localizes it."""
        return re.sub(r"\s+", " ", self.lang.get("Items/" + item["m_Name"]) or item["displayName"]).strip()

    def text(self, key):
        v = self.lang.get(key)
        return re.sub(r"\s+", " ", v).strip() if v else None

    def sell(self, item):
        """InventoryItem.PriceSell for a new item without attachments: half the base price."""
        return math.ceil(item["basePrice"] * 0.5)

    def quality(self, item):
        return self.enums["ItemQuality"].get(item["itemQuality"])

    def grid(self, item):
        s = item["inventorySize"]
        return f"{s['x']}x{s['y']}"

    def save_icon(self, item_id, folder):
        """Write the item's inventory sprite to folder/<m_Name>.png; return the file name."""
        item, o = self.items[item_id], self.item_obj[item_id]
        art = self.get(o, item["artwork"])
        if art is None:
            return None
        path = Path(folder) / f"{item['m_Name']}.png"
        try:
            art.read().image.save(path)
        except Exception as e:
            print("icon failed:", item["m_Name"], e)
            return None
        return path.name

    def _entity(self, attr_id):
        return self.enums["EntityAttributes"].get(attr_id, str(attr_id))

    def _entity_label(self, attr_id):
        key = self._entity(attr_id)
        return self.text(f"EntityAttributes/{key}_itemDescription") or \
            self.entity_attrs.get(attr_id, {}).get("itemDescriptionName") or key

    @staticmethod
    def _num(v):
        v = round(float(v), 2)
        return str(int(v)) if v.is_integer() else str(v)

    def consume_effects(self, item):
        """ItemDescription's lines for what eating, drinking, or using the item does."""
        lines, heal = [], 0
        tmpl = lambda k: self.text("ItemDescriptions/" + k) or ""
        for c in item.get("valueChangeOnItemConsume", []):
            if self.enums["ItemAttributes"].get(c["attribute"]) == "Durability":
                lines.append(tmpl("DynamicString_RepairValue").replace("VALUE_X", str(int(c["value"]))))
        for b in item.get("buffsOnConsume", []):
            attr = self._entity(b["attributeId"])
            if attr == "None":
                continue
            dur = self._num(b["duration"])
            if attr == "Stat_HealthRegen":
                total = b["totalValueOverride"] or b["value"] * b["duration"]
                heal += total
                lines.append(tmpl("DynamicString_HealthConsumable").replace("VALUE_X", self._num(total))
                             .replace("DURATION_X", dur))
            elif attr == "Stat_MovementSpeed":
                lines.append(f"Gives {self._num(b['value'] * 100)}% extra movement speed for {dur} seconds.")
            else:
                pct = self.entity_attrs.get(b["attributeId"], {}).get("isPercentageAttribute")
                sign = "+" if b["value"] > 0 else ""
                val = f"{sign}{self._num(b['value'] * 100)}%" if pct else f"{sign}{self._num(b['value'])}"
                lines.append(tmpl("DynamicString_AttributeBonusBuff").replace("VALUE_X", val)
                             .replace("ATTRIBUTE_X", self._entity_label(b["attributeId"])).replace("DURATION_X", dur))
        for s in item.get("addStatusOnConsume", []):
            if self._entity(s["status"]) != "None":
                lines.append(tmpl("DynamicString_StatusAdd").replace("VALUE_X", self._num(s["value"]))
                             .replace("STATUS_X", self._entity_label(s["status"])))
        for a in item.get("removeStatusOnConsume", []):
            if self._entity(a) not in ("None", "End"):
                lines.append(tmpl("DynamicString_RemovesStatus").replace("STATUS_X", self._entity_label(a)))
        return [l.rstrip(".") for l in lines if l], heal

    def enchant_effects(self, item):
        """ItemDescription's lines for the enchantment a scroll applies to a weapon."""
        ench = self.enchants.get(item["appliesEnchantment"]["value"])
        if not ench:
            return None, []
        lines = []
        for m in ench["modifiersApplied"]:
            a = self.item_attrs.get(m["attribute"])
            key = self.enums["ItemAttributes"].get(m["attribute"], str(m["attribute"]))
            if not a or not a["showInItemDescription"]:
                continue
            label = self.text(f"ItemAttributes/{key}_itemDescription") or a["itemDescriptionName"]
            if a["simplifiedModAmount"]:
                which = "Increase" if m["value"] > 0 else "Decrease"
                lines.append(self.text(f"ItemAttributes/{key}_simplified{which}") or a[f"simplified{which}String"])
            elif a["isBooleanAttribute"]:
                lines.append(label)
            else:
                if a["showPercentageAsFactor"]:
                    val = "x" + self._num(m["value"])
                elif a["isPercentageAttribute"] or m["modType"] in (200, 300):
                    val = ("+" if m["value"] >= 0 else "") + self._num(m["value"] * 100) + "%"
                else:
                    val = ("+" if m["value"] >= 0 else "") + self._num(m["value"]) + a["unitMeasure"]
                lines.append(f"{label}: {val}{a['overrideUnitName']}")
        if not ench["CostsDurability"]:
            lines.append(self.text("ItemDescriptions/Label_NoExtraDurabilityCost"))
        return ench, [l for l in lines if l]
