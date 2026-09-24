# TODO

Written to survive a `/clear` — read this file first in a fresh session.

## Suspected bugs (from docs refactor, 2026-09-22)

Found while writing `docs/PIPELINE.md` (full write-ups, evidence and confidence in
`docs/refactor/callgraph/90-findings.md` — kept in git history once the refactor folder is
removed — same B-numbers). **Not yet reviewed by the user; nothing has been fixed.** Tier 1
changes the Plover dictionary (or other exported output) today; tier 2 changes reports or
tracked artifacts; tier 3 is latent (no measured impact). B39/B40 were dropped: their code
was removed in Dead-Code Removal (Pass 5).

### Tier 1 — affects the Plover output today

- **B1** Spelling twins: only the first Word of a spelling gets its feature discriminating stroke —
  src/ambiguitychecker.py:797-800 (`_resolveEntryWord`) — Words sharing (ortho, `lemmeGramCat`) and
  strokes: `next(...)` marks one ("agis" participle vs finite). 230 same-lemmeGramCat collision pairs;
  99 pairs in 98 strokes reach the disambiguated theory unmarked. Invisible to the 0-residual invariant.
- **B2** Synthetic verb forms get a vowel-less trailing syllable — src/verbparadigm.py:561, :611 —
  radical cut by character count keeps the infinitive's syllable boundary (`cannes` sub:pre:2s: 2
  strokes vs NOM 1). 3,843 new Words carry an extra stroke and miss their real homophones.
- **B3** Breakdown built from a LexiqueInfra association that disagrees with the phonology —
  lexique.py:1021, :1033 (with :770-883) — match uses Infra `phono`, `syll_cv` comes from `assoc`
  (`embêter` typed with closed `e`). 132 mixed-lexicon rows; 175 VER synthetic rows inherit it.
- **B4** Alternate entries of self-homographs take unrelated words' only stroke —
  src/ambiguitychecker.py:1288 (`buildExtraInducedStrokes`), dictionary.py:389 — alternate entry
  strokes skip the star/hash marks (`subits` loses to `subis`). 9 spellings have no Plover entry.
- **B5** Frequency ties make star/hash marks depend on input order — src/ambiguitychecker.py:224-232,
  `_starHashCompare` :242-258 — not antisymmetric on equal frequency (`pas`/`pâts`). Shuffling input
  changes marks in 619 of 4,450 lemma-homophone groups (14%); any lexicon row move can flip them.
- **B6** 1990-reform deletion/insertion rules miss inflected forms after lemma normalization —
  lexique.py:224-225 with :1197-1198 — rules keyed under `oldSpelling`, lemma already normalized
  (`balloter` beside `ballottait`). 67 rows over 24 lemmas keep pre-reform spellings in Plover.
- **B7** NOM/ADJ exception override keeps the source word's syllabification —
  util/generateMissingNomAdjForms.py:88, :94 — ortho/phon from the exception table, `syll_cv` from the
  source (`molle(s)` typed like `mou`). Among 12 NOM/ADJ synthetic rows with `syll_cv` ≠ `phon`.
- **B8** Phonetic stroke rule never checks that a stroke is pressable — src/keyboard.py:607-620 with
  dictionary.py:305 — no check against `_possibleKeypress` (`traumatisme` coda `zm` → 3-key
  right-pinky press). 529 Words, 39 distinct illegal strokes in the Plover output.
- **B9** Identity merge discards the later row's frequency and syllabification —
  dictionary.py:113-137 (`readCorpus`) — frequencies not summed, differing `syll_cv` dropped (24
  reform-rewrite identities: `gélinotte`, …). Undercounted frequency feeds the frequency-ratio rule
  (R4) and the Plover "most frequent" pick.
- **B10** Plover export breaks frequency ties by phonetic-theory order — util/export_plover_dictionary.py:56
  — `max(key=frequency)` keeps the first Word (`dégotés`/`dégottés`, both 0.0). Low impact;
  order-dependent like B5.

### Tier 2 — affects reports or tracked artifacts (not the Plover output)

- **B11** Residual-collision lists in the realization report change between clean rebuilds —
  src/word.py:94, :155; src/ambiguitychecker.py:739-747, :1248-1257 — salted `hash()` stored in the
  pickles sets `allWords` order and first-seen pairing. Cross-category clashes 34/40/38, cross-lemma
  1,283/1,292 across rebuilds; the disambiguated theory and Plover unaffected (`PYTHONHASHSEED=0` workaround).
- **B12** The precedence-spec checker covers much less than the spec —
  util/check_conjugation_disambiguation_order.py:69-77, :100-126 — "masculine must be free" checked
  for participles only; mandatory impératif/subjonctif and line order unchecked. The validation
  report can be clean while answers contradict the spec.
- **B13** Verb paradigm completion is not idempotent — util/completeVerbParadigms.py:95-97 with
  :324-340 — `--apply` twice without deleting the pickles appends the same rows again to the tracked
  `LexiqueSynthetic.tsv` (duplicates merge by identity; only the file grows).
- **B43** The S2.1 appender's "confirmed to cause a new discriminator collision" gating is
  PYTHONHASHSEED-sensitive (found 2026-09-24 via the pipeline-timing test run): on the same
  converged tree and identical pickles, `python -m util.completeVerbParadigms` (dry run) reports
  0 flagged lemmas / 0 candidate rows under `PYTHONHASHSEED=0` but 10 / 84 unpinned, so an
  unpinned `python dictionary.py` (or S2 wrapper) appends 84 rows to the tracked
  `LexiqueSynthetic.tsv` a pinned run wouldn't — and then cascades a pickle rebuild (~95 s)
  plus a full extra S2 round (~330 s at the time): the 726 s S2 step was mostly this cascade.
  (Since the 2026-09-24 S2.1 speedup — `extractDiscriminatingFeatures` 75 s → 14 s,
  `detectUndersampledLemmas` 127 s → 4 s — a pinned S2 step takes ~67 s, so the extra round
  is much cheaper, but the 84 unwanted rows remain.)
  Mechanism (confirmed 2026-09-24 with digest-instrumented dry runs, `scratch/b43_probe.py`
  and `scratch/b43_probe2.py`): every stage through candidate generation is content-identical
  across seeds (same 1,817 structural candidates, identical baseline selection and
  collisions). The seed does NOT enter through candidate order (an earlier hypothesis): the
  augmented pass fed seed-1-ordered candidates under seed 0 gives byte-identical feasible
  options, chosen discriminators and feature-set keys as seed-0 order, once the generated
  Words' cached `_hash` is recomputed. The only seed channel is `Word._hash` itself
  (`src/word.py:94`, a salted `hash()` of an f-string, cached at construction and pickled
  with the Word): `extractDiscriminatingFeatures` returns `dict[WordFeature, set[Word]]`, and
  `set[Word]` iteration order follows those hash values into `buildFeasibleDiscriminatorOptions`
  / `selectSharedDiscriminators` tie-breaks, and from there into `buildDiscriminatorSelection`'s
  word-order feature-set tuples (e.g. `('s','p')` 20,902 lemmas vs `('p','s')` 3,125 are
  distinct keys) that `crossLemmaFeatureSetCollisions` compares literally. Theory Words carry
  the hashes of whatever process built `PhoneticTheory.pickle`; freshly generated candidate
  Words get the current process's — under an unpinned run the two regimes are mixed.
  Related latent bug (unverified impact): `Word.__eq__` (`src/word.py:158`) compares only
  `_hash`, so a pickled Word and an identical freshly constructed Word compare unequal (and
  miss in dict/set lookups) whenever the pickle was built under a different seed. Amplifier: the confirm pass re-runs the global
  shared-discriminator selection on the augmented theory, reshuffling ~2,000 uninvolved
  lemmas' tuples (1,994 flagged under seed 0, 2,004 unpinned) — the gate mostly measures
  set-cover reshuffle noise, and the seed decides whether a candidate lemma lands in it
  (seed 0: none → 0 rows; two independent unpinned draws: 10 → the same 84 rows, so random
  seeds agree and PYTHONHASHSEED=0 is the outlier). Same salted-`hash()` family as B11/B27.
  Workaround: always pin `PYTHONHASHSEED=0` for anything that can run the appenders.
  Candidate fixes: make `Word._hash` seed-independent (e.g. a `hashlib.blake2b` digest of the
  same fields) and `__eq__` compare the fields — removes the whole salted-Word-hash family
  (likely B11/B27 too) but changes every `set[Word]` iteration order, so it needs a
  LexiqueSynthetic.tsv re-convergence and new output baselines; alternatively (or also) make
  the feature-set key order-insensitive (sorted (feature, word) pairs or frozenset — changes
  which collisions are detected, same re-convergence); restricting the augmented
  selection to the receiving stroke groups would also remove the ~2,000-lemma noise and the
  second full-corpus extraction pass.
- **B14** RESOLVED 2026-09-24 (the theory-build extraction into `util.build_phonetic_theory` /
  `util.build_disambiguated_theory`): `phonetic_theory.tsv` is now written on every run (pickle
  hit or miss; a pickle round-trip preserves dict order, so the bytes are stable), and
  `disambiguated_theory.tsv` is only ever written by its own command from the JSONs that exist
  at that moment — the old buildOnly could emit it from stale inputs mid-run.

### Tier 3 — latent (no measured current impact)

- **B15** Pickle caches are never invalidated — dictionary.py:451, :498 — not checked against the
  lexicon TSVs, `excluded_words.txt` or `starboard3h.json`; editing the layout without
  `rm -f *.pickle` yields a silently wrong Plover dictionary. Likelihood low while the layout is frozen.
- **B16** First-seen pairing can hide same-lemmeGramCat collisions — src/ambiguitychecker.py:739-747
  with :1248-1250 — X, Z (same `lemmeGramCat`) and Y on one stroke: if Y is seen first, (X,Z) never
  reaches `residualCollisions`. No instance observed.
- **B17** `buildDisambiguatedTheory` ignores unassigned Keypress Groups and residuals — dictionary.py:380-389
  — an unrealizable group's Words silently lose their feature discriminating stroke in the disambiguated theory and
  Plover. Not triggered (all 7 groups have keys).
- **B18** Trainer legend can disagree with the dictionary — util/export_keyboard_layout.py:128 —
  legend reads the tracked realization report, the dictionary recomputes keys inline; rerunning
  Discriminating-Feature Grouping (Grouping Phase) without the report build shows old keys. Agree today.
- **B19** Null `chosenKeys` crashes the trainer legend — util/export_keyboard_layout.py:133-141, :144
  — an unassigned group raises `TypeError`. Not triggered.
- **B20** `_resolveEntryWord` silently falls back to the first candidate — src/ambiguitychecker.py:800
  — stale resolved discriminating feature sets (lexicon fix without rerunning Discriminating-Feature
  Elicitation (Elicitation Phase)) mark `candidates[0]` instead of failing.
- **B21** Extra alternates of empty-primary spellings are never verified —
  src/ambiguitychecker.py:1227-1241 — only Words in `allWords` get alternates checked; 2,749
  spellings have an empty primary ("abaisse"). 0 collisions with the phonetic theory today.
- **B22** Collision tests compare raw strokes — src/ambiguitychecker.py:1114, :1142, :1243-1247 —
  collisions are physical (canonical) but raw Strokes are compared. 0 cases today.
- **B23** Non-live hard-rule feature raises `KeyError` — src/featuregroupingsat.py:117 with :128-135
  — a feature in `ALONE_KEYS`/`MUST_DIFFER_GROUPS` that stops being live gives `KeyError` instead of
  a clear error.
- **B24** A solver timeout can lock a non-optimal result — src/featuregroupingsat.py:172, :274, :398
  — FEASIBLE is accepted and locked, so tier score/tie-break are neither proven nor reproducible.
- **B25** The frequency-ratio rule (R4) and the category-priority rule (R6) can form a cycle —
  src/ambiguitychecker.py:224 vs :229 — A<B (R6), B<C (R6), C<A (R4) → order-dependent sort. 0
  cycles among live representatives.
- **B26** Doublet merge checks only the representative's lemma — src/ambiguitychecker.py:321-326 —
  a rarer homograph carrying the reform-pair lemma makes the doublet look like a real ambiguity. 0
  instances.
- **B27** Word identity is fragile — src/word.py:94, :161 — separator-free `_hash` concatenation and
  `__eq__` on `_hash` only: Words from pickles of different processes never compare equal. Root
  cause of B11.
- **B28** `zip` truncation can leave a syllable unregistered — dictionary.py:177 — 99 Words have
  phonetic/orthographic syllable lists of different lengths; a unique extra syllable would make
  `buildPhoneticTheory` (:310) raise `KeyError`. Not triggered.
- **B29** `lexicalPhonemeAmbiguityScore` looks up a word phonology as a syllable name —
  src/grammar.py:913, :931 — `getSyllable("apodiR")` → `None`, the branch adds 0 for polysyllabic
  words. Affects the fallback keymap only.
- **B30** `optimizeOrder` starts from set order — src/grammar.py:307-320 — the best permutation (and
  the phoneme-order tables in `docs/ARCHITECTURE.md`) can change with the hash seed. Fallback
  keymap only.
- **B31** Multiphoneme frequencies are always 0 — src/grammar.py:566, :574-584 — all 353 values are
  0.0; no reader.
- **B32** The layout solver wipes the layout before solving — src/cpsatsolver.py:422 (not run) —
  an infeasible or timed-out part leaves its bank empty and the next `buildPhoneticTheory` raises `IndexError`.
- **B33** `lexique.py` rebuilds on import — lexique.py:1261-1263 — no `__main__` guard: importing it
  overwrites `LexiqueMixte.tsv`. No importers today.
- **B34** `Lexique` keeps its rows in class-level lists — lexique.py:957-958 — a second `Lexique()`
  in one process doubles every row. Not triggered.
- **B35** The sentence exporter's drill-item gate depends on another process —
  util/export_practice_sentences.py:158 — compares against `practice-words.json` from a separate
  disambiguated-theory recompute; changed inputs between the runs reject valid sentences.

### Added at Interactive Triage (2026-09-23)

- **B36** `baux` carries a comma-joined dual lemma (`bail,bau`) — `resources/LexiqueMixte.tsv` —
  a lexicon data defect: the lemma field holds two lemmas, which confuses lemma-based grouping
  (lemma-homophone detection, doublet merge). Verified still present 2026-09-23.
- **B37** `baud` is phoneticized `bo` (missing the final consonant) — `resources/LexiqueMixte.tsv`
  — a pronunciation/sense defect (the fish vs the unit [bod]). Verified still present 2026-09-23.
- **B38** Suspected mistagged-verb "ghost lemmas" — `pars`, `sert`, `bute`, `mar`, `lack`, `fy`,
  `mise`, `vins` — verb forms catalogued as NOM lemmas; they pollute lemma indexes and cross-lemma
  grouping.
- **B41** 182 nouns have no gender in Lexique383 (`maison`, `voiture`, `main`, …) — the trainer's
  Words mode then has no le/la context word for their singular; a lexicon gender fill would fix it.
- **B42** `régnions`/`régnons` are both `ReN§` in the lexicon (no yod on `-ions`) — a false-homophone
  questionnaire pair, still present in `questionnaire.json`/`elicitation_answers.json`; possibly a
  broader `-ions`/`-iez`-after-[N] pattern worth a systematic check.

## Queued follow-ups (from docs refactor)

- **Code renames for "lemma" names that mean lemma + category** (decision a12; no code change
  yet): `LemmaHomophoneGroupKey` (src/elicitation.py:24) → `HomophoneGroupKey`; `groupWordsByLemme`
  (src/word.py:414) → `groupWordsByLemmeGramCat` (`groupWordsByBareLemme` is correctly named).
  Same pattern, also worth renaming: `buildLemmaHomophoneGroups` (src/elicitation.py:61) and
  `buildWordsByOrthoLemme` (src/ambiguitychecker.py:772, keyed by (ortho, `lemmeGramCat`)).
- ~~**No command regenerates `starboard3h.json`**~~ — done (2026-09-23): `python -m
  util.optimize_keyboard` runs the CP-SAT layout solve, seeds from the committed
  `starboard3h.json` and writes `starboard3h_optimized.json` by default (`--output
  starboard3h.json` to replace the seed deliberately).
- **Realization report vs inline path drift** — the trainer keyboard legend reads the tracked
  `realization_report.json`, while the disambiguated theory and the Plover dictionary recompute the
  Discriminating-Feature Stroke Realization (Realization Phase) inline; nothing compares them
  (B18, B19).
- **`.claude/settings.local.json` still allow-lists the old `build_phase_p_realization`
  commands** — user to update to `util.build_realization_report`.
- **Runtime strings still say "Phase G/P"** — ask the user before changing them (it is a code
  change, not a comment edit): print messages and report keys at dictionary.py:537/539,
  src/featuregrouping.py:316/324, src/featuregroupingsat.py:591, util/build_realization_report.py:111/132,
  and the French questionnaire HTML at util/build_questionnaire_page.py:312. Renaming a report key
  changes the tracked `realization_report.json`.

### Added at Interactive Triage (2026-09-23)

- **Regenerate `MARKING_OVERRIDES` from one canonical run** at the 10× threshold — the current
  ~51-pair list was built from a top-10-by-regret cross-check against 30×/100×, not one clean run
  (the spec's §3 "provisional" note).
- **Confirm (not just assume) that bucket 2 and bucket 3 share one physical marking mechanism** —
  implemented that way (`decideStarHashMark` handles both), but the design question was never
  explicitly re-confirmed; caveat now recorded in `docs/specs/star-hash-marking.md` §8.
- **The `-er`/`-ers` noun wishlist** — reuse the `Infinitif`/`Infinitif:p` atomic features instead
  of a generic star/hash mark for a whole NOM/VER homophone sub-class (raised, not sized or
  verified against real data).
- **Done — Integrate the pipeline steps into one orchestrated entrypoint** — `python
  dictionary.py` now runs the four steady-state S2 appenders (`--apply`), the Elicitation,
  Grouping and Realization phases, the disambiguated-theory refresh and every export, rebuilding the
  pickles itself when its appenders appended rows; the manual-`rm` staleness trap is
  intentionally preserved (see `docs/PIPELINE.md` "How to run a full rebuild").
- **No tests for `cpsatsolver.py`'s ambiguity math** — the layout solver's cost model is untested
  (low urgency while the layout is frozen).
- **Housekeeping: merge or delete the `phase-g-grouping` branch** — it long outgrew the Grouping
  Phase and still exists locally and on origin.
- **Trainer: definition search is exact-spelling only** — no accent-insensitive or prefix fallback
  in Definitions mode.
- **Trainer: hyphenated compounds are drilled as two chords** (`celle-ci`, `là-haut`) in sentence
  mode, while Plover would output them as two words.
