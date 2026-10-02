# RESUME 2026-10-02 — affix layer (S9) MERGED and PUSHED; what is left

Start here in a fresh session (Sonnet is fine). Repo `/home/jfsp/stenalgo`, branch `main`, HEAD `3c644af` (pushed to origin; GitHub Pages deploy of the
steno-trainer succeeded). Environment: `env/bin/python`, `PYTHONPATH=.`, long runs with `PYTHONUNBUFFERED=1` in the background, ONE heavy job at a time
(7 GB RAM); wait on a PID with `timeout 595 tail --pid=PID -f /dev/null`. Never commit/push without an explicit request. Branch
`affix-abbreviation-rules` still exists locally (merged; may be deleted if the user agrees).

## Mission
Affix Abbreviation Building (S9) gives the stable theory an OPTIONAL second Plover dictionary of shorter outlines (30 affix rules, one keypress each).
It is done; the remaining work is a learner trial and the non-affix items below. Docs: `docs/AFFIX_DESIGN.md` (why), `docs/AFFIX_RULES.md` (how).

## State (verified 2026-10-01/02)

- Full rebuild from nothing (`rm -f` all four pickles, `python dictionary.py`, 1,734 s): every output byte-identical to the committed files, no question asked.
- After the merge with main (which added the lessons exporter): 1,005 tests pass; `mypy src/` 140 errors = 127 old + 13 in main's lessons code
  (`src/test/lessons_test.py`, `util/export_lessons.py`), none in affix files. `dictionary.py` was NOT rerun after the merge (main only added the
  lessons exporter, no lexicon/layout change, so the affix outputs stay valid).
- Result: 30 rules, 72,204 abbreviations for 80,473 carrier words, strokes saved x frequency 116,720; nothing pending.
- Outputs at the repo root: `plover_stenalgo_affix_dictionary.json` (usable Plover dictionary), `affix_abbreviations.tsv`, `affix_rules.json`,
  `affix_rules_report.md`; verdicts in `affix_decisions.json` (committed input; keep it with `elicitation_answers.json` when deleting pickles).
- Untracked `scratch/` snapshots are intentional; never `git clean -x`.

## Decisions for the user (recommendation first; ask, do not guess)

1. **Delete the merged local branch `affix-abbreviation-rules`?** Ask the user.
2. **Untracked files.** `scratch/` holds many untracked snapshots (`*-before/`, pickles, logs) and is never cleaned with `git clean -x`.
   Recommended: leave them. Old `RESUME_2026-09-*` / `PLAN_*` / `DESIGN_*` notes at the repo root are historical (marked so); moving them to
   `docs/history/` would tidy the root, only if you want it.
3. **Key search is not proven exhaustive.** With 30 finalists it fixed the 3 known misses (`a|ah|ha|hâ|â` +3%, `am|an|...` +2%,
   `de|des|dé|déh` +7%); the best key for `am|an|...` was found at 7,324 whereas a top-60 check found 7,342, so a miss of about 0.25% remains
   possible. Recommended: leave it; if you want certainty, evaluate all 1,751 keys on all carriers for the 15 rules above the 2,000-word sample
   (`scratch/keysearch_misses.py` is the starting point) and compare, costing hours of machine time.
4. **Learnability is untested.** No learner has used the 30 rules. Recommended: before any further tuning, try a handful of rules by hand with
   `plover_stenalgo_affix_dictionary.json` as a second, higher-priority Plover dictionary and report which rules are hard to remember.
5. **Budget of 30.** If the trial in 4 says some rules are not worth their memory cost, lower `RULE_BUDGET`; the selection reruns in about 20
   minutes (the cache is keyed on the budget). Do not split rules into several keys (rejected 2026-09-29).

## Other open items (not affix)

- Duplicate rule-examples line in the Lessons UI (steno-trainer).
- Vowel harmony: `chopper`, the blank-gender NOM audit.
- Lessons: the "homophone badge" idea (exponent = number of `*`/`#` homophones per word).
- Suspected bugs in `TODO.md`.

## Reminders

- After a lexicon or layout change: `rm -f *.pickle` (including `AffixSelection.pickle`), rebuild with `python dictionary.py`; only
  `affix_decisions.json` and `elicitation_answers.json` (committed inputs) are kept. A changed spelling set re-opens a merge as PENDING:
  `python -m util.review_affix_rules` (loops by itself).
- Growth is asked before fusion; a merge inherits its parts' growth (`Decisions.growthForms`).
- `MAX_ALTERNATIVES` and the other prices are part of the cache fingerprint (`currentWeights`): changing one forces a full reselection.
