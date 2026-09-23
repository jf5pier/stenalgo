# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stenalgo is a stenotype keyboard layout and theory generator for French. It uses constraint programming (Google OR-Tools CP-SAT solver) to optimize steno keyboard key assignments, minimizing both physical finger strain and mental complexity of the resulting stenographic theory. The primary target keyboard is the Starboard (26-key custom steno keyboard).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest src/test/

# Run a single test
pytest src/test/word_test.py::TestWord::test_method_name

# Type checking
mypy src/

# Build the combined lexicon (LexiqueMixte.tsv)
python lexique.py

# Run dictionary processing and optimization pipeline
python dictionary.py

# Resolve the discriminating feature sets from elicitation_answers.json (Elicitation Phase)
python -m src.elicitation

# Group the atomic features onto Keypress Groups (Grouping Phase) -> keypress_groups.json
python -m util.build_keypress_groups

# Rebuild the realization report (Realization Phase, report build) -> realization_report.json
python -m util.build_realization_report

# Export the Plover dictionary and key table
python -m util.export_plover_dictionary
python -m util.export_plover_system

# Regenerate steno-trainer's data exports (run after starboard3h.json or the lexicon changes)
python -m util.export_keyboard_layout
python -m util.export_practice_words
python -m util.export_practice_sentences
python -m util.export_definitions
```

## Architecture

### Processing Pipeline

**Full reference: `docs/PIPELINE.md`** (call graph, rebuild order, dataset states) and
**`docs/GLOSSARY.md`** (canonical vocabulary; maps legacy names such as "Phase G",
"press-set", "marker", "cluster" to current ones). Stages and phases are cited by
descriptive name with the code in parentheses. The two homophone problems have separate
mechanisms, decided by the 2026-09-18 elicitation-first pivot; older notes describing a
solver-picks-features design are superseded. Current status and open decisions:
`ROADMAP.md`'s "Status update" section and `todo.md`.

1. **Lexicon Building (S1)** (`lexique.py`) — Merges Lexique383 and LexiqueInfra into `resources/LexiqueMixte.tsv` (136,456 rows with frequencies, phoneme and grapheme syllable breakdowns); applies `lexiconExclusions.tsv` and the 1990-reform rewrites
2. **Synthetic Lexicon Building (S2)** (`util/completeVerbParadigms.py`, `util/generateMissingNomAdjForms.py`, `util/fix*.py`, run by hand) — appends missing paradigm forms to `resources/LexiqueSynthetic.tsv` (42k rows); the verb completion is gated by the legacy feature extraction (`src/featureextractor.py`)
3. **Dictionary Loading (S3)** (`dictionary.py`) — Reads `LexiqueMixte.tsv` + `LexiqueSynthetic.tsv` into 167,639 Words (identity merge), indexes them by orthography and lemma, excludes words from `excluded_words.txt`, builds the syllable inventory; cached in `Dictionary.pickle`
4. **Keyboard Layout Optimization (S4)** (`src/cpsatsolver.py::optimizeKeyboard`, CP-SAT minimizing ambiguity/ergonomics/order violations, fed by the layout statistics `optimizeBiphonemeOrder`/`analyseAmbiguities`) — a real, rare and costly stage whose solver call is commented out (dictionary.py:494); the live pipeline loads the committed `starboard3h.json`, and no command regenerates it today
5. **Phonetic Theory Building (S5)** (`Dictionary.buildTheory`) — theory 1: phonetic strokes per Word, homophones sharing one raw stroke sequence; cached in `FirstTheory.pickle`, human view `theory.tsv`
6. **Same-Lemma and Grammatical-Category Disambiguation (S6)** — separates the Homophone Groups (same `lemmeGramCat`, same canonical strokes) in three phases:
   - **Discriminating-Feature Elicitation (Elicitation Phase)** (`src/elicitation.py`, `python -m src.elicitation`) — Questionnaire Generation, Answer Collection (the user's own feature presses, pair by pair via a web questionnaire; `elicitation_answers.json` tracked) and Press-Set Resolution (`resolved_press_sets*.json`, gitignored, regenerable)
   - **Discriminating-Feature Grouping (Grouping Phase)** (`src/featuregroupingsat.py` exact CP-SAT, `python -m util.build_keypress_groups`) — groups the atomic features onto Keypress Groups (K=7, proven optimal; tracked output `keypress_groups.json`). The greedy `src/featuregrouping.py` path is not live; only its loaders and verifiers are used
   - **Discriminating-Feature Stroke Realization (Realization Phase)** (`src/ambiguitychecker.py::realizeKeypressGroupsAsExtraStroke`) — realizes each Keypress Group as a coda-bank feature discriminating stroke. Two call sites: the **inline path** (inside `Dictionary.buildFinalTheory`, feeds theory 2 and every export) and the **report build** (`python -m util.build_realization_report` → the tracked realization report `realization_report.json`, read only by the trainer keyboard legend). The must-stay-green regression: 0 residual same-lemmeGramCat collisions
7. **Different-Lemma or Grammatical-Category Disambiguation (S7)** (`src/ambiguitychecker.py`) — star/hash marks for lemma-homophone groups. `decideStarHashMark` rule stack (homograph exemption (R1) → reform-doublet exemption (R2) → per-pair override (R3, `MARKING_OVERRIDES`) → frequency-ratio rule (R4, 10x) → same-category rule (R5) → category-priority rule (R6, `GRAMCAT_PRIORITY`) → frequency fallback (R7)) → `rankHomophoneCluster`/`assignStarHashMarks` (N-ary, escalates with extra `*#` syllables) → `assignStarHashPhysicalStrokes`/`composeReservedKeyStrokes` (`STAR_KEY`=10, `HASH_KEY`=15, keys 0/1 held for a possible third mark). Wired into `Dictionary.buildFinalTheory` (theory 2); the mark's first symbol is pressed with the word's last phoneme stroke (`*a`, `swa#`), only escalated codes add \*/# marker strokes (`util/_stenorender.py` renders them the way Plover writes them)
8. **Theory Export (S8)** — two branches, Plover (`util/export_plover_dictionary.py`, `util/export_plover_system.py`) and steno-trainer (`util/export_keyboard_layout.py`, `export_practice_words.py`, `export_practice_sentences.py`, `export_definitions.py`). **Nothing reads `theory2.tsv`** (a gitignored human view written by `python dictionary.py`): every exporter recomputes theory 2 through `util/_theoryio.py` (`loadFirstAndFinalTheory` → `Dictionary.buildFinalTheory`)

Pitfalls: `dictionary.py` reuses `Dictionary.pickle`/`FirstTheory.pickle` whenever they exist and never checks them against the lexicon or layout (`rm -f *.pickle` after any lexicon or layout change); pin `PYTHONHASHSEED=0` when the tracked realization report must be reproducible. The legacy discriminator path (`buildDiscriminatorSelection`, `satOptimizeDiscriminator`, `assignDiscriminatorKeypresses`) no longer runs in `dictionary.py` `__main__`: `satOptimizeDiscriminator` and `assignDiscriminatorKeypresses` are test-only, `src/featureextractor.py` feeds only Synthetic Lexicon Building (S2)'s gating and the `ambiguitychecker` diagnostic, and of `FEATURE_PRIORITY`/`GRAMCAT_PRIORITY` in `src/greedyoptimizer.py` only `GRAMCAT_PRIORITY` is live (category-priority rule (R6)). Suspected bugs found during the docs refactor are listed in `todo.md`.

### Core Data Model

- **`src/grammar.py`** — Phonology primitives: `Phoneme`, `Biphoneme`, `Multiphoneme`, `Syllable` and their collection classes. French uses 20 consonants + 16 vowels (nucleus phonemes) in X-SAMPA notation (single ASCII characters).
- **`src/word.py`** — `Word` dataclass with orthography, phonology, lemma, `GramCat` enum (22 grammatical categories), gender/number, verb conjugation info, corpus frequencies (books + film subtitles).
- **`src/keyboard.py`** — Abstract `Keyboard` base class; `Starboard` implementation with `FingerWeights`/`PositionWeights` cost models. Key type aliases: `Stroke`, `Strokes`, `Keypress`.

### Key Constants (cpsatsolver.py)

- `AMBIGUITY_PENALTY = 30000` — Cost for stroke ambiguities
- `ORDER_PENALTY = 500` — Cost for phoneme ordering violations
- `STROKE_ASSIGNMENT_PENALTY = 1` — Base cost per stroke assignment
- Solver timeout: 90 seconds

## Conventions

- Phonemes use X-SAMPA notation (single ASCII chars, e.g., `@` for schwa, `R` for French R)
- Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda (consonants); `8` (ɥ) is a nucleus phoneme, `j`/`w` are consonants, all consonants after the first vowel go to the coda, and a vowel-less syllable goes entirely to the onset
- TSV files use tab separators; recent commits fixed spaces-vs-tabs issues
- `starboard3h.json` contains the pre-optimized keyboard mapping (26 keys: 22 phoneme keys + 4 reserved keys, 10 `*` and 15 `#` for the star/hash marks, 0/1 held for a possible third mark)
- Resource lexicon files in `resources/` are large (10-25MB TSV); `top500_books.txt` and `top500_film.txt` define frequent words
