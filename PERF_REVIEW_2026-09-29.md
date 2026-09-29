# Performance review — 2026-09-29 (branch `performance-optim`, HEAD 8e811b2)

Stage 1 (profiling) + Stage 2 (this report) of the plan
`~/.claude/plans/i-want-to-plan-sleepy-parrot.md`. No pipeline source was modified; the only
files created are `scratch/profiles/*` and this report.

## 1. Method

- Interpreter `/home/jfsp/stenalgo/env/bin/python` (3.14.7), repo root `/home/jfsp/stenalgo-fix`,
  all runs serial (7 GB RAM machine).
- `rm -f Dictionary.pickle PhoneticTheory.pickle`, then each step profiled in its own
  subprocess with `python -m cProfile -o scratch/profiles/<step>.pstats -m <module> [args]`
  for the 9 steps below, plus `util.completeVerbParadigms --apply`. Top-15 tables by
  `cumulative` and by `tottime` extracted into `scratch/profiles/<step>.top.txt`.
- Whole run: `py-spy record --rate 25 --subprocesses -o scratch/profiles/pipeline.svg --
  <python> dictionary.py` from clean pickles. Exit 0, 60,661 samples, 2 errors, 2391.8 s wall.
  Inclusive shares extracted from the SVG's per-frame sample counts
  (`scratch/profiles/pipeline_top_functions.txt`).
- Step wall times read from the new `pipeline_timings.log` lines (kept in git alongside this
  run; the pre-run log is snapshotted at `scratch/profiles/pipeline_timings.before.txt`).
- Incidents (recorded per the delegation rules, nothing debugged):
  - py-spy at its default 100 Hz fell >14 s behind within seconds and was restarting the run
    (worktree cleaned first); rerun at 25 Hz. Even at 25 Hz it emitted 1100
    "behind in sampling" messages once S2's memory-heavy appender scans started, so **wall
    times of the S2 step and its child S3–S5 rebuild pass 3 are inflated by sampling overhead**
    (details in Finding 6). Per-step cProfile numbers and the non-lagged step times are the
    quantitative backbone; py-spy is used only for cross-step shares.
  - `util.completeVerbParadigms --apply` ran against the pre-pipeline synthetic lexicon and
    appended 0 rows; the orchestrated run's S2 later appended 17 rows (two rounds), which is
    the expected converged-S2 behavior but means `resources/LexiqueSynthetic.tsv` and the
    downstream `plover_stenalgo_dictionary.json` (+21 entries), `realization_report.json`,
    `steno-trainer/public/data/definitions.json` now differ from the committed versions.
    `keypress_groups.json`, `resolved_press_sets.json`, `practice-words.json` and
    `practice-sentences.json` were regenerated **byte-identical**.

### Measured step times

| Step | cProfile total (s) | unprofiled wall (s, pipeline_timings.log) | Dominant rows (profiled) |
|---|---|---|---|
| `util.build_phonetic_theory` (S3+S5, clean pickles) | 265.6 | 132.6 (pass 1 of whole run; 250.7 for `loadOrBuildDictionary` under cProfile vs 113.5 unprofiled) | `analyseAmbiguities` 230.2; `lexicalSyllabicPartAmbiguityScore` 208.2 cum / 63.3 tot (27,084 calls) |
| `src.elicitation --resolve` | 104.0 | 29.2 (pipeline mode `both`) | 70.5 s `waitpid` on its two child steps (grouping + realization, `--resolve`-only); `resolveAndWritePressSets` 25.1 |
| `util.build_keypress_groups` | 29.6 | 36.1 | 23 CP-SAT `solve` calls 22.5 |
| `util.build_disambiguated_theory` (S7) | 130.9 | 55.4 | `buildDisambiguatedTheory` 114.2 wall / 114.4 logged; `realizeKeypressGroupsAsExtraStroke` 103.1 |
| `util.build_realization_report` | 109.4 | 44.9 | `realizeKeypressGroupsAsExtraStroke` 99.5 |
| `util.export_plover_dictionary` | 133.0 | 56.2 | `loadDisambiguatedTheory` 118.7 (of which `buildDisambiguatedTheory` 113.2) |
| `util.export_practice_words` | 148.9 | 61.3 | `loadPhoneticAndDisambiguatedTheory` 120.6; `renderFinalStrokesToRTFCRE` 13.5 (190,236 calls) |
| `util.export_practice_sentences` | 150.7 | 61.9 | `buildDisambiguatedTheory` 125.9 |
| `util.export_definitions` | 166.4 | 58.9 | `buildDisambiguatedTheory` 124.3; `strokesToRTFCRE` 13.6 cum (716,227 calls) |
| `util.completeVerbParadigms --apply` | 130.3 | (runs inside S2) | `extractDiscriminatingFeatures` **2 calls**, 17.9 s; `Word.__hash__` 98.8M calls 10.0 s |

Whole-run py-spy inclusive shares (60,661 samples): `lexicalSyllabicPartAmbiguityScore`
6,690 (11.0%), `buildDisambiguatedTheory` 5,044 (8.3%, = its 6 invocations),
`realizeKeypressGroupsAsExtraStroke` 4,947 (8.2%), S2's discriminator path
(`confirmCandidates` 1,485 + `extractDiscriminatingFeatures` 1,313 +
`buildDiscriminatorSelection` 1,100 ≈ 6.4%), `getStrokeCost` 1,164.

cProfile inflation on this workload is ~2.2–2.6× (e.g. S7 44.7 s unprofiled vs 114.4 logged
under cProfile; S3 113.5 vs 250.7). All "expected saving" numbers below are given on the
**unprofiled** scale.

## 2. Findings — plan hypotheses vs measurements

1. **S7 disambiguated theory recomputed ~6–7× per run — CONFIRMED at 6×.**
   `util/_theoryio.py:97` calls `Dictionary.buildDisambiguatedTheory` inline; the six
   invocations are S7 (`util/build_disambiguated_theory.py`), realization
   (`util/build_realization_report.py`) and the four exporters
   (util/export_plover_dictionary.py:41, export_practice_words.py:220,
   export_practice_sentences.py:154, export_definitions.py:52). Measured: 44.7 s unprofiled
   per call (S7 step, `pipeline_timings.log` 14:17:11), 113–126 s under cProfile in each of
   the five other steps. The orchestrated elicitation step runs in mode `both`, which skips
   `--resolve`'s child steps (src/elicitation.py:696–699 are guarded by
   `args.mode == "resolve"`), so there is no 7th call — the plan's "~6–7×" resolves to 6.
2. **`buildWordToStrokes` / `buildWordsByOrthoLemme` rebuilt repeatedly — CONFIRMED, but
   second-order.** Call sites: dictionary.py:408–409, src/ambiguitychecker.py:980, :1220,
   :1248, plus util/export_practice_words.py:183–184 (2 more each for the three trainer
   exporters via `buildReadingsByWord`). Measured cost: `buildWordsByOrthoLemme` 3.4–6.5 s
   profiled per step (2 calls of 3.2 s in `export_practice_words`), i.e. ~10–15 s profiled /
   ~5 s unprofiled per run — real but small next to item 1/3.
3. **`realizeKeypressGroupsAsExtraStroke` is the conflict-finding hot spot — CONFIRMED, and
   it is the single biggest in-process cost after S3.** 99–114 s of every one of the 6 S7
   computations (79–85% of `buildDisambiguatedTheory`). Inside it (S7 profile):
   `getStrokeCost` 3,262,439 calls, 74.0 s cum / 44.5 tot; `_composedInduced` 3,262,439
   calls, 13.0 s; `_feasible` 129 calls 53.5 s; `_candidateCost` 93 calls 46.7 s. The
   doubling is visible in the data: `_feasible` builds `induced` for all words
   (src/ambiguitychecker.py:1054) and `_candidateCost` then recomputes the same
   `_composedInduced` per word (:1108). `getStrokeCost` (src/keyboard.py:546) is hot because
   per call it loops fingers × keys and does `(key,) in fingerKeypress.keys()` — source of
   the 52.5M `dict.keys` (6.9 s) and 32.6M `keyboard.py:99 __getitem__` (10.8 s) rows, plus
   41.8M `sorted` calls (8.2–9.2 s, from `_composedInduced`→`_appendCodaExtraStroke` /
   `canonicalizeStrokes`). `Word.__hash__` is a cached digest (src/word.py:166–168) and is
   *not* a bottleneck (3.4–10.0 s spread over 20–99M calls).
4. **S3 hot spots — plan hypothesis REFUTED; the data points elsewhere.** The plan expected
   `getStrokesOfPhoneme` (~10⁸ calls), `readCorpus` double pass and `deepcopy([])` to
   dominate. Measured: `getStrokesOfPhoneme` 1,137,046 calls, **6.8 s** cum; `readCorpus`
   **9.8 s** cum; `deepcopy` not in the top 15. The actual S3 cost is
   `analyseAmbiguities` (dictionary.py:213) → `analyseMultiphonemeLexicalAmbiguity_serial`:
   `lexicalSyllabicPartAmbiguityScore` (src/grammar.py:975) is 208 s of the 265 s profiled
   step (63.3 s tottime over 27,084 calls; ~90 s of the 113.5 s unprofiled pass), driven by
   48.2M `Word.replaceSyllables` (src/word.py:383, 73.9 s cum), 48.4M `sum` (56.9 s) and
   96.7M `str.find` (13.6 s). It is also the #1 whole-run py-spy share (11.0%). The
   per-syllabic-part stage does run in 3 forked workers (src/grammar.py:1054–1094,
   `_getLexicalAmbiguityScores`), but the serial multiphoneme-pair stage dominates.
5. **Per-call recompute with ~1000:1 hit rates — CONFIRMED as real, REFUTED as a priority.**
   `keyDisplayName` (src/keyboard.py:654, list membership per call): 2,598,276 calls, 4.0 s
   in `export_definitions`. `strokesToRTFCRE` (src/keyboard.py:683): 636,613–716,227 calls,
   8.8–13.6 s per exporter. `renderFinalStrokesToRTFCRE` (util/_stenorender.py:40): 190,236
   calls, 13.5 s in `export_practice_words`. `formatReadingsLabel` (defined
   util/export_practice_words.py:113, used at export_definitions.py:68) does not even reach
   the top 15 — its cost is negligible at 168 distinct labels. Sum over the whole run:
   roughly 15–25 s unprofiled — worth batching only after A–C.
6. **S2 reruns the full S3–S5 build per appending round — CONFIRMED and measured as the
   largest wall-clock item on lexicon-change runs.** This run's S2 appended rows in rounds 1
   and 2 (LexiqueSynthetic.tsv +17 rows), forcing two extra S3–S5 rebuild passes
   (`loadOrBuildDictionary` 131.8 s for pass 2; pass 3 logged 1389.8 s but is **mostly py-spy
   artifact** — the pass did the same 183/27/140 multiphoneme-pair scan as pass 1 on +17
   words while the sampler was 5–15 s behind; treat pass 3 as ~135 s real). S2 step total
   1855.2 s logged; corrected ≈ 600 s, of which ≈ 270 s is the two avoidable-in-principle
   rebuild passes and ≈ 330 s appender scans. `extractDiscriminatingFeatures` running twice
   per `completeVerbParadigms` invocation is CONFIRMED: exactly 2 calls, 17.9 s of the
   130.3 s profiled run (once at util/completeVerbParadigms.py:377, once inside
   `confirmCandidates`).
7. **Elicitation computes the opposition cross-product 3× — CONFIRMED, small.**
   src/elicitation.py:613 (`resolveGroupPressSets`), :622 (`validateElicitation` →
   `resolveGroupPressSets` again) and :629 (`resolvePressByCombination` again). Measured:
   `resolvePressByCombination` 3 calls, 5.4 s cum inside the 25.1 s `resolveAndWritePressSets`
   (profiled); ~2 s unprofiled. The phase costs 29.2 s in the pipeline.
8. **No profiler existed — now it does**: 10 `.pstats` + extracts + one whole-run flame graph
   under `scratch/profiles/` (see appendix). S2's appender rounds remain unmeasured by
   `util/_timing` (only whole-step `step` lines exist).

**New finding not in the plan:** the S3–S5 build cost is multiplicative in the corpus's
multiphoneme inventory (`lexicalSyllabicPartAmbiguityScore` is called once per
(multiphoneme-pair × matching syllable × phonological word)); any S2 appender that
introduces new coda clusters raises every subsequent S3 pass, converged or not.

## 3. Ranked proposals

Sizing basis: unprofiled numbers from this run (~575–900 s converged run; ~1100 s when S2
appends). Savings are per full `python dictionary.py` run unless stated.

### A. Persist the disambiguated theory as `DisambiguatedTheory.pickle` (user-approved)
- **Change**: write the pickle in `util/build_disambiguated_theory.py` after
  `buildDisambiguatedTheory`; load it in `util/_theoryio.py:58/82`
  (`loadDisambiguatedTheory` / `loadPhoneticAndDisambiguatedTheory`), envelope
  `(fingerprint, theory)` with fingerprint = md5 of LexiqueMixte.tsv, LexiqueSynthetic.tsv,
  starboard3h.json, keypress_groups.json, resolved_press_sets.json — mismatch ⇒ recompute
  (unlike the existing never-checked pickles, because `elicitation_answers.json` is
  hand-edited between runs). Register in `PICKLE_CACHE_PATHS`
  (util/build_synthetic_lexicon.py:31), `.gitignore`, and the rm-pickle discipline in
  CLAUDE.md / docs/PIPELINE.md. While there, thread `wordToStrokes` /
  `wordsByOrthoLemme` through instead of rebuilding (dictionary.py:408–409 vs
  src/ambiguitychecker.py:980/1220/1248 and util/export_practice_words.py:183–184).
- **Expected saving (measured)**: eliminates 5 of 6 `buildDisambiguatedTheory` calls × 44.7 s
  = **~220 s/run** (exporters collapse to unpickle + render; the S7 and realization calls
  can share one computation). Plan's 150–220 s estimate confirmed at the top of the range.
- **Risk**: staleness silently producing a wrong theory — mitigated by the fingerprint (md5s
  of all five inputs); pickle size ~ that of PhoneticTheory.pickle.
- **Determinism**: none threatened — same computation, cached; artifacts must stay
  byte-identical.

### B. `realizeKeypressGroupsAsExtraStroke` inner loop (src/ambiguitychecker.py:928–1200)
- **Change**: compute `induced` once per (candidate, words) and share it between `_feasible`
  (:1041) and `_candidateCost` (:1089); memoize `getStrokeCost(stroke[-1], "coda")` per
  distinct key-tuple (3.26M calls collapse to the few thousand distinct coda chords);
  memoize `_appendCodaExtraStroke` per (word, keys); precompute the
  `finger → {(key,)}` sets in `getStrokeCost` (src/keyboard.py:546) instead of
  `(key,) in fingerKeypress.keys()` per (finger, key).
- **Expected saving (measured)**: of the ~40–45 s unprofiled per call,
  `getStrokeCost`+`_composedInduced`+`__getitem__`+`sorted` ≈ 30 s; sharing the
  feasibility/cost pass halves the `_composedInduced`+`getStrokeCost` work again. Estimate
  **~25–35 s per remaining invocation**; with A in place (1–2 invocations) that is
  **~30–60 s/run**, and it also shrinks the one unavoidable S7 computation.
- **Risk**: medium — the ranking ties in `_bestCandidate` (:1119) must produce identical
  orderings; keep candidate/group enumeration order byte-identical.
- **Determinism**: memo tables must be keyed on immutable tuples; no iteration-order change.

### C. S3/S5 build — retargeted at the measured hot spot
- **Change (revised from the plan)**: the plan's `(phoneme, part) → strokes` index,
  single-pass `readCorpus` and `deepcopy([])` removal are confirmed *not* where the time is
  (6.8 s / 9.8 s profiled — keep them as trivial cleanups). The measured target is
  `lexicalSyllabicPartAmbiguityScore` (src/grammar.py:975): hoist the per-syllable
  `phonoWords` frequency sums (48.4M `sum` calls) into a precomputed per-(syllable,
  phonoword) value; avoid `Word.replaceSyllables` (48.2M calls) by caching the mutated
  syllable name per (syllable, target multiphoneme, part) — the mutation result is reused
  across every phonological word of the same syllable.
- **Expected saving (measured)**: ~90 s unprofiled per S3 pass (pass 1 measured 113.5 s
  total). Realistic 40–60 s per pass ⇒ **~50 s/run converged, ~150 s/run when S2 appends**
  (3 passes). `Dictionary.words` insertion order must not change.
- **Risk**: medium — the ambiguity scores feed `Syllable.optimizeBiphonemeOrder` and the
  layout cost model; any value change alters the theory. Pure caching keeps values identical.
- **Determinism**: caches keyed on tuples; no set iteration introduced.

### D. S2 — deduplicate the discriminator passes and measure the rounds
- **Change**: compute `extractDiscriminatingFeatures` once per
  `completeVerbParadigms` invocation and pass it into `confirmCandidates`
  (util/completeVerbParadigms.py:377 + `confirmCandidates`); add `util._timing` `phase`
  lines around each `runAppendersOnce()` round (util/build_synthetic_lexicon.py:82) — this
  run had to infer round costs from timestamps. Longer term: the two full S3–S5 rebuild
  passes per appending round (~135 s each, measured pass 2) are the real S2 cost;
  incremental appending is architecturally blocked (`Syllable` class-level state,
  src/grammar.py:451–466), so gate any further work on the new per-round measurements.
- **Expected saving (measured)**: the dedup saves ~9 s profiled (~4 s unprofiled) per
  appender round; measurement costs nothing. The rebuild-pass issue is ~270 s but only on
  appending runs — out of scope for a quick win, in scope for design.
- **Risk**: low (pure sharing of an immutable result).
- **Determinism**: none threatened.

### E. Memoisation sweep (demoted below D by the data)
- **Change**: per-exporter memo for `renderFinalStrokesToRTFCRE` /
  `strokesToRTFCRE` (190k–716k calls each), dict-based `keyDisplayName`
  (src/keyboard.py:654), `formatReadingsLabel` (util/export_practice_words.py:113),
  module-level `loadReform1990DoubletPairs` (src/ambiguitychecker.py:92), parallel-set
  membership in `stenoToWords` (util/export_plover_dictionary.py:44–52), `canonicalizeStrokes`
  memo. All memos return immutable/shared-safe values.
- **Expected saving (measured)**: ~15–25 s unprofiled across the four exporters — worth
  doing in the same PR as A (the exporters become render-bound once A lands, and these rows
  then dominate what's left).
- **Risk**: low. **Determinism**: memos must not change any ordering.

### F. Elicitation — compute the cross-product once
- **Change**: `resolveAndWritePressSets` (src/elicitation.py:596–647) calls
  `resolveGroupPressSets`, then `validateElicitation` (which reruns it), then
  `resolvePressByCombination` again; compute once, share the result.
- **Expected saving (measured)**: ~2 s unprofiled of the 29.2 s phase — the smallest item;
  do it for clarity, not speed.
- **Risk**: low.

## 4. Per-batch verification protocol (for the implementer)

1. `pytest src/test/` (704 test functions at this HEAD; CLAUDE.md's "649" is stale).
2. Baseline first: `rm -f *.pickle` + full `python dictionary.py`, then `md5sum` of
   `phonetic_theory.tsv`, `disambiguated_theory.tsv`, `resolved_press_sets.json`,
   `keypress_groups.json`, `realization_report.json`, `plover_stenalgo_dictionary.json`,
   `steno-trainer/public/data/*.json` (note: `resources/LexiqueSynthetic.tsv` on this branch
   is now converged +17 rows — commit or revert it first so the baseline is stable).
3. Per change batch: same rebuild, compare md5s — they must be identical; record the
   `pipeline_timings.log` step deltas alongside.
4. A md5 mismatch after a memoisation/caching change almost certainly means an
   iteration-order leak — investigate, never sort-to-match.
5. For A specifically: also test the miss path (touch one fingerprint input ⇒ recompute ⇒
   identical artifacts) and the S2 interaction (S2 must delete the new pickle when it
   appends rows — it already deletes `PICKLE_CACHE_PATHS`).

## 5. Baseline caveat

Before trusting md5 comparisons across machines/runs: run the pipeline twice from clean
pickles and diff the artifact md5s. Partial evidence from this effort is positive —
`keypress_groups.json`, `resolved_press_sets.json`, `practice-words.json` and
`practice-sentences.json` were regenerated byte-identical to the committed versions in a
single run with `PYTHONHASHSEED` unset — but a genuine two-clean-runs comparison was not
performed here (machine-time budget went to the profiles). If instability appears, fix
`PYTHONHASHSEED=0` in the protocol and investigate the string-set iteration that leaked.

## 6. Implementation handoff (for a fresh session implementing A–F)

Everything needed to implement is in this file; no conversation context is required.

- **Execution order**: A alone first (isolated commit so a bisect is possible), then C
  (biggest remaining measured item), then B, then E in the same PR as whatever exporters
  it touches, then D, then F. One batch per commit; run the §4 protocol after each.
- **Before the first baseline**: decide the fate of the four modified tracked files listed
  in the Appendix (`resources/LexiqueSynthetic.tsv` + its three regenerated outputs) —
  commit them together or revert all four together. Never baseline with them dangling.
- **Rules of engagement**: interpreter `/home/jfsp/stenalgo/env/bin/python`; work in this
  worktree only; run heavy steps serially (7 GB RAM); `pytest src/test/` green plus the
  §4 md5-identical rebuild after every batch; on a md5 mismatch, suspect an
  iteration-order leak from a new cache/memo — investigate, never sort-to-match; for A,
  also test the fingerprint-miss path and that S2's `PICKLE_CACHE_PATHS` deletion covers
  the new pickle.
- **Update the docs when A lands**: CLAUDE.md (rm-pickle discipline, new output),
  docs/PIPELINE.md (rebuild table), `.gitignore`.

## Appendix — artifacts and final state

- `scratch/profiles/`: 10 `.pstats` + 10 `.top.txt` extracts, `pipeline.svg` (py-spy whole
  run, 60,661 samples), `pipeline_top_functions.txt` (inclusive shares),
  `pipeline_timings.before.txt` (log snapshot before the whole run), `pyspy_run.log`.
- Whole-run `pipeline_timings.log` step times (this run): S3-S5 pass 1 132.6 s; S2 1855.2 s
  (distorted, see Finding 6; ≈600 s corrected); Elicitation 29.2 s; Grouping 36.1 s; S7
  55.4 s; Realization 44.9 s; Plover dict 56.2 s; key table 0.0 s; keyboard layout 0.0 s;
  word drills 61.3 s; sentences 61.9 s; definitions 58.9 s; total 2391.8 s.
- `git status --short` at report time:

```
 M plover_stenalgo_dictionary.json
 M realization_report.json
 M resources/LexiqueSynthetic.tsv
 M steno-trainer/public/data/definitions.json
?? scratch/profiles/
```

  (plus this file, `PERF_REVIEW_2026-09-29.md`, untracked). The four modified tracked files
  are the expected downstream effect of S2's converged 17-row append during the profiled
  whole run; restoring them is the user's call, but note that reverting only the outputs and
  not `LexiqueSynthetic.tsv` would leave the repo inconsistent.
