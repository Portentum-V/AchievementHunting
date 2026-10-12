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
recipes one ingredient short. With the tracker running, open
`/sulfur-tracker/recipes/`. Without it, open `index.html` directly.

The recipes come from the SULFUR wiki. After a game update, rebuild them:

```
py -I sulfur-tracker/recipes/build_recipes.py
```

## Not in the repo

The tracker writes each game's Steam snapshot (`steam_status.js`), icons,
header image, and page copy into the game folder. `.gitignore` excludes them:
the snapshot holds your SteamID and unlock history, and the rest regenerates.
