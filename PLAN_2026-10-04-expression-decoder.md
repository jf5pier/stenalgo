# PLAN 2026-10-04 — the expression decoder (offline prototype first, Plover plugin last)

**STATUS (end of 2026-10-04): steps 1-5 DONE (step 5: plugin built and installed in a real Plover 5.4.1, see `RESULTS_2026-10-04-expression-decoder.md` "Plover plugin" and `docs/PIPELINE.md` S8.10).** Code: `src/expressiondecoder.py`, `src/expressionranking.py`, `src/keyconflicts.py`, `src/elision.py`; numbers: `RESULTS_2026-10-04-expression-decoder.md`;
handoff for step 5: `RESUME_2026-10-04-step5-plover-plugin.md`. Sections 1-3 below are the ORIGINAL plan, kept for the record (the committed rule set has changed since: elision pairs, theory shadow term, key conflicts).

Written for delegation: a fresh agent should be able to run steps 1-3 from this file alone. Read first, in this order:
`RESUME_2026-10-04-selector-order-and-variants.md` (state), `NOTES_2026-10-03-attach-overlap-and-plover-decoder.md`
(sections 1-4 and 7: the algebra, why Plover needs a decoder, the overlap study), `docs/GLOSSARY.md` section "Expression
abbreviation layer" (vocabulary), `TODO.md` ("attach keypress reused as a standalone stroke").

## 0. Goal and non-goals

The expression layer composes a word-unit sequence into FEWER strokes: attach keypresses (key sets, ~24 rules, up to 4 selector
variants per family) are unioned into the host's first/last stroke, briefs replace a whole expression by one stroke. Stock Plover
dictionaries are exact lookups, so reading such strokes needs a DECODER: stroke tuple -> (attach rules, host words). Goal: a
decoder that inverts `composeOutlineTraced` EXACTLY on the committed rule set, proven offline, then (step 5) wrapped as a Plover
dictionary plugin. Non-goals now: changing the rule selection, the slot budget (20), the que family cut, merging main, pushing.

## 1. State to start from (verify with `git log`, `git status`)

- Worktree `/home/jfsp/Steno/stenalgo-briefs`, branch `abbreviations`, last commit `e8444c3`. Nothing pushed. Interpreter
  `/home/jfsp/Steno/stenalgo/env/bin/python`, always `PYTHONPATH=.`. `pytest src/test/` must stay green (818 tests).
- NEVER `git add -A` (untracked logs, `AffixSelection.pickle`, the box-drawing-named file, `scratch/que_run_*.log`, experiment
  folders stay out). Commit only when asked; no push, no merge of main.
- One heavy job at a time, in the background with a log. The driver `PYTHONPATH=. env/bin/python scratch/select_expression_rules.py`
  takes ~5 min and OVERWRITES the tracked `scratch/expr-*` files; `git checkout scratch/expr-*.tsv scratch/expr-rules-final.json`
  restores the committed run. Do not wait with `pgrep -f NAME` (see CLAUDE.md process rules); wait on the log.
- Committed result (budget 20): attaches alone 25.7% (3.672e9 of 1.430e10), 155 exceptions, 0 shadows, 0 collisions; with the 40
  forced briefs 4.297e9. The decoder's inputs are `scratch/expr-rules-final.json` (24 selected rules, keys and beta),
  `scratch/expr-briefs.tsv` (40 forced briefs), and the theory (`util._theoryio.loadDisambiguatedTheory`).
- Plover is NOT installed in the project env (`import plover` fails). Steps 1-4 need no Plover. Step 5 must verify the plugin API
  against a real install; the notes' API details are "from memory".
- `scratch/measure_attach_standalone.py` shows how to load the pool, the rules and a `SimContext` (copy its loader; the driver's
  `main()` is monolithic).

## 2. The algebra the decoder must invert (all in `src/expressions.py`)

- `planStream(rules, tokens)`: matches briefs and attach rules on the word-unit stream (prefix twin yields to its suffix twin at the
  end of the stream; `orderBan` pairs; `MAX_ATTACH_UNITS = 2` for attaches, 3+-unit expressions are briefs only).
- `composeOutlineTraced`: prefix attaches merge into the FIRST stroke of the host content segment that follows, suffix attaches into
  the LAST stroke of the one before, prefixes first, then suffixes. Refused (-> ladder) when `attachKeysOverlap(syllabic(host),
  syllabic(keys))` (strict, `EXPR_MAX_SHARED_KEYS = 0`) or the union is illegal (`ctx.isLegal`). `*`/`#` (keys 10, 15) are
  transparent to both checks (`RESERVED_MARK_KEYS`).
- Ladder: standalone (the keypress alone) if the particle spans >= 2 strokes and the chord is not a live single-stroke outline
  (`standaloneTrap`); else exception (longform kept): reasons `noNeighbour`, `spanOne`, `standaloneTrap`. A run of >= 2 consecutive
  hostless attaches becomes ONE stroke (union, `attachCluster`) when disjoint, legal and not a live outline.
- Selectors: a family has one base keypress, its variants add `*`, `#` or both (`SELECTORS`, order by `freq + stackMass`, or
  m/s,f/s,... for gendered families). A host stroke that already carries `*`/`#` swallows a variant's selector; Stage C then drops the
  variant (selector collapse). So the DECODER cannot tell a selector from a host mark: the committed rules were audited collision-free
  under exactly that.
- Strict zero overlap makes a merge invertible: `H = S \ K`. Stacked attaches on one host: `S = H ∪ K1 ∪ K2`, with the families'
  syllabic keys pairwise disjoint when they co-occur (the "disjoint-pair constraint" in the driver).

## 3. Steps

### Step 1 — offline decoder, strict mode (new module `src/expressiondecoder.py` + tests `src/test/expressiondecoder_test.py`)

Pure Python, no Plover. API suggestion: `class ExpressionDecoder(rules: Rules, theory index, ctx)` with
`decode(strokes: Strokes) -> list[Decoding]` returning EVERY reading (empty list = not an expression outline; one element =
unambiguous). A `Decoding` = ordered segments (attach rule / brief / word) with the host words. Cases to cover:
(a) briefs: exact stroke lookup (single stroke, `BriefRule.beta`); (b) merged attach(es) on a host: for the first stroke try every
subset of attach rules whose key sets are subsets of the stroke (~24 rules x variants; stacks of <= 3 in practice), subtract, look
the remainder up as the first stroke of a theory word (and the suffix case on the last stroke); (c) `attachCluster` strokes (union of
hostless attaches); (d) standalone strokes (keypress alone, particle >= 2 strokes); (e) multi-stroke outlines: the host may have
several strokes and neighbours; decode left to right, a segment boundary is where a theory word's full outline ends.
Index the theory once (first-stroke -> words, last-stroke -> words, outline -> words). Keep it deterministic. Do NOT change
`src/expressions.py` behaviour. Unit tests with a tiny hand-built theory and rules, then a smoke test on the real rules.

### Step 2 — round-trip over the audit

For every pool expression, compose with the committed rules (`composeOutlineTraced`), then `decode` the resulting stroke tuple and
check: the original word-unit sequence is among the readings; report how many outlines decode to exactly one reading, to several
(ambiguous), to none (decoder bug). Weighted by frequency. Expected: 0 none; ambiguity should be 0 because the driver's audit
reports 0 collisions, but the audit only compares composed pool outlines to each other and to live single-stroke outlines. Anything
else is a finding: write it down, do not hide it.

### Step 3 — whole-theory injectivity (the audit the notes ask for)

Use EVERY theory outline as a potential host (~190k words, not just the 1,151 pool expressions): for each selected attach rule (and
each stack of two from the disjoint families) and each host first/last stroke, compute the union and count: (i) unions that equal a
live outline of ANOTHER word (shadowing, Q7); (ii) two different (rule, host) pairs with the same union (collision); (iii) hosts
refused by overlap/illegal chord (fine, they become exceptions). Report counts and frequency mass, per rule. This decides whether a
decoder may legally return ONE reading per stroke tuple, or must rank readings. Also report the forced-brief and attach-chord
clashes (already fixed for the pool in `e8444c3`; re-check over the whole theory).

### Step 4 — decisions (STOP and ask the user; do not decide alone)

Present the step 1-3 numbers and ask, in this order:
1. Brief that depends on a failed attach ("option 2", +2.9% when measured on 2026-10-03, rejected then because the decoder cannot see
   whether an attach would have merged): with a real decoder in hand, is it decodable now? (Needs the decoder to try readings
   with and without the attach.)
2. Attach keypress doubling as the standalone stroke (TODO.md, measured 2026-10-04: only `avec` 1.1e8 and `n' y` 1.1e7 strokes,
   about 3% of the attach saving). Park unless step 1-3 show the standalone case is already needed.
3. Overlap limit: 0 (current) vs max-1 (`EXPR_MAX_SHARED_KEYS`, NOTES section 4). Run the experiments listed there only after the strict
   decoder is proven.
4. How ambiguity found in step 3 is handled: forbid at build time (more exceptions) vs rank at decode time.
5. Where ties go if the Plover translator asks about stroke PREFIXES: dictionary `longest_key` and miss cost.

### Step 5 — Plover dictionary plugin (only after step 4)

A `plover.dictionary` entry-point plugin, living beside the existing `plover_stenalgo` system plugin (`plover_stenalgo/plover_stenalgo/`:
`system.py`, `_generated_keys.py`; the exporters are `util/export_plover_*`). The attach/brief table is exported as data
(from `expr-rules-final.json` + forced briefs) and the plugin calls the step-1 decoder. First verify against a real Plover install:
the dictionary lookup signature, how `longest_key` is used, how misses are cached, how `{^}`-style glue is expressed in the returned
translation. Add the export to the pipeline (CLAUDE.md "Commands", `docs/PIPELINE.md`, `docs/GLOSSARY.md`) only in the Phase 4 work.

## 4. Verification

- `pytest src/test/` green after every `.py` change; mypy (`mypy src/`) must not get worse.
- Step 2's numbers go into a short `RESULTS_2026-10-0X-expression-decoder.md`; update `TODO.md` and the RESUME file at the end.
- If the driver is re-run for any reason, compare `md5sum scratch/expr-rules.tsv` with `a2a334eab8524d88b0ed51426de6deb6` (committed
  run). `scratch/md5_expr_deterministic.txt` is STALE (older run); do not use it.

## 5. Stop and ask the user when

Any decision in step 4, any push, any merge into main, changing the slot budget (20) or the que family cut, touching main's affix
code, installing Plover system-wide (use a venv), or if step 2 finds a composed outline with NO reading (decoder/composer mismatch).
