> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Resume: affix rules — partial-key-overlap flag (written 2026-09-29, for a fresh Sonnet session)

Supersedes the "next steps" of `RESUME_2026-09-29-affix-after-lexicon-fix.md` (its Steps 1-2 are done; its
open questions are still listed at the bottom of this file). Read, in order: this file,
`FINDINGS_2026-09-29-affix-exceptions-analysis.md` (all measurements + reasons), `PLAN_2026-09-29-affix-scan-speedup.md`.

## 1. Mission
The affix-abbreviation rules (prefix/suffix rules that OR one keypress into the stem's first/last stroke)
have many "exception" words in the H/M/L weight settings. The user wants to know whether letting a rule apply
when only SOME of its keys are already in the neighbouring stroke ("partial overlap") reduces exceptions
without lowering quality, and how that changes key assignment. **Done** = the relaxation exists behind an
OFF-by-default flag, the default output is byte-identical to today's, a flagged full L/M/H sweep is compared
with the baseline, and the user has the comparison to decide.

## 2. Where things are
- Repo `/home/jfsp/stenalgo`, branch `affix-abbreviation-rules` (base `main`), HEAD `7c0ee5f`. Use `env/bin/python`,
  `PYTHONPATH=.`, and **always `PYTHONUNBUFFERED=1` + a redirected log for long runs**. 8 cores, 7 GB RAM.
- Commits this session: `855627e`, `8e811b2` (cherry-picked -ption/-ction lexicon fixes from main),
  `93a36eb` (sweep speedup: `_exceptionRateFloor` prefilter in `src/affixrules.py`, `simulate(boundaryRisk=)`,
  lru_cache on `markCostForCluster`; full sweep 669 s instead of ~5,200 s), `7c0ee5f` (refreshed sweep outputs).
- Uncommitted (intentional, keep): `RESUME_2026-09-29-affix-after-lexicon-fix.md` (edited),
  `FINDINGS_2026-09-29-affix-exceptions-analysis.md`, this file, and ~20 new `scratch/*.py` analysis scripts + outputs.
  Nothing in `src/` or `util/` is uncommitted. Commit the notes only when the user asks.
- No background jobs are running.
- Baselines: `scratch/affix-sweep-baseline-2026-09-29/{L,M,H}/affix-rules.tsv` and `-report.md`; test bench
  `scratch/choose_bench.py` + `scratch/choose-baseline.json` (177 s originally, 19 s now, output byte-identical).
- 711 tests pass (`env/bin/python -m pytest src/test/ -q`, ~2 s).

## 3. State / what is known (details in FINDINGS)
- `_newBase` (`src/affixes.py:1422`) fails a RULE merge when ANY of the rule's keys is in the neighbour stroke
  (line 1438 `if set(neighbour) & set(binding.keys):`), even partially. For span-1 rules the stand-alone fallback
  gains nothing, so these words are `standaloneTrap` exceptions. Example: `en` (keys 18+22 = coda k+n):
  `entraîne` has n but not k -> exception, although the merged chord is legal and unique.
- In-memory test with keys fixed (`scratch/overlap_relax.py`): over 25 H rules exception words 1,039 -> 783 but
  exception frequency and saving flat (~2,303 -> ~2,309; 93,985 -> 93,975): removed exceptions were rare words,
  new ones frequent (`ai|aî|…` got worse: 326 -> 422 freq, saving 4,197 -> 4,026). Real effect needs re-optimised keys.
- The user's questions this turn (answered): relaxing one rule does not change another rule (per-rule
  independent); words vs frequency (score uses frequency); it WILL change key assignment because
  `chooseRuleKeypress`, its prefilter `_exceptionRateFloor` and `bindKeypresses`/`_jointLoss` all use the overlap test.

## 4. Decisions and constraints
- User rejected splitting a rule into two keys (does not ease learning). Do not retry.
- Learnability first: 20-30 rules total, simple human-checkable logic (memory: affix-rule-learnability).
- The user has NOT chosen L/M/H (I recommended H). Do not pick one.
- The user approved only the *proposal* "put the relaxed check behind a flag and rerun the full sweep"
  (asked, then `/preclear` came; treat it as approved for implementation + sweep, NOT for committing or adopting).

## 5. Next steps
1. **Flag.** Add module constant `RULE_PARTIAL_OVERLAP = False` in `src/affixes.py`. In `_newBase`, when True and
   `binding.kind == RULE`, treat overlap as failure only if `set(binding.keys) <= set(neighbour)`; otherwise fall
   through to the legality check with the union (MERGED/DEDICATED bindings, used by Part B family binding, must
   NOT change: keep the old test for them). Mirror it in `_exceptionRateFloor` (`src/affixrules.py:211`, line ~225
   uses `set(neighbour) & keySet`) — if the two disagree the prefilter wrongly rejects keys and results drift.
2. **Sweep option.** In `util/affix_scan.py` add `--partial-overlap` (sets the flag) and make the sweep output
   dir configurable (`SWEEP_DIR` is a module constant, default `scratch/affix-sweep`; use
   `scratch/affix-sweep-partial`). Never overwrite the baseline dir.
3. **Unit tests** (`src/test/`, find the existing `_newBase`/simulate tests): partial overlap fails with the flag
   off and merges with it on for a 2-key rule; complete overlap fails in both modes; single-key rule unchanged.
   Expect 711 + new tests passing.
4. **Flag OFF must not change anything:** run
   `PYTHONUNBUFFERED=1 PYTHONPATH=. nohup env/bin/python -m util.affix_scan --part b --reuse-pool --sweep > scratch/sweep-off.log 2>&1 &`
   (~11 min) then `cmp` every `affix-rules.tsv` and `affix-rules-report.md` in `scratch/affix-sweep/{L,M,H}` against
   `scratch/affix-sweep-baseline-2026-09-29/` (`comparison.md` may differ only in row order among ties).
5. **Flag ON:** same command with `--partial-overlap` into `scratch/affix-sweep-partial/`.
6. **Compare** L/M/H, flag off vs on: selected rules (entered/left), per-rule exceptions (words, freq, kinds),
   totals, credited saving @30, forms, and whether keys changed. Adapt `scratch/weights_comparison.py` and
   `scratch/scope_prune.py` (both hard-code `scratch/affix-sweep`; parametrize the dir). Report to the user in
   tables: exception words AND frequency, saving, which rules improved/worsened and why.
7. **Also owed to the user:** show the table they asked for earlier — every rule in L, M, H with covered words +
   freq and exception words + freq — from `scratch/coverage-exceptions.json` (fields covW covF excW excF othW othF;
   `othW/othF` = words neither gaining nor exception, e.g. no neighbour).

## 6. Verification bar
`env/bin/python -m pytest src/test/ -q` all pass; flag-OFF sweep byte-identical to the baseline dir;
`env/bin/python scratch/choose_bench.py /tmp/x.json` (in scratchpad, not repo) must equal
`scratch/choose-baseline.json` with the flag off. CLAUDE.md's rebuild-md5 bar is not affected (nothing in the
theory/Plover output changes).

## 7. Pitfalls
- Never `pkill -f name` from a command line containing the name (it kills its own shell; happened once).
- Background jobs launched with `nohup … &` inside the Bash tool: the tool's completion notice is the launcher
  shell exiting, NOT the job; check `ps -eo pid,etime,args | grep '[n]ame'` and the log.
- `chooseRuleKeypress` results depend on the module-global weights (`R.EXCEPTION_ALPHA`, `R.EXCLUSION_COST`,
  `R.FORM_COST`): set them per setting (L 1/5/10, M 1/50/100, H 2/150/300) before rebuilding a rule.
- To rebuild a selected rule from a TSV row match `len(rule.results) == carriers` and `wordExceptions`
  (roots can share an ortho with different phono); see `scratch/scope_prune.py`.
- Greedy class selection can be trapped by an early choice (en: key 14 was picked first, hiding the clean
  k/n/m class). Prefer mechanical conditions to greedy ones.
- The bench prefilter and `_newBase` must stay in agreement (see step 1).
- DESIGN §4.2 says physical fallbacks are not exceptions, but span-1 stand-alone is unavailable so they are
  `standaloneTrap` exceptions: a possible design/code mismatch, do not "fix" it without the user.
- Bash occasionally returns a transient "auto mode classifier" error: retry once, use Read meanwhile.

## 8. Stop and ask the user when
- Adopting the flag as default, changing default weights or choosing L/M/H, committing or pushing, merging
  `main` into this branch (deferred by the user), or altering DESIGN semantics (fallback/exception counting).
- The flag-ON result is mixed (some rules worse): present the tables, let the user decide.

## 9. Doc updates owed before merge
If the flag is adopted: `DESIGN_2026-09-27-affix-rule-selection.md` §4.2/§4.4 (overlap definition),
`resources/reference/README.md` note if reference diff changes, and `CLAUDE.md` test count (says 649, now 711+).
Rerun `env/bin/python scratch/affix_reference_diff.py > scratch/affix-reference-diff.md` after any selection change.

## 10. Still-open decisions from `RESUME_2026-09-29-affix-after-lexicon-fix.md` / FINDINGS §7
L/M/H choice; pseudo-affixes (`der`, `er`, `nir`, `voir`, `in`, `ve`: test an attestedShare weight or reserved
slots); curated multi-syllable anchors (anti-, inter-, -able, -cation …); whether the affix key joins an existing
stroke or is its own stroke (answered in code: it is ORed into the neighbour stroke, stand-alone only as fallback).
Cluster-onset fusion measured and dropped (10 pairs, freq 167); spelling-keyed merge (30 pairs, freq 1,912)
pending. `-th` anchors unchecked.

---
## 11. Progress log (appended 2026-09-29, Sonnet session)
Steps 1-4 DONE, step 5 RUNNING, steps 6-7 not started.
- **Step 1 (flag)**: `RULE_PARTIAL_OVERLAP = False` + helper `ruleKeysOverlap(neighbour, keys)` in `src/affixes.py`
  (used by `_newBase` for `binding.kind == RULE` only; MERGED/DEDICATED keep the old test) and by
  `_exceptionRateFloor` in `src/affixrules.py`. Uncommitted.
- **Step 2**: `util/affix_scan.py --partial-overlap` sets the flag and switches `SWEEP_DIR` to
  `SWEEP_DIR_PARTIAL = scratch/affix-sweep-partial`. Uncommitted.
- **Step 3**: `TestRulePartialOverlap` (4 tests) in `src/test/affixes_test.py`; 715 tests pass.
- **Step 4**: flag OFF sweep (643 s): all six `affix-rules.tsv` / `-report.md` in L/M/H are byte-identical to
  `scratch/affix-sweep-baseline-2026-09-29/`. Not yet run: `scratch/choose_bench.py` equality check.
- **Step 5**: flag-ON sweep launched (`scratch/sweep-on.log`, PID 182414). FINDING: it is MUCH slower than flag-off:
  after 30 min it was still in the L setting (flag-off whole sweep = 11 min). Cause (hypothesis, unverified):
  with partial overlap the `_exceptionRateFloor` prefilter rejects far fewer keypresses, so most of the 1,751
  keypresses go through the full simulation per rule. Check `tail scratch/sweep-on.log` and
  `ps -eo pid,etime,args | grep '[a]ffix_scan'`; if hopeless (>3 h), kill by PID and consider profiling or
  restricting the flagged sweep to the ~25 H rules. Output appears in `scratch/affix-sweep-partial/{L,M,H}` only
  as each setting finishes.
- Steps 6-7 (comparison tables; the covered/exception table from `scratch/coverage-exceptions.json`) still owed.
