"""Log in to Steam once and keep an authenticated web session.

The login runs through the WebAuth class of the steam package, using Steam's
IAuthenticationService flow as a web-browser login. The password is never
stored. The refresh token (valid for about 30 days) and the current access
token (valid for about 24 hours) go into the OS credential store through
keyring. A small JSON file holds the non-secret account details.

Steam answers GenerateAccessTokenForApp with AccessDenied for web-browser
refresh tokens, so renewal follows the browser: finalizelogin trades the
refresh token for a one-time nonce, and settoken turns it into a new
steamLoginSecure cookie that carries the new access token.
"""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

import keyring
import keyring.errors
import requests
import steam.webauth as wa
from steam.enums.proto import EAuthTokenPlatformType, ESessionPersistence

SERVICE = "steam-achievements"
CONFIG_DIR = Path(os.environ.get("APPDATA") or Path.home() / ".config") / "steam-achievements"
ACCOUNT_FILE = CONFIG_DIR / "account.json"
FINALIZE_URL = "https://login.steampowered.com/jwt/finalizelogin"
SETTOKEN_URL = "https://steamcommunity.com/login/settoken"
BROWSER_HEADERS = {"Origin": "https://steamcommunity.com", "Referer": "https://steamcommunity.com/"}
REFRESH_MARGIN = 300  # refresh the access token when it has less than 5 minutes left
COOKIE_DOMAINS = ("steamcommunity.com", "store.steampowered.com", "help.steampowered.com")


class NotLoggedIn(Exception):
    """No usable login. Run `py -m steam_achievements login`."""


@dataclass
class Account:
    username: str
    steamid: str


class _WebBrowserAuth(wa.WebAuth):
    """WebAuth that requests a web-browser token.

    The upstream class asks for a SteamClient token. Steam renews web-browser
    refresh tokens over plain HTTPS, while SteamClient tokens need a
    connection to the Steam network. The fields match upstream otherwise.
    """

    def _startSessionWithCredentials(self, account_encrypted_password, time_stamp):
        resp = self.send_api_request(
            {"device_friendly_name": "steam-achievements (Python)",
             "account_name": self.username,
             "encrypted_password": account_encrypted_password,
             "encryption_timestamp": time_stamp,
             "remember_login": "1",
             "platform_type": EAuthTokenPlatformType.WebBrowser,
             "persistence": ESessionPersistence.Persistent,
             "website_id": "Community"},
            "IAuthentication", "BeginAuthSessionViaCredentials", 1)
        try:
            r = resp["response"]
            self.client_id = r["client_id"]
            self.request_id = r["request_id"]
            self.steam_id = wa.SteamID(r["steamid"])
            self.allowed_confirmations = [
                wa.EAuthSessionGuardType(c["confirmation_type"]) for c in r["allowed_confirmations"]]
        except KeyError as e:
            # Steam answers a wrong username or password with an empty response.
            if not resp.get("response") or resp["response"].get("interval") == wa.EResult.InvalidPassword:
                raise wa.LoginIncorrect("Steam rejected the username or password.")
            raise wa.WebAuthException(e, resp)


def _key(steamid: str, kind: str) -> str:
    return f"{steamid}:{kind}"


def _jwt_claims(token: str) -> dict:
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def load_account() -> Account | None:
    try:
        data = json.loads(ACCOUNT_FILE.read_text(encoding="utf-8"))
        return Account(data["username"], data["steamid"])
    except (OSError, ValueError, KeyError):
        return None


def login(username: str | None = None) -> Account:
    """Log in interactively and store the tokens. Prompts for Steam Guard when needed."""
    username = username or input("Steam username: ").strip()
    password = getpass(f"Password for {username}: ")
    auth = _WebBrowserAuth(username)
    auth.cli_login(username, password)

    steamid = str(auth.steam_id.as_64)
    keyring.set_password(SERVICE, _key(steamid, "refresh"), auth.refresh_token)
    keyring.set_password(SERVICE, _key(steamid, "access"), auth.access_token)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNT_FILE.write_text(json.dumps({"username": username, "steamid": steamid}, indent=2),
                            encoding="utf-8")
    return Account(username, steamid)


def logout() -> None:
    """Forget the stored tokens and account details."""
    account = load_account()
    if account:
        for kind in ("refresh", "access"):
            try:
                keyring.delete_password(SERVICE, _key(account.steamid, kind))
            except keyring.errors.PasswordDeleteError:
                pass
    ACCOUNT_FILE.unlink(missing_ok=True)


def token_status() -> dict:
    """Describe the stored login without refreshing anything."""
    account = load_account()
    if not account:
        return {"logged_in": False}
    out = {"logged_in": True, "username": account.username, "steamid": account.steamid}
    for kind in ("refresh", "access"):
        tok = keyring.get_password(SERVICE, _key(account.steamid, kind))
        out[f"{kind}_expires"] = _jwt_claims(tok).get("exp") if tok else None
    return out


def refresh_access_token(account: Account) -> str:
    """Trade the refresh token for a new access token, the way a browser does."""
    refresh = keyring.get_password(SERVICE, _key(account.steamid, "refresh"))
    if not refresh:
        raise NotLoggedIn("No refresh token stored. Run: py -m steam_achievements login")
    if _jwt_claims(refresh).get("exp", 0) < time.time():
        raise NotLoggedIn("The Steam login expired. Run: py -m steam_achievements login")

    s = requests.Session()
    r = s.post(FINALIZE_URL, headers=BROWSER_HEADERS, timeout=20, files={
        "nonce": (None, refresh),
        "sessionid": (None, wa.generate_session_id()),
        "redir": (None, "https://steamcommunity.com/login/home/?goto="),
    })
    r.raise_for_status()
    body = r.json()
    transfer = next((t for t in body.get("transfer_info", []) if t.get("url") == SETTOKEN_URL), None)
    if not transfer:
        raise NotLoggedIn(f"Steam refused to renew the login ({body.get('error', 'no transfer')}). "
                          "Run: py -m steam_achievements login")
    params = {**transfer["params"], "steamID": body["steamID"]}
    r = s.post(SETTOKEN_URL, timeout=20, files={k: (None, str(v)) for k, v in params.items()})
    r.raise_for_status()
    cookie = s.cookies.get("steamLoginSecure", domain="steamcommunity.com")
    if not cookie:
        raise NotLoggedIn("Steam did not issue a new session. Run: py -m steam_achievements login")
    access = cookie.replace("%7C%7C", "||").split("||", 1)[1]
    keyring.set_password(SERVICE, _key(account.steamid, "access"), access)
    return access


def access_token(account: Account | None = None, force_refresh: bool = False) -> str:
    """Return a valid access token, refreshing it when it is about to expire."""
    account = account or load_account()
    if not account:
        raise NotLoggedIn("Not logged in. Run: py -m steam_achievements login")
    tok = keyring.get_password(SERVICE, _key(account.steamid, "access"))
    if force_refresh or not tok or _jwt_claims(tok).get("exp", 0) - REFRESH_MARGIN < time.time():
        tok = refresh_access_token(account)
    return tok


def get_session(force_refresh: bool = False) -> tuple[requests.Session, Account]:
    """Return a requests session logged in to the Steam websites, plus the account."""
    account = load_account()
    if not account:
        raise NotLoggedIn("Not logged in. Run: py -m steam_achievements login")
    tok = access_token(account, force_refresh)
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) steam-achievements/0.1"
    for domain in COOKIE_DOMAINS:
        s.cookies.set("steamLoginSecure", f"{account.steamid}%7C%7C{tok}", domain=domain, secure=True)
        s.cookies.set("sessionid", wa.generate_session_id(), domain=domain)
    return s, account
