# Fact-check brief template

Fill in the `<...>` fields. Send the brief to a `general-purpose` agent that
did not write the guide.

---

Fact-check a sample of tips in an achievement guide for <GAME> (Steam app
<APPID>). Another agent wrote the guide. Your job is to find wrong tips, not
to defend them.

## Input
- The guide: `<REPO>\<slug>-tracker\guide.js`. Each key under `achievements`
  is a lower-cased Steam API name. `tip` is a string or an array of
  paragraphs, and `steps` is a checklist.
- The Steam list: `<LIST.json>`. Read it with `py -I` and
  `sys.stdout.reconfigure(encoding="utf-8")`.

## Task
1. Pick 10 locked achievements that have a tip. Weight the
   sample toward the riskiest claims: exact numbers, locations, required
   conditions, missables, codes, and content newer than a year. Include at
   least two claims the guide states as certain, that is, with no hedge
   such as "uncertain" or "sources do not say".
2. For each one, find an independent source: the game's wiki, a Steam guide
   or discussion, or patch notes. The guide's header comment lists the
   sources it used. Prefer a source outside that list. When the only source
   is one the guide already cites, say so in the verdict line. When
   WebFetch returns 429, 403 or a JavaScript-only page, use `curl` with a
   browser user agent. Save each download in a new, empty folder under
   `<SCRATCHPAD>`.
3. Give each sampled tip one verdict:
   - **confirmed**: a source supports every concrete claim in the tip.
   - **wrong**: a source contradicts a claim. Quote the source and give the
     correct fact.
   - **unverifiable**: no source supports or contradicts the claim. Note
     whether the tip already says it is uncertain.
4. Check every run plan or playthrough plan in the guide, in addition to the
   10. A plan is a checklist or tip that stacks several achievements in one
   run. Walk it step by step, and look for an order the game does not allow.
   Examples: a portal that leads elsewhere, a choice that ends the run
   early, a step that locks a later one. In an earlier test, a plan failed this way, and
   the sample of single tips missed it.

## Rules
- Do not edit any file. Report only.
- Judge only what a source says. Do not use your own memory of the game as
  proof.

Report back with these items:
- one line per sampled achievement: key, verdict, source URL, and the
  correction for each wrong tip;
- one verdict per plan, with the failing step and a fix;
- the counts per verdict.
