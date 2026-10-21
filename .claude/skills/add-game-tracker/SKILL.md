---
name: add-game-tracker
description: Add a Steam game to the Achievement_Hunting trackers. When the user names a game or a store link and asks to add or track it, use this skill. It pulls the achievement list and playtime. One research sub-agent per game writes <game>-tracker/guide.js. You validate the guide, check the live page, and update the READMEs. You commit only on request.
---

# Add a game tracker

The repo is the folder that holds this skill's `.claude` folder. Normally it
is `%USERPROFILE%\OneDrive\Documents\Gaming\Achievement_Hunting`, a public
GitHub repo; a test copy works the same way. Each game needs only `<slug>-tracker/guide.js`; the
tracker generates everything else in the folder. `steam-achievements/README.md`
documents the `guide.js` fields.

`SKILL` below means this skill's folder:
`<repo>\.claude\skills\add-game-tracker`. `SCRATCH` means the session
scratchpad.

## Steps

1. **Get the app ID** from the store URL (`/app/<appid>/`). An agecheck URL
   works the same way. Pick a short slug, such as `bg3` or `ror2`.

2. **Check the login.** Run `py -m steam_achievements status` from the repo.
   An expired access token is fine; it renews itself. When the refresh token
   has expired, ask the user to run `! py -m steam_achievements login`. It
   prompts for a password and a Steam Guard code, so you cannot run it.

3. **Pull the list:**
   `py -I SKILL\scripts\pull_game.py <appid> SCRATCH\<appid>.json`.
   The summary prints the unlocked count, playtime, last-played date, and
   every remaining achievement.
   - When the user has 0 unlocks, check the playtime before you suspect the
     sync. Valheim read 0 because the user last played it before the game
     added achievements. When the summary says "last played never", use
     the unstarted-game line in the brief.

4. **Brief one sub-agent per game.** Fill in
   `SKILL\references\agent-brief.md`. Launch it as a `general-purpose` agent
   in the background. For several games, launch one agent per game in a single
   message. The user asked for this split: agents research, and you validate.
   - Name the hard remaining achievements in the brief's "Research"
     paragraph, so the agent spends its effort there.
   - Do not research the same game yourself while the agent runs.

5. **Validate each guide** when its agent reports back. Do not take the
   report on trust:
   - Run `node SKILL\scripts\validate_guide.js <slug>-tracker\guide.js SCRATCH\<appid>.json`.
     Fix the guide until the script prints PASS. The script compares the key
     set with Steam. It checks categories, flags, colors and ASCII. Every
     remaining achievement needs a tip. The user's SteamID and username must
     not appear.
   - Spot-check a few tips: an ending, a missable, a single-run condition.
     Flag anything that contradicts what you know.
   - Check the missables. The validator requires the top-level `missables`
     line and lists every `missable` entry. Resolve each missable warning:
     set a deadline, or set `missable: false`. Read the list against what
     you know of the game. A missable with no mark is the costliest gap.
   - When the agent says it corrected a fact in your brief, confirm the guide
     uses the corrected fact.

6. **Fact-check a sample.** The validator checks structure, not truth.
   - Fill in `SKILL\references\fact-check-brief.md`. Launch it as a second
     `general-purpose` agent, never the agent that wrote the guide.
   - It samples 10 tips on remaining achievements and checks each one against
     a source. Each tip gets one verdict: confirmed, wrong, or unverifiable.
     It also walks every run plan in the guide, step by step.
   - Fix every wrong tip and every failing plan step. When a tip is unverifiable and does not say so,
     mark it as unconfirmed.
   - Record the counts, such as "7 confirmed, 1 wrong, 2 unverifiable". The
     report and the run review use them. Also count the verdicts that rest
     only on a source the guide already cites; they confirm less.
   - Step 7 does not depend on the verdicts. Start it while this agent runs.
     The page reads `guide.js` on each load, so a later fix needs a reload only.

7. **Check the live tracker.**
   - Run `py -m steam_achievements.tracker --no-browser --port 8799` from the
     repo in the background.
   - Poll `http://127.0.0.1:8799/api/games` until the new game's `total` is
     not 0. The server syncs every game in folder order, so the new game can
     take 30 seconds or more. Poll every 3 seconds for up to 2 minutes. Until
     its sync ends, `steam_status.js` returns 404; ignore that. The endpoint
     returns a JSON list with one object per game, keyed by `appid`.
   - Open `/<slug>-tracker/` with Playwright and take a viewport screenshot.
     A full-page shot of a long guide shrinks too far to read. Check the
     heading, the counts against `pull_game.py`, the highlight card, and a
     checklist. Pass a relative filename such as
     `.playwright-mcp\<slug>.png`. Playwright accepts only paths in the repo,
     and `.gitignore` excludes `.playwright-mcp/`.
   - Stop the server by PID only. Find the PID with `netstat -ano` on port
     8799, confirm with `tasklist` that it is `python.exe`, then run
     `taskkill //F //PID <pid>`. Never kill processes by filter or by name.
     The background task then reports exit code 1; ignore it.

8. **Update the docs.** Add the game to the table in the top-level `README.md`
   and to "Used by" in `steam-achievements/README.md`. Keep both lists sorted
   by folder. Lint them with `py ~/.claude/standards/prose_lint.py <file>`.
   - Make these edits with the Edit tool, not a shell or Python one-liner.
     The "Used by" lines hold paths like `..\ror2-tracker`, and a string
     escape turns `\r` into a carriage return. The lint does not catch it.

9. **Review the run.** Improve the skill from what this run taught you.
   - List what went wrong or slowed you down. Examples: a blocked source, a
     validator gap, a brief that misled the agent, a step you had to work out.
   - For each item, edit `SKILL.md`, a script, or a brief template so the
     next run avoids it. Add a line to "Lessons from earlier runs" only for a
     lesson no step can encode.
   - Keep each edit small. Remove any step that proved useless.
   - Leave the edits uncommitted. The user reviews them in `git diff` and
     accepts or rejects them. Never commit a change to this skill unless the
     user asks.

10. **Report to the user.** Give the unlocked count, what the guide covers,
    the fact-check counts, and what nobody could confirm. List the skill
    edits from step 9. Ask before you commit.

11. **When the user asks, commit and push.**
   - Run `git add -A`, then `git status --short`. Expect only `guide.js`, the
     READMEs and any code fixes.
   - Grep the staged diff for the SteamID, the username, `eyJ` (JWT tokens)
     and `password`. Expect no matches.
   - Commit on `main` with the attribution line.
   - Push to `origin main`.

## Lessons from earlier runs

- **Personal data stays out of git.** `.gitignore` excludes `steam_status.js`,
  icons, `header.jpg` and the generated `index.html`. Keep it that way.
- **`py -I` ignores `PYTHONIOENCODING`.** Call
  `sys.stdout.reconfigure(encoding="utf-8")` in the script instead.
- **Fetching sources:** Steam guides return 429 to WebFetch, and several
  wikis return 401, 402 or 403. Fetch them with `curl` and a browser user
  agent, into an empty scratch folder.
- **Titles with apostrophes:** a title like "Baldur's Gate 3" once broke the
  hub title and the page heading. Commit `68df944` fixed both. A new failure of that
  kind belongs in `steam_achievements/tracker`, not in the guide.
- **Template changes:** the tracker copies the template into each game folder
  at startup. Restart the server after editing `tracker/index.html`.
- **Moving files:** never chain `rm -rf` after a move whose result you have
  not checked. An earlier session lost the library source that way.
