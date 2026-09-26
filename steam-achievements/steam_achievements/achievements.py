"""Fetch a player's achievements for one game.

Three Steam sources feed `fetch`:

- IPlayerService/GetGameAchievements (no login) gives the full list, including
  hidden achievements, with API names, icons, and global unlock rates.
- IPlayerService/GetTopAchievementsForGames, called with your access token,
  gives the achievements you have unlocked, even with private game details.
- Your logged-in achievements page gives unlock times. It is the only source
  that has them. Parsing is best effort: a failure leaves the times empty.

The community XML feed (?xml=1) is not used for private data. Steam serves it
the public view even to a logged-in session.
"""

from __future__ import annotations

import html
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import auth

API = "https://api.steampowered.com/IPlayerService/{}/v1/"
ICON_URL = "https://shared.fastly.steamstatic.com/community_assets/images/apps/{appid}/{icon}"
PAGE_URL = "https://steamcommunity.com/profiles/{steamid}/stats/{appid}/achievements/?l={lang}"
XML_URL = PAGE_URL + "&xml=1"
WHOAMI_URL = "https://steamcommunity.com/chat/clientjstoken"
MAX_ACHIEVEMENTS = 10000  # GetTopAchievementsForGames returns at most this many unlocks


class SteamError(Exception):
    """Steam returned an error or an unexpected page."""


@dataclass
class Achievement:
    api: str  # API name as the game defines it, e.g. ACH_Selfish
    name: str
    description: str
    unlocked: bool
    unlock_time: int | None  # Unix seconds, when known
    icon: str  # colour icon URL
    icon_locked: str  # grey icon URL
    hidden: bool = False
    global_percent: float | None = None

    @property
    def unlocked_at(self) -> datetime | None:
        return datetime.fromtimestamp(self.unlock_time, timezone.utc) if self.unlock_time else None


@dataclass
class GameAchievements:
    appid: str
    game: str
    steamid: str
    fetched_at: int
    authenticated: bool
    achievements: list[Achievement] = field(default_factory=list)

    @property
    def unlocked(self) -> list[Achievement]:
        return [a for a in self.achievements if a.unlocked]

    def to_dict(self) -> dict:
        return asdict(self)


def _api(method: str, params: dict) -> dict:
    r = requests.get(API.format(method), params=params, timeout=30)
    if r.status_code in (401, 403):
        raise auth.NotLoggedIn("Steam rejected the access token. Run: py -m steam_achievements login")
    r.raise_for_status()
    return r.json().get("response", {})


def whoami(session: requests.Session) -> str | None:
    """Return the SteamID64 a web session is logged in as, or None."""
    r = session.get(WHOAMI_URL, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("steamid") if data.get("logged_in") else None


def schema(appid: int | str, language: str = "english") -> list[Achievement]:
    """Return every achievement of a game, all marked locked. Needs no login."""
    items = _api("GetGameAchievements", {"appid": appid, "language": language}).get("achievements", [])
    if not items:
        raise SteamError(f"Steam lists no achievements for app {appid}.")
    return [Achievement(
        api=a["internal_name"],
        name=a.get("localized_name", ""),
        description=a.get("localized_desc", ""),
        unlocked=False,
        unlock_time=None,
        icon=ICON_URL.format(appid=appid, icon=a["icon"]) if a.get("icon") else "",
        icon_locked=ICON_URL.format(appid=appid, icon=a["icon_gray"]) if a.get("icon_gray") else "",
        hidden=bool(a.get("hidden")),
        global_percent=float(a["player_percent_unlocked"]) if a.get("player_percent_unlocked") else None,
    ) for a in items]


_ROW = re.compile(r'<div class="achieveTxt">\s*<h3[^>]*>(.*?)</h3>\s*<h5>(.*?)</h5>\s*</div>\s*'
                  r'<div class="achieveUnlockTime">\s*(.*?)<br', re.S)
_TIME = re.compile(r"Unlocked (\w{3}) (\d{1,2})(?:, (\d{4}))? @ (\d{1,2}):(\d{2})([ap]m)")


def _parse_unlock(text: str, now: datetime) -> int | None:
    m = _TIME.search(text)
    if not m:
        return None
    mon, day, year, hour, minute, ampm = m.groups()
    hour = int(hour) % 12 + (12 if ampm == "pm" else 0)
    month = datetime.strptime(mon, "%b").month
    dt = datetime(int(year) if year else now.year, month, int(day), hour, int(minute), tzinfo=timezone.utc)
    if not year and dt > now:  # Steam omits the current year; December unlocks read in January
        dt = dt.replace(year=dt.year - 1)
    return int(dt.timestamp())


def unlock_times(session: requests.Session, steamid: str, appid, language="english") -> dict[str, int]:
    """Map achievement name to unlock time, read from the logged-in achievements page."""
    for d in auth.COOKIE_DOMAINS:
        session.cookies.set("timezoneOffset", "0,0", domain=d)  # page times in UTC
    r = session.get(PAGE_URL.format(steamid=steamid, appid=appid, lang=language), timeout=30)
    r.raise_for_status()
    now = datetime.now(timezone.utc)
    out = {}
    for name, _desc, when in _ROW.findall(r.text):
        ts = _parse_unlock(when, now)
        if ts:
            out[html.unescape(name).strip()] = ts
    return out


def fetch(appid: int | str, steamid: str | None = None, language: str = "english",
          times: bool = True) -> GameAchievements:
    """Fetch achievements as the logged-in account.

    With no `steamid`, reads your own achievements. Another player's data
    appears only when their game details are visible to you. Raises
    auth.NotLoggedIn when no valid login is stored.
    """
    account = auth.load_account()
    if not account:
        raise auth.NotLoggedIn("Not logged in. Run: py -m steam_achievements login")
    steamid = steamid or account.steamid
    token = auth.access_token(account)
    items = schema(appid, language)

    resp = _api("GetTopAchievementsForGames", {
        "access_token": token, "steamid": steamid, "language": language,
        "max_achievements": MAX_ACHIEVEMENTS, "appids[0]": appid})
    games = resp.get("games") or [{}]
    got = games[0].get("achievements", [])
    # Match on the icon file, which is unique per achievement; fall back to the name.
    got_icons = {g.get("icon") for g in got}
    got_names = {g.get("name") for g in got}
    for a in items:
        a.unlocked = a.icon.rsplit("/", 1)[-1] in got_icons or a.name in got_names
    if len(got) != sum(a.unlocked for a in items):
        raise SteamError(f"Matched {sum(a.unlocked for a in items)} of {len(got)} unlocked achievements.")

    if times and got:
        session, _ = auth.get_session()
        try:
            when = unlock_times(session, steamid, appid, language)
        except (requests.RequestException, ValueError):
            when = {}
        for a in items:
            if a.unlocked:
                a.unlock_time = when.get(a.name)

    return GameAchievements(
        appid=str(appid),
        game=_game_name(appid),
        steamid=steamid,
        fetched_at=int(time.time()),
        authenticated=True,
        achievements=items,
    )


def _game_name(appid) -> str:
    try:
        r = requests.get("https://store.steampowered.com/api/appdetails",
                         params={"appids": appid, "filters": "basic"}, timeout=20)
        # The store may answer under a different ID, such as an edition's.
        entry = next(iter(r.json().values()))
        return entry["data"]["name"]
    except (requests.RequestException, ValueError, KeyError, TypeError, StopIteration):
        return str(appid)


def fetch_public(appid: int | str, steamid: str, language: str = "english") -> GameAchievements:
    """Fetch achievements without logging in. Private game details read as all locked."""
    r = requests.get(XML_URL.format(steamid=steamid, appid=appid, lang=language), timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 steam-achievements/0.1"})
    r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        raise SteamError("Steam did not return achievement XML. The app ID may be wrong.") from e
    if root.findtext("error"):
        raise SteamError(f"Steam returned an error: {root.findtext('error')}")
    items = []
    for a in root.iter("achievement"):
        ts = (a.findtext("unlockTimestamp") or "").strip()
        items.append(Achievement(
            api=(a.findtext("apiname") or "").strip(),
            name=(a.findtext("name") or "").strip(),
            description=(a.findtext("description") or "").strip(),
            unlocked=a.get("closed") == "1",
            unlock_time=int(ts) if ts.isdigit() else None,
            icon=(a.findtext("iconClosed") or "").strip(),
            icon_locked=(a.findtext("iconOpen") or "").strip(),
        ))
    return GameAchievements(str(appid), root.findtext("game/gameName") or "", steamid,
                            int(time.time()), False, items)


def download_icons(game: GameAchievements, dest: str | os.PathLike) -> dict[str, tuple[str, str]]:
    """Save each icon into `dest` once. Return {api: (colour_file, grey_file)} as file names."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for a in game.achievements:
        names = []
        for url, suffix in ((a.icon, ""), (a.icon_locked, "_locked")):
            ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
            name = f"{a.api.lower()}{suffix}{ext}"
            path = dest / name
            if url and not path.exists():
                try:
                    r = requests.get(url, timeout=20)
                    r.raise_for_status()
                    path.write_bytes(r.content)
                except requests.RequestException:
                    name = url  # fall back to the remote URL
            names.append(name)
        out[a.api] = (names[0], names[1])
    return out
