# Phonetic Theory Building (S2)

Per-stage call graph, Pass 1b. Branch `docs-refactor` at 5ae0118. All anchors were checked
against the code. Sizes come from read-only probes of the current `Dictionary.pickle`,
`FirstTheory.pickle` (both 2026-09-22 20:1x), the two lexicon TSVs and `starboard3h.json`.
Terms follow `00-skeleton.md` §3 (dataset states) and §4 (glossary). New terms are defined
at the end.

## Overview

```
S2   Phonetic Theory Building — dictionary.py __main__ (dictionary.py:448)
├─ S2.1  Dictionary cache check — __main__ (dictionary.py:451)
├─ S2.2  Dictionary construction — Dictionary.__init__ (dictionary.py:76)
│  └─ S2.2.1  Lexicon reading and identity merge — Dictionary.readCorpus (dictionary.py:92)
│     ├─ S2.2.1.1  Word construction — Word.__post_init__ (src/word.py:84)
│     │  ├─ S2.2.1.1.1  e+n syllable repair — Word.fix_e_n_en (src/word.py:202)
│     │  ├─ S2.2.1.1.2  -rdre infinitive split — Word.fix_rdre_coda_syllable_break (src/word.py:215)
│     │  ├─ S2.2.1.1.3  -ayer conditionnel split — Word.fix_ayer_conditionnel_onset_glide (src/word.py:248)
│     │  └─ S2.2.1.1.4  -uer glide split — Word.fix_glide_low_vowel_syllable_break (src/word.py:297)
│     └─ S2.2.1.2  Reading fold-in — Word.mergeInfoVerb (src/word.py:129)
├─ S2.3  Syllable inventory — Dictionary.analyseSyllabification (dictionary.py:169)
│  ├─ S2.3.1  Syllable registration — SyllableCollection.updateSyllable (src/grammar.py:803)
│  │  ├─ S2.3.1.1  Onset/nucleus/coda decomposition — Syllable.__init__ (src/grammar.py:468)
│  │  └─ S2.3.1.2  Frequency accumulation — Syllable.increaseSpellingFrequency (src/grammar.py:586)
│  └─ S2.3.2  Collection sorting — Syllable.sortPhonemesCollections (src/grammar.py:592)
├─ S2.4  Phoneme order search — Syllable.optimizeBiphonemeOrder (src/grammar.py:644)
│  ├─ S2.4.1  Best permutation — BiphonemeCollection.optimizeOrder (src/grammar.py:318)
│  └─ S2.4.2  Pairwise order matrix — BiphonemeCollection.generateBiphonemeOrderMatrix (src/grammar.py:361)
├─ S2.5  Ambiguity statistics — Dictionary.analyseAmbiguities (dictionary.py:183)
│  ├─ S2.5.1  Syllabic phoneme ambiguity — SyllableCollection.analysePhonemSyllabicAmbiguity (src/grammar.py:1032)
│  ├─ S2.5.2  Lexical phoneme ambiguity — SyllableCollection.analysePhonemeLexicalAmbiguity (src/grammar.py:1098)
│  └─ S2.5.3  Syllabic-part ambiguity — SyllableCollection.analyseMultiphonemeLexicalAmbiguity_serial (src/grammar.py:1138)
├─ S2.6  Dictionary cache write — pickle.dump ×5 (dictionary.py:467-472)
├─ S2.7  Keyboard layout loading — Keyboard.fromJSONFile (src/keyboard.py:252)
├─ S2.8  Fallback keymap (only if starboard3h.json is missing) — Dictionary.generateBaseKeymap (dictionary.py:212)
├─ S2.9  Keyboard Layout Optimization (S2b, not run) — optimizeKeyboard (src/cpsatsolver.py:13)
├─ S2.10 Theory-1 cache check — __main__ (dictionary.py:498)
├─ S2.11 Theory 1 construction — Dictionary.buildTheory (dictionary.py:305)
│  └─ S2.11.1 Phonetic stroke rule — Starboard.getStrokeOfSyllableByPart (src/keyboard.py:607)
├─ S2.12 Theory-1 report — Dictionary.writeTheory (dictionary.py:317)
└─ S2.13 Theory-1 cache write — pickle.dump (dictionary.py:504)
```

Phonetic Theory Building (S2) reads the mixed lexicon (136,456 rows) and the synthetic
lexicon rows (42,225 rows) and turns them into the **Word list**: 167,639 Words, sorted by
descending film frequency. It then registers every spoken syllable (5,866 distinct) in the
**syllable statistics**. It loads the committed **keyboard layout** (`starboard3h.json`)
and maps every Word to its base strokes: one Stroke per syllable. The result is **theory
1**, `dict[Strokes, list[Word]]` with 80,725 entries. Every Word whose raw Strokes match
lands in the same entry. That is the only place where "homophones" come into existence in
this stage. Everything later (Same-Lemma Disambiguation (S3), Lemma-Homophone Marking (S4),
Theory Export (S5)) starts from theory 1. The layout optimizer and the three statistics
passes (S2.4, S2.5) still run on every fresh rebuild. None of their output reaches theory 1
or any live consumer. They exist for the layout solver, which is not called.

### The phonetic stroke rule, and how two words end up with the same Strokes

1. **Syllables come from the lexicon.** Each Word's `syll_cv` (e.g. `p_E_R|d_R_#`) is split
   on `|` into syllables and on `_` into phonemes. The silent marker `#` is dropped
   (`phonemesToSyllableNames(withSilent=False)`, src/word.py:341). Four hard-coded
   steno-encoding exceptions can move a syllable break at Word construction (S2.2.1.1.x).
2. **Each syllable is split into onset / nucleus / coda** by `Syllable.__init__`
   (src/grammar.py:499-518): consonants before the first vowel go to the onset, **every**
   vowel goes to the nucleus, and every consonant after the first vowel goes to the coda.
   "Vowel" means the 16 nucleus phonemes `aeiE@o°§uy5O9821`. That set includes `8` (ɥ), but
   `j` and `w` count as consonants. A syllable with no vowel (63 kinds, e.g. `dR`, `n`,
   `pst`) puts **all** its consonants in the onset, so the left hand types it.
3. **Each phoneme becomes its layout key tuple** for its syllabic part (S2.11.1). The keys
   are concatenated in onset → nucleus → coda order, phoneme by phoneme. Each phoneme's
   tuple is kept whole, with no sorting and no deduplication. This is the **raw Stroke**.
4. **A word's Strokes** is the tuple of its syllables' raw Strokes, in order. A word with
   n syllables gives n Strokes: 1 to 9 today, and most entries have 2 to 4.
5. **Theory 1 keys on the raw Strokes** (dictionary.py:312). Two Words share a theory-1
   entry exactly when they have the same number of syllables and, syllable by syllable, the
   same key sequence. That happens when:
   - they have the same phonemes and the same syllable breaks. These are true homophones
     and paradigm forms: 41,640 entries hold ≥2 distinct spellings, 951 more hold only
     same-spelling homographs, and the largest has 18 spellings (`aller`/`allez`/`allé`/
     `haler`/`hâlé`…).
   - different phonemes map to the **same layout entry** (a shared layout entry): onset key
     9 = `w`/`N`/`G`, nucleus key 11 = `@`/`9`, nucleus (11,12) = `°`/`8`, nucleus 14 =
     `e`/`O`, coda 16 = `j`/`b`/`w`, coda 24 = `Z`/`G`.
   - they differ only in silent `#` letters, which are dropped before any lookup.
6. **Theory 1 does not see physical collisions whose key order or key repeats differ.** A
   Stroke is physically a set of keys. Two raw Strokes that have the same **canonical form**
   (`canonicalizeStrokes`, src/keyboard.py:31) type identically but sit in *different*
   theory-1 entries. This happens through digraph subsumption (coda `k`=18 plus `d`=19
   equals `g`=(18,19)) or through order (`@tR` "entre" vs `@Rt` "heurte" on nucleus key 11).
   Today 233 canonical Strokes merge 2+ raw entries, and all 233 mix different spellings.
   4,535 raw Strokes contain a repeated key. Consumers downstream canonicalize before
   testing collisions (Marker Elicitation (Phase E) `buildLemmaHomophoneGroups`,
   Lemma-Homophone Marking (S4)). `theory.tsv` and any raw-key count under-report the
   physical collisions.
7. Different syllable breaks give different Strokes even when the phonemes are equal
   (`ka/n` vs `kan`). This is why the synthetic-row split described in Suspected bugs
   matters.

## Calls

### Dictionary cache check — __main__ (S2.1)   dictionary.py:451
Called by: Phonetic Theory Building (S2) entry.
Input state: nothing in memory; maybe a `Dictionary.pickle` on disk.
Transformation: if `Dictionary.pickle` exists, it loads five objects in order: the
`Dictionary`, then `Syllable.allPhonemeCol`, `phonemeColByPart`, `biphonemeColByPart` and
`multiphonemeColByPart`, which it assigns back onto the `Syllable` class (:453-457). S2.2
to S2.6 are then skipped. There is no staleness check against the lexicon TSVs or
`excluded_words.txt`.
Result: Word list + syllable statistics, restored.
Artifacts: reads `Dictionary.pickle`.
Notes: every downstream loader (`util/_theoryio.py:26-30`, `src/elicitation.py:540-543`,
`util/check_conjugation_disambiguation_order.py:141-144`,
`util/build_pers3_default_answers.py:163-166`, `src/ambiguitychecker.py:1334-1337`) repeats
the same five-object read. It has to, because the pickle is a stream. None of them uses
the `Syllable` class state afterwards.

### Dictionary construction — Dictionary.__init__ (S2.2)   dictionary.py:76
Called by: Dictionary cache check (S2.1), on a cache miss.
Input state: source files only.
Transformation: creates an empty `SyllableCollection`, the empty indexes, and three empty
ambiguity dicts (`syllabicAmbiguity`, `lexicalAmbiguity`, `syllabicPartAmbiguity`,
each keyed `onset`/`nucleus`/`coda`). It also stores `syllableClass = Syllable` (never
read). Then it calls `readCorpus`.
Result: `Dictionary` with `words` (the Word list) filled; statistics still empty.

### Lexicon reading and identity merge — Dictionary.readCorpus (S2.2.1)   dictionary.py:92
Called by: Dictionary construction (S2.2).
Input state: mixed lexicon (136,456 rows) then synthetic lexicon rows (42,225 rows), read
in that order (`wordSources`, :66-69). A missing file is skipped silently (:117).
Transformation:
- Reads `resources/top500_film.txt`. The first line's last field (907,046.92) becomes
  `totalFrequencies`. The next 200 spellings become `frequentWords` (`nbFrequentWords`=200,
  :63) and their summed frequency becomes `frequentWordsFrequencies`.
- Loads `excluded_words.txt` (44 non-comment spellings, e.g. `alèze`, `d`, `s`, `bitte`).
  Rows whose `ortho` is in the list are dropped (52 rows). Rows whose `ortho` starts with
  `#` are dropped too (0 today).
- **Identity merge** (:113-137): the identity is `(ortho, phon, lemme, cgram, genre,
  nombre)`, the same fields as `Word._hash`. A later row with an identity already seen is
  never turned into a new Word. If it carries an `infover`, that tag is folded into the
  first Word (`mergeInfoVerb`). Otherwise it is dropped. Today 10,990 rows fold: 10,973
  with an infoVerb and 17 without. **The first row's syllabification and frequency win.**
  5,369 folded rows had a different `syll_cv`, and 6,028 a different film frequency.
- Otherwise it builds a `Word` (S2.2.1.1), appends it, and indexes it in
  `wordsByLemme[lemme]` (bare lemma) and `wordsByOrtho[ortho]`.
Result: Word list of 167,639 Words, in load order (136,456 + 42,225 − 52 − 10,990).
`wordsByOrtho` has 147,732 spellings and `wordsByLemme` 43,111 lemmas. It prints the merge
count.
Artifacts: reads `resources/LexiqueMixte.tsv`, `resources/LexiqueSynthetic.tsv`,
`resources/top500_film.txt`, `excluded_words.txt`.
Helpers not expanded: `GramCat[...]` lookup (src/word.py:10).

### Word construction — Word.__post_init__ (S2.2.1.1)   src/word.py:84
Called by: Lexicon reading and identity merge (S2.2.1).
Input state: one lexicon row's fields.
Transformation: runs the four syllable-break exceptions (S2.2.1.1.1-4) on `rawSyllCV` /
`rawOrthosyllCV`, then parses both into `syllCV` / `orthosyllCV` (`list[list[str]]`,
split on `|` then `_`). It sets `frequency = frequencyFilm` (:93); book frequency is
ignored. It sets `_hash = hash(ortho+phonology+lemme+gramCat.name+gender+number)`
(:94; salted per process, no separators), parses `infoVerb` into `_infoVerb`, and sets
`lemmeGramCat = f"{lemme}_{gramCat.name}"`.
Result: one Word, which now carries the syllabification that the phonetic stroke rule
(S2.11.1) will read.
Helpers not expanded: `parseOrthoSyll` :358, `parsePhonoSyll` :365, `splitInfoVerb` :102.

### e+n syllable repair — Word.fix_e_n_en (S2.2.1.1.1)   src/word.py:202
Called by: Word construction (S2.2.1.1).
Transformation: rewrites `@|n_` → `@|` and `e|n_` → `en|` (e.g. "enivre", where the `n`
belongs to the nasal vowel), recursively until none is left. Applies to every row.
Result: the syllable-initial `n` is removed after a nasal `@` spelled "en".

### -rdre infinitive split — Word.fix_rdre_coda_syllable_break (S2.2.1.1.2)   src/word.py:215
Called by: Word construction (S2.2.1.1).
Transformation: only if `infoVerb` is set. A last phonetic syllable ending `_R_d_R_#` is
split so that `d_R_#` becomes its own syllable. The orthographic `_r_d_r_e` is split the
same way.
Result: `perdre` = `pER|dR` (the second syllable is vowel-less, so it goes to the onset).
Otherwise it would canonicalize onto `perdent`/`perde`.

### -ayer conditionnel split — Word.fix_ayer_conditionnel_onset_glide (S2.2.1.1.3)   src/word.py:248
Called by: Word construction (S2.2.1.1).
Transformation: only for verbs. A segment ending `_E_#` followed by one starting `R_j_` is
rewritten `…|R|j_…`, and the orthographic side `r_i_(ez|ons)` is split to match.
Result: `paieriez` = `pE|R|je`. The bare-onset `R` stroke keeps it apart from `payez`
(onset `R`=8 is a subset of onset `j`=(8,9)).

### -uer glide split — Word.fix_glide_low_vowel_syllable_break (S2.2.1.1.4)   src/word.py:297
Called by: Word construction (S2.2.1.1).
Transformation: only for verbs. A last syllable ending `_8_a` or `_8_@` has its vowel split
into its own syllable. The orthographic side matching `^(.*_u)_(ant|as|ât|a)$` is split the
same way.
Result: `tua` = `t8|a`, `tuant` = `t8|@`. Without the split, nucleus `8`=(11,12) would
subsume `a`=12 and `@`=11.
Notes: the phonetic and orthographic tests are independent. Today no row matches one and
not the other (checked), but a future row could misalign the two syllable lists.

### Reading fold-in — Word.mergeInfoVerb (S2.2.1.2)   src/word.py:129
Called by: Lexicon reading and identity merge (S2.2.1).
Transformation: strips `;`, skips the tag if it is empty or already present, then appends
it and re-parses `_infoVerb`.
Result: one Word with the union of the readings (e.g. a synthetic `sub:pre:1s` added to a
Lexique383 `ind:pre:1s` row). The incoming row's `syll_cv` is not compared.

### Syllable inventory — Dictionary.analyseSyllabification (S2.3)   dictionary.py:169
Called by: Phonetic Theory Building (S2) entry, after S2.2.
Input state: Word list in load order; empty `SyllableCollection`.
Transformation: sorts `self.words` **in place** by descending `frequency` (:171). This order
persists into `Dictionary.pickle` and into every theory-1 entry's list (verified: all
80,725 lists are frequency-descending). For each Word, it zips the phonetic syllable names
with the orthographic syllable spellings (:177) and registers each pair with weight
`frequency`. The weight is 0 for the 200 `frequentWords` (:174), so function words do not
dominate the statistics.
Result: syllable statistics: 5,866 `Syllable` objects plus the class-level phoneme,
biphoneme and multiphoneme collections.
Notes: `zip` silently truncates when the two syllable lists differ in length. 99 Words are
in that state (e.g. `assyez` `a|s_E|j_e` vs `a|ss_y_ez`, `ognon`), and their extra
syllables are never registered from that Word. See Suspected bugs.

### Syllable registration — SyllableCollection.updateSyllable (S2.3.1)   src/grammar.py:803
Called by: Syllable inventory (S2.3).
Transformation: creates `Syllable(name, spelling)` on first sight (initial frequency 0.0).
It then adds the frequency through `increaseSpellingFrequency` and records the Word in
`phonoWords[word.phonology]` (`trackWord` :612).
Result: `syllable_names[name]` → `Syllable`. `buildTheory` later looks syllables up by name
here (dictionary.py:310).

### Onset/nucleus/coda decomposition — Syllable.__init__ (S2.3.1.1)   src/grammar.py:468
Called by: Syllable registration (S2.3.1).
Input state: a syllable name such as `plyR` and one spelling.
Transformation: resolves each character to a shared `Phoneme` in `Syllable.allPhonemeCol`.
`Phoneme.__post_init__` raises `ValueError` for a character that is not one of the 16
nucleus, 20 consonant or 1 temporary (`x`) phonemes. Each phoneme is then classified by
position (:499-518):
- not a vowel, and no vowel seen yet → **onset**;
- not a vowel, after the first vowel → **coda** (even when another vowel follows; 0
  syllables have a consonant between two vowels today);
- a vowel → **nucleus** (all vowels; 237 syllables have 2 or more, almost all with `8`,
  e.g. `l8i`).
Each part's phonemes are also counted in `Syllable.phonemeColByPart[part]`. Ordered pairs
of consonants in the onset, ordered pairs in the coda, and pairs across a multi-vowel
nucleus are counted as `Biphoneme`s in `biphonemeColByPart` (:525-561). The whole part is
registered as a `Multiphoneme` in `multiphonemeColByPart` (:562-567). Totals: 184 onset,
28 nucleus and 141 coda multiphonemes.
Result: `phonemesByPart` lists that preserve phoneme order. `phonemeNamesByPart()` (:569)
is what the stroke rule reads.
Notes: `verbose` (:491) prints only for an empty syllable name. There are none today.

### Frequency accumulation — Syllable.increaseSpellingFrequency (S2.3.1.2)   src/grammar.py:586
Called by: Syllable registration (S2.3.1).
Transformation: adds the frequency to the spelling, then `increaseFrequency` (:574). That
adds it to the syllable, to each whole-syllable phoneme (with per-position counters), to
each per-part phoneme and to each per-part biphoneme. **Multiphonemes are not updated**,
so every `Multiphoneme.frequency` is 0.0 (all 353 checked).
Result: frequency-weighted phoneme and biphoneme counts.

### Collection sorting — Syllable.sortPhonemesCollections (S2.3.2)   src/grammar.py:592
Called by: Syllable inventory (S2.3).
Transformation: sorts the phoneme and biphoneme lists by descending frequency.
Result: the frequency ranking read by `generateBaseKeymap` and `optimizeKeyboard`.

### Phoneme order search — Syllable.optimizeBiphonemeOrder (S2.4)   src/grammar.py:644
Called by: Phonetic Theory Building (S2) entry (dictionary.py:464).
Input state: syllable statistics (biphoneme frequencies per part).
Transformation: for onset, coda and nucleus, runs S2.4.1 then S2.4.2 on that part's
`BiphonemeCollection`.
Result: `bestPermutation`, `pairwiseBiphonemeOrder` and `pairwiseBiphonemeOrderScore` on
each collection. Today: onset `dZksvptgzSmnbflNRwj`, coda `bjgpfwsktdvRNzlmnSZ`, nucleus
`8ieE§5Oao92@` (only the 12 vowels that occur in a multi-vowel nucleus).
Notes: **nothing live consumes this.** `bestPermutation` feeds only `generateBaseKeymap`
(fallback, S2.8) and a commented-out printout. `pairwiseBiphonemeOrderScore` feeds only
`optimizeKeyboard` (src/cpsatsolver.py:363, not called) and `writeConstrainFiles`
(dictionary.py:430, call commented at :481). `pairwiseBiphonemeOrder` feeds only
`printBarchart`. It still runs on every rebuild and is pickled.

### Best permutation — BiphonemeCollection.optimizeOrder (S2.4.1)   src/grammar.py:318
Called by: Phoneme order search (S2.4).
Transformation: a greedy local search over the permutations of the phonemes seen in any
biphoneme. It runs n passes, and in each pass it moves each phoneme to the insertion
position that maximizes `scorePermutation` (:347): the sum of +frequency for each
biphoneme typed left-to-right in order, and −frequency for each one out of order. The
starting order comes from a `set` (`getPhonemesNames` :307), so it depends on the
per-process hash seed.
Result: `bestPermutation` string, its score and its negative ("disordered") score. These
are the numbers README.md:92-146 shows.

### Pairwise order matrix — BiphonemeCollection.generateBiphonemeOrderMatrix (S2.4.2)   src/grammar.py:361
Called by: Phoneme order search (S2.4).
Transformation: for every ordered pair (p1, p2), it compares the permutation score with p1
inserted just before p2 against p1 inserted just after. It records `<`, `>` or `=` and the
signed score difference.
Result: `pairwiseBiphonemeOrder` (the README's `<`/`>`/`=` matrix) and
`pairwiseBiphonemeOrderScore`, which is the order-penalty input of Keyboard Layout
Optimization (S2b).

### Ambiguity statistics — Dictionary.analyseAmbiguities (S2.5)   dictionary.py:183
Called by: Phonetic Theory Building (S2) entry (dictionary.py:466).
Input state: syllable statistics with `phonoWords`.
Transformation: runs S2.5.1 to S2.5.3 and stores the results in the three dicts.
Result: `syllabicAmbiguity` and `lexicalAmbiguity` hold 190/120/190 phoneme pairs
(onset/nucleus/coda). `syllabicPartAmbiguity` holds 16,836/378/9,870 multiphoneme pairs
(all pairs of the 184/28/141 multiphonemes). Every pair is included, even with score 0.
Notes: **no live consumer**. `syllabicAmbiguity` is read only by `printSyllabificationStats`
(call commented, :478). `lexicalAmbiguity` is read only by `getLowAmbiguityPhonemes` inside
the fallback `generateBaseKeymap`. `syllabicPartAmbiguity` is read only by `optimizeKeyboard`
(commented, :494) and `writeConstrainFiles` (commented, :481). This is the slowest step of
a fresh rebuild.

### Syllabic phoneme ambiguity — SyllableCollection.analysePhonemSyllabicAmbiguity (S2.5.1)   src/grammar.py:1032
Called by: Ambiguity statistics (S2.5).
Transformation: forks 3 processes (one per part) and scores every phoneme pair with
`syllabicAmbiguityScore` (:841). The question is "if one key meant both p1 and p2, which
syllables would merge". If p2 replaces p1, the score adds min(freq(syllable),
freq(mutated syllable)). If both are in the syllable, it adds the sum of the two smaller
of the three frequencies (syllable, syllable without p1, syllable without p2). Each part's
result is sorted ascending and sent back over a `Pipe`.
Result: `syllabicAmbiguity[part]: dict[(p1, p2), float]`.

### Lexical phoneme ambiguity — SyllableCollection.analysePhonemeLexicalAmbiguity (S2.5.2)   src/grammar.py:1098
Called by: Ambiguity statistics (S2.5).
Transformation: the same idea at word level through `lexicalPhonemeAmbiguityScore` (:883).
For each word with a syllable containing p1, it mutates the word's phonology
(`Word.replaceSyllables` src/word.py:369, a plain substring replace) and adds the smaller
word-frequency sum. It runs as 3 forked processes.
Result: `lexicalAmbiguity[part]`.
Notes: the "both phonemes in one syllable" branch looks up the mutated **word** phonology
as a syllable name (:913, :931). See Suspected bugs.

### Syllabic-part ambiguity — SyllableCollection.analyseMultiphonemeLexicalAmbiguity_serial (S2.5.3)   src/grammar.py:1138
Called by: Ambiguity statistics (S2.5) (dictionary.py:197; the forked twin at :1171 is unused).
Transformation: for every pair of whole-part phoneme groups (e.g. onset `('p','R')` vs
`('b','R')`), `lexicalSyllabicPartAmbiguityScore` (:975) finds the syllables with group 1
(`_getSyllablesOfMultiphonemes` :969, `lru_cache`), swaps in group 2, and adds
min(word-frequency sum, mutated-word frequency sum) whenever the mutated word exists.
Result: `syllabicPartAmbiguity[part]: dict[(mp1, mp2), float]`. This is the
"AMBIGUITY" input of Keyboard Layout Optimization (S2b).

### Dictionary cache write — pickle.dump ×5 (S2.6)   dictionary.py:467-472
Called by: Phonetic Theory Building (S2) entry, on a cache miss only.
Result: `Dictionary.pickle` (57.8 MB): the Dictionary (Word list, both indexes, syllable
collection with each syllable's `phonoWords` Word references, the three ambiguity dicts)
followed by the four `Syllable` class collections.
Artifacts: writes `Dictionary.pickle`.

### Keyboard layout loading — Keyboard.fromJSONFile (S2.7)   src/keyboard.py:252
Called by: Phonetic Theory Building (S2) entry (dictionary.py:488, as
`Starboard.fromJSONFile('starboard3h.json')`).
Input state: `starboard3h.json` (tracked, 211 lines).
Transformation: `json.load` with an `object_hook` that `ast.literal_eval`s every dict key
that parses as a tuple (`"(8, 9)"` → `(8, 9)`). It then builds a `Starboard` with
`cls.__new__` and `__dict__.update`, **bypassing `__init__`**. Only
`FileNotFoundError` is caught and turned into `None`. A malformed file raises.
Result: keyboard layout. Its instance state comes entirely from the JSON:
- `nbKeys` = 26; `allowedKeys` = the 22 keys other than the reserved keys 0, 1, 10, 15
  (class attribute `_reservedKeys`, keyboard.py:320).
- `keyIDinSyllabicPart`: onset = keys 2-9 (left fingers), nucleus = 11-14 (thumbs), coda =
  16-25 (right fingers).
- `phonemesAssignedToStroke: dict[Stroke, list[str]]` with 48 layout entries. Every one of
  the 20 consonants has exactly one entry in the onset and one in the coda, and every one
  of the 16 vowels has one entry in the nucleus. Single-key entries onset: `k`2 `s`3 `p`4
  `v`5 `m`6 `t`7 `R`8 `w/N/G`9. Nucleus: `@/9`11 `a`12 `i`13 `e/O`14. Coda: `j/b/w`16 `s`17
  `k`18 `d`19 `t`20 `R`21 `n`22 `l`23 `Z/G`24 `m`25. The other phonemes use 2-4-key tuples,
  e.g. onset `j`=(8,9), `l`=(6,7); nucleus `1`=(11,12,13,14); coda `g`=(18,19), `z`=(22,23),
  `S`=(24,25). In a shared entry, list order is phoneme priority, and `keyDisplayName`
  names the key after the first phoneme.
Artifacts: reads `starboard3h.json`.
Helpers not expanded: `Starboard.printLayout` keyboard.py:395 (console print, dictionary.py:495).
Notes: provenance. The file was first committed in 37fdc4e (2026-09-13) and has never been
rewritten. It came from an earlier, uncommitted run of Keyboard Layout Optimization (S2b).
The "3h" apparently refers to solve time: keyboard.py:758-759 still names a `starboard1h.json`
"1h optimization", which is not in the repo. `optimizeKeyboard` today uses a 90 s limit.
Nothing in the pipeline writes it (`toJSONFile` is commented out at dictionary.py:496).

### Fallback keymap — Dictionary.generateBaseKeymap (S2.8)   dictionary.py:212
Called by: Phonetic Theory Building (S2) entry, **only** when `starboard3h.json` is missing (:489-492).
Input state: `Starboard()` (via `__init__`, 8/4/10 keys per part, empty layout), syllable statistics.
Transformation: for each part, the N most frequent phonemes (N = single keys in the part:
8, 4 or 10) get single keys in `bestPermutation` order. The remaining phonemes take 2-,
3- then 4-key strokes from `getPossibleStrokes` (keyboard.py:521), with a per-key overuse
cap of `2 + 2·(len−2)`. Any phoneme still unassigned shares the existing single-phoneme
stroke of its lowest-`lexicalAmbiguity` partner (`getLowAmbiguityPhonemes` :296).
Result: an in-memory layout that is **not saved**. Theory 1 would then be built on it,
while every exporter hard-fails without `starboard3h.json`.
Helpers not expanded: `Starboard.addToLayout` keyboard.py:417, `getStrokesOfPhoneme` :466.

### Keyboard Layout Optimization (S2b, not run) — optimizeKeyboard (S2.9)   src/cpsatsolver.py:13
Called by: nothing. The call at dictionary.py:494 is commented out, and the import at :32
survives only as a side effect (it forces `ortools` to load on every `import dictionary`).
Input state (if run): keyboard layout (used as a hint), `syllabicPartAmbiguity`, the
`Syllable` class collections.
Transformation (design rationale). There is **one independent CP-SAT model per syllabic
part**, because onset, nucleus and coda have separate key banks:
- *Decision:* each phoneme of the part gets **exactly one** stroke out of every legal 1-4-key
  stroke in that part's bank (`getPossibleStrokes`, sorted left to right by
  `strokeIsLowerThen`). A phoneme uses between 1 and `maxKeysPerPhoneme` (5/4/5) keys.
  Several phonemes *may* share a stroke; this is not forbidden, only penalized through
  ambiguity. The current layout is supplied as solver hints.
- *Ambiguity term:* a phoneme group's key set is the union of its phonemes' key sets. That
  models what a chord physically is, so it captures digraph subsumption too. For each of
  the 2,000 most ambiguous group pairs (`MAX_MULTIPHONEMES`), if the two key sets are
  identical the cost is `ambiguity score × AMBIGUITY_PENALTY` (30,000). The score is the
  word frequency that would become indistinguishable (S2.5.3).
- *Ergonomic term:* for every assigned stroke, `phoneme frequency × stroke cost ×
  STROKE_ASSIGNMENT_PENALTY` (1). Stroke cost = the sum of `FingerWeights` for each
  finger's keypress (keyboard.py:47-71), plus shape penalties for zig-zags and row gaps in
  the onset and coda, times a 0.85^fingers discount (`getStrokeCost` keyboard.py:547). An
  illegal finger combination has no cost and so cannot be chosen.
- *Order term:* for each phoneme pair, `pairwiseBiphonemeOrderScore × ORDER_PENALTY`
  (500), signed according to which phoneme's stroke is further left. A pair sharing one
  stroke pays half. This rewards layouts where a syllable's phonemes read left-to-right
  across the hand in the order they are spoken.
- *Objective:* minimize ambiguity + ergonomics + order, each part solved for
  `SOLVER_TIME` = 90 s.
Result (if run): `keyboard.clearLayout()` and then the solved strokes are added to the
layout. This is **destructive**: a part whose model fails keeps no entries. It is not
persisted.
Notes: the penalties show the priority order. With frequencies in occurrences per million,
one shared ambiguous pair outweighs almost any ergonomic or order gain. That matches the
shape of the committed layout: shared entries only among rare phonemes (`N`, `G`, `9`,
`O`, `w`). Other files: `src/cpsatprinter.py` (`SolutionPrinter`).

### Theory-1 cache check — __main__ (S2.10)   dictionary.py:498
Called by: Phonetic Theory Building (S2) entry.
Transformation: if `FirstTheory.pickle` exists, it is loaded and S2.11 to S2.13 are
skipped. The cache is keyed neither on `Dictionary.pickle` nor on `starboard3h.json`.
Result: theory 1.
Artifacts: reads `FirstTheory.pickle`.

### Theory 1 construction — Dictionary.buildTheory (S2.11)   dictionary.py:305
Called by: Theory-1 cache check (S2.10), on a cache miss. Also called by
`util/completeVerbParadigms.py:109` (`loadTheoryAndKeyboard` fallback).
Input state: Word list (frequency-descending), syllable statistics, keyboard layout.
Transformation: for each Word it takes the syllable names (silent `#` removed) and looks
up each `Syllable` in `syllableCollection.syllable_names`. This raises `KeyError` if one
is missing. It turns each syllable into a Stroke (S2.11.1) and appends the Word to
`theory[raw Strokes]`.
Result: theory 1: 80,725 entries covering all 167,639 Words. 42,591 entries have ≥2
Words (129,505 Words), 41,640 of them with ≥2 distinct spellings. Strokes per entry: 1
→ 3,111, 2 → 20,701, 3 → 33,534, 4 → 18,069, 5+ → 5,310. Each entry's list is
frequency-descending.
Notes: the layout does not enforce physical legality of the *whole* chord. 529 Words (39
distinct canonical chords) contain a Stroke that `getStrokeCost` rejects. Most are "-isme"
(coda `z`(22,23)+`m`(25) = a 3-key right-pinky press). See Suspected bugs.

### Phonetic stroke rule — Starboard.getStrokeOfSyllableByPart (S2.11.1)   src/keyboard.py:607
Called by: Theory 1 construction (S2.11).
Input state: `{"onset": [...], "nucleus": [...], "coda": [...]}`, phoneme order preserved.
Transformation: for each part in onset → nucleus → coda order, and for each phoneme in
spoken order, `getStrokesOfPhoneme(phoneme, part)` (:466) collects every layout entry
whose **first key** is in the part's bank and whose phoneme list contains the phoneme. The
first match (JSON order) is used, and its keys are appended as they are. There is no
sort, dedupe or legality check. A phoneme with no entry would raise `IndexError` (none
today, since all 36 phonemes are covered). An empty syllable would give `()`.
Result: one raw Stroke per syllable, e.g. `plyR` → `(4, 6,7, 11,13, 21)`, and `ce` (`s°`)
→ `(3, 11,12)`.

### Theory-1 report — Dictionary.writeTheory (S2.12)   dictionary.py:317
Called by: Theory-1 cache check (S2.10), on a cache miss.
Transformation: writes one line per theory-1 entry: `strokesToString(strokes)` (:622) and
the sorted, deduplicated spellings. It prints the entry with the most spellings, and the
entry with the highest summed frequency. That second "max frequency ambiguity" also counts
single-spelling entries.
Result: `theory.tsv` (80,726 lines incl. header).
Artifacts: writes `theory.tsv`.
Notes: `strokesToString` spells each **key** by the first phoneme of its single-key entry,
so multi-key phonemes appear as their component keys: "aller" is written `a/mte` (`l` =
keys 6,7 = "m"+"t"). The column is a key spelling, not a phoneme transcription. It is also
not the RTFCRE form used by Theory Export (S5).

### Theory-1 cache write — pickle.dump (S2.13)   dictionary.py:504
Called by: Theory-1 cache check (S2.10), on a cache miss.
Result: `FirstTheory.pickle` (52 MB). Its Words are copies of the Word list, and they
compare equal to it only through the stored `_hash`.
Artifacts: writes `FirstTheory.pickle`.
Notes: control then passes to the `buildFinalTheory` block (dictionary.py:521-541), which
belongs to Same-Lemma Disambiguation (S3) and Lemma-Homophone Marking (S4).

## New glossary terms
- **Raw Strokes** — The theory-1 key form: per syllable, each phoneme's full layout key
  tuple concatenated in onset → nucleus → coda, spoken order, with repeats kept.
  *`getStrokeOfSyllableByPart` keyboard.py:607; theory-1 keys.* Contrast **Canonical form**.
  Use it whenever a count or equality is taken on theory-1 keys.
- **Theory-1 entry** — One `(raw Strokes, list[Word])` item of theory 1. The list is
  frequency-descending. *dictionary.py:312.*
- **Theory-1 collision** — A theory-1 entry holding ≥2 distinct spellings (41,640 today).
  It is the S2-level meaning of "homophones". Proposed replacement for "stroke cluster" in
  the skeleton's Cluster CONFLICT, sense (3a).
- **Canonical-only collision** — Words in *different* theory-1 entries whose raw Strokes
  have the same canonical form, so they type identically (233 canonical Strokes today,
  e.g. entre/heurte). Visible only after `canonicalizeStrokes`.
- **Layout entry** — One `phonemesAssignedToStroke` item: a key tuple within one syllabic
  bank, and the phoneme(s) it types. **Shared layout entry**: one tuple assigned to ≥2
  phonemes of the same part (key 9 `w/N/G`, …). *starboard3h.json.*
- **Digraph subsumption** — The union of some phonemes' key tuples equals another phoneme's
  tuple, or contains a key already in it, so different phoneme sequences give one chord
  (coda `k`+`d` = `g`; onset `R` ⊂ `j`). Named in the docstrings at word.py:215-340.
- **Onset-only stroke (vowel-less syllable)** — A syllable with no nucleus phoneme. All its
  consonants go to the onset bank. This comes from the syllabification exceptions and from
  synthetic rows. *grammar.py:499.*
- **Syllable-break exception** — One of the four `Word.fix_*` rewrites that move a
  syllable boundary for steno reasons, not phonology. *word.py:202-340.*
- **Identity merge** — `readCorpus` folding a later row with the same Word identity into
  the first Word. Only `infoVerb` is merged, and the first row's syllabification wins.
  *dictionary.py:113-137.*
- **Frequent words** — The 200 top spellings of `top500_film.txt`. They get weight 0 in the
  syllable statistics and are reused by Marker Elicitation (Phase E) (elicitation.py:615).
- **Best permutation / pairwise order matrix** — The left-to-right phoneme order that
  maximizes in-order biphoneme frequency, and its per-pair `<`/`>`/`=` preferences.
  *grammar.py:318, :361.* Off the live path.
- **Syllabic-part ambiguity** — The word frequency that would become indistinguishable if
  two whole onset/nucleus/coda phoneme groups shared a key set. It is the solver's
  ambiguity input. *grammar.py:975.* Off the live path.
- **Illegal chord** — A canonical Stroke that no finger assignment in `_possibleKeypress`
  can press (`getStrokeCost` returns `None`). *keyboard.py:547.*
- **Keyboard Layout Optimization (S2b)** — The CP-SAT phoneme-to-key solver. It is not run;
  its past output is `starboard3h.json`. *cpsatsolver.py:13.*

## Suspected bugs
- dictionary.py:451 + :498 — Neither pickle cache is invalidated when its inputs change,
  and `FirstTheory.pickle` does not depend on `starboard3h.json`. Scenario: edit
  `starboard3h.json` (move coda `m` off key 25), then run `python dictionary.py` and the
  exporters. Theory 1 still holds the old key indices, while `strokesToRTFCRE` and
  `keyDisplayName` render them with the new layout. The Plover dictionary becomes silently
  wrong. Confidence: high (mechanism); likelihood low while the layout is frozen.
- LexiqueSynthetic rows as seen by S2 (origin: Lexicon Building (S1) synthetic side branch)
  — 10,539 of 42,225 synthetic rows split a word-final consonant into its own vowel-less
  syllable (`k_a|n_#`). Mixte does this in 3 rows (`k_a_n_#`). S2 has no normalization,
  so the 3,843 synthetic-only Words get an extra onset-only stroke. Scenario: `façonne`
  subjonctif (`f_a|s_o|n_#`) → 3 Strokes `fa/so/n-`, while indicative `façonne`
  (`f_a|s_O_n_#`) → 2 Strokes. `pause` VER `po/z-` vs `pause` NOM `poz`. The same spelling
  and sound get different, longer strokes. Confidence: medium (it looks unintended: the
  `Word.fix_*` docstrings treat such splits as justified exceptions).
- src/keyboard.py:607-620 (with dictionary.py:305) — The stroke rule never checks that a
  syllable's key union is pressable. Scenario: `traumatisme` coda `zm` → keys (22,23,25),
  a 3-key right-pinky press that is absent from `_possibleKeypress["rightPinky"]`. 529 Words
  are affected (39 chords, mostly "-isme"). Confidence: medium (it depends on
  `_possibleKeypress` being the hardware authority).
- dictionary.py:177 — `zip` drops the extra syllables of the 99 Words whose phonetic and
  orthographic syllable counts differ. If such a syllable occurs in no other Word, it is
  never registered, and `buildTheory` (:310) raises `KeyError`. Scenario: a new synthetic
  row with a misaligned `orthosyll_cv` and a unique last syllable. It does not trigger
  today. Confidence: medium.
- src/grammar.py:913, :931 — `lexicalPhonemeAmbiguityScore` passes a mutated *word*
  phonology to `getSyllable`, which is keyed by syllable name. It should be
  `short_syllable1/2`. Scenario: p/l in "applaudir" (`aplodiR`): `getSyllable("apodiR")`
  → `None`, so every polysyllabic word adds 0 to the triple-ambiguity branch. Impact:
  only `lexicalAmbiguity` → fallback keymap. Confidence: high.
- src/grammar.py:574-584 (and :566) — `Syllable.increaseFrequency` never updates
  `multiphonemesByPart`, and the constructor adds only the initial 0.0. All 353
  `Multiphoneme.frequency` values are 0. No reader today. Confidence: high; impact: none.
- src/grammar.py:307-320 — `optimizeOrder` starts from `set` iteration order, which is
  seeded per process by hashing, so `bestPermutation` (and the README's figures) can
  change between runs. Impact: fallback keymap only. Confidence: medium.
- src/cpsatsolver.py:422 (not run) — `keyboard.clearLayout()` wipes all three parts
  before solving. If one part's model is infeasible or times out without a solution, that
  bank is left empty, and the next `buildTheory` would raise `IndexError`. Confidence:
  medium.

## Dead-code observations
- dictionary.py:32 imports `optimizeKeyboard`, whose only call (:494) is commented out.
  The import still loads OR-Tools on every `import dictionary`, including every exporter
  through `util/_theoryio.py:18`.
- `Syllable.optimizeBiphonemeOrder` (grammar.py:644) and `Dictionary.analyseAmbiguities`
  (dictionary.py:183) run on every fresh rebuild. **Verified:** their outputs reach only
  `generateBaseKeymap` (fallback), `optimizeKeyboard` (not called), `writeConstrainFiles`
  (call commented :481) and `printSyllabificationStats` (call commented :478). Nothing on
  the live path reads them. This confirms the skeleton's suspicion.
- `Dictionary.generateBaseKeymap` :212 and `getLowAmbiguityPhonemes` :296 are reachable
  only when `starboard3h.json` is missing. Their layout is never saved.
- Unused twins: `analysePhonemSyllabicAmbiguity_serial` grammar.py:1007,
  `analysePhonemeLexicalAmbiguity_serial` :1071, and the forked
  `analyseMultiphonemeLexicalAmbiguity` :1171.
- `Dictionary` fields never read after construction: `stemmOfLemme` (never filled),
  `wordsByLemme` (bare lemma; no reader), `totalFrequencies`, `frequentWordsFrequencies`,
  `syllableClass`. `printVerbose` dictionary.py:51 is a no-op.
- The four `Syllable` class collections pickled into `Dictionary.pickle` are reloaded by 5
  downstream loaders and used by none of them. `Syllable.phonoWords` (a Word reference per
  syllable) serves only the dead ambiguity scorers but adds to the 57.8 MB pickle.
- `Starboard.setIrelandEnglishLayout` keyboard.py:718 and keyboard.py `__main__` (:742,
  which loads the missing `starboard1h.json`) are demos.

## Doc drift
- CLAUDE.md "Dictionary Loading … identifies homophones": `Dictionary()` does not.
  Homophones exist only as theory-1 entries built in `buildTheory` (dictionary.py:305),
  and only in raw form. The same line omits `LexiqueSynthetic.tsv` (42k rows,
  dictionary.py:68).
- CLAUDE.md "Indexes words by orthography, lemma, and frequency": there is no frequency
  index. The Word list is sorted by frequency (dictionary.py:171), and `frequentWords` is
  the top-200 film list.
- CLAUDE.md "Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda": ɥ
  (`8`) is a nucleus phoneme, `j`/`w` are consonants, consonants after the first vowel all
  go to the coda, and vowel-less syllables go entirely to the onset (grammar.py:499-518).
- CLAUDE.md "`starboard3h.json` … 26 keys, 4 reserved for control": 22 phoneme keys. The
  reserved keys are mark keys (10 `*`, 15 `#`) and 0/1, which are held for a possible
  third mark, not control keys.
- src/word.py:62 docstring: `frequency` is "chosen mix of the film and book frequencies".
  The code uses film only (:93).
- src/grammar.py:32 comment lists `G` and `N` among the nucleus X-SAMPA symbols. They are
  consonants (:33).
- src/keyboard.py:193-196 (`getStrokeOfSyllableByPart` docstring): "Get the list of
  strokes". It returns one Stroke.
- README.md:73 says 136,348 words; `LexiqueMixte.tsv` has 136,456 rows, and S2 works on
  167,639 Words once the synthetic rows are added. README.md's "Identifying homophones"
  section (:221-226) says the `*`/`#` case is "still unaddressed" and names the retired
  discriminator functions. Lemma-Homophone Marking (S4) is live.
- `00-skeleton.md` §2 (Phonetic Theory Building (S2)) says "Homophones share a key". That
  is true only for the raw form: 233 canonical-only collisions are split across theory-1
  entries.
