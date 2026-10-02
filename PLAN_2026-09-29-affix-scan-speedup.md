> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Plan: cut the affix scan sweep from ~86 min to minutes (written 2026-09-29)

Branch `affix-abbreviation-rules`. Goal: same selected rules, far less compute. Each step is
independent, exact (results must not change) and can be done in its own session. Do NOT run the
full sweep (`util.affix_scan --sweep`, ~86 min) until step 5; use the small checks below.

Always run long Python with `PYTHONUNBUFFERED=1` and redirect to a log (empty logs cost us an hour
on 2026-09-29). Use `env/bin/python`, `PYTHONPATH=.`; 8 cores, 7 GB RAM.

## Findings (measured 2026-09-29)
- Full sweep = 5,174 s (2026-09-28 log; this session's rerun ~90 min). Per setting (L/M/H):
  variant-rival resolution 1,200-1,600 s, Phase 3 184-428 s, Part A ~1 min once.
- Building `buildCandidateRule` for ALL 3,087 anchors is cheap (150 anchors = 9.8 s -> ~3 min).
- The cost is `chooseRuleKeypress` (`src/affixrules.py:199`): exact keypress choice, 30-50 s per
  large rule (60-100 s under cProfile: `scratch/profile_choose.py`, `scratch/profile-choose.log`).
  Stage 1 calls `simulate` (`src/affixes.py:1469`) once for each of 1,751 legal keypresses on a
  carrier sample (~21 M `_newBase` calls per 6 rules). `resolveVariantRivals` (`affixrules.py:381`)
  exact-evaluates M and main rules for the top `RIVAL_RESOLVE_TOP=60` anchors, per setting.
- Profile split for 6 big rules (471 s): `simulate` 164 s self, `_newBase` 127 s cum,
  `markCostForCluster` 37 s, `hasBoundaryRisk` 26 s, `assignStarHashCombos` 18 s.
- `buildCandidateRule` depends on the weights (`FORM_COST` etc.), so rule caches can't be shared
  across L/M/H directly; per-(carrier, keypress) simulation results can (weight-independent).

## Test bench (build first, reuse in every step)
`scratch/choose_bench.py`: loads `scratch/affix-pool.pickle`, records, engine (as
`scratch/profile_choose.py` does), builds rules, picks the 6 largest + ~10 random small/medium
anchors, runs `chooseRuleKeypress` serially and dumps for each rule: `keys`, `score`,
`strokeFreqSaved`, `wordExceptions`, `alternatives` to `scratch/choose-baseline.json`. A step is
accepted only if the dump is byte-identical to the baseline. Store the wall time per step in
`scratch/choose-bench-times.txt`. Keep the run under ~10 min (use the 6 big rules only for timing).
Also run `pytest src/test/` (affix tests) after each code change.

## Step 1: free wins in `simulate` (exact)
1a. Stage 1 doesn't need `boundaryRisk` (a report flag only, never in score or exception rate).
    Add a `simulate(..., boundaryRisk=False)` parameter; pass True only for the finals in
    `chooseRuleKeypress` and other callers that read the flag.
1b. Memoise `markCostForCluster` / `assignStarHashCombos` (pure functions of a small int).
Expected: ~15% off. Verify with the bench.

## Step 2: measure how tight a cheap upper bound is (no code change to the pipeline)
For 6 big rules and every legal keypress compute (a) the pass-1-only bound
`sum f * saved` over carriers with a valid `_newBase` (saved = span if merged else span-1),
(b) the exact stage-1 score. Report: how many keys have bound <= the MAX_ALTERNATIVES-th best exact
score (skippable), and whether the bound is always >= exact (it must be: collisions/mark costs and
exception penalties only lower the score). Output `scratch/bound-tightness.md`.
Decision rule: if >70% of keys are skippable, do step 3; otherwise go to step 4.

## Step 3: branch-and-bound over keypresses in `chooseRuleKeypress` (exact)
Compute the pass-1 bound for all keys, sort descending, run the full simulate in that order, stop
once the next bound < the MAX_ALTERNATIVES-th best exact score among keys that passed
`sc > 0` and `_exceptionRate <= MAX_EXCEPTION_RATE`. Keys are tie-broken by
`(-score, -simOf[k], k)` in stage 1 -- the stop test must use `<` on the score with the same
tie-break so the top-N set is identical. Verify with the bench.

## Step 4: neighbour grouping in pass 1 (exact, if step 3 isn't enough)
`_newBase` legality/overlap/union depend only on the neighbour stroke and the key, not the word.
Precompute per (position, neighbour stroke, key) once per `chooseRuleKeypress`, or globally in
`SimContext`, and reuse for all carriers sharing that neighbour. Verify with the bench.

## Step 5: share across L/M/H and re-verify end to end
5a. Cache the weight-independent per-(carrier set, keypress) stage-1 results across settings if
    step 3/4 don't already make M/H cheap; check peak RSS on the bench first (<3 GB).
5b. Only now rerun the full sweep (`PYTHONUNBUFFERED=1 ... util.affix_scan --refresh --sweep`,
    background, log). Compare `scratch/affix-sweep/{L,M,H}/affix-rules.tsv` against the current
    files (copy them to `scratch/affix-sweep-baseline-2026-09-29/` BEFORE the rerun): must be
    identical. Rerun `env/bin/python scratch/affix_reference_diff.py`.
5c. Record the new timings in `docs/` (or the FINDINGS doc) and commit.

## Optional, not exact (needs user sign-off)
- Lower `SAMPLE_CARRIERS` for stage 1, or `RIVAL_RESOLVE_TOP`: changes results; compare against the
  baseline and report the differences.
- `multiprocessing` (fork, copy-on-write) over keypresses: only distributes work; useful last if
  steps 1-4 leave the sweep above ~15 min.

## State at time of writing
- Cherry-picked the `-ption`/`-ction` lexicon fixes (855627e, 8e811b2); pickles and the
  sweep outputs in `scratch/` were regenerated from the fixed lexicon on 2026-09-29.
- Still to check (cheap, from `scratch/affix-candidates.tsv`): the stray `psj§ ption` and
  `ksj§ ction` anchors are gone and `tion`'s carriers grew. Bash was down when I tried.
- Open decisions from `RESUME_2026-09-29-affix-after-lexicon-fix.md` (cluster-onset fusion, L/M/H
  choice, pseudo-affixes, multi-syllable anchors) are unchanged and come after the speedup.

## Progress log
- 2026-09-29 bench built (`scratch/choose_bench.py`; baseline `scratch/choose-baseline.json`, 177 s).
- Step 1 done (uncommitted): `simulate(boundaryRisk=)` + `lru_cache` on `markCostForCluster`;
  results identical, no measurable speedup (180 s) -- the profile hot spots were not stage 1.
- Step 2 done (`scratch/bound-tightness.md`/`.log`): the 6 biggest rules have NO valid key at all
  (`keys=None`, every key breaks the 5% exception cap), so the "Nth best score" bound is useless
  (threshold -inf); the pass-1 exception-rate floor instead rejects 1,724-1,740 of 1,751 keys
  per rule, 0 violations.
- Step 3 done (uncommitted): `_exceptionRateFloor` in `src/affixrules.py`, checked before each
  stage-1 `simulate`. Bench 177 s -> 45 s, dump byte-identical, 711 tests pass. Remaining cost
  per big rule 5-11 s is pass 1 (`_newBase` on every carrier for every key) -> step 4.
- Next: step 4 (neighbour grouping), then the step 5 full sweep against saved baselines
  (copy `scratch/affix-sweep/*` to `scratch/affix-sweep-baseline-2026-09-29/` first).
- Step 4 done: `_neighbourGroups` + group-based `_exceptionRateFloor` (pass-1 classification per
  (neighbour stroke, single-syllable) group instead of per carrier). Bench 45 s -> 19 s, dump
  byte-identical, 711 tests pass.
- Step 5 done (5a cache skipped, not needed): full sweep `--part b --reuse-pool --sweep` = 669 s
  (was ~5,200 s). Rival resolution 142-228 s/setting (was 1,200-1,600), phase 3 13-46 s (was
  184-428). L/M/H `affix-rules.tsv` and reports byte-identical to
  `scratch/affix-sweep-baseline-2026-09-29/`; `comparison.md` identical as a set of lines (row
  order among ties varies run to run: it is built from an unordered set).
- Still open: confirm the stray `psj§ ption` / `ksj§ ction` anchors are gone from
  `scratch/affix-candidates.tsv`; then the decisions in RESUME_2026-09-29.
