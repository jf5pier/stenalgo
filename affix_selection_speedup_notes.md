# Speeding up AffixSelection.pickle creation: findings for planning

Written 2026-10-02 from a read-through of the code and one pipeline run's timings. **Nothing here has been profiled or
implemented.** Every performance number is an estimate. Verify with `cProfile` before committing to a design.

## 1. Problem

`python -m util.build_affix_rules` (step S9a of `python dictionary.py`) took **2815.6 s (~47 min)** in the clean run when
`AffixSelection.pickle` was absent. The script's own docstring still says "~25 min" (`util/build_affix_rules.py:12`),
which is stale. Every other step of the run takes under 2 min. Machine: 16 cores (WSL2).

Measured timings from `pipeline_timings.log` of the clean run on 2026-10-02 (`lexique.py` then `dictionary.py`, after
deleting the cache pickles; whole orchestrated run 3254.7 s, `user` 56m26s vs `real` 56m50s, i.e. one core busy
throughout):

| Step | Seconds |
|---|---|
| Dictionary + phonetic theory (S3-S5) | 45 |
| Synthetic lexicon appender (S2) | 91 |
| Elicitation | 37 |
| Grouping | 43 |
| Disambiguated theory refresh (S7) | 52 |
| Realization report | 28 |
| S8 exports: Plover 8, drills 19, sentences 16, definitions 21, lessons 50 | ~114 |
| **S9a affix selection** | **2815.6** (selection itself 2930 s inside the script's own clock, which includes load) |
| S9b affix dictionary | 29 |

## 2. Where the time goes

- `selectRules` (`src/affixrules.py:441`) is a lazy greedy loop over a 3-stage heap. It calls the exact evaluation
  `chooseRuleKeypress` (`src/affixrules.py:~232`) for each rule it reaches at stage 2. In the clean run the log says
  "30 rules selected and bound; 30 rules evaluated now, 0 from the cache", at ~2930 s, so **~95-100 s per evaluated
  rule** (the earlier ~40 rules x ~35 s estimate was wrong). Which rules get evaluated depends
  on what was selected earlier, so this outer loop is inherently sequential.
- `chooseRuleKeypress` stage 1 tests every one of ~1751 legal keypresses `k`. For each `k` it prunes with
  `_exceptionRateFloor`, then calls `resolveFallbacks` and `simulate` on a sample of up to `SAMPLE_CARRIERS = 2000`
  carriers (`src/affixbinding.py:15`). Stage 1 keeps `(score, similarity, k)` tuples. Stage 2 (the "finals") re-simulates
  at most `MAX_ALTERNATIVES` keys on the full carrier set.
- That is ~2000 carriers × 1751 keys ≈ 3.5M carrier-key pairs per rule, or ~27 us per pair at ~95 s per rule. The same
  carriers are revisited for every key.

## 3. What `simulate` repeats per (carrier, key) pair (`src/affixes.py:835`)

- Allocates a `CarrierResult` per carrier.
- `_newBase` (`:785`) recomputes the neighbour index and neighbour stroke, though neither depends on `k`.
- `ruleKeysOverlap` and `ctx.isLegal(neighbour ∪ k)` depend only on (neighbour stroke, `k`). There are probably only a few
  hundred distinct neighbour strokes against 1751 keys. `_exceptionRateFloor` (`src/affixrules.py`) already groups by
  neighbour, so the idea has precedent in the code.
- Builds `newBase` and does `ctx.baseIndex.get(newBase)`, which hashes a tuple of tuples. In most pairs there is no
  collision, so `markCost == 0` and `gain == span` (merged) or `span - 1` (standalone fallback).

## 4. Option A: parallelize the keypress loop (naive, safe)

- Stage 1's iterations are independent given `(rule, k, ctx, pk)`. They only append small tuples to `stage1`, which is
  then sorted by `(-score, -sim, k)`, so the result is deterministic regardless of completion order.
- Use a `multiprocessing` fork pool with `ctx`, `rule`, `pk` as module globals (inherited, not pickled) and chunked
  `imap` over `keypresses`. Only small tuples come back. Leave the finals loop serial.
- Expected ~8–12× on 16 cores, so ~47 min to ~4-6 min (estimate). Output should be bit-identical.
- **Unverified:** that `simulate` and `SimContext` have no mutable state that changes results. `SimContext._legal` is a
  memo cache, which with fork only becomes per-worker and warms separately. Read `simulate` and `markCostForCluster` for
  anything else.
- Outer-loop speculation (pre-evaluating the top N heap entries in parallel) is possible, because evaluations are cached
  by `ruleSignature`. It is more complex, and with Option A in place it's probably not worth it.

## 5. Option B: batch `simulate` over keys (refactor, likely bigger win)

Add a new `simulateKeys(rule, keys, carriers)` and keep `simulate` unchanged. **Do not** pass the keys to the existing
`simulate` as multiple groups: `simulate` models cross-group collisions through its `pending` dict, so the keys would
interact with each other.

Sketch:

1. Once per rule, hoist the key-independent work per carrier: neighbour index/stroke, `lo`/`hi`, the size of its existing
   homophone cluster (`ctx.baseIndex[w.base]`), and its lemma set.
2. Build, once per run (it depends only on layout and position), a table (neighbour stroke × key) → one of
   {merge, `keyOverlap`, `illegalChord`}. Bitmask strokes make this cheap.
3. Assume no collision. Then the key's score is a frequency-weighted sum over neighbour groups (like
   `_neighbourGroups` but weighted), with no loop over carriers.
4. Handle only the sparse collision cases, where `union(neighbour, k)` hits `baseIndex` or another carrier's `newBase`,
   through a reverse index (skeleton with the neighbour slot wildcarded → records). This reproduces `lostDistinction`,
   `markCost` and the `partners` bookkeeping. **This is the risky part.**
5. Keep the final full-carrier pass (stage 2) on the existing `simulate`.

Estimated stage-1 cost per rule: ~(number of neighbour groups × 1751) table lookups plus sparse fix-ups, versus ~3.5M
object-heavy iterations. Likely well over 20× faster. If it lands, Option A for stage 1 probably becomes unnecessary,
and the finals pass dominates what remains.

## 6. Comparison

| | A: pool | B: batch refactor |
|---|---|---|
| Estimated speedup | ~8–12× | probably >20× |
| Effort | ~30 lines | new function + differential tests |
| Risk | none (identical output) | collision / mark-cost logic must match exactly |

## 7. Suggested sequence

1. The clean run is done. Keep its `AffixSelection.pickle` (gitignored, so copy it aside) and the committed
   `affix_rules.json` / `affix_rules_report.md` as the golden reference. The pickle stores every evaluated rule's keys, score and alternatives.
2. Profile one `chooseRuleKeypress` call with `cProfile` (idle machine) to confirm the time split between
   `simulate`/`_newBase`/object allocation and the rest of stage 1.
3. Implement Option A. Check byte-identical `affix_rules.json` against the golden run.
4. Implement Option B only if still worthwhile. Differential-test `simulateKeys` against the old `simulate` on random
   (rule, key) pairs, and the full selection against the golden pickle.

## 8. Other pipeline steps (lower priority)

- The S8 exports (~114 s total) are separate `python -m util.export_*` subprocesses. They could probably run
  concurrently, bringing ~114 s down to ~50 s (limited by lessons at 50 s), if they only read the theory files and write
  different outputs. Not verified. Check S9a/S8 ordering dependencies in `dictionary.py` before reordering.
- Elicitation and Grouping (80 s) look sequential by design. Appender (91 s) is unread, so unknown.

## 9. Environment note

A stray empty root `__init__.py` made 8 tests fail through double-import of modules. It was deleted. All 1005 tests pass
on `main` at `ebb7a2e` without it.

## 10. Reproducibility check of the clean run

After deleting the cache pickles and running `lexique.py` + `dictionary.py` on `main` (`ebb7a2e`), `git status` showed
**no modified tracked files**. Every tracked generated output is byte-identical to what is committed: `affix_rules.json`,
`affix_rules_report.md`, `affix_abbreviations.tsv`, both Plover dictionaries, `keypress_groups.json`,
`realization_report.json`, `resources/LexiqueMixte.tsv`, `resources/LexiqueSynthetic.tsv` and the five
`steno-trainer/public/data/*.json`. The run is deterministic, so a golden-output comparison for a refactor is
well-founded. Caveats: `phonetic_theory.tsv`, `disambiguated_theory.tsv` and the pickles are gitignored, so they could not
be compared with anything pushed. `LexiqueSynthetic.tsv` was not rewritten (the appender converged in round 1).

## Done (2026-10-02)

Implemented the exact lean evaluator instead of "Option B": `SimUnit`/`simulateRuleUnits` (src/affixes.py) and
`KeySweep`/`sweepKey` (src/affixrules.py) replace `resolveFallbacks` + `simulate` in `chooseRuleKeypress`'s key loops.
Findings: collisions are the common case (50-70% of new outlines collide), so a sparse-collision batch is not viable;
branch-and-bound pruned only ~half the keys and was rejected.
Measured: full selection 2930 s -> 429 s (~6.8x); `affix_rules.json`, `affix_rules_report.md` byte-identical, pickle
`evaluations` and `selection` equal. The delta fallback pass (plan step 3) was not done. Differential test:
`src/test/affixrules_sweep_test.py`.

### Profile and delta pass (2026-10-02, later)
Profile of the largest prefix rule (2,000-carrier sample): stage 1 is ~90% of a rule (~1,700 keys x ~9 ms), the 10 finals on
the full carriers ~1.3 s. Per `sweepKey`: mergeUnions 19%, pass A 42%, pass B 39% (only ~11 of 2,000 carriers failed, yet
pass B reran all of them). Implemented `simulateRuleDelta` (only the buckets left or joined by swapped units are redone) and a
leaner `mergeUnions` (frozenset intersection). Golden run again byte-identical; selection 429 s -> 307 s (total 5m26s).

### Fork pool (2026-10-02, later still)
`keySweepMap` (src/affixrules.py) maps the floor filter, the stage-1 sweep and the finals over a fork pool
(`--workers N`, default all cores, 1 = serial); results are bit-identical (golden files and pickle equal). 16 cores:
selection 307 s -> 121 s (total 2m25s), only ~2.5x: setup is ~23 s serial and the pool is forked once per rule.
`pool.terminate()` stalled 4-8 s per rule on the workers' queue lock; `close()` + `join()` fixed that.
Replacing the winner's `resolveFallbacks` (a full `simulate`) by `fallbackCarriers` saved almost nothing.
Next candidates if needed: profile the non-sweep part of selectRules/swapPass/bindKeypresses, one persistent pool.
