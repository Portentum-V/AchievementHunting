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

The recipes come from the SULFUR wiki. After a game update, rebuild them:

```
py -I sulfur-tracker/recipes/build_recipes.py
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

Stats and sell values come from the SULFUR wiki. Reload time and attachment
slots come from sulfurbuild.com, because the wiki leaves them out. Neither
source lists weapon quality. After a game update, rebuild the table:

```
py -I sulfur-tracker/weapons/build_weapons.py
```

## Not in the repo

The tracker writes each game's Steam snapshot (`steam_status.js`), icons,
header image, and page copy into the game folder. `.gitignore` excludes them:
the snapshot holds your SteamID and unlock history, and the rest regenerates.
