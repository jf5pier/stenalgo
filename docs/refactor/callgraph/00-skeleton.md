# Pipeline call graph: skeleton and seed glossary

Output of Pipeline Call Graph and Glossary (Pass 1), skeleton step. It covers the path
from building `resources/LexiqueMixte.tsv` to writing the Plover theory. Later per-stage
files expand one stage each. They reuse the stage names, dataset-state names and glossary
terms defined here word for word. All `file:line` anchors were checked against branch
`docs-refactor` at 5ae0118.

Naming rule: every stage and phase has a descriptive name with its code in parentheses,
for example "Marker Grouping (Phase G)". Cite it by that name, never by the bare code.

---

## 1. Execution order

A full rebuild, in real dependency order. `docs/refactor/rebuild_and_hash.sh` runs steps
2 to 9. It does not run step 1 or the human loop in step 4h.

| # | Command | Stage | Needed for | Notes |
|---|---|---|---|---|
| 0 | `util/fix*.py --apply`, `util/completeVerbParadigms.py --apply`, `util/generateMissingNomAdjForms.py --apply`, … | Lexicon Building (S1) | only after a lexicon correction | Patch `Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv` and `LexiqueMixte.tsv` in place, or append rows to `LexiqueSynthetic.tsv`. Done by hand, one fix at a time. |
| 1 | `python lexique.py` | Lexicon Building (S1) | a full regeneration of `LexiqueMixte.tsv` only | Runs at import time: no `__main__` guard (lexique.py:1261-1263). The fix scripts deliberately avoid it (LEXICON_RECOMPUTE_PIPELINE.md checklist step 1). |
| 2 | `rm -f Dictionary.pickle FirstTheory.pickle` | — | any lexicon change | Otherwise `dictionary.py` silently reuses the stale caches (dictionary.py:451, :498). |
| 3 | `python dictionary.py` (first run) | Phonetic Theory Building (S2) | everything downstream | Writes theory 1. Then, **only if** `phase_g_keypress_assignment.json` and `resolved_press_sets.json` already exist (dictionary.py:531), it also writes `theory2.tsv` from those possibly stale inputs. On a fresh clone `resolved_press_sets.json` is absent because it is gitignored, so theory 2 is skipped. |
| 4 | `python -m src.elicitation` | Marker Elicitation (Phase E) | Marker Grouping (Phase G), Marker Stroke Realization (Phase P), theory 2, all exports | Rebuilds the resolved press-sets from the stored `elicitation_answers.json`. No questions are asked. |
| 4h | `python -m util.build_questionnaire_page` → publish → answer → edit `elicitation_answers.json` → rerun step 4 | Marker Elicitation (Phase E) | only when new oppositions appear (step 4 reports "unresolved oppositions") | The human-in-the-loop part. |
| 5 | `python -m util.build_phase_g_assignment` | Marker Grouping (Phase G) | only when the live marker vocabulary or press-sets change | The tracked output rarely changes after a lexicon fix (LEXICON_RECOMPUTE_PIPELINE.md, "What's usually safe to skip"). |
| 6 | `python -m util.build_phase_p_realization` | Marker Stroke Realization (Phase P) | **only** `export_keyboard_layout.py`'s marker legend | A standalone report. It does not feed theory 2 or the Plover dictionary; see the Phase P note under the stage table. |
| 7 | `python dictionary.py` (second run) | Phonetic Theory Building (S2) + Same-Lemma Disambiguation (S3) + Lemma-Homophone Marking (S4) | **only** refreshing `theory2.tsv` | Fast, because the pickles exist. **Correction to the brief:** nothing downstream reads `theory2.tsv`. Every exporter recomputes theory 2 in its own process through `util._theoryio.loadFinalTheory` → `Dictionary.buildFinalTheory` (util/_theoryio.py:82). The second run is therefore needed only for the human-readable, gitignored `theory2.tsv`, not for the Plover output. |
| 8 | `python -m util.export_plover_dictionary`, `python -m util.export_plover_system` | Theory Export (S5) | Plover | Can run in either order. |
| 9 | `python -m util.export_keyboard_layout` (after step 6), `python -m util.export_practice_words`, **then** `python -m util.export_practice_sentences`, then `python -m util.export_definitions` | Theory Export (S5), steno-trainer branch | steno-trainer | `export_practice_sentences` reads `practice-words.json` (export_practice_sentences.py:157), so it must run after `export_practice_words`. |
| (opt) | `python -m util.check_conjugation_disambiguation_order` | Marker Elicitation (Phase E) validator | checking | Checks the answers against `conjugation_disambiguation_order.txt` and writes `conjugation_disambiguation_report.json` (gitignored). |

Does `dictionary.py` need to run twice? **Partly true.** The first run is required for
theory 1. The second run only refreshes `theory2.tsv`, a terminal report. Exports stay
correct even if the second run is skipped, as long as step 4 (and step 5 when needed)
has run. Stale inputs only reach the first run's `theory2.tsv`.

---

## 2. Stage table

Summary: one line per stage.

| Stage | Entry point | Main input | Main output |
|---|---|---|---|
| Lexicon Building (S1) | `lexique.py` module body :1261 (+ `util/completeVerbParadigms.py` & co.) | Lexique383 + LexiqueInfra | mixed lexicon (`LexiqueMixte.tsv`) + synthetic rows (`LexiqueSynthetic.tsv`) |
| Phonetic Theory Building (S2) | `dictionary.py` `__main__` :448 | both lexicon TSVs + `starboard3h.json` | theory 1 (`FirstTheory.pickle`, `theory.tsv`) + `Dictionary.pickle` |
| Same-Lemma Disambiguation (S3) | `src/elicitation.py` :527 → `util/build_phase_g_assignment.py` :49 → `Dictionary.buildFinalTheory` dictionary.py:342 / `util/build_phase_p_realization.py` :38 | theory 1 + `elicitation_answers.json` | resolved press-sets → keypress groups → final induced strokes |
| Lemma-Homophone Marking (S4) | `composeReservedKeyStrokes` src/ambiguitychecker.py:410, called at dictionary.py:385 | final induced strokes | theory 2 (`theory2.tsv`, and in-memory `finalTheory`) |
| Theory Export (S5) | `util/export_plover_dictionary.py` :35, `util/export_plover_system.py` :38, steno-trainer exporters | pickles + press-sets + keypress groups (theory 2 recomputed) | Plover dictionary, Plover key table, trainer JSON |

### Lexicon Building (S1)
- **Entry:** `python lexique.py`. Everything runs at module level: `Lexique()` at
  lexique.py:1261, `printSyllabificationStats()` at :1262, `outputMixedLexique(...)` at :1263.
- **Reads:** `resources/Lexique383.tsv` (:959), `resources/LexiqueInfraCorrespondance.tsv`
  (:960), `resources/lexiconExclusions.tsv` (:38/:56), `resources/reform1990.tsv`
  (:132, :313, :375), `resources/verbiste/verbs-fr.xml` (:482). All tracked.
- **Writes:** `resources/LexiqueMixte.tsv`, tracked.
- **Calls, in order:** at import: `loadLexiconExclusions` :38, `loadReform1990Lemmes` :117,
  `loadReform1990OrthoRewrites` :196, `loadReform1990PluralRewrites` :329,
  `loadElerEterQualifyingVerbs` :423. Then `Lexique.__init__` :963 → `read_corpus` :966
  (uses `normalizeLemme` :540) → `breakdownSyllables` :1007 → `lexique.Word.breakdownSyllables`
  :750; `printSyllabificationStats` :1097; `outputMixedLexique` :1174 (uses
  `stripSubjonctifImparfait` :1155, `applyOrthoRewrite` :259, `regularizeElerEterOrtho` :454,
  `rewriteOrthosyllSuffix` :343).
- **Synthetic side branch:** `resources/LexiqueSynthetic.tsv` (tracked, 42k rows, extra
  `source` column) is **appended to** by `util/completeVerbParadigms.py --apply` (writer at
  :402), `util/generateMissingNomAdjForms.py`, `util/fixAsseoirDualFormGaps*.py` and
  `util/fixPayerDualFormGaps.py`, and **edited in place** by
  `util/fixEvaserWordFinalZSyllabification.py`. `lexique.py` never reads or writes it. It
  is consumed only by Phonetic Theory Building (S2) (`Dictionary.wordSources`,
  dictionary.py:66-69) and by some validators.
- **Before → after:** Before: two source TSVs keyed by word with separate phonology and
  grapheme-phoneme association columns. After: one 12-column TSV (136k rows) with
  1990-reform spellings, normalized lemmas, subjonctif imparfait tags removed, and
  `syll_cv`/`orthosyll_cv` syllable breakdowns joined with `|` and `_`.

### Phonetic Theory Building (S2)
- **Entry:** `python dictionary.py`, `__main__` at dictionary.py:448.
- **Reads:** `resources/LexiqueMixte.tsv`, `resources/LexiqueSynthetic.tsv`
  (dictionary.py:66-69), `resources/top500_film.txt` (:70), `excluded_words.txt` (:102),
  `starboard3h.json` (:487-488). All tracked. It also reads `Dictionary.pickle` and
  `FirstTheory.pickle` when they exist (:451, :498).
- **Writes:** `Dictionary.pickle` (:467; five objects: the dictionary plus four `Syllable`
  class collections), `FirstTheory.pickle` (:504), `theory.tsv` (:503). All gitignored.
  It writes `theory2.tsv` (gitignored) only when theory 2 is enabled (see Lemma-Homophone
  Marking (S4)).
- **Calls, in order:** `Dictionary.__init__` :76 → `readCorpus` :92 (merges rows with the
  same identity through `Word.mergeInfoVerb` word.py:129); `analyseSyllabification` :169
  (`SyllableCollection.updateSyllable` grammar.py:803); `Syllable.optimizeBiphonemeOrder`
  grammar.py:644; `analyseAmbiguities` :183; pickle dump; `Keyboard.fromJSONFile`
  keyboard.py:252 (fallback `generateBaseKeymap` :212 only if the JSON is missing);
  `Starboard.printLayout`; `buildTheory` :305 (`Starboard.getStrokeOfSyllableByPart`
  keyboard.py:607); `writeTheory` :317; pickle dump. The layout solver call
  `optimizeKeyboard` at :494 is commented out.
- **Before → after:** Before: lexicon rows. After: a `list[Word]` (the Word list), plus
  a mapping from each word's raw Strokes (one Stroke per syllable, onset+nucleus+coda keys
  in phoneme order) to every Word that produces them. That mapping is theory 1.
  Homophones share a key.

### Same-Lemma Disambiguation (S3)
**Marker Elicitation (Phase E):** `python -m src.elicitation`, src/elicitation.py:527.
- Reads `Dictionary.pickle`, `FirstTheory.pickle`, `elicitation_answers.json` (tracked,
  hand-maintained). Writes `questionnaire.json` (:572) and `resolved_press_sets.json`
  (:620), both gitignored.
- Calls: `buildLemmaHomophoneGroups` :61 (regroups by `canonicalizeStrokes` keyboard.py:31
  and `groupWordsByLemme` word.py:414); `reportScale` :164; `buildQuestionnaireItems` :220;
  `buildAnswersByOpposition` :279; `resolveGroupPressSets` :374 (→ `resolvePressByCombination`
  :312 → `featureCombinationsByOrtho` :86 → `wordFeatureCombinations` :30);
  `validateElicitation` :425; `buildFrequencyByGroupOrtho` :449; `resolvePressByCombination`
  :312 again (for readings); `serializeResolvedPressSets` :471.
- Before → after: theory 1 → 47,828 homophone groups. Each maps every spelling to its
  list of alternate press-sets (marker names), plus frequencies and readings. Groups with
  conflicts or unresolved oppositions are dropped.

**Marker Grouping (Phase G):** `python -m util.build_phase_g_assignment`, main at :49.
- Reads `resolved_press_sets.json` and `questionnaire.json` (optional, used for the full
  atom inventory). Writes `phase_g_keypress_assignment.json` (tracked).
- Calls: `loadResolvedPressSets` src/phaseg.py:33; `loadGroupOrthoFrequencies` :48;
  `minKeypressesSatWithPriorities` src/phasegsat.py:490 (CP-SAT, exact minimum K, with hard
  rules `ALONE_KEYS`/`MUST_DIFFER_GROUPS` and soft `PREFERENCE_TIERS` at
  build_phase_g_assignment.py:39-45); `verifyKeypressAssignment` phaseg.py:160;
  `liveMarkers` :63; `frequencyWeightedChordSizes` :189; `serializeAssignment`
  phasegsat.py:530.
- Before → after: per-group press-sets → `markersByKeypress`, which currently has
  **K=7** keypress groups over 13 live markers, with 7 unpressable markers.

**Marker Stroke Realization (Phase P):** one algorithm, called from **two code paths**
with an identical sequence of calls:
1. **Inline, feeding theory 2:** `Dictionary.buildFinalTheory` dictionary.py:342, lines
   373-384. It runs during both `dictionary.py` runs and inside every exporter through
   `util/_theoryio.py:82`. Nothing is persisted except `theory2.tsv`.
2. **Standalone report:** `util/build_phase_p_realization.py` main :38 → writes
   `phase_p_keypress_realization.json` (tracked). It records the chosen coda keys per
   keypress group, cost, alternates and the four residual-collision buckets. Its only
   pipeline reader is `export_keyboard_layout.py:128`, the trainer legend.
- Shared calls: `buildWordToStrokes` src/ambiguitychecker.py:553; `buildWordsByOrthoLemme`
  :766; `buildKeypressGroupToWords` :803 (→ `_resolveEntryWord` :776, primary alternate
  only); `buildKeypressGroupExtraAlternates` :844; `resolvePreferredKeysByGroup` :952
  (`PREFERRED_KEYS_BY_MARKER` :945); `realizeKeypressGroupsAsExtraStroke` :987. The inline
  path only then calls `buildFinalInducedStrokes` :1261 (the whole lexicon) and later
  `buildExtraInducedStrokes` :1288 (self-homograph alternates, dictionary.py:389).
- Before → after: keypress groups → each group gets 1 physical coda-bank key (keys
  16-25). Each marked word gains **one** extra trailing stroke containing the union of its
  groups' keys. The current report shows 0 same-`lemmeGramCat` residual collisions, 34
  cross-category clashes and 1,283 cross-lemma collisions (the last two are left for
  Lemma-Homophone Marking (S4)).

### Lemma-Homophone Marking (S4)
- **Entry:** inside `Dictionary.buildFinalTheory`, `composeReservedKeyStrokes(...)` at
  dictionary.py:385-388, with `loadReform1990DoubletPairs` src/ambiguitychecker.py:94 and
  `phonemeStrokeCounts` (merge mode). `writeFinalTheory` dictionary.py:392 writes
  `theory2.tsv` (dictionary.py:533).
- **Reads:** `resources/reform1990.tsv`; the in-memory final induced strokes.
- **Calls:** `composeReservedKeyStrokes` :410 → `groupHomophonesByReservedStroke` :380 →
  `assignStarHashPhysicalStrokes` :369 → `assignStarHashMarks` :292 → `rankHomophoneCluster`
  :261 → `_starHashCompare` :242 → `decideStarHashMark` :183 (`MARKING_OVERRIDES` :130,
  `RATIO_EXEMPTION_THRESHOLD` :91, `GRAMCAT_PRIORITY` src/greedyoptimizer.py:62);
  `assignStarHashCombos` :272; `starHashCodeToStrokes` :361 (`STAR_KEY`=10, `HASH_KEY`=15 at
  :351-352).
- **Before → after:** Before: one final induced Strokes per word, with collisions still
  left between different `lemmeGramCat`s. After: theory 2, `dict[Word, list[Strokes]]`.
  Index 0 is the primary stroke. When a mark is needed, its first symbol is merged into
  the last phoneme stroke, and escalated codes add bare `*#` strokes. Self-homograph
  alternates follow as extra entries and get no `*`/`#` mark.

### Theory Export (S5)
- **Plover dictionary:** `util/export_plover_dictionary.py` main :35 →
  `loadFinalTheory` util/_theoryio.py:48 → `loadFirstAndFinalTheory` :68 →
  `_loadDictionaryAndFirstTheory` :17 → `Dictionary.buildFinalTheory` (recomputes Same-Lemma
  Disambiguation (S3) Marker Stroke Realization (Phase P) and Lemma-Homophone Marking (S4))
  → `renderFinalStrokesToRTFCRE` util/_stenorender.py:39 (→ `_renderMarkedStroke` :26,
  `Starboard.strokesToRTFCRE` keyboard.py:683). When several words share one steno string,
  it keeps the most frequent (:56). Writes `plover_stenalgo_dictionary.json` (tracked,
  about 163k entries).
- **Plover system:** `util/export_plover_system.py` main :38 → `Starboard.keyDisplayNames`
  keyboard.py:679 plus the hardware-sniffed `GEMINI_PR_LABELS` :28. Writes
  `plover_stenalgo/plover_stenalgo/_generated_keys.py` (tracked). The plugin
  `plover_stenalgo/plover_stenalgo/system.py` imports it (entry point in
  `plover_stenalgo/pyproject.toml`).
- **steno-trainer branch:** these write `steno-trainer/public/data/*.json` (tracked).
  `export_keyboard_layout.py` main :148 reads `starboard3h.json` and
  `phase_p_keypress_realization.json` and does not call `buildFinalTheory`.
  `export_practice_words.py` main :208, `export_practice_sentences.py` main :145 and
  `export_definitions.py` main :46 all call `loadFirstAndFinalTheory` and read
  `resolved_press_sets.json` for readings. Sentences also read
  `util/candidate_sentences.jsonl` and `practice-words.json`.
- **Before → after:** Before: theory 2 as Word → key-index Strokes. After: steno strings
  in RTFCRE format with Stenalgo key names (`*a`, `swa#`, `pvR-#`) mapped to spellings.

---

## 3. Dataset states

Use these names in "Input state" and "Result" lines.

| Name | Python type / shape | Created | Persisted |
|---|---|---|---|
| **source lexicons** | TSV/XML files | external, then patched by `util/fix*.py` | `resources/Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`, `reform1990.tsv`, `verbiste/*.xml` (tracked) |
| **raw lexicon rows** | `list[lexique.Word]` (a *different* dataclass from `src.word.Word`, lexique.py:547) | `Lexique.read_corpus` lexique.py:966 | no |
| **mixed lexicon** | TSV, 12 columns (`ortho phon lemme cgram cgramortho genre nombre infover syll_cv orthosyll_cv freqlivres freqfilms2`) | `outputMixedLexique` lexique.py:1174 | `resources/LexiqueMixte.tsv` |
| **synthetic lexicon rows** | the same TSV plus a `source` column | `util/completeVerbParadigms.py` & co. | `resources/LexiqueSynthetic.tsv` |
| **Word list** | `list[src.word.Word]`, deduplicated by identity (`ortho, phonology, lemme, gramCat, gender, number`) | `Dictionary.readCorpus` dictionary.py:92 | inside `Dictionary.pickle` |
| **syllable statistics** | `SyllableCollection` + `Syllable.*ColByPart` class state | `analyseSyllabification` :169, `optimizeBiphonemeOrder`, `analyseAmbiguities` :183 | `Dictionary.pickle` (objects 1-5) |
| **keyboard layout** | `Starboard` (26 keys; `_reservedKeys` [0,1,10,15]) | `Keyboard.fromJSONFile` keyboard.py:252 | `starboard3h.json` (tracked, never rewritten by the pipeline) |
| **theory 1** | `dict[Strokes, list[Word]]`, keyed by *raw* (order-preserving, repeats allowed) Strokes | `Dictionary.buildTheory` dictionary.py:305 | `FirstTheory.pickle`; human view `theory.tsv` |
| **same-lemma homophone groups** | `dict[LemmaHomophoneGroupKey, list[Word]]`, key = (canonical Strokes, LemmeGramCat) | `buildLemmaHomophoneGroups` elicitation.py:61 | no |
| **questionnaire items** | `list[QuestionnaireItem]` (one per distinct opposition) | `buildQuestionnaireItems` elicitation.py:220 | `questionnaire.json` |
| **elicitation answers** | JSON list of `{atomsA, checkedA, atomsB, checkedB, …}` | a person, through the questionnaire page | `elicitation_answers.json` (tracked) |
| **resolved press-sets** | in memory `dict[LemmaHomophoneGroupKey, dict[WordOrtho, list[frozenset[str]]]]`; on disk a list of `{strokes, lemmeGramCat, pressSets, frequencies, readings}`; reloaded by Marker Grouping (Phase G) as `PressSetsByGroup` (phaseg.py:27, group id `lemmeGramCat@strokes`) | `resolveGroupPressSets` :374 / `serializeResolvedPressSets` :471 | `resolved_press_sets.json` |
| **keypress groups** | `markersByKeypress: dict[int, frozenset[str]]` (7 groups) + metadata | `minKeypressesSatWithPriorities` phasegsat.py:490 / `serializeAssignment` :530 | `phase_g_keypress_assignment.json` (tracked) |
| **keypress group population** | `groupToWords: dict[int, list[Word]]`; `extraGroupSetsByWord: dict[Word, list[frozenset[int]]]` | ambiguitychecker.py:803, :844 | no |
| **physical keypress assignment** | `KeypressGroupPhysicalAssignment` (`chosenKeysByGroup: dict[int, tuple[int,...]]`, residual buckets) | `realizeKeypressGroupsAsExtraStroke` ambiguitychecker.py:987 | report only: `phase_p_keypress_realization.json` (tracked) |
| **final induced strokes** | `dict[Word, Strokes]`: theory-1 strokes plus at most one extra coda stroke | `buildFinalInducedStrokes` ambiguitychecker.py:1261 | no (in the code: `finalInduced`) |
| **theory 2** | `dict[Word, list[Strokes]]` (index 0 primary, then self-homograph alternates) | `Dictionary.buildFinalTheory` dictionary.py:342 | `theory2.tsv` (gitignored, human view, not read by anything) |
| **Plover dictionary** | `dict[str, str]` (RTFCRE steno → ortho) | `export_plover_dictionary.main` | `plover_stenalgo_dictionary.json` (tracked) |
| **Plover key table** | Python module: `KEYS`, `IMPLICIT_HYPHEN_KEYS`, `GEMINI_PR_KEYMAP` | `export_plover_system.main` | `plover_stenalgo/plover_stenalgo/_generated_keys.py` (tracked) |
| **trainer data** | JSON (`keyboard-layout`, `practice-words`, `practice-sentences`, `definitions`) | steno-trainer exporters | `steno-trainer/public/data/*.json` (tracked) |

---

## 4. Seed glossary

Format: **Term** — definition. *Anchor.* Preferred/Avoid notes where useful.
`CONFLICT:` marks terms with competing usages; these need a user decision (section 5).

- **Alternate (press-set alternate)** — One of several press-sets for a self-homograph
  spelling, one per reading. Pressing any one of them is enough. Index 0 is the
  *primary*: it drives Marker Stroke Realization (Phase P)'s key search, and the rest
  become extra strokes. *`resolveGroupPressSets` elicitation.py:374; `buildKeypressGroupExtraAlternates` ambiguitychecker.py:844.*
- **Atomic feature** — See **Marker**. *`atomicFeatures` word.py:406.* Avoid in new prose.
- **Base strokes** — A word's theory-1 Strokes, with no marks. *`buildWordToStrokes`
  ambiguitychecker.py:553; `strokes` column of `theory2.tsv`.* Preferred over "phoneme strokes"
  except where the phoneme-only nature matters.
- **Canonical form (of a Strokes)** — A Strokes with each Stroke sorted and deduplicated.
  This is the physically realized chord. Every collision test must compare this form,
  never the raw form. *`canonicalizeStrokes` keyboard.py:31.*
- **Canonical member** — The member of a homophone group or cluster that gets no mark:
  the empty press-set `∅` in Same-Lemma Disambiguation (S3), or code `()` in Lemma-Homophone Marking (S4).
  *`assignStarHashCombos` ambiguitychecker.py:272.*
- **Chord** — CONFLICT: This means a physical Stroke in keyboard.py:21 and in the Phase P
  docstrings ("composed chord"). In ATOMIC_KEYPRESS_REWIRE_PLAN.md:49 it means an
  *abstract Keypress*. The trainer uses `Chord` for a (word, strokes, steno) record
  (export_practice_sentences.py:50). Preferred: **Stroke** for physical keys. Avoid "chord"
  for abstract keypresses.
- **Cluster** — CONFLICT: This word has three meanings. (1) The plan's fixed vocabulary
  (ATOMIC_KEYPRESS_REWIRE_PLAN.md:40): same-lemma homophones, i.e. a **Homophone Group**.
  (2) GLOSSARY.md: a synonym to avoid, replaced by Homophone Group. (3) ambiguitychecker.py:
  `StrokeClusterReport` :46 means all words sharing one stroke, and
  `rankHomophoneCluster` :261 means a *lemma-homophone* group (Lemma-Homophone Marking (S4)).
  Proposed: **Homophone Group** for (1), **lemma-homophone cluster** for (3b), **stroke
  cluster** for (3a).
- **Coda / Onset / Nucleus (syllabic part)** — The consonants after the vowel, the
  consonants before it, and the vowel(s) of a syllable. Each part maps to its own key bank.
  *`Phoneme.phonemesByPart` grammar.py:35; `Syllable.phonemeNamesByPart` :569.*
- **Coda bank** — The right-hand keys 16-25. Marker Stroke Realization (Phase P) chooses
  marker keys only from these. *build_phase_p_realization.py:4; `GEMINI_PR_LABELS` export_plover_system.py:28.*
- **Cross-category clash** — Two words with the same bare lemma but different `gramCat`
  that collide ("aller"-style). Marker Stroke Realization (Phase P) does not handle them.
  Lemma-Homophone Marking (S4) does, because their `lemmeGramCat`s differ.
  *`detectCrossCategoryClash` ambiguitychecker.py:59.*
- **Discriminator** — Legacy term (before 2026-09-18) for a solver-chosen feature that
  separates homophones. Still used in function names such as `buildDiscriminatorSelection`
  and `_appendCodaExtraStroke`'s docstring. Avoid; use **Marker** / **Press-set**.
- **Doublet (1990-reform spelling doublet)** — Pre- and post-reform spellings of the
  same word. Never marked against each other. *`loadReform1990DoubletPairs` ambiguitychecker.py:94.*
- **Elicitation answers** — The person's recorded checkbox answers, one per opposition.
  They are the only hand-authored input of Same-Lemma Disambiguation (S3). *`elicitation_answers.json`; `AnsweredOpposition` elicitation.py:266.*
- **Escalation / escalated code** — A `*`/`#` code past the four-code budget (`()`,
  `*`, `#`, `*#`) that adds bare `*#` strokes. *`assignStarHashCombos` ambiguitychecker.py:272.*
- **Extra stroke (trailing stroke)** — A stroke appended after the base strokes. In
  Marker Stroke Realization (Phase P) it holds the coda-bank marker keys. In Lemma-Homophone
  Marking (S4) it holds escalated mark symbols. *`_appendCodaExtraStroke` ambiguitychecker.py:892.*
- **Feature Combination** — See **Reading**. *`FeatureCombination` elicitation.py:27.*
- **Final induced strokes** — Base strokes plus the Marker Stroke Realization (Phase P)
  extra stroke, before Lemma-Homophone Marking (S4). *`buildFinalInducedStrokes` ambiguitychecker.py:1261.*
  Avoid "finalInduced" in prose.
- **GramCat** — The grammatical category enum: 22 values such as `NOM`, `VER`, `ADJ:pos`.
  *word.py:10.* (CLAUDE.md says 21; the enum has 22.)
- **Homograph** — Two Words with the same `ortho`. They type the same text, so they are
  never disambiguated. **Self-homograph**: one spelling with several readings inside
  one homophone group ("calmez"). *`decideStarHashMark` rule 1 ambiguitychecker.py:211.*
- **Homophone Group** — Words with the same `LemmeGramCat` and the same canonical Strokes;
  the unit of Same-Lemma Disambiguation (S3). *`buildLemmaHomophoneGroups` elicitation.py:61,
  `LemmaHomophoneGroupKey` :24.* Preferred (GLOSSARY.md). Avoid "cluster". Note that the
  type is named `LemmaHomophoneGroupKey` even though it is a *same-lemma* group.
- **K** — The number of keypress groups found by Marker Grouping (Phase G). Currently 7
  (`keypressCount` in `phase_g_keypress_assignment.json`).
- **Keypress** — CONFLICT: In `src/keyboard.py:26` (`Keypress: TypeAlias = tuple[int, ...]`)
  it is a *physical* key combination under one finger, used by `PositionWeights`. In
  Marker Grouping (Phase G) and the plan (phaseg.py:10, ATOMIC_KEYPRESS_REWIRE_PLAN.md:49) it
  is the *abstract* unit that a set of markers maps to. Proposed: **Keypress Group** for
  the abstract unit; keep `Keypress` only as the keyboard.py type.
- **Keypress Group** — One output unit of Marker Grouping (Phase G): an integer id plus
  its markers. Marker Stroke Realization (Phase P) turns each into physical coda keys.
  *`markersByKeypress`; `KeypressGroupPhysicalAssignment` ambiguitychecker.py:904.*
- **Lemma-homophone** — Homophones whose lemmas differ (ver/vert/verre). ROADMAP.md:281.
  In the code the test is "different `lemmeGramCat`" (ambiguitychecker.py:402).
- **Lemma-Homophone Marking (S4)** — The stage that adds `*`/`#` marks to words that
  still collide after Marker Stroke Realization (Phase P) with a different `lemmeGramCat`.
  *`composeReservedKeyStrokes` ambiguitychecker.py:410.* Also called the "`*`/`#` track",
  "cross-lemma track" or "reserved-key track". Avoid all three in new prose.
- **Lemme / LemmeGramCat** — The lemma string, and the key `"lemme_GramCat"`
  (e.g. `rucher_NOM`). The key that almost every "same-lemma" test actually uses.
  *word.py:22-23, :100.* Note: `groupWordsByLemme` word.py:414 groups by
  **LemmeGramCat**; `groupWordsByBareLemme` :425 groups by bare lemme.
- **Lexicon Building (S1)** — The stage that produces the mixed lexicon and synthetic
  lexicon rows. *lexique.py:1261.*
- **Live marker / unpressable marker** — A marker that appears in at least one resolved
  press-set, or one that never does and so is left out of Marker Grouping (Phase G).
  *`liveMarkers` phaseg.py:63.*
- **Marker** — CONFLICT (a naming spread rather than a clash): one grammatical value
  (`pers_2`, `nbr_p`, `subjonctif`, `f`). Also written as *atom*, *atomic feature*,
  *feature* (legacy `WordFeature`, which also covers compound features such as
  `ind:pre:3s`) and *discriminator*. Preferred: **Marker**. Avoid the other four for this
  meaning. *ATOMIC_KEYPRESS_REWIRE_PLAN.md:44.*
- **Marker Elicitation (Phase E)** — Sub-phase of Same-Lemma Disambiguation (S3): it
  builds questionnaire items and resolves the stored answers into resolved press-sets.
  *elicitation.py:527.*
- **Marker Grouping (Phase G)** — Sub-phase of Same-Lemma Disambiguation (S3): it assigns
  live markers to the minimum number of keypress groups without breaking any homophone
  group. *build_phase_g_assignment.py:49; phasegsat.py:490.*
- **Marker Stroke Realization (Phase P)** — Sub-phase of Same-Lemma Disambiguation (S3):
  it chooses a coda-bank key per keypress group and appends one extra stroke per marked
  word. *`realizeKeypressGroupsAsExtraStroke` ambiguitychecker.py:987.*
- **Mark code (`*`/`#` code)** — A symbolic tuple such as `()`, `('*',)` or `('*#','*#')`.
  **Merged mark**: the code's first symbol pressed together with the last phoneme stroke.
  *`assignStarHashMarks` :292; `composeReservedKeyStrokes` :410.*
- **Opposition** — An unordered pair of distinct feature combinations from different
  spellings in one homophone group. It is the unit a questionnaire item asks about.
  *`OppositionSample` elicitation.py:99; `AnswerByOpposition` :276.*
- **Phoneme** — A single-character X-SAMPA sound: 16 nucleus and 20 consonant symbols.
  *grammar.py:16, :32-33.* A `Biphoneme` or `Multiphoneme` is a sequence of phonemes
  within one syllabic part.
- **Phonetic Theory Building (S2)** — The stage that maps each Word to its base strokes
  on the adopted layout, producing theory 1. *dictionary.py:448.*
- **Plover dictionary** — The RTFCRE → spelling JSON used by Plover. *plover_stenalgo_dictionary.json.*
- **Press / Press-set** — The set of markers a writer presses, beyond the sound strokes,
  to get one spelling. The empty set `∅` means the canonical member.
  *`AnsweredOpposition.pressA`; `resolveGroupPressSets`.* Preferred over **Signature**.
- **Questionnaire item** — One opposition shown with a pair of example spellings.
  *`QuestionnaireItem` elicitation.py:210.*
- **Reading** — CONFLICT: one grammatical analysis of a spelling, stored as a frozenset of
  markers. ATOMIC_KEYPRESS_REWIRE_PLAN.md:46, `readings` in `resolved_press_sets.json`
  and `type Reading` export_practice_words.py:70 all use **Reading**. GLOSSARY.md prefers
  **Feature Combination** (`FeatureCombination` elicitation.py:27). The two are the same
  type (`frozenset[str]`). The user must choose one.
- **Reserved keys** — Starboard keys 0, 1, 10 and 15, excluded from phoneme assignment.
  `STAR_KEY`=10 (`*`) and `HASH_KEY`=15 (`#`) carry marks. Keys 0 and 1 are held for a
  possible third mark. *keyboard.py:320; ambiguitychecker.py:351-352.*
- **Residual collision** — Two different words still sharing a final stroke after a
  stage. It falls into one of four buckets: theory, same-`lemmeGramCat`, cross-category,
  or cross-lemma. *`KeypressGroupPhysicalAssignment` ambiguitychecker.py:904.*
- **RTFCRE** — Plover's steno string notation (`/` between strokes, `-` separating the
  right bank). *`renderFinalStrokesToRTFCRE` _stenorender.py:39.*
- **Same-Lemma Disambiguation (S3)** — The stage that separates words sharing both a
  `lemmeGramCat` and a stroke, using elicited markers realized as coda keys.
  It covers Phases E, G and P.
- **Signature** — CONFLICT: GLOSSARY.md defines it as the old name for **Press-set**, and
  its definition ("union across all readings") is stale since the 2026-09-22 alternates
  change. phasegsat.py:37 `GroupSignature` means something else: a group's *shape*, i.e.
  its set of per-spelling alternate press-sets, used to deduplicate CP-SAT problems.
  Proposed: keep `GroupSignature` for the shape only and never use "signature" for a
  press-set.
- **Starboard** — The 26-key target keyboard; `Starboard` class keyboard.py:290,
  layout `starboard3h.json`.
- **Stroke / Strokes** — CONFLICT (with chord and keypress): a `Stroke` is the key indices
  pressed at once for one syllable. `Strokes` is the tuple of Strokes for a whole word.
  *keyboard.py:27-28.* Preferred: **Stroke** for physical simultaneous keys.
- **Syllable** — A syllable made of onset, nucleus and coda, parsed from `syll_cv`.
  Each syllable becomes one Stroke. *`Syllable` grammar.py:422; `Word.phonemesToSyllableNames` word.py:341.*
- **Theory 1** — Every Word's base strokes (`dict[Strokes, list[Word]]`), with no
  disambiguation. *`buildTheory` dictionary.py:305.* Also called "first theory".
- **Theory 2** — Every Word's final Strokes list after Same-Lemma Disambiguation (S3)
  and Lemma-Homophone Marking (S4). *`buildFinalTheory` dictionary.py:342.* Preferred over
  "final theory" (a code name only, as in `finalTheory`).
- **Theory Export (S5)** — The stage that renders theory 2 into the Plover dictionary,
  the Plover key table and the trainer data.
- **Word** — The lexicon entry dataclass (`src.word.Word`, word.py:28). Its identity is
  a hash of `ortho`, `phonology`, `lemme`, `gramCat`, `gender` and `number`. Note:
  `lexique.py:547` defines an unrelated `Word` used only by Lexicon Building (S1).

Count: 50 entries, 7 marked CONFLICT.

---

## 5. Naming notes

Stage-name refinements to propose (not applied above):
1. **Same-Lemma Disambiguation (S3)** actually works on the *same `lemmeGramCat`*
   (lemma + category), not the same bare lemma (`_isInScopeCollision`
   ambiguitychecker.py:968; `groupWordsByLemme`). Option A: keep the name and define
   "lemma" as lemma + category in this pipeline. Option B: "Same-Paradigm
   Disambiguation (S3)".
2. **Lemma-Homophone Marking (S4)** also marks *same-lemma, cross-category* clashes
   (34 in the current Marker Stroke Realization (Phase P) report), because its filter is
   "≥ 2 distinct `lemmeGramCat`" (ambiguitychecker.py:402). Option: "Cross-Paradigm
   Homophone Marking (S4)", or keep the name and note the scope.
3. **Marker Elicitation (Phase E)**: in a rebuild, `python -m src.elicitation` asks
   nothing. It generates questionnaire items and resolves the stored answers. Suggest
   splitting it into sub-steps "Questionnaire Generation" and "Press-Set Resolution",
   with the human "Answer Collection" loop between them.
4. **Marker Stroke Realization (Phase P)** has two call sites (inline in
   `buildFinalTheory`, and the standalone report). Later docs should say "Marker Stroke
   Realization (Phase P), report build" when they mean `util/build_phase_p_realization.py`.
5. Phonetic Theory Building (S2) contains a syllable-statistics sub-step
   (`analyseSyllabification`, `optimizeBiphonemeOrder`, `analyseAmbiguities`). Only the
   first feeds theory 1 (see Observations).

Terminology the user should decide: **Cluster** (plan vocabulary vs GLOSSARY.md),
**Reading vs Feature Combination** (plan vs GLOSSARY.md, opposite preferences),
**Keypress** (physical type alias vs abstract unit), **Signature** (stale press-set alias
vs `GroupSignature`), **Chord** (physical vs abstract vs trainer record). Also:
`LemmaHomophoneGroupKey` and `groupWordsByLemme` are names that say "lemma" but mean
same-`lemmeGramCat`.

---

## 6. Observations

**Dead or off-path code on the main pipeline**
- dictionary.py:32 imports `optimizeKeyboard`, but its only call (:494) is commented out.
  `src.cpsatoptimizer` is commented out at :47. Confidence: high.
- dictionary.py:464-466: the results of `Syllable.optimizeBiphonemeOrder` and
  `analyseAmbiguities` are used only by `generateBaseKeymap` (:212, a fallback that runs
  only when `starboard3h.json` is missing), `writeConstrainFiles` (call commented, :481),
  `printSyllabificationStats` (commented, :478) and `src/cpsatsolver.py:363` (not called).
  They are paid for on every fresh rebuild. Confidence: medium-high.
- src/phaseg.py greedy path (`runPhaseG` :247, `greedyColorMarkers` :117,
  `wouldCollideIfMergedPairs` :89) is used only by tests. The live Marker Grouping
  (Phase G) uses phasegsat.py plus phaseg's loaders and verifiers. Confidence: high.
- src/ambiguitychecker.py `__main__` (:1326, "Phase 0 ambiguity report") and its
  atomic-feature path (`buildAtomicFeatureToWords` :568, `findFeatureKeypresses` :623,
  `FEATURE_PRIORITY`) are diagnostics outside the pipeline, still on the legacy
  `buildDiscriminatorSelection`.
- util/build_pers3_default_answers.py:177 is a one-off that **overwrites**
  `elicitation_answers.json`, which has been hand-fixed since (commits 4e73533, 688c74d,
  3b22e0f). Rerunning it would silently undo those fixes. Confidence: high.

**Stale docs and comments**
- CLAUDE.md item 5 says Phase G has "K=5". The artifact has `keypressCount` 7.
  build_phase_g_assignment.py:18 says "still K=6", and build_pers3_default_answers.py:9
  says "model 2 (K=6)".
- CLAUDE.md item 7 says `FEATURE_PRIORITY` still does live work. Only `GRAMCAT_PRIORITY`
  is on the main path (ambiguitychecker.py:227). `FEATURE_PRIORITY` feeds only the
  diagnostic `_selectCanonicalIndex` :557. The legacy path described in item 7 no longer
  runs in `dictionary.py`.
- CLAUDE.md says there are "23 consonants". grammar.py:33 lists 20 consonant phonemes.
  CLAUDE.md says `GramCat` has 21 values; it has 22.
- util/completeVerbParadigms.py:27-31 and :405, and util/fixAsseoirDualFormGaps.py:34,
  say `LexiqueSynthetic.tsv` is "not yet wired" into the pipeline. It is read by
  dictionary.py:66-69.
- The error message "run dictionary.py once first to generate it" (for `starboard3h.json`)
  appears at build_phase_p_realization.py:47, export_plover_dictionary.py:38,
  export_plover_system.py:41, export_keyboard_layout.py:151, export_practice_words.py:216,
  export_practice_sentences.py:153, export_definitions.py:49 and ambiguitychecker.py:1346.
  `dictionary.py` never writes that file (`toJSONFile` is commented out at :496).
- ambiguitychecker.py:1303 (the `buildExtraInducedStrokes` docstring) says the
  cross-lemma track "isn't yet wired into dictionary.py's persisted output". It is
  (dictionary.py:385).
- The rule numbers of `decideStarHashMark` drift: ambiguitychecker.py:392 calls the
  homograph rule "Rule 2" (it is Rule 1), and :431 calls the doublet rule "Rule 3" (it is
  Rule 2). ambiguitychecker.py:14 and :65 cite a stale anchor "dictionary.py:496-505".
- build_phase_p_realization.py:10-12 says it "does NOT yet rewrite theory". Theory 2 now
  exists through `buildFinalTheory`. LEXICON_RECOMPUTE_PIPELINE.md calls
  `phase_p_keypress_realization.json` a "reference artifact", but
  export_keyboard_layout.py:128 consumes it.
- GLOSSARY.md "Signature" still describes a union across readings. That was superseded
  by per-reading alternates (elicitation.py:374).

**Suspected bugs and hazards** (all unverified by execution)
- export_keyboard_layout.py:133-141: if any Marker Stroke Realization (Phase P) group is
  unassigned (`chosenKeys: null`), `keyDisplayName(k) for k in keys` raises `TypeError`
  and the sort at :144 compares `None`. It does not trigger today (all 7 groups have
  keys). Confidence that it would crash: high. Likelihood: low.
- Drift between the two Marker Stroke Realization (Phase P) paths: the Plover dictionary
  recomputes the keys inline, while the trainer key legend reads the tracked
  `phase_p_keypress_realization.json`. If Marker Grouping (Phase G) or the press-sets
  change without rerunning `util/build_phase_p_realization.py`, the legend shows
  different keys from the ones the dictionary uses. Confidence: medium.
- dictionary.py:498-505: `theory.tsv` is written only when `FirstTheory.pickle` is
  absent, so it is also stale whenever the pickle cache is stale. The first `dictionary.py`
  run writes `theory2.tsv` from possibly stale press-sets (:531). Confidence: high,
  impact: low, because both files are human views only.
- ambiguitychecker.py:800: when a `resolved_press_sets.json` entry's strokes no longer
  match any theory-1 Word (stale press-sets after a lexicon fix), `_resolveEntryWord`
  silently falls back to `candidates[0]`. That can put marks on the wrong same-spelling
  Word instead of failing. Confidence: medium.
- word.py:94 and :161: `Word` identity is the salted-per-process `hash()` of an
  unseparated concatenation of fields, and `__eq__` compares only that hash. Words from
  pickles built in different processes never compare equal, for example after deleting
  only `Dictionary.pickle`. Separator-free concatenation could in theory collide.
  Confidence: low to medium; nothing on the current main path mixes pickles.
- lexique.py has no `__main__` guard (:1261-1263), so importing it runs a full lexicon
  rebuild and overwrites `LexiqueMixte.tsv`. There are no importers today. Confidence: high,
  risk: low.
- Self-homograph alternate strokes (`buildExtraInducedStrokes`, dictionary.py:389) skip
  Lemma-Homophone Marking (S4), so an alternate can collide with an unrelated lemma. This
  is a known and documented scope gap, not a regression.
