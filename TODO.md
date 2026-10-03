# TODO

Written to survive a `/clear` — read this file first in a fresh session.

## Suspected bugs (from docs refactor, 2026-09-22)

Found while writing `docs/PIPELINE.md` (full write-ups, evidence and confidence in
`docs/refactor/callgraph/90-findings.md` — kept in git history once the refactor folder is
removed — same B-numbers). **Not yet reviewed by the user.** Tier 1
changes the Plover dictionary (or other exported output) today; tier 2 changes reports or
tracked artifacts; tier 3 is latent (no measured impact). B39/B40 were dropped: their code
was removed in Dead-Code Removal (Pass 5). B1 was dropped 2026-09-24: every reading of a
spelling is already an alternate press-set on the resolved Word, so the unresolved "twin" Word
only adds a redundant route (269 twins: 133 alone on their stroke, 38 on a resolved stroke, 98
losing a tie, 0 hiding another spelling — B47 later removed those redundant routes). B2, B4,
B11, B14, B27, B43, B44, B45, B46 and B47 have since been fixed.

### Tier 1 — affects the Plover output today

- **B47** RESOLVED 2026-09-25 (`findSpellingTwinWords`, src/ambiguitychecker.py:785, dropped by
  `Dictionary.buildDisambiguatedTheory` at dictionary.py:426): the residual bare entry belonged
  to a spelling twin — another Word with the same ortho, `lemmeGramCat` and canonical base
  stroke as the one `_resolveEntryWord` picked for the spelling's resolved press-set entry
  (`affadis` participe m. pl. beside `affadis` indicatif passé 2e sg.). The press-set's
  alternates already realize every reading of the spelling on the resolved Word (the entry's
  parallel "readings" field), but `buildFinalInducedStrokes` still gave the twin its own bare
  primary stroke, since it iterates every theory Word and the twin is in no keypress group.
  The fix drops the 272 twin Words (259 spellings) from the disambiguated theory entirely:
  disambiguated_theory.tsv −272 rows (`affadis` keeps only `a/kpa/pvi/-s` and `a/kpa/pvi/-dt`),
  same-lemma residual collisions 104 → 6 (the six survivors are the `-eter`/`-eler` variant
  conjugations `caquette`/`caquète`…, the spelling-variant follow-up), cross-lemma 0, reform
  doublet 0. Plover: −130 stenos (the twins' phantom bare/star-marked chords), 0 added, 0 owner
  changes, 0 spellings lost (each spelling stays reachable through its resolved Word's
  entries). Trainer: definitions.json −272 stray rows (`affadis` now shows each reading on its
  own chord only); practice-words/practice-sentences unchanged (the phantom chords were outside
  the top-10,000 drill set). In a star/hash cluster a twin even consumed a */# slot for a
  spelling already reachable through its feature strokes — those 138 marked phantoms are gone
  too. Before/after in `scratch/b47-before/`. Original entry: Same-lemma disambiguation leaves a
  residual BARE entry for readings that already have a feature stroke — e.g. `affadir_VER`: the
  disambiguated theory (disambiguated_theory.tsv) held THREE `affadis` rows on the same base
  stroke `a/kpa/pvi`: `a/kpa/pvi` + extraStrokes `17` (participe passé m. pl., realized as the
  `-s` suffix), `a/kpa/pvi` + extraStrokes `19,20` (realized as the `-dt` suffix), and
  `a/kpa/pvi` with EMPTY extraStrokes — a residual unmarked entry for the indicatif passé 2e sg.
  reading, shadowed by `affadi` (which owns the bare chord: `a/kpa/pvi` → `affadi` in
  plover_stenalgo_dictionary.json; `affadis`'s real entries are `a/kpa/pvi/-dt` and
  `a/kpa/pvi/-s`). Expected behavior: once the Realization Phase assigns a reading its
  feature-discriminating stroke, that reading should have NO other entry — the bare placement
  belongs to the group's default reading only. The stray row was invisible in Plover (the
  exporter's entry resolution dropped it) but surfaced in the trainer Definitions page
  (export_definitions iterates the phonetic-theory homophone group), where `affadis` showed as
  "indicatif passé, 2e sg." on BOTH the bare chord and the `-dt` chord.
- **B44** RESOLVED 2026-09-24 (`composeReservedKeyStrokesForEntries`, src/ambiguitychecker.py:424:
  Different-Lemma or Grammatical-Category Disambiguation (S7) now clusters and marks every entry,
  primary and alternate, on its own final stroke; `panse` → `p*@s`, `p*@s/-k`, `p*@s/-R`). Plover:
  +183 stenos, 0 removed, 50 spellings newly reachable (`subits`, `amplis`, `garanties`, `buttent`…),
  none lost; 5 stenos change owner (`ksa/R@/ti/-s` `garantis` → `garanties`, the VER reading moving
  to `ksa/R@/t*i/-s`). Why no tool flagged it: the Realization Phase files these under
  "cross-lemma collisions (out of scope — */# track's job)", S7 never re-checked the final strokes,
  and `export_plover_dictionary` printed its 14,739 "same-steno collisions" as expected, lumping
  same-stroke homographs with real collisions. New final check `findFinalCollisions`: `python -m
  util.build_disambiguated_theory` (so `python dictionary.py`) exits 1 on any cross-lemma collision
  (191 before the fix, 0 after); it reports, without failing, 104 same-lemma residuals and 28
  reform-doublet (R2) collisions. Of the 104, 98 are an unresolved synthetic twin Word on its
  unmarked base stroke (`agis` ind:pas:2s, freq 0, beside `agi` on `a/vti`) — harmless while the
  twin is the rarer, since the attested Word reaches the spelling — and 6 make spellings unreachable
  (`caquette`/`caquète`, `dételle`/`détèle`, `nivelle`/`nivèle`… `-eter`/`-eler` variant
  conjugations of one lemma, for the spelling-variant follow-up); the 28 R2 collisions all hide a
  variant spelling on purpose. Probes: `scratch/b44_collisions.py`, `scratch/b44_residuals.py`;
  pre-fix outputs in `scratch/b44-before/`, diff in `scratch/b44-plover-diff.txt`. The 9 B45
  participles (`promis` → `promises`) and the variant spellings were separate causes of the old
  list: the B45 ones are gone since the B45 fix (probe rerun 2026-09-24); re-check the variant
  spellings after the spelling-variant removal.
- **B45** RESOLVED 2026-09-24 (`spliceParticiplePhon`, src/verbparadigm.py:326, now adds the
  consonant of a consonant-final feminine stem for a feminine slot and drops it for a masculine
  one, `feminineParticipleConsonant` :306; util/completeVerbParadigms.py prefers a same-gender
  donor; `util/fixParticipleGenderPhon.py --apply` added the consonant to 45 feminine rows
  (`découverte`, `cuite`, `feinte`, `jointe`, `méprise`…), dropped it from 17 masculine plurals
  and deleted 17 synthetic rows duplicating an attested one (`promis` m_s, stale since e3b0358)).
  Backtest over 22,168 attested cross-gender pairs: 96.7% → 99.5% exact phon, no regression.
  Rebuild: S2 appended 82 rows (`recuire`, `romancer`, `introduire`), Plover +60 entries
  (`enclos` `@/kmtae` / `enclose` `@/kmtaenl`; `promis` loses its star-marked stroke), no
  spelling lost; clusters 6,703 → 6,707, overflow 8.32% unchanged. Before/after in
  `scratch/b45-before/`, `scratch/b45-plover-diff.txt`. Original entry: synthetic past
  participles copied another gender's phonology — 33 masculine rows carried the feminine's `/z/`
  (`enclos` `@kloz` outranked `enclose` on `@/kmtaenl`), and feminine rows lacked it.
- **B46** RESOLVED 2026-09-25 (`_padSilentUnits`, src/verbparadigm.py, applied by
  `generateMissingParticiple`: appends one silent trailing `_#` per orthographic unit the phonemic
  breakdown is short of, matching the attested convention — `garnis` `g_a_R|n_i_#` beside
  `g_a_r|n_i_s`; `util/fixParticipleSilentUnits.py --apply` repaired the 4,920 existing synthetic
  rows in place — 4,829 one unit short, 91 two (the silent `h` of `inhumées` is its own ortho
  unit), 294 already aligned, 0 errors). Measured at last: the missing `#` never changed any
  stroke — after `rm -f *.pickle` + a full `python dictionary.py` rebuild (S2 converged, 0 rows
  appended), all 10 tracked outputs are byte-identical to the pre-change baseline
  (`scratch/b46-before-md5s.txt`); the fix only makes the rows usable by unit-aligned readers
  (deriveSyllableSplitTable, deriveMidVowelTable, `normalizeSplicedBreakdown`'s boundary copy).
  Original entry: synthetic `discriminées` `…m_i|n_e` / `…m_i|n_é_es`, attested `aimées`
  `E|m_e_#` / `ai|m_é_es`; 4,910 of 5,227 synthetic participle rows, predating the B2 fix.
- **B2** RESOLVED 2026-09-24 (`normalizeSplicedBreakdown`, src/verbparadigm.py:589, applied by
  `generateMissingConjugatedForm`: re-places every syllable boundary from a split table learned from
  the corpus Words, vocalizes a word-final glide after a consonant, and sets mid vowels from their
  spelling; `util/fixSplicedVerbBreakdowns.py --apply` corrected the 14,926 rows spliced before). A
  backtest regenerating the 13,461 attested finite forms the generator can rebuild went from 83.5% to
  98.0% exact on phon/`syll_cv`/`orthosyll_cv` (residue: Lexique's own `e`/`E`, `u`/`w` variation).
  Rebuild: 3,587 spellings got a shorter shortest stroke (none longer), S2 added 167 `sub:pre:3p` rows,
  lemma-homophone clusters 6,552 → 6,703, overflow 8.03% → 8.32%. 64 Plover spellings were reachable
  only through their wrong extra stroke and now lose to a real homophone (`buttent` → `butent`,
  `caquette` → `caquète`): B44 (unmarked feature strokes) and the spelling-variant follow-up. Original
  entry: Synthetic verb forms get a vowel-less trailing syllable — src/verbparadigm.py:561, :611 —
  radical cut by character count keeps the infinitive's syllable boundary (`cannes` sub:pre:2s: 2
  strokes vs NOM 1). 3,843 new Words carry an extra stroke and miss their real homophones.
  The cut also keeps the infinitive's vowel quality: `abonne` sub:pre is `abon` `a|b_o|n_#` (closed
  `o` from `abone`, trailing onset-only `n`) → `a/svae/mR-`, vs the attested `abOn` → `a/sven`.
- **B3** Breakdown built from a LexiqueInfra association that disagrees with the phonology —
  lexique.py:1021, :1033 (with :770-883) — match uses Infra `phono`, `syll_cv` comes from `assoc`
  (`embêter` typed with closed `e`). 132 mixed-lexicon rows; 175 VER synthetic rows inherit it.
- **B4** RESOLVED 2026-09-24 with B44 (alternate entries now carry their own star/hash mark; `subits`
  is reachable as `s@i/sv*i/-s`). Original entry: alternate entries of self-homographs take
  unrelated words' only stroke — src/ambiguitychecker.py:1288 (`buildExtraInducedStrokes`),
  dictionary.py:389 — alternate entry strokes skip the star/hash marks (`subits` loses to `subis`).
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

- **B11** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). The realization report is identical under seeds 0, 1 and unset (37 cross-category, 1,326 cross-lemma). Original entry: Residual-collision lists in the realization report change between clean rebuilds —
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
- **B43** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). The S2.1 dry run now confirms 0 rows under seeds 0, 1 and unset. Kept for the record; the order-insensitive feature-set key / receiving-group restriction below remain optional cleanups. Original entry: The S2.1 appender's "confirmed to cause a new discriminator collision" gating is
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
- **B27** RESOLVED 2026-09-24 (`Word._hash` is now a blake2b digest of `Word.identity()`, `__eq__` compares the identity fields; a clean unpinned `python dictionary.py` rebuild is byte-identical to a `PYTHONHASHSEED=0` one on all 11 tracked outputs). Word identity is fragile — src/word.py:94, :161 — separator-free `_hash` concatenation and
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
- **DONE (2026-09-25): Remove spelling variants from the lexicon** — `resources/spellingVariants.tsv`
  (422 sets: 374 active / 48 veto, human-reviewed against Google Books Ngram 2010–2019 counts in
  `resources/LexiqueGoogleNgram.tsv`) is enforced by `src/spellingvariants.py` at Lexicon Building
  (S1) and the `dictionary.py` load choke point; `util/prune_spelling_variants.py` keeps
  `LexiqueSynthetic.tsv` clean. The canonical may sit on either side of a reform pair (the
  reconcile-back rule), and a dropped spelling that coincides with a conjugated form of a kept verb
  (`boite`/`boiter`, `fritte`/`fritter`) is exempt unless its lemme carries the set's canonical
  (`absout`/`absoudre` drops). Rebuild verified: reform doublets (R2) 28 → 0, cross-lemma 0 → 0.
  Follow-ups: (a) R2/doublet machinery (`doubletPairs`, the reform-doublet exemption in S7) now has
  nothing to handle and can be removed; (b) neologism patch from a future
  `LexiqueGoogleNgramAdditions.tsv` (`python -m util.ngram_data extract-additions`, calibrate the
  threshold on the distribution first); (c) RESOLVED 2026-09-25 (`util/fixRectifiedEConjugations.py`,
  working tree): the 6 residual same-lemma collisions after B47 were the `-eter`/`-eler`
  variant-conjugation doublets — attested rectified forms (`caquète` ind.) beside synthetic
  traditional-doubling subjonctif/future rows (`caquette` subj) from Verbiste's `j:eter`/
  `app:eler` templates; the subjonctif-vs-indicatif cross-spelling opposition was never asked,
  so the Elicitation Phase skipped the whole group and NO reading got a feature stroke. Fix:
  the script remapped the 49 verbs whose LexiqueMixte forms attest the `è` convention
  (caqueter, atteler, renouveler, étiqueter…; only the appeler/jeter family keeps doubling)
  to `ach:eter`/`p:eler` in `resources/verbiste/verbs-fr.xml` and pruned the 330 doubled
  LexiqueSynthetic.tsv rows; S2 regenerated 507 rows with rectified spellings (converged in
  3 rounds). Final-stroke collisions now 0/0/0 (cross-lemma / same-lemma / reform doublet),
  resolved press-set groups 47,838 → 47,911, subjonctif readings live as same-spelling
  alternates (B47 machinery). Plover: +489/−261 stenos, 57 owner changes; the 240 lost
  spellings are ALL doubled spellings (wrong convention per their verb's own lexicon) — 171
  have their `è` counterpart reachable, 69 rare readings (2s futures, 3p forms of ~25
  freq-0 verbs) are unwritable until their regenerated row passes the S2 collision gate.
  Before/after in `scratch/b48-before/`, rebuild log `scratch/b48-rebuild.log`.
- **Audit the 2% of attested finite verb forms the B2 generator does not reproduce** —
  GENERATOR SIDE RESOLVED 2026-09-25 (non-final-syllable vowel laxing in
  `normalizeSplicedBreakdown`/`deriveMidVowelTable`/`_midVowelContexts`, src/verbparadigm.py: the
  new `nonfinal-closed`/`nonfinal-open` contexts are learned and applied after the boundary
  re-placement, only the coarse `e`/`o` units are rewritten — a committed `°`/`E`/`O`/`2`/`9` never
  changes (`devriez` keeps its schwa, `bottèlent` its `O`) — and in the learning the coarse
  counterpart of a lax winner abstains, as do non-mid nuclei like `wa`; the existing 26 rules were
  unchanged, 26 added; `util/fixSplicedVerbBreakdowns.py --apply` corrected the 531 stored synthetic
  rows). Backtest 13,007 → 13,027 exact of 13,269: the `ai`/`ei`/`aî`/`ê`→`E` classes and the
  closed-syllable `e`→`E`/`o`→`O` ones are gone (`affaiblira`, `vieillira`, `fraîchira`,
  `portâtes`); the new `E`→`e`/`O`→`o` entries (66) are the generator being finer than coarse
  attested rows (`aigrirent`), not regressions. Residue, classified per the audit's rule:
  plain-`e` non-final-open (96, `aguerrira` /ɛ/ vs `descend` /e/) is undecidable from spelling or
  the coarse infinitive — a within-lemma lexicon inconsistency, fix-script material (upgrade coarse
  infinitive vowels from the lemma's own committed finite rows); `o` non-final-open (24,
  `délogera` O vs `posera` o) is LexiqueInfra-internal inconsistency — no rule learnable at 89.5%
  share; `u`↔`w` (18) splits within lemmas (`évanouir` w vs `réjouir` u) — lexicon errors;
  `°`↔`E` (6, `jetterez`) needs rewriting a committed schwa in doubling stems — left open;
  `2`/`9`/`°` (≈10), the dropped `n` (5, `enorgueillir`), the malformed `ij#` (3,
  `oublierions`), and the boundary/1-offs stay as noise or small splice bugs. Rebuild verified:
  S2 converged appending 0 rows; final collisions 0/0/0; phonetic theory 446 spellings' stroke
  sets changed, none shorter/longer/gone/new; Plover 167,719 → 167,708 (−478/+467, 6 re-pointed),
  0 spellings lost or gained; definitions.json regrouped (−4 net), practice-words 3,784 rows carry
  the corrected chords, practice-sentences and keyboard-layout byte-identical; lemma-homophone
  clusters 6,551 → 6,555, overflow 8.32% → 8.31%. Before/after `scratch/b2r-before/`, rebuild log
  `scratch/b2r-rebuild.log`, ambiguity log `scratch/b2r-ambiguity.log`, classifier
  `scratch/b2_audit.py`. Follow-ups: the coarse-infinitive vowel upgrade script and the `u`↔`w`
  normalization script (both lexicon halves, like the other `fix*` scripts).
- **Close the B2 residue the audit classified but left open** — the continuation of the entry above,
  now that the generator side is done:
  - the plain-`e` non-final rows — DOUBLED-CONSONANT RULE DONE 2026-09-25 (NON_FINAL_DOUBLED in
    src/verbparadigm.py, learned and applied like the other non-final contexts): a coarse `e`
    before a doubled consonant letter in any syllable but the word's first laxes to E (`aguerrir`
    rr, `assujettir` tt, `pressentir` ss; 38 rows fixed, 0 flipped; backtest 13,027 -> 13,065 of
    13,269; `fixSplicedVerbBreakdowns --apply` corrected 142 more stored rows). The first syllable
    is excluded because the prefix vowels keep their quality there (`dessécher` /deseSe/,
    `effacer` /efase/ — 120 rows), and `sc` is not a doubled `s` because `descendre` attests
    /des@d/ (86 rows). Both widenings of the rule were tested 2026-09-25 and REVERTED: treating
    `sc` as a doubled `s` (flips `descendre`'s 86 correct rows), and admitting the word's first
    syllable for `pressentiez`/`tressaillez` (first-syllable cases, not a detector gap — the
    widened detector changed nothing else on the corpus). Residue, all lexicon-side (per-lemma
    coarse infinitive vs committed finite forms — the upgrade script): `condescendre`/`redescendre` attest E before `sc` (27 rows,
    `k§dEs@`, `R°dEs@`) though `descendre` attests `e`; `essuyer` (`Es8ija`), `blettir`
    (`blEtisE`), `pressentir` (`pREs@tje`) and `tressaillir` (`tREsaje`) attest E from the word's
    first syllable (16 rows). The 12 `élever` rows (`El°va`) are NOT generator gaps: `é` is a
    one-phoneme grapheme (/e/), so the attested E rows are lexicon errors to correct in the
    attested rows, not in the generator. Same heuristic may still unlock the 6 `jetterez` rows
    (the doubled-consonant stem marks the E the committed `°` hides — would need rewriting a
    committed schwa, left open).
  - `u`↔`w` — DONE 2026-09-26 (`util/fixOuGlideConsistency.py --apply`): the 25 lemmas whose
    `ou`+vowel rows split between hiatus /u/ and glide /w/ (`jouez` Z_u|e beside `jouer` Z_w_e,
    `évanouir` 18 u / 17 w, `réjouirai`, `relouer`, `touareg`…) are normalized to /w/ with the
    syllable merge, in all four files (Lexique383 phon/syll/nbsyll/cv-cv/p_cvcv/phonrenv, Infra
    phono/assoc/regTo_GP, Mixte and Synthetic phon/syll_cv/orthosyll_cv): 36 Mixte + 19 Synthetic
    rows. `python lexique.py` regenerates exactly the 36 patched Mixte rows. Uniformly-/u/ lemmas
    (`hindouisme`, `louisianais`, `ouïgour`) and the obstruent+liquid hiatus lemmas (`trouer`,
    `clouer`, /u/ is correct there) are untouched. Rebuild: S2 converged after appending 71 rows
    (3 rounds; the changed strokes moved the collision gate: the whole `sidérer` paradigm (33)
    plus one gap each in 35 hiatus/participle lemmas: `clouer`, `strier`, `suppléer`,
    `individué`, `mosaïqué`…); final collisions 0/0/0; Plover 167,708 → 167,768 (−55/+115
    stenos), 0 spellings lost, 27 gained (23 `sidérer` forms, `individué(es)`, `mosaïqué(es)`);
    keyboard-layout.json identical; 639 tests pass. Before/after `scratch/uw-before/`, log
    `scratch/uw-rebuild.log`.
  - the splice bugs behind the malformed `u#`/`ij#` units — FIXED 2026-09-26 (generator guard +
    `util/fixMalformedSyntheticSplices.py --apply`): the endings are mined by string length, so an
    -ouer/-uer/-éer verb spliced with the -ier donors of `étudi:er` lost its R in the cnd forms
    (`clouerions` `kluj§`) and left an empty/fused unit (`cloue` `k_l_u#`). `repairSpliceUnits`
    turns empty and fused units into a sounded unit + `#`; `isWellFormedSplice` (no empty unit,
    phon == sounded join up to mid vowels) makes `generateMissingConjugatedForm` skip a bad slot;
    the script repaired 281 stored rows (58 phon R restored, 36 lost `n` unit reinserted for
    `enorgueillir`/`enivrer` via `reinsertLostNasalUnit`) and deleted 49. Rebuild: collisions
    0/0/0, Plover 167,768 → 167,747 (34 spellings lost, 13 gained); 649 tests pass. OPEN: the 34
    lost spellings are the cnd `-ierions`/`-ieriez` forms of 15 -ier verbs (`trier`, `crier`,
    `plier`…; the donor ending gives `ij#|R_j_` / phon `jj` — needs a glide-aware ending class,
    e.g. splitting `étudi:er` by infinitive tail), `oublieriez`/`publieriez`, and the
    `désennuie(nt)` forms (unit-count rule vs the `ui` ortho unit); 9 loanword/noun rows
    (`games`, `kreutzers`, `miladys`, `sweepstakes`, `updates`, `molle(s)`, `interviewée(s)`)
    still fail the guard, made by another generator. `enorgueillir`'s dropped `n` is fixed
    (reinserted); `interviewer` stays deleted (its Mixte source is inconsistent).
  - the 34 lost `-ierions`/`-ieriez` spellings — FIXED 2026-09-26 (`endingTemplateKey`,
    src/verbparadigm.py): the ending tables are keyed by template plus the glide class of the
    infinitive (`#ij` when the phon ends `ije`: `crier`, `trier`, `plier`, `oublier`, and the
    `-iller` verbs), so those verbs no longer splice the `étudier` (`d_j_e`) endings; `crierions`
    `k_R_i_#|R_j_§`. Rebuild: S2 converged after 2 rounds appending 2,560 rows (34 back plus the
    full paradigms of ~85 `-iller` verbs, `tiller`… ~30 rows each, previously blocked by the
    well-formedness guard); collisions 0/0/0; Plover 167,747 → 170,098 strokes, 0 spellings
    lost, 1,900 gained; 649 tests pass. Before-state `scratch/ier-before/`, logs
    `scratch/ier-rebuild.log`, `scratch/ier-full.log`. Still open: 9 loanword/noun rows made by
    another generator.
  - the plain-`e` first-syllable residue — DONE 2026-09-26 (`util/fixFirstSyllableE.py --apply`, user-validated
    lemma list): the harmonisation vocalique is ignored (docs/ARCHITECTURE.md decision 6), so every
    form of `essayer`, `essuyer`, `descendre`, `effacer`, `dessiner`, `voir` (`verrons`), `nerver`,
    `dessaper` (`dEsape`, syllable added)… gets `E`; `re-` prefix verbs keep their schwa (`restructurer`
    untouched, `redescendre` `R°dEs@dR`). 586 Mixte + 392 Synthetic rows (Lexique383 577, Infra 603;
    `python lexique.py` regenerates the same Mixte). Rebuild: S2 converged, collisions 0/0/0, Plover
    170,098 → 170,156, 3 spellings lost (`dessoula`, `dessoulais`, `dessoulez`: rare variant-spelling
    rows of `dessouler` the regeneration no longer carries, not regenerated by S2's gate), 0 gained
    spellings. Before-state `scratch/fse-before/`, log `scratch/fse-rebuild.log`. OPEN: the generator's
    first-syllable exclusion in NON_FINAL_DOUBLED now contradicts the corpus (first-syllable `E`
    everywhere) — revisit, and the coarse-infinitive upgrade script is no longer needed for this set.
  - `python lexique.py` stopped reproducing the committed LexiqueMixte.tsv after 0b5eace (found
    and FIXED 2026-09-26): the 49 verbs remapped to `ach:eter`/`p:eler` dropped out of
    `loadElerEterQualifyingVerbs`, so reform rule 5 no longer regularized their Lexique383
    doubled rows (56 rows reverted, `amoncèle` → `amoncelle`). The loader now also accepts those
    two templates (the rewrite only fires on a still-doubled prefix, so regular è verbs are
    untouched); a regeneration is byte-identical to the committed Mixte again.
  - accepted noise, no action: `o` non-final-open (Infra contradicts itself, `posera` `o` vs
    `délogera` `O`), `2`/`9`/`°` variation (~10 rows), the boundary 1-offs.
- **Vowel-harmony standardization, batch 2** — the read-only report (`python -m util.reportVowelHarmony`)
  found 687 within-lemma E/e, O/o, 9/2 disagreements in 663 lemmas; the classified findings, the ~12
  genuine-harmony lemmas (`-ologique`, `coronarien`, `monopoliser`…), the ~40 loi-de-position `-onner`
  verbs awaiting a decision, and the plan are in `docs/VOWEL_HARMONY_CANDIDATES.md`. Follows the first
  batch (`util/fixFirstSyllableE.py`, docs/ARCHITECTURE.md decision 6).
  - Batch 2, family 2 APPLIED 2026-09-26 (`util/fixHarmonyVowels.py --apply`; lemma table checked on
    fr.wiktionary): `O` for `cosmologique`, `radiologique`, `radioscopique`, `étiologique`,
    `troglodytique`, `coronarien`, `ovoïdal`, `philosophal`, `cochonnée`, `corroborer`, `lobotomiser`,
    `monopoliser`, `autographier`; `o` for `rototo`; word-final open vowels (`ovoïdaux`) untouched.
    34 Mixte + 21 Synthetic rows. Rebuild: collisions 0/0/0, 649 tests, Plover 170,156 → 170,321 (0
    spellings lost, +165 gained: S2 appended 164 rows, 156 ADJ — the -ique adjectives' plural/gender
    forms now agree with their exemplars). Before-state `scratch/harm-before/`. Families 1 (~40
    `-onner` loi-de-position verbs) and 3 (suffix-driven pairs) DECIDED 2026-09-26: left as is (real
    positional/suffix alternations). Only the `mixed` rows remain open.
  - The generator's first-syllable exclusion of NON_FINAL_DOUBLED — TESTED AND KEPT 2026-09-26: dropping
    the `any(boundary <= nucleus …)` condition in `_midVowelContexts` (so a first-syllable `e` before a
    doubled consonant laxes too) is a net wash on the backtest (14,376 -> 14,375 of 14,529 exact): the
    `condescend` 23 `e`/`E` rows become 11 `°`/`E`, 18 new `enquête`/`enterre` `e`/`E` misses appear (`e`
    that stays tense before `rr`/`tt` in non-prefix first syllables), 1 `celait` regression. Now that
    `util/fixFirstSyllableE.py` put `E` in the infinitives themselves, the rule has nothing left to add;
    reverted. The `jetterez` 6 rows stay open.
  - Batch 3, the `mixed` rows APPLIED 2026-09-26 (`util/fixMixedHarmonyVowels.py --apply`, targets in
    `util/harmonyVowelTargets.tsv`, candidates by `util/buildMixedHarmonyCandidates.py`, all validated by
    hand against fr.wiktionary, see docs/VOWEL_HARMONY_CANDIDATES.md): `E` before a doubled consonant
    or `sc`, `O`/`o`/`e` per Wiktionary; left alone: the masculine `-o(t)` / feminine `-Ot(te)` pairs,
    `boeuf`/`oeuf`, and the 49 `-oter`/`-onner`/... verbs that only flatten the loi de position
    (`greloter`, `flotter`, `adorer`, `téléphoner`…; `cloner`, `diplômer` stay flattened to `o`);
    `professeur` is `O` in all its forms (homophones). 282 Mixte + 42 Synthetic rows. `lexique.py` learns
    `oo-OO` (coopter); Lexique383 gives `professeur`/`professeurs` genre `m` (it was blank, so the reading
    "s" was a subset of `professeure` "f s" and no press-set group formed). Rebuild: S2 converged, collisions
    0/0/0, 649 tests, Plover 170,321 -> 171,586 strokes, 0 spellings lost, 1,253 gained (S2 regenerated
    forms once the strokes moved). Before-state `scratch/mh-before/`, log `scratch/mh-rebuild4.log`.
    OPEN: `chopper` (no pronunciation); 30 other NOM lemmas have a blank-genre row beside a feminine one
    (`amateur`, `architecte`, `malade`…), not audited; `agressions` NOM row lost its merge with the
    `agresser` VER row (harmless).
- **Pluvier-style TAO prefix/suffix shortcut scan** — go through Pluvier's dictionary rules
  (docs/PRIOR_ART.md; the TAO strokes that emit a whole multi-syllable prefix or suffix from
  one special keystroke), and for each rule measure the payoff in OUR lexicon: the sum of
  word frequencies of Words whose current stroke sequence would be shortened by having that
  shortcut stroke (a positively-affected word is one whose orthography starts/ends with the
  rule's target affix and whose stroke count would drop). Store the scored rules in
  descending order of usefulness in a tracked scratch file (e.g.
  `scratch/pluvier-affix-shortcuts.tsv`) for later human evaluation — do NOT wire any of
  them into the theory; this is measurement only.
- ~~**Resyllabify 5 wrong `-ption` lemmas**~~ — DONE 2026-09-29 (`lexique.py` `fix_p_sj`; Mixte 5 rows, Plover 5 entries, trainer definitions regrouped). Also DONE 2026-09-29: the 5 `-ction` lemmas with an x (`exaction(s)`, `extinction`, `extraction(s)`) — `fix_x_k_s` wrongly moved the k of `-ction` into the last syllable; `-xion`/`-xtion` (genuine x = ks) deliberately left as `ksj§`. Still open: check the `-th` stray anchor. Original note: — `resources/LexiqueMixte.tsv` (source: Lexique383
  syllable columns) — `absorption`, `absorptions`, `réabsorption`, `résorption`, `résorptions`
  are split `…R|p_s_j_§` (the `p` in the onset of the last syllable, phono `psj§`, ortho `ption`).
  Every other `-ption` word (adoption, exception, acception, assomption, exemption, rédemption,
  circonscription, …) is split `p|s_j_§` (`p` in the coda of the previous syllable, last syllable
  `sj§`/`tion`). The five are wrong: they create a stray `psj§ ption` suffix anchor (5 carriers,
  freq 0.6) in the affix scan that can never fuse with `tion`. Fix the split, then rebuild per
  `docs/PIPELINE.md` ("Recomputing after a fix", lexicon change → `rm -f *.pickle`). Afterwards
  check whether other stray anchors (`ction` `ksj§`, 5 carriers; `-th`) are the same kind of
  syllabification artefact. Found 2026-09-29 while comparing affix rules to OQLF/TAO.

- **`ra`-spelled prefix syllables with an `Re` phonology (lexicon, to investigate).** Found 2026-09-30 while
  analysing rank 17 (`ra|rai|raie|re|rhé|ré|réh`, `Re` phonology) of the affix sweep. Besides `ré`, its parts are:
  `rai` (raidir, rainer, rainure(s), rainurer, rainurés; `ai` = é is plausible), `raie` (raiera, raierai, raierais,
  raieras, raierions, raieront), `rhé` (rhétorique, rhésus, rhéostat…) and `ra` carried by a single word,
  `rayâmes` (orthographic syllable `ra` pronounced `Re`, which should not be possible for a syllable spelled `ra`: look
  at its phonology / orthosyll in `Lexique383.tsv` / `LexiqueInfraCorrespondance.tsv`, probably the `ra|yâmes`
  split of `rayer` forms). Decision (user, 2026-09-30): `re` (`R°`) and `ré` (`Re`) stay separate rules, no
  phonology-class merge. Check also the `raie`/`rayer` family for the same split, then rebuild per `docs/PIPELINE.md`.

- **Affix pipeline integration (2026-10-01): DONE and committed on `affix-abbreviation-rules`.** Stage Affix Abbreviation Building (S9) per `docs/history/PLAN_2026-10-01-affix-pipeline-implementation.md` (decisions file, S9a/S9b, self-looping interactive review, per-rule cache; docs in `docs/AFFIX_RULES.md` and `docs/AFFIX_DESIGN.md`); a full rebuild from nothing is byte-identical. Open: the trainer integration (separate branch, plan decision 6); the `ra`/`Re` phonology items above; re-review of the verdicts when the lexicon changes (pending items are listed by `util.build_affix_rules`).

- **DONE (2026-10-02): Affix abbreviations carry the conjugation markings.** Records now keep every route of a Word in the disambiguated
  theory (`WordRecord.routes`) and `src/affixabbrev.py` abbreviates each route with its own marks and trailing feature strokes:
  79,715 abbreviations (the 72,204 earlier ones unchanged, plus 7,511 for the other routes; TSV column `route`). The marks (keys 10/15)
  never overlap a keypress; S9a output byte-identical. Not covered: a Word whose primary route has no free abbreviation can still
  get one for another route (by design, each route is settled on its own).

- **Plan a conjugation-engine plugin for Plover (2026-10-02, to plan, not to build yet).** Goal: for all homophones of a word
  stenogram (the outline without conjugation marking) keep ONE entry in the theory, with a reference to a conjugation table
  listing the possible conjugation strokes and endings, so the static dictionary no longer needs one entry per marked form.
  The plan should cover: the table format (shared paradigm data, see [[dual-target architecture]] note: Plover static dict +
  Javelin-style runtime engine), the plugin type (Plover extension / meta or command plugin vs a dictionary-replacing
  engine), how marker strokes resolve to a form at runtime, interaction with the affix layer (S9) and the `*`/`#` homophone
  marks, undo behaviour, and what the Plover dictionary export keeps as a static fallback. Output: a `PLAN_<date>-...md` in
  `docs/history/` or `docs/`.
