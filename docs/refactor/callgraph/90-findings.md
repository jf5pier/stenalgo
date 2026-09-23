# Consolidated findings (Pipeline Call Graph and Glossary (Pass 1), merge step)

Merged and de-duplicated from `01-lexicon-building.md`, `02-phonetic-theory-building.md`,
`03-same-lemma-disambiguation.md`, `04-marking-and-export.md` and the observations of
`00-skeleton.md`, plus read-only re-measurements made during the merge (pickles rebuilt
2026-09-22 20:31 with `PYTHONHASHSEED=0`). Nothing here has been fixed.

Sections: **Suspected bugs** (to `todo.md § Suspected bugs`), **Dead-code observations**
(raw material for Dead-Code Removal (Pass 5)), **Doc drift** (raw material for Interactive
Triage (Pass 4)).

---

## Suspected bugs

Ordered by severity: tier 1 changes the Plover dictionary (or other exported output) today;
tier 2 changes reports or tracked artifacts other than the Plover output; tier 3 is latent
(a hazard with no measured current impact).

### Tier 1 — affects the Plover output today

**B1. Spelling twins: only the first Word of a spelling is marked.**
- Where: src/ambiguitychecker.py:797-800 (`_resolveEntryWord`), used by
  `buildKeypressGroupToWords` :803 and `buildKeypressGroupExtraAlternates` :844.
- Defect: when several Words share (ortho, `lemmeGramCat`) and the entry's canonical strokes,
  `next(...)` returns the first; the others keep bare base strokes.
- Scenario: "agis" has a participle m:p Word and a finite Word; its primary press is
  {impératif}; only one gets the `-k` feature discriminating stroke, the other stays on `a/vti`, the stroke of
  the canonical member "agi".
- Impact (reconciled, see note): 262 twin spellings in the current resolved discriminating feature sets; **230
  same-lemmeGramCat collision pairs in the final induced strokes, all involving a twin**. Of
  these, 131 pairs sit in strokes that also hold another `lemmeGramCat`, so Different-Lemma or Grammatical-Category Disambiguation (S7) ranks them and marks the rarer one (e.g. `kpi/mR*i` → "finis"). The other **99
  pairs in 98 strokes** have a single `lemmeGramCat` and are dropped by Lemma-homophone group detection (S7.5); they reach theory 2 unmarked and the Plover export keeps the more frequent
  Word. All 98 losing spellings are still reachable through another Word's stroke today.
  Invisible to the "0 residual same-lemmeGramCat collisions" invariant (the unchosen twin is
  not in `allWords`).
- Reconciliation of 229 vs 98: both stage files were right and measured different things.
  `03-same-lemma-disambiguation.md` counted all same-lemmeGramCat, different-ortho pairs on
  canonical final induced strokes over the whole lexicon (**before** Different-Lemma or Grammatical-Category Disambiguation (S7)): 229 on the pickles of about 20:13, 230 on the 20:31 rebuild. `04-marking-and-export.md`
  counted canonical-stroke buckets with ≥2 spellings but a single `lemmeGramCat` (the ones the filter of
  Lemma-homophone group detection (S7.5) at :402 drops), i.e. what survives **after** marking: 98 buckets = 99 pairs. 230 − 131
  resolved by marking = 99. The 230/262 vs 03's 229/230 drift comes from the rebuild.
- Confidence: high. Reported by: 03 (twins, 229/230), 04 (98 buckets), skeleton (fallback, see B20).

**B2. Synthetic verb forms get a vowel-less trailing syllable.**
- Where: src/verbparadigm.py:561, :611 (radical cut by character count on the raw `|`/`_`
  breakdown string).
- Defect: the infinitive's syllable boundary before the stem-final consonant survives into
  word-final forms, producing an onset-only last stroke.
- Scenario: synthetic `cannes` (canner, sub:pre:2s) `k_a|n_#` → theory 1 `((2,12),(6,8))`, 2
  strokes, while NOM `cannes` is `((2,12,22),)`. `façonne` subjonctif `fa/so/n-` vs indicative
  2 strokes; `pause` VER `po/z-` vs NOM `poz`.
- Impact: 10,539 of 42,225 synthetic rows over 3,628 lemmas; **3,843 become new Words** with an
  extra stroke and miss their real homophones (the rest merge into mixed-lexicon identities,
  which discards their bad `syll_cv`). `fixEvaserWordFinalZSyllabification` patched one lemma.
- Confidence: high (checked in `FirstTheory.pickle`). Reported by: 01 (#4), 02.

**B3. Breakdown built from a LexiqueInfra association that disagrees with the phonology.**
- Where: lexique.py:1021, :1033 with :770-883.
- Defect: the match test uses Infra `phono`, but `syll_cv` is built from `assoc`; nothing checks
  they agree.
- Scenario: `embêter` `phon=@bEte`, `assoc` `ê-e` → `syll_cv=@|b_e|t_e`, so theory 1 types a
  closed `e`; `capharnaüm` loses its final `Om`.
- Impact: 132 mixed-lexicon rows with `syll_cv` ≠ `phon`; 175 VER synthetic rows inherit it
  through the ending tables.
- Confidence: high (data). Reported by: 01 (#2).

**B4. Unmarked alternate entries of self-homographs take unrelated words' only stroke.**
- Where: src/ambiguitychecker.py:1288 (`buildExtraInducedStrokes`), dictionary.py:389.
- Defect: alternate entry strokes skip Different-Lemma or Grammatical-Category Disambiguation (S7), so an alternate entry can equal the
  only stroke of a word of another lemma.
- Scenario: `subits` (ADJ, `s@i/svi/-s`) loses to `subis`'s participle-plural alternate; `pais`
  (`pie/-k`) loses to `paie`'s; `amplis` to `emplis`.
- Impact: **9 spellings with no Plover entry** (subits, pais, amplis, bénits, brandys,
  bégaies, baillez, baryes, repais). Known, documented scope gap, now with measured cost.
- Confidence: high. Reported by: 04; skeleton (scope gap).

**B5. Frequency ties make marking depend on input order (`_starHashCompare` not antisymmetric).**
- Where: src/ambiguitychecker.py:224-225, :232 (tie → first argument marked), used through
  `_starHashCompare` :242-258 and `rankHomophoneCluster` :261.
- Defect: on equal frequency under the frequency-ratio rule (R4), the same-category rule (R5) or the frequency fallback (R7), `compare(a,b) == compare(b,a) == +1`, so the
  ranking depends on lemma-homophone group member order.
- Scenario: `pas`/`pâts` (both 0.0): input `[pas, pâts]` marks `pâts`; `[pâts, pas]` marks `pas`.
- Impact: 648 tied representative pairs in 618 of 4,450 lemma-homophone groups; shuffling group input
  changes marks in **619 groups (14%)**, almost all zero-frequency words. Deterministic run to
  run (order comes from lexicon row order, not hashing), but any lexicon row move, new synthetic
  row or theory-1 regrouping can flip marks. The `aile/ailes/elles/hèle` change of a1d0fb5 is
  **not** such a flip (fully explained by folding `elles` into lemma `elle`). The comparator's
  docstring (:245-250) claims determinism for a branch that never runs.
- Confidence: high (reproduced in memory). Reported by: 04; requested in the merge brief.

**B6. 1990-reform deletion/insertion rules miss inflected forms after lemma normalization.**
- Where: lexique.py:224-225 with :1197-1198 (and `normalizeLemme` :540).
- Defect: deletion/insertion rules are keyed only under `oldSpelling`, but when the same reform
  row also normalizes the lemma, `word.lemme` is already `newSpelling`, so the lemma lookup misses.
- Scenario: lemma `ballotter→balloter`: the mixed lexicon has `balloter` next to `ballottait`,
  `ballottés`, `ballotte`; `dégoter` next to `dégottera`.
- Impact: 67 rows over 24 lemmas (balloter, cachotier, corole, fumerole, greloter, joailler,
  quincailler, ognon, …) keep pre-reform spellings in the Plover output. The comment at
  :220-223 says this case is covered.
- Confidence: high (in-memory regeneration). Reported by: 01 (#1).

**B7. NOM/ADJ exception override keeps the source word's syllabification.**
- Where: util/generateMissingNomAdjForms.py:88, :94 (`overrideCandidate`); related
  src/nomAdjParadigm.py:562 (`morphalou_override`).
- Defect: ortho and phon come from the exception table, `syll_cv`/`orthosyll_cv` from the source word.
- Scenario: `molle`/`molles` (lemma `mou`, ADJ f) get `phon=mOl`, `syll_cv=m_u` and are typed
  like `mou`; `vieux` keeps `vieil`'s placeholder `vjEj`.
- Impact: `molle(s)` among the 12 NOM/ADJ synthetic rows with `syll_cv` ≠ `phon` (the rest
  inherit B3). Separately, 52 `morphalou_override` rows have an `orthosyll_cv` that does not
  spell their ortho (`bijoux` `b_i|j_ou`), low impact since strokes use `syll_cv`.
- Confidence: high. Reported by: 01 (#3).

**B8. Stroke rule never checks that a stroke is pressable.**
- Where: src/keyboard.py:607-620 with dictionary.py:305.
- Defect: key tuples are concatenated without a legality check against `_possibleKeypress`.
- Scenario: `traumatisme` coda `zm` → keys (22,23,25), a 3-key right-pinky press.
- Impact: 529 Words, 39 distinct illegal strokes (mostly "-isme") in the Plover output.
- Confidence: medium (depends on `_possibleKeypress` being the hardware authority). Reported by: 02.

**B9. Identity merge discards the later row's frequency and syllabification.**
- Where: dictionary.py:113-137 (`readCorpus`), fed by lexique.py:1197-1244 (reform rewrites).
- Defect: a later row with a known identity only contributes its verb tag; frequencies are not
  summed and a differing `syll_cv` is silently dropped.
- Scenario: a reform rewrite turns an old-spelling row into the identity of an attested
  new-spelling row (24 identities: `gélinotte`, `allègement`, `acuponcture`, `dessouler`,
  `brunchs`, …); the merged Word keeps only the first row's frequency.
- Impact: undercounted film frequency for 24 Words, which feeds the frequency-ratio rule (R4)
  and the Plover "keep the most frequent" pick. Overall 10,990 rows fold; 5,369 had a different
  `syll_cv` and 6,028 a different film frequency (most are synthetic rows with frequency 0).
- Confidence: medium. Reported by: 01 (#5), 02 (identity merge note).

**B10. Plover export breaks frequency ties by theory-1 order.**
- Where: util/export_plover_dictionary.py:56.
- Defect: `max(..., key=frequency)` keeps the first Word on a tie.
- Scenario: reform pair `dégotés`/`dégottés` (both 0.0): the entry goes to whichever row comes
  first in the lexicon.
- Impact: low; order-dependent in the same way as B5. 20 reform-doublet or near-doublet
  spellings have no entry at all (by design: doublets are never marked).
- Confidence: high. Reported by: 04.

### Tier 2 — affects reports or tracked artifacts (not the Plover output)

**B11. Residual-collision lists in the realization report change between clean rebuilds.**
- Where: src/word.py:94, :155 (`Word._hash` = per-process salted `hash()`, stored in the
  pickles, used by `__hash__`); src/ambiguitychecker.py:1047, :1227 (iteration over the
  `allWords` set); :739-747 (`findCollidingInducedStrokes` pairs each key with the first key
  seen on its stroke); :1248-1257 (bucketing).
- Defect: a clean rebuild gives new hash values, a new set order and a different first-seen
  Word per stroke, so pairs are reversed (('affidées','affidés') ↔ ('affidés','affidées')) and
  bucket membership changes (A1, A2 same ortho + B: A1 first → one cross-lemma pair; B first →
  two).
- Impact: `realization_report.json` cross-category clashes seen as 34, 40 and 38 and
  cross-lemma collisions as 1,283 and 1,292 on different rebuilds. Confirmed empirically: with
  the same pickles, four different `PYTHONHASHSEED`s gave identical `theory2.tsv`, realization
  report and Plover dictionary; fresh pickles changed only the report's residual lists. Chosen
  keys, theory 2 and the Plover dictionary are unaffected (`_feasible` uses order-independent
  `any`/`all`; `buildFinalInducedStrokes` iterates theory-1 dict order).
  `docs/refactor/rebuild_and_hash.sh` pins `PYTHONHASHSEED=0` as a workaround. Fix direction:
  sort `allWords` and report every pair within a stroke bucket.
- Confidence: high. Reported by: 03; main session (empirical check).

**B12. The precedence-spec checker covers much less than the spec.**
- Where: util/check_conjugation_disambiguation_order.py:69-77, :100-126.
- Defect: "masculine must be free" is checked for participles only (ADJ/NOM gender and finite
  indicatif Feature Combinations never); impératif/subjonctif are "mandatory" in the spec
  (conjugation_disambiguation_order.txt:55-58) but an empty discriminating feature set passes; the line order is never checked.
- Scenario: an answer leaving an impératif Feature Combination as the `∅` default produces no violation.
- Impact: the validation report can be clean while answers contradict the spec.
- Confidence: medium. Reported by: 03.

**B13. Verb paradigm completion is not idempotent.**
- Where: util/completeVerbParadigms.py:95-97 with :324-340.
- Defect: "already attested" comes from `FirstTheory.pickle`, and `writeSynthetic` does not
  deduplicate against the file.
- Scenario: `--apply` twice without deleting the pickles appends the same rows again to the
  tracked `LexiqueSynthetic.tsv` (duplicates later merge by identity, so only the file grows).
- Confidence: medium. Reported by: 01 (#7).

**B14. Human views go stale with the caches.**
- Where: dictionary.py:498-505 (`theory.tsv` written only on a `FirstTheory.pickle` miss);
  dictionary.py:531 (first run writes `theory2.tsv` from possibly stale discriminating feature sets).
- Impact: low; both files are gitignored human views that nothing reads.
- Confidence: high. Reported by: skeleton.

### Tier 3 — latent (no measured current impact)

**B15. Pickle caches are never invalidated.** dictionary.py:451, :498. Neither cache is checked
against the lexicon TSVs, `excluded_words.txt` or `starboard3h.json`, and `FirstTheory.pickle`
does not depend on the layout. Scenario: edit `starboard3h.json` (move coda `m` off 25), run
`dictionary.py` and the exporters → theory 1 keeps old key indices while `strokesToRTFCRE`
renders them with the new names: a silently wrong Plover dictionary. Same trap after any lexicon
fix without `rm -f *.pickle`. Confidence: high (mechanism); likelihood low while the layout is
frozen. Reported by: 02, skeleton.

**B16. First-seen pairing can hide same-lemmeGramCat collisions.** src/ambiguitychecker.py:739-747
with :1248-1250. X and Z (same `lemmeGramCat`) and Y (another lemma) on one stroke: if Y is seen
first, only (Y,X) and (Y,Z) are reported (cross-lemma) and the real pair (X,Z) never reaches
`residualCollisions`; whether the invariant shows 0 depends on hash order. No instance observed.
Confidence: high (mechanism). Reported by: 03.

**B17. `buildFinalTheory` ignores unassigned groups and residuals.** dictionary.py:380-389.
If a keypress group cannot be realized, its Words silently lose that feature discriminating stroke in theory 2 and the
Plover dictionary; only the separate report build would show it. Not triggered (all 7 groups
have keys). Confidence: medium. Reported by: 03.

**B18. Trainer legend can disagree with the dictionary.** util/export_keyboard_layout.py:128.
The legend reads the tracked realization report; the dictionary recomputes keys inline; nothing
compares them. Scenario: rerun Discriminating-Feature Grouping (Grouping Phase) without rebuilding the report → legend
shows old keys. They agree today (verified). Confidence: medium. Reported by: skeleton, 04.

**B19. Null `chosenKeys` crashes the trainer legend.** util/export_keyboard_layout.py:133-141,
:144. An unassigned group (`chosenKeys: null`) raises `TypeError` and the sort compares `None`.
Not triggered. Confidence: high; likelihood low. Reported by: skeleton, 04.

**B20. `_resolveEntryWord` silently falls back to the first candidate.**
src/ambiguitychecker.py:800. When an entry's strokes match no theory-1 Word (stale resolved discriminating feature sets
after a lexicon fix without rerunning Discriminating-Feature Elicitation (Elicitation Phase)), `candidates[0]` gets the
marks instead of failing. Confidence: medium. Reported by: skeleton.

**B21. Extra alternates of empty-primary spellings are never verified.**
src/ambiguitychecker.py:1227-1241. Only Words in `allWords` (non-empty primary) get their
alternates checked; 2,749 spellings have an empty primary and non-empty alternates ("abaisse"
[∅, {impératif}, {pers_1}, {subjonctif}]). 0 collisions with theory 1 today (see B4 for the
cross-lemma shadowing that does happen). Confidence: medium (gap). Reported by: 03.

**B22. Collision tests compare raw strokes.** src/ambiguitychecker.py:1114, :1142, :1243-1247.
`stroke in theory`, `finalizedWordsByStroke` and `findCollidingInducedStrokes` use raw Strokes
although collisions are physical (canonical). 0 cases today (read-only canonical check).
Confidence: medium (mechanism). Reported by: 03.

**B23. Non-live hard-rule feature raises `KeyError`.** src/featuregroupingsat.py:117 with :128-135. If a
feature in `ALONE_KEYS`/`MUST_DIFFER_GROUPS` stops being live (e.g. nobody checks `infinitif`),
`x[m1, k]` raises instead of a clear error. Confidence: high; likelihood low. Reported by: 03.

**B24. A solver timeout can lock a non-optimal result.** src/featuregroupingsat.py:172, :274, :398
(locks at :178, :282, :405). FEASIBLE is accepted and locked, so a timeout makes the tier score
or tie-break neither proven nor reproducible. Confidence: low. Reported by: 03.

**B25. The frequency-ratio rule (R4) and the category-priority rule (R6) can form a cycle.** src/ambiguitychecker.py:224 vs :229. A ADV f=1, B NOM f=2,
C VER f=10: A<B (R6), B<C (R6), C<A (R4) → order-dependent sort. 0 cycles among live
representatives. Confidence: high (possible); low impact. Reported by: 04.

**B26. Doublet merge checks only the representative's lemma.** src/ambiguitychecker.py:321-326.
If a lower-frequency homograph carries the lemma that forms the reform pair, the doublet is
missed and marked as a real ambiguity. 0 instances. Confidence: low. Reported by: 04.

**B27. Word identity is fragile.** src/word.py:94, :161. `_hash` hashes a separator-free
concatenation (theoretical collisions) and `__eq__` compares only `_hash`, so Words from pickles
written by different processes never compare equal (e.g. after deleting only
`Dictionary.pickle`). Nothing on the main path mixes pickles today. Root cause of B11.
Confidence: low-medium. Reported by: skeleton, 02.

**B28. `zip` truncation can leave a syllable unregistered.** dictionary.py:177. 99 Words have
phonetic and orthographic syllable lists of different lengths; their extra syllables are not
registered from that Word, and a unique one would make `buildTheory` (:310) raise `KeyError`.
Not triggered. Confidence: medium. Reported by: 02.

**B29. `lexicalPhonemeAmbiguityScore` looks up a word phonology as a syllable name.**
src/grammar.py:913, :931. `getSyllable("apodiR")` → `None`, so the "both phonemes in one
syllable" branch adds 0 for polysyllabic words. Impact: `lexicalAmbiguity` → fallback keymap
only. Confidence: high. Reported by: 02.

**B30. `optimizeOrder` starts from set order.** src/grammar.py:307-320. The best permutation
(and README.md:92-146 figures) can change with the hash seed. Impact: fallback keymap only.
Confidence: medium. Reported by: 02.

**B31. Multiphoneme frequencies are always 0.** src/grammar.py:566, :574-584. All 353 values
are 0.0; no reader. Confidence: high; impact none. Reported by: 02.

**B32. The layout solver wipes the layout before solving.** src/cpsatsolver.py:422
(not run). `keyboard.clearLayout()` clears all three banks; an infeasible or timed-out part
leaves its bank empty and the next `buildTheory` raises `IndexError`. Confidence: medium.
Reported by: 02.

**B33. `lexique.py` rebuilds on import.** lexique.py:1261-1263. No `__main__` guard: importing
it overwrites `LexiqueMixte.tsv`. No importers today. Confidence: high; risk low. Reported by: skeleton.

**B34. `Lexique` keeps its rows in class-level lists.** lexique.py:957-958. A second `Lexique()`
in one process would double every row and break breakdown matching. Not triggered.
Confidence: high; likelihood low. Reported by: 01 (#6).

**B35. The sentence exporter's drill-item gate depends on another process.**
util/export_practice_sentences.py:158. It compares against `practice-words.json` written by a
separate recompute of theory 2; if inputs changed between the two runs, valid sentences are
rejected. Confidence: medium; impact low. Reported by: 04.

---

## Dead-code observations

Each item: what, evidence, stage source. Raw material for Dead-Code Removal (Pass 5); nothing is
removed without per-item approval.

1. **NOT DEAD — Keyboard Layout Optimization (S4), user decision b5.** **`optimizeKeyboard`
   import** (`cpsatsolver.optimizeKeyboard`, dictionary.py:32) — only unused because the S4 call
   is commented out at dictionary.py:494; do not remove without deciding how S4 is invoked.
   `src.cpsatoptimizer` import commented at :47. The import still loads OR-Tools on every
   `import dictionary`, including every exporter through util/_theoryio.py:18. (02, skeleton)
2. **NOT DEAD — Keyboard Layout Optimization (S4), user decision b5.** Layout statistics:
   **Phoneme order search and Ambiguity statistics** — `Syllable.optimizeBiphonemeOrder`
   (src/grammar.py:644) and `Dictionary.analyseAmbiguities` (dictionary.py:183), called at
   dictionary.py:464-466 on every fresh rebuild (the slowest step). Verified: outputs reach only
   `generateBaseKeymap`, `cpsatsolver.optimizeKeyboard` (call commented out),
   `writeConstrainFiles` (call commented :481), `printSyllabificationStats` (call commented :478), `printBarchart`. (02, skeleton)
3. **NOT DEAD — Keyboard Layout Optimization (S4), user decision b5.** **Fallback keymap** —
   `Dictionary.generateBaseKeymap` dictionary.py:212 and `getLowAmbiguityPhonemes` :296: reachable only when `starboard3h.json` is missing; the layout
   is never saved and exporters would fail anyway. (02)
4. **Unused scorer twins** — `analysePhonemSyllabicAmbiguity_serial` src/grammar.py:1007,
   `analysePhonemeLexicalAmbiguity_serial` :1071, forked `analyseMultiphonemeLexicalAmbiguity`
   :1171. (02)
5. **Unused `Dictionary` fields** — `stemmOfLemme` (never filled), `wordsByLemme` (no reader),
   `totalFrequencies`, `frequentWordsFrequencies`, `syllableClass`; `printVerbose`
   dictionary.py:51 is a no-op. (02)
6. **Pickled `Syllable` class state** — the four class collections in `Dictionary.pickle` are
   reloaded by 5 loaders and used by none; `Syllable.phonoWords` serves only the dead scorers but
   inflates the 57.8 MB pickle. (02)
7. **Keyboard demos** — `Starboard.setIrelandEnglishLayout` src/keyboard.py:718 and
   keyboard.py `__main__` :742 (loads the missing `starboard1h.json`). (02)
8. **Lexique helpers never called** — `Lexique.printTopWordsFilm`/`printTopWordsBooks`
   lexique.py:1087-1095; `lexique.Word.isSyllConsensus`/`isOrthoSyllConsensus` :933-951. (01)
9. **No-op expression** — lexique.py:775 `_ = syllNb == len(cv_syll) - 1`. (01)
10. **`printSyllabificationStats` statistics** — lexique.py:1097: `sylCol`, `Syllable` class
    state and `moveDualPhonem` :1055 are never read. **Not removable as-is**: its
    `words.sort(...)` side effect (:1101) fixes the row order of `LexiqueMixte.tsv`. (01)
11. **Debug tracing** — `verboseList`/`printVerbose` lexique.py:32-36 (6 hard-coded words). (01)
12. **Stale exclusion** — `lexiconExclusions.tsv` entry `schampooiner` matches no Lexique383 row (data). (01)
13. **Legacy discriminator path still gating paradigm completion** —
    `src/featureextractor.py` (`extractDiscriminatingFeatures` :31, `buildDiscriminatorSelection`
    :284) is imported only by util/completeVerbParadigms.py (`confirmCandidates` :266,
    `detectUndersampledLemmas` verbparadigm.py:681, `newlyCollidingLemmas` :646) and the
    diagnostic `src/ambiguitychecker.py` `__main__`. Retiring it requires re-gating or retiring
    Verb paradigm completion (S2.1). (01, skeleton)
14. **Greedy Discriminating-Feature Grouping (Grouping Phase)** — src/featuregrouping.py `runFeatureGrouping` :247, `greedyColorMarkers`
    :117 (also set-order dependent), `coOccurrencePairs` :75, `wouldCollideIfMergedPairs` :89,
    `_findSharedKeypressPair` :222, `FeatureGroupingResult` :214, `__main__` :294: called only by
    src/test/featuregrouping_test.py and its own `__main__`. The live path uses only featuregrouping's loaders,
    `liveMarkers`, `verifyKeypressAssignment`, `inducedPressSet`, `frequencyWeightedChordSizes`. (03, skeleton)
15. **"Preferring" grouping path** — src/featuregroupingsat.py `minKeypressesSatPreferring` :455,
    `_bestAssignmentPreferring` :232 and the `mustShareKey` branch of `_feasibleAssignment`:
    reached only from featuregroupingsat `__main__` :570 and tests. (03)
16. **"Phase 0 ambiguity report" diagnostic** — src/ambiguitychecker.py `__main__` :1326 and
    what only it reaches: `_selectCanonicalIndex` :557, `buildAtomicFeatureToWords` :568,
    `findFeatureKeypresses` :623, `checkComposedChords` :669, `_appendCodaAddition` :593,
    `_isFeasibleAddition` :601, `classifyTheory` :483, `classifyStrokeCluster` :448,
    `detectCrossCategoryClash` :59 (also tests). `findCollidingNewAdditions` :750 has test callers
    only. (03, 04, skeleton)
17. **`FEATURE_PRIORITY` and `assignDiscriminatorKeypresses`** — src/greedyoptimizer.py:16
    feeds only `_selectCanonicalIndex` (item 16) and `assignDiscriminatorKeypresses` :196/:305,
    which only src/test/greedyoptimizer_test.py calls. `GRAMCAT_PRIORITY` (:62) is live. (03)
18. **`satOptimizeDiscriminator`** — src/satoptimizer.py:282; the module is imported only by
    src/test/satoptimizer_test.py (checked during the merge). (merge; CLAUDE.md item 7)
19. **Print-only elicitation statistics** — src/elicitation.py `reportScale` :164,
    `enumerateOppositionSamples` :107, `_greedyColorCount` :126: live but their output feeds
    nothing. (03)
20. **Redundant press resolution** — src/elicitation.py:586, inside :587, :616 compute
    `resolvePressByCombination` three times per run (identical results). Not dead; redundant. (03)
21. **One-shot answer rewriter** — util/build_pers3_default_answers.py:177 overwrites
    `elicitation_answers.json`; rerunning undoes hand fixes 4e73533, 688c74d, 3b22e0f. Hazardous. (03, skeleton)
22. **Unreachable marking branches** — `decideStarHashMark` homograph exemption (R1) (:211) and reform-doublet exemption (R2) (:214) and
    `_starHashCompare`'s `None` fallback (:254-257) cannot fire in the pipeline because
    `assignStarHashMarks` merges homographs and doublets first; kept for the pairwise API and tests. (04)
23. **Unreached `MARKING_OVERRIDES` entries** — {new, news}, {réaux, réal}, {dévonien,
    dévonienne}, {stabilisant, stabilisante} are in no lemma-homophone group today (45 of 49
    entries are reached). (04)
24. **Appended mode of `composeReservedKeyStrokes`** — `phonemeStrokeCounts is None`
    (src/ambiguitychecker.py:440-441) is used only by tests (src/test/ambiguitychecker_test.py:393,
    :411, :422, :430). (04)
25. **Thin theory loaders** — util/_theoryio.py `loadFirstTheory` :42 (one caller,
    build_realization_report.py:44) and `loadFinalTheory` :48 (one caller, export_plover_dictionary):
    live, but could fold into `loadFirstAndFinalTheory`. (04)
26. **`buildFinalTheory` as a method** — dictionary.py:342 never uses `self`; exporters unpickle
    the whole `Dictionary` just to call it. Refactor candidate, not dead. (04)

---

## Doc drift

Format: where — what the doc says; what the code does. Grouped by document.

### CLAUDE.md
1. CLAUDE.md:56 — Discriminating-Feature Grouping (Grouping Phase) "K=5, proven optimal"; the artifact has K=7 since
   688c74d (K=5 at 8330b8e/0fa69af, K=6 from 4e73533).
2. CLAUDE.md:56 — lists "`src/featuregrouping.py` greedy" as part of Discriminating-Feature Grouping (Grouping Phase); the
   greedy path is not live (dead-code item 14).
3. CLAUDE.md:59 (item 7) — "Legacy path still live in `dictionary.py` `__main__`";
   `buildDiscriminatorSelection`/`satOptimizeDiscriminator` are no longer called there
   (dictionary.py:521-527 says the path was retired); `satOptimizeDiscriminator` is test-only.
4. CLAUDE.md:59 — "`FEATURE_PRIORITY`/`GRAMCAT_PRIORITY` … still do live work (canonical-form
   picks)"; only `GRAMCAT_PRIORITY` is live (category-priority rule (R6) of Different-Lemma or Grammatical-Category Disambiguation (S7),
   ambiguitychecker.py:227); the canonical member of a homophone group comes from the
   elicitation answers.
5. CLAUDE.md:52 (item 3) — Feature Extraction "feeds the legacy path below"; it now feeds only
   Synthetic Lexicon Building (S2)'s gating and the ambiguitychecker diagnostic.
6. CLAUDE.md:51 — "Dictionary Loading … Indexes words by … frequency; identifies homophones";
   there is no frequency index (the list is sorted by frequency) and homophones appear only as
   theory-1 entries in `buildTheory`; it also omits `LexiqueSynthetic.tsv` (42k rows,
   dictionary.py:68).
7. CLAUDE.md:63 — "23 consonants + 16 vowels"; src/grammar.py:33 has 20 consonants.
8. CLAUDE.md:64 — `GramCat` "21 grammatical categories"; the enum has 22 (word.py:10).
9. CLAUDE.md:77 — "Onset (consonants) → Nucleus (vowels) → Coda"; `8` (ɥ) is a nucleus
   phoneme, `j`/`w` are consonants, all consonants after the first vowel go to the coda, and
   vowel-less syllables go entirely to the onset (grammar.py:499-518).
10. CLAUDE.md:79 — `starboard3h.json` "26 keys, 4 reserved for control"; 22 phoneme keys, and
    the reserved keys are mark keys (10 `*`, 15 `#`) plus 0/1 held for a third mark.
11. CLAUDE.md:50 — "136k French words"; 136,456 *rows* (not distinct words), 167,639 Words
    once synthetic rows are added.
12. CLAUDE.md pipeline list — does not say that exporters recompute theory 2 and that nothing
    reads `theory2.tsv`, nor mention the pickle-cache trap or `PYTHONHASHSEED`.

### README.md
13. README.md:72-73 — "137k of the 142k words", "136,348 words"; 137,822 Infra rows,
    `LexiqueMixte.tsv` has 136,456 rows.
14. README.md:92-146 — best-permutation figures depend on the per-process hash seed (B30).
15. README.md:221-226 — the `*`/`#` case is "still unaddressed" and names the retired
    discriminator functions; Different-Lemma or Grammatical-Category Disambiguation (S7) is live.

### ROADMAP.md, LEXICON_RECOMPUTE_PIPELINE.md, design notes, root GLOSSARY.md
16. ROADMAP.md:175 and src/ambiguitychecker.py:200 — the frequency-ratio rule (R4) called a "frequency-ratio exemption";
    the rarer word is still marked.
17. ROADMAP.md:183-184 — "biggest real cluster: 7 readings (au/eau/oh/haut/ho/ô/aux)"; that
    lemma-homophone group has 8 representatives (plus `aulx`); the largest groups have 11 Words.
18. LEXICON_RECOMPUTE_PIPELINE.md:22 — lists only Lexique383 and Infra as `lexique.py` inputs;
    it also reads `lexiconExclusions.tsv`, `reform1990.tsv`, `verbs-fr.xml`.
19. LEXICON_RECOMPUTE_PIPELINE.md:23 — paradigm completion "reads `Lexique383.tsv`"; it reads
    `FirstTheory.pickle` (mixed + synthetic), Verbiste and `verbModelExceptions.tsv`
    (`generateMissingNomAdjForms` also Morphalou and `nomAdjModelExceptions.tsv`).
20. LEXICON_RECOMPUTE_PIPELINE.md:56-58 — advises patching `LexiqueMixte.tsv` directly to avoid
    "unrelated full-file regen diffs"; a regeneration is byte-identical today.
21. LEXICON_RECOMPUTE_PIPELINE.md — calls `realization_report.json` a "reference
    artifact"; export_keyboard_layout.py:128 consumes it.
22. DESIGN_alternate_press_sets.md §4 — lists realizing each alternate through the full
    composition search as option (a); alternates only reuse the primary search's keys and are
    verified only for non-empty primaries.
23. RESUME_2026-09-20-starhash-priority.md — numbers the marking rules ratio = 1, homograph =
    2, doublet = 3; the code docstring numbers homograph = R1, doublet = R2 (see item 33).
24. GLOSSARY.md (root) "Signature" — describes a union across readings; superseded by
    per-Feature-Combination alternates (elicitation.py:374).
25. GLOSSARY.md (root) "Reading" — prefers "Feature Combination"; the plan, the JSON field and
    the trainer use "Reading" (decision a2: use "Feature Combination").

### Code comments and docstrings — Lexicon Building (S1) and Synthetic Lexicon Building (S2)
26. lexique.py:89-94, :135-145, :317 — reform flags "Off by default"/"opt-in"; all five
    `APPLY_1990_REFORM_*` flags are `True` (:95, :145, :326, :420, :505, :534).
27. lexique.py:220-223 — the lemma fallback "finds deletion rules whenever word.ortho … still
    needs rewriting"; it does not once the lemma is normalized (B6).
28. util/completeVerbParadigms.py:27-31, :405; util/fixPayerDualFormGaps.py:38-41;
    util/fixAsseoirDualFormGaps.py:34 — `LexiqueSynthetic.tsv` "not yet wired"; dictionary.py:66-69 reads it.
29. src/nomAdjParadigm.py:28-30 — `newlyCollidingLemmas` reused as the NOM/ADJ collision
    check; `generateMissingNomAdjForms.py` runs none.

### Code comments and docstrings — Dictionary Loading (S3) and Phonetic Theory Building (S5)
30. src/word.py:62 — `frequency` is a "chosen mix of the film and book frequencies"; film only (:93).
31. src/grammar.py:32 — comment lists `G` and `N` among nucleus symbols; they are consonants (:33).
32. src/keyboard.py:193-196 — `getStrokeOfSyllableByPart` docstring "Get the list of strokes";
    it returns one stroke.

### Code comments and docstrings — Same-Lemma and Grammatical-Category Disambiguation (S6) and Different-Lemma or Grammatical-Category Disambiguation (S7)
33. src/ambiguitychecker.py:392 ("Rule 2", homograph) and :431 ("Rule 3", doublet) — RESUME
    numbering; the docstring calls them R1/R2.
34. src/ambiguitychecker.py:14, :65 — cite a stale anchor "dictionary.py:496-505".
35. src/ambiguitychecker.py:998, :1060 — "Phase G's 6 groups"; K=7.
36. src/ambiguitychecker.py:1303 (`buildExtraInducedStrokes` docstring) — the `*`/`#` track
    "isn't yet wired into dictionary.py's persisted output"; it is (dictionary.py:385).
37. src/ambiguitychecker.py:206-208 — category pairs outside the table "not observed"; 93
    representative pairs use the frequency fallback (R7) (`aux`/`oh`, `à`/`a`).
38. src/ambiguitychecker.py:245-250 (`_starHashCompare` docstring) — the frequency/ortho
    fallback keeps the sort "stable and deterministic"; that branch never runs, and real ties
    have no tie-break (B5).
39. dictionary.py:357-360 (`buildFinalTheory` docstring) — accurate that alternate entries skip the
    star/hash marks, but silent on alternates now taking unrelated words' only stroke (B4).
40. src/featuregroupingsat.py:7 "K=6/7"; util/build_keypress_groups.py:18-19 "still K=6 … all three
    soft tiers fully achieved" (tiers still achieved, K is 7); util/build_pers3_default_answers.py:9 "model 2 (K=6)".
41. src/featuregroupingsat.py:17-20 — "47,799 homophone groups … ~200 distinct problems"; 47,828 and 294.
42. src/elicitation.py:3-15 — module "only measures"; it builds questionnaire items, resolves
    answers and writes `resolved_press_sets.json`.
43. src/elicitation.py:560-561 — prints "K lower bound" for a greedy coloring (an upper bound,
    docstring :127-129).
44. util/check_conjugation_disambiguation_order.py:12 — subjonctif press "must be exactly
    {"subjonctif"}"; the code (:116-126) and the spec allow one `pers_*`/`nbr_*` clarifier.
45. util/check_conjugation_disambiguation_order.py:3-4 — calls the spec an ordered precedence
    vocabulary; the order is parsed but unused.
46. util/build_realization_report.py:10-12 — "does NOT yet rewrite theory"; theory 2 now
    exists via `buildFinalTheory`.

### Code comments and docstrings — Theory Export (S8)
47. util/export_plover_dictionary.py:12-14; util/export_practice_words.py:13-15 — collisions
    remain for "one word >10x rarer"; the frequency-ratio rule (R4) marks the rarer word. Remaining collisions are
    homographs, doublets, same-lemmeGramCat residuals (B1) and alternate shadowing (B4).
48. util/export_practice_words.py:4-6 — deduplicated "on `ortho` … keeping the
    highest-frequency one"; keyed by (ortho, steno) with merged labels (:225).
49. util/_theoryio.py:1-4 — factored out of `build_realization_report.py`, which "duplicated
    this exact block"; that script now uses only `loadFirstTheory`.
50. util/export_keyboard_layout.py:15-17 — the realization report is "optional"; without it the
    legend is silently empty.
51. "run dictionary.py once first to generate it" (for `starboard3h.json`) at
    build_realization_report.py:47, export_plover_dictionary.py:38, export_plover_system.py:41,
    export_keyboard_layout.py:151, export_practice_words.py:216, export_practice_sentences.py:153,
    export_definitions.py:49, ambiguitychecker.py:1346 — `dictionary.py` never writes it
    (`toJSONFile` commented at :496).

### Refactor working files
52. 00-skeleton.md §1 step 0 and STAGE_BRIEF.md mention `resources/reform1990*.tsv`; only
    `resources/reform1990.tsv` exists.
53. 00-skeleton.md §2 — "Homophones share a key" in theory 1; true only for raw Strokes (233
    canonical-only collisions are split across entries).
