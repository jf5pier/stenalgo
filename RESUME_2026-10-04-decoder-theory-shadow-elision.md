# RESUME 2026-10-04 (later) — expression decoder, theory-wide shadow term, elision pairs

Continues `RESUME_2026-10-04-selector-order-and-variants.md` and `PLAN_2026-10-04-expression-decoder.md`. Numbers: `RESULTS_2026-10-04-expression-decoder.md`.
Vocabulary: `docs/GLOSSARY.md` (theory shadow rate, decoder, elision pair).

## State
- Branch `abbreviations`, worktree `/home/jfsp/Steno/stenalgo-briefs`, interpreter `/home/jfsp/Steno/stenalgo/env/bin/python`, `PYTHONPATH=.`. Nothing pushed, main not merged.
- Plan steps 1-3 done: `src/expressiondecoder.py` (+ tests), round trip (0 unreadable / 0 mismatched), whole-theory injectivity. Step 4 partly decided, step 5 (Plover plugin) not started.
- New default Stage B: theory-wide shadow term (limit 0.002): attach saving 24.0% (was 25.7%), 4.038e9 with briefs, 5 theory shadows (was 4,467).
  The committed `scratch/expr-*` files are this run (md5 `expr-rules.tsv` f98fd383d538...).
- Experiment `ELISION_PAIRS=1` (one chord + one slot per elision pair, the decoder reads the host): built and tested, OFF by default (22.6%, see results). Its files: `scratch/expr_elision/`.
- Tests: all pass (`pytest src/test/`); new files `src/test/expressiondecoder_test.py`, `src/test/elision_test.py`, a `HostIndex` test in `expressionrules_test.py`.

## Switches (`scratch/select_expression_rules.py`)
`THEORY_SHADOW=0` (pool-only Stage B), `SHADOW_MAX_RATE=x`, `ELISION_PAIRS=1`, plus the earlier `SELECTOR_RETRY`, `KEEP_COLLAPSED`, ... Each run overwrites the tracked `scratch/expr-*`;
`git checkout scratch/expr-*.tsv scratch/expr-rules-final.json` restores the committed run. Read-only audits on those files: `scratch/theory_injectivity.py`, `scratch/shadow_frequency.py`,
`scratch/decode_roundtrip.py`, `scratch/rank_loss.py` (they read `scratch/expr-rules-final.json`).

## Decisions
- Ranking at decode time (user): precedence plain word > pure brief > attested pool reading > rest; the composer must apply the same ranking (a losing reading becomes an exception). Not built yet.
- `pas ce dans à` shadows too costly (user): fixed by the Stage B term. Limit stays 0.002 (0.01 tried, `la` shadows `les`).

## NEXT
1. Build the ranking: attested table export, `loses(reading)` in the composer, decoder tie-break; the grammar filter of the elision experiment is already in the decoder.
2. Remaining collisions: `n' y`, `il n'`, `je me` (their `*` is swallowed by hosts such as `a`/`est`), `le`, `qui`, `un`.
3. Elision experiment: why the saving falls (freed slots go to `un`, `elle`, `en`, `les`, `sur` drops); try re-weighing before adopting. `ASPIRATED_H` / `NO_ELISION` are short lists, complete them from a lexicon if adopted.
4. Step 4 leftovers (brief depending on a failed attach, standalone-as-attach, overlap max-1, `longest_key`), then step 5 (Plover plugin, needs a venv with Plover).
5. The earlier list: preselect more than 4 candidates per family.

## Stop and ask the user when
Any push, any merge into main, changing the slot budget (20) or the que family cut, touching main's affix code, installing Plover system-wide.
