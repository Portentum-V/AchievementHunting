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
too, but the page leaves them out. After a game update, rebuild it:

```
py -I sulfur-tracker/scrolls/build_scrolls.py
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

All three builders read the game through `sulfur-tracker/game_files.py`.
They find SULFUR through Steam; pass the install folder if that fails.
Install their two packages once:

```
py -m pip install UnityPy dnfile
```

Each builder writes its data file and an `icons/` folder beside its page.
The repo keeps the data files. Git ignores the icon folders, because
someone could reuse the game's art elsewhere, so a page shows icons only
after you run its builder.

## Not in the repo

The tracker writes each game's Steam snapshot (`steam_status.js`), icons,
header image, and page copy into the game folder. `.gitignore` excludes them:
the snapshot holds your SteamID and unlock history, and the rest regenerates.
