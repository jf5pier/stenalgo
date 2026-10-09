# Performance review round 2 — 2026-09-29 (branch `performance-optim`, HEAD 2fb3488)

Follow-up to `PERF_REVIEW_2026-09-29.md` (round 1, proposals A–F, all landed; pipeline
596.4 → 251.0 s). Mission per `PERF_ROUND2_HANDOFF.md`: re-profile the optimized code,
produce a fresh ranked list, implement what is worth it. No round-1 line numbers were
reused; everything below is from this session's measurements.

## 1. Method

Same recipe as round 1, updated per the handoff:

- Per-step cProfile, each step its own subprocess, dependency order, clean pickles
  first (`Dictionary.pickle`, `PhoneticTheory.pickle`, `DisambiguatedTheory.pickle`
  all `rm -f`'d; S7 profiled before the exporters so they exercise the cache-hit path
  exactly as the pipeline does). The four S2 appenders profiled individually (the
  wrapper only subprocesses). 13 `.pstats` + top-20 extracts (cumulative + tottime)
  under `scratch/profiles2/`; per-step driver timestamps in `scratch/profiles2/driver.log`.
- Whole run: `py-spy record --rate 25 --subprocesses --format speedscope` over
  `dictionary.py` from clean pickles → `scratch/profiles2/pipeline.speedscope`
  (302.6 s of samples; run wall 290 s under py-spy vs 251.0 s clean). Shares parsed
  from the speedscope JSON (inclusive per function, aggregated across all 21 process
  profiles, fork workers included — this is the only view that sees the S3 fork
  workers and the S2 appenders without cProfile's tqdm-lock attribution artifacts).
- All artifacts md5-identical to `scratch/baseline_A_md5s.txt` after all profiling
  runs (7th+ consecutive clean-pickle byte-identical rebuild).
- cProfile inflation this round ≈ 1.8–2.6× (step-dependent); unprofiled numbers below
  come from `pipeline_timings.log` (251.0 s run) and py-spy shares, cProfile only for
  call counts and intra-step composition.

### Measured step times

| Step | cProfile total (s) | clean wall (s, timings log) |
|---|---|---|
| S3-S5 `util.build_phonetic_theory` | 65.7 | 36.8 (pass 1) |
| S2.1 `completeVerbParadigms --apply` | 106.2* | ~45 (inside S2's 61.8) |
| S2.2 `generateMissingNomAdjForms --apply` | 18.4 | ~8 |
| S2.3/S2.4 payer/asseoir | 1.2 / 1.1 | ~1 each |
| Elicitation `src.elicitation` (mode both) | 30.1 | 22.9 |
| Grouping | 27.3 | 24.0 |
| S7 `build_disambiguated_theory` | 43.3 | 26.4 (unpickle 4.0, build 16.8, pickle 1.7, TSV 1.9+2) |
| Realization report | 27.3 | 15.8 |
| Plover dict | 15.8 | 11.7 |
| Trainer words | 26.0 | 17.8 |
| Trainer sentences | 18.5 | 13.9 |
| Trainer definitions | 34.6 | 20.0 |

\* 29.5 s of the S2.1 cProfile total is tqdm lock-acquire attribution artifact
   (cProfile + tqdm monitor thread); use py-spy shares for S2.1 composition.

### Whole-run inclusive shares (py-spy, 302.6 s sampled)

Top functions: `extractDiscriminatingFeatures` 46.4 s (15.3%, all in S2.1's two
invocations); CP-SAT `solve` 19.0 (grouping, untouchable); `__hash__` (Word) 19.6
(6.5%, split S2.1 26.7M calls / S7+realization 15.7M); `buildDiscriminatorSelection`
19.4; `realizeKeypressGroupsAsExtraStroke` 20.9 (S7 + realization, by design);
`_getLexicalAmbiguityScores` fork workers 24.1 across 3 workers (~8-10 s wall);
`buildWordsByOrthoLemme` 14.8 (4.9%, rebuilt in S7 + every exporter);
`loadPhoneticAndDisambiguatedTheory` 35.7 total (11.8%: `loadCachedDisambiguatedTheory`
unpickle 19.6 + `_loadDictionaryAndPhoneticTheory` 21.7 — overlapping);
`buildPhoneticTheory` 6.8 incl (`getStrokesOfPhoneme` 4.4+); `canonicalizeStrokes` 6.6.

## 2. Findings

1. **S2.1 is now the single biggest CPU consumer, and it is the discriminator
   feature machinery, not the theory loads.** `extractDiscriminatingFeatures` runs
   twice (baseline + augmented inside `confirmCandidates`, 30.4 s incl) = 46.4 s
   sampled ≈ 15% of the whole run. Hot lines (py-spy self time):
   - featureextractor.py:48 `wordFeatures[word] = wordFeatures.get(word, []) +
     [selectedFeature]` — O(features²) list copying per word, 4.5 s;
   - the per-(stroke,lemme) feature scan (lines 78–131) ≈ 10 s self across lines,
     including the line-127 `filter(lambda w: w.ortho == ortho, ...)` (5.1M calls);
   - the greedy ordering loop (lines 148–181): its `leftOverDiscriminatedFrom`
     rebuild (10.2M `set.add` in cProfile) feeds only a print statement and the
     loop's `leftOverFeatures` re-sort per iteration (O(F²·W) + O(F²) complexity);
   - `buildFeasibleDiscriminatorOptions` (12.2 s incl): for every word of a
     multi-word group it scans ALL of `wordIsDiscrminatedByFeature` (26.7M
     `Word.__hash__` calls) — an inverted index makes it O(words + features).
   Each appender also re-loads theory from pickles (~2 s each), second-order.
2. **Theory loading is the biggest cluster: ~35.7 s sampled (~12%, ≈30 s clean).**
   ~10 subprocesses unpickle Dictionary (59 MB) + PhoneticTheory (53 MB) +
   DisambiguatedTheory (55.8 MB). Two structural wastes: (a) on a
   DisambiguatedTheory cache HIT the `Dictionary` object is never used by
   `loadPhoneticAndDisambiguatedTheory`'s callers, yet 59 MB are unpickled first;
   (b) every consumer rebuilds `buildWordToStrokes`/`buildWordsByOrthoLemme`
   (14.8 s sampled for the latter alone) although S7 already computed both when
   writing the cache — they can ride in the pickle envelope.
3. **Round-1 E's `canonicalizeStrokes` memo is ineffective: `@lru_cache` defaults
   to maxsize=128 while callers present ~80k distinct stroke tuples.** Elicititation
   alone: 79,623 calls, 1.87M inner iterations (i.e. ~every call recomputed). Fix is
   `maxsize=None` (pure tuple→tuple). Same-class bug: none other found —
   `loadReform1990DoubletPairs` is a no-arg cache, fine.
4. **`getStrokesOfPhoneme` scans the whole layout dict per call** (keyboard.py:478),
   1.14M calls / 5.9 s cProfile in S3-S5 alone (via `getStrokeOfSyllableByPart` in
   `buildPhoneticTheory`); layout is frozen during that loop → per-instance lazy
   memo invalidated by `_dropRenderMemos` (the E pattern) collapses it to ~66
   lookups. Also hit in `realizeKeypressGroupsAsExtraStroke`'s codaKeysOf build and
   `generateBaseKeymap`.
5. **`json.dump` never uses the C encoder** — `json.dump` chunks via pure-Python
   `iterencode`; only `json.dumps` is one-shot C-accelerated, and only without
   `indent`. The only hot no-indent dump is definitions.json (6.0 s cProfile);
   `f.write(json.dumps(...))` is byte-identical there. The indent=1 dumps
   (questionnaire, resolved_press_sets, practice words/sentences, keypress groups,
   plover dict) cannot switch to the C encoder without changing bytes — left alone.
6. **The S3 fork stage still has round-1 C's original pattern in
   `lexicalPhonemeAmbiguityScore`** (grammar.py:904-987): per-phono-word
   `sum(map(...))` over `phonoWords` buckets, `word.replaceSyllables`, and a
   `getSyllable(p1_to_p2)` inside the word loop (hoistable). The stage costs 24.1 s
   sampled across 3 parallel workers ≈ 8-10 s wall of the 36.8 s step; the
   multiphoneme (serial) stage C already fixed is now only 9.0 s cProfile.
   `phonoWordFrequencySums()` exists and is safe to reuse here; iteration order of
   `phonoWords` dicts is untouched by the substitution (same keys, same order).
7. **S7/realization residual is `_feasible`/`_composedInduced`** (1.65M calls,
   15.7M Word hashes; realizeKeypressGroupsAsExtraStroke 20.9 s incl across its two
   invocations). The duplication between S7 and the realization report is by design
   (report re-runs the assignment against ground truth); persisting S7's assignment
   for the report to REUSE would change the S6/S7 contract — design-level, needs
   user sign-off. Not attempted this round.
8. **Grouping = 23 CP-SAT solves, 19.0 s** — solver-dominated; not touched.
9. `renderFinalStrokesToRTFCRE` (190k calls × 4 exporters, 3.2-5.4 s cProfile each)
   has ~no duplicate chords within a step (practice-words: 10k records, 10k distinct),
   so a plain memo is useless; the only structural fix is precomputing rendered
   strings once in S7 into the envelope — folded into proposal R2b as an option.
10. Refuted/deprioritized this round: `readCorpus` (3.2 s sampled — small);
    `Word.__post_init__` in S2.2 (375k Words rebuilt from TSVs — would need the
    appender to switch to the pickle as data source, a semantic change; left alone);
    elicitation json dumps (indent=1, C encoder impossible);
    `formatReadingsLabel` (1.0 s); `strokesToString` in S7's TSV write (1.3 s).

## 3. Ranked proposals

Savings are per converged `python dictionary.py` run (251.0 s baseline), realistic
estimates from the shares above.

### R2a. Trivial memos + C-encoder — ~7 s, lowest risk
- `canonicalizeStrokes`: `@lru_cache(maxsize=None)` (src/keyboard.py:32).
- `getStrokesOfPhoneme`: per-instance lazy memo keyed (phoneme, syllabicPart),
  dropped in `_dropRenderMemos` (src/keyboard.py:478,addToLayout/removeFromLayout).
- definitions.json: `f.write(json.dumps(...))` instead of `json.dump` (identical
  bytes — C encoder, no indent).
**Expected**: canonicalize ~3 s (elicitation+S7+exporters), getStrokesOfPhoneme ~2 s
(+2 s more per extra S3 pass on appending runs), definitions dump ~2.5 s.
**Determinism**: all three are pure caches/identical-output rewrites.

### R2b. Theory-load restructuring — ~15 s, medium risk (envelope format bump)
1. Check the DisambiguatedTheory fingerprint BEFORE unpickling Dictionary;
   on a hit, skip `Dictionary.pickle` entirely (its object is unused by
   `loadPhoneticAndDisambiguatedTheory`'s callers on that path). Miss path unchanged.
2. Store `wordToStrokes` + `wordsByOrthoLemme` in the DisambiguatedTheory pickle
   envelope (S7 already computes both; `_ENVELOPE_FORMAT` 1→2). Loaders expose them
   so `buildReadingsByWord` and `writeDisambiguatedTheory` stop rebuilding
   (14.8 s sampled for `buildWordsByOrthoLemme` across the run).
**Risk**: envelope shape change — every consumer must handle format 1 (miss →
recompute) — the loader already treats wrong format as a miss, so old pickles just
rebuild once. Elicititation keeps loading Dictionary (it needs `frequentWords`).
**Determinism**: the stored dicts are the exact objects the recomputation would build
(same insertion order — they are pickled straight from S7's build).

### R2c. S2.1 discriminator machinery — ~12-18 s, medium risk (order-sensitive)
- `buildFeasibleDiscriminatorOptions`: inverted index (word → features) built once
  per call from `wordIsDiscrminatedByFeature.items()`; per-group sets then come from
  the index. Set CONTENTS unchanged (same members), and every downstream consumer is
  order-insensitive (membership tests, `sorted(featureCounts)`, unions) — kills
  26.7M Word-hash calls.
- featureextractor.py:48: replace the `get()+[f]` list copy with `.setdefault(word,
  []).append(f)` — same resulting list order.
- The greedy ordering loop: compute `leftOverDiscriminatedFrom[selectedFeature]`
  lazily (only the value the print uses) instead of rebuilding every feature's set
  every iteration; same printed values, same `orderedFeaturesSelected`.
**Determinism**: no iteration order changes; verified by md5 of downstream artifacts
(LexiqueSynthetic.tsv is S2.1's output — the converged no-append run must leave it
byte-identical, and the round's full rebuild checks every artifact).

### R2d. S3 fork-stage C-fix — ~3-4 s (wall capped by slowest worker), medium risk
- `lexicalPhonemeAmbiguityScore`: reuse `phonoWordFrequencySums()` for the
  per-bucket base scores; hoist `getSyllable(p1_to_p2)` out of the per-word loop
  (it depends only on syll1/part); keep `word.replaceSyllables` only where the
  mutated phonology genuinely varies per word (it does — keyed by phono_word1) but
  note the bucket-first-Word trick used by the multiphoneme fix does NOT apply in
  the triple-ambiguity branch (two different mutated syllables per word).
- Float-identity: substituting `phonoWordFrequencySums()[key]` for
  `sum(map(lambda w: w.frequency, bucket))` is the same additions in the same order
  (the cache is built with exactly that sum) → bit-identical scores.

### Not attempted (recorded for the user)
- Persisting S7's physical assignment for `build_realization_report` to reuse
  (~8 s) — changes the S6/S7 contract (report is an independent verification by
  design). Design-level; needs sign-off.
- S2 appender theory-load sharing / S2.2 reading pickles instead of TSVs — semantic
  changes to what data appenders see; out of scope for a perf pass.
- Slimming the Word payload of DisambiguatedTheory.pickle (key by identity tuple
  instead of Word objects) — touches every consumer for ~2-3 s; poor ratio now.

**Combined realistic expectation: 251 → ~215-220 s.**

## 4. Verification protocol (unchanged, §5 of the handoff)

Per batch: `pytest src/test/` green (716), mypy on touched modules, then
`rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle &&
python dictionary.py` and md5-compare against `scratch/baseline_A_md5s.txt`
(all identical). R2b additionally: fingerprint-miss path (touch an input →
recompute → identical artifacts), and format-1-pickle handling (stale envelope →
miss → rebuild). One batch per commit. On md5 mismatch after a caching change:
suspect an iteration-order leak; investigate, never sort-to-match.

## 5. Outcome

(filled in as batches land)

| Batch | Commit | Pipeline (s) | Notes |
|---|---|---|---|
| baseline (round-1 end) | 2fb3488 | 251.0 | |
| R2a | e479ea9 | 242.6 | S3-S5 36.8→30.2, definitions 20.0→17.1; md5s identical |
| R2b | d7df8d9 | 215.4 | Plover dict 11.8→4.6 (hit loads no large pickle), words 17.9→11.2, sentences 13.9→9.3, definitions 17.1→11.9, realization 16.5→14.3; md5s identical; miss path + format-1-miss tested |
| R2c | 6aef21f | 211.1 | S2 appender round 61.8→52.6 (extractDiscriminatingFeatures + buildFeasibleDiscriminatorOptions); LexiqueSynthetic.tsv unchanged (S2 still converged) |
| R2d | 2d93978 | 208.2 | S3-S5 pass 1 30.3→29.1 (fork-stage fix; wall capped by slowest worker) |

**Total round 2: 251.0 → 208.2 s (−17%). Round 1 + 2 together: 596.4 → 208.2 s (−65%).**

Residual step sizes after R2d (next-round targets, in order): S2 round 52.6
(inside it, `deriveConjugationEndingTables`+`findStructuralCandidates` ≈ 10 s,
theory loads ≈ 2 s); Grouping 23.8 (CP-SAT, 19 s); S7 26.4 (build 19.1:
`realizeKeypressGroupsAsExtraStroke`'s `_feasible`/`_composedInduced`; the
design-level fix — persisting S7's assignment for the realization report to
reuse — remains the single biggest structural idea, needs user sign-off);
S3-S5 29.1 (readCorpus 3.2 s sampled, fork stages); elicitation 22.9 (json
dumps with indent=1, serialize ≈ 8 s — no stdlib C-encoder path without changing
bytes); trainer exporters 11-12 each (render + json, both fairly flat now).
