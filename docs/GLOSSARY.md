# Glossary

Canonical vocabulary for Stenalgo's code and docs, companion to [PIPELINE.md](PIPELINE.md).
When an entry names a **preferred synonym**, use the preferred word in new code, comments
and docs; the other entry is kept only so older prose (commit messages, RESUME notes,
planning docs) stays readable.

Each entry gives a plain definition, a code anchor, preferred/avoid notes where relevant,
and the pipeline stage where the term first matters. Stages and phases are always cited by
descriptive name with the code in parentheses, for example "Marker Grouping (Phase G)".

Entries marked **⚠ provisional — pending user decision** are picks made while merging the
per-stage call graphs, where the existing docs and code disagree. Their review question id
(a1, a2, …) points to `docs/refactor/callgraph/91-review-questions.md`.

---

### Alternate (press-set alternate)
One of several press-sets that each identify the same self-homograph spelling, one per
distinct reading; pressing any one of them is enough. Index 0 is the primary alternate.
- Code: `resolveGroupPressSets` src/elicitation.py:374; `buildKeypressGroupExtraAlternates` src/ambiguitychecker.py:844.
- First used in: Marker Elicitation (Phase E).

### Association (grapheme-phoneme association, `assoc`)
LexiqueInfra's column of `grapheme-phoneme` pairs joined by `.`, with `#` for a silent
letter. It is aligned onto the Lexique383 syllable skeleton to build a breakdown.
- Code: `resources/LexiqueInfraCorrespondance.tsv`; `fixLexiqueInfraGraphPhon` lexique.py:652.
- First used in: Lexicon Building (S1).

### Atomic feature
Old name for a marker.
- Code: `atomicFeatures` src/word.py:406.
- Preferred synonym: **Marker**. Avoid "atom" and "atomic feature" in new prose.
- First used in: Marker Elicitation (Phase E).

### Bare mark stroke
A trailing stroke that holds only reserved mark keys (rendered `*#`). Only escalated mark
codes produce one, for their second and later symbols.
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:444; util/_stenorender.py:11.
- First used in: Lemma-Homophone Marking (S4).

### Base strokes
A word's theory-1 Strokes: one stroke per syllable, no markers or marks.
- Code: `buildWordToStrokes` src/ambiguitychecker.py:553; `strokes` column of `theory2.tsv`.
- Preferred synonym for "phoneme strokes" and "theory-1 strokes". Keep "last phoneme
  stroke" for the specific stroke that receives a merged mark.
- First used in: Phonetic Theory Building (S2).

### Best permutation / pairwise order matrix
The left-to-right phoneme order per syllabic part that maximizes in-order biphoneme
frequency, and its per-pair `<`/`>`/`=` preferences with score differences. Computed on every
fresh rebuild but used only by the uncalled layout solver and the fallback keymap.
- Code: `BiphonemeCollection.optimizeOrder` src/grammar.py:318, `generateBiphonemeOrderMatrix` :361.
- First used in: Phonetic Theory Building (S2).

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
- First used in: Marker Stroke Realization (Phase P).

### Canonical form (of a Strokes)
A Strokes with each stroke's keys sorted and deduplicated: the chord as physically pressed.
Every collision test should compare this form, not the raw form.
- Code: `canonicalizeStrokes` src/keyboard.py:31.
- Contrast: **Raw Strokes**.
- First used in: Phonetic Theory Building (S2).

### Canonical member
The member of a homophone group or lemma-homophone cluster that gets no mark: the spelling
whose primary alternate is the empty press-set `∅` in Same-Lemma Disambiguation (S3), or the
rank-0 word with mark code `()` in Lemma-Homophone Marking (S4). In a homophone group it is
chosen by the elicitation answers, never computed.
- Code: `resolveGroupPressSets` src/elicitation.py:374; `assignStarHashCombos` src/ambiguitychecker.py:272.
- First used in: Marker Elicitation (Phase E).

### Canonical-only collision
Words in different theory-1 entries whose raw Strokes have the same canonical form, so they
type identically (233 canonical Strokes today, e.g. entre/heurte). Visible only after
canonicalization.
- Code: `canonicalizeStrokes` src/keyboard.py:31.
- First used in: Phonetic Theory Building (S2).

### Chord ⚠ provisional — pending user decision (a5)
Used for three things: a physical stroke (src/keyboard.py:21, Marker Stroke Realization
(Phase P) docstrings), an abstract keypress group (ATOMIC_KEYPRESS_REWIRE_PLAN.md:49), and a
trainer record (`Chord`, util/export_practice_sentences.py:50).
- Preferred synonym: **Stroke** for keys pressed together; **Keypress Group** for the
  abstract unit; **Drill item** for the trainer record. Avoid "chord" in new prose.
- First used in: Phonetic Theory Building (S2).

### Cluster ⚠ provisional — pending user decision (a1)
Has had three meanings: same-lemma homophones (the plan's vocabulary, now **Homophone
Group**), all words sharing one theory-1 stroke (`StrokeClusterReport`
src/ambiguitychecker.py:46, now **Theory-1 collision**), and a group of words of different
lemmas sharing a final stroke (`rankHomophoneCluster` :261, now **Lemma-homophone cluster**).
- Avoid bare "cluster"; use one of the three preferred terms.
- First used in: Phonetic Theory Building (S2).

### Coda / Onset / Nucleus (syllabic part)
The consonants after the first vowel, the consonants before it, and all the vowels of a
syllable. Each part maps to its own key bank. A syllable with no vowel puts all its
consonants in the onset.
- Code: `Syllable.__init__` src/grammar.py:499-518; `Phoneme.phonemesByPart` :35.
- First used in: Phonetic Theory Building (S2).

### Coda bank
The right-hand keys 16-25, which type coda consonants. Marker Stroke Realization (Phase P)
chooses marker keys only from this bank.
- Code: `keyIDinSyllabicPart` in `starboard3h.json`; util/build_phase_p_realization.py:4.
- First used in: Phonetic Theory Building (S2).

### Conjugation-marker legend
The trainer's table from keypress group to physical keys and French marker labels, read from
the realization report (not from the inline recompute).
- Code: `_conjugationMarkers` util/export_keyboard_layout.py:117.
- First used in: Theory Export (S5).

### Cross-category clash
Two colliding words with the same bare lemma but different grammatical category (appel NOM /
appelle VER). Their `lemmeGramCat`s differ, so Marker Stroke Realization (Phase P) ignores
them and Lemma-Homophone Marking (S4) marks them.
- Code: `crossCategoryClashCollisions` src/ambiguitychecker.py:1251; `detectCrossCategoryClash` :59 (diagnostic only).
- First used in: Marker Stroke Realization (Phase P).

### Cross-lemma collision
Two colliding words with different bare lemmas (ver/vert/verre). Left to Lemma-Homophone
Marking (S4).
- Code: `crossLemmaCollisions` src/ambiguitychecker.py:1255.
- First used in: Marker Stroke Realization (Phase P).

### Digraph subsumption
When the union of some phonemes' key tuples equals, or contains, another phoneme's tuple,
different phoneme sequences give the same physical stroke (coda `k`+`d` = `g`; onset `R` ⊂ `j`).
- Code: docstrings of the syllable-break exceptions, src/word.py:215-340.
- First used in: Phonetic Theory Building (S2).

### Discriminator
Pre-2026-09-18 name for a solver-chosen feature that separates homophones. Survives in
function names (`buildDiscriminatorSelection`) and in Synthetic Paradigm Completion (S1b)'s gating.
- Preferred synonym: **Marker** (the value) or **Press-set** (what is pressed). Avoid.
- First used in: Synthetic Paradigm Completion (S1b).

### Donor / ending table
The attested words of a verb template or NOM/ADJ ending class (donors), and the suffix
transformation learned from them by majority, with match rate and donor count, then spliced
onto a missing form.
- Code: `deriveConjugationEndingTables` src/verbparadigm.py:493; `deriveNomAdjEndingTables` src/nomAdjParadigm.py:250.
- First used in: Synthetic Paradigm Completion (S1b).

### Doublet (1990-reform spelling doublet)
The pre- and post-reform spellings of one lemma (259 pairs). They are merged and share one
mark code, so they are never marked against each other and may stay colliding.
- Code: `loadReform1990DoubletPairs` src/ambiguitychecker.py:94.
- First used in: Lemma-Homophone Marking (S4).

### Drill item
One `practice-words.json` record of the steno-trainer, keyed by (spelling, steno).
- Code: util/export_practice_words.py:225.
- Avoid "Chord" for it.
- First used in: Theory Export (S5).

### Elicitation answers
The person's recorded checkbox answers, one per opposition: the only hand-authored input of
Same-Lemma Disambiguation (S3). A dataset state.
- Code: `elicitation_answers.json`; `AnsweredOpposition` src/elicitation.py:266.
- First used in: Marker Elicitation (Phase E).

### Escalated code
A mark code past the four-code budget `()`, `*`, `#`, `*#`: `*#` repeated n ≥ 2 times. Its
second and later symbols become bare mark strokes.
- Code: `assignStarHashCombos` src/ambiguitychecker.py:272.
- First used in: Lemma-Homophone Marking (S4).

### Excluded word
A spelling listed in `excluded_words.txt` (44 today), dropped when the Word list is read.
Distinct from a lexicon exclusion.
- Code: `Dictionary.readCorpus` dictionary.py:102.
- First used in: Phonetic Theory Building (S2).

### Extra stroke ⚠ provisional — pending user decision (a8)
Umbrella word for any stroke appended after a word's base strokes. Three kinds exist.
- Preferred synonym: say which one — **Marker stroke** (the coda-bank stroke of Marker
  Stroke Realization (Phase P)), **Bare mark stroke** (Lemma-Homophone Marking (S4)) or
  alternate stroke (a self-homograph's extra theory-2 entry). Avoid "trailing stroke" and
  "coda stroke".
- Code: `_appendCodaExtraStroke` src/ambiguitychecker.py:892.
- First used in: Marker Stroke Realization (Phase P).

### Feature Combination ⚠ provisional — pending user decision (a2)
The type name for a reading (`FeatureCombination`, a `frozenset[str]` of markers).
- Code: `FeatureCombination` src/elicitation.py:27; `wordFeatureCombinations` :30.
- Preferred synonym: **Reading** (provisional; the root GLOSSARY.md preferred the opposite).
- First used in: Marker Elicitation (Phase E).

### Film frequency
`Word.frequency`, which is the film-subtitle frequency only (`freqfilms2`); book frequency is
read but never used. It drives every frequency rule and every "keep the most frequent" choice.
- Code: src/word.py:93.
- First used in: Phonetic Theory Building (S2).

### Final induced strokes
A dataset state: every Word's base strokes plus at most one marker stroke, before
Lemma-Homophone Marking (S4). `dict[Word, Strokes]`.
- Code: `buildFinalInducedStrokes` src/ambiguitychecker.py:1261.
- Avoid "finalInduced" in prose.
- First used in: Marker Stroke Realization (Phase P).

### Finalized word
A Word whose keypress groups have all been given keys, so its composed marker stroke can no
longer change; later candidates are checked against it.
- Code: `_finalizeReadyWords` src/ambiguitychecker.py:1066.
- First used in: Marker Stroke Realization (Phase P).

### Fix script
A one-shot `util/fix*.py` lexicon patch: dry run by default, `--apply` writes.
- Preferred over "fixer".
- First used in: Lexicon Building (S1).

### Frequency-ratio rule (R4) ⚠ provisional — pending user decision (a9)
Rule R4 of the marking rule stack: when one word's film frequency is at least 10 times the
other's (or the other is 0), the rarer word is marked, without looking at categories.
- Code: `RATIO_EXEMPTION_THRESHOLD` src/ambiguitychecker.py:91; `decideStarHashMark` :221-225.
- Avoid "10x ratio exemption" / "frequency-ratio exemption" (code and ROADMAP.md wording):
  the pair is still marked; only the category rule is skipped.
- First used in: Lemma-Homophone Marking (S4).

### Frequent words
The 200 top spellings of `resources/top500_film.txt`. They get weight 0 in the syllable
statistics and in the keypress usage weights.
- Code: `Dictionary.frequentWords` dictionary.py:63; src/elicitation.py:615.
- First used in: Phonetic Theory Building (S2).

### Gemini PR keymap
The mapping from Stenalgo key names to Gemini PR wire labels, taken from hardware sniffing.
Keys 0, 1, 2 and 10 are sent as number-bar bits; key 15 (`#`) is the only star bit.
- Code: `GEMINI_PR_LABELS` util/export_plover_system.py:28.
- First used in: Theory Export (S5).

### GramCat
The grammatical category enum: 22 values such as `NOM`, `VER`, `ADJ:pos` (CLAUDE.md says 21).
- Code: src/word.py:10.
- First used in: Phonetic Theory Building (S2).

### Group shape ⚠ provisional — pending user decision (a4)
A homophone group reduced to its set of per-spelling alternate sets, with spellings,
strokes and lemmas removed. Groups with the same shape pose the same grouping problem (294
shapes for 47,828 groups).
- Code: `GroupSignature` src/phasegsat.py:37; `groupSignatures` :40.
- Avoid "signature".
- First used in: Marker Grouping (Phase G).

### Hard grouping rule / soft preference tier
Marker Grouping (Phase G) constraints that may raise K (`ALONE_KEYS`, `MUST_DIFFER_GROUPS`)
versus lexicographic preferences applied at the fixed minimum K (`PREFERENCE_TIERS`).
- Code: util/build_phase_g_assignment.py:39-45.
- First used in: Marker Grouping (Phase G).

### Homograph / Self-homograph
Two Words with the same spelling; they type the same text, so they are never separated. A
**self-homograph** is one spelling with several readings inside one homophone group
("calmez": impératif or indicatif 2p); it gets one alternate per reading.
- Code: `decideStarHashMark` rule R1 src/ambiguitychecker.py:211; `resolveGroupPressSets` src/elicitation.py:374.
- First used in: Marker Elicitation (Phase E).

### Homophone Group
Words with the same `LemmeGramCat` and the same canonical Strokes: forms of one paradigm
that sound alike (dors/dort). The unit of Same-Lemma Disambiguation (S3); the dataset state
"homophone groups" holds all 47,830 of them.
- Code: `buildLemmaHomophoneGroups` src/elicitation.py:61; `LemmaHomophoneGroupKey` :24 (named "lemma" but keyed by LemmeGramCat).
- Avoid "cluster" and "same-lemma homophone group" (redundant).
- First used in: Marker Elicitation (Phase E).

### Identity merge
`readCorpus` folding a later lexicon row with an already-seen Word identity into the first
Word. Only the verb tags are merged; the first row's syllabification and frequency win.
- Code: dictionary.py:113-137; `Word.mergeInfoVerb` src/word.py:129.
- First used in: Phonetic Theory Building (S2).

### Illegal stroke ⚠ provisional — pending user decision (a5)
A stroke (canonical key set) that no finger assignment of the keyboard can press:
`getStrokeCost` returns `None`. 529 Words contain one (mostly "-isme").
- Code: `Keyboard.getStrokeCost` src/keyboard.py:547.
- Avoid "illegal chord".
- First used in: Phonetic Theory Building (S2).

### Implicit-hyphen key
A key whose presence in a stroke makes Plover's `-` separator before the right bank
unnecessary. Here: nucleus keys 11-14 and `*` (10).
- Code: util/export_plover_system.py:44; util/_stenorender.py:27.
- First used in: Theory Export (S5).

### In-scope collision ⚠ provisional — pending user decision (a11)
Code name for a same-lemmeGramCat collision.
- Code: `_isInScopeCollision` src/ambiguitychecker.py:968.
- Preferred synonym: **Same-lemmeGramCat collision**.
- First used in: Marker Stroke Realization (Phase P).

### Induced press-set
Every marker asserted when a spelling's markers are pressed through their keypress groups:
the union of all markers of the groups touched.
- Code: `inducedPressSet` src/phaseg.py:135.
- First used in: Marker Grouping (Phase G).

### Inline path / report build
The two call sites of Marker Stroke Realization (Phase P). The inline path runs inside
`Dictionary.buildFinalTheory` and feeds theory 2 and all exports; the report build
(`util/build_phase_p_realization.py`) writes only the realization report.
- Code: dictionary.py:373-389; util/build_phase_p_realization.py:38.
- First used in: Marker Stroke Realization (Phase P).

### K
The number of keypress groups found by Marker Grouping (Phase G): the smallest number that
is feasible under the hard grouping rules. Currently 7 (CLAUDE.md still says 5).
- Code: `keypressCount` in `phase_g_keypress_assignment.json`; `minKeypressesSat` src/phasegsat.py:417.
- First used in: Marker Grouping (Phase G).

### Keyboard layout
A dataset state: the `Starboard` loaded from `starboard3h.json`, mapping phonemes to key
tuples per syllabic bank. Never rewritten by the pipeline.
- Code: `Keyboard.fromJSONFile` src/keyboard.py:252.
- First used in: Phonetic Theory Building (S2).

### Keyboard Layout Optimization (S2b)
The CP-SAT phoneme-to-key solver (ambiguity, ergonomics and order terms). Not run; its past
output is `starboard3h.json`.
- Code: `optimizeKeyboard` src/cpsatsolver.py:13 (call commented out at dictionary.py:494).
- First used in: Phonetic Theory Building (S2).

### Keypress ⚠ provisional — pending user decision (a3)
In code, the type alias for a *physical* key combination under one finger
(`Keypress: TypeAlias = tuple[int, ...]`, used by `PositionWeights`). The plan and Marker
Grouping (Phase G) docstrings also use it for the abstract unit.
- Code: src/keyboard.py:26.
- Keep "Keypress" for the keyboard.py type only; for the abstract unit use **Keypress Group**.
- First used in: Phonetic Theory Building (S2).

### Keypress conflict
Two different spellings of one homophone group that induce the same set of keypress groups
after markers are bundled. Any conflict aborts Marker Grouping (Phase G)'s write.
- Code: `KeypressConflict` src/phaseg.py:150.
- First used in: Marker Grouping (Phase G).

### Keypress Group ⚠ provisional — pending user decision (a3)
One output unit of Marker Grouping (Phase G): an integer id and the markers it carries;
pressing it asserts all of them. Marker Stroke Realization (Phase P) gives each one physical
coda keys. The dataset state "keypress groups" holds all K of them.
- Code: `markersByKeypress` in `phase_g_keypress_assignment.json`; `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904.
- Preferred over "keypress" and "chord" for the abstract unit.
- First used in: Marker Grouping (Phase G).

### Keypress group population
A dataset state: the Words that need each keypress group (from their primary alternate),
plus each self-homograph Word's extra alternate group sets.
- Code: `buildKeypressGroupToWords` src/ambiguitychecker.py:803; `buildKeypressGroupExtraAlternates` :844.
- First used in: Marker Stroke Realization (Phase P).

### Last phoneme stroke
The last of a word's base strokes. The first symbol of its mark code is pressed together
with it (a merged mark), even when a marker stroke follows.
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:437-444.
- First used in: Lemma-Homophone Marking (S4).

### Layout entry / shared layout entry
One `phonemesAssignedToStroke` item: a key tuple within one syllabic bank and the phonemes it
types (48 today). A shared layout entry types two or more phonemes of the same part (key 9 =
`w`/`N`/`G`).
- Code: `starboard3h.json`; src/keyboard.py:466.
- First used in: Phonetic Theory Building (S2).

### Lemma-homophone
Homophones whose `lemmeGramCat` differs (different lemma, or same lemma in another category).
- Code: the "≥2 distinct `lemmeGramCat`" filter, src/ambiguitychecker.py:402.
- First used in: Lemma-Homophone Marking (S4).

### Lemma-homophone cluster ⚠ provisional — pending user decision (a1)
The unit of Lemma-Homophone Marking (S4): Words sharing one canonical final induced stroke,
with at least 2 `lemmeGramCat`s and 2 spellings (4,450 today).
- Code: `groupHomophonesByReservedStroke` src/ambiguitychecker.py:380; `rankHomophoneCluster` :261.
- Avoid "homophone group" for it (that is the same-`lemmeGramCat` unit).
- First used in: Lemma-Homophone Marking (S4).

### Lemma-Homophone Marking (S4)
The stage that adds `*`/`#` marks to words that still collide after Marker Stroke
Realization (Phase P) with a different `lemmeGramCat`, producing theory 2. Its scope also
covers same-lemma cross-category clashes; the name is under review (question b2).
- Code: `composeReservedKeyStrokes` src/ambiguitychecker.py:410, called from `Dictionary.buildFinalTheory` dictionary.py:385.
- Avoid "`*`/`#` track", "cross-lemma track", "reserved-key track".
- First used in: Lemma-Homophone Marking (S4).

### Lemme / LemmeGramCat
The lemma string, and the key `"lemme_GramCat"` (`rucher_NOM`) that almost every "same-lemma"
test actually uses. `groupWordsByLemme` groups by LemmeGramCat; `groupWordsByBareLemme` by
bare lemme.
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

### Live marker / unpressable marker
A marker that appears in at least one resolved press-set (13 today), versus one that never
does (7) and is left out of Marker Grouping (Phase G).
- Code: `liveMarkers` src/phaseg.py:63.
- First used in: Marker Grouping (Phase G).

### Mark ⚠ provisional — pending user decision (a7)
The `*`/`#` symbols Lemma-Homophone Marking (S4) adds to separate lemma-homophones. Not to be
confused with a **marker** (a grammatical value).
- Code: `STAR_KEY` = 10, `HASH_KEY` = 15, src/ambiguitychecker.py:351-352.
- Avoid "marker" for a `*`/`#` symbol, and "mark" for a grammatical value.
- First used in: Lemma-Homophone Marking (S4).

### Mark code / merged mark / merged mark stroke
A mark code is a symbolic tuple such as `()`, `('*',)` or `('*#','*#')` given to one rank of a
lemma-homophone cluster. The **merged mark** is its first symbol pressed with the last
phoneme stroke; the **merged mark stroke** is that stroke's rendered form (`*iel`, `ie#l`,
`pvR-#`).
- Code: `assignStarHashMarks` src/ambiguitychecker.py:292; `_renderMarkedStroke` util/_stenorender.py:26.
- First used in: Lemma-Homophone Marking (S4).

### Mark representative
The most frequent member of a merged homograph/doublet group inside a lemma-homophone
cluster. Only representatives are ranked; every member takes its code.
- Code: `assignStarHashMarks` src/ambiguitychecker.py:311, :332.
- First used in: Lemma-Homophone Marking (S4).

### Marker ⚠ provisional — pending user decision (a6)
One grammatical value that a writer can assert with a press: `pers_2`, `nbr_p`,
`subjonctif`, `f`, …
- Code: ATOMIC_KEYPRESS_REWIRE_PLAN.md:44; `Word.splitInfoVerb` src/word.py:102.
- Preferred over "atom", "atomic feature", "feature" (legacy `WordFeature`, which also covers
  compound features like `ind:pre:3s`) and "discriminator".
- First used in: Marker Elicitation (Phase E).

### Marker Elicitation (Phase E)
The first phase of Same-Lemma Disambiguation (S3): builds homophone groups and questionnaire
items, and resolves the stored elicitation answers into resolved press-sets. In a rebuild it
asks nothing.
- Code: `python -m src.elicitation`, src/elicitation.py:527.
- First used in: Marker Elicitation (Phase E).

### Marker Grouping (Phase G)
The second phase of Same-Lemma Disambiguation (S3): packs the live markers into the minimum
number K of keypress groups so no two spellings of a homophone group press the same thing.
- Code: util/build_phase_g_assignment.py:49; `minKeypressesSatWithPriorities` src/phasegsat.py:490.
- First used in: Marker Grouping (Phase G).

### Marker stroke ⚠ provisional — pending user decision (a8)
The single extra coda-bank stroke that Marker Stroke Realization (Phase P) appends after a
word's base strokes: the union of the chosen keys of every keypress group the word needs.
- Code: `_appendCodaExtraStroke` src/ambiguitychecker.py:892.
- Avoid "Phase P stroke", "coda extra stroke", "trailing stroke".
- First used in: Marker Stroke Realization (Phase P).

### Marker Stroke Realization (Phase P)
The third phase of Same-Lemma Disambiguation (S3): gives each keypress group a coda-bank
key-set and appends one marker stroke per marked word. Runs on two paths (inline path and
report build).
- Code: `realizeKeypressGroupsAsExtraStroke` src/ambiguitychecker.py:987.
- First used in: Marker Stroke Realization (Phase P).

### Marking rule stack (R1-R7) ⚠ provisional — pending user decision (a10)
The ordered pairwise rules that decide which of two lemma-homophones is marked: R1 homograph
exemption, R2 reform-doublet exemption, R3 per-pair override, R4 frequency-ratio rule, R5
same-category rule, R6 category-priority rule, R7 frequency fallback. The first match decides.
- Code: `decideStarHashMark` src/ambiguitychecker.py:183-232.
- Cite rules by name; comments at :392/:431 and RESUME_2026-09-20-starhash-priority.md use
  another numbering (ratio = Rule 1, homograph = Rule 2, doublet = Rule 3).
- First used in: Lemma-Homophone Marking (S4).

### Mixed lexicon
A dataset state: `resources/LexiqueMixte.tsv`, 136,456 rows × 12 columns (rows, not distinct words).
- Code: `outputMixedLexique` lexique.py:1174.
- First used in: Lexicon Building (S1).

### Onset-only stroke (vowel-less syllable)
The stroke of a syllable with no vowel: all its consonants go to the onset bank. Comes from
the syllable-break exceptions and, unintentionally, from many synthetic rows.
- Code: src/grammar.py:499.
- First used in: Phonetic Theory Building (S2).

### Opposition / tie opposition / unresolved opposition
An **opposition** is an unordered pair of different readings of two spellings in one homophone
group — the unit a questionnaire item asks about. A **tie opposition** pairs two spellings with
the same reading (no marker can separate them; skipped). An **unresolved opposition** has no
answer, or disagreeing answers; its whole group is dropped.
- Code: `OppositionSample` src/elicitation.py:99; `AnswerByOpposition` :276; :356-363.
- First used in: Marker Elicitation (Phase E).

### Phoneme
A single-character X-SAMPA sound: 16 nucleus (vowel) and 20 consonant symbols, plus a
temporary `x`. A `Biphoneme`/`Multiphoneme` is a sequence of phonemes within one syllabic part.
- Code: src/grammar.py:16, :32-33.
- First used in: Phonetic Theory Building (S2).

### Phonetic stroke rule
How a syllable becomes a stroke: each phoneme's layout key tuple for its part, concatenated
onset → nucleus → coda in spoken order, kept raw.
- Code: `Starboard.getStrokeOfSyllableByPart` src/keyboard.py:607.
- First used in: Phonetic Theory Building (S2).

### Phonetic Theory Building (S2)
The stage that reads both lexicons into the Word list and maps each Word to its base strokes
on the adopted layout, producing theory 1.
- Code: `python dictionary.py`, dictionary.py:448.
- First used in: Phonetic Theory Building (S2).

### Physical keypress assignment
A dataset state: the chosen coda keys per keypress group, their costs and alternates, the
unassigned groups and the residual-collision buckets.
- Code: `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904.
- First used in: Marker Stroke Realization (Phase P).

### Plover dictionary / Plover key table
The RTFCRE-steno → spelling JSON used by Plover (`plover_stenalgo_dictionary.json`, 163,238
entries), and the generated module of key names, implicit-hyphen keys and Gemini PR keymap
(`_generated_keys.py`) used by the `plover_stenalgo` system plugin.
- Code: util/export_plover_dictionary.py:35; util/export_plover_system.py:38.
- First used in: Theory Export (S5).

### Precedence spec
`conjugation_disambiguation_order.txt`: the ordered marker combinations and special rules
that express intended precedence. Authoritative intent, but the code only partly checks it
and never enforces the order.
- Code: `parsePrecedenceOrder` util/check_conjugation_disambiguation_order.py:43.
- First used in: Marker Elicitation (Phase E).

### Preferred key
A human-chosen key-set for the keypress group holding a given marker (impératif → 18,
pers_2 → 19, pers_3 → 20); it wins whenever it is feasible.
- Code: `PREFERRED_KEYS_BY_MARKER` src/ambiguitychecker.py:945.
- First used in: Marker Stroke Realization (Phase P).

### Press-set
The set of markers a writer presses, beyond the sound strokes, to get one spelling. The empty
set `∅` marks the canonical member.
- Code: `AnsweredOpposition.pressA`; `resolveGroupPressSets` src/elicitation.py:374.
- Preferred over **Signature**.
- First used in: Marker Elicitation (Phase E).

### Press-set conflict
Two different spellings of one homophone group holding the same resolved press-set; the group
is dropped.
- Code: `GroupConflict` src/elicitation.py:414.
- Preferred over "group conflict".
- First used in: Marker Elicitation (Phase E).

### Primary alternate
Index 0 of a spelling's sorted alternates (smallest press-set first). Only the primary drives
Marker Stroke Realization (Phase P)'s key search; the others become alternate strokes.
- Code: src/elicitation.py:404-407; `buildKeypressGroupToWords` src/ambiguitychecker.py:832.
- First used in: Marker Elicitation (Phase E).

### Pronoun paradigm lemma
The fold of pronoun lemmas into one paradigm (`ils→il`, `elles→elle`, `ceux→celui`), so their
forms are separated by Same-Lemma Disambiguation (S3).
- Code: `pronounParadigmLemme` lexique.py:81.
- First used in: Lexicon Building (S1).

### Questionnaire item
One opposition shown with an example pair of spellings (200 today); the dataset state
"questionnaire items" is persisted as `questionnaire.json`.
- Code: `QuestionnaireItem` src/elicitation.py:210.
- First used in: Marker Elicitation (Phase E).

### Raw lexicon rows
A dataset state: `list[lexique.Word]` read from Lexique383 (a different dataclass from `src.word.Word`).
- Code: `Lexique.read_corpus` lexique.py:966; lexique.py:547.
- First used in: Lexicon Building (S1).

### Raw Strokes
The theory-1 key form: per syllable, each phoneme's full layout key tuple concatenated in
onset → nucleus → coda and spoken order, repeats kept. Theory 1 is keyed on it.
- Code: `getStrokeOfSyllableByPart` src/keyboard.py:607.
- Contrast: **Canonical form**. Say "raw" whenever a count or equality is taken on theory-1 keys.
- First used in: Phonetic Theory Building (S2).

### Reading ⚠ provisional — pending user decision (a2)
One grammatical analysis of a spelling, as a set of markers ("parle" = 1s or 3s présent).
Participle readings include gender and number; a Word without verb tags has one reading
{gender, number}.
- Code: `wordFeatureCombinations` src/elicitation.py:30; `readings` in `resolved_press_sets.json`; `type Reading` util/export_practice_words.py:70.
- Preferred over **Feature Combination** (provisional; reverses the root GLOSSARY.md).
- First used in: Phonetic Theory Building (S2) (verb tags merged per Word).

### Realization report ⚠ provisional — pending user decision (b4)
`phase_p_keypress_realization.json`: the tracked output of Marker Stroke Realization
(Phase P)'s report build (chosen keys, costs, alternates, residual buckets). Read only by the
trainer keyboard legend.
- Code: util/build_phase_p_realization.py:38.
- Avoid "Phase P report", "reference artifact".
- First used in: Marker Stroke Realization (Phase P).

### Reform rewrite / reform lemma normalization
A **reform rewrite** is an output-time 1990-reform change to `ortho`/`orthosyll_cv` (ortho
rule, -eler/-eter, loanword plural, two one-offs), never to `phon`. **Reform lemma
normalization** changes only `lemme`, at read time.
- Code: lexique.py:1197-1244; `normalizeLemme` lexique.py:540.
- First used in: Lexicon Building (S1).

### Reserved keys
Starboard keys 0, 1, 10 and 15, excluded from phonemes. 10 (`*`) and 15 (`#`) carry marks;
0 and 1 are held for a possible third mark. They are not "control" keys.
- Code: `_reservedKeys` src/keyboard.py:320; src/ambiguitychecker.py:351-352.
- First used in: Phonetic Theory Building (S2).

### Residual collision
Two different words still sharing a final stroke after Marker Stroke Realization (Phase P),
in one of four buckets: theory (a marked stroke equals a theory-1 key), same-lemmeGramCat,
cross-category clash, or cross-lemma collision.
- Code: `KeypressGroupPhysicalAssignment` src/ambiguitychecker.py:904; :1219-1258.
- First used in: Marker Stroke Realization (Phase P).

### Resolved press-sets
A dataset state: for every homophone group, each spelling's list of alternate press-sets,
plus frequencies and readings (47,828 groups; `resolved_press_sets.json`, gitignored).
- Code: `resolveGroupPressSets` src/elicitation.py:374; `serializeResolvedPressSets` :471; `PressSetsByGroup` src/phaseg.py:27.
- First used in: Marker Elicitation (Phase E).

### RTFCRE
Plover's steno string notation: `/` between strokes, `-` before right-bank keys when no
implicit-hyphen key is present.
- Code: `renderFinalStrokesToRTFCRE` util/_stenorender.py:39.
- First used in: Theory Export (S5).

### Same-lemmeGramCat collision ⚠ provisional — pending user decision (a11)
Two Words with different spellings, the same `lemmeGramCat` and the same final stroke — the
only collision Marker Stroke Realization (Phase P) blocks. Its invariant ("0 residual
same-lemmeGramCat collisions") is checked by the report build only.
- Code: `_isInScopeCollision` src/ambiguitychecker.py:968; `residualCollisions` :1248.
- Preferred over "in-scope collision".
- First used in: Marker Stroke Realization (Phase P).

### Same-Lemma Disambiguation (S3)
The stage that separates words sharing both a `lemmeGramCat` and a stroke, with elicited
markers realized as coda keys. Contains Marker Elicitation (Phase E), Marker Grouping
(Phase G) and Marker Stroke Realization (Phase P). The name is under review (question b1),
because "lemma" here means lemma + category.
- First used in: Same-Lemma Disambiguation (S3).

### Signature ⚠ provisional — pending user decision (a4)
Two unrelated uses: the root GLOSSARY.md's old name for a press-set (its definition, a union
across readings, is stale since per-reading alternates), and `GroupSignature`, a group's shape.
- Preferred synonym: **Press-set** for what is pressed; **Group shape** for `GroupSignature`. Avoid "signature".
- First used in: Marker Grouping (Phase G).

### Source lexicons
A dataset state: the external input files `Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`,
`reform1990.tsv`, `lexiconExclusions.tsv` and Verbiste XML, patched in place by fix scripts.
- First used in: Lexicon Building (S1).

### Spelling twins
Two or more Words in one homophone group with the same spelling and `lemmeGramCat` but a
different identity ("finis" participle m:p and "finis" finite form). Marker Elicitation
(Phase E) merges them into one spelling; Marker Stroke Realization (Phase P) marks only the first.
- Code: `_resolveEntryWord` src/ambiguitychecker.py:776.
- First used in: Marker Elicitation (Phase E).

### Starboard
The 26-key target keyboard; its layout is `starboard3h.json`.
- Code: `Starboard` src/keyboard.py:290.
- First used in: Phonetic Theory Building (S2).

### Stroke / Strokes ⚠ provisional — pending user decision (a5)
A `Stroke` is the key indices pressed at once (one per syllable, plus marker and mark strokes);
`Strokes` is the tuple of strokes for a whole word.
- Code: src/keyboard.py:27-28.
- Preferred over "chord" for physically simultaneous keys; use **key-set** for a set of keys
  that forms part of a stroke (a candidate key-set).
- First used in: Phonetic Theory Building (S2).

### Syllabic-part ambiguity
The word frequency that would become indistinguishable if two whole onset/nucleus/coda
phoneme groups shared a key set: the solver's ambiguity input. Off the live path.
- Code: `lexicalSyllabicPartAmbiguityScore` src/grammar.py:975.
- First used in: Phonetic Theory Building (S2).

### Syllable
Onset + nucleus + coda, parsed from `syll_cv`; each becomes one stroke.
- Code: `Syllable` src/grammar.py:422; `Word.phonemesToSyllableNames` src/word.py:341.
- First used in: Lexicon Building (S1).

### Syllable-break exception
One of four `Word.fix_*` rewrites that move a syllable boundary for steno reasons, not
phonology (e+n repair, -rdre, -ayer conditionnel, -uer glide).
- Code: src/word.py:202-340.
- First used in: Phonetic Theory Building (S2).

### Syllable statistics
A dataset state: the `SyllableCollection` and the `Syllable` class-level phoneme, biphoneme
and multiphoneme collections. Only the syllable lookup feeds theory 1.
- Code: `analyseSyllabification` dictionary.py:169.
- First used in: Phonetic Theory Building (S2).

### Synthetic Paradigm Completion (S1b)
The manual side branch of Lexicon Building (S1): scripts that generate missing verb, noun and
adjective forms and append them to `LexiqueSynthetic.tsv`. Never run in a rebuild.
- Code: util/completeVerbParadigms.py:350; util/generateMissingNomAdjForms.py:99.
- First used in: Synthetic Paradigm Completion (S1b).

### Synthetic row (synthetic lexicon rows)
A generated lexicon row in `resources/LexiqueSynthetic.tsv` (`source=synthetic`, frequency 0;
42,225 rows). Read after the mixed lexicon by Phonetic Theory Building (S2).
- Code: `writeSynthetic` util/completeVerbParadigms.py:324; dictionary.py:66-69.
- First used in: Synthetic Paradigm Completion (S1b).

### Theory 1
Every Word's base strokes, grouped by raw Strokes (`dict[Strokes, list[Word]]`, 80,725
entries), with no disambiguation. Persisted as `FirstTheory.pickle`; human view `theory.tsv`.
- Code: `Dictionary.buildTheory` dictionary.py:305.
- Preferred over "first theory".
- First used in: Phonetic Theory Building (S2).

### Theory-1 collision ⚠ provisional — pending user decision (a1)
A theory-1 entry holding two or more distinct spellings (41,640 today): the raw-key meaning of
"homophones" in Phonetic Theory Building (S2).
- Code: `StrokeClusterReport` src/ambiguitychecker.py:46 (diagnostic).
- Avoid "stroke cluster".
- First used in: Phonetic Theory Building (S2).

### Theory-1 entry
One (raw Strokes, list[Word]) item of theory 1; its list is frequency-descending.
- Code: dictionary.py:312.
- First used in: Phonetic Theory Building (S2).

### Theory 2
Every Word's final Strokes list after Same-Lemma Disambiguation (S3) and Lemma-Homophone
Marking (S4): index 0 is the primary (marked) stroke, then self-homograph alternate strokes.
Recomputed by every exporter; `theory2.tsv` is a human view that nothing reads.
- Code: `Dictionary.buildFinalTheory` dictionary.py:342.
- Preferred over "final theory" (code name `finalTheory` only).
- First used in: Lemma-Homophone Marking (S4).

### Theory Export (S5)
The stage that renders theory 2 into the Plover dictionary, the Plover key table and plugin,
and the steno-trainer data.
- Code: util/export_plover_dictionary.py, util/export_plover_system.py, util/export_keyboard_layout.py, util/export_practice_words.py, util/export_practice_sentences.py, util/export_definitions.py.
- First used in: Theory Export (S5).

### Trainer data
A dataset state: the four steno-trainer JSON files (`keyboard-layout`, `practice-words`,
`practice-sentences`, `definitions`) under `steno-trainer/public/data/`.
- First used in: Theory Export (S5).

### Undersampled lemma
A verb LemmeGramCat whose legacy discriminating-feature space is a strict subset of its
template siblings'; the trigger for verb paradigm completion.
- Code: `detectUndersampledLemmas` src/verbparadigm.py:681.
- First used in: Synthetic Paradigm Completion (S1b).

### Word
The lexicon entry dataclass `src.word.Word`. Its identity is a per-process salted hash of
`ortho`, `phonology`, `lemme`, `gramCat`, `gender` and `number`, stored in the pickles.
`lexique.py:547` defines an unrelated `Word` used only in Lexicon Building (S1).
- Code: src/word.py:28, :94, :155.
- First used in: Phonetic Theory Building (S2).

### Word list
A dataset state: all `src.word.Word`s after the identity merge (167,639), sorted by descending
film frequency; stored in `Dictionary.pickle`.
- Code: `Dictionary.readCorpus` dictionary.py:92.
- First used in: Phonetic Theory Building (S2).
