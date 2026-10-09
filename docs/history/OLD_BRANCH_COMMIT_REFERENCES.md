# Commit ids cited in the old branches (before the 2026-10-09 author rewrite)

On 2026-10-09 the 24 commits of 2024 that carried a work email were re-authored as `jf5pier`, which changed **every** commit id of
`jf5pier/stenalgo`. `main` and `lexique-completion` had the commit ids cited in their docs and comments remapped (`docs/history/COMMIT_MAP_2026-10-09.tsv`
holds the full old -> new map of the 377 commits). The other branches below were rewritten (new author, new ids) but their docs, TODO and comments
were **not** edited: they still cite the **old** ids. This file gives, for each branch, the old id as written, the new id, the commit subject, and
the files that cite it, so the citations stay resolvable when you revisit these branches. `git show <new id>` works on any branch of the rewritten repo;
the old ids no longer belong to any branch of the repo (GitHub may keep the old commits reachable by id for a while, do not rely on it).

To resolve any other old id: `grep <old id> docs/history/COMMIT_MAP_2026-10-09.tsv` (use at least the first 7 characters).

## `abbreviations`  (tip 04d358a)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `066897d` | `5699ab1` | Merge main (re schwa lexicon fix) into affix-abbreviation-rules | `docs/history/RESUME_2026-09-30-ment-regex-scope.md`, `docs/history/RESUME_2026-09-30-scope-decisions-to-engine.md`, `scratch/rules-table-H-nogrowth.md` |
| `0b5eace` | `a8779e0` | Conjugate -eter/-eler verbs on their attested rectified-è templates | `TODO.md` |
| `0fa69af` | `812eb20` | Add a soft same-key preference to the Phase G CP-SAT search | `docs/PIPELINE.md` |
| `133a766` | `03faa64` | Cache the disambiguated theory in a fingerprinted DisambiguatedTheory.pickle (perf A) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `1884dae` | `1076a3c` | Record the pushed commit SHA in the abbreviations resume | `RESUME_2026-10-02-que-families.md`, `RESUME_2026-10-03-que-briefs-overlap.md` |
| `1f4d2f1` | `76321f2` | Add Phase 0 of the abbreviation algorithm: coverage and candidate pool | `RESUME_2026-10-01-abbreviations.md` |
| `20b047f` | `3143632` | Add abbreviation-rule complexity analysis, phased plan, and round-2 questions | `RESUME_2026-10-01-abbreviations.md` |
| `2127790` | `91b1a84` | Resolve absous/dissous/repartie/repartir, closing out the 1990 reform thread | `scratch/reform1990/RESUME_2026-09-16.md` |
| `26be94d` | `629170b` | Exclude azulejo/azulejos, fixing the dictionary.py buildTheory crash | `scratch/reform1990/RESUME_2026-09-16.md` |
| `37fdc4e` | `e060dd2` | Fix verb-paradigm synthetic-generation bugs: split ambiguous Verbiste templates, correct p | `docs/PIPELINE.md` |
| `39c3ff9` | `6aef21f` | Cut the discriminator feature scan's quadratic parts (perf R2c) | `PERF_REVIEW_2026-09-29_round2.md` |
| `3c644af` | `b9ede78` | Merge affix-abbreviation-rules: Affix Abbreviation Building (S9), optional affix dictionar | `RESUME_2026-10-02-affix-merged.md` |
| `3de3273` | `525414f` | TODO: resyllabify 5 wrong -ption lemmas (absorption, résorption, ...) | `docs/history/RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `3e4f655` | `550d451` | Log one util._timing phase line per S2 appender round (perf D, measurement half) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `447fa9c` | `2d93978` | Apply the round-1 multiphoneme fix to the forked phoneme stage too (perf R2d) | `PERF_REVIEW_2026-09-29_round2.md` |
| `4516d77` | `9abb513` | Decode-time ranking: plain word > pure brief > attested > probability | `RESUME_2026-10-04-step5-plover-plugin.md` |
| `46b4878` | `2ce23f7` | Add Phase 2 Stage B: keypress assignment for expression families | `RESUME_2026-10-01-abbreviations.md` |
| `49d223c` | `a3c8d4e` | Merge lesson-generator: lessons mode, exporter, and spec | `RESUME_2026-10-01-abbreviations.md` |
| `4b53c14` | `2fb3488` | Add round-2 profiling handoff notes and round-1 evidence to the branch | `PERF_REVIEW_2026-09-29_round2.md` |
| `4e0faf2` | `51d18a7` | Suffix-word list, unigram evidence for suffix words, slot budget 20 | `RESUME_2026-10-04-selector-order-and-variants.md` |
| `4e73533` | `fbda37e` | Fix 7 elicitation answers that marked impératif via pers_2 instead of itself | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md` |
| `5087bd5` | `2a6bad2` | Give the 164 re+consonant words the schwa of the re- prefix instead of /ø/ | `RESUME_2026-10-01-abbreviations.md`, `docs/history/RESUME_2026-09-30-ment-regex-scope.md`, `docs/history/RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `5230068` | `b5aca46` | Add French n-gram frequency data, TAO abbreviations, and queryViewer corpus fix | `RESUME_2026-10-01-abbreviations.md` |
| `5ae0118` | `4ed85f0` | Snapshot pending doc edits and session notes before docs refactor | `docs/PIPELINE.md` |
| `62435c6` | `9e8e5d7` | Selector order by stacking mass and gender/number, order ban for commutative attach pairs, | `RESUME_2026-10-04-selector-order-and-variants.md` |
| `6609e63` | `e479ea9` | Fix round-1 memos: unbounded canonicalizeStrokes cache, getStrokesOfPhoneme memo, C-encode | `PERF_REVIEW_2026-09-29_round2.md` |
| `688c74d` | `9114fbb` | Fix same-spelling-homograph over-marking (calmez/-kt bug) and elicitation data errors | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md`, `util/build_keypress_groups.py` |
| `69611b1` | `96f63a9` | Add Phase 3: the expression rule report and composability matrix | `RESUME_2026-10-01-abbreviations.md` |
| `70bd2e2` | `6a114eb` | Hoist per-syllable invariants out of lexicalSyllabicPartAmbiguityScore (perf C) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `755b4f2` | `64d3558` | Wire the decided affix growth scopes and fusions into the engine | `PLAN_2026-10-01-abbreviations-algorithm.md`, `docs/history/RESUME_2026-10-01-option-c-engine.md` |
| `7c0ee5f` | `5068501` | Refresh affix sweep outputs and reference diff after the -ption/-ction lexicon fix | `docs/history/FINDINGS_2026-09-29-affix-exceptions-analysis.md`, `docs/history/RESUME_2026-09-29-affix-after-lexicon-fix.md`, `docs/history/RESUME_2026-09-29-affix-partial-overlap-flag.md` (+1) |
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `7f2e6fa` | `dc243c6` | Fix attach stacking: syllabic-key disjointness for co-occurring families | `RESUME_2026-10-01-abbreviations.md` |
| `7f4de93` | `2a6f2b1` | Add category 3 (loanwords) and interpeller/interpeler to 1990 reform tooling | `scratch/reform1990/RESUME_2026-09-16.md` |
| `82609f7` | `ff6b465` | Compute the elicitation opposition cross-product once (perf F) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `8330b8e` | `b3b7fd5` | Persist Phase G's adopted keypress assignment (nbr_p bound to p) | `docs/PIPELINE.md` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `855627e` | `9ea9d51` | Resyllabify the five -ption lemmas that put the p in the last syllable's onset | `docs/history/PLAN_2026-09-29-affix-scan-speedup.md`, `docs/history/RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `8630552` | `30662bc` | Checkpoint: one-key-per-territory patch for affix rule selection (superseded) | `docs/history/PLAN_2026-09-28-affix-single-generator-rewrite.md`, `docs/history/RESUME_2026-09-28-affix-territory-merge.md` |
| `88ecc2b` | `d7df8d9` | Carry the word indexes in DisambiguatedTheory.pickle; skip Dictionary.pickle on cache hits | `PERF_REVIEW_2026-09-29_round2.md` |
| `8e811b2` | `c9d3b68` | Keep the k of -ction in the coda when the word also contains an x | `PERF_REVIEW_2026-09-29.md`, `docs/history/PLAN_2026-09-29-affix-scan-speedup.md`, `docs/history/RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `93a36eb` | `e31e6a7` | Speed up the affix sweep about 8x: prune keypresses by a pass-1 exception-rate floor | `docs/history/FINDINGS_2026-09-29-affix-exceptions-analysis.md`, `docs/history/RESUME_2026-09-29-affix-after-lexicon-fix.md`, `docs/history/RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `94000fe` | `58d0480` | Add the que-families resume for the abbreviations branch | `RESUME_2026-10-03-que-briefs-overlap.md` |
| `95a9555` | `6006f4c` | Add Phase 2 Stage A: proxy selection over the expression pool | `RESUME_2026-10-01-abbreviations.md` |
| `9bc2219` | `fb5b79d` | Suffix twin fix: a trailing prefix-rule particle yields to its suffix rule | `RESUME_2026-10-03-que-briefs-overlap.md` |
| `9e08475` | `4f1a837` | Add two TODO items: conjugation markings in affix abbreviations, Plover conjugation-engine | `RESUME_2026-10-02-affix-merged.md` |
| `9e2ac38` | `b340fe1` | Rerun the affix pool and H sweep on the re-schwa lexicon; add --settings to the sweep | `docs/history/RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `a6e4bd8` | `39f92d7` | Merge affix-abbreviation-rules into abbreviations | `RESUME_2026-10-01-abbreviations.md` |
| `a9b85cf` | `27668cf` | Keep the k of -ction in the coda when the word also contains an x | `docs/history/RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `ae6ad5d` | `923c657` | Rebuild the n-gram TSVs with real orthography and particle word-units | `PLAN_2026-10-01-abbreviations-algorithm.md`, `RESUME_2026-10-01-abbreviations.md` |
| `afa8fac` | `9f871e7` | Resyllabify the five -ption lemmas that put the p in the last syllable's onset | `docs/history/RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `bde9a34` | `813ed6e` | Plan the affix pipeline integration; mark the older affix notes historical | `RESUME_2026-10-01-abbreviations.md` |
| `bf2562b` | `cb6f6a7` | Register the Q3 decision: circumfix as decomposition with disjoint keys | `RESUME_2026-10-01-abbreviations.md` |
| `c5c78ac` | `242b3d8` | Register round-2 answers for the abbreviation algorithm | `RESUME_2026-10-01-abbreviations.md` |
| `ca153cf` | `5d8a843` | Share the composed-stroke pass and memoize getStrokeCost in the coda key search (perf B) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `cea684f` | `d571891` | Affix search: default --workers capped at 8 | `RESUME_2026-10-03-que-briefs-overlap.md` |
| `d2d4fa0` | `3a84cc5` | Re-converge LexiqueSynthetic.tsv against the adaptive shared-discriminator selection | `scratch/config-extraction-plan-full-detail.md`, `scratch/config-extraction-plan.md` |
| `da7fcee` | `f505adb` | Regenerate LexiqueMixte.tsv from the current committed lexique.py | `scratch/reform1990/RESUME_2026-09-16.md` |
| `dc5bc93` | `bd6c659` | Move historical plan/design/findings/resume notes to docs/history/ | `RESUME_2026-10-02-affix-merged.md` |
| `dce8dfb` | `766c0bf` | Add Phase 2 Stage C: joint repair and the collision audit | `RESUME_2026-10-01-abbreviations.md` |
| `de27537` | `c52fd93` | Add forced briefs with multi-stroke eligibility, pool fragment fix, budget sweep | `RESUME_2026-10-01-abbreviations.md` |
| `df71a24` | `649809f` | Rename phase-lettered files and identifiers to descriptive names | `docs/GLOSSARY.md` |
| `e0b7514` | `e8444c3` | Reserve attach chords against forced briefs; attach-as-standalone measurement | `PLAN_2026-10-04-expression-decoder.md`, `RESULTS_2026-10-04-expression-decoder.md` |
| `e3b0358` | `d1fceb0` | Fix Verbiste template/lexicon defects flagged by cross-checker | `TODO.md`, `docs/PIPELINE.md`, `util/fixParticipleGenderPhon.py` |
| `e5a7966` | `671902a` | Record the re/ré remeasurement and the ra/Re phonology TODO | `docs/history/RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `ebb7a2e` | `fb7a471` | Refresh the affix resume note: tidy done, trial sheet ready, two new TODOs | `affix_selection_speedup_notes.md` |
| `f0f4eed` | `10c640a` | Memoize the render path: keyDisplayName, strokesToRTFCRE, canonicalizeStrokes (perf E) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `f4141e8` | `aa681e2` | Record the implementation outcome in the performance review report | `PERF_ROUND2_HANDOFF.md` |
| `f8ea2bc` | `198ab48` | Add Phase 1 of the abbreviation algorithm: the composition algebra | `RESUME_2026-10-01-abbreviations.md` |
| `fab8461` | `d691b1a` | Add Q2 rule families to the expression proxy selection | `RESUME_2026-10-01-abbreviations.md` |
| `fd7e242` | `3249c05` | Fix collision syllabification exceptions; drop subjonctif imparfait | `docs/PIPELINE.md` |

## `affix-abbreviation-rules`  (tip 813ed6e)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `066897d` | `5699ab1` | Merge main (re schwa lexicon fix) into affix-abbreviation-rules | `RESUME_2026-09-30-ment-regex-scope.md`, `RESUME_2026-09-30-scope-decisions-to-engine.md`, `scratch/rules-table-H-nogrowth.md` |
| `0b5eace` | `a8779e0` | Conjugate -eter/-eler verbs on their attested rectified-è templates | `TODO.md` |
| `0fa69af` | `812eb20` | Add a soft same-key preference to the Phase G CP-SAT search | `docs/PIPELINE.md` |
| `133a766` | `03faa64` | Cache the disambiguated theory in a fingerprinted DisambiguatedTheory.pickle (perf A) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `2127790` | `91b1a84` | Resolve absous/dissous/repartie/repartir, closing out the 1990 reform thread | `scratch/reform1990/RESUME_2026-09-16.md` |
| `26be94d` | `629170b` | Exclude azulejo/azulejos, fixing the dictionary.py buildTheory crash | `scratch/reform1990/RESUME_2026-09-16.md` |
| `37fdc4e` | `e060dd2` | Fix verb-paradigm synthetic-generation bugs: split ambiguous Verbiste templates, correct p | `docs/PIPELINE.md` |
| `39c3ff9` | `6aef21f` | Cut the discriminator feature scan's quadratic parts (perf R2c) | `PERF_REVIEW_2026-09-29_round2.md` |
| `3de3273` | `525414f` | TODO: resyllabify 5 wrong -ption lemmas (absorption, résorption, ...) | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `3e4f655` | `550d451` | Log one util._timing phase line per S2 appender round (perf D, measurement half) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `447fa9c` | `2d93978` | Apply the round-1 multiphoneme fix to the forked phoneme stage too (perf R2d) | `PERF_REVIEW_2026-09-29_round2.md` |
| `4b53c14` | `2fb3488` | Add round-2 profiling handoff notes and round-1 evidence to the branch | `PERF_REVIEW_2026-09-29_round2.md` |
| `4e73533` | `fbda37e` | Fix 7 elicitation answers that marked impératif via pers_2 instead of itself | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md` |
| `5087bd5` | `2a6bad2` | Give the 164 re+consonant words the schwa of the re- prefix instead of /ø/ | `RESUME_2026-09-30-ment-regex-scope.md`, `RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `5ae0118` | `4ed85f0` | Snapshot pending doc edits and session notes before docs refactor | `docs/PIPELINE.md` |
| `6609e63` | `e479ea9` | Fix round-1 memos: unbounded canonicalizeStrokes cache, getStrokesOfPhoneme memo, C-encode | `PERF_REVIEW_2026-09-29_round2.md` |
| `688c74d` | `9114fbb` | Fix same-spelling-homograph over-marking (calmez/-kt bug) and elicitation data errors | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md`, `util/build_keypress_groups.py` |
| `70bd2e2` | `6a114eb` | Hoist per-syllable invariants out of lexicalSyllabicPartAmbiguityScore (perf C) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `755b4f2` | `64d3558` | Wire the decided affix growth scopes and fusions into the engine | `RESUME_2026-10-01-option-c-engine.md` |
| `7c0ee5f` | `5068501` | Refresh affix sweep outputs and reference diff after the -ption/-ction lexicon fix | `FINDINGS_2026-09-29-affix-exceptions-analysis.md`, `RESUME_2026-09-29-affix-after-lexicon-fix.md`, `RESUME_2026-09-29-affix-partial-overlap-flag.md` (+1) |
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `7f4de93` | `2a6f2b1` | Add category 3 (loanwords) and interpeller/interpeler to 1990 reform tooling | `scratch/reform1990/RESUME_2026-09-16.md` |
| `82609f7` | `ff6b465` | Compute the elicitation opposition cross-product once (perf F) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `8330b8e` | `b3b7fd5` | Persist Phase G's adopted keypress assignment (nbr_p bound to p) | `docs/PIPELINE.md` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `855627e` | `9ea9d51` | Resyllabify the five -ption lemmas that put the p in the last syllable's onset | `PLAN_2026-09-29-affix-scan-speedup.md`, `RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `8630552` | `30662bc` | Checkpoint: one-key-per-territory patch for affix rule selection (superseded) | `PLAN_2026-09-28-affix-single-generator-rewrite.md`, `RESUME_2026-09-28-affix-territory-merge.md` |
| `88ecc2b` | `d7df8d9` | Carry the word indexes in DisambiguatedTheory.pickle; skip Dictionary.pickle on cache hits | `PERF_REVIEW_2026-09-29_round2.md` |
| `8e811b2` | `c9d3b68` | Keep the k of -ction in the coda when the word also contains an x | `PERF_REVIEW_2026-09-29.md`, `PLAN_2026-09-29-affix-scan-speedup.md`, `RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `93a36eb` | `e31e6a7` | Speed up the affix sweep about 8x: prune keypresses by a pass-1 exception-rate floor | `FINDINGS_2026-09-29-affix-exceptions-analysis.md`, `RESUME_2026-09-29-affix-after-lexicon-fix.md`, `RESUME_2026-09-29-affix-partial-overlap-flag.md` |
| `9e2ac38` | `b340fe1` | Rerun the affix pool and H sweep on the re-schwa lexicon; add --settings to the sweep | `RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `a9b85cf` | `27668cf` | Keep the k of -ction in the coda when the word also contains an x | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `afa8fac` | `9f871e7` | Resyllabify the five -ption lemmas that put the p in the last syllable's onset | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `ca153cf` | `5d8a843` | Share the composed-stroke pass and memoize getStrokeCost in the coda key search (perf B) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `d2d4fa0` | `3a84cc5` | Re-converge LexiqueSynthetic.tsv against the adaptive shared-discriminator selection | `scratch/config-extraction-plan-full-detail.md`, `scratch/config-extraction-plan.md` |
| `da7fcee` | `f505adb` | Regenerate LexiqueMixte.tsv from the current committed lexique.py | `scratch/reform1990/RESUME_2026-09-16.md` |
| `df71a24` | `649809f` | Rename phase-lettered files and identifiers to descriptive names | `docs/GLOSSARY.md` |
| `e3b0358` | `d1fceb0` | Fix Verbiste template/lexicon defects flagged by cross-checker | `TODO.md`, `docs/PIPELINE.md`, `util/fixParticipleGenderPhon.py` |
| `e5a7966` | `671902a` | Record the re/ré remeasurement and the ra/Re phonology TODO | `RESUME_2026-09-30-scope-decisions-to-engine.md` |
| `f0f4eed` | `10c640a` | Memoize the render path: keyDisplayName, strokesToRTFCRE, canonicalizeStrokes (perf E) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `f4141e8` | `aa681e2` | Record the implementation outcome in the performance review report | `PERF_ROUND2_HANDOFF.md` |
| `fd7e242` | `3249c05` | Fix collision syllabification exceptions; drop subjonctif imparfait | `docs/PIPELINE.md` |

## `cl_test_coverage`  (tip 1c27b74)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `e3b0358` | `d1fceb0` | Fix Verbiste template/lexicon defects flagged by cross-checker | `todo.md` |

## `docs-refactor`  (tip 851d296)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `0fa69af` | `812eb20` | Add a soft same-key preference to the Phase G CP-SAT search | `docs/PIPELINE.md` |
| `2127790` | `91b1a84` | Resolve absous/dissous/repartie/repartir, closing out the 1990 reform thread | `scratch/reform1990/RESUME_2026-09-16.md` |
| `26be94d` | `629170b` | Exclude azulejo/azulejos, fixing the dictionary.py buildTheory crash | `scratch/reform1990/RESUME_2026-09-16.md` |
| `37fdc4e` | `e060dd2` | Fix verb-paradigm synthetic-generation bugs: split ambiguous Verbiste templates, correct p | `docs/PIPELINE.md` |
| `4e73533` | `fbda37e` | Fix 7 elicitation answers that marked impératif via pers_2 instead of itself | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md` |
| `5ae0118` | `4ed85f0` | Snapshot pending doc edits and session notes before docs refactor | `docs/PIPELINE.md` |
| `688c74d` | `9114fbb` | Fix same-spelling-homograph over-marking (calmez/-kt bug) and elicitation data errors | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md`, `util/build_keypress_groups.py` |
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `7f4de93` | `2a6f2b1` | Add category 3 (loanwords) and interpeller/interpeler to 1990 reform tooling | `scratch/reform1990/RESUME_2026-09-16.md` |
| `8330b8e` | `b3b7fd5` | Persist Phase G's adopted keypress assignment (nbr_p bound to p) | `docs/PIPELINE.md` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `da7fcee` | `f505adb` | Regenerate LexiqueMixte.tsv from the current committed lexique.py | `scratch/reform1990/RESUME_2026-09-16.md` |
| `df71a24` | `649809f` | Rename phase-lettered files and identifiers to descriptive names | `docs/GLOSSARY.md` |
| `fd7e242` | `3249c05` | Fix collision syllabification exceptions; drop subjonctif imparfait | `docs/PIPELINE.md` |

## `performance-optim`  (tip c42c4d3)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `0b5eace` | `a8779e0` | Conjugate -eter/-eler verbs on their attested rectified-è templates | `TODO.md` |
| `0fa69af` | `812eb20` | Add a soft same-key preference to the Phase G CP-SAT search | `docs/PIPELINE.md` |
| `133a766` | `03faa64` | Cache the disambiguated theory in a fingerprinted DisambiguatedTheory.pickle (perf A) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `2127790` | `91b1a84` | Resolve absous/dissous/repartie/repartir, closing out the 1990 reform thread | `scratch/reform1990/RESUME_2026-09-16.md` |
| `26be94d` | `629170b` | Exclude azulejo/azulejos, fixing the dictionary.py buildTheory crash | `scratch/reform1990/RESUME_2026-09-16.md` |
| `37fdc4e` | `e060dd2` | Fix verb-paradigm synthetic-generation bugs: split ambiguous Verbiste templates, correct p | `docs/PIPELINE.md` |
| `39c3ff9` | `6aef21f` | Cut the discriminator feature scan's quadratic parts (perf R2c) | `PERF_REVIEW_2026-09-29_round2.md` |
| `3de3273` | `525414f` | TODO: resyllabify 5 wrong -ption lemmas (absorption, résorption, ...) | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `3e4f655` | `550d451` | Log one util._timing phase line per S2 appender round (perf D, measurement half) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `447fa9c` | `2d93978` | Apply the round-1 multiphoneme fix to the forked phoneme stage too (perf R2d) | `PERF_REVIEW_2026-09-29_round2.md` |
| `4b53c14` | `2fb3488` | Add round-2 profiling handoff notes and round-1 evidence to the branch | `PERF_REVIEW_2026-09-29_round2.md` |
| `4e73533` | `fbda37e` | Fix 7 elicitation answers that marked impératif via pers_2 instead of itself | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md` |
| `5ae0118` | `4ed85f0` | Snapshot pending doc edits and session notes before docs refactor | `docs/PIPELINE.md` |
| `6609e63` | `e479ea9` | Fix round-1 memos: unbounded canonicalizeStrokes cache, getStrokesOfPhoneme memo, C-encode | `PERF_REVIEW_2026-09-29_round2.md` |
| `688c74d` | `9114fbb` | Fix same-spelling-homograph over-marking (calmez/-kt bug) and elicitation data errors | `docs/PIPELINE.md`, `docs/specs/discriminating-features.md`, `util/build_keypress_groups.py` |
| `70bd2e2` | `6a114eb` | Hoist per-syllable invariants out of lexicalSyllabicPartAmbiguityScore (perf C) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `7f4de93` | `2a6f2b1` | Add category 3 (loanwords) and interpeller/interpeler to 1990 reform tooling | `scratch/reform1990/RESUME_2026-09-16.md` |
| `82609f7` | `ff6b465` | Compute the elicitation opposition cross-product once (perf F) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `8330b8e` | `b3b7fd5` | Persist Phase G's adopted keypress assignment (nbr_p bound to p) | `docs/PIPELINE.md` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `8630552` | `30662bc` | Checkpoint: one-key-per-territory patch for affix rule selection (superseded) | `PLAN_2026-09-28-affix-single-generator-rewrite.md`, `RESUME_2026-09-28-affix-territory-merge.md` |
| `88ecc2b` | `d7df8d9` | Carry the word indexes in DisambiguatedTheory.pickle; skip Dictionary.pickle on cache hits | `PERF_REVIEW_2026-09-29_round2.md` |
| `8e811b2` | `c9d3b68` | Keep the k of -ction in the coda when the word also contains an x | `PERF_REVIEW_2026-09-29.md` |
| `a9b85cf` | `27668cf` | Keep the k of -ction in the coda when the word also contains an x | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `afa8fac` | `9f871e7` | Resyllabify the five -ption lemmas that put the p in the last syllable's onset | `RESUME_2026-09-29-affix-after-lexicon-fix.md` |
| `ca153cf` | `5d8a843` | Share the composed-stroke pass and memoize getStrokeCost in the coda key search (perf B) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `da7fcee` | `f505adb` | Regenerate LexiqueMixte.tsv from the current committed lexique.py | `scratch/reform1990/RESUME_2026-09-16.md` |
| `df71a24` | `649809f` | Rename phase-lettered files and identifiers to descriptive names | `docs/GLOSSARY.md` |
| `e3b0358` | `d1fceb0` | Fix Verbiste template/lexicon defects flagged by cross-checker | `TODO.md`, `docs/PIPELINE.md`, `util/fixParticipleGenderPhon.py` |
| `f0f4eed` | `10c640a` | Memoize the render path: keyDisplayName, strokesToRTFCRE, canonicalizeStrokes (perf E) | `PERF_REVIEW_2026-09-29.md`, `PERF_ROUND2_HANDOFF.md` |
| `f4141e8` | `aa681e2` | Record the implementation outcome in the performance review report | `PERF_ROUND2_HANDOFF.md` |
| `fd7e242` | `3249c05` | Fix collision syllabification exceptions; drop subjonctif imparfait | `docs/PIPELINE.md` |

## `phase-g-grouping`  (tip 897b067)

| Cited (old) | New id | Commit subject | Cited in |
|---|---|---|---|
| `023cca1` | `af86d59` | Correct the pers_3-default repair to a minimal, single-atom fix | `RESUME_2026-09-19-phaseG.md` |
| `2127790` | `91b1a84` | Resolve absous/dissous/repartie/repartir, closing out the 1990 reform thread | `RESUME_2026-09-20-starhash-priority.md`, `scratch/reform1990/RESUME_2026-09-16.md` |
| `26be94d` | `629170b` | Exclude azulejo/azulejos, fixing the dictionary.py buildTheory crash | `scratch/reform1990/RESUME_2026-09-16.md` |
| `29da8d2` | `14166f6` | Fix atomicFeatures() tokenizer and gender/number compound feature format | `ATOMIC_KEYPRESS_REWIRE_PLAN.md`, `RESUME_2026-09-18.md` |
| `2b02479` | `0d64c2d` | Add scoping plan for wiring atomic-feature keypress search into a joint solver | `RESUME_2026-09-18.md` |
| `2eab659` | `1cbbc58` | Remove bogus male/males duplicate of mâle/mâles | `todo.md` |
| `31b3a3c` | `6f80f10` | Land Phase P milestone 1: pressability contract, build script, and artifacts | `ATOMIC_KEYPRESS_REWIRE_PLAN.md` |
| `7da7bf3` | `9ac6f78` | Changed Equal sign to At sign in phonology | `util/fixXlfnSingleCorruption.py` |
| `7f4de93` | `2a6f2b1` | Add category 3 (loanwords) and interpeller/interpeler to 1990 reform tooling | `scratch/reform1990/RESUME_2026-09-16.md` |
| `83d9a32` | `2948571` | Fix -gniez/-gnez false homophone in Lexique383/LexiqueInfra/LexiqueMixte | `util/fixGniezInfraPhono.py` |
| `a450d07` | `08c1ab0` | Baseline commit before set-cover discriminator rewiring | `RESUME_2026-09-17.md` |
| `ccd4d4b` | `1c1809f` | Wire adaptive shared-discriminator selection into the live theory generation | `RESUME_2026-09-18.md` |
| `d0c7ffb` | `f252593` | Fix Phase G: greedy coloring needs a verify-and-repair loop, not just pairwise pre-checks | `RESUME_2026-09-19-phaseG.md` |
| `d8671b0` | `295b732` | Fix lexicon gender/number gaps and consolidate casher's paradigm | `RESUME_2026-09-18.md` |
| `da7fcee` | `f505adb` | Regenerate LexiqueMixte.tsv from the current committed lexique.py | `scratch/reform1990/RESUME_2026-09-16.md` |
| `e3b0358` | `d1fceb0` | Fix Verbiste template/lexicon defects flagged by cross-checker | `todo.md` |
| `f4d735b` | `8835143` | Implement Phase E5 (validate) and correct its group-scoping bug | `RESUME_2026-09-19-phaseG.md` |
| `fe00a1f` | `7a82538` | Change -E phonemes to -e in all verbs ending in -ai in both lexics | `RESUME_2026-09-19.md` |

## `cpsatsolver`

No commit id cited in its docs or comments.
