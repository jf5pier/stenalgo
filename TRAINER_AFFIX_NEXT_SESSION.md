# Next session: finish the affix trainer (branch `affix-trainer`)

Start by reading `TRAINER_AFFIX_LEFTOVERS.md` (state, unverified items, open questions) and
`/home/jfsp/.claude/plans/create-a-plan-for-iridescent-snail.md` (the original plan). Python is `env/bin/python`.
Do not push or merge without being asked.

## State
Steps 0-5 of the plan are done and committed (5 commits after `ce7a517`, plus the leftovers file). pytest 1024 pass,
golden md5s of the existing trainer JSONs and affix outputs unchanged. `steno-trainer/public/data/affix-lessons.json`
is committed and deterministic.

## To do, in order
1. Ask the user the 4 open questions of the leftovers file (alternates schema, verb-lesson duplicates, legend timing,
   rule-specific text) unless they answered already; apply the answers (exporter in `util/export_affix_lessons.py`,
   tests in `src/test/affix_lessons_test.py`, Elm in `steno-trainer/src/{Drill,Lessons,Main,Keyboard}.elm`, then
   `python -m util.export_affix_lessons` and re-commit the JSON).
2. If the user has Elm 0.19.2 available: `cd steno-trainer && elm make src/Main.elm --output=main.js` and `--optimize`
   (this machine only has 0.19.1; compile a scratch copy with `elm.json` patched, do not commit that change).
3. Have the user do the manual browser check listed in the leftovers file; fix what they report.
4. After `python -m pytest src/test -q` and the md5 comparison against `tmp/trainer_golden/` (untracked), tidy: delete the
   two TRAINER_AFFIX_*.md files once resolved (or fold into docs), then ask whether to merge `affix-trainer` into `main`.

## Out of scope (unchanged)
Learner progress, free-drill affix mode, teaching exceptions, elm-test, deploying, the learner trial (`scratch/affix_trial.md`).
