# Achievement Hunting

Offline Steam achievement trackers that sync with your own account, private
game details included.

## Layout

- `steam-achievements/` - Python library and command line. It logs in to
  Steam, reads your achievements, and serves the tracker pages. Its README
  covers login and building a tracker for a new game.
- `<game>-tracker/guide.js` - one guide per game: categories, tips, and
  checklists, keyed by Steam API name.
- `.claude/skills/add-game-tracker/` - a Claude Code skill that adds a game:
  it pulls the list, briefs a research agent, and validates the guide. To
  use it, start Claude Code in this folder and ask it to add a game.

| Folder | Game | Guide source |
| --- | --- | --- |
| `avatar-tracker` | Avatar: Frontiers of Pandora | PowerPyx, Steam community guides, Avatar Wiki |
| `bg3-tracker` | Baldur's Gate 3 | bg3.wiki, Steam community guides |
| `dawnwalker-tracker` | The Blood of Dawnwalker | IGN wiki |
| `dragonwilds-tracker` | RuneScape: Dragonwilds | RuneScape: Dragonwilds wiki |
| `megabonk-tracker` | Megabonk | Steam community guides |
| `ror2-tracker` | Risk of Rain 2 | Risk of Rain 2 wiki, Hallowed Concepts patch notes |
| `sulfur-tracker` | SULFUR | SULFUR wiki, Steam community guides and patch notes |
| `valheim-tracker` | Valheim | Steam community guide and its tracking sheet |

## Run

```
py -m pip install -e steam-achievements
py -m steam_achievements login
py -m steam_achievements.tracker
```

The last command opens a hub page that lists every game here. Run it from
this folder.

## SULFUR recipe calculator

`sulfur-tracker/recipes/` holds a cooking calculator. Add what you carry to
the pantry, and it lists the dishes you can cook, the best yield, and the
recipes one ingredient short. Press Cook on a recipe to swap its ingredients
in the pantry for the dish; Undo reverses it. With the tracker running, open
`/sulfur-tracker/recipes/`. Without it, open `index.html` directly.

"Cook next" lists dishes that need other dishes cooked first, up to 4 levels
deep. It ranks them by total heal, number of buffs, or sell value. Its Cook
button runs the whole chain.

The recipes come from your installed copy of SULFUR. The game lists one
recipe per ingredient combination. The calculator folds recipes that differ
in one ingredient into a slot that takes any of its items, and keeps every
combination exact. Once you know a recipe, you can quick-cook it from your
backpack at any stove. "Learn on a 4x4 stove" marks recipes whose
ingredients fit only the Wood Stove, and "Quick-cook only" marks recipes
whose ingredients fit no stove. After a game update, rebuild the recipes:

```
py -I sulfur-tracker/recipes/build_recipes.py
```

## SULFUR scrolls

`sulfur-tracker/scrolls/` lists every scroll with its description and the
weapon effects it adds, as the game's tooltip shows them. A chart shows
what the Scholar makes from each pair of scrolls, and each card shows what
makes the scroll and what it combines into. Weapon oils are enchantments
too, and they have their own page. After a game update, rebuild it:

```
py -I sulfur-tracker/scrolls/build_scrolls.py
```

## SULFUR oils

`sulfur-tracker/oils/` lists every weapon oil with the effects it adds, as
the game's tooltip shows them. Green marks a benefit and red a drawback.
The groups are the game's own tags for each oil's main effect, such as
Spread or Multishot. Toggle several groups at once, or show only oils with
no drawback.

To plan one weapon, click Add on up to 5 oils, since a rank 5 weapon holds
5. The side panel totals them the way the game stacks modifiers: flat
values add, percents add into one multiplier, and multiplying percents
multiply on top. After a game update, rebuild it:

```
py -I sulfur-tracker/oils/build_oils.py
```

## SULFUR armor and trinkets

`sulfur-tracker/gear/` lists every armor piece and trinket with what it
changes while worn. Click Wear to build an outfit: a head piece, a chest
piece, two feet, and four trinkets. The side panel totals the outfit with the
same stacking rules as the oils page. It also shows how much of each damage
type gets through, since each point of armor or resistance cuts that damage
by 1%. After a game update, rebuild it:

```
py -I sulfur-tracker/gear/build_gear.py
```

## SULFUR weapon table

`sulfur-tracker/weapons/` lists every gun and melee weapon in one table. Use
it to decide what to keep and what to sell without paging through each type.
It sorts by sell value by default; click any column to sort by it. Pink
marks the best seller of each type. The table skips throwables.

A star marks each gun whose "Pity for ..." achievement you have: you gave
Telia that gun at rank 5. The stars come from the tracker's last Steam sync,
so the page shows none until the tracker has run once.

With the tracker running, open `/sulfur-tracker/weapons/`. Without it, open
`index.html` directly.

The builder reads the stats, quality, sell values, and icons from your
installed copy of SULFUR, so the table matches your game version. Sell is
half the base price: what a trader pays for a bare gun before durability
changes it. Reload times come from the length of the reload animations, so
treat them as approximate. The game flags automatic weapons but not burst
fire. After a game update, rebuild the table:

```
py -I sulfur-tracker/weapons/build_weapons.py
```

### Building the SULFUR pages

All five builders read the game through `sulfur-tracker/game_files.py`.
They find SULFUR through Steam; pass the install folder if that fails.
Install their two packages once:

```
py -m pip install UnityPy dnfile
```

Each builder writes its data file and an `icons/` folder beside its page.
The repo keeps the data files. Git ignores the icon folders, because
someone could reuse the game's art elsewhere, so a page shows icons only
after you run its builder.

## SULFUR save editor

`sulfur-tracker/save-editor/save_edit.py` changes a SULFUR save slot. It
sets the amulet charge, the stamps, and the ammo in the backpack or the
church stash. For stamps, `stamps 50` sets the count, and `stamps +20`
adds to it.
The script also adds, removes, moves, and repairs items in the backpack and
each stash. Every command that changes a save is a dry run until you add
`--apply`.

The game reads a save only when you pick its slot, and then overwrites the
file each time it saves. During a run, the next save wipes out an edit.
To apply a change, quit to the main menu and add `--game-open`, or quit the
game. Without the flag, the script refuses to write while SULFUR runs.

```
py -I sulfur-tracker/save-editor/save_edit.py -s 3 show
py -I sulfur-tracker/save-editor/save_edit.py -s 3 amulet 5 --apply
py -I sulfur-tracker/save-editor/save_edit.py -s 3 add stash "Low Fat Milk" --apply
```

Run it with `-h` for every command. Every command but `slots` and `find`
needs `-s N` (or `--slot N`), before or after the command. The `grid`
command draws a grid with the item number in each filled cell. `remove`
and `move` take the same numbers, and `--x` marks filled cells with x
instead. In a terminal, item names and grid cells show in their item
type's color, and the `grid` command prints a key of the types. For plain
text, add `--no-color` before the command or set `NO_COLOR`.

To find an item to add, search its name with `find`, or list a type of item
with `find --type`, such as `attachment`, `oil`, or `crafting`. Run
`find --types` for every type.

To swap items for another item, use `convert`. The new items fill the space
each old item used. For example, `convert backpack "Health Potion" --type food`
turns each food in the backpack into Health Potions, one per cell, so a 1x2
food becomes two potions. Give `all` in place of a grid for every grid, or
item numbers in place of `--type`. For one new item per old item, add
`--one`.

To ready the backpack for a run in one write, use `restock`:

```powershell
py .\save-editor\save_edit.py -s 3 restock --apply
```

It takes the food and organs out of the backpack, repairs every grid, and sets
carried ammo to the caps. Each empty hotbar slot (the gadget slots
on keys 3 to 5) gets a First Aid Kit, and full ones keep their item.
`--hotbar NAME` picks another item, and `--hotbar none` skips the step.

Then `restock` tops the backpack up to 3 repair kits
and fills every free cell with Health Potions. The kits go in before the
potions, so they always get room. To keep a different number of kits, add
`--kits N`, and `--kits 0` skips them. For another item than Health Potion,
add `--item NAME`.

To get the Escape card, the one Endless card that sends you back to the
church, use `endless escape`. It banishes every other card for the rest of
the run, so the next level-up deals Escape. Taking the card in game also
updates the Endless records. `endless` alone shows the card pool and the
odds. `endless rerolls N` and `endless banishes N` set what the run has left.

To end an Endless run without the Escape card, use `leave-endless`. It clears the same run state the card clears, so the slot
loads at the church with the backpack as the game last saved it. The run's
card upgrades end, as they do with the card. The Endless records keep their
old values, since the game updates them only during a run.

Before each write, the script copies the slot to `save-editor/backups/`.
To undo an edit or a bad run, `revert` lists every earlier copy of the slot.
It finds the script's backups and the game's own, newest first, and
`revert N --apply` puts copy N back.

A loadout is a saved set of equipped items, or the contents of one
container. `loadout save NAME` keeps what a slot has equipped, and
`loadout save NAME GRID` keeps a container. `loadout apply NAME` puts
copies of those items back, each with its enchantments, attachments, and
durability. Items it displaces move to the stash, or to the grid that
`--to` names. With a container, `--replace` empties it first. The amulet
stays out of loadouts.

The script keeps the game's limits: the amulet holds 5 charges, and the backpack
holds a set amount of each caliber. It places new
items only in free cells, because the game drops an item that overlaps
another. Leave achievement progress alone: an edit there can unlock
achievements on your Steam account.

## Not in the repo

The tracker writes each game's Steam snapshot (`steam_status.js`), icons,
header image, and page copy into the game folder. `.gitignore` excludes them:
the snapshot holds your SteamID and unlock history, and the rest regenerates.
