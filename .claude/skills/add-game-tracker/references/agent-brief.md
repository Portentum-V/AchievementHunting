# Sub-agent brief template

Fill in the `<...>` fields. Send the brief to one `general-purpose` sub-agent
per game, in the background. Write the game-specific "Research" paragraph
yourself. Name the hard or unclear achievements from the pull summary there,
so the agent knows where to spend effort.

---

Write an achievement guide file for <GAME> (Steam app <APPID>) for the
user's offline achievement tracker.

## Context
Repo: `<REPO>` (git, public on GitHub). Each game has a
`<game>-tracker/guide.js` that sets `window.GUIDE`. A Python tracker serves a
page that merges the guide with the user's live Steam unlocks. It matches them
by lower-case Steam API name.
- Read `steam-achievements/README.md` (section "guide.js fields") for the format.
- Read `<MODEL>-tracker/guide.js` as the style model. For a roguelite or a
  long list, use `megabonk` or `ror2`. For a story game with endings and
  missables, use `bg3` or `dawnwalker`. For collection checklists, use `valheim`.
- The full list (API names, descriptions, hidden flags, global %, the user's
  unlocks) is at `<LIST.json>`: <N> achievements, <DONE> unlocked. Read it with
  `py -I` and `sys.stdout.reconfigure(encoding="utf-8")`; the Windows console
  is cp1252 and crashes on non-ASCII names.
- Completed achievements need only `cat`, plus a flag where one applies. Spend
  the effort on the <REMAINING> remaining ones.

## Research
<GAME-SPECIFIC: name the remaining achievements that need real detail. Look
for missables, single-run conditions and mutually exclusive endings. Also look
for DLC content and for collection lists that can become `steps` checklists.
Do not assert the game's version. Ask the agent to find the current build
and any announced major update.>

Use the game's wiki, Steam community guides (steamcommunity.com/sharedfiles)
and discussions, and patch notes, through WebSearch and WebFetch. When
WebFetch returns 429, 403 or a JavaScript-only page, use `curl` with a browser
user agent. Save each download in a new, empty folder in the scratchpad
(`<SCRATCHPAD>`). Where sources disagree or are thin, say so in the tip.
Never invent a detail.

Collect the practical catches, not only the rules. A player who follows a
tip must not fail on something the tip left out. For each remaining
achievement, look for these:
- codes, combinations and exact inputs, such as an artifact code or a
  password, written out in full;
- traps that end a run or waste an attempt: an item thief, a choice that
  locks a route;
- items, builds or settings that make the attempt much easier;
- timing windows, stated the right way round: what happens first, and how
  long you have.
In an earlier test, the most useful tips were codes and run-ending traps.

## Write
Create `<REPO>\<slug>-tracker\guide.js`:
- `appid: "<APPID>"`, `title`, a `titleAccent` that is a substring of the
  title, `subtitle: "Achievement tracker, synced from Steam"`, a `credit` line
  naming the sources, and `defaultStatus: "todo"`. Add a header comment with
  the source URLs.
- Pick `colors` (light and dark `accent` and `accent2`) that suit the game and
  differ from the existing guides. Grep `#[0-9a-f]{6}` across
  `*-tracker/guide.js` to see the colors already in use.
- `categories` grouped by how you unlock them. `flags` mark planning concerns
  such as single-run conditions, missables, endings, difficulty, DLC or co-op.
  A card holds one flag. When one flag makes the most useful third stat card,
  add a `highlight` for it.
- Every Steam API name appears exactly once as a lower-cased key, with no
  extra keys. Use `steps` for "do all of X" achievements and for routes.
  Mark entries with long checklists `wide: true`.
- When several achievements stack in one run, write a plan. Put it in a tip
  or a checklist on the most relevant card.

## Validate
Run `node <SKILL>\scripts\validate_guide.js <guide.js> <LIST.json>`. Fix the
guide until the script prints PASS. Report its output.

## Rules
- Create only that one file in the repo. Scratch files go in the scratchpad.
  Do not run git. Do not start the tracker server.
- Prose: active voice, short sentences, lead with the action. ASCII only:
  straight quotes and hyphens, no em dashes or curly quotes. No filler.
  State facts plainly, and mark uncertain ones as uncertain.
- Before you report, reread every unhedged claim. Hedge or cut any claim that
  no source you read states.
- Never put the user's SteamID, username or unlock data in the file.

Report back with these items:
- the file path, the categories with counts, and the flags;
- any playthrough or stacking plan, in brief;
- the sources (URLs) and the validation output;
- the achievements without reliable information.
