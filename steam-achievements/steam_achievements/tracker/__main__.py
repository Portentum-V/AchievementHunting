"""Run offline achievement trackers.

Usage:
    py -m steam_achievements.tracker [folder]          Serve and open in the browser.
    py -m steam_achievements.tracker [folder] --once   Sync once and exit.

`folder` defaults to the current directory. A folder with a guide.js is one
game. A folder whose subfolders hold guide.js files is a hub: the start page
lists every game, and each game lives at /<subfolder>/.

Each game folder needs a guide.js that sets window.GUIDE, including `appid`.
The tracker copies the page template into the folder, caches icons in
<folder>/icons, and writes the last Steam snapshot to <folder>/steam_status.js,
so a game folder also works offline from file://. Pages re-poll Steam every
60 seconds while the server runs.
"""

import argparse
import errno
import functools
import http.server
import json
import re
import shutil
import socket
import threading
import time
import webbrowser
from pathlib import Path

import requests

from .. import achievements as ach

HERE = Path(__file__).parent
TEMPLATE = HERE / "index.html"
HUB_TEMPLATE = HERE / "hub.html"
HEADER_URL = "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"
APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
PORT = 8765
CACHE_SECONDS = 30
HUB_STALE_SECONDS = 300  # the hub page refreshes a game in the background after this long


class Tracker:
    def __init__(self, folder: Path):
        self.folder = folder
        self.slug = folder.name
        guide = folder / "guide.js"
        if not guide.exists():
            raise SystemExit(f"{guide} not found. Each tracker folder needs a guide.js.")
        text = guide.read_text(encoding="utf-8")
        m = re.search(r"""\bappid\s*:\s*["']?(\d+)""", text)
        if not m:
            raise SystemExit(f"{guide} has no appid.")
        self.appid = m.group(1)
        t = re.search(r"""\btitle\s*:\s*["']([^"']+)""", text)
        self.title = t.group(1) if t else self.slug
        self._lock = threading.Lock()
        self._at = 0.0
        self._data = None
        self._refreshing = False

    def install_page(self):
        shutil.copyfile(TEMPLATE, self.folder / "index.html")

    def fetch(self) -> dict:
        game = ach.fetch(self.appid)
        # download_icons returns a local file name, or the remote URL when a download fails.
        icons = {api: [n if "/" in n else "icons/" + n for n in pair]
                 for api, pair in ach.download_icons(game, self.folder / "icons").items()}
        self._cache_header()
        return {
            "error": None,
            "appid": self.appid,
            "game": game.game,
            "steamId": game.steamid,
            "fetchedAt": game.fetched_at,
            # guide.js keys achievements by lower-case API name
            "achievements": [{
                "api": a.api.lower(),
                "name": a.name,
                "desc": a.description,
                "unlocked": a.unlocked,
                "time": a.unlock_time,
                "hidden": a.hidden,
                "pct": a.global_percent,
                "icon": icons[a.api][0],
                "iconLocked": icons[a.api][1],
            } for a in game.achievements],
        }

    def _cache_header(self):
        path = self.folder / "header.jpg"
        if path.exists():
            return
        # Newer games keep the header under a hashed path that only appdetails reports.
        urls = [HEADER_URL.format(appid=self.appid)]
        try:
            r = requests.get(APPDETAILS_URL, params={"appids": self.appid, "filters": "basic"}, timeout=20)
            entry = next(iter(r.json().values()))
            urls.insert(0, entry["data"]["header_image"])
        except (requests.RequestException, ValueError, KeyError, TypeError, StopIteration):
            pass
        for url in urls:
            try:
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                path.write_bytes(r.content)
                return
            except requests.RequestException:
                continue  # the hub shows the title when no image loads

    def status(self, force=False) -> dict:
        with self._lock:
            if self._data is None or force or time.time() - self._at > CACHE_SECONDS:
                data = self.fetch()
                (self.folder / "steam_status.js").write_text(
                    "// Written by steam_achievements.tracker. Last Steam snapshot for offline use.\n"
                    "window.STEAM = " + json.dumps(data, indent=1) + ";\n", encoding="utf-8")
                self._data, self._at = data, time.time()
            return self._data

    def snapshot(self) -> dict | None:
        """Return the latest data without contacting Steam: memory first, then steam_status.js."""
        if self._data:
            return self._data
        path = self.folder / "steam_status.js"
        try:
            text = path.read_text(encoding="utf-8")
            return json.loads(text[text.index("{"):text.rstrip().rindex(";")])
        except (OSError, ValueError):
            return None

    def refresh_in_background(self):
        if self._refreshing or time.time() - self._at < HUB_STALE_SECONDS:
            return
        self._refreshing = True

        def run():
            try:
                self.status()
            except Exception:
                pass  # the game page reports sync errors itself
            finally:
                self._refreshing = False
        threading.Thread(target=run, daemon=True).start()

    def summary(self) -> dict:
        snap = self.snapshot() or {}
        items = snap.get("achievements", [])
        left = sorted((a for a in items if not a["unlocked"] and a.get("pct") is not None),
                      key=lambda a: a["pct"])
        return {
            "slug": self.slug, "title": self.title, "appid": self.appid,
            "header": "header.jpg" if (self.folder / "header.jpg").exists() else None,
            "unlocked": sum(a["unlocked"] for a in items), "total": len(items),
            "fetchedAt": snap.get("fetchedAt"), "error": snap.get("error"),
            "rarest": {"name": left[0]["name"], "pct": left[0]["pct"]} if left else None,
        }


def discover(root: Path) -> tuple[list[Tracker], bool]:
    """Return the trackers under `root` and whether `root` is a hub."""
    if (root / "guide.js").exists():
        return [Tracker(root)], False
    games = [Tracker(d) for d in sorted(root.iterdir()) if (d / "guide.js").exists()]
    if not games:
        raise SystemExit(f"No guide.js in {root} or its subfolders.")
    return games, True


class Handler(http.server.SimpleHTTPRequestHandler):
    trackers: dict = {}  # slug -> Tracker; "" for a single game served at /
    hub = False

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if self.hub and path in ("/", "/index.html"):
            return self._send(200, HUB_TEMPLATE.read_bytes(), "text/html; charset=utf-8")
        if self.hub and path == "/api/games":
            games = list(self.trackers.values())
            for t in games:
                t.refresh_in_background()
            return self._json(200, [t.summary() for t in games])
        m = re.fullmatch(r"/(?:([^/]+)/)?api/steam", path)
        if m:
            tracker = self.trackers.get(m.group(1) or "")
            if not tracker:
                return self._json(404, {"error": "Unknown game."})
            try:
                return self._json(200, tracker.status(force="force=1" in self.path))
            except Exception as e:  # report any fetch failure to the page
                return self._json(502, {"error": str(e)})
        super().do_GET()

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        if "/api/" not in self.path:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "/api/" not in self.path:
            super().log_message(fmt, *args)


class ExclusiveServer(http.server.ThreadingHTTPServer):
    """Refuse ports another process holds.

    HTTPServer sets SO_REUSEADDR, and on Windows that lets a second server bind
    a port already in use. Both then answer, so one tracker can show another's
    data. Exclusive binding makes the port fallback work.
    """
    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def serve(root: Path, trackers: list[Tracker], hub: bool, port: int, open_browser: bool):
    table = {t.slug: t for t in trackers} if hub else {"": trackers[0]}
    handler = functools.partial(type("H", (Handler,), {"trackers": table, "hub": hub}), directory=str(root))
    for p in range(port, port + 20):  # another tracker may hold the default port
        try:
            server = ExclusiveServer(("127.0.0.1", p), handler)
            break
        except OSError as e:
            if e.errno not in (errno.EADDRINUSE, errno.EACCES) and getattr(e, "winerror", None) not in (10048, 10013):
                raise
    else:
        raise SystemExit(f"No free port between {port} and {port + 19}.")
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Tracker running at {url}  (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    # Sync in the background so the page opens at once. A page's first poll waits on the same lock.
    threading.Thread(target=lambda: [initial_sync(t) for t in trackers], daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def initial_sync(tracker: Tracker) -> bool:
    try:
        data = tracker.status(force=True)
    except Exception as e:  # the page shows the same error on its next poll
        print(f"{tracker.title}: Steam sync failed: {e}", flush=True)
        return False
    got = sum(a["unlocked"] for a in data["achievements"])
    print(f"{data['game']}: {got}/{len(data['achievements'])} unlocked on Steam.", flush=True)
    return True


def main(argv=None):
    p = argparse.ArgumentParser(prog="steam_achievements.tracker", description=__doc__.splitlines()[0])
    p.add_argument("folder", type=Path, nargs="?", default=Path("."))
    p.add_argument("--once", action="store_true", help="sync once and exit")
    p.add_argument("--no-browser", action="store_true", help="do not open a browser")
    p.add_argument("--port", type=int, default=PORT)
    args = p.parse_args(argv)

    root = args.folder.resolve()
    trackers, hub = discover(root)
    for t in trackers:
        t.install_page()
    if args.once:
        results = [initial_sync(t) for t in trackers]
        if not all(results):
            raise SystemExit(1)
    else:
        serve(root, trackers, hub, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
