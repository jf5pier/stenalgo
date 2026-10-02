# PLAN 2026-10-01 — affix pipeline integration: decisions and implementation (section 6 decided; AWAITING APPROVAL TO START CODING)

Follows `PLAN_2026-10-01-affix-pipeline-integration.md` (inventory). Branch `affix-abbreviation-rules`; no merge, no push without an explicit request.

## 0. Handoff for a fresh session (read this first)

- Read: this file, then `docs/AFFIX_RULES.md`, then `src/affixscopes.py`, `src/affixrules.py` (`resolveVariantRivals`, `selectRules`,
  `chooseRuleKeypress`), `util/affix_scan.py` (`selectAndBind`, `partSweep`, `main`), `src/affixabbrev.py`, `util/export_affix_dictionary.py`.
  The inventory `PLAN_2026-10-01-affix-pipeline-integration.md` is background only; sections 1, 2 and 6 here supersede its proposals.
- Environment: `env/bin/python` (bare `python` is not on PATH); `PYTHONPATH=.`; long runs with `PYTHONUNBUFFERED=1`, in the background,
  ONE heavy job at a time (7 GB RAM); wait on a background job by its PID or a log line, never `pgrep -f` in a loop.
- Gates: `env/bin/python -m pytest src/test/ -q` (740 pass at start); `env/bin/python -m mypy src/ | tail -1` (127 errors at start, must not grow).
- Do steps in order (section 5); finish each green before the next. STOP and report to the user (do not work around) when: a md5 that must
  stay identical changes; step 4 does not reproduce today's 30 rules and keys; a deletion in step 3 finds a live caller outside the affix code.
- Never commit, push or merge without the user's explicit request (branch `affix-abbreviation-rules`). Never touch S1-S8 code or
  `elicitation_answers.json`. Never `git clean -x` (untracked scratch pickles and baselines are needed).
- No interactive prompt may run inside `python dictionary.py`; only `util.review_affix_rules` asks questions.
- Report at the end: per step what changed, test count (lattice tests deleted on purpose), mypy count, md5 comparison, S9 timings.

## 1. Decisions (user, 2026-10-01)

1. **Growth and fusion are confirmed by the user, not by a numeric rule.** The algorithm proposes; for each proposal it shows how much it
   helps (words, frequency) and how much it hurts (fallbacks, hard exceptions, their frequency), plus learnability hints (pattern already used
   by another rule; added spelling already a spelling of another rule; two decided rules on one key). Examples of the judgement: `cé`+`m@`
   kept at +7 (other rules already grow on `m@`), `ssion`+`pRe` refused at +247 (few words, resembles no rule).
2. **Interactive terminal review**, a hand-run command; it writes the committed verdicts file.
3. **Cache convention**: the ~23-min selection reruns only when its output pickle is missing (`rm` to force, like `Dictionary.pickle`);
   the verdicts file is reused while it exists (like `elicitation_answers.json`). Nothing interactive inside `python dictionary.py`:
   an undecided item gets the safe default (merge kept apart, anchor alone), is listed as pending, and the run continues.
4. **No growth without a verdict; delete the generic lattice** and the `--legacy` path. The pool becomes the k=1 anchors, the variant
   merges and the decided growth forms.
5. **Own stage "Affix Abbreviation Building (S9)"** after Theory Export (S8), with rebuild-table row, md5 baseline and recompute entry.
6. **Trainer later**, separate branch.

## 2. Corrections to the inventory plan (verified in the code)

- Code map omits `src/affixbinding.py` (`PhonemeKeys`, `enumerateKeypresses` are live; the rest serves the legacy Part B).
- Two no-growth mechanisms: `NO_GROWTH_PREFIX_ORTHOS` (`src/affixes.py`) and the `[]` entries of `SCOPES`.
- Merged anchors are keyed by the exact `|`-joined spelling set of the greedy merge (`buildVariantMerges`): a lexicon change that adds or
  drops one variant changes the key and the decision silently stops applying.
- Ten of the 30 rules are merges never judged as fusions (`cer|cé|…|sé`, `ai|aî|e|…|é`, `ra|…|ré|réh`, `rae|…|rée`, `ser|sée|zer|zé`,
  `de|dea|di|…`, `e|hi|hy|i|y|î`, `re|reh`, `ain|hin|im|in`, `pro|proh|prô`…); some share spellings across rules (`ser`, `re`, `de`, `e`, `é`).
  They are migrated as "fused" (grandfathered) verdicts.
- Scopes and selection depend on each other (scopes decided on the H sweep's 30, then D reselected): the review loop below is that fixed point.
- `affix_rules.json` holds keys but not forms; editing the scopes silently changes the export under keys chosen for other forms.
- `RULE_PARTIAL_OVERLAP` ("experiment", default False) and the D weights are set by mutating module globals in the CLI and the exporter.
- The exporter rebuilds the whole lattice (~12k nodes) though the 30 rules are all scoped.
- The engine's default rival test fuses at any non-negative gain (`VARIANT_GROWTH_TOLERANCE = 0`); it contradicts the user's verdicts.
- Likely drift source (to confirm): lattice tie-breaks (`_reduceExceptions` `max` over dict order) follow record `idx`, i.e. theory iteration order.

## 3. Target flow

```
python dictionary.py   ... S8 ...
  S9a util.build_affix_rules     AffixSelection.pickle present (warn if its lexicon/layout fingerprint differs)
                                   made from the current affix_decisions.json -> reuse the final selection as is
                                   decisions changed -> reselect, reusing the cached per-rule evaluations (only rules whose
                                     forms/verdict changed, and new roots, are evaluated again, ~30 s each)
                                 absent -> pool (anchors + merges + decided forms) -> rivals by verdict (undecided: apart)
                                           -> select 30 -> bind keys -> AffixSelection.pickle, affix_rules.json, affix_rules_report.md
                                 prints PENDING items (undecided growth/fusion among the 30 selected rules)
  S9b util.export_affix_dictionary  plover_stenalgo_affix_dictionary.json, affix_abbreviations.tsv (as today)

hand-run: python -m util.review_affix_rules   reads the pickle, proposes each pending item, y/n/s/q, writes affix_decisions.json
          (never deletes the pickle); the next dictionary.py run reselects from the cache; repeat until nothing is pending.
```

Fingerprint stored in the pickle and in `affix_rules.json`: md5 of the two lexicons, `starboard3h.json`, `affix_decisions.json`
(the theory pickles are not fingerprinted, same as today). A lexicon/layout mismatch only WARNS (never an automatic rerun; `rm` the pickle for a full recompute, since cached
evaluations of the old lexicon are wrong). `affix_decisions.json` is NOT part of that check: its md5 is stored with the final
selection only, and a change triggers the cheap reselection above.

Per-rule cache (in the pickle): rule signature = (position, phono, spelling set, forms as strings, verdict) -> exact evaluation
(keys, score, benefit, exceptions, fallbacks, per-carrier gains by record idx). Valid only for a byte-identical pool, hence the
determinism work of step 3. Timing of the 2026-10-01 D sweep (1,415 s): variant rivals 336 s (exact merged-vs-main runs; vanishes
with verdict-only rivals), phase 3 1,072 s for 36 exact evaluations (~30 s each, 1,751 keypresses), swap + binding 2 s.

## 4. Files

New
- `affix_decisions.json` (committed): per anchor `{position, phono, spellings (the exact merge set), verdict: fused|apart|-, growth: [forms] | [] (no growth),
  refused: [proposal labels], note, date, numbers at decision time}`. Forms as strings (`label`, `anchors`, `sound`, `spelling`). Migrated
  one-to-one from `SCOPES`, `APPROVED_FUSIONS`, `NO_GROWTH_PREFIX_ORTHOS` and the refused fusions of `scratch/fusion-check-2026-10-01.md`.
- `src/affixdecisions.py` (replaces `src/affixscopes.py`): load/validate/save (atomic write), `ScopeForm`, `scopeFormsOf`, `fusionVerdict`
  (undecided -> "apart"), fingerprint helper. Unknown regex or duplicate key = load error.
- `src/affixproposals.py`: proposal generation and help/hurt evaluation, engine functions only (`simulate`, `resolveFallbacks`,
  `chooseRuleKeypress`, `ruleScoreFromResults`), no duplicated scorer.
  - fusion: merged vs apart on the rule's keys: added words/freq, fallbacks/freq, hard exceptions/freq, net; flags "spelling in rule X",
    "two decided rules".
  - growth: per anchor spelling, atoms from a fixed grammar on the neighbour's SOUND (onset {exact, C, C{1,2}, C*, [mn]} x nucleus
    {exact, vowel class, any}) plus exact-syllable literals; greedy, best net first; an accepted form is then offered its best extension
    (max ~4 atoms); refused labels are not asked again. Spelling-regex candidates (as `-ment`) shown only when they beat the best sound one.
    Flag "pattern already used by rule X". Sibling-spelling extension of an accepted form (the `der` case) generated automatically.
- `util/build_affix_rules.py`: S9a above (moves `selectAndBind` and the report writer out of `util/affix_scan.py`); persists the
  existing in-memory `ruleCache` of `src/affixrules.py` as the per-rule cache.
- `util/review_affix_rules.py`: the interactive prompt (format agreed: `helps N words freq F | hurts N fb freq F, N exc | net ±N | similar rule: …`,
  `accept? [y/n/s/q]`, optional note); saves after every answer; scope = the 30 selected rules (decision c).
- Tests: `src/test/affixdecisions_test.py`, `affixproposals_test.py`, `build_affix_rules_test.py`, `review_affix_rules_test.py`.

Changed
- `src/affixes.py`: delete the lattice (`growAffixesLattice`, `_growLatticeLevel`, `_reduceExceptions`, dedupe/fold, `growAffixes`,
  `_growOneLevel`) and the legacy-only code (tail variants, families, clustering) once grep shows no caller; `buildCandidates` returns
  anchors + merges + decided forms; `RULE_PARTIAL_OVERLAP` becomes a `SimContext` field, default True (the decided mode).
- `src/affixrules.py`: weights as constants at the D values (alpha 2, fallback 5, form 100); no global mutation; rival resolution by verdict only.
- `src/affixbinding.py`: keep `PhonemeKeys`, `enumerateKeypresses`; delete the rest if unused.
- `src/affixabbrev.py`, `util/export_affix_dictionary.py`: same pool builder; a rule whose anchor vanished is skipped with a warning
  (safe default) instead of a KeyError; warn when `affix_rules.json`'s fingerprint differs.
- `util/affix_scan.py`: delete (its Part B moves to S9a; sweeps L/M/H and legacy go). Scratch scripts importing it or `affixscopes` stay as
  historical files and will no longer run (noted in `docs/AFFIX_RULES.md`).
- `dictionary.py`: S9a + S9b after S8. `.gitignore`: `AffixSelection.pickle`.
- Docs: `docs/PIPELINE.md` (stage S9, rebuild row, md5 list, recompute entry), `docs/AFFIX_RULES.md` (rewrite: flow, review, decisions file),
  `docs/GLOSSARY.md`, `CLAUDE.md` (commands, verification md5 list, test count), `TODO.md`.

## 5. Order (each step ends green: pytest, mypy count <= 127, and the stated check)

0. Baseline: md5 of every S1-S8 tracked output and of `affix_rules.json`, `plover_stenalgo_affix_dictionary.json`, `affix_abbreviations.tsv`
   into `scratch/affix-integration-md5s.txt`; pytest 740, mypy 127.
1. `affix_decisions.json` + `src/affixdecisions.py`, migration script run once (kept in scratch); engine reads the file.
   Check: exporter md5s identical.
2. Weights/flag as constants and a `SimContext` field; remove the mutations. Check: exporter md5s identical.
3. Delete the lattice and legacy code. Check: exporter md5s identical; pool node count identical under `PYTHONHASHSEED=0` and `=1`.
4. `util/build_affix_rules.py` (per-rule cache, fingerprint, report, pending list). Check: one run (~23 min or less) gives the same 30 rules
   and keys as today's `affix_rules.json`; if not, STOP and report the difference before going on. Then a second full run (pickle removed)
   under another `PYTHONHASHSEED`: identical `affix_rules.json` and report. Then a cache check: change one verdict in a scratch copy of the
   decisions, rerun: only that rule is re-evaluated, and the result equals a full recompute with the same decisions; report the wall time.
5. `src/affixproposals.py` + `util/review_affix_rules.py`. Check: with today's decisions nothing is pending; with a copy of the decisions file
   minus the `tion` and `ner` fusions and minus the `i` growth, the proposals reproduce the D numbers of `scratch/fusion-check-2026-10-01.md`
   (+344, +1,578) and the `i:[mn][aeiouy]` scope as the best growth.
6. `dictionary.py` wiring, docs.
7. Final: `rm -f AffixSelection.pickle`, full `python dictionary.py` (background, `PYTHONUNBUFFERED=1`, alone): every S1-S8 md5 equals the
   baseline, the three affix outputs equal the baseline (or the step-4 explained difference); second run reuses the pickle (S9a < 1 min).

Unit tests (hand-built fixtures as in `affixabbrev_test.py`): decisions round-trip and validation; exact-set merge matching (a merge with one
extra spelling is undecided -> apart, pending); undecided anchor -> anchor alone; proposals' help/hurt numbers on a fixture; refused label not
re-proposed; "similar rule" flag; review prompt driven by a monkeypatched `input` (y/n/s/q, save per answer, pickle deleted on a verdict);
cache reuse and fingerprint warning; a changed verdict invalidates exactly that rule's cache entry; reselection from cache equals a
full recompute; exporter skips a vanished anchor; pool determinism across two `PYTHONHASHSEED` subprocesses.
Deleted: the lattice/legacy tests (`affixes_test.py`, `affixscopes_test.py`, possibly `affixbinding_test.py`); the final count is reported.

## 6. Further decisions (user, 2026-10-01)

a. Prices and the partial-overlap flag are code constants (no policy file); the decisions file holds verdicts only.
b. A lexicon/layout fingerprint mismatch warns, never reruns.
c. The review covers only the 30 selected rules.
d. Per-rule cache in `AffixSelection.pickle` instead of deleting it: a verdict change re-evaluates only the affected rules; the global
   selection always reruns (seconds).
e. Merged anchors matched on the exact spelling set; a changed set is pending (shown next to the closest decided entry), never auto-applied.
f. `affix_rules_report.md` tracked at the repo root (deterministic, no timings), next to `affix_rules.json`.
