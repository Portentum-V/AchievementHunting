"""Pull a game's achievement list and the user's playtime, for a new tracker.

Usage: py -I pull_game.py <appid> <out.json>

Writes the full list (API names, descriptions, hidden flags, global rarity,
the user's unlocks) to out.json and prints a summary: unlocked count,
playtime, last-played date, and every remaining achievement.
"""
import json
import sys
import time

import requests
import steam_achievements as sa
from steam_achievements import auth

sys.stdout.reconfigure(encoding="utf-8")  # names can hold non-ASCII; the console is cp1252


def playtime(appid: str) -> str:
    account = sa.load_account()
    if not account:
        raise SystemExit("Not logged in. Run: py -m steam_achievements login")
    steamid = account.steamid
    r = requests.get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params={"access_token": auth.access_token(), "steamid": steamid,
                "include_played_free_games": 1, "appids_filter[0]": appid},
        timeout=20,
    )
    games = r.json().get("response", {}).get("games", [])
    if not games:
        return "not owned on this account"
    g = games[0]
    last = g.get("rtime_last_played") or 0
    when = time.strftime("%Y-%m-%d", time.gmtime(last)) if last else "never"
    return f"{g['playtime_forever'] / 60:.1f} h played, last played {when}"


def main() -> None:
    appid, out = sys.argv[1], sys.argv[2]
    game = sa.fetch(int(appid))
    ach = game.achievements
    data = {
        "appid": appid, "game": game.game,
        "achievements": [
            {"api": a.api, "name": a.name, "description": a.description,
             "unlocked": a.unlocked, "hidden": a.hidden, "global_percent": a.global_percent}
            for a in ach
        ],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

    done = sum(a.unlocked for a in ach)
    print(f"{game.game} ({appid}): {done}/{len(ach)} unlocked; {playtime(appid)}")
    print(f"Saved the list to {out}")
    print("Remaining (API name | name | description | global %):")
    for a in ach:
        if not a.unlocked:
            hid = " | hidden" if a.hidden else ""
            print(f"  {a.api} | {a.name} | {a.description or ''} | {a.global_percent or 0:.1f}{hid}")


if __name__ == "__main__":
    main()
