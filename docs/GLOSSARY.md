# Glossary

Canonical vocabulary for Stenalgo's code and docs, companion to [PIPELINE.md](PIPELINE.md).
When an entry names a **preferred synonym**, use the preferred word in new code, comments
and docs; the other entry is kept only so older prose (commit messages, RESUME notes,
planning docs) stays readable.

Each entry gives a plain definition, a code anchor, preferred/avoid notes where relevant,
and the pipeline stage where the term first matters. Stages and phases are always cited by
descriptive name with the code in parentheses, for example "Discriminating-Feature Grouping
(Grouping Phase)". The terminology was settled in the Glossary Review (Pass 1d) of the docs
refactor (decision log in git history: `docs/refactor/DECISIONS.md`, ids a1-a12 and b1-b9).

## Legacy names

Older prose (the RESUME/NOTES/PLAN session notes and ROADMAP history, the docs-refactor
decision log and callgraph drafts, and commit messages — all only in git history) uses letter
phase codes, older stage names and older terms. They map as follows.

| Legacy name | Current name |
|---|---|
| Phase E, Marker Elicitation | Discriminating-Feature Elicitation (Elicitation Phase) |
| Phase G, Marker Grouping | Discriminating-Feature Grouping (Grouping Phase) |
| Phase P, Marker Stroke Realization | Discriminating-Feature Stroke Realization (Realization Phase) |
| Same-lemma homophones track, Same-Lemma Disambiguation (S3) | Same-Lemma and Grammatical-Category Disambiguation (S6) |
| Lemma-homophones track, the `*`/`#` track, Lemma-Homophone Marking (S4) | Different-Lemma or Grammatical-Category Disambiguation (S7) |
| Synthetic Paradigm Completion (S1b) | Synthetic Lexicon Building (S2) |
| Theory Export (S5) | Theory Export (S8) |
| Phase 0 | the older ambiguity-report diagnostic (`src/ambiguitychecker.py` `__main__`) |
| marker, atom, discriminator (a grammatical value) | **Atomic feature** / **Feature** |
| press-set, signature (what is pressed) | **Discriminating feature set** |
| signature (`GroupSignature`) | **Homophone group set of feature sets** |
| cluster | **Homophone Group**, **Theory-1 collision** or **Lemma-homophone group** (see Cluster) |
| reading | **Feature Combination** |
| keypress (the abstract unit) | **Keypress Group** |
| chord | **Stroke** (see Chord for the other senses) |
| mark, marker (for `*`/`#`) | **star/hash mark**, **star/hash code** |
| marker stroke, Phase P stroke, coda extra stroke, trailing stroke | **Feature discriminating stroke** |
| bare mark stroke | **\*/# marker stroke** |
| 10x rule, frequency-ratio exemption | **frequency-ratio rule (R4)** |
| in-scope collision | **Same-lemmeGramCat collision** |

### Renamed files

The files and identifiers carrying the letter codes were renamed in commit df71a24. Commit
messages before it keep the old names.

| Old path | New path |
|---|---|
| `src/phaseg.py` | `src/featuregrouping.py` |
| `src/phasegsat.py` | `src/featuregroupingsat.py` |
| `src/test/phaseg_test.py` | `src/test/featuregrouping_test.py` |
| `src/test/phasegsat_test.py` | `src/test/featuregroupingsat_test.py` |
| `util/build_phase_g_assignment.py` | `util/build_keypress_groups.py` |
| `util/build_phase_p_realization.py` | `util/build_realization_report.py` |
| `phase_g_keypress_assignment.json` | `keypress_groups.json` |
| `phase_p_keypress_realization.json` | `realization_report.json` |
| `runPhaseG` (identifier) | `runFeatureGrouping` (both since removed — the greedy path is gone) |
| `PhaseGResult` (identifier) | `FeatureGroupingResult` (both since removed) |

---

### \*/# marker stroke
An extra stroke that holds only the reserved star/hash keys (rendered `*#`). Only escalated
star/hash codes produce one, for their second and later symbols; the first symbol is always
merged into the last phoneme stroke. One of the two kinds of extra stroke.
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:444; util/_stenorender.py:43-44.
- Avoid "bare mark stroke", "bare `*#` stroke".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Alternate (alternate discriminating feature set)
One of several discriminating feature sets that each identify the same self-homograph
spelling, one per distinct feature combination; pressing any one of them is enough. Index 0
is the primary alternate; the others become alternate entries.
- Code: `resolveGroupPressSets` src/elicitation.py:374; `buildKeypressGroupExtraAlternates` src/ambiguitychecker.py:844.
- Avoid "press-set alternate". Not the same as an **alternate entry** (the theory-2 stroke it produces).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Alternate entry
A theory-2 stroke after index 0: a self-homograph's second dictionary entry, built from a
non-primary alternate (base strokes plus that alternate's feature discriminating stroke).
It is a separate concept, **not** an extra stroke. Alternate entries skip the star/hash
marks (item B4).
- Code: `buildExtraInducedStrokes` src/ambiguitychecker.py:1288; dictionary.py:389.
- Avoid "alternate stroke", "alternates" (for the entry).
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Answer Collection
The human-loop sub-step of Discriminating-Feature Elicitation (Elicitation Phase): the
questionnaire page is published, a person checks for each opposition which atomic features
each side needs, and the answers are copied into `elicitation_answers.json`. Needed only when
Press-Set Resolution reports unresolved oppositions (rebuild step 4h).
- Code: util/build_questionnaire_page.py:521 (S6.Elicitation.5); validator util/check_conjugation_disambiguation_order.py:130 (S6.Elicitation.6).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Association (grapheme-phoneme association, `assoc`)
LexiqueInfra's column of `grapheme-phoneme` pairs joined by `.`, with `#` for a silent
letter. It is aligned onto the Lexique383 syllable skeleton to build a breakdown.
- Code: `resources/LexiqueInfraCorrespondance.tsv`; `fixLexiqueInfraGraphPhon` lexique.py:652.
- First used in: Lexicon Building (S1).

### Atomic feature / Feature
One grammatical value that a writer can assert with a press: `pers_2`, `nbr_p`,
`subjonctif`, `f`, … "Feature" is the short form. The legacy `WordFeature` also covered
compound features such as `ind:pre:3s`; say "compound feature (legacy)" for those.
- Code: `atomicFeatures` src/word.py:406; `Word.splitInfoVerb` :102; the on-disk/UI fields `atomsA`/`atomsB` of `elicitation_answers.json`.
- Preferred over "marker" (code names `markersByKeypress`, `liveMarkers`, `PREFERRED_KEYS_BY_MARKER` keep it), "atom" and "discriminator".
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Bare mark stroke
Legacy name. Use **\*/# marker stroke**.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Base strokes
A word's theory-1 Strokes: one stroke per syllable, no extra strokes or star/hash marks.
- Code: `buildWordToStrokes` src/ambiguitychecker.py:553; `strokes` column of `theory2.tsv`.
- Preferred synonym for "phoneme strokes" and "theory-1 strokes". Keep "last phoneme
  stroke" for the specific stroke that receives a merged star/hash mark.
- First used in: Phonetic Theory Building (S5).

### Best permutation / pairwise order matrix
The left-to-right phoneme order per syllabic part that maximizes in-order biphoneme
frequency, and its per-pair `<`/`>`/`=` preferences with score differences
(`pairwiseBiphonemeOrderScore`). Part of the layout statistics; the matrix is the order term
of the layout solver (src/cpsatsolver.py:363).
- Code: `BiphonemeCollection.optimizeOrder` src/grammar.py:318, `generateBiphonemeOrderMatrix` :361.
- First used in: Keyboard Layout Optimization (S4).

### Breakdown (syllable breakdown)
The pair `syll_cv` (phonemes) / `orthosyll_cv` (graphemes) of a lexicon row, syllables
joined by `|` and slots by `_`, `#` for silent phonemes. Strokes are read from `syll_cv` only.
- Code: `lexique.Word.breakdownSyllables` lexique.py:750.
- First used in: Lexicon Building (S1).

### Breakdown orphan
A Lexique383 row with no LexiqueInfra association of matching phonology; it is silently
dropped from the mixed lexicon (4,852 rows, mostly multi-word expressions).
- Code: lexique.py:1184.
- First used in: Lexicon Building (S1).

### Candidate key-set
A coda-bank key-set considered for one keypress group: the keys of one consonant phoneme,
or the union of two.
- Code: `codaKeysOf` src/ambiguitychecker.py:1041-1045; `_bestCandidate` :1177.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Canonical form (of a Strokes)
A Strokes with each stroke's keys sorted and deduplicated: the stroke as physically pressed.
Every collision test should compare this form, not the raw form.
- Code: `canonicalizeStrokes` src/keyboard.py:31.
- Contrast: **Raw Strokes**.
- First used in: Phonetic Theory Building (S5).

### Canonical member
The member of a homophone group or lemma-homophone group that gets nothing extra: the
spelling whose primary alternate is the empty discriminating feature set `∅` in Same-Lemma
and Grammatical-Category Disambiguation (S6), or the rank-0 word with star/hash code `()` in
Different-Lemma or Grammatical-Category Disambiguation (S7). In a homophone group it is
chosen by the elicitation answers, never computed.
- Code: `resolveGroupPressSets` src/elicitation.py:374; `assignStarHashCombos` src/ambiguitychecker.py:272.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Canonical-only collision
Words in different theory-1 entries whose raw Strokes have the same canonical form, so they
type identically (233 canonical Strokes today, e.g. entre/heurte). Visible only after
canonicalization.
- Code: `canonicalizeStrokes` src/keyboard.py:31.
- First used in: Phonetic Theory Building (S5).

### Chord
Avoid. It was used for a physical stroke (src/keyboard.py:21, Realization Phase
docstrings), an abstract keypress group (pre-elicitation-pivot plan, git history) and a
trainer record (`Chord`, util/export_practice_sentences.py:50). Code names such as
`frequencyWeightedChordSizes`, `chordsWithReadings`, `chordsByOrtho` stay.
- Preferred synonym: **Stroke** for keys pressed together; **key-set** for part of a
  stroke; **Keypress Group** for the abstract unit; **Drill item** for the trainer record;
  **Illegal stroke** for "illegal chord".
- First used in: Phonetic Theory Building (S5).

### Cluster
Avoid entirely, including qualified forms. It had three meanings, now: **Homophone Group**
(same `lemmeGramCat`, same canonical stroke), **Theory-1 collision** (all words on one
theory-1 stroke; `StrokeClusterReport` src/ambiguitychecker.py:46) and **Lemma-homophone
group** (the unit of the star/hash marks; `rankHomophoneCluster` :261). Code names keep
"cluster". A phonetic consonant cluster is called a consonant sequence or multiphoneme.
- First used in: Phonetic Theory Building (S5).

### Coda / Onset / Nucleus (syllabic part)
The consonants after the first vowel, the consonants before it, and all the vowels of a
syllable. Each part maps to its own key bank. A syllable with no vowel puts all its
consonants in the onset.
- Code: `Syllable.__init__` src/grammar.py:499-518; `Phoneme.phonemesByPart` :35.
- First used in: Dictionary Loading (S3).

### Coda bank
The right-hand keys 16-25, which type coda consonants. The Realization Phase chooses
feature keys only from this bank.
- Code: `keyIDinSyllabicPart` in `starboard3h.json`; util/build_realization_report.py:4.
- First used in: Phonetic Theory Building (S5).

### Conjugation-feature legend
The trainer's table from keypress group to physical keys and French feature labels, read
from the realization report (not from the inline path).
- Code: `_conjugationMarkers` util/export_keyboard_layout.py:117.
- Avoid "conjugation-marker legend".
- First used in: Theory Export (S8).

### Cross-category clash
Two colliding words with the same bare lemma but different grammatical category (appel NOM /
appelle VER). Their `lemmeGramCat`s differ, so the Realization Phase ignores them and
Different-Lemma or Grammatical-Category Disambiguation (S7) gives them star/hash marks.
- Code: `crossCategoryClashCollisions` src/ambiguitychecker.py:1251; `detectCrossCategoryClash` :59 (diagnostic only).
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Cross-lemma collision
Two colliding words with different bare lemmas (ver/vert/verre). Left to Different-Lemma or
Grammatical-Category Disambiguation (S7).
- Code: `crossLemmaCollisions` src/ambiguitychecker.py:1255.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Dictionary Loading (S3)
The stage that reads the mixed lexicon and the synthetic lexicon rows into the Word list:
`Dictionary()` construction, excluded words, identity merge, spelling/lemma indexes,
`analyseSyllabification` (syllable statistics) and the `Dictionary.pickle` cache. First part
of `python dictionary.py`.
- Code: dictionary.py:448-472; `Dictionary.readCorpus` :92.
- Avoid calling it part of "Phonetic Theory Building (S2)" (legacy scope).
- First used in: Dictionary Loading (S3).

### Different-Lemma or Grammatical-Category Disambiguation (S7)
The stage that adds star/hash marks to words that still collide after the Realization Phase
with a different `lemmeGramCat` (different lemma, or same lemma in another category),
producing theory 2. Its rule stack is the star/hash rule stack (R1-R7).
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:410, called from `Dictionary.buildFinalTheory` dictionary.py:385.
- Avoid "Lemma-Homophone Marking (S4)", "`*`/`#` track", "cross-lemma track", "reserved-key track".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Digraph subsumption
When the union of some phonemes' key tuples equals, or contains, another phoneme's tuple,
different phoneme sequences give the same physical stroke (coda `k`+`d` = `g`; onset `R` ⊂ `j`).
- Code: docstrings of the syllable-break exceptions, src/word.py:215-340.
- First used in: Phonetic Theory Building (S5).

### Discriminating feature set
The set of atomic features a writer presses, beyond the sound strokes, to get one spelling
of a homophone group. The empty set `∅` marks the canonical member. A self-homograph
spelling has several (its alternates).
- Code: `AnsweredOpposition.pressA`; `resolveGroupPressSets` src/elicitation.py:374; `pressSets` in `resolved_press_sets.json`.
- Avoid "press-set" and "signature" in prose (code names `pressSet`, `PressSetsByGroup`, `resolved_press_sets.json` stay).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Discriminating feature set conflict
Two different spellings of one homophone group holding the same resolved discriminating
feature set; the group is dropped.
- Code: `GroupConflict` src/elicitation.py:414.
- Avoid "press-set conflict", "group conflict".
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Discriminating-Feature Elicitation (Elicitation Phase)
The first phase of Same-Lemma and Grammatical-Category Disambiguation (S6). Three named
sub-steps: **Questionnaire Generation**, **Answer Collection** (human loop) and
**Press-Set Resolution**. In a rebuild it asks nothing: it regenerates questionnaire items
and resolves the stored answers into the resolved discriminating feature sets.
- Code: `python -m src.elicitation`, src/elicitation.py:527; call ids S6.Elicitation.n.
- Avoid "Marker Elicitation (Phase E)", "Phase E".
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Discriminating-Feature Grouping (Grouping Phase)
The second phase of Same-Lemma and Grammatical-Category Disambiguation (S6): packs the live
features into the minimum number K of keypress groups so no two spellings of a homophone
group induce the same thing.
- Code: util/build_keypress_groups.py:49; `minKeypressesSatWithPriorities` src/featuregroupingsat.py:490; call ids S6.Grouping.n.
- Avoid "Marker Grouping (Phase G)", "Phase G".
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Discriminating-Feature Stroke Realization (Realization Phase)
The third phase of Same-Lemma and Grammatical-Category Disambiguation (S6): gives each
keypress group a coda-bank key-set and appends one feature discriminating stroke per word
that needs features. Runs on two call sites, the inline path and the report build.
- Code: `realizeKeypressGroupsAsExtraStroke` src/ambiguitychecker.py:987; call ids S6.Realization.n.
- Avoid "Marker Stroke Realization (Phase P)", "Phase P".
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Discriminator
Pre-2026-09-18 name for a solver-chosen feature that separates homophones. Survives in
function names (`buildDiscriminatorSelection`) and in Synthetic Lexicon Building (S2)'s gating.
- Preferred synonym: **Atomic feature** (the value) or **Discriminating feature set** (what is pressed). Avoid.
- First used in: Synthetic Lexicon Building (S2).

### Donor / ending table
The attested words of a verb template or NOM/ADJ ending class (donors), and the suffix
transformation learned from them by majority, with match rate and donor count, then spliced
onto a missing form.
- Code: `deriveConjugationEndingTables` src/verbparadigm.py:493; `deriveNomAdjEndingTables` src/nomAdjParadigm.py:250.
- First used in: Synthetic Lexicon Building (S2).

### Doublet (1990-reform spelling doublet)
The pre- and post-reform spellings of one lemma (259 pairs). They are merged and share one
star/hash code, so they are never marked against each other and may stay colliding.
- Code: `loadReform1990DoubletPairs` src/ambiguitychecker.py:94.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Drill item
One `practice-words.json` record of the steno-trainer, keyed by (spelling, steno).
- Code: util/export_practice_words.py:225.
- Avoid "chord" for it.
- First used in: Theory Export (S8).

### Elicitation answers
The person's recorded checkbox answers, one per opposition: the only hand-authored input of
Same-Lemma and Grammatical-Category Disambiguation (S6). A dataset state.
- Code: `elicitation_answers.json`; `AnsweredOpposition` src/elicitation.py:266.
- First used in: Answer Collection, in Discriminating-Feature Elicitation (Elicitation Phase).

### Escalated star/hash code
A star/hash code past the four-code budget `()`, `*`, `#`, `*#`: `*#` repeated n ≥ 2 times.
Its second and later symbols become \*/# marker strokes.
- Code: `assignStarHashCombos` src/ambiguitychecker.py:272.
- Avoid "escalated mark code".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Excluded word
A spelling listed in `excluded_words.txt` (44 today), dropped when the Word list is read.
Distinct from a lexicon exclusion.
- Code: `Dictionary.readCorpus` dictionary.py:102.
- First used in: Dictionary Loading (S3).

### Extra stroke
Umbrella word for a stroke appended to a word's base strokes. Exactly two kinds exist: the
**feature discriminating stroke** (Realization Phase) and the **\*/# marker stroke**
(escalated star/hash code). An alternate entry is not an extra stroke, and neither is the
merged star/hash mark (it joins an existing stroke).
- Code: `_appendCodaExtraStroke` src/ambiguitychecker.py:892; `composeReservedKeyStrokes` :444.
- Say which kind when it matters. Avoid "trailing stroke", "coda stroke".
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Feature Combination
One grammatical analysis of a spelling, as a set of atomic features ("parle" = 1s or 3s
présent). Participle combinations include gender and number; a Word without verb tags has
one combination {gender, number}.
- Code: `FeatureCombination` src/elicitation.py:27; `wordFeatureCombinations` :30; on-disk field `readings` of `resolved_press_sets.json`; `type Reading` util/export_practice_words.py:70.
- Preferred over "reading" (code names `readings`, `Reading`, `buildReadingsByWord` stay).
- First used in: Dictionary Loading (S3) (verb tags merged per Word).

### Feature discriminating stroke
The single extra coda-bank stroke that the Realization Phase appends after a word's base
strokes: the union of the chosen keys of every keypress group the word needs. One of the two
kinds of extra stroke.
- Code: `_appendCodaExtraStroke` src/ambiguitychecker.py:892; `buildFinalInducedStrokes` :1261.
- Avoid "marker stroke", "Phase P stroke", "coda extra stroke", "trailing stroke".
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Film frequency
`Word.frequency`, which is the film-subtitle frequency only (`freqfilms2`); book frequency is
read but never used. It drives every frequency rule and every "keep the most frequent" choice.
- Code: src/word.py:93.
- First used in: Dictionary Loading (S3).

### Final induced strokes
A dataset state: every Word's base strokes plus at most one feature discriminating stroke,
before the star/hash marks. `dict[Word, Strokes]`.
- Code: `buildFinalInducedStrokes` src/ambiguitychecker.py:1261.
- Avoid "finalInduced" in prose.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Finalized word
A Word whose keypress groups have all been given keys, so its composed feature
discriminating stroke can no longer change; later candidates are checked against it.
- Code: `_finalizeReadyWords` src/ambiguitychecker.py:1066.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Fix script
A one-shot `util/fix*.py` lexicon patch: dry run by default, `--apply` writes.
- Preferred over "fixer".
- First used in: Lexicon Building (S1).

### Frequency-ratio rule (R4)
Rule R4 of the star/hash rule stack: when one word's film frequency is at least 10 times the
other's (or the other is 0), the rarer word is marked, without looking at categories.
- Code: `RATIO_EXEMPTION_THRESHOLD` src/ambiguitychecker.py:91 (name unchanged); `decideStarHashMark` :221-225.
- Avoid "10x ratio exemption" / "frequency-ratio exemption" (code and ROADMAP.md wording):
  the pair is still marked; only the category rules are skipped.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Frequent words
The 200 top spellings of `resources/top500_film.txt`. They get weight 0 in the syllable
statistics and in the keypress group usage weights.
- Code: `Dictionary.frequentWords` dictionary.py:63; src/elicitation.py:615.
- First used in: Dictionary Loading (S3).

### Gemini PR keymap
The mapping from Stenalgo key names to Gemini PR wire labels, taken from hardware sniffing.
Keys 0, 1, 2 and 10 are sent as number-bar bits; key 15 (`#`) is the only star bit.
- Code: `GEMINI_PR_LABELS` util/export_plover_system.py:28.
- First used in: Theory Export (S8).

### GramCat
The grammatical category enum: 22 values such as `NOM`, `VER`, `ADJ:pos`.
- Code: src/word.py:10.
- First used in: Dictionary Loading (S3).

### Group representative
The most frequent member of a merged homograph/doublet set inside a lemma-homophone group.
Only representatives are ranked by the star/hash rule stack; every member takes its code.
- Code: `assignStarHashMarks` src/ambiguitychecker.py:311, :332.
- Avoid "mark representative".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Group shape
Legacy provisional name. Use **Homophone group set of feature sets**.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Hard grouping rule / soft preference tier
Grouping Phase constraints that may raise K (`ALONE_KEYS`, `MUST_DIFFER_GROUPS`) versus
lexicographic preferences applied at the fixed minimum K (`PREFERENCE_TIERS`).
- Code: util/build_keypress_groups.py:39-45.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Homograph / Self-homograph
Two Words with the same spelling; they type the same text, so they are never separated. A
**self-homograph** is one spelling with several feature combinations inside one homophone
group ("calmez": impératif or indicatif 2p); it gets one alternate per combination.
- Code: `decideStarHashMark` homograph exemption (R1) src/ambiguitychecker.py:211; `resolveGroupPressSets` src/elicitation.py:374.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Homophone Group
Words with the same `LemmeGramCat` and the same canonical Strokes: forms of one paradigm
that sound alike (dors/dort). The unit of Same-Lemma and Grammatical-Category Disambiguation
(S6); the dataset state "homophone groups" holds all 47,830 of them.
- Code: `buildLemmaHomophoneGroups` src/elicitation.py:61; `LemmaHomophoneGroupKey` :24 (named "lemma" but keyed by LemmeGramCat; rename to `HomophoneGroupKey` queued in TODO.md).
- Avoid "cluster" and "same-lemma homophone group" (redundant).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Homophone group set of feature sets
A homophone group reduced to its set of per-spelling alternate sets (each a set of
discriminating feature sets), with spellings, strokes and lemmas removed. Groups with the
same set of feature sets pose the same grouping problem (294 distinct ones for 47,828 groups).
- Code: `GroupSignature` src/featuregroupingsat.py:37; `groupSignatures` :40.
- Avoid "signature", "group signature", "group shape".
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Identity merge
`readCorpus` folding a later lexicon row with an already-seen Word identity into the first
Word. Only the verb tags are merged; the first row's syllabification and frequency win.
- Code: dictionary.py:113-137; `Word.mergeInfoVerb` src/word.py:129.
- First used in: Dictionary Loading (S3).

### Illegal stroke
A stroke (canonical key-set) that no finger assignment of the keyboard can press:
`getStrokeCost` returns `None`. 529 Words contain one (mostly "-isme").
- Code: `Keyboard.getStrokeCost` src/keyboard.py:547.
- Avoid "illegal chord".
- First used in: Phonetic Theory Building (S5).

### Implicit-hyphen key
A key whose presence in a stroke makes Plover's `-` separator before the right bank
unnecessary. Here: nucleus keys 11-14 and `*` (10).
- Code: util/export_plover_system.py:44; util/_stenorender.py:27.
- First used in: Theory Export (S8).

### In-scope collision
Code-only name for a same-lemmeGramCat collision.
- Code: `_isInScopeCollision` src/ambiguitychecker.py:968.
- Preferred synonym: **Same-lemmeGramCat collision**. Use "in-scope" only as the function name.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Induced discriminating feature set
Every atomic feature asserted when a spelling's features are pressed through their keypress
groups: the union of all features of the groups touched.
- Code: `inducedPressSet` src/featuregrouping.py:135.
- Avoid "induced press-set".
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Inline path / report build
The two call sites of the Realization Phase. The **inline path** runs inside
`Dictionary.buildFinalTheory` and feeds theory 2 and all exports; the **report build**
(`util/build_realization_report.py`) writes only the realization report. The trainer legend
reads the report while Plover recomputes inline, so the two can drift (item B18).
- Code: dictionary.py:373-389; util/build_realization_report.py:38.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Four-code budget
The four star/hash codes `()`, `*`, `#`, `*#` — every combination of the two reserved mark
keys 10 and 15. Codes past it are escalated star/hash codes.
- Code: `assignStarHashCombos` src/ambiguitychecker.py:284-288.
- Avoid "two-key budget", "base budget", "4-slot budget".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### K
The number of keypress groups found by the Grouping Phase: the smallest number that is
feasible under the hard grouping rules. Currently 7.
- Code: `keypressCount` in `keypress_groups.json`; `minKeypressesSat` src/featuregroupingsat.py:417.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Key-set
A set of keys that forms part of a stroke, for example a candidate key-set of the
Realization Phase or the keys chosen for one keypress group.
- Code: `chosenKeysByGroup` in `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904.
- Avoid "chord" for it.
- First used in: Keyboard Layout Optimization (S4).

### Keyboard layout
A dataset state: the `Starboard` loaded from `starboard3h.json`, mapping phonemes to key
tuples per syllabic bank. Produced by Keyboard Layout Optimization (S4); no current command
rewrites it.
- Code: `Keyboard.fromJSONFile` src/keyboard.py:252.
- First used in: Keyboard Layout Optimization (S4).

### Keyboard Layout Optimization (S4)
The stage that produces `starboard3h.json`: the layout statistics (Phoneme order search
(S4.1), Ambiguity statistics (S4.2)), the fallback keymap (S4.3) and the CP-SAT layout solve
(S4.4, ambiguity ×30,000 + ergonomics ×1 + phoneme order ×500 per syllabic part, 90 s each).
A real, rarely run and costly stage, **not dead code** (decision b5). The statistics run on
every fresh rebuild; the solver call is commented out at dictionary.py:494, so no command
regenerates the layout today (queued in TODO.md).
- Code: `optimizeKeyboard` src/cpsatsolver.py:13; dictionary.py:464-466, :489-496.
- Avoid "Keyboard Layout Optimization (S2b)", "not run" as a description of the stage.
- First used in: Keyboard Layout Optimization (S4).

### Keypress
Only the type alias for a *physical* key combination under one finger
(`Keypress: TypeAlias = tuple[int, ...]`, used by `PositionWeights`). Older plan and Grouping
Phase docstrings also used it for the abstract unit; say **Keypress Group** for that.
- Code: src/keyboard.py:26.
- First used in: Phonetic Theory Building (S5).

### Keypress Group
One output unit of the Grouping Phase: an integer id and the atomic features it carries;
pressing it asserts all of them. The Realization Phase gives each one physical coda keys.
The dataset state "keypress groups" holds all K of them.
- Code: `markersByKeypress` in `keypress_groups.json`; `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904.
- Preferred over "keypress", "marker group" and "chord" for the abstract unit.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Keypress group conflict
Two different spellings of one homophone group that induce the same set of keypress groups
after features are bundled. Any conflict aborts the Grouping Phase's write.
- Code: `KeypressConflict` src/featuregrouping.py:150.
- Avoid "keypress conflict" in prose.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Keypress group population
A dataset state: the Words that need each keypress group (from their primary alternate),
plus each self-homograph Word's extra alternate group sets.
- Code: `buildKeypressGroupToWords` src/ambiguitychecker.py:803; `buildKeypressGroupExtraAlternates` :844.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Last phoneme stroke
The last of a word's base strokes. The first symbol of its star/hash code is pressed together
with it (a merged star/hash mark), even when a feature discriminating stroke follows.
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:437-444.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Layout entry / shared layout entry
One `phonemesAssignedToStroke` item: a key tuple within one syllabic bank and the phonemes it
types (48 today). A shared layout entry types two or more phonemes of the same part (key 9 =
`w`/`N`/`G`).
- Code: `starboard3h.json`; src/keyboard.py:466.
- First used in: Phonetic Theory Building (S5).

### Layout statistics
The two statistics computed for the layout solver: the best permutation and pairwise order
matrix (Phoneme order search (S4.1)) and the syllabic-part ambiguity, with the syllabic and
lexical ambiguity tables (Ambiguity statistics (S4.2)). They run on every fresh rebuild (a
`Dictionary.pickle` miss) and are saved in the pickle; they are inputs of `optimizeKeyboard`
(src/cpsatsolver.py:14, :48, :363) and of the fallback keymap. Not dead code (decision b5).
- Code: `Syllable.optimizeBiphonemeOrder` src/grammar.py:644; `Dictionary.analyseAmbiguities` dictionary.py:183.
- First used in: Keyboard Layout Optimization (S4).

### Lemma-homophone
Homophones whose `lemmeGramCat` differs (different lemma, or same lemma in another category).
- Code: the "≥2 distinct `lemmeGramCat`" filter, src/ambiguitychecker.py:402.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Lemma-homophone group
The unit of Different-Lemma or Grammatical-Category Disambiguation (S7): Words sharing one
canonical final induced stroke, with at least 2 `lemmeGramCat`s and 2 spellings (4,450 today).
- Code: `groupHomophonesByReservedStroke` src/ambiguitychecker.py:380; `rankHomophoneCluster` :261 (code name keeps "cluster").
- Avoid "lemma-homophone cluster", and "homophone group" for it (that is the same-`lemmeGramCat` unit).
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Lemma-Homophone Marking (S4)
Legacy stage name. Use **Different-Lemma or Grammatical-Category Disambiguation (S7)**.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Lemme / LemmeGramCat
The lemma string, and the key `"lemme_GramCat"` (`rucher_NOM`) that almost every "same-lemma"
test actually uses. `groupWordsByLemme` groups by LemmeGramCat (rename to
`groupWordsByLemmeGramCat` queued in TODO.md); `groupWordsByBareLemme` groups by bare lemme.
- Code: src/word.py:22-23, :100, :414, :425.
- First used in: Lexicon Building (S1).

### Lexicon Building (S1)
The stage that merges Lexique383 and LexiqueInfra into the mixed lexicon
(`LexiqueMixte.tsv`) with syllable breakdowns, normalized lemmas and 1990-reform spellings.
- Code: lexique.py:1261-1263 (module body).
- First used in: Lexicon Building (S1).

### Lexicon exclusion
A spelling dropped while building the mixed lexicon (`resources/lexiconExclusions.tsv`, 134
entries). Distinct from an excluded word and from `ambiguityIgnoreList.tsv` (collision metric
only); avoid calling any of them "the exclusion list".
- Code: `loadLexiconExclusions` lexique.py:38.
- First used in: Lexicon Building (S1).

### Live feature / unpressable feature
An atomic feature that appears in at least one resolved discriminating feature set (13
today), versus one that never does (7) and is left out of the Grouping Phase.
- Code: `liveMarkers` src/featuregrouping.py:63.
- Avoid "live marker", "unpressable marker".
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Mark
Avoid bare "mark". For `*`/`#` say **star/hash mark** (and **star/hash code**); a
grammatical value is an **atomic feature**. The verb "to mark" (give a star/hash mark, or
give a word its feature discriminating stroke when the context says which) is fine.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Mark code / merged mark / mark representative
Legacy names. Use **Star/hash code**, **merged star/hash mark** and **Group representative**.
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Marker
Avoid for a grammatical value; use **Atomic feature** / **Feature** (decision a6). It
survives in code names (`markersByKeypress`, `liveMarkers`, `PREFERRED_KEYS_BY_MARKER`,
`_conjugationMarkers`) and, by decision a8, in the name **\*/# marker stroke**.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Marker Elicitation / Marker Grouping / Marker Stroke Realization (Phase E / G / P)
Legacy phase names. Use **Discriminating-Feature Elicitation (Elicitation Phase)**,
**Discriminating-Feature Grouping (Grouping Phase)** and **Discriminating-Feature Stroke
Realization (Realization Phase)**. The letter codes survive only in commit history and in
the old file names listed under Renamed files.
- First used in: Same-Lemma and Grammatical-Category Disambiguation (S6).

### Marker stroke
Legacy name. Use **Feature discriminating stroke** (not to be confused with the **\*/#
marker stroke**).
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Mixed lexicon
A dataset state: `resources/LexiqueMixte.tsv`, 136,456 rows × 12 columns (rows, not distinct words).
- Code: `outputMixedLexique` lexique.py:1174.
- First used in: Lexicon Building (S1).

### Onset-only stroke (vowel-less syllable)
The stroke of a syllable with no vowel: all its consonants go to the onset bank. Comes from
the syllable-break exceptions and, unintentionally, from many synthetic rows.
- Code: src/grammar.py:499.
- First used in: Phonetic Theory Building (S5).

### Opposition / tie opposition / unresolved opposition
An **opposition** is an unordered pair of different feature combinations of two spellings in
one homophone group — the unit a questionnaire item asks about. A **tie opposition** pairs two
spellings with the same feature combination (no feature can separate them; skipped). An
**unresolved opposition** has no answer, or disagreeing answers; its whole group is dropped.
- Code: `OppositionSample` src/elicitation.py:99; `AnswerByOpposition` :276; :356-363.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Phoneme
A single-character X-SAMPA sound: 16 nucleus (vowel) and 20 consonant symbols, plus a
temporary `x`. A `Biphoneme`/`Multiphoneme` is a sequence of phonemes within one syllabic part.
- Code: src/grammar.py:16, :32-33.
- First used in: Dictionary Loading (S3).

### Phonetic stroke rule
How a syllable becomes a stroke: each phoneme's layout key tuple for its part, concatenated
onset → nucleus → coda in spoken order, kept raw.
- Code: `Starboard.getStrokeOfSyllableByPart` src/keyboard.py:607.
- First used in: Phonetic Theory Building (S5).

### Phonetic Theory Building (S5)
The stage that loads `starboard3h.json` and maps each Word to its base strokes, producing
theory 1 (`buildTheory`, `writeTheory`, `FirstTheory.pickle`). Second part of
`python dictionary.py`. Its legacy code (S2) also covered Dictionary Loading (S3) and the
layout statistics.
- Code: dictionary.py:487-505; `Dictionary.buildTheory` :305.
- First used in: Phonetic Theory Building (S5).

### Physical keypress group assignment
A dataset state: the chosen coda keys per keypress group, their costs and alternates, the
unassigned groups and the residual-collision buckets.
- Code: `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904.
- Avoid "physical keypress assignment".
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Plover dictionary / Plover key table
The RTFCRE-steno → spelling JSON used by Plover (`plover_stenalgo_dictionary.json`, 163,238
entries), and the generated module of key names, implicit-hyphen keys and Gemini PR keymap
(`_generated_keys.py`) used by the `plover_stenalgo` system plugin. Both belong to the Plover
branch of Theory Export (S8).
- Code: util/export_plover_dictionary.py:35; util/export_plover_system.py:38.
- First used in: Theory Export (S8).

### Precedence spec
`conjugation_disambiguation_order.txt`: the ordered feature combinations and special rules
that express intended precedence. Authoritative intent, but the code only partly checks it
and never enforces the order.
- Code: `parsePrecedenceOrder` util/check_conjugation_disambiguation_order.py:43.
- First used in: Answer Collection, in Discriminating-Feature Elicitation (Elicitation Phase).

### Preferred key
A human-chosen key-set for the keypress group holding a given atomic feature (impératif →
18, pers_2 → 19, pers_3 → 20); it wins whenever it is feasible.
- Code: `PREFERRED_KEYS_BY_MARKER` src/ambiguitychecker.py:945.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Press-set
Legacy name. Use **Discriminating feature set**. The code keeps it (`pressSet`, `pressA`,
`pressSets`, `PressSetsByGroup`, `resolveGroupPressSets`, `resolved_press_sets.json`) and so
does the sub-step name Press-Set Resolution.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Press-Set Resolution
The last sub-step of Discriminating-Feature Elicitation (Elicitation Phase): indexes the
elicitation answers, resolves each spelling's discriminating feature sets per homophone group,
validates conflicts and writes `resolved_press_sets.json`. The name keeps the code's word;
the thing produced is a discriminating feature set.
- Code: src/elicitation.py:585-620 (S6.Elicitation.8-12).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Primary alternate
Index 0 of a spelling's sorted alternates (smallest discriminating feature set first). Only
the primary drives the Realization Phase's key search; the others become alternate entries.
- Code: src/elicitation.py:404-407; `buildKeypressGroupToWords` src/ambiguitychecker.py:832.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Pronoun paradigm lemma
The fold of pronoun lemmas into one paradigm (`ils→il`, `elles→elle`, `ceux→celui`), so their
forms are separated by Same-Lemma and Grammatical-Category Disambiguation (S6).
- Code: `pronounParadigmLemme` lexique.py:81.
- First used in: Lexicon Building (S1).

### Questionnaire Generation
The first sub-step of Discriminating-Feature Elicitation (Elicitation Phase): builds the
homophone groups, enumerates feature combinations and oppositions, and writes one
questionnaire item per distinct opposition (`questionnaire.json`).
- Code: src/elicitation.py:548-573 (S6.Elicitation.1-4).
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Questionnaire item
One opposition shown with an example pair of spellings (200 today); the dataset state
"questionnaire items" is persisted as `questionnaire.json`.
- Code: `QuestionnaireItem` src/elicitation.py:210.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Raw lexicon rows
A dataset state: `list[lexique.Word]` read from Lexique383 (a different dataclass from `src.word.Word`).
- Code: `Lexique.read_corpus` lexique.py:966; lexique.py:547.
- First used in: Lexicon Building (S1).

### Raw Strokes
The theory-1 key form: per syllable, each phoneme's full layout key tuple concatenated in
onset → nucleus → coda and spoken order, repeats kept. Theory 1 is keyed on it.
- Code: `getStrokeOfSyllableByPart` src/keyboard.py:607.
- Contrast: **Canonical form**. Say "raw" whenever a count or equality is taken on theory-1 keys.
- First used in: Phonetic Theory Building (S5).

### Reading
Avoid. Use **Feature Combination** (decision a2). The on-disk field `readings` and the
trainer type `Reading` keep the word as code names.
- First used in: Dictionary Loading (S3).

### Realization report
`realization_report.json`: the tracked output of the Realization Phase's report
build (chosen keys, costs, alternates, residual buckets). Read only by the trainer keyboard
legend, which can therefore drift from the inline path.
- Code: util/build_realization_report.py:38.
- Avoid "Phase P report", "reference artifact".
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Reform rewrite / reform lemma normalization
A **reform rewrite** is an output-time 1990-reform change to `ortho`/`orthosyll_cv` (ortho
rule, -eler/-eter, loanword plural, two one-offs), never to `phon`. **Reform lemma
normalization** changes only `lemme`, at read time.
- Code: lexique.py:1197-1244; `normalizeLemme` lexique.py:540.
- First used in: Lexicon Building (S1).

### Regret (gap)
For a clashing lemma-homophone pair A/B with film frequencies `fA`/`fB`: the cost of the
chosen star/hash assignment is the frequency of the Word it marks (one extra key per
occurrence); the per-pair optimum is `min(fA, fB)` (mark the rarer); the **gap** —
equivalently the **regret** of the choice — is `cost − optimum`. Summed over all clashing
pairs and divided by their total mass it becomes **gap%**, the headline quality metric of
the star/hash rules (about 0.5 %; [specs/star-hash-marking.md §2](specs/star-hash-marking.md)).
Regret is the reason the frequency-ratio rule (R4) exists (≥ 10× pairs: marking the rarer
word is near-free, so the ratio is its own mnemonic) and why the same-category (R5) and
category-priority (R6) rules take that specific linear order: it matches every observed
category pair's regret-optimal direction.
- Code: `decideStarHashMark` src/ambiguitychecker.py:183; the design-time numbers are
  reproduced by `scratch/combined_regret.py`.
- Avoid contrasting "regret" and "gap": the same quantity.

### Reserved keys
Starboard keys 0, 1, 10 and 15, excluded from phonemes. 10 (`*`) and 15 (`#`) carry star/hash
marks; 0 and 1 are held for a possible third mark. They are not "control" keys.
- Code: `_reservedKeys` src/keyboard.py:320; src/ambiguitychecker.py:351-352.
- First used in: Phonetic Theory Building (S5).

### Residual collision
Two different words still sharing a final stroke after the Realization Phase, in one of four
buckets: theory (a composed stroke equals a theory-1 key), same-lemmeGramCat, cross-category
clash, or cross-lemma collision.
- Code: `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904; :1219-1258.
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Resolved discriminating feature sets
A dataset state: for every homophone group, each spelling's list of alternate discriminating
feature sets, plus frequencies and feature combinations (47,828 groups;
`resolved_press_sets.json`, gitignored).
- Code: `resolveGroupPressSets` src/elicitation.py:374; `serializeResolvedPressSets` :471; `PressSetsByGroup` src/featuregrouping.py:27.
- Avoid "resolved press-sets".
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### RTFCRE
Plover's steno string notation: `/` between strokes, `-` before right-bank keys when no
implicit-hyphen key is present.
- Code: `renderFinalStrokesToRTFCRE` util/_stenorender.py:39.
- First used in: Theory Export (S8).

### Same-lemmeGramCat collision
Two Words with different spellings, the same `lemmeGramCat` and the same final stroke — the
only collision the Realization Phase blocks. Its invariant ("0 residual same-lemmeGramCat
collisions") is checked by the report build only.
- Code: `_isInScopeCollision` src/ambiguitychecker.py:968; `residualCollisions` :1248.
- Preferred over "in-scope collision" (function name only).
- First used in: Discriminating-Feature Stroke Realization (Realization Phase).

### Same-Lemma and Grammatical-Category Disambiguation (S6)
The stage that separates words sharing both a `lemmeGramCat` (lemma + grammatical category)
and a stroke, with elicited atomic features realized as one feature discriminating stroke.
Contains three phases: Discriminating-Feature Elicitation (Elicitation Phase),
Discriminating-Feature Grouping (Grouping Phase) and Discriminating-Feature Stroke
Realization (Realization Phase).
- Avoid "Same-Lemma Disambiguation (S3)".
- First used in: Same-Lemma and Grammatical-Category Disambiguation (S6).

### Same-Lemma Disambiguation (S3)
Legacy stage name. Use **Same-Lemma and Grammatical-Category Disambiguation (S6)**.
- First used in: Same-Lemma and Grammatical-Category Disambiguation (S6).

### Signature
Avoid. It named both a discriminating feature set (the root GLOSSARY.md's old sense, with a
stale "union across readings" definition) and `GroupSignature`.
- Preferred synonym: **Discriminating feature set** for what is pressed; **Homophone group set of feature sets** for `GroupSignature`.
- First used in: Discriminating-Feature Grouping (Grouping Phase).

### Source lexicons
A dataset state: the external input files `Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`,
`reform1990.tsv`, `lexiconExclusions.tsv` and Verbiste XML, patched in place by fix scripts.
- First used in: Lexicon Building (S1).

### Spelling twins
Two or more Words in one homophone group with the same spelling and `lemmeGramCat` but a
different identity ("finis" participle m:p and "finis" finite form). The Elicitation Phase
merges them into one spelling; the Realization Phase gives only the first a feature
discriminating stroke (item B1).
- Code: `_resolveEntryWord` src/ambiguitychecker.py:776.
- First used in: Discriminating-Feature Elicitation (Elicitation Phase).

### Star/hash code / merged star/hash mark
A **star/hash code** is the symbolic tuple such as `()`, `('*',)` or `('*#','*#')` given to one
rank of a lemma-homophone group. The **merged star/hash mark** is its first symbol pressed
with the last phoneme stroke; the **merged star/hash stroke** is that stroke's rendered form
(`*iel`, `ie#l`, `pvR-#`). Later symbols of an escalated code are \*/# marker strokes.
- Code: `assignStarHashMarks` src/ambiguitychecker.py:292; `assignStarHashCombos` :272; `_renderMarkedStroke` util/_stenorender.py:26.
- Avoid "mark code", "merged mark".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Star/hash mark
The `*` (key 10) and `#` (key 15) symbols that Different-Lemma or Grammatical-Category
Disambiguation (S7) adds to separate lemma-homophones. Not to be confused with an atomic
feature (a grammatical value) or a \*/# marker stroke (one kind of extra stroke that carries
them).
- Code: `STAR_KEY` = 10, `HASH_KEY` = 15, src/ambiguitychecker.py:351-352.
- Avoid bare "mark".
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Star/hash rule stack (R1-R7)
The ordered pairwise rules that decide which of two lemma-homophones gets the star/hash mark:
homograph exemption (R1), reform-doublet exemption (R2), per-pair override (R3),
frequency-ratio rule (R4), same-category rule (R5), category-priority rule (R6), frequency
fallback (R7). The first match decides. Numbers follow code order; always cite a rule by
name with its number, e.g. "frequency-ratio rule (R4)".
- Code: `decideStarHashMark` src/ambiguitychecker.py:183-232.
- Avoid "marking rule stack". Older design notes (git history,
  `RESUME_2026-09-20-starhash-priority.md`) use another numbering (ratio = Rule 1,
  homograph = Rule 2, doublet = Rule 3).
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Starboard
The 26-key target keyboard; its layout is `starboard3h.json`.
- Code: `Starboard` src/keyboard.py:290.
- First used in: Keyboard Layout Optimization (S4).

### Stroke / Strokes
A `Stroke` is the key indices pressed at once (one per syllable, plus extra strokes and
merged star/hash marks); `Strokes` is the tuple of strokes for a whole word.
- Code: src/keyboard.py:27-28.
- Preferred over "chord" for physically simultaneous keys; use **key-set** for a set of keys
  that forms part of a stroke.
- First used in: Phonetic Theory Building (S5).

### Syllabic-part ambiguity
The word frequency that would become indistinguishable if two whole onset/nucleus/coda
phoneme groups shared a key-set: the ambiguity input of the layout solver
(src/cpsatsolver.py:14, :48). One of the layout statistics.
- Code: `lexicalSyllabicPartAmbiguityScore` src/grammar.py:975; `Dictionary.syllabicPartAmbiguity`.
- First used in: Keyboard Layout Optimization (S4).

### Syllable
Onset + nucleus + coda, parsed from `syll_cv`; each becomes one stroke.
- Code: `Syllable` src/grammar.py:422; `Word.phonemesToSyllableNames` src/word.py:341.
- First used in: Lexicon Building (S1).

### Syllable-break exception
One of four `Word.fix_*` rewrites that move a syllable boundary for steno reasons, not
phonology (e+n repair, -rdre, -ayer conditionnel, -uer glide).
- Code: src/word.py:202-340.
- First used in: Dictionary Loading (S3).

### Syllable statistics
A dataset state: the `SyllableCollection` and the `Syllable` class-level phoneme, biphoneme
and multiphoneme collections. The syllable lookup feeds theory 1; the frequencies feed the
layout statistics.
- Code: `analyseSyllabification` dictionary.py:169.
- First used in: Dictionary Loading (S3).

### Synthetic Lexicon Building (S2)
The stage of hand-run scripts that generate missing verb, noun and adjective forms and
append them to `LexiqueSynthetic.tsv`. Never run in a rebuild; its own stage, not part of
Lexicon Building (S1) (decision b6).
- Code: util/completeVerbParadigms.py:350; util/generateMissingNomAdjForms.py:99.
- Avoid "Synthetic Paradigm Completion (S1b)".
- First used in: Synthetic Lexicon Building (S2).

### Synthetic Paradigm Completion (S1b)
Legacy stage name. Use **Synthetic Lexicon Building (S2)**.
- First used in: Synthetic Lexicon Building (S2).

### Synthetic row (synthetic lexicon rows)
A generated lexicon row in `resources/LexiqueSynthetic.tsv` (`source=synthetic`, frequency 0;
42,225 rows). Read after the mixed lexicon by Dictionary Loading (S3).
- Code: `writeSynthetic` util/completeVerbParadigms.py:324; dictionary.py:66-69.
- First used in: Synthetic Lexicon Building (S2).

### Theory 1
Every Word's base strokes, grouped by raw Strokes (`dict[Strokes, list[Word]]`, 80,725
entries), with no disambiguation. Persisted as `FirstTheory.pickle`; human view `theory.tsv`.
- Code: `Dictionary.buildTheory` dictionary.py:305.
- Preferred over "first theory".
- First used in: Phonetic Theory Building (S5).

### Theory-1 collision
A theory-1 entry holding two or more distinct spellings (41,640 today): the raw-key meaning of
"homophones" in Phonetic Theory Building (S5).
- Code: `StrokeClusterReport` src/ambiguitychecker.py:46 (diagnostic).
- Avoid "stroke cluster".
- First used in: Phonetic Theory Building (S5).

### Theory-1 entry
One (raw Strokes, list[Word]) item of theory 1; its list is frequency-descending.
- Code: dictionary.py:312.
- First used in: Phonetic Theory Building (S5).

### Theory 2
Every Word's final Strokes list after Same-Lemma and Grammatical-Category Disambiguation (S6)
and Different-Lemma or Grammatical-Category Disambiguation (S7): index 0 is the primary
stroke (with its star/hash mark), then alternate entries. Recomputed by every exporter;
`theory2.tsv` is a human view that nothing reads.
- Code: `Dictionary.buildFinalTheory` dictionary.py:342.
- Preferred over "final theory" (code name `finalTheory` only).
- First used in: Different-Lemma or Grammatical-Category Disambiguation (S7).

### Theory Export (S8)
The stage that renders theory 2 for its users, in two branches: the **Plover branch**
(Plover dictionary, key table, system plugin) and the **trainer branch** (keyboard legend,
word drill, sentences, definitions).
- Code: util/export_plover_dictionary.py, util/export_plover_system.py, util/export_keyboard_layout.py, util/export_practice_words.py, util/export_practice_sentences.py, util/export_definitions.py.
- Avoid "Theory Export (S5)".
- First used in: Theory Export (S8).

### Trainer data
A dataset state: the four steno-trainer JSON files (`keyboard-layout`, `practice-words`,
`practice-sentences`, `definitions`) under `steno-trainer/public/data/`; the output of the
trainer branch.
- First used in: Theory Export (S8).

### Undersampled lemma
A verb LemmeGramCat whose legacy discriminating-feature space is a strict subset of its
template siblings'; the trigger for verb paradigm completion.
- Code: `detectUndersampledLemmas` src/verbparadigm.py:681.
- First used in: Synthetic Lexicon Building (S2).

### Word
The lexicon entry dataclass `src.word.Word`. Its identity is a per-process salted hash of
`ortho`, `phonology`, `lemme`, `gramCat`, `gender` and `number`, stored in the pickles.
`lexique.py:547` defines an unrelated `Word` used only in Lexicon Building (S1).
- Code: src/word.py:28, :94, :155.
- First used in: Dictionary Loading (S3).

### Word list
A dataset state: all `src.word.Word`s after the identity merge (167,639), sorted by descending
film frequency; stored in `Dictionary.pickle`.
- Code: `Dictionary.readCorpus` dictionary.py:92.
- First used in: Dictionary Loading (S3).
