# RESUME 2026-10-01 (night) — affix branch verified, ready to merge

Start here in a fresh session. Branch `affix-abbreviation-rules` (HEAD `7b9d346`), unmerged and unpushed. Environment: `env/bin/python`,
`PYTHONPATH=.`, long runs with `PYTHONUNBUFFERED=1` in the background, ONE heavy job at a time (7 GB RAM); wait on a PID with
`timeout 595 tail --pid=PID -f /dev/null`. Never commit/push/merge without an explicit request.

## State

- Stage S9 (Affix Abbreviation Building) is complete and committed: S9a rule selection, S9b affix dictionary, the interactive review.
- This session's commits: `c468ad2` (review asks growth before fusion; fused merges inherit their parts' growth; the review loops by itself,
  reselecting after each pass; `MAX_ALTERNATIVES` 5 -> 30), `6f3be10` (regenerated affix data), `7b9d346` (`docs/AFFIX_DESIGN.md`).
- **Full rebuild verified (2026-10-01, 1,734 s):** `rm -f *.pickle` (all four, `AffixSelection.pickle` included), then `python dictionary.py`
  ran every step ok. Every output was byte-identical to the committed files: `phonetic_theory.tsv`, `disambiguated_theory.tsv`,
  `resolved_press_sets.json`, `keypress_groups.json`, `realization_report.json`, `plover_stenalgo_dictionary.json`,
  `steno-trainer/public/data/*.json`, `affix_rules.json`, `affix_rules_report.md`, `plover_stenalgo_affix_dictionary.json`,
  `affix_abbreviations.tsv`; `git status` shows no tracked change. The affix selection is deterministic from scratch (S9a 1,497 s).
  No question was asked: `affix_decisions.json` and `elicitation_answers.json` were kept.
- Gates: 758 tests pass; `mypy src/` 127 errors (unchanged, pre-existing).
- Result: 30 rules, 72,204 abbreviations for 80,473 carrier words, strokes saved x frequency 116,720; nothing pending.
- Docs: `docs/AFFIX_DESIGN.md` (philosophy, design choices, algorithms), `docs/AFFIX_RULES.md` (operational reference), `docs/PIPELINE.md`.

## Decisions for you (recommendation first)

1. **Merge to main.** Recommended. It is a direct merge (your convention), then rerun `pytest src/test/`. The branch is large (522 files, mostly
   scratch/ and resource data), so check `git diff --stat main...HEAD -- . ':!scratch'` before merging. Push only on a separate request.
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
