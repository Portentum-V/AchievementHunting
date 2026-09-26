"""Command line: py -m steam_achievements {login,logout,status,get}."""

import argparse
import json
import sys
from datetime import datetime

from . import achievements, auth


def _when(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "-"


def cmd_login(args):
    account = auth.login(args.username)
    print(f"Logged in as {account.username} ({account.steamid}). Tokens saved to the credential store.")


def cmd_logout(args):
    auth.logout()
    print("Stored Steam login removed.")


def cmd_status(args):
    if args.refresh:
        auth.access_token(force_refresh=True)
    s = auth.token_status()
    if not s["logged_in"]:
        print("Not logged in. Run: py -m steam_achievements login")
        return 1
    print(f"Account:         {s['username']} ({s['steamid']})")
    print(f"Access token:    expires {_when(s['access_expires'])}")
    print(f"Refresh token:   expires {_when(s['refresh_expires'])}")
    session, account = auth.get_session()
    who = achievements.whoami(session)
    print(f"Web session:     {'logged in' if who == account.steamid else 'NOT accepted by Steam'}")
    return 0 if who == account.steamid else 1


def cmd_get(args):
    game = (achievements.fetch_public(args.appid, args.steamid) if args.public
            else achievements.fetch(args.appid, args.steamid))
    if args.json:
        json.dump(game.to_dict(), sys.stdout, indent=1)
        print()
        return
    print(f"{game.game}: {len(game.unlocked)}/{len(game.achievements)} unlocked"
          f"{'' if game.authenticated else ' (public view)'}")
    for a in sorted(game.achievements, key=lambda a: (not a.unlocked, a.unlock_time or 0, a.name)):
        mark = "x" if a.unlocked else " "
        print(f"  [{mark}] {a.name:<34} {_when(a.unlock_time) if a.unlocked else ''}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="steam_achievements", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("login", help="log in once and store tokens")
    s.add_argument("username", nargs="?")
    s.set_defaults(fn=cmd_login)
    sub.add_parser("logout", help="forget the stored login").set_defaults(fn=cmd_logout)
    s = sub.add_parser("status", help="show the stored login and test it")
    s.add_argument("--refresh", action="store_true", help="force a token refresh first")
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("get", help="list achievements for a game")
    s.add_argument("appid")
    s.add_argument("--steamid", help="another player's SteamID64 (default: you)")
    s.add_argument("--public", action="store_true", help="skip login and read the public page")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_get)
    args = p.parse_args(argv)
    if args.cmd == "get" and args.public and not args.steamid:
        p.error("--public needs --steamid")
    try:
        return args.fn(args) or 0
    except auth.NotLoggedIn as e:
        print(e, file=sys.stderr)
        return 2
    except achievements.SteamError as e:
        print(e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
