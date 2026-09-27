# Achievement Hunting

Offline Steam achievement trackers that sync with your own account, private
game details included.

## Layout

- `steam-achievements/` - Python library and command line. It logs in to
  Steam, reads your achievements, and serves the tracker pages. Its README
  covers login and building a tracker for a new game.
- `<game>-tracker/guide.js` - one guide per game: categories, tips, and
  checklists, keyed by Steam API name.

| Folder | Game | Guide source |
| --- | --- | --- |
| `bg3-tracker` | Baldur's Gate 3 | bg3.wiki, Steam community guides |
| `dawnwalker-tracker` | The Blood of Dawnwalker | IGN wiki |
| `dragonwilds-tracker` | RuneScape: Dragonwilds | RuneScape: Dragonwilds wiki |
| `megabonk-tracker` | Megabonk | Steam community guides |
| `valheim-tracker` | Valheim | Steam community guide and its tracking sheet |

## Run

```
py -m pip install -e steam-achievements
py -m steam_achievements login
py -m steam_achievements.tracker
```

The last command opens a hub page that lists every game here. Run it from
this folder.

## Not in the repo

The tracker writes each game's Steam snapshot (`steam_status.js`), icons,
header image, and page copy into the game folder. `.gitignore` excludes them:
the snapshot holds your SteamID and unlock history, and the rest regenerates.
