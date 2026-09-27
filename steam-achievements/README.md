# steam-achievements

Read your own Steam achievements, including unlock times, without making your
profile or game details public.

Steam shows every achievement as locked to visitors when your game details are
private. This library logs in as you, so it reads the real data.

## Install

```
py -m pip install -e %USERPROFILE%\OneDrive\Documents\Gaming\Achievement_Hunting\steam-achievements
```

Login uses the `WebAuth` class of
[solsticegamestudios/steam](https://github.com/solsticegamestudios/steam), a
maintained fork of ValvePython/steam. The original package stopped working
after Steam's 2023 login change.

## Log in once

```
py -m steam_achievements login
```

The command prompts for your username, your password, and a Steam Guard code
or mobile-app approval. It stores no password. The refresh token (valid 30
days) and the access token (valid 24 hours) go into Windows Credential Manager
under `steam-achievements`. `%APPDATA%\steam-achievements\account.json` holds
only your username and SteamID64.

The library renews the access token on its own, the way a browser does:
`login.steampowered.com/jwt/finalizelogin`, then `steamcommunity.com/login/settoken`.
Steam rejects `GenerateAccessTokenForApp` for web-browser tokens. When
`status` shows the refresh token near expiry, run `login` again.

## Command line

```
py -m steam_achievements status             # show the login and test it against Steam
py -m steam_achievements status --refresh   # force a token renewal
py -m steam_achievements get 3751260        # list your achievements for an app ID
py -m steam_achievements get 3751260 --json
py -m steam_achievements get 3751260 --public --steamid <id>   # public view, no login
py -m steam_achievements logout             # delete the stored tokens
```

Find a game's app ID in its Steam store URL.

## Python

```python
import steam_achievements as sa

game = sa.fetch(3751260)             # your own achievements
print(game.game, len(game.unlocked), "/", len(game.achievements))
for a in game.unlocked:
    print(a.name, a.unlocked_at)

sa.download_icons(game, "icons")     # cache icons for offline use
```

`fetch` raises `sa.NotLoggedIn` when it finds no valid login, and
`sa.SteamError` when Steam returns an error.

## Where the data comes from

| Data | Source | Login |
| --- | --- | --- |
| Full list, hidden ones included, API names, icons, global rates | `IPlayerService/GetGameAchievements` | No |
| Which achievements you unlocked | `IPlayerService/GetTopAchievementsForGames` | Access token |
| Unlock times | Your achievements page on steamcommunity.com, read in UTC | Cookie |

If the page parse fails, `fetch` still returns the unlocks, with empty times.

Do not use the community XML feed (`?xml=1`) for private data. Steam serves it
the public view even to a logged-in session. `fetch_public` uses that feed on
purpose, for other players' public profiles.

## Offline tracker pages

`steam_achievements.tracker` serves checklist pages that sync with Steam every
60 seconds. Start it from the `Achievement_Hunting` folder:

```
py -m steam_achievements.tracker          # hub of every game here, opens the browser
py -m steam_achievements.tracker --once   # sync every game once and exit
py -m steam_achievements.tracker megabonk-tracker   # one game only
```

With no folder argument, the tracker uses the current directory. A folder
whose subfolders hold `guide.js` files becomes a hub: the start page lists
each game with its progress, and each game opens at `/<subfolder>/`. A folder
that holds a `guide.js` itself serves that one game.

Each game folder needs only a `guide.js`. The tracker copies the page template
into the folder. It also caches icons, the store header image, and the last
Steam snapshot there, so `<folder>\index.html` opens offline from `file://`.
When a port is busy, the tracker takes the next free one.

### Build a tracker for a new game

1. Get the app ID from the store URL, then pull the list:
   `py -m steam_achievements get <appid> --json > list.json`. The list holds
   API names, descriptions, hidden flags, global rarity, and your unlocks.
2. Find guide content: a Steam community guide, a wiki, or IGN. Prefer a
   guide that groups achievements by how you unlock them. Spend the effort on
   the achievements you still lack.
3. Create `Achievement_Hunting\<game>-tracker\guide.js`. Key each entry by the
   lower-case Steam API name.
4. Check that every Steam API name appears exactly once in the guide.
   Achievements missing from the guide land in "Other".
5. Restart the tracker. The new game appears on the hub; compare its count
   with your Steam profile.

### guide.js fields

```js
window.GUIDE = {
  appid: "3405340",                 // required
  title: "Megabonk", titleAccent: "bonk",
  subtitle: "...", credit: "Tips from ...",
  defaultStatus: "todo",            // "all", "todo", or "done"
  storageKey: "...",                // optional; defaults to tracker-<appid>
  colors: { light: { accent, accent2 }, dark: { accent, accent2 } },
  flags: { run: { label: "Single run", tone: "accent" } },          // tone: accent or accent2
  highlight: { flag, label, note }, // third stat card; default: rarest remaining
  pointsLabel, pointsNote, pointsSuffix, // second stat card when entries have `g`
  categories: [["hats", "Hats"], ...],
  achievements: {
    a_hatcrown: { cat: "hats", flag: "run", wide: true,
      tip: "text, or an array of paragraphs",
      steps: ["checklist item", ...], g: 10 },
  },
};
```

## Used by

- `..\bg3-tracker` - Baldur's Gate 3 (tips from bg3.wiki and Steam community guides).
- `..\dawnwalker-tracker` - The Blood of Dawnwalker (tips from the IGN wiki).
- `..\dragonwilds-tracker` - RuneScape: Dragonwilds (tips from the RuneScape: Dragonwilds wiki).
- `..\megabonk-tracker` - Megabonk (tips from Steam community guides).
- `..\valheim-tracker` - Valheim (tips from a Steam community guide and its tracking sheet).
