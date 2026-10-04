# RESUME 2026-10-04 (later) — expression decoder, theory-wide shadow term, elision pairs

Continues `RESUME_2026-10-04-selector-order-and-variants.md` and `PLAN_2026-10-04-expression-decoder.md`. Numbers: `RESULTS_2026-10-04-expression-decoder.md`.
Vocabulary: `docs/GLOSSARY.md` (theory shadow rate, decoder, elision pair).

## State
- Branch `abbreviations`, worktree `/home/jfsp/Steno/stenalgo-briefs`, interpreter `/home/jfsp/Steno/stenalgo/env/bin/python`, `PYTHONPATH=.`. Nothing pushed, main not merged.
- Plan steps 1-3 done: `src/expressiondecoder.py` (+ tests), round trip (0 unreadable / 0 mismatched), whole-theory injectivity. Step 4 partly decided, step 5 (Plover plugin) not started.
- New default Stage B: theory-wide shadow term (limit 0.002) + pinky-diagonal key conflicts: attach saving 24.8% (was 25.7% before the shadow term), 4.149e9 with briefs, 9 theory shadow events (was 4,467).
  Then elision became the default (see above); the committed `scratch/expr-*` files are that run (md5 `expr-rules.tsv` 7e5a6c68eb38...).
- Elision pairs (one chord + one slot per pair, the decoder reads the host) are the DEFAULT (`ELISION_PAIRS=0` turns them off; `SELECTOR_RETRY` on with them): 24.2% total, hosted saving 2.560e9 (+4.0% over no elision), 46 theory shadow events (0.23% of host frequency). The run without elision: `scratch/expr_noelision/`.
- Brief chords: `attachMergeChords` keeps forced briefs off any chord an attach can write over a one-stroke word.
- Tests: all pass (`pytest src/test/`); new files `src/test/expressiondecoder_test.py`, `src/test/elision_test.py`, a `HostIndex` test in `expressionrules_test.py`.

## Switches (`scratch/select_expression_rules.py`)
`THEORY_SHADOW=0` (pool-only Stage B), `SHADOW_MAX_RATE=x`, `ELISION_PAIRS=1`, plus the earlier `SELECTOR_RETRY`, `KEEP_COLLAPSED`, ... Each run overwrites the tracked `scratch/expr-*`;
`git checkout scratch/expr-*.tsv scratch/expr-rules-final.json` restores the committed run. Read-only audits on those files: `scratch/theory_injectivity.py`, `scratch/shadow_frequency.py`,
`scratch/decode_roundtrip.py`, `scratch/rank_loss.py` (they read `scratch/expr-rules-final.json`).

## Decisions
- Ranking at decode time (user): precedence plain word > pure brief > attested pool reading > rest; the composer must apply the same ranking (a losing reading becomes an exception). Not built yet.
- `pas ce dans à` shadows too costly (user): fixed by the Stage B term. Limit stays 0.002 (0.01 tried, `la` shadows `les`).

## NEXT
0. DONE: the `il` + `n'` stacking regression was a pinky-diagonal conflict (keys 23+24); `src/keyconflicts.py` (footprint model) is now the overlap test everywhere; default = 24.8%, hosted 2.454e9. Fragments (n-gram slices ending on a particle) are ~40% of the pool saving: compare runs on hosted expressions (results file, run-independent split).
1. DONE: ranking (`src/expressionranking.py`: plain word > pure brief > attested > probability; pool 0 differ, open set 98.4% read back). Still to do for the plugin: export the attested table and the word probabilities as data files.
2. Remaining collisions: `n' y`, `il n'`, `je me` (their `*` is swallowed by hosts such as `a`/`est`), `le`, `qui`, `un`.
3. Elision experiment: the lost saving is all in hostless n-gram fragments (hosted expressions +3.9%), see the results file; compare runs on hosted expressions only. `ASPIRATED_H` / `NO_ELISION` are short lists, complete them from a lexicon if adopted.
4. Step 4 leftovers (brief depending on a failed attach, standalone-as-attach, overlap max-1, `longest_key`), then step 5 (Plover plugin, needs a venv with Plover).
5. The earlier list: preselect more than 4 candidates per family.

## Stop and ask the user when
Any push, any merge into main, changing the slot budget (20) or the que family cut, touching main's affix code, installing Plover system-wide.
