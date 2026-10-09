# Performance round 2 — handoff notes for a fresh profiling session

Written 2026-09-29 after the round-1 implementation (proposals A–F of
`PERF_REVIEW_2026-09-29.md`, all landed on `performance-optim`). Mission for the new
session: **rerun the profiling toolchain against the optimized code, produce a fresh
ranked list of optimization candidates, implement what is worth it** — same method,
same verification bar, new numbers. Do not trust round-1 line numbers: everything
moved.

## 1. Current state (starting point)

- Branch `performance-optim`, worktree `/home/jfsp/stenalgo-fix`, interpreter
  `/home/jfsp/stenalgo/env/bin/python` (bare `python` is NOT on PATH in Claude's shell).
- Round-1 commits: A `03faa64` (fingerprinted `DisambiguatedTheory.pickle`), C `6a114eb`
  (`lexicalSyllabicPartAmbiguityScore` hoist), B `5d8a843` (coda-search sharing +
  `getStrokeCost` memo), E `10c640a` (render-path memos), D `550d451` (per-round S2
  timing lines), F `ff6b465` (elicitation cross-product once), outcome note `aa681e2`
  (report §7 — read its three corrections before proposing anything).
- Converged orchestrated run is now **251.0 s** (was 596.4 s pre-round-1). Last run's
  steps: S3-S5 pass 1 **36.8**; S2 appender round **61.8**; Elicitation **22.9**;
  Grouping **24.0**; S7 **26.4** (build 16.8 + unpickle 2.9 + writes); Realization
  report **15.8**; Plover dict **11.7**; key table / layout ~0; drills **17.8**;
  sentences **13.9**; definitions **20.0**.
- There are now **three** cache pickles: `Dictionary.pickle`, `PhoneticTheory.pickle`
  (both never staleness-checked — `rm -f` after any lexicon/layout change) and
  `DisambiguatedTheory.pickle` (fingerprint-checked, self-invalidating, no manual rm).
- Six consecutive clean-pickle rebuilds produced byte-identical artifacts —
  PYTHONHASHSEED instability was not observed; don't fix what isn't broken.

## 2. How to rerun the profiling (round-1 recipe, updated)

```bash
# Per-step cProfile (serial; 7 GB RAM machine — never parallelize heavy steps)
rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle
mkdir -p scratch/profiles2
for each step, its own subprocess from clean-ish state:
  /home/jfsp/stenalgo/env/bin/python -m cProfile -o scratch/profiles2/<step>.pstats -m <module> [args]
# steps: util.build_phonetic_theory, src.elicitation, util.build_keypress_groups,
#        util.build_disambiguated_theory, util.build_realization_report,
#        util.export_plover_dictionary, util.export_practice_words,
#        util.export_practice_sentences, util.export_definitions,
#        plus: -m util.completeVerbParadigms --apply
# extract: python -c "import pstats; pstats.Stats('<f>').sort_stats('cumulative').print_stats(15)"
#          (and sort_stats('tottime')) → scratch/profiles2/<step>.top.txt

# Whole-run flame graph — py-spy at 25 Hz, NOT the default 100 (it fell >14 s behind
# within seconds last time and py-spy restarted the run):
py-spy record --rate 25 --subprocesses -o scratch/profiles2/pipeline.svg -- \
  /home/jfsp/stenalgo/env/bin/python dictionary.py
```

Round-1 pitfalls that still apply:
- py-spy's "behind in sampling" spam inflates S2-step wall times; treat py-spy numbers
  as cross-step shares only, per-step cProfile + `pipeline_timings.log` as the backbone.
  cProfile inflation on this workload was ~2.2–2.6× (unprofiled = divide roughly by 2.4).
- Always `PYTHONUNBUFFERED=1` on long redirected runs.
- S2 is converged on this tree (one round, ~62 s, appends nothing) — the appending-run
  costs (two extra S3-S5 passes) do NOT show up; note that in the report.
- Snapshot `pipeline_timings.log` before/after each run (`cp` to scratch/profiles2/).
- Do NOT `pgrep -f` inside monitor loops (matches itself); use run_in_background/PIDs.

## 3. Already optimized — do not re-propose these

| Hot spot (round-1 name) | What landed |
|---|---|
| S7 disambiguated theory recomputed per exporter | `DisambiguatedTheory.pickle`, fingerprint = md5s of LexiqueMixte/LexiqueSynthetic/starboard3h.json/keypress_groups.json/resolved_press_sets.json; S7 is the only writer |
| `lexicalSyllabicPartAmbiguityScore` (48M `replaceSyllables`, 48M `sum`) | per-syllable hoist + `Syllable.phonoWordFrequencySums()` (lazy, dropped by `__getstate__`) + `Word.replaceSyllables` = `str.replace` |
| `realizeKeypressGroupsAsExtraStroke` doubling (`_feasible` vs `_candidateCost`) | `otherKeysByWord` once per group; `_feasible` returns the induced dict; `getStrokeCost` memoized per (stroke, part) — lazily, `fromJSONFile` bypasses `__init__` |
| render path (`keyDisplayName` 2.6M calls, `strokesToRTFCRE`, `canonicalizeStrokes`) | per-instance memos invalidated by `addToLayout`/`clearLayout`; `canonicalizeStrokes`/`loadReform1990DoubletPairs` are `lru_cache`d |
| elicitation cross-product 3× | computed once in `resolveAndWritePressSets` |
| S2 round costs invisible | per-round `util._timing` phase lines in `pipeline_timings.log` |

Round-1 proposals that were checked and REFUTED (don't re-raise without new evidence):
`getStrokesOfPhoneme`/`readCorpus`-double-pass/`deepcopy` as S3 hot spots (6.8/9.8 s
profiled, second-order); D's `extractDiscriminatingFeatures` "dedup" (the baseline and
augmented passes compute different things); `formatReadingsLabel` (negligible).

## 4. Round-2 candidate hypotheses (unmeasured — verify before believing)

Ordered by residual step size:

1. **S2 appender round, 61.8 s** — now the largest step. Known internals from round-1
   profiles: `extractDiscriminatingFeatures` 17.9 s profiled for 2 calls inside
   `completeVerbParadigms` (baseline + augmented), `Word.__hash__` 98.8M calls /
   10.0 s, `deriveConjugationEndingTables`, and each of the 4 appenders re-loads
   `PhoneticTheory.pickle` (+`Dictionary.pickle` class state) in its own subprocess.
   Question to answer with per-appender phase lines: is the cost the discriminator
   passes, the theory loads, or the scans?
2. **S3-S5 pass, 36.8 s** — `readCorpus` (~10 s profiled), `analyseSyllabification`,
   `buildPhoneticTheory`, the two 59/53 MB pickle writes, and the three FORKED
   phoneme-level ambiguity stages: `syllabicAmbiguityScore` and
   `lexicalPhonemeAmbiguityScore` still contain the per-word `sum(...)` +
   per-word-`replaceSyllables` pattern that C fixed only for the multiphoneme
   (serial) function — same fix likely applies (share `phonoWordFrequencySums`,
   hoist the per-syllable mutation), but they run in 3 fork workers so the wall win
   is capped by the slowest worker.
3. **Exporters, 63.4 s total (11.7 + 17.8 + 13.9 + 20.0)** — each subprocess
   unpickles Dictionary (59 MB) + PhoneticTheory (53 MB) + DisambiguatedTheory
   (55.8 MB) and rebuilds `wordToStrokes`/`wordsByOrthoLemme` via
   `buildReadingsByWord` (export_practice_words.py:183-184, ~2×3 s profiled).
   Ideas: memoize `buildReadingsByWord`'s index into the DisambiguatedTheory pickle
   envelope; measure how much of each step is unpickle vs render (phase lines exist
   only in S7); `renderFinalStrokesToRTFCRE`'s own body is still per-call (its inner
   helpers are memoized, it is not).
4. **Grouping, 24.0 s** — 23 CP-SAT `solve` calls (22.5 s round-1 profiled). Solver
   timeouts/hints tuning is the only lever; likely leave alone.
5. **Elicitation 22.9 s / realization 15.8 s / S7 26.4 s** — S7's residual is
   `composeReservedKeyStrokesForEntries` + `findSpellingTwinWords` +
   `writeDisambiguatedTheory` (1.9 s TSV). realization's residual is the report-side
   `realizeKeypressGroupsAsExtraStroke` (already B-optimized; it duplicates S7's
   assignment search by design — a shared persisted assignment could kill ~15 s but
   changes the S6/S7 contract; design-level, only with user sign-off).
6. **Pickle I/O overall** — ~10 subprocesses each unpickle 50-60 MB objects. A
   `DisambiguatedTheory.pickle` that embeds `wordToStrokes`/`wordsByOrthoLemme`
   (or a slimmer Dictionary pickle) could shave seconds per exporter. Measure the
   unpickle share first (add `util._timing` phase lines around `_theoryio` loads).

Also worth measuring, zero-risk: `pytest src/test/` runtime (1.4-3.7 s — fine), and
`python -m util.check_conjugation_disambiguation_order` if the user still runs it.

## 5. Rules of engagement (unchanged from round 1)

- Interpreter `/home/jfsp/stenalgo/env/bin/python`; work only in this worktree; heavy
  steps serial (7 GB RAM).
- Per implementation batch: `pytest src/test/` green (716 at this HEAD), `mypy` on the
  touched modules (round 1: mypy caught a real would-be bug — a `_feasible` path left
  returning `False` instead of `None`), then the §4 rebuild-and-compare:
  `rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle &&
  python dictionary.py`, md5-compare `phonetic_theory.tsv disambiguated_theory.tsv
  resolved_press_sets.json keypress_groups.json realization_report.json
  plover_stenalgo_dictionary.json steno-trainer/public/data/*.json` against
  `scratch/baseline_A_md5s.txt` — must be identical. One batch per commit.
- On an md5 mismatch after a caching change: suspect an iteration-order leak; investigate,
  never sort-to-match.
- Float-identity matters: ambiguity scores feed the layout cost model — keep summation
  order and iteration order byte-identical when refactoring hot loops.
- Update `PERF_REVIEW_<date>.md` (round 2 = new file, cross-link round 1) and the
  memory file `perf_review_branch.md` as batches land.
- User commits directly on main normally; this branch exists for the perf work. Pushing
  or merging needs its own request.

## 6. Pointers

- `PERF_REVIEW_2026-09-29.md` — round-1 method, findings, §6 handoff, §7 outcome+corrections.
- `scratch/baseline_A_md5s.txt` — the artifact-md5 baseline all runs must reproduce.
- `scratch/verify_{A,B,C,E,F}_md5s.txt`, `scratch/verify_*_run.log` — round-1 evidence.
- `scratch/profiles/` — round-1 profiles (for before/after comparison only).
- `pipeline_timings.log` — gitignored, appended per run; round-1 final steps in §1.
