# Pipeline: from LexiqueMixte to the Plover theory

This document is the call graph of the whole Stenalgo pipeline. It starts with the two
French source lexicons and ends with the Plover dictionary, the Plover key table and the
steno-trainer data. For every call that transforms, filters or decides something, it says
what the data looks like going in, what the call does (with its rules, thresholds and
constants) and what comes out, with sizes measured on the 2026-09-22 data.

How to read it:

- Eight stages, S1 to S8, one top-level section each. Stages and phases are cited by
  descriptive name with the code in parentheses ("Discriminating-Feature Grouping (Grouping
  Phase)"). Calls are numbered in execution order inside their stage ("Theory 1 construction
  (S5.3)"); in Same-Lemma and Grammatical-Category Disambiguation (S6) the ids carry the
  phase (`S6.Elicitation.n`, `S6.Grouping.n`, `S6.Realization.n`). A number always follows a
  descriptive name. Ids are stable citations, so gaps exist where a call was removed
  (`S6.Elicitation.7` was the deleted one-off pers_3-default rewrite script).
- Terms in **bold** (at first use) and every dataset-state name are defined in
  [GLOSSARY.md](GLOSSARY.md), in this folder. The glossary also maps older names (letter
  phase codes, "press-set", "marker", "cluster", the old stage numbers) to the ones used here.
- Each call uses the same fields: **Called by**, **Input state**, **Transformation**,
  **Result**, **Artifacts** (files read/written), **Helpers not expanded** (small functions
  folded into the call) and **Notes**. Empty fields are left out.
- `file:line` anchors were checked on branch `docs-refactor` at 5ae0118. Counts come from
  read-only probes of the pickles and JSON files rebuilt on 2026-09-22; a later rebuild can
  shift them slightly.
- Suspected defects are only pointed to here ("see TODO.md § Suspected bugs, item B1").
  They are described in full in the findings list of this refactor.

---

## How to run a full rebuild

The real dependency order. Run the steps that write the pickles with `PYTHONHASHSEED=0`
pinned when byte-reproducible tracked outputs matter (fact 3 below). Steps 0 and 1 and the
human loop 4h are run by hand, not by any script.

| # | Command | Stage | Needed when | Notes |
|---|---|---|---|---|
| 0 | `python -m util.fix<Name> --apply`, `python -m util.completeVerbParadigms --apply`, `python -m util.generateMissingNomAdjForms --apply`, … | Lexicon Building (S1), Synthetic Lexicon Building (S2) | only after a lexicon correction | Patch `Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`, Verbiste XML and/or `LexiqueMixte.tsv`, or append rows to `LexiqueSynthetic.tsv`. Run by hand, one fix at a time. |
| 1 | `python lexique.py` | Lexicon Building (S1) | a full regeneration of `LexiqueMixte.tsv` | Everything runs at import time (no `__main__` guard, lexique.py:1261-1263). A rerun today is byte-identical to the committed file. |
| 2 | `rm -f Dictionary.pickle FirstTheory.pickle` | — | **any** lexicon or layout change | The pickle-cache trap: see below. |
| 3 | `python dictionary.py` (first run) | Dictionary Loading (S3), Keyboard Layout Optimization (S4) statistics, Phonetic Theory Building (S5) | everything downstream | Writes theory 1 and both pickles. If `keypress_groups.json` and `resolved_press_sets.json` already exist (dictionary.py:531), it also writes `theory2.tsv` from those possibly stale inputs. On a fresh clone `resolved_press_sets.json` is absent (gitignored), so theory 2 is skipped. |
| — | (no command) | Keyboard Layout Optimization (S4), solver | only to regenerate `starboard3h.json` | Rare and costly. The solver call (dictionary.py:494) and the layout write (:496) are commented out, so today it needs a code edit (see that stage). |
| 4 | `python -m src.elicitation` | Discriminating-Feature Elicitation (Elicitation Phase): Questionnaire Generation, Press-Set Resolution | everything after it | Rebuilds the resolved discriminating feature sets from the stored `elicitation_answers.json`. Asks no questions. |
| 4h | `python -m util.build_questionnaire_page` → publish → answer → copy answers into `elicitation_answers.json` → rerun step 4 | Elicitation Phase: Answer Collection | only when step 4 reports "unresolved oppositions" | The human-in-the-loop part. |
| 5 | `python -m util.build_keypress_groups` | Discriminating-Feature Grouping (Grouping Phase) | when the live features or discriminating feature sets change | The tracked output rarely changes after a lexicon fix. |
| 6 | `python -m util.build_realization_report` | Discriminating-Feature Stroke Realization (Realization Phase), report build | before step 9's keyboard legend | Writes the realization report only. It does not feed theory 2 or the Plover dictionary. |
| 7 | `python dictionary.py` (second run) | Phonetic Theory Building (S5) → Different-Lemma or Grammatical-Category Disambiguation (S7) | only to refresh `theory2.tsv` | Fast (pickles exist). |
| 8 | `python -m util.export_plover_dictionary`, `python -m util.export_plover_system` | Theory Export (S8), Plover branch | Plover | Either order. |
| 9 | `python -m util.export_keyboard_layout` (after step 6), `python -m util.export_practice_words`, **then** `python -m util.export_practice_sentences`, then `python -m util.export_definitions` | Theory Export (S8), trainer branch | steno-trainer | `export_practice_sentences` reads `practice-words.json` (export_practice_sentences.py:157). |
| opt | `python -m util.check_conjugation_disambiguation_order` | Elicitation Phase: Answer Collection, validator | checking answers | Writes `conjugation_disambiguation_report.json` (gitignored). |

Five facts that the command list does not show:

1. **Nothing reads `theory2.tsv`.** It is a gitignored human view. Every exporter that
   needs theory 2 recomputes it (`util/_theoryio.loadFirstAndFinalTheory` →
   `Dictionary.buildFinalTheory`, util/_theoryio.py:82), rerunning the Realization Phase and
   Different-Lemma or Grammatical-Category Disambiguation (S7), four times in a full export.
   Step 7 only refreshes `theory2.tsv`; the Plover dictionary needs steps 4 and 5.
2. **The pickle-cache trap.** `dictionary.py` reuses `Dictionary.pickle` and
   `FirstTheory.pickle` whenever they exist (dictionary.py:451, :498). Neither cache is
   checked against the lexicon TSVs, `excluded_words.txt` or `starboard3h.json`. After a
   lexicon or layout change without step 2, every later step silently works on the old
   Word list and old strokes. `theory.tsv` is only written on a `FirstTheory.pickle` miss,
   so it goes stale with the cache.
3. **`PYTHONHASHSEED` changes pickle contents.** Each Word's identity hash (`Word._hash`,
   src/word.py:94) is Python's per-process salted `hash()` of its fields, computed when the
   Word is built and stored in the pickles. The Realization Phase iterates a `set` of Words
   when it lists residual collisions, so a clean rebuild (new pickles, new hash values)
   reorders those lists in `realization_report.json`. With the same pickles, four
   different seeds gave identical `theory2.tsv`, realization report and Plover dictionary;
   fresh pickles changed only the report's residual lists. Pin `PYTHONHASHSEED` for the run
   that writes the pickles when the tracked report must be reproducible. See TODO.md
   § Suspected bugs, item B11.
4. **The realization report is read by one exporter.** `export_keyboard_layout.py:128`
   takes the conjugation-feature legend from the tracked `realization_report.json`,
   while the Plover dictionary and drills use the keys recomputed on the inline path. Skip
   step 6 after a change of keypress groups and the legend disagrees with the dictionary
   (item B18).
5. **No command regenerates `starboard3h.json`.** Keyboard Layout Optimization (S4) is a
   real stage, but its solver call and the layout write are commented out
   (dictionary.py:494, :496). Eight error messages say "run dictionary.py once first to
   generate it"; `dictionary.py` only reads it.

## Recomputing after a fix

Read this before changing any of `resources/Lexique383.tsv`,
`resources/LexiqueInfraCorrespondance.tsv`, `resources/LexiqueMixte.tsv` or
`resources/LexiqueSynthetic.tsv`. The rebuild table above is the general chain; this
section is the fix-specific ordering. The two silent-failure traps are facts 2 and 4 above
(the pickle cache; the separately-tracked realization report).

Motivating incident (2026-09-20, the `évaser` fix): fixing `évaser`'s word-final-z
syllabification in `LexiqueSynthetic.tsv` changed which words collide in theory 1
(`évases` then correctly collided with `évase`/`évasent`). Rebuilding
`Dictionary.pickle`/`FirstTheory.pickle`/`theory2.tsv` alone was **not** enough —
`resolved_press_sets.json` stayed stale, so `évases` silently came out unmarked
(indistinguishable from "canonical") instead of getting the `pers_2` feature the elicited
answers said it should. Nothing errored; it was caught only because the outcome contradicted
the pers_3-default design rule.

**What is usually safe to skip:** the Grouping Phase groups the fixed vocabulary of ~194
atomic features (`pers_2`, `subjonctif`, …), not specific words — a lexicon fix essentially
never adds or removes atomic features, so `python -m util.build_keypress_groups` rarely needs
a rerun. Confirmed directly for the `évaser` case (both needed features already existed in
`keypress_groups.json`), not assumed. Skip it unless a fix introduces a genuinely new feature
requirement to a previously-unseen opposition — vanishingly unlikely for an ordinary
phonology or syllabification correction.

**Checklist for a fix that changes theory-1 collisions:**

1. Apply the fix (typically a scoped `util/fix*.py` dry-run + `--apply` script, patching the
   exact source file(s) plus `LexiqueMixte.tsv` directly rather than re-running `lexique.py`
   wholesale, to keep the diff scoped; a full `lexique.py` rerun is the safer check).
2. `rm -f Dictionary.pickle FirstTheory.pickle`
3. `python dictionary.py` — rebuilds theory 1; writes `theory2.tsv` from whatever Elicitation
   and Grouping Phase outputs currently exist (possibly stale at this point — expected).
4. `python -m src.elicitation` — re-derives `resolved_press_sets.json` against the fixed
   theory 1.
5. `python -m util.build_realization_report` — refreshes the tracked realization report
   (`realization_report.json`).
6. `python dictionary.py` again — rebuilds `theory2.tsv` against the now-fresh Elicitation
   Phase data (the pickles exist from step 3, so this run is fast).
7. Verify: `pytest src/test/`, plus a targeted collision check for the specific word(s) or
   lemma(s) the fix touched: group theory-2 output (loaded via `util/_theoryio.py`, not
   `theory2.tsv`) by final stroke and flag any group with ≥ 2 distinct `ortho` and ≥ 2
   distinct `lemmeGramCat`, excluding `reform1990.tsv` spelling-doublet pairs.

---

## Dataset states

The names below are used in every "Input state" and "Result" line.

| Name | Python shape | Created by | Persisted as |
|---|---|---|---|
| **source lexicons** | TSV/XML files | external, patched by fix scripts | `resources/Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`, `reform1990.tsv`, `lexiconExclusions.tsv`, `verbiste/*.xml` (tracked) |
| **raw lexicon rows** | `list[lexique.Word]` (a different dataclass from `src.word.Word`, lexique.py:547) | `Lexique.read_corpus` lexique.py:966 | no |
| **mixed lexicon** | TSV, 12 columns: `ortho phon lemme cgram cgramortho genre nombre infover syll_cv orthosyll_cv freqlivres freqfilms2`; 136,456 rows | `outputMixedLexique` lexique.py:1174 | `resources/LexiqueMixte.tsv` (tracked) |
| **synthetic lexicon rows** | same TSV plus a `source` column; 42,225 rows | Synthetic Lexicon Building (S2) scripts | `resources/LexiqueSynthetic.tsv` (tracked) |
| **Word list** | `list[src.word.Word]`, deduplicated by identity (`ortho, phonology, lemme, gramCat, gender, number`); 167,639 Words | `Dictionary.readCorpus` dictionary.py:92 | inside `Dictionary.pickle` (gitignored) |
| **syllable statistics** | `SyllableCollection` + `Syllable.*ColByPart` class state | `analyseSyllabification` dictionary.py:169 | `Dictionary.pickle` (objects 1-5) |
| **layout statistics** | best permutation, pairwise order matrix (`pairwiseBiphonemeOrderScore`) and `syllabicPartAmbiguity`, per syllabic part | `optimizeBiphonemeOrder` grammar.py:644, `analyseAmbiguities` dictionary.py:183 | `Dictionary.pickle` |
| **keyboard layout** | `Starboard` (26 keys; reserved keys 0, 1, 10, 15) | Keyboard Layout Optimization (S4), last run before 37fdc4e; loaded by `Keyboard.fromJSONFile` keyboard.py:252 | `starboard3h.json` (tracked, never rewritten by today's commands) |
| **theory 1** | `dict[Strokes, list[Word]]` keyed by raw Strokes; 80,725 entries | `Dictionary.buildTheory` dictionary.py:305 | `FirstTheory.pickle` (gitignored); human view `theory.tsv` |
| **homophone groups** | `dict[LemmaHomophoneGroupKey, list[Word]]`, key = (canonical Strokes, LemmeGramCat); 47,830 | `buildLemmaHomophoneGroups` elicitation.py:61 | no |
| **questionnaire items** | `list[QuestionnaireItem]`, one per distinct opposition; 200 | `buildQuestionnaireItems` elicitation.py:220 | `questionnaire.json` (gitignored) |
| **elicitation answers** | JSON list of `{atomsA, checkedA, atomsB, checkedB, …}`; 200 | a person, through the questionnaire page | `elicitation_answers.json` (tracked) |
| **resolved discriminating feature sets** | in memory `dict[LemmaHomophoneGroupKey, dict[WordOrtho, list[frozenset[str]]]]`; on disk a list of `{strokes, lemmeGramCat, pressSets, frequencies, readings}`; reloaded as `PressSetsByGroup` (group id `lemmeGramCat@strokes`); 47,828 groups | `resolveGroupPressSets` elicitation.py:374, `serializeResolvedPressSets` :471 | `resolved_press_sets.json` (gitignored) |
| **keypress groups** | `markersByKeypress: dict[int, frozenset[str]]` (K=7) + metadata | `minKeypressesSatWithPriorities` featuregroupingsat.py:490, `serializeAssignment` :530 | `keypress_groups.json` (tracked) |
| **keypress group population** | `groupToWords: dict[int, list[Word]]` + `extraGroupSetsByWord: dict[Word, list[frozenset[int]]]` | ambiguitychecker.py:803, :844 | no |
| **physical keypress group assignment** | `KeypressGroupPhysicalAssignment` (`chosenKeysByGroup`, cost, alternates, residual buckets) | `realizeKeypressGroupsAsExtraStroke` ambiguitychecker.py:987 | report build only: `realization_report.json` (tracked) |
| **final induced strokes** | `dict[Word, Strokes]`: base strokes plus at most one feature discriminating stroke | `buildFinalInducedStrokes` ambiguitychecker.py:1261 | no |
| **theory 2** | `dict[Word, list[Strokes]]`: index 0 primary (with its star/hash mark), then alternate entries | `Dictionary.buildFinalTheory` dictionary.py:342 | `theory2.tsv` (gitignored, read by nothing) |
| **Plover dictionary** | `dict[str, str]` (RTFCRE steno → spelling); 163,238 entries | `export_plover_dictionary.main` | `plover_stenalgo_dictionary.json` (tracked) |
| **Plover key table** | module with `KEYS`, `IMPLICIT_HYPHEN_KEYS`, `GEMINI_PR_KEYMAP` | `export_plover_system.main` | `plover_stenalgo/plover_stenalgo/_generated_keys.py` (tracked) |
| **trainer data** | JSON: `keyboard-layout`, `practice-words`, `practice-sentences`, `definitions` | trainer exporters | `steno-trainer/public/data/*.json` (tracked) |

---

## Overview

```
Lexicon Building (S1) ............................ python lexique.py
├─ module load: exclusions, 1990-reform tables, -eler/-eter verbs ... S1.1-S1.6
├─ Read and filter Lexique383 — read_corpus ...................... S1.7
│  └─ Attach grapheme-phoneme breakdowns — breakdownSyllables ..... S1.7.3
├─ Syllabification stats (and row reorder) ........................ S1.8
└─ Write the mixed lexicon — outputMixedLexique ................... S1.9  → LexiqueMixte.tsv

Synthetic Lexicon Building (S2) .................. manual --apply scripts  → LexiqueSynthetic.tsv
├─ Verb paradigm completion — completeVerbParadigms ............... S2.1
├─ NOM/ADJ gap generation — generateMissingNomAdjForms ............ S2.2
└─ Dual-form gap fillers, in-place repair ......................... S2.3, S2.4

Dictionary Loading (S3) .......................... python dictionary.py (first part)
├─ Dictionary cache check ......................................... S3.1  ← Dictionary.pickle
├─ Lexicon reading and identity merge — readCorpus ................ S3.2.1  (Word list)
├─ Syllable inventory — analyseSyllabification .................... S3.3  (syllable statistics)
└─ Dictionary cache write (after S4.1, S4.2) ...................... S3.4  → Dictionary.pickle

Keyboard Layout Optimization (S4) ................ rare, costly; solver call commented out
├─ Phoneme order search — optimizeBiphonemeOrder .................. S4.1  (layout statistics, every fresh rebuild)
├─ Ambiguity statistics — analyseAmbiguities ...................... S4.2  (layout statistics, every fresh rebuild)
├─ Fallback keymap — generateBaseKeymap ........................... S4.3  (only if starboard3h.json is missing)
└─ Layout solve — optimizeKeyboard (CP-SAT) ....................... S4.4  → starboard3h.json (no command today)

Phonetic Theory Building (S5) .................... python dictionary.py (second part)
├─ Keyboard layout loading — Starboard.fromJSONFile ............... S5.1  ← starboard3h.json
└─ Theory 1 construction — buildTheory ............................ S5.3  → FirstTheory.pickle, theory.tsv

Same-Lemma and Grammatical-Category Disambiguation (S6)
├─ Discriminating-Feature Elicitation (Elicitation Phase) .... python -m src.elicitation
│  ├─ Questionnaire Generation
│  │  ├─ Homophone group building — buildLemmaHomophoneGroups .... S6.Elicitation.1
│  │  └─ Questionnaire item selection — buildQuestionnaireItems .. S6.Elicitation.4 → questionnaire.json
│  ├─ Answer Collection (human loop) — questionnaire page ......... S6.Elicitation.5 → elicitation_answers.json
│  └─ Press-Set Resolution
│     ├─ Discriminating feature set resolution — resolveGroupPressSets  S6.Elicitation.9
│     └─ Serialization ............................................ S6.Elicitation.12 → resolved_press_sets.json
├─ Discriminating-Feature Grouping (Grouping Phase) .......... python -m util.build_keypress_groups
│  ├─ Exact minimum-K grouping — minKeypressesSatWithPriorities ... S6.Grouping.2
│  └─ Assignment serialization .................................... S6.Grouping.5 → keypress_groups.json
└─ Discriminating-Feature Stroke Realization (Realization Phase)  inline path in buildFinalTheory, and report build
   ├─ Keypress group population — buildKeypressGroupToWords ....... S6.Realization.2
   ├─ Coda key search — realizeKeypressGroupsAsExtraStroke ........ S6.Realization.5
   ├─ Final induced strokes (inline path) — buildFinalInducedStrokes  S6.Realization.6
   └─ Report serialization (report build) ......................... S6.Realization.8 → realization_report.json

Different-Lemma or Grammatical-Category Disambiguation (S7) .. inside Dictionary.buildFinalTheory (S7.1)
├─ Lemma-homophone group detection — groupHomophonesByReservedStroke  S7.5
├─ Star/hash code assignment + star/hash rule stack (R1-R7) ....... S7.7-S7.11
├─ Star/hash mark merge into the last phoneme stroke .............. S7.13
└─ Theory 2 report — writeFinalTheory ............................. S7.15 → theory2.tsv

Theory Export (S8) ............................... python -m util.export_*
├─ Theory 2 loading (recomputes theory 2) — loadFirstAndFinalTheory  S8.1
├─ Plover branch: dictionary, key table, plugin ................... S8.3-S8.5 → plover_stenalgo_dictionary.json, _generated_keys.py
└─ Trainer branch: legend, word drill, sentences, definitions ..... S8.6-S8.9 → steno-trainer/public/data/*.json
```

The two homophone problems have two mechanisms. Words that are forms of the same lemma and
grammatical category (dors/dort) are separated by Same-Lemma and Grammatical-Category
Disambiguation (S6), using grammatical features the user chose, realized as one extra
coda-bank stroke, the **feature discriminating stroke**. Words with different lemmas or
categories that still sound alike (ver/vert/verre, appel/appelle) are separated by
Different-Lemma or Grammatical-Category Disambiguation (S7), using **star/hash marks** on the
`*` and `#` keys. The two kinds of **extra stroke** are the feature discriminating stroke and
the **\*/# marker stroke** (the bare `*#` stroke of an escalated star/hash code). An
**alternate entry** (a second theory-2 stroke for a self-homograph) is a separate concept,
not an extra stroke.

---
## Lexicon Building (S1)

Lexicon Building (S1) turns the source lexicons into the mixed lexicon. Stenalgo needs
each word's phonemes grouped into syllables, split into onset/nucleus/coda, with the
letters of each syllable attached. Lexique383 alone has unreliable orthographic syllables;
LexiqueInfra supplies the grapheme-phoneme alignment. The stage reads
`Lexique383.tsv` (142,669 rows), drops 145 excluded and 17 `#`-prefixed rows, fixes lemmas,
attaches a syllable **breakdown** from `LexiqueInfraCorrespondance.tsv` (137,822 rows), then
drops the 4,852 **breakdown orphans** and 1,199 subjonctif-imparfait-only rows and applies
the 1990 spelling reform. Output: `resources/LexiqueMixte.tsv`, 136,456 rows, 12 columns.
Everything runs at module level: `lexique = Lexique()` (:1261),
`printSyllabificationStats()` (:1262), `outputMixedLexique(...)` (:1263).

Verified: running lexique.py:1-1260 in memory with the output redirected gives a file
**byte-identical** to the committed `LexiqueMixte.tsv`.

### Load lexicon exclusions — loadLexiconExclusions (S1.1)   lexique.py:38
Called by: module import (lexique.py:56, `ignoredList = frozenset(...)`).
Input state: `resources/lexiconExclusions.tsv` (`word reason note`): 134 entries — 99
`foreign_word`, 19 `unpopular_spelling`, 14 `data_defect`, 2 `unsupported_phoneme`.
Transformation: keeps only the words, as the frozenset `ignoredList`; the reason is documentation.
Result: 134 exact-match `ortho` strings. They drop 145 Lexique383 rows in Read and filter
Lexique383 (S1.7) and skip 144 LexiqueInfra rows in Attach grapheme-phoneme breakdowns (S1.7.3).
Artifacts: reads `resources/lexiconExclusions.tsv`.
Notes: `schampooiner` matches no row (stale). Not the same list as `excluded_words.txt`
(an **excluded word** is dropped in Dictionary Loading (S3)) or
`resources/ambiguityIgnoreList.tsv` (collision metric only).

### Reform and -eler/-eter tables (S1.2-S1.6)   lexique.py:98-537
Called by: module import. All five `APPLY_1990_REFORM_*` flags are `True` (:95, :145, :326, :420, :505/:534).
Input state: `resources/reform1990.tsv`, read by `_readReform1990Rows` (:98) and padded to 8
columns (`oldSpelling newSpelling category appliesToLemmeNormalization appliesToOrthoRewrite
appliesToPluralRewrite isException note`; 10 categories: 91 `autres_rectifications`, 65
`mots_empruntes_accent`, 40 `olle_otter`, 35 `mots_empruntes_pluriel`, 11 `circonflexe`, 11
`trema`, 9 `illier_illiere`, 6 `accent_grave`, 1 `numeraux_composes`, 1
`participe_passe_laisser`); `resources/verbiste/verbs-fr.xml`.
Transformation and result, one bullet per call (rows with `isException` are always skipped):
- **Load 1990-reform lemma table — loadReform1990Lemmes (S1.2)** :117, applied :131-132 —
  `appliesToLemmeNormalization` rows as `{old: new}`, merged into `spellingVariantLemme` (:71,
  seeded with `ile→île`): 56 entries.
- **Load 1990-reform ortho rules — loadReform1990OrthoRewrites (S1.3)** :196, bound :312-314 —
  `computeSingleEditRule` (:156) turns each `appliesToOrthoRewrite` pair into one
  `OrthoRewriteRule` (position, old prefix, old char, new char): a substitution, deletion or
  insertion; more than one edit raises at import. Keyed under `oldSpelling`; **only
  substitutions** also under `newSpelling` (:224-225), so a deletion is not re-applied to a
  reformed word (`grole` → `groe`, :214-223). `_reform1990OrthoRewrites`: 237 keys. With
  Load 1990-reform lemma table (S1.2), deletion/insertion rules miss inflected forms (item B6).
- **Load 1990-reform plural rewrites — loadReform1990PluralRewrites (S1.4)** :329, bound
  :374-377 — whole-word `{oldPlural: newPlural}`: 33 entries (`barmen→barmans`, `lieder→lieds`).
- **Load -eler/-eter qualifying verbs — loadElerEterQualifyingVerbs (S1.5)** :423, bound
  :481-484 — Verbiste template `app:eler` → `{lemme: "l"}`, `j:eter` → `{lemme: "t"}`, minus
  `APPELER_EXCEPTIONS` (:397) and `JETER_FAMILY_EXCEPTIONS` (:398, jeter + 7 compounds): 124
  verbs; plus `ELER_ETER_DERIVED_NOUN_VERBS` (:408), 9 `-ellement`/`-ettement` nouns.
- **Build one-off reform rules — computeSingleEditRule (S1.6)** :507, :536-537 — three rules:
  `_interpelerRule` for the 13 `INTERPELER_FIXED_FORMS` (:512; stressed présent and
  futur/conditionnel excluded on purpose, OQLF :498-504), `_absousRule`, `_dissousRule`.
Artifacts: reads `resources/reform1990.tsv`, `resources/verbiste/verbs-fr.xml`.

### Read and filter Lexique383 — read_corpus (S1.7)   lexique.py:966
Called by: `Lexique.__init__` (lexique.py:963), from `lexique = Lexique()` (:1261).
Input state: source lexicons: `Lexique383.tsv`, 142,669 rows, 35 columns.
Transformation: skips rows whose `ortho` starts with `#` (17) or is in `ignoredList` (145).
Builds a `lexique.Word` with ortho, phon, normalized lemma (S1.7.1), cgram, cgramortho,
genre, nombre, infover, syll, cv-cv, orthosyll, `freqlivres`, `freqfilms2`; appends it to
`self.words` and `words_by_ortho[ortho]`. Then calls Attach grapheme-phoneme breakdowns (S1.7.3).
Result: raw lexicon rows, 142,507 `lexique.Word`: 137,655 with a breakdown, 4,852 orphans.
Artifacts: reads `resources/Lexique383.tsv`.
Helpers not expanded: `printVerbose` (:34, debug print for the 6 words of `verboseList` :32).
Notes: `words`/`words_by_ortho` are class-level lists (lexique.py:957-958), see item B34.
Frequencies are copied verbatim; lemma frequencies and the other Lexique383 columns are dropped.

### Normalize lemma — normalizeLemme (S1.7.1)   lexique.py:540
Called by: Read and filter Lexique383 (S1.7), lexique.py:977.
Transformation: first `pronounParadigmLemme` (:81), keyed by (lemme, cgram): `ils→il`,
`elles→elle` (PRO:per), `celle/celles/ceux→celui` (PRO:dem). This puts pronoun forms under
one LemmeGramCat, so Same-Lemma and Grammatical-Category Disambiguation (S6) handles them,
not Different-Lemma or Grammatical-Category Disambiguation (S7). Otherwise `spellingVariantLemme` (`ile→île` + 55 reform lemmas), keyed by lemma only.
Result: 5 rows get a **pronoun paradigm lemma**, 149 a reform or variant lemma.
Notes: the lemma changes before the ortho rewrite looks rules up by lemma (item B6).

### Repair affricate syllabification — lexique.Word.__post_init__ (S1.7.2)   lexique.py:598
Called by: `lexique.Word(...)` in Read and filter Lexique383 (S1.7).
Transformation: saves `orig_syll`/`orig_cv_cv`; while `syll` and `cv_cv` have the same shape
(`isWellFormedCVSyll` :921), moves syllable breaks so a one-grapheme two-consonant sound
stays in one onset: `fix_x_k_s` (:608, `k-s`→`-ks` with `x`), `fix_g_dZ` (:619), `fix_j_dZ`
(:630), `fix_ch_tS` (:641, no ortho condition). Each recurses until stable.
Result: `cv_cv` rewritten on 2,344 rows (it is what the alignment walks; `syll` is not written out).

### Attach grapheme-phoneme breakdowns — Lexique.breakdownSyllables (S1.7.3)   lexique.py:1007
Called by: Read and filter Lexique383 (S1.7), lexique.py:998.
Input state: raw lexicon rows without breakdown + `LexiqueInfraCorrespondance.tsv`
(`item phono cgram grapheme assoc regTo_GP`; the **association** `assoc` is `grapheme-phoneme`
pairs joined by `.`, `#` for silent letters).
Transformation: for each non-excluded Infra row, takes the Lexique383 Words with that ortho
(`words_by_ortho[item]`, `KeyError` if absent) and breaks down every Word whose `phonology`
equals Infra `phono`. Second chance: rebuild a phonology from `assoc`
(`associationToPhonology` :1002) and retry — rescues 273 rows. A Word already broken down is
skipped (:755), so the first matching Infra row wins; 15,047 Infra orthos have several rows
with the same phono (one per cgram).
Result: 137,655 Words with `syll_cv: list[list[phoneme]]` and `orthosyll_cv:
list[list[(C|V|Y|#, grapheme)]]`. The 4,852 orphans are mostly multi-word expressions and
compounds (4,795 contain a space, hyphen or apostrophe): 3,491 NOM, 794 ADJ, 212 VER. One
real miss: `engraisser` VER `@gRese`.
Artifacts: reads `resources/LexiqueInfraCorrespondance.tsv`.
Notes: the match uses Infra `phono`, but the breakdown is built from `assoc`, which can
disagree. See item B3.

### Correct LexiqueInfra associations — Word.fixLexiqueInfraGraphPhon (S1.7.3.1)   lexique.py:652
Called by: Align associations onto syllables (S1.7.3.2), lexique.py:770.
Transformation: 18 hard-coded first-occurrence substitutions (`fixAssociation` :720) that
split a grapheme-phoneme pair straddling two syllables: `cc-ks`, `xc-ksk`, `rr-RR`, `oy-waj`,
`ill-ij`, `ui-8i`, `gu-g8`, `ey-Ej`, `ay-Ej.e-°`, `en-5n`, `enn-@n`, `en-@n`, `oo-oO`, `zz-dz`,
`gg-gZ`, `qu-k8`, `lli-ji`.
Result: an association whose pairs line up one-to-one with the C/V/Y slots.
Notes: only the first occurrence is fixed; a second straddling pair in one word stays merged.

### Align associations onto syllables — lexique.Word.breakdownSyllables (S1.7.3.2)   lexique.py:750
Called by: Attach grapheme-phoneme breakdowns (S1.7.3), lexique.py:1023, :1035.
Transformation: walks the `cv_cv` skeleton slot by slot, consuming pairs. Silent `#` pairs
attach to the current syllable (or the previous one at a syllable end). Rules: `skip_next_C`
(`ch-tS`, `x-ks/gz`, `g|j-dZ`, word-final `pp`), `skip_next_Y` (after `ij`/`Ej` and some
English `Ej`), Y slots only take glide-capable graphemes (`i ll o y u ill il ou l lli w ï`).
Leftover pairs or any exception print a diagnostic and **`sys.exit(1)`** the whole build (:904-918).
Result: `syll_cv`/`orthosyll_cv`, later written as `syll1ph1_syll1ph2|syll2…` by
`writePhonoSyll` (:746) / `writeOrthoSyll` (:742).
Helpers not expanded: `phonemesToSyllables` (:728), `lettersToSyllables` (:735).

### Syllabification stats (and row reorder) — printSyllabificationStats (S1.8)   lexique.py:1097
Called by: module body, lexique.py:1262.
Transformation: prints Lexique383 vs breakdown disagreements (52,942 syll/orthosyll count
mismatches, 306 syll/infrasyll mismatches after `moveDualPhonem` :1055, 137,329 matches) and
fills statistics nothing reads. **Side effect:** `self.words.sort(key=frequencyFilm,
reverse=True)` (:1101).
Result: no data change, but because Write the mixed lexicon (S1.9) sorts stably by ortho,
this sort fixes the order of rows sharing an ortho (film frequency, descending).
Notes: dropping this "print-only" call changes `LexiqueMixte.tsv` bytes and can change
first-seen tie-breaks in Dictionary Loading (S3).

### Write the mixed lexicon — outputMixedLexique (S1.9)   lexique.py:1174
Called by: module body, lexique.py:1263.
Input state: raw lexicon rows, broken down, reordered by Syllabification stats (S1.8).
Transformation: iterates rows sorted by **original** `ortho` (:1183), runs the seven steps
below in order, from Drop breakdown orphans (S1.9.1) to absous/dissous → absout/dissout (S1.9.7), then writes 12 columns: `ortho` (rewritten), `phon` (unchanged), `lemme` (normalized),
`cgram`, `cgramortho`, `genre`, `nombre`, `infover` (stripped), `syll_cv`, `orthosyll_cv`
(rewritten), `freqlivres`, `freqfilms2`.
Result: mixed lexicon, 136,456 rows (142,507 − 4,852 − 1,199).
Artifacts: writes `resources/LexiqueMixte.tsv`.
Notes: `cgramortho` is not recomputed after a rewrite; rewritten rows sit at their old sort
position (`acuponcture` where `acupuncture` was). Rewriting can duplicate an existing
identity (24 cases, item B9). `borough` has an `orthosyll_cv` that does not spell its ortho.

- **Drop breakdown orphans (S1.9.1)** lexique.py:1184 — rows with `orthosyll_cv == []` are
  skipped silently: 4,852 rows (`a priori`, `abaisse-langue`, …).
- **Strip subjonctif imparfait — stripSubjonctifImparfait (S1.9.2)** lexique.py:1155 —
  removes every `sub:imp*` tag from `infover`; returns `None` if nothing is left and the row
  is dropped. 1,199 rows dropped (`suffît`), 237 keep other tags. Out of scope since
  2026-09-21.
- **Apply reform ortho rewrite — orthoRewriteOccurrence / applyOrthoRewrite (S1.9.3)**
  lexique.py:1197-1203 — `rule = rewrites.get(word.lemme) or rewrites.get(word.ortho)`;
  `orthoRewriteOccurrence` (:229) finds which occurrence of the anchor to edit (or `None`
  outside the family); `applyOrthoRewrite` (:259) edits `ortho` and `orthosyll_cv` alike (a
  deletion also removes one adjacent separator; an insertion creates a digraph token).
  243 rows rewritten (`allégement→allègement`, `asseoir→assoir`); 77 harmless no-ops. Misses
  67 rows of 24 `-otter`/`-olle`/`-illier` lemmas (item B6).
- **Regularize -eler/-eter (S1.9.4)** lexique.py:1208-1215 — for qualifying verbs and the 9
  derived nouns, a doubled-consonant prefix (`amoncell`) becomes `è`+single consonant; the
  orthosyll string gets the first `e[_|]ll`→`è[_|]l`. 130 rows (`amoncelle→amoncèle`,
  `nivellement→nivèlement`).
- **Regularize loanword plurals — rewriteOrthosyllSuffix (S1.9.5)** lexique.py:1220-1224 —
  plural rows whose original ortho is a plural-rewrite key get the new plural; the orthosyll
  string keeps the shared prefix plus the new suffix. 33 rows (`ferries→ferrys`).
- **interpeller → interpeler (S1.9.6)** lexique.py:1229-1234 — `_interpelerRule` on the 13
  fixed forms. 13 rows.
- **absous/dissous → absout/dissout (S1.9.7)** lexique.py:1238-1244 — VER only; the ADJ
  homographs are left alone (:525-533). 2 rows.

The **reform rewrites** (Apply reform ortho rewrite (S1.9.3) through absous/dissous →
absout/dissout (S1.9.7)) change only `ortho`/`orthosyll_cv`, never `phon`.
**Reform lemma normalization** (S1.7.1) changes only `lemme`.

### One-shot fix scripts

Historical `util/fix*.py` patches, run by hand with `--apply`. "Mixte" = writes
`LexiqueMixte.tsv` directly; "Source" = the same fix also exists where `lexique.py` would
regenerate it (Lexique383, Infra, Verbiste or lexique.py code). **No fix is held only in
`LexiqueMixte.tsv` today** (a regeneration is byte-identical). † = source half completed by a
later companion script.

| Script | Patches | Mixte | Source | Purpose |
|---|---|---|---|---|
| fixAbregerFutureAccent | conjugations-fr.xml | no | n/a | abr:éger futur/cnd `è`→`é` |
| fixAdvenirRenaitreGaps | conjugations-fr.xml | no | n/a | adv:enir 3p présent; ren:aître participles |
| fixAsseoirDualFormGaps | Synthetic (append) | no | n/a | ass:eoir alternants (S2.3) |
| fixAsseoirDualFormGapsManual | Lexique383 tags, Synthetic | no | yes | 26 hand rows + missing tags |
| fixAyGraphemeEjQuality | Lexique383, Mixte | yes | yes† | `ay` is always open `Ej` |
| fixAyGraphemeInfraPhono | Infra | no | yes | same rule in Infra |
| fixCeSchwa | Lexique383, Infra, Mixte | yes | yes | `ce` /s2/ → /s°/ |
| fixCroitreMouvoirAccents | conjugations-fr.xml, Lexique383, Mixte | yes | yes | croître/mouvoir circumflex |
| fixDeleteWeatherVerbErrors | Lexique383, Mixte | yes | yes | drop 1st/2nd-person weather-verb rows |
| fixDuplicateInfTag | Lexique383, Mixte | yes | yes | `inf;;inf;;` → `inf;` |
| fixEstOuverteVoyelle | Lexique383, Infra, Mixte | yes | yes | `est` (être) /e/ → /E/ |
| fixEvaserWordFinalZSyllabification | Synthetic (in place) | no | n/a | évaser coda z (S2.4) |
| fixFoutreDefectiveTenses | conjugations-fr.xml | no | n/a | foutre passé simple / sub:imp |
| fixGniezInfraPhono | Infra | no | yes | completes fixGniezPronunciation |
| fixGniezPronunciation | Lexique383, Infra, Mixte | yes | yes† | `-gniez` keeps /j/ |
| fixGrelerFigurativePlural | conjugations-fr.xml | no | n/a | grêl:er 3p slots |
| fixInfPlusOtherTag | Lexique383, Mixte | yes | yes | spurious tag next to `inf` |
| fixLeguerEquerHarcelerAccent | conjugations-fr.xml | no | n/a | futur/cnd endings |
| fixMarinDateCorruption | Infra | no | yes | `Mar-05` → `maR5` (Excel) |
| fixMatirVerbTemplate | verbs-fr.xml | no | n/a | matir → fin:ir |
| fixMultiTagPartialMismatch | Lexique383, Mixte | yes | yes | drop tags not matching the ortho |
| fixOuirConditionnelOrder | conjugations-fr.xml | no | n/a | o:uïr cnd order |
| fixParticipeAdjNomVowelQuality | Lexique383, Mixte | yes | yes | ADJ/NOM take the VER row's E/e |
| fixParticipeMissingNombre | Lexique383, Mixte | yes | yes | blank `nombre` → `s` |
| fixParticipePlusOtherTag | Lexique383, Mixte | yes | yes | spurious tag next to `par:pas` |
| fixPayerAyGrapheme | Infra, Mixte | yes | yes | split `ay-Ej` in 3 infinitives |
| fixPayerDualFormGaps | Synthetic (append) | no | n/a | pa:yer i/y twins (S2.3) |
| fixPayerNonfuturVowelQuality | Lexique383, Mixte | yes | yes† | pa:yer présent vowel = E |
| fixResidualConjugationTemplates | conjugations-fr.xml | no | n/a | dép:ecer etc. primary alternative |
| fixResidualRowErrors | Lexique383, Mixte | yes | yes | 4 row fixes (`lamer` → `inf;`) |
| fixSourdreDefectiveGaps | conjugations-fr.xml, Lexique383, Mixte | yes | yes | sourdre slots |
| fixSpuriousDuplicateVerbRows | Lexique383, Mixte | yes | yes | duplicate VER/AUX rows |
| fixXlfnSingleCorruption | Infra | no | yes | `_xlfn.SINGLE(...)` (Excel) |
| completeVerbParadigms | Synthetic (append) | no | n/a | Verb paradigm completion (S2.1) |
| generateMissingNomAdjForms | Synthetic (append) | no | n/a | NOM/ADJ gap generation (S2.2) |
| splitEtudierVerbisteTemplate, splitAnglicismErVerbisteTemplate | Verbiste XML | no | n/a | split aim:er for the ending tables |
| change_ai-E_to_ai-e_endings.sh, change_eCe_to_ECe_words.sh | `*_modified` copies | no | manual copy-back | early bulk phonology edits |
| copyLineFromTo.py | `<file>.out` | no | n/a | generic column substitution helper |

A Mixte-only patch can still be lost by a later `python lexique.py` if a future script
patches Mixte without its source, or matches Mixte by the pre-reform ortho. The "Recomputing
after a fix" section below still recommends patching Mixte directly alongside the source (to
keep diffs scoped); a full `lexique.py` rerun is the safer check.

---
## Synthetic Lexicon Building (S2)

Synthetic Lexicon Building (S2) fills gaps in the paradigms of the mixed lexicon (missing verb
forms, missing NOM/ADJ gender or number forms, dual spellings) and appends the generated rows
to `resources/LexiqueSynthetic.tsv`. It is its own stage, not part of Lexicon Building (S1):
its scripts read theory 1 or the lexicon TSVs, write a different file, and are run by hand.

None of these runs in a rebuild. Each is a dry run unless given `--apply`. `lexique.py`
never reads or writes `resources/LexiqueSynthetic.tsv`: 42,225 **synthetic rows** (35,928
VER, 3,896 NOM, 2,401 ADJ), mixed-lexicon columns plus `source` (always `synthetic`), all
frequencies 0.0, no duplicates, no `sub:imp` rows (removed in fd7e242 by an unrecorded edit).
6,759 rows share an identity with a mixed-lexicon row and only merge their `infover`; 31,252
become new Words.

The NOM/ADJ side optionally cross-checks against **Morphalou 3.1** (ATILF/CNRS,
LGPL-LR), an external download from the
[Ortolang repository](https://repository.ortolang.fr) — extract the CSV to
`morphalou/Morphalou3.1_CSV.csv` (gitignored; the code default path); `--morphalou PATH`
overrides and `--no-morphalou` disables it.

### Verb paradigm completion — completeVerbParadigms.main (S2.1)   util/completeVerbParadigms.py:350
Called by: a person, `python -m util.completeVerbParadigms [--apply]`.
Input state: theory 1 (mixed lexicon + current synthetic rows), Verbiste XML, `resources/verbModelExceptions.tsv`.
Transformation: caps its address space at 4 GiB (`_capMemory` :343); loads templates
(`loadVerbisteTemplates` verbparadigm.py:48, `loadVerbModelExceptions` :67,
`parseConjugationTemplates` :190); runs the **legacy** `extractDiscriminatingFeatures`
(src/featureextractor.py:31); then the five steps below, Load theory 1 (S2.1.1) to Append
synthetic rows (S2.1.5).
Result: VER synthetic rows (participle gender/number forms and finite forms).
Artifacts: reads `FirstTheory.pickle`, `starboard3h.json`, Verbiste, `verbModelExceptions.tsv`; appends to `LexiqueSynthetic.tsv`.
Notes: its gating depends on the retired solver-picks-features design; the selection it
gates on (`selectSharedDiscriminators` src/featureextractor.py:222) is coverage-first, with a
feature-complexity tie-break. Not idempotent (item B13).

- **Load theory 1 — loadTheoryAndKeyboard (S2.1.1)** :91 — unpickles `FirstTheory.pickle`,
  or builds a `Dictionary` and theory 1 in memory without writing. A stale pickle hides rows
  appended since the last rebuild.
- **Derive conjugation ending tables — deriveConjugationEndingTables (S2.1.2)**
  verbparadigm.py:493 — donors are VER Words with a trusted template (`getTrustedTemplate`
  :88: Verbiste, or an exception with status `regular`/`family_template`) and an attested
  infinitive (`ortho == lemme`, :433). Per template and field (`phonology`, `rawSyllCV`,
  `rawOrthosyllCV`): infinitive suffix = longest common suffix of donor infinitives; for each
  attested finite tag, ending = slot value minus an infinitive-length radical (:561); keeps
  the most common ending with match rate and donor count. Result: `ConjugationEndingTables`
  (:467). The radical is cut by character count on the raw `|`/`_` string (item B2).
- **Find structural candidates — findStructuralCandidates (S2.1.3)** :165 — for each
  **undersampled lemma** found by Detect undersampled lemmas (S2.1.3.1), fills missing
  participle gender/number slots with Generate missing participles (S2.1.3.2) and missing
  finite slots of `allFiniteSlots` (:407, which excludes `inf`, `par:pre`, `par:pas`,
  `sub:imp`, `FINITE_SLOT_EXCLUDED_CODES` :397) with Generate missing finite forms
  (S2.1.3.3), gated by `MIN_FINITE_MATCH_RATE = 1.0` (:73). Result: (lemmeGramCat, info,
  generated Word, reference Word) candidates.
  - *Detect undersampled lemmas (S2.1.3.1)* verbparadigm.py:681 — per trusted template, a
    lemma whose legacy feature space (`fullFeatureSpace` :119) is a strict subset of the union
    of its siblings'. Lemmas without siblings are skipped.
  - *Generate missing participles (S2.1.3.2)* :367 — ortho from the Verbiste `par:pas`
    ending (`infinitiveRadical` :239, `generateOrthoForm` :252); phon and `syll_cv` copied
    from the donor participle (`spliceParticiplePhon` :296); `orthosyll_cv` = donor radical +
    `""/s/e/es` (:344); `infover = "par:pas;"`.
  - *Generate missing finite forms (S2.1.3.3)* :577 — ortho = Verbiste radical + ending;
    each phonological field = infinitive value truncated by the suffix length + the table
    ending (:611); `None` below the match rate.
- **Confirm by legacy collision check — confirmCandidates (S2.1.4)** :266 —
  temporarily adds each candidate to its reference word's theory-1 entry
  (`temporarilyAugmented` :238), reruns `extractDiscriminatingFeatures` and
  `buildDiscriminatorSelection` (featureextractor.py:284) and keeps only lemmas in
  `newlyCollidingLemmas` (verbparadigm.py:646). Others are "irrelevant to disambiguation today".
- **Append synthetic rows — writeSynthetic (S2.1.5)** :324 — appends one line per
  confirmed candidate; no deduplication against the file.

### NOM/ADJ gap generation — generateMissingNomAdjForms.main (S2.2)   util/generateMissingNomAdjForms.py:99
Called by: a person, `python -m util.generateMissingNomAdjForms [--apply] [--morphalou PATH | --no-morphalou]`.
Input state: mixed lexicon + synthetic rows (`loadWords` nomAdjParadigm.py:415, minus
`excluded_words.txt`), `resources/nomAdjModelExceptions.tsv` (:76), optionally
`morphalou/Morphalou3.1_CSV.csv` (:477, **untracked**; without it only the ending tables are used).
Transformation: for each NOM/ADJ LemmeGramCat (`attestedSlots` :100) and missing slot, picks a
source slot (`chooseSourceSlot` :566), skips `invariable` exceptions and the forms flagged by
Enumerate missing slots (S2.2.2), then uses Exception-table override (S2.2.3) or
Morphalou-authoritative form (S2.2.4). Skips a candidate whose ortho already exists for the lemma in either TSV
(`loadAllOrthosByLemme` :392).
Result: about 6.3k NOM/ADJ synthetic rows. No collision check is run.
Artifacts: appends to `LexiqueSynthetic.tsv` (:191).

- **Derive NOM/ADJ ending tables (S2.2.1)** nomAdjParadigm.py:250 — lemmas with ≥2 attested
  slots give per-field (fromSuffix, toSuffix) per slot pair, grouped by gramCat and by 3-, 2-
  and 1-letter ortho ending class (`orthoClassKeys` :227); keeps the mode with match rate and
  donor count (`NomAdjEndingTables` :236).
- **Enumerate missing slots (S2.2.2)** :132 / :166 — NOM expects `s`/`p` per attested gender,
  ADJ all four slots. No row when the number changes and the ortho ends in `s`/`z`, a NOM
  singular or an ADJ ends in `x`, or the gender changes and the ADJ ends in one of
  `ADJ_INVARIANT_GENDER_SUFFIXES` (:159).
- **Exception-table override — overrideCandidate (S2.2.3)** generateMissingNomAdjForms.py:77
  — `irregular` rows supply `override_ortho` and `override_phonology` (blank → source phon
  as placeholder, :88); **`syll_cv`/`orthosyll_cv` always come from the source word** (:94).
  See item B7.
- **Morphalou-authoritative form (S2.2.4)** nomAdjParadigm.py:522 → `generateMissingForm`
  (:309) — class keys from most to least specific, match rate 1.0 and
  `MIN_DONOR_COUNT_BY_CLASS_KEY_LENGTH` {3:1, 2:2, 1:4} (:306); cross-axis ADJ go through a
  same-gender detour. Morphalou confirms (`morphalou`), replaces the ortho
  (`morphalou_override`, :562, keeping donor phon/`syll_cv`/`orthosyll_cv`) or leaves it
  unverified (`donor_table`).

### Dual-form gap fillers (S2.3) and in-place synthetic repair (S2.4)
- `util/fixPayerDualFormGaps.py` main :113 — adds the missing `i`/`y` twin forms of pa:yer
  verbs (`balaie`/`balaye`) from a per-(slot, form type) ending table (match rate 1.0).
- `util/fixAsseoirDualFormGaps.py` main :103 — same method for the 2- and 3-way ass:eoir
  alternations (`ié`/`eye`/`oi`).
- `util/fixAsseoirDualFormGapsManual.py` main :204 — 26 hand rows (`NEW_SYNTHETIC_ROWS`,
  `(ortho, lemme)` dedup :173) plus `TAG_ONLY_FIXES` written into `Lexique383.tsv`
  (:142-163). Its header (:34-43) records an earlier fix lost by patching `LexiqueMixte.tsv` only.
- `util/fixEvaserWordFinalZSyllabification.py` main :109 — rewrites the `évaser` rows with
  phon `evaz` so the word-final `z` is a coda (`|z_#` → `_z_#`); the only script editing
  synthetic rows in place. The defect is systemic (item B2).

### Consumption
`LexiqueSynthetic.tsv` is consumed only by Lexicon reading and identity merge (S3.2.1); its
other readers are generators and validators (`validateLexiconAgainstNomAdjParadigms`,
`crossCheckNomAdjWithMorphalou`).

---
## Dictionary Loading (S3)

Dictionary Loading (S3) reads the mixed lexicon (136,456 rows) and the synthetic lexicon rows
(42,225) into the Word list (167,639 Words, by descending film frequency): it drops excluded
words, merges identical identities, indexes Words by spelling and lemma and registers every
syllable (5,866) in the syllable statistics. It is the first part of `python dictionary.py`
(`__main__` :448), cached in `Dictionary.pickle`; on a cache miss the layout statistics (S4.1,
S4.2) run between Syllable inventory (S3.3) and Dictionary cache write (S3.4).

### Dictionary cache check — __main__ (S3.1)   dictionary.py:451
Called by: `python dictionary.py` (`__main__` :448).
Transformation: if `Dictionary.pickle` exists, loads five objects (the `Dictionary`, then
`Syllable.allPhonemeCol`, `phonemeColByPart`, `biphonemeColByPart`,
`multiphonemeColByPart`, assigned back onto the class, :453-457) and skips Dictionary
construction (S3.2), Syllable inventory (S3.3), the layout statistics (S4.1, S4.2) and
Dictionary cache write (S3.4). No staleness check.
Result: Word list + syllable statistics + layout statistics, restored.
Artifacts: reads `Dictionary.pickle`.
Notes: four downstream loaders repeat this five-object read (util/_theoryio.py:26-30,
src/elicitation.py:540-543, util/check_conjugation_disambiguation_order.py:141-144,
src/ambiguitychecker.py:1334-1337); none uses the class state. Cache trap: item B15.

### Dictionary construction — Dictionary.__init__ (S3.2)   dictionary.py:76
Called by: Dictionary cache check (S3.1), on a miss.
Transformation: creates the empty `SyllableCollection`, indexes and three ambiguity dicts
(`syllabicAmbiguity`, `lexicalAmbiguity`, `syllabicPartAmbiguity`, each keyed by part), then
calls `readCorpus`.
Result: `Dictionary` with the Word list filled; statistics empty.

### Lexicon reading and identity merge — Dictionary.readCorpus (S3.2.1)   dictionary.py:92
Called by: Dictionary construction (S3.2).
Input state: mixed lexicon, then synthetic lexicon rows (`wordSources`, :66-69, `source`
column ignored); a missing file is skipped silently (:117).
Transformation:
- `resources/top500_film.txt`: first line's last field (907,046.92) → `totalFrequencies`;
  the next 200 spellings → `frequentWords` (**frequent words**, `nbFrequentWords`=200, :63).
- `excluded_words.txt`: 44 spellings (`alèze`, `d`, `s`, `bitte`); drops 52 rows. `#`-prefixed
  orthos are dropped too (0 today).
- **Identity merge** (:113-137): identity = `(ortho, phon, lemme, cgram, genre, nombre)`. A
  later row with a known identity only folds its `infover` into the first Word
  (`mergeInfoVerb`) or is dropped. 10,990 rows fold (10,973 with a tag, 17 without); 6,759
  synthetic rows share an identity with a mixed-lexicon row. **The first row's syllabification and frequency win**: 5,369
  folded rows had another `syll_cv`, 6,028 another film frequency (item B9).
- Otherwise builds a `Word` (Word construction (S3.2.1.1)) and indexes it in
  `wordsByLemme[lemme]` (bare lemma) and `wordsByOrtho[ortho]`.
Result: Word list, 167,639 Words in load order (136,456 + 42,225 − 52 − 10,990);
`wordsByOrtho` 147,732 spellings, `wordsByLemme` 43,111 lemmas.
Artifacts: reads `resources/LexiqueMixte.tsv`, `resources/LexiqueSynthetic.tsv`, `resources/top500_film.txt`, `excluded_words.txt`.
Helpers not expanded: `GramCat[...]` lookup (src/word.py:10).

### Word construction — Word.__post_init__ (S3.2.1.1)   src/word.py:84
Called by: Lexicon reading and identity merge (S3.2.1).
Transformation: runs the four syllable-break exceptions on `rawSyllCV`/`rawOrthosyllCV`,
parses them into `syllCV`/`orthosyllCV` (`list[list[str]]`), sets `frequency =
frequencyFilm` (:93; book frequency is ignored — the **film frequency**), sets `_hash =
hash(ortho+phonology+lemme+gramCat.name+gender+number)` (:94: salted per process, no
separators), parses `_infoVerb`, sets `lemmeGramCat = f"{lemme}_{gramCat.name}"`.
Result: one Word.
Helpers not expanded: `parseOrthoSyll` :358, `parsePhonoSyll` :365, `splitInfoVerb` :102.
Notes: `__eq__`/`__hash__` use only `_hash` (:155, :161); see items B11 and B27.

The four **syllable-break exceptions** (steno reasons, not phonology):
- **e+n syllable repair — fix_e_n_en (S3.2.1.1.1)** word.py:202 — `@|n_` → `@|`, `e|n_` →
  `en|` ("enivre"), recursively; every row.
- **-rdre infinitive split (S3.2.1.1.2)** word.py:215 — verbs only; a last syllable ending
  `_R_d_R_#` splits off `d_R_#` (ortho `_r_d_r_e` alike): `perdre` = `pER|dR`, so it does not
  canonicalize onto `perdent`/`perde`.
- **-ayer conditionnel split (S3.2.1.1.3)** word.py:248 — verbs only; `_E_#` + `R_j_` →
  `…|R|j_…` (ortho `r_i_(ez|ons)` alike): `paieriez` = `pE|R|je`; onset `R`=8 ⊂ `j`=(8,9) would
  otherwise merge it with `payez`.
- **-uer glide split (S3.2.1.1.4)** word.py:297 — verbs only; a last syllable ending `_8_a` or
  `_8_@` splits off the vowel (ortho `^(.*_u)_(ant|as|ât|a)$`): `tua` = `t8|a`. Nucleus
  `8`=(11,12) would subsume `a`=12 and `@`=11. The phonetic and orthographic tests are
  independent; no row mismatches today.

### Verb-tag fold-in — Word.mergeInfoVerb (S3.2.1.2)   src/word.py:129
Called by: Lexicon reading and identity merge (S3.2.1).
Transformation: strips `;`, skips empty or known tags, appends, re-parses `_infoVerb`.
Result: one Word with the union of verb tags, hence of **feature combinations** (e.g.
synthetic `sub:pre:1s` added to a Lexique383 `ind:pre:1s` row). The incoming `syll_cv` is
not compared.

### Syllable inventory — Dictionary.analyseSyllabification (S3.3)   dictionary.py:169
Called by: `__main__` (:463), after Dictionary construction (S3.2).
Transformation: sorts `self.words` **in place** by descending frequency (:171) — this order
persists into `Dictionary.pickle` and into every theory-1 entry's list. For each Word, zips
phonetic syllable names with orthographic syllables (:177) and registers each pair
(Syllable registration (S3.3.1)) with weight `frequency`, or 0 for the 200 frequent words (:174).
Result: syllable statistics: 5,866 `Syllable` objects + class-level phoneme, biphoneme and
multiphoneme collections. The syllable lookup feeds Theory 1 construction (S5.3); the
frequencies feed the layout statistics (S4.1, S4.2).
Notes: `zip` truncates for the 99 Words whose two syllable lists differ in length (item B28).

- **Syllable registration — updateSyllable (S3.3.1)** grammar.py:803 — creates
  `Syllable(name, spelling)` on first sight, adds frequency (Frequency accumulation
  (S3.3.1.2)), records the Word in `phonoWords[phonology]` (`trackWord` :612). `buildTheory`
  later looks syllables up here.
- **Onset/nucleus/coda decomposition — Syllable.__init__ (S3.3.1.1)** grammar.py:468 —
  resolves each character to a shared `Phoneme` (`ValueError` for anything outside the 16
  nucleus, 20 consonant and 1 temporary `x` phonemes); classifies by position (rule 2 of the
  phonetic stroke rule, Phonetic Theory Building (S5); 0 syllables have a consonant between
  two vowels; 237 have ≥2 vowels, almost all with `8`, e.g. `l8i`); counts per-part
  phonemes, ordered consonant pairs and cross-vowel pairs as `Biphoneme`s (:525-561) and the
  whole part as a `Multiphoneme` (:562-567): 184 onset, 28 nucleus, 141 coda multiphonemes.
  `phonemeNamesByPart()` (:569) feeds the stroke rule.
- **Frequency accumulation — increaseSpellingFrequency (S3.3.1.2)** grammar.py:586 — adds
  to spelling, syllable, phonemes and biphonemes (`increaseFrequency` :574). Multiphonemes
  are never updated: all 353 have frequency 0.0 (item B31).
- **Collection sorting — sortPhonemesCollections (S3.3.2)** grammar.py:592 — sorts
  phonemes and biphonemes by frequency (read by Fallback keymap (S4.3) and Layout solve (S4.4)).

### Dictionary cache write — pickle.dump ×5 (S3.4)   dictionary.py:467-472
Called by: `__main__`, on a cache miss, after Phoneme order search (S4.1) and Ambiguity
statistics (S4.2).
Result: `Dictionary.pickle` (57.8 MB): Word list, indexes, syllable collection (with
`phonoWords` Word references), ambiguity dicts, then the four `Syllable` class collections.
Artifacts: writes `Dictionary.pickle`.

---
## Keyboard Layout Optimization (S4)

Keyboard Layout Optimization (S4) chooses which keys type which phoneme, per syllabic part,
and produces the keyboard layout `starboard3h.json`. It is a real stage, rarely run and
costly (several CP-SAT solves), not dead code. Its layout was last produced by an
uncommitted run and committed in 37fdc4e (2026-09-13); every later stage reads that file.

The two **layout statistics**, Phoneme order search (S4.1) and Ambiguity statistics (S4.2),
run on **every fresh rebuild** (a `Dictionary.pickle` miss, dictionary.py:464-466; S4.2 is
the slowest step) and are the solver's inputs (src/cpsatsolver.py:14, :48
`syllabicPartAmbiguity`; :363 `pairwiseBiphonemeOrderScore`). The solver call itself is
**commented out** at dictionary.py:494, and so is the layout write at :496: **today no
command regenerates `starboard3h.json` without editing code** (TODO.md § Queued follow-ups).

**The objective in plain words.** The solver solves one independent model per syllabic
part (onset, nucleus, coda), because each part has its own key bank. It gives every phoneme
one stroke of its bank and minimizes the sum of three costs:
1. *Ambiguity* (×30,000): when two phoneme groups that occur in real words would end up with
   the same keys, the words that differ only by those groups become indistinguishable; the
   cost is how frequent those words are (the syllabic-part ambiguity), times 30,000.
2. *Ergonomics* (×1): each phoneme's frequency times the physical cost of its stroke, so
   frequent phonemes get the easiest keys.
3. *Phoneme order* (×500): phoneme pairs whose keys read left-to-right in the order they are
   usually spoken earn a bonus; pairs in the wrong order pay a penalty.
Each part is solved for at most 90 s. Because frequencies are per million, one ambiguous
pair outweighs almost any ergonomic or order gain.

### Phoneme order search — Syllable.optimizeBiphonemeOrder (S4.1)   src/grammar.py:644
Called by: `__main__` (dictionary.py:464), on a `Dictionary.pickle` miss.
Input state: syllable statistics.
Transformation: for each part, runs a greedy local search (`BiphonemeCollection.optimizeOrder`
:318): n passes, each moving every phoneme to the insertion point that maximizes
`scorePermutation` (:347: +frequency for each biphoneme typed in order, −frequency out of
order), starting from `set` order (so it depends on the hash seed, item B30). Then
`generateBiphonemeOrderMatrix` (:361) records, for every pair, `<`/`>`/`=` and the score
difference of p1-before-p2 vs after (`pairwiseBiphonemeOrderScore`, :387).
Result: layout statistics: **best permutation** and **pairwise order matrix** per part.
Today: onset `dZksvptgzSmnbflNRwj`, coda `bjgpfwsktdvRNzlmnSZ`, nucleus `8ieE§5Oao92@`.
README.md:92-146 shows these.
Notes: read by Fallback keymap (S4.3) and the order term of Layout solve (S4.4) (cpsatsolver.py:363),
plus `writeConstrainFiles` (call commented :481) and `printBarchart`. Nothing in
Phonetic Theory Building (S5) reads it.

### Ambiguity statistics — Dictionary.analyseAmbiguities (S4.2)   dictionary.py:183
Called by: `__main__` (dictionary.py:466), on a `Dictionary.pickle` miss.
Input state: Word list + syllable statistics.
Transformation: three scorers:
- `analysePhonemSyllabicAmbiguity` (grammar.py:1032, 3 forked processes,
  `syllabicAmbiguityScore` :841): "if one key meant both p1 and p2, which syllables merge" —
  adds min(freq(syllable), freq(mutated)) or, when both are present, the two smaller of the
  three frequencies.
- `analysePhonemeLexicalAmbiguity` (:1098, `lexicalPhonemeAmbiguityScore` :883): same at word
  level via `Word.replaceSyllables` (word.py:369). Looks up a word phonology as a syllable
  name at :913, :931 (item B29).
- `analyseMultiphonemeLexicalAmbiguity_serial` (:1138, `lexicalSyllabicPartAmbiguityScore`
  :975): for every pair of whole-part phoneme groups, swaps group 1 for group 2 and adds
  min(word frequency, mutated-word frequency) when the mutated word exists — the
  **syllabic-part ambiguity**.
Result: layout statistics: `syllabicAmbiguity`/`lexicalAmbiguity` 190/120/190 pairs
(onset/nucleus/coda); `syllabicPartAmbiguity` 16,836/378/9,870 pairs, zeros included.
Notes: `syllabicPartAmbiguity` feeds Layout solve (S4.4); `lexicalAmbiguity` feeds Fallback keymap (S4.3).

### Fallback keymap — Dictionary.generateBaseKeymap (S4.3)   dictionary.py:212
Called by: `__main__`, **only** if `starboard3h.json` is missing (:489-492).
Transformation: per part, the N most frequent phonemes (N = 8/4/10 single keys) get single
keys in best-permutation order; the rest take 2-, 3-, 4-key strokes (`getPossibleStrokes`
keyboard.py:521) with a per-key overuse cap `2 + 2·(len−2)`; leftovers share the stroke of
their lowest-`lexicalAmbiguity` partner (`getLowAmbiguityPhonemes` :296).
Result: an in-memory starting layout, never saved; every exporter would still fail without
`starboard3h.json`.
Helpers not expanded: `Starboard.addToLayout` keyboard.py:417, `getStrokesOfPhoneme` :466.

### Layout solve — optimizeKeyboard (S4.4)   src/cpsatsolver.py:13
Called by: nothing today (dictionary.py:494, commented out:
`optimizeKeyboard(starboard, dictionary.syllabicPartAmbiguity, ["onset", "nucleus", "coda"])`).
The import at dictionary.py:32 still loads OR-Tools on every `import dictionary`.
Input state: keyboard layout (as hints), layout statistics, syllable statistics.
Transformation: one CP-SAT model per syllabic part, the objective described above:
- *Decision:* each phoneme gets one stroke among the legal 1-4-key strokes of its bank
  (`getPossibleStrokes`, ordered by `strokeIsLowerThen`), with 1 to `maxKeysPerPhoneme`
  (5/4/5) keys; sharing a stroke is allowed but penalized.
- *Ambiguity term:* a phoneme group's key-set is the union of its phonemes' keys (digraph
  subsumption). For the 2,000 most ambiguous group pairs (`MAX_MULTIPHONEMES`), identical
  key-sets cost `syllabic-part ambiguity × AMBIGUITY_PENALTY` (30,000).
- *Ergonomic term:* `phoneme frequency × stroke cost × STROKE_ASSIGNMENT_PENALTY` (1); stroke
  cost = `FingerWeights` per finger press (keyboard.py:47-71) + zig-zag and row-gap
  penalties, × 0.85^fingers (`getStrokeCost` keyboard.py:547); an illegal stroke has no cost
  and cannot be chosen.
- *Order term:* `pairwise order score × ORDER_PENALTY` (500), signed by which stroke is
  further left; a shared stroke pays half. `SOLVER_TIME` = 90 s per part.
Result (if run): `keyboard.clearLayout()` (:422) then the solved strokes; destructive (item
B32). The write (`toJSONFile`, dictionary.py:496) is commented out too.
Notes: consistent with the committed layout sharing entries only among rare phonemes (`N`,
`G`, `9`, `O`, `w`). See also `src/cpsatprinter.py`.

---
## Phonetic Theory Building (S5)

Phonetic Theory Building (S5) loads the committed keyboard layout and maps every Word to its
**base strokes**, one stroke per syllable. The result is theory 1, `dict[Strokes, list[Word]]`
with 80,725 entries. Words with the same raw Strokes land in the same **theory-1 entry**;
this is where homophones first appear. Everything later starts from theory 1. It is the
second part of `python dictionary.py` (dictionary.py:487-505), cached in `FirstTheory.pickle`.

### The phonetic stroke rule

1. **Syllables come from the lexicon.** `syll_cv` (e.g. `p_E_R|d_R_#`) is split on `|` into
   syllables and on `_` into phonemes; silent `#` is dropped
   (`phonemesToSyllableNames(withSilent=False)`, src/word.py:341). The four syllable-break
   exceptions can move a break during Word construction (S3.2.1.1).
2. **Each syllable is split into onset / nucleus / coda** (src/grammar.py:499-518):
   consonants before the first vowel → onset; every vowel → nucleus; every consonant after
   the first vowel → coda. Vowels are the 16 nucleus phonemes `aeiE@o°§uy5O9821` (so `8` = ɥ
   is a vowel, `j` and `w` are consonants). A vowel-less syllable (63 kinds: `dR`, `n`, `pst`)
   puts all its consonants in the onset: an **onset-only stroke**.
3. **Each phoneme becomes its layout key tuple** for its part (see Phonetic stroke
   rule (S5.3.1)), concatenated onset → nucleus → coda in spoken order, kept whole: no sort, no
   deduplication. This is the **raw Stroke**.
4. **A word's Strokes** is the tuple of its syllables' raw Strokes: 1 to 9 strokes, mostly 2-4.
5. **Theory 1 keys on the raw Strokes** (dictionary.py:312). Two Words share an entry when
   they have the same syllable count and, syllable by syllable, the same key sequence:
   - same phonemes and breaks: true homophones and paradigm forms. 41,640 entries hold ≥2
     spellings (**theory-1 collisions**), 951 more hold only homographs; the largest has 18
     spellings (`aller`/`allez`/`allé`/`haler`/`hâlé`…);
   - different phonemes in one **shared layout entry**: onset key 9 = `w`/`N`/`G`, nucleus 11
     = `@`/`9`, nucleus (11,12) = `°`/`8`, nucleus 14 = `e`/`O`, coda 16 = `j`/`b`/`w`, coda 24
     = `Z`/`G`;
   - differences in silent letters only.
6. **Theory 1 misses collisions that differ only in key order or repeats.** A stroke is
   physically a set of keys. Raw Strokes with the same **canonical form**
   (`canonicalizeStrokes`, src/keyboard.py:31) type identically but sit in different entries,
   through **digraph subsumption** (coda `k`=18 + `d`=19 = `g`=(18,19)) or order (`@tR` "entre"
   vs `@Rt` "heurte"). 233 canonical Strokes merge 2+ raw entries (**canonical-only
   collisions**), all with different spellings; 4,535 raw Strokes repeat a key. Later stages
   canonicalize before testing collisions; `theory.tsv` and raw-key counts under-report.
7. Different syllable breaks give different Strokes for equal phonemes (`ka/n` vs `kan`),
   which is why item B2 matters.

### Keyboard layout loading — Keyboard.fromJSONFile (S5.1)   src/keyboard.py:252
Called by: `__main__` (dictionary.py:488).
Input state: `starboard3h.json` (tracked, 211 lines).
Transformation: `json.load` with an `object_hook` that `ast.literal_eval`s tuple-like keys;
builds a `Starboard` via `cls.__new__` + `__dict__.update`, **bypassing `__init__`**. Only
`FileNotFoundError` becomes `None` (then Fallback keymap (S4.3) runs).
Result: keyboard layout:
- `nbKeys` 26; `allowedKeys` = the 22 non-reserved keys (**reserved keys** 0, 1, 10, 15, `_reservedKeys` keyboard.py:320).
- banks: onset 2-9 (left fingers), nucleus 11-14 (thumbs), **coda bank** 16-25 (right fingers).
- `phonemesAssignedToStroke: dict[Stroke, list[str]]`, 48 **layout entries**. Each of the
  20 consonants has one onset and one coda entry; each of the 16 vowels one nucleus entry.
  Single keys — onset `k`2 `s`3 `p`4 `v`5 `m`6 `t`7 `R`8 `w/N/G`9; nucleus `@/9`11 `a`12 `i`13
  `e/O`14; coda `j/b/w`16 `s`17 `k`18 `d`19 `t`20 `R`21 `n`22 `l`23 `Z/G`24 `m`25. Others are
  2-4-key tuples (onset `j`=(8,9), `l`=(6,7); nucleus `1`=(11,12,13,14); coda `g`=(18,19),
  `z`=(22,23), `S`=(24,25)). In a shared entry, list order is priority; `keyDisplayName` uses the first.
Artifacts: reads `starboard3h.json`.
Helpers not expanded: `Starboard.printLayout` keyboard.py:395.
Notes: produced by Keyboard Layout Optimization (S4). "3h" is apparently solve time
(keyboard.py:758-759 names a missing `starboard1h.json` "1h optimization").

### Theory-1 cache check — __main__ (S5.2)   dictionary.py:498
Called by: `__main__`.
Transformation: loads `FirstTheory.pickle` if present and skips Theory 1 construction (S5.3)
through Theory-1 cache write (S5.5). Not keyed on `Dictionary.pickle` or `starboard3h.json`
(item B15).
Result: theory 1.

### Theory 1 construction — Dictionary.buildTheory (S5.3)   dictionary.py:305
Called by: Theory-1 cache check (S5.2) on a miss; also `util/completeVerbParadigms.py:109`.
Input state: Word list (frequency-descending), syllable statistics, keyboard layout.
Transformation: for each Word, looks up each syllable in `syllableCollection.syllable_names`
(`KeyError` if missing), turns it into a stroke (Phonetic stroke rule (S5.3.1)) and appends the Word to
`theory[raw Strokes]`.
Result: theory 1: 80,725 entries covering 167,639 Words; 42,591 entries with ≥2 Words
(129,505 Words), 41,640 with ≥2 spellings. Strokes per entry: 1 → 3,111; 2 → 20,701; 3 →
33,534; 4 → 18,069; 5+ → 5,310. Every entry's list is frequency-descending.
Notes: legality of the whole stroke is never checked: 529 Words (39 canonical strokes, mostly
"-isme", coda `z`(22,23)+`m`(25)) contain an **illegal stroke** (item B8).

#### Phonetic stroke rule — Starboard.getStrokeOfSyllableByPart (S5.3.1)   src/keyboard.py:607
Called by: Theory 1 construction (S5.3).
Transformation: for each part in onset → nucleus → coda order and each phoneme in spoken
order, `getStrokesOfPhoneme(phoneme, part)` (:466) returns the layout entries whose first
key is in the part's bank and which list the phoneme; the first (JSON order) is used and its
keys appended as-is. No sort, dedupe or legality check. No entry → `IndexError` (none today:
all 36 phonemes are covered).
Result: one raw Stroke per syllable: `plyR` → `(4, 6,7, 11,13, 21)`; `ce` (`s°`) → `(3, 11,12)`.

### Theory-1 report — Dictionary.writeTheory (S5.4)   dictionary.py:317
Called by: Theory-1 cache check (S5.2), on a miss.
Transformation: one line per theory-1 entry: `strokesToString(strokes)` (:622) + sorted
spellings; prints the entry with most spellings and the one with highest summed frequency.
Result: `theory.tsv` (80,726 lines with header).
Artifacts: writes `theory.tsv`.
Notes: `strokesToString` spells each key by the first phoneme of its single-key entry, so
"aller" shows as `a/mte` (`l` = keys 6,7 = "m"+"t"): a key spelling, not a transcription, and
not RTFCRE.

### Theory-1 cache write — pickle.dump (S5.5)   dictionary.py:504
Result: `FirstTheory.pickle` (52 MB). Its Words are copies of the Word list and compare equal
only through the stored `_hash`.
Artifacts: writes `FirstTheory.pickle`.
Notes: control then reaches the `buildFinalTheory` block (dictionary.py:521-541), described
under Different-Lemma or Grammatical-Category Disambiguation (S7).

---
## Same-Lemma and Grammatical-Category Disambiguation (S6)

```
Discriminating-Feature Elicitation (Elicitation Phase) — python -m src.elicitation (src/elicitation.py:527)
 Questionnaire Generation
  S6.Elicitation.1 Homophone group building — buildLemmaHomophoneGroups (src/elicitation.py:61)
  S6.Elicitation.2 Feature combination enumeration — wordFeatureCombinations / featureCombinationsByOrtho (:30, :86)
  S6.Elicitation.3 Scale report — reportScale (:164)                                        [print only]
  S6.Elicitation.4 Questionnaire item selection — buildQuestionnaireItems (:220)
 Answer Collection (human loop, side tools)
  S6.Elicitation.5 Questionnaire page — util/build_questionnaire_page.py main (:521)
  S6.Elicitation.6 Precedence-spec check — util/check_conjugation_disambiguation_order.py main (:130)
 Press-Set Resolution
  S6.Elicitation.8 Answer indexing — buildAnswersByOpposition (:279)
  S6.Elicitation.9 Discriminating feature set resolution — resolveGroupPressSets (:374)
    S6.Elicitation.9.1 Per-combination resolution — resolvePressByCombination (:312)
  S6.Elicitation.10 Discriminating feature set conflict validation — validateElicitation (:425)
  S6.Elicitation.11 Per-spelling frequency table — buildFrequencyByGroupOrtho (:449)
  S6.Elicitation.12 Serialization — serializeResolvedPressSets (:471)

Discriminating-Feature Grouping (Grouping Phase) — python -m util.build_keypress_groups (util/build_keypress_groups.py:49)
S6.Grouping.1 Discriminating feature set reload — loadResolvedPressSets / loadGroupOrthoFrequencies (src/featuregrouping.py:33, :48)
S6.Grouping.2 Exact minimum-K grouping — minKeypressesSatWithPriorities (src/featuregroupingsat.py:490)
  S6.Grouping.2.1 Set-of-feature-sets dedup — groupSignatures (:40)
  S6.Grouping.2.2 Minimum-K scan — minKeypressesSat → _feasibleAssignment (:417, :183)
  S6.Grouping.2.3 Distinctness model — _buildDistinctnessModel (:51)
  S6.Grouping.2.4 Hard constraints — _aloneAndMustDifferPairs / _addMustDifferPairs (:120, :108)
  S6.Grouping.2.5 Soft preference tiers — _bestAssignmentWithPriorities (:358)
  S6.Grouping.2.6 Alphabetical tie-break — _breakTiesAlphabetically (:153)
S6.Grouping.3 Ground-truth verification — verifyKeypressAssignment (src/featuregrouping.py:160)
S6.Grouping.4 Usage weights — frequencyWeightedChordSizes (src/featuregrouping.py:189)          [report only]
S6.Grouping.5 Assignment serialization — serializeAssignment (src/featuregroupingsat.py:530)

Discriminating-Feature Stroke Realization (Realization Phase) — inline path in Dictionary.buildFinalTheory (dictionary.py:373-389)
                                      and report build util/build_realization_report.py main (:38)
S6.Realization.1 Word lookup indexes — buildWordToStrokes / buildWordsByOrthoLemme (src/ambiguitychecker.py:553, :766)
S6.Realization.2 Keypress group population — buildKeypressGroupToWords (:803)
  S6.Realization.2.1 Entry-to-Word resolution — _resolveEntryWord (:776)
S6.Realization.3 Extra alternate population — buildKeypressGroupExtraAlternates (:844)
S6.Realization.4 Preferred key resolution — resolvePreferredKeysByGroup (:952)
S6.Realization.5 Coda key search — realizeKeypressGroupsAsExtraStroke (:987)
  S6.Realization.5.1 Candidate ranking — _bestCandidate (:1177)
  S6.Realization.5.2 Candidate feasibility — _feasible (:1099)
  S6.Realization.5.3 Candidate cost — _candidateCost (:1147)
  S6.Realization.5.4 Word finalization — _finalizeReadyWords (:1066)
  S6.Realization.5.5 Final verification and residual buckets — (:1219-1258)
S6.Realization.6 Final induced strokes (inline path) — buildFinalInducedStrokes (:1261)
S6.Realization.7 Alternate entry strokes (inline path) — buildExtraInducedStrokes (:1288)
S6.Realization.8 Report serialization (report build) — build_realization_report.main (:74-112)
```

Theory 1 cannot tell apart the inflected forms of one paradigm (dors/dort, finis/finit); their
`lemmeGramCat` is the same, so Different-Lemma or Grammatical-Category Disambiguation (S7)
does not handle them either. Same-Lemma and Grammatical-Category Disambiguation (S6) takes
theory 1 and the hand-made elicitation answers and produces the final induced strokes: each
Word's base strokes plus, when the Word needs grammatical **features**, one extra coda-bank
**feature discriminating stroke**. "Same lemma" here always means same `lemmeGramCat` (lemma +
grammatical category). It has three phases:

- **Discriminating-Feature Elicitation (Elicitation Phase)** finds every **homophone group**
  (same `lemmeGramCat`, same canonical Strokes) and turns the person's answers into, per
  spelling, alternate **discriminating feature sets** (atomic features such as `pers_2`, `f`).
- **Discriminating-Feature Grouping (Grouping Phase)** packs the 13 live features into the
  smallest number K of **keypress groups** that still separates every spelling (K=7 today).
- **Discriminating-Feature Stroke Realization (Realization Phase)** gives each keypress group
  one physical coda-bank key, greedily and under collision checks, and appends one feature
  discriminating stroke per Word that needs features.

### Discriminating-Feature Elicitation (Elicitation Phase)

Entry: `python -m src.elicitation`, `__main__` at src/elicitation.py:527. Loads
`Dictionary.pickle` (restoring the class state, :538-543) and `FirstTheory.pickle`
(:545-546). Of its three named sub-steps, the command runs **Questionnaire Generation** and
**Press-Set Resolution** and asks nothing. **Answer Collection** is the human loop between
them (rebuild step 4h): a person checks, per opposition, which atomic features to press for
each side, producing the elicitation answers. It is needed only when Press-Set Resolution
reports unresolved oppositions.

#### Questionnaire Generation

##### Homophone group building — buildLemmaHomophoneGroups (S6.Elicitation.1)   src/elicitation.py:61
Called by: Elicitation Phase entry (:548); also the precedence-spec check (:148) and the
pers_3 rewrite (:169).
Input state: theory 1, 80,725 raw-Strokes keys, 167,639 Words.
Transformation: re-keys theory 1 by canonical form (`canonicalizeStrokes` keyboard.py:31),
splits each bucket by `lemmeGramCat` (`groupWordsByLemme` word.py:414) and keeps sub-groups
with more than one Word. Different-`lemmeGramCat` homophones are left to Different-Lemma or
Grammatical-Category Disambiguation (S7).
Result: homophone groups, `dict[(canonical Strokes, LemmeGramCat), list[Word]]`, 47,830, in
theory-1 order.
Notes: the key type is named `LemmaHomophoneGroupKey` (:24) although it is keyed by
`lemmeGramCat`; a rename is queued (TODO.md § Queued follow-ups).

##### Feature combination enumeration — wordFeatureCombinations / featureCombinationsByOrtho (S6.Elicitation.2)   src/elicitation.py:30, :86
Called by: every step that walks a group (Scale report (S6.Elicitation.3), Questionnaire item
selection (S6.Elicitation.4), Discriminating feature set resolution (S6.Elicitation.9) and
Per-combination resolution (S6.Elicitation.9.1)).
Transformation: a Word with verb tags yields one **feature combination** per tag, split into
atomic features by `Word.splitInfoVerb` (word.py:102): `ind:pre:1p` → {indicatif, présent,
pers_1, nbr_p}. Only participle combinations also get the Word's gender and number and a
`VER` feature (:47-51). Subjonctif imparfait combinations are dropped (:56, scope decision
2026-09-19). A Word without tags yields one combination {gender, number}, possibly empty.
`featureCombinationsByOrtho` merges all Words sharing an `ortho` into one combination list.
Result: `dict[WordOrtho, list[FeatureCombination]]` per group; a feature combination is a
`frozenset[str]` of atomic features.
Notes: from here on, the Elicitation Phase reasons per spelling; the Realization Phase must
map a spelling back to one Word (**spelling twins**, item B1).

##### Scale report — reportScale (S6.Elicitation.3)   src/elicitation.py:164
Called by: Elicitation Phase entry (:549).
Transformation: enumerates every cross-spelling feature-combination pair
(`enumerateOppositionSamples` :107) and prints: distinct **oppositions**, **tie oppositions**
(two spellings with the same feature combination — no feature can separate them), maximum
combination size, co-occurring feature pairs, and two Welsh-Powell greedy colorings
(`_greedyColorCount` :126) as a rough K estimate.
Result: console only.
Notes: labelled "K lower bound" (:560-561) although a greedy coloring is an upper bound (docstring :127-129).

##### Questionnaire item selection — buildQuestionnaireItems (S6.Elicitation.4)   src/elicitation.py:220
Called by: Elicitation Phase entry (:570).
Transformation: one example pair per distinct opposition, scored by (number of "clean"
spellings — spellings with only this feature combination in the group — then summed corpus
frequency); the best pair is kept; items are ranked by frequency and given positional ids `q0…`.
Result: questionnaire items, 200 today.
Artifacts: writes `questionnaire.json` (:572-573).
Notes: ids are renumbered every run. Answers store `id`, `orthoA/B`, `lemma`, `reviewed`,
`clean`, but resolution uses only `atomsA/B` + `checkedA/B` (:578-584); `reviewed` is ignored.

#### Answer Collection (human loop)

##### Questionnaire page — build_questionnaire_page.main (S6.Elicitation.5)   util/build_questionnaire_page.py:521
Called by: a person (rebuild step 4h).
Transformation: reads `questionnaire.json` at import (:12), injects items and French feature
labels (`LABELS` :15) into an HTML/JS page with two spellings and their feature checkboxes per
item. Answers go to the Artifact `db` document `progress/answers` (:478, :511); a person
copies them into `elicitation_answers.json` by hand. No code reads the `db` document back.
Artifacts: reads `questionnaire.json`; writes `elicitation_questionnaire.html`.

##### Precedence-spec check — check_conjugation_disambiguation_order.main (S6.Elicitation.6)   util/check_conjugation_disambiguation_order.py:130
Called by: a person (optional).
Input state: theory 1 + elicitation answers; recomputes Homophone group building
(S6.Elicitation.1), Answer indexing (S6.Elicitation.8) and Per-combination resolution
(S6.Elicitation.9.1) itself.
Transformation: `parsePrecedenceOrder` (:43) reads the **precedence spec**
`conjugation_disambiguation_order.txt` up to `---`, but uses it only for the feature
vocabulary (:137, "unknown atoms" report): **precedence is never enforced or checked.**
`classifyCombination` (:63) assigns each feature combination a family;
`checkPressByOrthoCombination` (:90) applies three rules: (1) a participle combination with
gender/number ⊆ {m, s} must have an empty discriminating feature set; (2) a non-empty
impératif or infinitif set must be exactly that feature; (3) a non-empty subjonctif set is
`subjonctif` plus at most one `pers_*`/`nbr_*`.
Result: console summary; never rewrites answers.
Artifacts: reads the spec, `elicitation_answers.json`, pickles; writes `conjugation_disambiguation_report.json`.
Notes: coverage gaps: item B12.


#### Press-Set Resolution

Turns the stored answers into each spelling's discriminating feature sets (the sub-step keeps
the code's name, `resolveGroupPressSets` / `resolved_press_sets.json`).

##### Answer indexing — buildAnswersByOpposition (S6.Elicitation.8)   src/elicitation.py:279
Called by: Elicitation Phase entry (:585).
Input state: elicitation answers (200), as `AnsweredOpposition` (`combinationA`=atomsA, `pressA`=checkedA, …).
Transformation: indexes answers by `frozenset({combinationA, combinationB})`; disagreeing
duplicates are reported and dropped, agreeing ones collapsed.
Result: `AnswerByOpposition`, 200 keys, 0 duplicates.
Artifacts: reads `elicitation_answers.json` (:576-577).

##### Discriminating feature set resolution — resolveGroupPressSets (S6.Elicitation.9)   src/elicitation.py:374
Called by: Elicitation Phase entry (:586), and again inside Discriminating feature set conflict validation
(S6.Elicitation.10).
Input state: homophone groups + `AnswerByOpposition`.
Transformation: calls Per-combination resolution (S6.Elicitation.9.1), then collapses the
per-combination sets to one list per spelling, deduplicated and sorted by (size, sorted
features). Index 0, the smallest, is the **primary alternate**. A **self-homograph** spelling
("calmez": impératif or indicatif 2p) keeps one **alternate** per distinct feature
combination instead of their union (the calmez fix). A spelling whose primary alternate is
`∅` is the group's **canonical member**.
Result: resolved discriminating feature sets, 47,828 groups; 9,692 spellings have >1
alternate; 4,858 groups have no `∅` member (every spelling in them gets an extra stroke).

###### Per-combination resolution — resolvePressByCombination (S6.Elicitation.9.1)   src/elicitation.py:312
Called by: Discriminating feature set resolution (S6.Elicitation.9); Elicitation Phase entry
(:616, for `readings`); precedence-spec check (:161).
Transformation: skips groups with <2 spellings (2 groups). For each cross-spelling pair of
different feature combinations, looks up that opposition's answer and unions each side's
checked features into that (spelling, combination)'s set. Tie oppositions are skipped
(:356-357). A missing answer (an **unresolved opposition**) drops the whole group (:360-363).
Result: `dict[group, dict[(ortho, FeatureCombination), frozenset[str]]]` + unresolved oppositions (0 today).
Notes: a combination's set is the union over every partner spelling in its group. Dropped
groups keep their base strokes and no later check sees them.

##### Discriminating feature set conflict validation — validateElicitation (S6.Elicitation.10)   src/elicitation.py:425
Called by: Elicitation Phase entry (:587).
Transformation: recomputes Discriminating feature set resolution (S6.Elicitation.9) and flags
any discriminating feature set held (as any alternate) by two different spellings of one
group: a **discriminating feature set conflict** (`GroupConflict` :414). Two alternates of one spelling may
be equal.
Result: 0 conflicts; conflicting groups would be dropped (:611-614).
Notes: Per-combination resolution (S6.Elicitation.9.1) runs three times per invocation (:586,
inside :587, :616) with identical results.

##### Per-spelling frequency table — buildFrequencyByGroupOrtho (S6.Elicitation.11)   src/elicitation.py:449
Called by: Elicitation Phase entry (:615).
Transformation: each spelling gets the maximum film frequency of its Words; the 200 frequent
words get 0.0 so they do not inflate usage weights.
Result: `dict[group, dict[ortho, float]]`, used only by Usage weights (S6.Grouping.4).

##### Serialization — serializeResolvedPressSets (S6.Elicitation.12)   src/elicitation.py:471
Called by: Elicitation Phase entry (:617).
Transformation: one entry per group: `strokes` (canonical), `lemmeGramCat`, `pressSets`
(ortho → list of sorted feature lists), `frequencies`, and `readings` (parallel to
`pressSets`: the feature combinations that resolved to each alternate). Stable sort by
`lemmeGramCat`.
Result: resolved discriminating feature sets on disk, 47,828 entries (about 32 MB).
Artifacts: writes `resolved_press_sets.json` (:620).
Notes: `readings` is read only by the trainer exporters.

### Discriminating-Feature Grouping (Grouping Phase)

Entry: `python -m util.build_keypress_groups`, `main` at :49. An atomic feature is
**live** if some resolved discriminating feature set contains it (13 today). The other 7
questionnaire features (`VER`, `indicatif`, `m`, `nbr_s`, `participe`, `présent`, `s`) are
**unpressable**: nobody checked them. Pressing a keypress group asserts every feature it
carries. A **keypress group conflict** (`KeypressConflict` featuregrouping.py:150) is two spellings of one
group inducing the same set of keypress groups.

#### Discriminating feature set reload — loadResolvedPressSets / loadGroupOrthoFrequencies (S6.Grouping.1)   src/featuregrouping.py:33, :48
Called by: Grouping Phase entry (:53-54).
Transformation: re-keys each entry by `lemmeGramCat@strokes`, alternates as frozensets,
frequencies in a parallel map. Also reads `questionnaire.json` (optional, :57-61) for the full
feature inventory.
Result: `PressSetsByGroup` (47,828 groups) + `FrequencyByGroup`.
Artifacts: reads `resolved_press_sets.json`, `questionnaire.json`.

#### Exact minimum-K grouping — minKeypressesSatWithPriorities (S6.Grouping.2)   src/featuregroupingsat.py:490
Called by: Grouping Phase entry (:63-65) with `ALONE_KEYS`={f},
`MUST_DIFFER_GROUPS`={{infinitif, pers_1, pers_2, pers_3}} and `PREFERENCE_TIERS`
(build_keypress_groups.py:39-45).
Transformation: sorts live features alphabetically (:511); reduces groups to their sets of
feature sets; finds the minimum K under **hard grouping rules** only; applies the **soft
preference tiers** at that K; then the alphabetical tie-break.
Result: `(numKeys=7, colorOf: feature → keypress group id, achieved=[1, 1, 0])`.

- **Set-of-feature-sets dedup — groupSignatures (S6.Grouping.2.1)** :40 — each group becomes
  its **homophone group set of feature sets** (a frozenset of per-spelling alternate sets,
  with spellings, strokes and lemmas removed; the code type is `GroupSignature`),
  deduplicated and canonically sorted: 294 distinct sets from 47,828 groups.
- **Minimum-K scan — minKeypressesSat → _feasibleAssignment (S6.Grouping.2.2)** :417, :183 —
  for K = 1…20, builds the distinctness model plus hard constraints; INFEASIBLE → next K; the
  first FEASIBLE K is the proven minimum; UNKNOWN (30 s limit) raises (:226-229). K=7.
- **Distinctness model — _buildDistinctnessModel (S6.Grouping.2.3)** :51 — Booleans
  `x[m,k]`, one keypress group per feature; `t[k]` = "this discriminating feature set touches
  keypress group k"; every pair of sets of **different** spellings must differ on some `k`
  (exact XOR linearization, :96-103); alternates of one spelling are exempt. Mirrors
  Ground-truth verification (S6.Grouping.3) exactly.
- **Hard constraints (S6.Grouping.2.4)** :120, :108 — `aloneKeys` → (m, every other live
  feature) pairs; `mustDifferGroups` → all pairs inside; each pair gets `x[m1,k] + x[m2,k] ≤ 1`.
  Can raise K.
- **Soft preference tiers — _bestAssignmentWithPriorities (S6.Grouping.2.5)** :358 —
  lexicographic at fixed K: tier 0 maximizes {p, nbr_p} sharing a keypress group; tier 1
  {future, passé}; tier 2 minimizes other features sharing the keypress group of {nbr_p, p}
  (`_sameKeyScoreExpr` :308, `_exclusiveGroupExtraCountExpr` :329). Each tier is locked by
  equality before the next (:405). Cannot raise K.
- **Alphabetical tie-break — _breakTiesAlphabetically (S6.Grouping.2.6)** :153 — per feature
  in alphabetical order, minimizes its keypress group index and locks it. Single-threaded,
  seed 0 (`_newDeterministicSolver` :139). Unique lexicographic minimum, provided every solve
  is OPTIMAL (item B24).

#### Ground-truth verification — verifyKeypressAssignment (S6.Grouping.3)   src/featuregrouping.py:160
Called by: Grouping Phase entry (:69); also tests.
Transformation: for every alternate, computes the **induced discriminating feature set**
(`inducedPressSet` :135, the union of the features of every keypress group touched) and
reports a keypress group conflict when two spellings induce the same set. Any conflict aborts the
write (:70-71).
Result: `[]`.

#### Usage weights — frequencyWeightedChordSizes (S6.Grouping.4)   src/featuregrouping.py:189
Called by: Grouping Phase entry (:74).
Transformation: per keypress group, sums the frequency of every spelling whose alternates touch it.
Result: reported only; the Realization Phase computes its own costs.

#### Assignment serialization — serializeAssignment (S6.Grouping.5)   src/featuregroupingsat.py:530
Called by: Grouping Phase entry (:76-82).
Result: keypress groups: `keypressCount` 7, `markersByKeypress` {0: conditionnel+infinitif,
1: f, 2: future+passé+pers_3, 3: imparfait+subjonctif, 4: impératif+pers_1, 5: nbr_p+p, 6:
pers_2}, hard/soft provenance, 7 unpressable features, usage weights.
Artifacts: writes `keypress_groups.json`.
Notes: **K history** from git: K=5 at 8330b8e and 0fa69af; K=6 from 4e73533 (impératif
answer fix); **K=7 from 688c74d** (per-combination alternates) to HEAD. The claim that the
hard constraints cost nothing extra was checked at K=6 only. The greedy grouping path is
gone (removed as dead code; the CP-SAT solver is the only one); `src/featuregrouping.py`
now holds only the loaders and verifiers (`loadResolvedPressSets`,
`loadGroupOrthoFrequencies`, `liveMarkers`, `inducedPressSet`, `KeypressConflict`,
`verifyKeypressAssignment`, `frequencyWeightedChordSizes`).

### Discriminating-Feature Stroke Realization (Realization Phase)

One sequence of calls, two code paths. The **inline path** runs inside
`Dictionary.buildFinalTheory` (dictionary.py:373-389) and feeds theory 2 and every exporter
(util/_theoryio.py:82). The **report build** is `util/build_realization_report.py` main
(:58-72) and writes the **realization report**. Both read `keypress_groups.json`
and `resolved_press_sets.json`. Only the trainer keyboard legend reads the report, so the two
can drift (item B18, TODO.md § Queued follow-ups).

**The realization rule.** Each keypress group gets one physical **key-set**. **Candidate
key-sets** are the coda-bank keys of the 20 consonants: single keys 16-25 and the digraphs
(16,17), (16,18), (17,19), (18,19), (20,22), (22,23), (24,25); unions of two are tried only if
no single one fits. A Word whose primary alternate touches groups {g1, g2, …} gets **one**
feature discriminating stroke — the sorted union of those groups' keys — after its base
strokes (`_appendCodaExtraStroke` :892); its last base stroke is unchanged. Groups are
decided greedily, largest population first. The cost is the frequency-weighted
`getStrokeCost` of the real composed feature discriminating stroke. A **preferred key** per
feature (`PREFERRED_KEYS_BY_MARKER` :945: impératif → 18 `-k`, pers_2 → 19 `-d`, pers_3 → 20
`-t`) wins whenever feasible.

#### Word lookup indexes — buildWordToStrokes / buildWordsByOrthoLemme (S6.Realization.1)   src/ambiguitychecker.py:553, :766
Called by: both paths (dictionary.py:373-374; build_realization_report.py:58-59).
Result: `Word → raw base strokes` and `(ortho, lemmeGramCat) → [Word]`, in theory-1 order.

#### Keypress group population — buildKeypressGroupToWords (S6.Realization.2)   src/ambiguitychecker.py:803
Called by: both paths (dictionary.py:375; build_realization_report.py:60).
Input state: resolved discriminating feature sets (JSON list) + `markersByKeypress`.
Transformation: per spelling, uses only the primary alternate `alternates[0]` (:832); skips
an empty one (canonical member); resolves the spelling to one Word (Entry-to-Word resolution
(S6.Realization.2.1)) and appends it to every keypress group whose features intersect the
primary set.
Result: keypress group population `groupToWords` (Words per group: g5 48,724; g1 15,295; g2
11,735; g4 7,334; g6 6,707; g0 3,922; g3 3,882).

##### Entry-to-Word resolution — _resolveEntryWord (S6.Realization.2.1)   src/ambiguitychecker.py:776
Called by: Keypress group population (S6.Realization.2) and Extra alternate population
(S6.Realization.3).
Transformation: among the Words with this (ortho, lemmeGramCat), returns the **first** whose
canonical base strokes equal the entry's canonical `strokes`; if none, falls back to
`candidates[0]` (:800).
Result: exactly one Word per spelling.
Notes: when a spelling has several matching Words (spelling twins, 262 spellings in the
current resolved sets), only the first gets its feature discriminating stroke. See TODO.md § Suspected bugs, item B1
(fallback: item B20).

#### Extra alternate population — buildKeypressGroupExtraAlternates (S6.Realization.3)   src/ambiguitychecker.py:844
Called by: both paths (dictionary.py:376-378; build_realization_report.py:65-67).
Transformation: for spellings with ≥2 alternates, maps each non-primary, non-empty
alternate to the set of keypress groups it touches.
Result: `extraGroupSetsByWord: Word → [frozenset[group id]]` (second half of the keypress group population).

#### Preferred key resolution — resolvePreferredKeysByGroup (S6.Realization.4)   src/ambiguitychecker.py:952
Called by: both paths (dictionary.py:379; build_realization_report.py:68).
Transformation: maps each preferred feature to its keypress group in this run (group ids
change between runs of the Grouping Phase); features that are not live are skipped.
Result: {4: (18,), 6: (19,), 2: (20,)}.

#### Coda key search — realizeKeypressGroupsAsExtraStroke (S6.Realization.5)   src/ambiguitychecker.py:987
Called by: both paths (dictionary.py:380-383; build_realization_report.py:69-72).
Input state: keypress group population + theory 1 + keyboard layout + preferred keys.
Transformation: builds `wordToGroups` (:882), the per-phoneme coda candidates (`codaKeysOf`,
in `Phoneme.consonantPhonemes` order) and `allWords`, the **set** of every Word in any group
(:1047). Decides groups in descending population order (:1205): takes the first candidate
from Candidate ranking (S6.Realization.5.1), or records the group in `unassignedGroups`; runs
Word finalization (S6.Realization.5.4); finally runs Final verification and residual buckets
(S6.Realization.5.5).
Result: physical keypress group assignment (`KeypressGroupPhysicalAssignment` :904): g0→21, g1→16,
g2→20, g3→23, g4→18, g5→17, g6→19 — all single keys, all three preferences honored.
Helpers not expanded: `_composedInduced` (:1077), `_isRedundantForAnyWord` (:1084),
`buildWordToGroups` (:882), `_appendCodaExtraStroke` (:892), `Keyboard.getStrokeCost` (keyboard.py:547).

- **Candidate ranking — _bestCandidate (S6.Realization.5.1)** :1177 — every distinct
  single-phoneme coda key-set, keeping the feasible ones with their cost; pairs
  (`comboSize`=2) only if none is feasible. Stable sort by cost (ties keep phoneme order,
  :1192). A feasible preferred key moves or is inserted first (:1195-1200); otherwise the
  preference is recorded as not honored (:1201-1202).
- **Candidate feasibility — _feasible (S6.Realization.5.2)** :1099 — rejects a candidate when:
  (a) it equals an already chosen key-set (:1104); (b) it is empty or redundant for some Word;
  (c) some Word's composed feature discriminating stroke is an illegal stroke
  (`getStrokeCost` → None, :1112); (d) some composed Strokes is an existing theory-1 key (raw
  comparison, :1114); (e) a **same-lemmeGramCat collision** (`_isInScopeCollision` :968:
  different ortho, same `lemmeGramCat`) among Words needing the same full group set
  (:1125-1133); (f) such a collision with an already finalized Word (:1140-1144).
  Cross-category and cross-lemma collisions never block.
- **Candidate cost — _candidateCost (S6.Realization.5.3)** :1147 — `round(Σ freq·cost(composed
  stroke) / Σ freq)` over the group's Words (isolated cost if the weight is 0). Using the
  real composed stroke lets same-column combinations earn the keyboard's discount.
- **Word finalization — _finalizeReadyWords (S6.Realization.5.4)** :1066 — a Word whose groups
  are all decided becomes a **finalized word**, indexed in `finalizedWordsByStroke`; this
  catches a multi-group union equal to another group's key-set. Iterates the `allWords` set,
  which affects only list order inside the index.
- **Final verification and residual buckets (S6.Realization.5.5)** :1219-1258 — for each
  Word in `allWords` (set iteration, :1227), composes the primary stroke and one per extra
  alternate (:1232-1241). `residualTheoryCollisions` = Words with a feature discriminating stroke whose composed stroke is
  a theory-1 key (raw, sorted by ortho, :1243). `findCollidingInducedStrokes` (:727) pairs
  each key with the **first key seen** on the same stroke; each pair goes to
  `residualCollisions` (same-lemmeGramCat, :1248), `crossCategoryClashCollisions` (same bare
  lemme, different `lemmeGramCat`, :1251) or `crossLemmaCollisions` (:1255); same-ortho pairs
  are dropped. Today: 0 theory, 0 same-lemmeGramCat, 34 to 40 **cross-category clashes** and
  about 1,290 **cross-lemma collisions** (the lists vary between clean rebuilds, item B11).
  **The "0 residual same-lemmeGramCat collisions" invariant** is
  `len(assignment.residualCollisions) == 0`, printed and persisted only by the report build
  (build_realization_report.py:89-91, :108, :129) and asserted by unit tests on fixtures
  (src/test/ambiguitychecker_test.py:844). `buildFinalTheory` discards the residuals and
  `unassignedGroups` (item B17). The check sees only `allWords` (not canonical members,
  unchosen spelling twins or dropped groups) and only first-seen pairs (item B16). An
  all-pairs canonical check over the whole lexicon finds 230 same-lemmeGramCat pairs in the
  final induced strokes, all from spelling twins (item B1).

#### Final induced strokes — buildFinalInducedStrokes (S6.Realization.6)   src/ambiguitychecker.py:1261
Called by: `Dictionary.buildFinalTheory` only (dictionary.py:384).
Transformation: for **every** theory-1 Word (dict order, deterministic): a Word that needs
groups gets one feature discriminating stroke with the union of their chosen keys; others
keep their base strokes. Unassigned groups add nothing, silently.
Result: final induced strokes, 167,639 Words, 79,449 with a feature discriminating stroke.
Handed to Reserved-key composition (S7.4).

#### Alternate entry strokes — buildExtraInducedStrokes (S6.Realization.7)   src/ambiguitychecker.py:1288
Called by: `Dictionary.buildFinalTheory` only (dictionary.py:389).
Transformation: for each extra alternate of a self-homograph, base strokes plus one feature
discriminating stroke with that alternate's union of chosen keys (empty key-sets skipped).
Result: `dict[Word, list[Strokes]]`, the **alternate entries**, appended after index 0 in
theory 2. They skip Different-Lemma or Grammatical-Category Disambiguation (S7) (item B4) and
are never collision-checked when the primary is empty (item B21).

#### Report serialization — build_realization_report.main (S6.Realization.8)   util/build_realization_report.py:38
Called by: a person (rebuild step 6).
Transformation: per group in id order: features, `affectedWords`, `chosenKeys`, `cost`, ranked
`alternates`; then the four residual buckets as ortho pairs, in the order produced by Final
verification and residual buckets (S6.Realization.5.5).
Artifacts: reads pickles, `starboard3h.json`, keypress groups, resolved discriminating
feature sets; writes `realization_report.json`.
Notes: its only pipeline reader is export_keyboard_layout.py:128 (uses `keypressGroups` only).

### Where the canonical member comes from

The unmarked spelling of a homophone group is chosen entirely by the elicitation answers: for
each opposition the person decides which side needs nothing (first record: `il` {m,s} checked
`[]` vs `ils` {m,p} checked `[p]`). Per-combination resolution (S6.Elicitation.9.1) and
Discriminating feature set resolution (S6.Elicitation.9) turn an empty union into the `∅`
primary alternate; Keypress group population (S6.Realization.2) skips it. No code computes it;
4,858 groups have none. The precedence spec only states the intended default ("m" / "m s"
first), and the precedence-spec check verifies it for participles only. `FEATURE_PRIORITY`
(src/greedyoptimizer.py:16) is not used on this path; `GRAMCAT_PRIORITY` (:62) is live only in
Different-Lemma or Grammatical-Category Disambiguation (S7).

---
## Different-Lemma or Grammatical-Category Disambiguation (S7)

The Realization Phase separates only words with the same `lemmeGramCat`; collisions across
lemmas ("ver/vert/verre") or categories ("appel"/"appelle") remain. This stage takes the final
induced strokes, finds every set of Words that share one canonical stroke **and** span ≥2
`lemmeGramCat`s and ≥2 spellings (a **lemma-homophone group**), merges homographs and
1990-reform **doublets**, ranks the group from most canonical to most marked with the
**star/hash rule stack**, and gives each rank a **star/hash code**: `()`, `*`, `#`, `*#`, then
escalated `*#` codes. The first symbol is pressed with the word's **last phoneme stroke** (a
**merged star/hash mark**); further symbols become **\*/# marker strokes**. The result is
theory 2, in memory, plus the human view `theory2.tsv`.

Scale: 4,450 lemma-homophone groups. Sizes (Words): 2: 2,947; 3: 989; 4: 341; 5: 104; 6:
40; 7: 19; 8: 7; 10: 1; 11: 2. Codes: `()` 5,530, `*` 4,886, `#` 579, `*#` 146, `(*#,*#)` 51,
`(*#)×3` 9, `(*#)×4` 3, `(*#)×5` 2 — 5,676 marked Words, 86 \*/# marker strokes.

### Theory 2 assembly — Dictionary.buildFinalTheory (S7.1)   dictionary.py:342
Called by: `python dictionary.py` `__main__` (dictionary.py:532, only when both
`keypress_groups.json` and `resolved_press_sets.json` exist, :531) and every
Theory Export (S8) exporter through Theory 2 loading (S8.1).
Input state: theory 1 (80,725 keys / 167,639 Words), keyboard layout, the two JSON paths.
Transformation: (1) loads `markersByKeypress` (:365-369) and the resolved discriminating
feature sets (:370-371); (2) runs the Realization Phase on its inline path (S7.2) → final
induced strokes; (3) calls Reserved-key composition (S7.4) with Reform-doublet loading (S7.3)
and `phonemeStrokeCounts` = each Word's base stroke count, which turns on the merge; (4)
calls Alternate entry strokes (S7.14); (5) returns `{word: [primaryComposed[word]] +
extraByWord.get(word, [])}` (:390).
Result: theory 2, 167,639 Words in theory-1 order; `theory2.tsv` has 181,869 rows, so 14,230
alternate entries.
Artifacts: reads both JSON files and `resources/reform1990.tsv` (path relative to the working directory).
Notes: never uses `self`, so exporters unpickle the whole `Dictionary` just to call it (refactor candidate).

### Realization Phase, inline path (S7.2)   dictionary.py:373-384
Called by: Theory 2 assembly (S7.1).
Transformation: Word lookup indexes (S6.Realization.1) → Keypress group population
(S6.Realization.2) → Extra alternate population (S6.Realization.3) → Preferred key
resolution (S6.Realization.4) → Coda key search (S6.Realization.5) → Final induced strokes
(S6.Realization.6), over the whole lexicon. Described under Same-Lemma and
Grammatical-Category Disambiguation (S6).
Result: final induced strokes + physical keypress group assignment (0→21, 1→16, 2→20, 3→23, 4→18,
5→17, 6→19, identical to the realization report).

### Reform-doublet loading — loadReform1990DoubletPairs (S7.3)   src/ambiguitychecker.py:94
Called by: Theory 2 assembly (S7.1), dictionary.py:386.
Transformation: every `reform1990.tsv` row whose `isException` is not `"True"` gives
`frozenset({oldSpelling, newSpelling})`. Exception rows (`fût`/`fut`, `croît`/`croit`) collide
with unrelated words and are left out.
Result: 259 pairs — **lemma spellings**, compared against `Word.lemme`, not `ortho`.
Notes: some pairs exist only at verb-lemma level (`boursoufler/boursouffler`), so the
adjective doublet `boursouflée/boursoufflée` needs a `MARKING_OVERRIDES` entry.

### Reserved-key composition — composeReservedKeyStrokes (S7.4)   src/ambiguitychecker.py:410
Called by: Theory 2 assembly (S7.1), dictionary.py:385.
Input state: final induced strokes, doublet pairs, `phonemeStrokeCounts`.
Transformation: `composed = dict(finalInduced)` (:434); for each lemma-homophone group from
Lemma-homophone group detection (S7.5), gets each member's star/hash strokes from Physical
star/hash assignment (S7.6); Words with code `()` keep their strokes, the others go through
Star/hash mark merge into the last phoneme stroke (S7.13).
Result: `dict[Word, Strokes]`: marked Words carry reserved keys 10/15, others unchanged.
Notes: safety argument (docstring :422-429): keys 10/15 are never in `allowedKeys`
(keyboard.py:376), so removing them gives back the final induced strokes exactly. It covers
primary strokes only, not alternate entries.

### Lemma-homophone group detection — groupHomophonesByReservedStroke (S7.5)   src/ambiguitychecker.py:380
Called by: Reserved-key composition (S7.4), :435.
Transformation: buckets Words by `canonicalizeStrokes(finalInduced[word])` (:396); keeps a
bucket with ≥2 Words (:400), ≥2 distinct `lemmeGramCat` (:402) and ≥2 distinct `ortho`
(:404). Members keep theory-1 order.
Result: 4,450 lemma-homophone groups.
Notes: a bucket with one `lemmeGramCat` and several spellings is dropped on purpose (a code
comment leaves it to the Realization Phase): 98 such buckets survive into theory 2, all from
spelling twins (item B1). Same-lemma cross-category clashes ("appel" NOM / "appelle" VER)
are in scope because their `lemmeGramCat`s differ.

### Physical star/hash assignment — assignStarHashPhysicalStrokes (S7.6)   src/ambiguitychecker.py:369
Called by: Reserved-key composition (S7.4), :436.
Transformation: `{word: starHashCodeToStrokes(code)}` over Star/hash code assignment (S7.7)
and Star/hash code realization (S7.12).
Result: `dict[Word, Strokes]` of star/hash strokes; `()` = no star/hash mark.

### Star/hash code assignment — assignStarHashMarks (S7.7)   src/ambiguitychecker.py:292
Called by: Physical star/hash assignment (S7.6), :376.
Input state: one lemma-homophone group in theory-1 order.
Transformation:
1. **Homograph merge** (:307-311): group by `ortho` (first-seen order); representative =
   `max(group, key=frequency)`, first wins ties.
2. **Doublet merge** (:313-330): union-find over ortho-group representatives; union when
   `{rep_i.lemme, rep_j.lemme}` is a doublet pair (path-halving `find`, `parent[ri] = rj`, no
   ranks). Only representatives' lemmas are checked (item B26).
3. Each merged set's **group representative** = `max(set, key=frequency)` (:332).
4. Group ranking (S7.8) of the representatives; Star/hash code sequence (S7.11) for their
   count; zip in rank order (:333-335).
5. Every Word of a merged set gets its representative's code, stored by `ortho` (:337-343).
Result: `dict[Word, tuple[str, ...]]`; homographs and doublets share a code. 18 groups end
with a single code (all doublets); 21 composed strokes stay shared by a doublet pair.

### Group ranking — rankHomophoneCluster (S7.8)   src/ambiguitychecker.py:261
Called by: Star/hash code assignment (S7.7), :333.
Transformation: `sorted(words, key=cmp_to_key(_starHashCompare))`, most canonical first.
Result: ranked representatives; position 0 is the canonical member.
Notes: a stable sort gives a unique result only for a consistent total order; this
comparator is not one (items B5, B25).

### Ranking comparator — _starHashCompare (S7.9)   src/ambiguitychecker.py:242
Called by: Group ranking (S7.8).
Transformation: `a is b` → 0. Else `marked = decideStarHashMark(a, b)` (Pairwise star/hash
decision (S7.10)); `None` → higher frequency first, then `ortho` ascending, then 0; otherwise
+1 if `a` is marked, −1 if `b`.
Result: −1/0/+1.
Notes: the `None` branch never runs in the pipeline (homographs and doublets are merged
first). On equal frequency under the frequency-ratio rule (R4), same-category rule (R5) or
frequency fallback (R7), `decideStarHashMark` marks its first argument, so `compare(a,b) ==
compare(b,a) == +1` (item B5).

### Pairwise star/hash decision — decideStarHashMark (S7.10)   src/ambiguitychecker.py:183
Called by: Ranking comparator (S7.9), :253.
Transformation: the star/hash rule stack; the first matching rule decides. "Mark X" = X is
less canonical and gets the star/hash mark. Frequency is the film frequency.

| Rule | Line | Condition | Outcome |
|---|---|---|---|
| homograph exemption (R1) | :211 | same `ortho` | `None` (no star/hash mark) |
| reform-doublet exemption (R2) | :214 | `{lemmeA, lemmeB}` in the 259 doublet pairs | `None` |
| per-pair override (R3) | :217-219 | `MARKING_OVERRIDES[frozenset({orthoA, orthoB})]` exists (49 entries, :130-180, keyed by ortho) | mark the stored spelling |
| frequency-ratio rule (R4) | :221-225 | `hi/lo ≥ RATIO_EXEMPTION_THRESHOLD` (10.0, :91), `inf` if `lo == 0` | mark the rarer; tie → first argument |
| same-category rule (R5) | :224-225 | equal `GramCat` enums (`ADJ` ≠ `ADJ:pos`) | mark the rarer; tie → first argument |
| category-priority rule (R6) | :227-230 | both categories in `GRAMCAT_PRIORITY` (src/greedyoptimizer.py:62) | mark the lower priority |
| frequency fallback (R7) | :232 | a category is missing from the table | mark the rarer; tie → first argument |

`GRAMCAT_PRIORITY` (higher = more canonical): `ADV` 50, `PRO:pos` 40, `NOM` 30, `VER` 20,
`ADJ` 10, `ADJ:pos` 0. Everything else (`PRE`, `ONO`, `ART:def`, `PRO:per`, `AUX`, `CON`, …)
falls to the frequency fallback (R7), even against `NOM`.

`MARKING_OVERRIDES` (pair → **marked** spelling): sales/**salles**, entrés/**entrées**,
alentours/**alentour**, virés/**virées**, portés/**portées**, envolés/**envolées**,
dorés/**dorées**, closes/**clauses**, comptés/**comtés**, montés/**montées**,
remontés/**remontées**, hautes/**hôtes**, retenus/**retenues**, éteints/**étains**,
new/**news**, plongés/**plongées**, survenus/**survenues**, gelés/**gelées**,
usagés/**usagers**, accros/**accrocs**, percés/**percées**, levés/**levers**,
traversés/**traversées**, rangés/**rangées**, réaux/**réal**, rentrés/**rentrées**,
impairs/**impers**, coronaires/**coroners**, crus/**crues**, nazes/**nases**,
balèzes/**balaises**, lares/**lards**, perçants/**persans**, troués/**trouées**,
craints/**crins**, visés/**visées**, ancrés/**encrés**, jetés/**jetées**, rués/**ruées**,
dévonienne/**dévonien**, pincés/**pincées**, monomoteurs/**monomoteur**,
hautains/**hautins**, boursouflée/**boursoufflée**, bouillis/**bouillies**,
bivalves/**bivalve**, nichés/**nichées**, stabilisante/**stabilisant**, camés/**camées**.

Result: the Word to mark, or `None`.
Rule usage among representative pairs: frequency-ratio rule (R4) 4,284 · same-category rule
(R5) 854 · category-priority rule (R6) 838 · frequency fallback (R7) 93 · per-pair override
(R3) 45 · reform-doublet exemption (R2) 0 · homograph exemption (R1) 0.
Notes: the code calls the frequency-ratio rule (R4) a "ratio exemption"; it exempts the pair
from the category rules, not from marking. Any zero-frequency word loses to any non-zero
word. The code docstring numbers R1-R6 the same way; comments at :392/:431 and a RESUME note
use another numbering.

### Star/hash code sequence — assignStarHashCombos (S7.11)   src/ambiguitychecker.py:272
Called by: Star/hash code assignment (S7.7), :334.
Transformation: base budget `[(), ('*',), ('#',), ('*#',)]`, then `('*#',) * n` for n = 2, 3,
… (:284-288), truncated to the rank count. Codes beyond the base budget are **escalated
codes**.
Result: rank 0 `()`, 1 `*`, 2 `#`, 3 `*#`, 4 `*# *#`, … No upper bound; live maximum `(*#)×5` (8 representatives).

### Star/hash code realization — starHashCodeToStrokes (S7.12)   src/ambiguitychecker.py:361
Called by: Physical star/hash assignment (S7.6).
Transformation: `_STAR_HASH_KEYS` (:354): `*` → `(10,)`, `#` → `(15,)`, `*#` → `(10, 15)`;
`STAR_KEY` = 10 (:351), `HASH_KEY` = 15 (:352). Keys 0/1 (left pinky) are held for a
possible third star/hash mark and never used.
Result: reserved-only strokes; `()` for the canonical member.

### Star/hash mark merge into the last phoneme stroke (S7.13)   src/ambiguitychecker.py:437-444
Called by: Reserved-key composition (S7.4).
Input state: a marked Word's final induced strokes `s` (base strokes, then maybe its feature
discriminating stroke) and its star/hash strokes `extra`.
Transformation: with `phonemeStrokeCounts` (always, in the pipeline), `last =
phonemeStrokeCounts[word] - 1` and the result is `s[:last] + (s[last] + extra[0],) +
s[last+1:] + extra[1:]`: the first star/hash symbol joins the last phoneme stroke (not the
feature discriminating stroke); remaining symbols follow as \*/# marker strokes. Without
counts (tests only) it appends `s + extra`.
Result: `pâts` `((4,12),(17,))` + `*` → `((4,12,10),(17,))` = `p*a/-s`; `aulx` `((12,14),)` +
`(*#)×5` → `*ae#/*#/*#/*#/*#`.

### Alternate entry strokes (S7.14)   src/ambiguitychecker.py:1288
Called by: Theory 2 assembly (S7.1), dictionary.py:389. Described as Alternate entry strokes
(S6.Realization.7).
Notes: scope gap with a measured cost: an alternate entry carries no star/hash mark and can
take an unrelated word's only stroke (`subits` loses to `subis`'s alternate entry, `pais`
to `paie`, `amplis` to `emplis`): 9 spellings without a Plover entry (item B4).

### Theory 2 report — Dictionary.writeFinalTheory (S7.15)   dictionary.py:392
Called by: `__main__` dictionary.py:533, right after Theory 2 assembly (S7.1).
Transformation: header `ortho lemme gramCat strokes extraStrokes`; Words sorted by (lemme,
gramCat, ortho), one row per stroke. `strokes` = base strokes as key spelling
(`strokesToString`); `extraStrokes` = `+k,…` for keys merged into the last phoneme stroke,
then extra strokes as key-index lists joined by `/`.
Result: `theory2.tsv`, 181,869 rows (`aile … iel +10`, `ailes … iel +10/17`, `hèle … iel +15`, `elles … iel 17`).
Artifacts: writes `theory2.tsv`.
Notes: a terminal human view; nothing reads it.

### Cross-category clash detector — detectCrossCategoryClash (S7.16, off-pipeline)   src/ambiguitychecker.py:59
Called by: `classifyStrokeCluster` :452 ← `classifyTheory` ← `ambiguitychecker`
`__main__` :1161 (the hand-run ambiguity report) and tests.
Transformation: flags a bare lemma with ≥2 singleton `lemmeGramCat` sub-groups of different spellings.
Notes: in the pipeline, cross-category clashes are handled implicitly by the ≥2
`lemmeGramCat` filter of Lemma-homophone group detection (S7.5). The `__main__` itself is a
hand-run check after Phonetic Theory Building (S5) (its console title still says "Phase 0
Ambiguity Report" — legacy wording, queued follow-up): it classifies every theory-1 stroke
cluster, honours `resources/ambiguityIgnoreList.tsv` (manually-triaged lemmas with reasons)
and writes `ambiguity_report.tsv`. Its "overflow" metric counts lemma-homophone clusters of
≥5 lemmas — beyond the old 4-slot `*`/`#` budget (no stroke, `*`, `#`, `*#`) that N-ary
escalation has since superseded — and reports their frequency mass; kept as a drift signal.

### Worked examples (2026-09-22 data)

1. **Category-priority rule (R6).** Group `((12,), (4,13,14,23))`: `appel` NOM 80.88,
   `appelle` VER 485.77. Ratio 6.0 < 10, categories differ, NOM 30 > VER 20 → `appelle` is
   marked although 6× more frequent. Plover: `a/piel` → appel, `a/p*iel` → appelle; its
   alternate entries `a/piel/-k`, `a/piel/-l` carry no star/hash mark.
2. **Homograph merge, frequency-ratio rule (R4) and frequency fallback (R7).** Group
   `((12,),)`: `à` PRE 12,190.4; `a` AUX 6,350.91 / VER 5,498.34 / NOM 81.36 (representative
   AUX); `ah` ONO 576.53; `ha` ONO 21.54 / NOM 2.94. à vs a: ratio 1.9, PRE not in the table →
   frequency fallback (R7) → `a` marked; ah vs a: ratio 11.0 → frequency-ratio rule (R4);
   `ha` loses to all by the frequency-ratio rule (R4). Codes: à `()`, a `*`, ah `#`, ha `*#` →
   Plover `a`, `*a`, `a#`, `*a#`.
3. **Escalation.** Group `((12,14),)` (11 Words, 8 representatives): au ART:def `()`; oh
   ONO `*`; aux ART:def `#` (vs oh: ratio 1.07 → frequency fallback (R7)); eau NOM `*#`; haut
   `*# *#`; ho `(*#)×3`; ô `(*#)×4`; aulx NOM 0.0 `(*#)×5`. Plover `ae`, `*ae`, `ae#`, `*ae#`,
   `*ae#/*#`, …, `*ae#/*#/*#/*#/*#`.
4. **Doublet.** Group `((3,5,13),(7,9,11,13))`: `bizut` 2.05 and `bizuths` 0.0 (lemmas
   bizut/bizuth, a reform pair) are merged and both get `()`; Plover keeps `bizut`.
5. **Tie decided by input order.** `pas` NOM 0.0 vs `pâts` NOM 0.0: the frequency-ratio rule
   (R4) (lo = 0) marks the first argument; the insertion sort calls `compare(later,
   earlier)`, so the later Word in theory-1 order is marked (`pâts` → `p*a/-s`); reversed
   input marks `pas` (item B5).

---

## Theory Export (S8)

Theory Export (S8) turns theory 2 into the files people use: the **Plover branch**
(dictionary, key table, plugin) and the **trainer branch** (four JSON files), plus two shared
calls. Every exporter that needs theory 2 recomputes it in its own process; none reads
`theory2.tsv`. The key table (S8.4) and the trainer legend (S8.6) read only `starboard3h.json`,
and the legend also reads the realization report.

### Shared calls

#### Theory 2 loading — loadFirstAndFinalTheory / loadFinalTheory (S8.1)   util/_theoryio.py:68, :48
Called by: Plover dictionary export (S8.3) via `loadFinalTheory`; Trainer word drill (S8.7),
Trainer sentences (S8.8) and Trainer definitions (S8.9) via `loadFirstAndFinalTheory`. The
report build of the Realization Phase uses only `loadFirstTheory` (:42).
Transformation: raises unless both JSON inputs exist (:76-79); `_loadDictionaryAndFirstTheory`
(:17) aliases `__main__.Dictionary` (the pickle was written from `dictionary.py` as `__main__`),
unpickles the five `Dictionary.pickle` objects and theory 1, then calls
`dictionary.buildFinalTheory(...)` (:82).
Result: (theory 1, theory 2); `loadFinalTheory` drops theory 1.
Artifacts: reads both pickles, both JSON inputs, `resources/reform1990.tsv`.

#### Stroke rendering — renderFinalStrokesToRTFCRE (S8.2)   util/_stenorender.py:39
Called by: Plover dictionary export (S8.3, :45), Trainer word drill (S8.7, :231), Trainer
sentences (S8.8, :164), Trainer definitions (S8.9, :65).
Transformation: per stroke, `keys = sorted(set(stroke))` (the canonical form), then:
1. **\*/# marker stroke** (only keys 10/15) → `*`, `#` or `*#` (:43-44);
2. **merged star/hash stroke** (reserved + phoneme keys) → `_renderMarkedStroke` (:26),
   Plover's `plover_stroke` hyphen rule: **implicit-hyphen keys** are nucleus 11-14 plus
   `STAR_KEY` 10; `firstRightKey` = 15; a `-` precedes the first key ≥15 only without an
   implicit-hyphen key (`*iel`, `ie#l`, `swa#`, `pvR-#`);
3. plain stroke → `Starboard.strokesToRTFCRE` (keyboard.py:683): keys by part, hyphens
   stripped, `-` as nucleus when there is no vowel key.
Strokes are joined with `/`.
Result: an **RTFCRE** string with Stenalgo key names.
Helpers not expanded: `Starboard.keyDisplayName` keyboard.py:654 (reserved names `{0:"&", 1:"%", 10:"*", 15:"#"}`, :652).

### Plover branch

#### Plover dictionary export — export_plover_dictionary.main (S8.3)   util/export_plover_dictionary.py:35
Called by: `python -m util.export_plover_dictionary`.
Transformation: renders every stroke of every Word into `stenoToWords[steno]` (exact
duplicate Words skipped, :50); per steno keeps `max(words, key=frequency)` (:56), first in
theory-1 order on a tie (item B10); prints the top 10 collisions.
Result: Plover dictionary, 163,238 entries (`sort_keys=True`, `indent=1`); 5,139 contain
`*`/`#`; 58 end in a \*/# marker stroke. 29 spellings have no entry: 20 reform-doublet or
near-doublet losers (`bizuths`, `dégottés`, `toquade`, `cuissot`, …) and 9 spellings shadowed
by an alternate entry (item B4).
Artifacts: writes `plover_stenalgo_dictionary.json`.

#### Plover key table export — export_plover_system.main (S8.4)   util/export_plover_system.py:38
Called by: `python -m util.export_plover_system`.
Transformation: `KEYS` = `Starboard.keyDisplayNames()` (keyboard.py:679) in key order:
`& % k- s- p- v- m- t- R- w- * @- a- -i -e # -j -s -k -d -t -R -n -l -Z -m`.
`IMPLICIT_HYPHEN_KEYS` = nucleus names + `*` (:44-46). `GEMINI_PR_KEYMAP` zips names with the
hardware-sniffed `GEMINI_PR_LABELS` (:28-35) — the **Gemini PR keymap**: keys 0, 1, 2, 10 are
number-bar bits `#A #B #C #1`; key 15 (`#`) is the only star bit `*4`.
Result: Plover key table.
Artifacts: writes `plover_stenalgo/plover_stenalgo/_generated_keys.py`.
Notes: the implicit-hyphen set is computed separately here and in `_renderMarkedStroke`; a
layout change moving `*` or the nucleus keys must update both.

#### Plover system plugin (S8.5)   plover_stenalgo/plover_stenalgo/system.py
Called by: Plover, via entry point `"Stenalgo French" = "plover_stenalgo.system"` (plover_stenalgo/pyproject.toml:12-13).
Registers: `KEYS`, `IMPLICIT_HYPHEN_KEYS`, `SUFFIX_KEYS = ()`, `NUMBER_KEY = None`,
`NUMBERS = {}`, `UNDO_STROKE_STENO = "*"`, no orthography rules, `KEYMAPS = {"Gemini PR":
GEMINI_PR_KEYMAP}` (no machine plugin), `DEFAULT_DICTIONARIES = ("user.json", "commands.json")`.
Notes: bare `*` as undo is safe because the first star/hash symbol is always merged and
\*/# marker strokes are always `*#`. The user adds `plover_stenalgo_dictionary.json` by hand.

### Trainer branch

#### Trainer keyboard legend — export_keyboard_layout.main (S8.6)   util/export_keyboard_layout.py:148
Called by: `python -m util.export_keyboard_layout`.
Transformation: per key: index, display name, 1-key phonemes, hand/row/col
(`_handAndGridPosition` :51), finger, syllabic part, reserved flag, Gemini label; multi-key
phoneme layers (`_phonemeLayers` :81); the **conjugation-feature legend**
(`_conjugationMarkers` :117) from the realization report (:128): per keypress group,
`chosenKeys`, key names and French feature labels. Does not call `buildFinalTheory`.
Result: `steno-trainer/public/data/keyboard-layout.json`.
Notes: inline-path and report keys agree today (0→21 … 6→19); nothing detects a mismatch
(item B18). A null `chosenKeys` would crash (item B19).

#### Trainer word drill — export_practice_words.main (S8.7)   util/export_practice_words.py:208
Called by: `python -m util.export_practice_words [--limit N]`.
Transformation: `buildReadingsByWord` (:175) maps each resolved entry's `readings` (feature
combinations) to a Word through `_resolveEntryWord`; `chordsWithReadings` (:194) pairs each
theory-2 stroke with its feature combinations (on a count mismatch, every stroke gets all
combinations and the Word counts as "misaligned"). **Drill items** are keyed by (ortho,
steno); a second Word with the same key merges label and context (:233-245). Each carries
context words (`formatContext` :133), a French label (`formatReadingsLabel` :112), dotted
phonology, steno, sorted key strokes and film frequency. Sorted by (−frequency, ortho,
steno), truncated to 10,000.
Result: `steno-trainer/public/data/practice-words.json`.

#### Trainer sentences — export_practice_sentences.main (S8.8)   util/export_practice_sentences.py:145
Called by: `python -m util.export_practice_sentences`, after Trainer word drill (S8.7).
Transformation: builds `chordsByOrtho` from theory 2; for each LLM-annotated candidate in
`util/candidate_sentences.jsonl` (276 lines), `resolveToken` (:74) narrows by lemma, category,
verb tag and gender/number; rejects `sub:`/`ind:pas` tags, unknown forms, ambiguous stenos, and
tokens that are not a drill item (`practice-words.json`, :158).
Result: `steno-trainer/public/data/practice-sentences.json` (217 sentences).
Notes: the drill-item gate compares against another process's recompute (item B35).

#### Trainer definitions — export_definitions.main (S8.9)   util/export_definitions.py:46
Called by: `python -m util.export_definitions`.
Transformation: groups every theory-1 Word by canonical base steno (`canonicalizeStrokes` +
`strokesToRTFCRE`); per Word lists spelling, phonology, frequency and `[steno, label index]`
per theory-2 stroke; merges identical rows (`_mergeIdenticalRows` :35); sorts by
(−frequency, ortho); writes compact positional JSON with a shared label table.
Result: `steno-trainer/public/data/definitions.json` (whole lexicon).
