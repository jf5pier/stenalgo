# Dead-Code Removal (Pass 5) — discovery

Method: static reachability from the real entry points, read-only. Entry points used:
`lexique.py` (module-level), `dictionary.py` `__main__`, `python -m src.elicitation`,
every `util/build_*.py`, `util/export_*.py`, `util/check_*.py`, and `plover_stenalgo/`
(the Plover plugin package). Reachability was checked by grep (`grep -rn <name>
--include=*.py .`, excluding `src/test/`) for every candidate symbol, by reading the
callers found, and by re-reading `dictionary.py`'s `__main__` and each module's own
`__main__` block directly. `docs/refactor/callgraph/90-findings.md` §"Dead-code
observations" (items 1-26, produced by the Pass-1 stage agents) was the starting
inventory; every item below was re-verified against the current tree on
branch `docs-refactor` rather than copied blind. Two false-positive traps from the task
were checked explicitly and are called out inline: pickle-only reachability (trap 1) and
the deliberately-kept Keyboard Layout Optimization (S4) code (trap 2).

No code was changed. `pytest -q --collect-only` was not run; test counts below are from
`grep -c "def test_"` over the relevant line ranges and should be treated as approximate
("~").

---

## KEPT DELIBERATELY

Per user decision b5 (`docs/refactor/callgraph/91-review-questions.md`): Keyboard Layout
Optimization (S4) is a real, rare, costly stage whose solver call is commented out, not
dead code.

- `src/cpsatsolver.py` `optimizeKeyboard` and its helpers — imported at dictionary.py:32,
  called only from the commented-out line dictionary.py:496. Do not remove.
- `Syllable.optimizeBiphonemeOrder` (src/grammar.py:644), `Dictionary.analyseAmbiguities`
  (dictionary.py:183, including `analysePhonemSyllabicAmbiguity`,
  `analysePhonemeLexicalAmbiguity`, `analyseMultiphonemeLexicalAmbiguity_serial` and
  `lexicalPhonemeAmbiguityScore` in src/grammar.py) — run on every fresh rebuild
  (dictionary.py:464-466) to produce the layout statistics that feed the commented-out
  solver call and `generateBaseKeymap`. Kept.
- `Dictionary.generateBaseKeymap` (dictionary.py:212) / `getLowAmbiguityPhonemes` (:296) —
  the fallback keymap, reachable when `starboard3h.json` is missing (dictionary.py:493-494).
  Kept.
- The commented-out solver call itself, dictionary.py:496
  (`#optimizeKeyboard(starboard, dictionary.syllabicPartAmbiguity, ["onset", "nucleus", "coda"])`)
  and the `#from src.cpsatoptimizer import optimizeTheory` import at dictionary.py:47 —
  keep as the documented resume point for regenerating `starboard3h.json`.

Correction to 90-findings.md item 6: `Syllable.phonoWords` (src/grammar.py:481) is **not**
dead. It is read by `lexicalPhonemeAmbiguityScore` (src/grammar.py:906-917), which is
called from both the dead `analysePhonemeLexicalAmbiguity_serial` (:1071, unused twin) and
the live `analysePhonemeLexicalAmbiguity` (:1098, called from `analyseAmbiguities` above,
kept deliberately). `phonoWords` should stay tagged KEPT DELIBERATELY, not "dead / only
serves dead scorers".

---

## DEAD

Unreachable from any entry point and from `src/test/`.

### D1. Legacy CP-SAT / SAT discriminator solvers
- `src/satoptimizer.py` (348 lines, incl. `satOptimizeDiscriminator` :282) — imported only
  by `src/test/satoptimizer_test.py`. No non-test import anywhere (`grep -rn satoptimizer
  --include=*.py .` outside `src/test/` returns only a comment in dictionary.py:529 and a
  doc comment in util/export_keyboard_layout.py:30).
- `src/cpsatoptimizer.py` (211 lines, `optimizeTheory`) — imported nowhere except the
  commented-out `#from src.cpsatoptimizer import optimizeTheory` at dictionary.py:47. No
  test file imports it (`src/test/` has no `cpsatoptimizer_test.py`), so this half has no
  test coverage to remove either.
- Risk: low (both are self-contained modules with no other module depending on their
  internals; `satoptimizer_test.py` would go with `satoptimizer.py`).
- Proposed group: **"legacy SAT/CP-SAT discriminator solvers"**.

### D2. Legacy greedy discriminator-keypress assignment
- `src/greedyoptimizer.py` `FEATURE_PRIORITY` (:16), `assignDiscriminatorKeypresses` (:196),
  `_buildStrokePool` (:180) — `FEATURE_PRIORITY` is imported by
  `src/ambiguitychecker.py:39` but used only inside `_selectCanonicalIndex` (:564-572),
  which is reached only from `ambiguitychecker.py`'s own `__main__` diagnostic (see D-MAIN
  below) — so at the entry-point level `FEATURE_PRIORITY` is unreachable. Trap 3 checked:
  `GRAMCAT_PRIORITY` (greedyoptimizer.py:62) **is** live (category-priority rule R6,
  imported and used at ambiguitychecker.py:231-232 inside `decideStarHashMark`, which is
  wired into `Dictionary.buildFinalTheory`) — keep it, do not touch this file's
  `GRAMCAT_PRIORITY` definition.
- `assignDiscriminatorKeypresses`/`_buildStrokePool` have no caller outside
  `src/test/greedyoptimizer_test.py` (verified: `grep -rn assignDiscriminatorKeypresses
  --include=*.py .` outside tests returns nothing but a doc-comment mention in
  src/ambiguitychecker.py:565).
- Tests removed: `src/test/greedyoptimizer_test.py`, all ~16 `def test_` functions (every
  one imports `assignDiscriminatorKeypresses`/`_buildStrokePool`; none exercises
  `GRAMCAT_PRIORITY`).
- Risk: low. The file keeps `GRAMCAT_PRIORITY` live; only `FEATURE_PRIORITY`,
  `assignDiscriminatorKeypresses`, `_buildStrokePool` and their test file would be removed.
- Proposed group: **"legacy greedy discriminator assignment"** (pairs naturally with D-MAIN
  item covering `_selectCanonicalIndex`, since that's `FEATURE_PRIORITY`'s only other
  reader).

### D3. Unused scorer twins (Phonetic Theory Building statistics)
- `src/grammar.py` `analysePhonemSyllabicAmbiguity_serial` (:1007) and
  `analysePhonemeLexicalAmbiguity_serial` (:1071) — unused; `analyseAmbiguities`
  (dictionary.py:188-191) calls the non-serial siblings `analysePhonemSyllabicAmbiguity`
  (:1032) and `analysePhonemeLexicalAmbiguity` (:1098) instead.
- `src/grammar.py` `analyseMultiphonemeLexicalAmbiguity` (:1171, non-serial) — unused;
  `analyseAmbiguities` (dictionary.py:196-197) calls the `_serial` sibling
  `analyseMultiphonemeLexicalAmbiguity_serial` (:1138) instead, which is KEPT DELIBERATELY
  (see above). So of this third pair the `_serial` one is live and the plain one is dead —
  opposite polarity from the first two pairs. Confirm no test imports the plain
  `analyseMultiphonemeLexicalAmbiguity` before removing (grep only found the definition;
  did not check every test file line-by-line for this one — **unsure**, worth a final grep
  before deleting).
- Risk: low-medium (getting the "serial vs. non-serial, which is live" polarity backwards
  for the wrong pair would delete a live function — verify each grep individually at
  removal time).
- Proposed group: **"unused ambiguity-scorer twins"**.

### D4. Lexique print/consensus helpers
- `lexique.py` `Lexique.printTopWordsFilm` (:1087), `printTopWordsBooks` (:1092) — no
  caller anywhere (`grep -rn printTopWordsFilm\|printTopWordsBooks --include=*.py .`
  returns only the definitions).
- `lexique.py` `Word.isSyllConsensus` (:933), `isOrthoSyllConsensus` (:943) — same, no
  caller anywhere including tests.
- `lexique.py:775` no-op expression `_ = syllNb == len(cv_syll) - 1` — a statement whose
  value is discarded and reused nowhere; dead in the sense of doing nothing (not a
  function to remove, but a line with no effect).
- Risk: low.
- Proposed group: **"unused lexique.py print/consensus helpers"**.

### D5. Keyboard demo code
- `src/keyboard.py` `Starboard.setIrelandEnglishLayout` (:718) — called from the module's
  own `__main__` (:755) **and** directly from `src/test/keyboard_test.py:21` (plus two
  comments at :509/:513 describing its effect). Because a test imports and calls it
  directly, this is TEST-ONLY rather than fully dead — see T1 below. Re-classified out of
  DEAD.
- `src/keyboard.py` `__main__` block (:742-...) itself, which loads the missing
  `starboard1h.json` (:759) — this would always fail today since that file does not exist
  in the repo (only `starboard3h.json` is tracked). Dead diagnostic entry point, not a
  reusable function; folding into COMMENTED-OUT/DIAGNOSTIC-MAIN-ONLY bucket below instead
  of DEAD since nothing needs to be deleted from importable code, only the `__main__`
  block.
- Risk: low.
- Proposed group: folds into **"keyboard.py demo `__main__`"** (see DIAGNOSTIC-MAIN-ONLY).

### D6. Unused `Dictionary` fields
- `dictionary.py` `stemmOfLemme` (:61, dict declared, assigned `{}` at :80, never
  populated past the empty init, never read) — verified no assignment beyond `{}` and no
  read anywhere (`grep -n stemmOfLemme dictionary.py` shows only the declaration and the
  `{}` init).
- `syllableClass` (dictionary.py:82, `self.syllableClass: type = Syllable`) — assigned,
  never read elsewhere.
- `Dictionary.printVerbose` (dictionary.py:51-ish) — a no-op method (per 90-findings item
  5; verified the method body is empty/pass-only by re-reading dictionary.py around that
  line during this pass — **treat as DEAD** but low priority since removing a no-op is
  cosmetic).
- `wordsByLemme`, `totalFrequencies`, `frequentWordsFrequencies` are **not** dead by a
  plain "no reader" test — `wordsByLemme` is populated (dictionary.py:158-160) but this
  pass did not find a *reader*; not removing without a caller-side grep across the whole
  tree with more time. Marking these three **unsure** rather than DEAD; flag for the
  removal PR to re-grep with `git grep -n '\.wordsByLemme\b\|\.totalFrequencies\b\|\.frequentWordsFrequencies\b'`.
- Risk: low for `stemmOfLemme`/`syllableClass`/`printVerbose`; unsure for the other three.
- Proposed group: **"unused Dictionary bookkeeping fields"** (ship `stemmOfLemme`,
  `syllableClass`, `printVerbose` only; leave the unsure three for a follow-up grep).

---

## TEST-ONLY

Referenced only from `src/test/`.

### T1. `Starboard.setIrelandEnglishLayout`
- src/keyboard.py:718 — called by `src/test/keyboard_test.py:21` and the module's own
  `__main__`. No pipeline entry point uses it (it is a demo layout, not `starboard3h.json`
  or any live keymap builder).
- Tests: `src/test/keyboard_test.py` — at least the test using it at line 21, plus the two
  comment-referencing assertions around :509/:513 (same test, not separate tests) — ~1
  test directly exercises it; do not remove the whole file, only this method and its one
  caller line, unless the removal PR decides to drop the whole demo-layout test too.
- Risk: low.
- Proposed group: **"keyboard.py demo layout"**.

### T2. Legacy SAT discriminator (test half)
- `src/satoptimizer.py` — see D1. Tests removed with it: `src/test/satoptimizer_test.py`,
  ~22 `def test_` functions.
- Proposed group: same as D1 ("legacy SAT/CP-SAT discriminator solvers").

### T3. Legacy greedy discriminator assignment (test half)
- `src/greedyoptimizer.py` `assignDiscriminatorKeypresses`/`_buildStrokePool` — see D2.
  Tests removed: `src/test/greedyoptimizer_test.py`, ~16 `def test_` functions (whole
  file — it has no test that only touches `GRAMCAT_PRIORITY`).
- Proposed group: same as D2 ("legacy greedy discriminator assignment").

### T4. Greedy Discriminating-Feature Grouping path
- `src/featuregrouping.py` `runFeatureGrouping` (:247), `greedyColorMarkers` (:117,
  also set-order dependent per the existing finding), `coOccurrencePairs` (:75),
  `wouldCollideIfMergedPairs` (:89), `_findSharedKeypressPair` (:222),
  `FeatureGroupingResult` (:214), and the module's own `__main__` (:294) — verified: the
  live Grouping Phase (`util/build_keypress_groups.py:37-39`) imports only
  `frequencyWeightedChordSizes, liveMarkers, loadGroupOrthoFrequencies, ...` from
  `featuregrouping` and `ExclusiveGroupPreference, SameKeyPreference,
  minKeypressesSatWithPriorities, ...` from `featuregroupingsat`; `src/featuregroupingsat.py`
  itself imports only `FrequencyByGroup, PressSetsByGroup, frequencyWeightedChordSizes,
  liveMarkers` (:30) and, inside its own `__main__`, `loadResolvedPressSets` (:575) — never
  `runFeatureGrouping` or `greedyColorMarkers`.
- Tests: `src/test/featuregrouping_test.py`, ~25 `def test_` functions — need a finer pass
  to say how many test only the dead greedy path vs. the still-used loaders
  (`liveMarkers`, `verifyKeypressAssignment`, `inducedPressSet`,
  `frequencyWeightedChordSizes`); **unsure** of the exact split without reading all 25
  tests, treat "~25, some subset" and let the removal PR re-triage per-test.
- Risk: medium (this is the largest single test file in the set, and it's the one place
  the "ground truth" verifier `verifyKeypressAssignment` used by `featuregroupingsat` is
  itself tested — do not delete `verifyKeypressAssignment`'s own tests).
- Proposed group: **"greedy feature grouping"**.

### T5. `minKeypressesSatPreferring` / "preferring" path
- `src/featuregroupingsat.py` `minKeypressesSatPreferring` (:455), `_bestAssignmentPreferring`
  (:232), and the non-empty branch of `_feasibleAssignment`'s `mustShareKey` handling —
  verified `util/build_keypress_groups.py:80` always calls the live entry point
  (`minKeypressesSatWithPriorities`) with `mustShareKey=frozenset()`, i.e. empty in
  production; the non-empty-`mustShareKey` code path and `minKeypressesSatPreferring`
  itself are exercised only by `src/featuregroupingsat.py`'s own `__main__` (:570-603) and
  tests. Note: the `mustShareKey` **parameter** is still live (passed, just always empty);
  only the code that handles a non-empty value is untested-in-production. Do not remove
  the parameter/plumbing, only `minKeypressesSatPreferring`/`_bestAssignmentPreferring` if
  the removal PR decides the "preferring" (soft-preference) API is retired in favor of
  `minKeypressesSatWithPriorities`.
- Tests: `src/test/featuregroupingsat_test.py`, ~7 tests directly named
  `*Preferring*`/`mustDifferGroups`/`aloneKeys` in the "preferring" section (lines ~209-313;
  counted by range, not by full manual read) out of ~26 total in the file — the other ~19
  test `minKeypressesSat`/`minKeypressesSatWithPriorities`/`serializeAssignment`, which are
  live and must stay.
- Risk: medium — `minKeypressesSatWithPriorities` (live) is documented as mirroring
  `minKeypressesSatPreferring`'s logic with an extra lexicographic-tiers layer
  (featuregroupingsat.py comments at :245, :431); read both functions carefully before
  deleting one, in case `minKeypressesSatWithPriorities` still calls into
  `_bestAssignmentPreferring` internally (this pass did not fully trace that; **unsure**,
  flag for the removal PR to grep `_bestAssignmentPreferring` callers one more time inside
  `featuregroupingsat.py` itself, not just from the outside).
- Proposed group: **"featuregroupingsat preferring API"** (keep separate from T4's greedy
  path — different module, different risk profile).

---

## DIAGNOSTIC-MAIN-ONLY

Reached only from a module's own `__main__` diagnostic block.

### M1. "Phase 0 ambiguity report" diagnostic (src/ambiguitychecker.py `__main__` ~:1394-1420, reads its own header at :1326 for setup)
Reached only from this block:
- `_selectCanonicalIndex` (:564), which is `FEATURE_PRIORITY`'s only reader (see D2) —
  called at :589 from inside the diagnostic's own helper `buildAtomicFeatureToWords` path.
- `buildAtomicFeatureToWords` (:575)
- `findFeatureKeypresses` (:630)
- `checkComposedChords` (:676)
- `_appendCodaAddition` (:600), `_isFeasibleAddition` (:608) — used by
  `findFeatureKeypresses`/`checkComposedChords` above and by `findCollidingNewAdditions`
  (:759, test-only, see below)
- `classifyTheory`, `classifyStrokeCluster`, `detectCrossCategoryClash` (per
  90-findings item 16; not individually re-verified line-by-line this pass, inherited from
  the Pass-1 stage agent's reading — **treat as probably correct, not independently
  re-checked**)
- `buildDiscriminatorSelection` import from `src/featureextractor.py` (ambiguitychecker.py:38,
  called at :1403) — this is the diagnostic's *only* non-test caller of
  `buildDiscriminatorSelection`; the function's other, live caller is
  `util/completeVerbParadigms.py` (S2-gating, see S1 below) so `buildDiscriminatorSelection`
  itself stays; only its use *inside this diagnostic* is diagnostic-only.
- Also writes `ambiguity_report.tsv` and `feature_keypress_feasibility.tsv` — both
  gitignored/scratch-style outputs read by nothing in the pipeline.

Tests: `src/test/ambiguitychecker_test.py` directly imports and unit-tests
`buildAtomicFeatureToWords`, `findFeatureKeypresses`, `checkComposedChords`,
`findCollidingNewAdditions` (import list at :30-41; test classes
`TestBuildAtomicFeatureToWords`, `TestFindFeatureKeypresses`, `TestCheckComposedChords`,
`TestFindCollidingNewAdditions`, lines ~480-651) — ~12 `def test_` functions in that
range. These are true unit tests of otherwise-diagnostic-only code, not incidental
coverage; removing the diagnostic functions removes these ~12 tests too.

Risk: medium. This is the single largest coherent removal candidate (a whole `__main__`
block plus ~7 helper functions plus ~12 tests) and it is explicitly named in
GLOSSARY.md ("Phase 0" legacy-name mapping) and CLAUDE.md's history, so removal should be
its own commit with a clear message, not folded into an unrelated group.

Proposed group: **"Phase 0 ambiguity-report diagnostic"**.

### M2. `dictionary.py` `__main__` commented-out lines
Not code to delete as functions, but literal commented lines inside the entry point's own
`__main__` (dictionary.py:450 onward) that are candidates for cleanup once the removal PR
looks at this file:
- `dictionary.py:47` — `#from src.cpsatoptimizer import optimizeTheory` — KEEP (part of
  the documented S4 resume point, see KEPT DELIBERATELY).
- `dictionary.py:475` — `#        pickle.dump(dictionary.syllableCollection, open("Syllables.pickle", "wb"))`
- `dictionary.py:477` — `#    print(dictionary.words[0])`
- `dictionary.py:478` — `#    sys.exit(1)`
- `dictionary.py:480` — `#dictionary.printSyllabificationStats()`
- `dictionary.py:483` — `#dictionary.writeConstrainFiles()`
- `dictionary.py:485` — `#pprint.pprint(dictionary.wordsByOrtho["effraye"])`
- `dictionary.py:486-488` — commented `for syllableStrokes, words in theory.items(): ...`
  debug-print loop
- `dictionary.py:496` — `#optimizeKeyboard(...)` — KEEP (documented S4 resume point).
- `dictionary.py:498` — `#starboard.toJSONFile('starboard.json')`
- `dictionary.py:507-517` (approx, the `# lemmeOrthoWords: ...` / `# infoVerbs = []`
  blocks) — ad hoc debug scratch code with a trailing `# sys.exit(1)`.
- Risk: low (they are already inert comments; removing them is pure cleanup, not a
  behavior change). Keep the two S4-related ones (:47, :496) per KEPT DELIBERATELY.
- Proposed group: **"dictionary.py __main__ comment cleanup"** — a trivial, separate,
  low-risk commit; do not mix with the KEPT DELIBERATELY lines.

### M3. `src/keyboard.py` `__main__` demo block
- keyboard.py:742 onward, loads `starboard1h.json` (:759) which does not exist in the
  tracked tree (`find . -name starboard1h.json` — not found; only `starboard3h.json` is
  tracked). Running this block today would raise/print a "could not load" style error
  (mirroring the pattern in dictionary.py's `__main__`). Not a function to delete, but a
  candidate `__main__` block to trim once `setIrelandEnglishLayout` usage in T1 is
  resolved.
- Proposed group: **"keyboard.py demo layout"** (same group as T1).

---

## S2-GATING-ONLY

Live, but reached only through Synthetic Lexicon Building (S2)'s verb-paradigm gating —
not dead, tag only.

- `src/featureextractor.py` `extractDiscriminatingFeatures` (:31),
  `buildDiscriminatorSelection` (:284) — imported by `util/completeVerbParadigms.py:40`
  (`confirmCandidates`, `detectUndersampledLemmas`, `newlyCollidingLemmas` per
  `src/verbparadigm.py`) and by `src/ambiguitychecker.py:38` for the diagnostic-only use
  covered in M1. `completeVerbParadigms.py` is not itself one of the required entry
  points (`build_*`/`export_*`/`check_*`), but it is the Synthetic Lexicon Building (S2)
  script referenced by CLAUDE.md's pipeline as the thing that gates verb paradigm
  completion — kept live via that gating relationship, not dead.
- Do not remove without first deciding whether Synthetic Lexicon Building (S2)'s verb
  completion keeps depending on it (CLAUDE.md already flags this dependency explicitly).

---

## ONE-SHOT SCRIPT

Already-run data-fix/validation scripts under `util/`; not deeply analyzed (per task
instructions), just inventoried. None of these are in the required entry-point list
(`build_*`/`export_*`/`check_*`); they are S1/S2 one-off patches, kept for history/
reproducibility of past fixes, not something to delete as "dead code" without an explicit
decision to prune old fix scripts.

| Script | Purpose (from name/docstring) |
|---|---|
| `util/fixAbregerFutureAccent.py` | one-off lexicon accent fix |
| `util/fixAdvenirRenaitreGaps.py` | one-off paradigm gap fix |
| `util/fixAsseoirDualFormGaps.py` | one-off dual-form fix |
| `util/fixAsseoirDualFormGapsManual.py` | manual follow-up to the above |
| `util/fixAyGraphemeEjQuality.py` | one-off grapheme quality fix |
| `util/fixAyGraphemeInfraPhono.py` | one-off LexiqueInfra phono fix |
| `util/fixCeSchwa.py` | one-off schwa fix |
| `util/fixCroitreMouvoirAccents.py` | one-off accent fix |
| `util/fixDeleteWeatherVerbErrors.py` | one-off row deletion |
| `util/fixDuplicateInfTag.py` | one-off tag dedup |
| `util/fixEstOuverteVoyelle.py` | one-off vowel fix |
| `util/fixEvaserWordFinalZSyllabification.py` | one-off syllabification fix |
| `util/fixFoutreDefectiveTenses.py` | one-off verb tense fix |
| `util/fixGniezInfraPhono.py` | one-off phono fix |
| `util/fixGniezPronunciation.py` | one-off pronunciation fix |
| `util/fixGrelerFigurativePlural.py` | one-off plural fix |
| `util/fixInfPlusOtherTag.py` | one-off tag fix |
| `util/fixLeguerEquerHarcelerAccent.py` | one-off accent fix |
| `util/fixMarinDateCorruption.py` | one-off data-corruption fix |
| `util/fixMatirVerbTemplate.py` | one-off verb-template fix |
| `util/fixMultiTagPartialMismatch.py` | one-off tag-mismatch fix |
| `util/fixOuirConditionnelOrder.py` | one-off ordering fix |
| `util/fixParticipeAdjNomVowelQuality.py` | one-off vowel-quality fix |
| `util/fixParticipeMissingNombre.py` | one-off missing-field fix |
| `util/fixParticipePlusOtherTag.py` | one-off tag fix |
| `util/fixPayerAyGrapheme.py` | one-off grapheme fix |
| `util/fixPayerDualFormGaps.py` | one-off dual-form fix |
| `util/fixPayerNonfuturVowelQuality.py` | one-off vowel-quality fix |
| `util/fixResidualConjugationTemplates.py` | one-off template fix |
| `util/fixResidualRowErrors.py` | one-off row-error fix |
| `util/fixSourdreDefectiveGaps.py` | one-off gap fix |
| `util/fixSpuriousDuplicateVerbRows.py` | one-off dedup |
| `util/fixXlfnSingleCorruption.py` | one-off data-corruption fix |
| `util/validateConjugationEndingTable.py` | one-off validation |
| `util/validateLexiconAgainstNomAdjParadigms.py` | one-off validation |
| `util/validateLexiconAgainstVerbiste.py` | one-off validation |
| `util/inventoryAsseoirFormsCoverage.py` | one-off coverage report |
| `util/inventoryPayerFormsCoverage.py` | one-off coverage report |
| `util/copyLineFromTo.py` | generic one-off row-copy helper |
| `util/crossCheckNomAdjWithMorphalou.py` | one-off cross-check against Morphalou |
| `util/splitAnglicismErVerbisteTemplate.py` | one-off Verbiste template split |
| `util/splitEtudierVerbisteTemplate.py` | one-off Verbiste template split |
| `util/build_pers3_default_answers.py` | one-off (2026-09-19) rewrite of `elicitation_answers.json` from the pers_1-default answer set to the pers_3-default one now used as PRIMARY; **hazardous to rerun** — would undo hand-fixes made after it ran (per its own docstring and 90-findings item 21) |

Not proposed for a removal PR unless the user separately decides to prune historical fix
scripts; listed here only so the discovery pass is complete.

---

## COMMENTED-OUT BLOCK

- `dictionary.py:475-517` (approx; see M2 for the itemized list) — assorted debug prints
  and one abandoned `lemmeOrthoWords`/`infoVerbs` scratch analysis, inert.
- `dictionary.py:47` — `#from src.cpsatoptimizer import optimizeTheory` — **KEEP** (S4
  resume point).
- `dictionary.py:496` — `#optimizeKeyboard(...)` — **KEEP** (S4 resume point).
- `dictionary.py:498` — `#starboard.toJSONFile('starboard.json')` — cleanup candidate,
  low risk, but arguably part of the same "how do I regenerate the layout" note as :496;
  suggest keeping it alongside :496 rather than deleting alone, since it's the write-back
  half of the same never-run step.

---

## Incidental observations (not fixed)

- `src/grammar.py` has three "serial vs non-serial" pairs
  (`analysePhonemSyllabicAmbiguity[_serial]`, `analysePhonemeLexicalAmbiguity[_serial]`,
  `analyseMultiphonemeLexicalAmbiguity[_serial]`) where the live one is the non-serial
  form for the first two pairs but the `_serial` form for the third. That inconsistency
  (which suffix means "live") is exactly the kind of thing that makes D3 above easy to
  get backwards; worth a comment in the code itself once someone touches this area, even
  though this pass leaves it as-is per instructions not to fix.
- `Dictionary.printVerbose` (dictionary.py, near :51) appears to be a no-op wrapper; if
  true, it's a strange thing to have shipped silently — but this pass did not confirm
  whether some other code path monkeypatches or checks its existence (unsure).
- The 90-findings.md item 6 claim about `Syllable.phonoWords` being dead is incorrect (see
  "Correction" under KEPT DELIBERATELY) — worth fixing that doc line during Interactive
  Triage / the eventual doc pass, since it could otherwise send a future removal PR after
  a live field.

---

## Proposed removal groups

| Group | Items | Tests removed (approx) | Risk |
|---|---|---|---|
| legacy SAT/CP-SAT discriminator solvers | `src/satoptimizer.py` (whole file), `src/cpsatoptimizer.py` (whole file) | ~22 (`satoptimizer_test.py`); 0 for cpsatoptimizer (no test file) | low |
| legacy greedy discriminator assignment | `greedyoptimizer.py`: `FEATURE_PRIORITY`, `assignDiscriminatorKeypresses`, `_buildStrokePool`; `ambiguitychecker.py`: `_selectCanonicalIndex`'s use of `FEATURE_PRIORITY` (function itself may fold into the Phase 0 group instead, see below) | ~16 (`greedyoptimizer_test.py`, whole file) | low |
| Phase 0 ambiguity-report diagnostic | `ambiguitychecker.py` `__main__`, `_selectCanonicalIndex`, `buildAtomicFeatureToWords`, `findFeatureKeypresses`, `checkComposedChords`, `_appendCodaAddition`, `_isFeasibleAddition`, `findCollidingNewAdditions`, `classifyTheory`, `classifyStrokeCluster`, `detectCrossCategoryClash` | ~12+ (`ambiguitychecker_test.py`, the four `Test*` classes at ~480-651; `findCollidingNewAdditions` tests overlap this range) | medium |
| unused ambiguity-scorer twins | `grammar.py`: `analysePhonemSyllabicAmbiguity_serial`, `analysePhonemeLexicalAmbiguity_serial`, `analyseMultiphonemeLexicalAmbiguity` (non-serial) | 0 found, but re-grep before deleting (unsure) | low-medium |
| unused lexique.py print/consensus helpers | `lexique.py`: `printTopWordsFilm`, `printTopWordsBooks`, `Word.isSyllConsensus`, `Word.isOrthoSyllConsensus`, the no-op at :775 | 0 | low |
| unused Dictionary bookkeeping fields | `dictionary.py`: `stemmOfLemme`, `syllableClass`, `printVerbose` | 0 | low |
| keyboard.py demo layout | `Starboard.setIrelandEnglishLayout`, keyboard.py `__main__` block | ~1 (`keyboard_test.py`, the one test at line ~21) | low |
| greedy feature grouping | `src/featuregrouping.py`: `runFeatureGrouping`, `greedyColorMarkers`, `coOccurrencePairs`, `wouldCollideIfMergedPairs`, `_findSharedKeypressPair`, `FeatureGroupingResult`, its `__main__` | ~25, but split needed (unsure exact count of dead-vs-live-covering tests) | medium |
| featuregroupingsat preferring API | `src/featuregroupingsat.py`: `minKeypressesSatPreferring`, `_bestAssignmentPreferring`, non-empty-`mustShareKey` branch of `_feasibleAssignment` | ~7 of ~26 in `featuregroupingsat_test.py` | medium (verify `minKeypressesSatWithPriorities` doesn't internally call `_bestAssignmentPreferring` first) |
| dictionary.py `__main__` comment cleanup | dictionary.py:475, 477, 478, 480, 483, 485-488, 498 (inert comments; keep :47 and :496) | 0 | low |

Items left out of the table on purpose (not proposed for removal): everything under KEPT
DELIBERATELY, S2-GATING-ONLY (`featureextractor.py`'s two functions), and the ONE-SHOT
SCRIPT table (needs a separate user decision about pruning historical fix scripts, not a
dead-code call).

---

## Main-thread spot-check (2026-09-23) — overrides the sections above

- **`detectCrossCategoryClash` is LIVE** — called by `util/build_realization_report.py:95` and
  `_isInScopeCollision` (ambiguitychecker.py:993). Removed from the Phase 0 group; its tests stay.
- `classifyTheory` (only caller: ambiguitychecker `__main__` :1373) and `classifyStrokeCluster`
  (callers: `classifyTheory` + 5 tests, ambiguitychecker_test.py ~:60–120) — confirmed diagnostic-only.
- Phase 0 helpers confirmed diagnostic/test-only: `buildAtomicFeatureToWords` (the :819 hit is a
  docstring), `findFeatureKeypresses`, `checkComposedChords`, `findCollidingNewAdditions`,
  `_isFeasibleAddition`, `_appendCodaAddition` (callers only inside that set), `_selectCanonicalIndex`.
  Tests: 12 (ambiguitychecker_test.py :480–652) + 5 (`classifyStrokeCluster`) = 17.
- **`setIrelandEnglishLayout` is the `starboard_with_layout` fixture** (keyboard_test.py:17–22),
  used ~46 times — not "~1 test". Recommend KEEP (test support); only keyboard.py's broken
  `__main__` (loads missing `starboard1h.json`) is a removal candidate.
- Grammar twins: polarity confirmed (dead = `analysePhonemSyllabicAmbiguity_serial`,
  `analysePhonemeLexicalAmbiguity_serial`, `analyseMultiphonemeLexicalAmbiguity` plain); no test refs.
- Preferring API: `minKeypressesSatWithPriorities` uses `_bestAssignmentWithPriorities`, **not**
  `_bestAssignmentPreferring` — safe to remove both Preferring functions (+ the `__main__` use at :600).
  Tests: 4 `test_minKeypressesSatPreferring_*` removed; :316 (WithPriorities vs Preferring) removed
  or rewritten; `aloneKeys`/`mustDifferGroups` tests (:269–296) stay. Do NOT touch the `mustShareKey` branch.
- `Dictionary.wordsByLemme`, `totalFrequencies`, `frequentWordsFrequencies`: written, never read
  (git grep, all `.py`) → DEAD, not unsure. `printVerbose` is a module-level function in
  dictionary.py (lexique.py has its own, live), no caller.
- `featuregrouping.py` greedy path: no non-test caller (elicitation.py's `coOccurrencePairs` is a
  local field; featuregroupingsat hits are docstrings). 25 tests in the file; per-test split at removal.
- Exact counts: satoptimizer_test.py 22, greedyoptimizer_test.py 16. pytest baseline 593.
