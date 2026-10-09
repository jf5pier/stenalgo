# RESUME 2026-10-04 (end of session) — start of PLAN step 5: the Plover dictionary plugin

**STATUS (later the same day): step 5 DONE.** The plugin exists (`plover_stenalgo/plover_stenalgo/{dictionary,render,stroke,wordindex}.py` + generated `_core/`), the data export is
`python -m util.export_expression_data` (0.3 MB `.stenalgo` + the stock `plover_stenalgo_dictionary.json` beside it, fingerprint-checked), the plugin is installed in the user's Windows Plover 5.4.1 and
reads `de l'` live on a Starboard. Numbers and open items: `RESULTS_2026-10-04-expression-decoder.md` "Plover plugin", `TODO.md` "Branch TODO — Plover expression dictionary plugin", docs in
`docs/PIPELINE.md` S8.10. The "What to do" list below is HISTORICAL (the 5 items are done; the open questions of item 4 are answered in the results file). Next: the `stenalgo-plover` repo sync, more GUI tests.

Read first, in this order: this file, `PLAN_2026-10-04-expression-decoder.md` (steps 1-4 done, step 5 below), `RESULTS_2026-10-04-expression-decoder.md` (all numbers),
`RESUME_2026-10-04-decoder-theory-shadow-elision.md` (state and switches), `docs/GLOSSARY.md` section "Expression abbreviation layer" (vocabulary).

## 1. State (verify with `git log`, `git status`)

- Worktree `/home/jfsp/Steno/stenalgo-briefs`, branch `abbreviations`, last commit `9abb513`. Nothing pushed, main not merged. Interpreter `/home/jfsp/Steno/stenalgo/env/bin/python`,
  always `PYTHONPATH=.`. `pytest src/test/` = 839 pass (853 after the plugin work). NEVER `git add -A` (untracked logs, `AffixSelection.pickle`, the box-drawing-named file, `scratch/*.log`, experiment folders stay out).
  Commit and push only when asked; no merge of main.
- The committed rule set (`scratch/expr-*`, md5 of `expr-rules.tsv` `7e5a6c68eb38...`) is the DEFAULT run of `PYTHONPATH=. env/bin/python scratch/select_expression_rules.py` (about 5 minutes; it
  overwrites the tracked `scratch/expr-*`; `git checkout scratch/expr-*.tsv scratch/expr-rules-final.json` restores). Defaults: elision pairs on (`ELISION_PAIRS=0` off), `SELECTOR_RETRY` on with them,
  theory-wide shadow term on (`THEORY_SHADOW=0` off, limit 0.002), pinky-diagonal key conflicts everywhere. The run without elision: `scratch/expr_noelision/`.
- Result: 29 attach rules + 40 forced briefs, attach saving 24.2% (3.457e9), 4.014e9 with briefs, 0 pool shadows and collisions, hosted-expression saving 2.560e9, 46 theory shadow events
  (0.23% of host frequency, none a frequent phrase).

## 2. What exists for the plugin (all pure Python, no Plover import anywhere)

| Piece | File | Role |
|---|---|---|
| composer | `src/expressions.py` (`composeOutlineTraced`, `AttachRule`, `BriefRule`, `Rules`, `conflictsOf`) | text -> strokes |
| key conflicts | `src/keyconflicts.py` | pinky diagonals (22-25, 0-3): the overlap test of the layer, derived from the layout |
| elision | `src/elision.py` | one chord per pair (`que`/`qu'`...), the host decides; `orderingExists` for stacks |
| decoder | `src/expressiondecoder.py` (`ExpressionDecoder(rules, words, unitStrokes, isLegal, conflicts)`) | stroke tuple -> EVERY reading |
| ranking | `src/expressionranking.py` (`ReadingRanker`, `rankedDecode`, `composedReading`, `attestedTable`, `unitProbabilities`) | readings -> the one answer |
| loaders | `scratch/decode_roundtrip.py::loadAll()` | shows how to build rules, pool, `words` (outline -> orthos), `unitStrokes`, `SimContext` |
| audits | `scratch/decode_roundtrip.py`, `theory_injectivity.py`, `shadow_frequency.py`, `rank_check.py` | read `scratch/expr-rules-final.json` + `scratch/expr-briefs.tsv` |

Ranking order: plain live word (an attested plain reading first, then the more probable) > pure brief > attested pool reading (by frequency) > the more probable reading (product of unigram probabilities).
Measured: pool 1,151 outlines, 0 differ from the composed reading; open set (43,599 attach + one-stroke-word merges), 86.2% decode to the merge itself, 12.2% to the same words grouped differently, 1.6% to
another merge, 0.01% to a plain word.

## 3. Step 5 — what to do

1. DATA EXPORT (not done): write the plugin's data files from the pipeline (new `util/export_*` or a `scratch` script first): the rules (attach: units, position, keys, family, elision; brief: units, strokes;
   `orderBan`), the 40 forced briefs (`scratch/expr-briefs.tsv`), the attested table (`attestedTable` over the pool: outline, normalized signature, frequency), the unigram probabilities (`unitProbabilities`),
   and the theory index the decoder needs (`words`: outline -> word surfaces; `unitStrokes`; the legality of chords, or the `Starboard` tables behind `isLegal`/`KeyConflicts`).
   The decoder must run without the full pipeline: decide what is serialized (probably JSON next to `plover_stenalgo_dictionary.json`).
2. PLOVER INSTALL in a VENV (never system-wide; ask before installing): verify against the real package, because the plan's API notes are "from memory": the `plover.dictionary` entry-point and class
   (`StenoDictionary`: `_lookup`, `__getitem__`, `longest_key`, `readonly`...), how `longest_key` is used by the translator, how misses are cached, how a glued `{^}` translation is returned.
3. The plugin lives beside the system plugin in `plover_stenalgo/plover_stenalgo/` (`system.py`, `_generated_keys.py`; exporters `util/export_plover_*`). It calls `rankedDecode` and renders the winning
   reading as a Plover translation (words joined by spaces; elision `qu'` glued without space; merged attaches in the order the reading gives, with the elision form decided by the host).
4. Open questions to settle with the user (PLAN step 4, items 5 and leftovers): `longest_key` and the miss cost when the translator asks about stroke PREFIXES; brief that depends on a failed attach;
   attach keypress doubling as the standalone stroke (parked); overlap max-1 (`EXPR_MAX_SHARED_KEYS`, keep 0 until the plugin works); how to show an unattested chord that reads as a plain word.
5. Add the export to `CLAUDE.md` "Commands", `docs/PIPELINE.md`, `docs/GLOSSARY.md` only with the Phase 4 work (build + export + docs), before any merge to main.

## 4. Known open issues (not blockers for step 5)

- Remaining collision families: `de`, `j'`, `je`, `il`, `à`, `n' y`, `il n'`, `je me` (a host's own `*`/`#` swallows a variant's selector); the ranking resolves them at decode time.
- Hostless pool fragments (n-gram slices ending on a particle) are about 40% of the pool saving: compare runs on hosted expressions (results file, "Pinky-diagonal key conflicts").
- `ASPIRATED_H` / `NO_ELISION` in `src/elision.py` are short lists; complete them from a lexicon.
- Theory shadows of `un`, `le`, `c'`, `qu'` (46 events, 0.23% of host frequency): the shadow index sees words and, after Stage C, attach-merge chords for briefs; it does not see multi-stroke briefs.
- 1.6% weighted open-set mis-decodes (`dans` + `et` read as `avec` + `la`, `à` + `me`, `de` + `ton`...), mostly unnatural pairs.
- Pitfalls met this session: a log file already holding `DONE` from an earlier run makes `until grep -q DONE` return at once (delete the marker or use a fresh file); a local name equal to a module
  global (`words`, `ELISION_PAIRS` imported inside `main`) shadows it; every experiment run overwrites the tracked `scratch/expr-*`.

## 5. Stop and ask the user when

Any push, any merge into main, changing the slot budget (20) or the que family cut, touching main's affix code, installing Plover (use a venv, ask first), or any decision of PLAN step 4.
