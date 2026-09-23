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

# Full pipeline in two commands, run from the repo root: dictionary.py orchestrates the
# four Synthetic Lexicon Building (S2) appenders (--apply), theory 1, the Elicitation/
# Grouping/Realization phases, theory 2 and every export, aborting on the first failure
python lexique.py                           # Lexicon Building (S1) -> LexiqueMixte.tsv
python dictionary.py                        # everything from S2 to the exports

# Individual steps (still work standalone)

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

**Full reference: `docs/PIPELINE.md`** (call graph, rebuild order, dataset states, the
"Recomputing after a fix" checklist) and **`docs/GLOSSARY.md`** (canonical vocabulary).
Architecture and design rationale: `docs/ARCHITECTURE.md`. The eight stages:

1. **Lexicon Building (S1)** — `python lexique.py` → `resources/LexiqueMixte.tsv` (136,456 rows)
2. **Synthetic Lexicon Building (S2)** — `util/completeVerbParadigms.py` etc., run by the `python dictionary.py` orchestrator → `resources/LexiqueSynthetic.tsv`
3. **Dictionary Loading (S3)** — inside `python dictionary.py` → 167,639 Words, syllable inventory (cached in `Dictionary.pickle`)
4. **Keyboard Layout Optimization (S4)** — CP-SAT layout solve; rare, costly, solver call commented out (loads committed `starboard3h.json`)
5. **Phonetic Theory Building (S5)** — `Dictionary.buildTheory` → theory 1 (`FirstTheory.pickle`)
6. **Same-Lemma and Grammatical-Category Disambiguation (S6)** — three phases: Elicitation (`python -m src.elicitation`), Grouping (`python -m util.build_keypress_groups`), Realization (feature discriminating strokes; inline in `Dictionary.buildFinalTheory` + `python -m util.build_realization_report`)
7. **Different-Lemma or Grammatical-Category Disambiguation (S7)** — star/hash marks (`decideStarHashMark` rule stack) → theory 2
8. **Theory Export (S8)** — Plover (`util/export_plover_*`) and steno-trainer (`util/export_*`) branches; nothing reads `theory2.tsv`, every exporter recomputes theory 2 via `util/_theoryio.py`

Pitfalls: `dictionary.py` reuses `Dictionary.pickle`/`FirstTheory.pickle` whenever they exist and never checks them against the lexicon or layout (`rm -f *.pickle` after any lexicon or layout change — `python dictionary.py` now orchestrates the full chain but rebuilds the pickles itself only for rows its own S2 appenders add during the run, and aborts on the first failing step); pin `PYTHONHASHSEED=0` when the tracked realization report must be reproducible; the NOM/ADJ cross-checkers need the external Morphalou 3.1 CSV (see `docs/PIPELINE.md` Synthetic Lexicon Building (S2)). The legacy discriminator path (`buildDiscriminatorSelection`, `satOptimizeDiscriminator`, `assignDiscriminatorKeypresses`) no longer runs: those functions are gone; `src/featureextractor.py` feeds only Synthetic Lexicon Building (S2)'s gating and the `ambiguitychecker` diagnostic, and of `src/greedyoptimizer.py` only `GRAMCAT_PRIORITY` is live (category-priority rule (R6)). Suspected bugs are listed in `TODO.md` ("Suspected bugs").

### Core Data Model

- **`src/grammar.py`** — Phonology primitives: `Phoneme`, `Biphoneme`, `Multiphoneme`, `Syllable` and their collection classes. French uses 20 consonants + 16 vowels (nucleus phonemes) in X-SAMPA notation (single ASCII characters).
- **`src/word.py`** — `Word` dataclass with orthography, phonology, lemma, `GramCat` enum (22 grammatical categories), gender/number, verb conjugation info, corpus frequencies (books + film subtitles).
- **`src/keyboard.py`** — Abstract `Keyboard` base class; `Starboard` implementation with `FingerWeights`/`PositionWeights` cost models. Key type aliases: `Stroke`, `Strokes`, `Keypress`.

(Fuller data model and the constants' rationale: `docs/ARCHITECTURE.md`.)

### Key Constants (cpsatsolver.py)

- `AMBIGUITY_PENALTY = 30000` — Cost for stroke ambiguities
- `ORDER_PENALTY = 500` — Cost for phoneme ordering violations
- `STROKE_ASSIGNMENT_PENALTY = 1` — Base cost per stroke assignment
- Solver timeout: 90 seconds

## Verification approach

- `pytest src/test/` must pass after any `.py` change (522 tests at the time of writing).
- Behaviour-preserving changes are proven by a full rebuild following the rebuild table in
  `docs/PIPELINE.md` with `PYTHONHASHSEED=0`, comparing the md5s of `theory.tsv`, `theory2.tsv`,
  `resolved_press_sets.json`, `keypress_groups.json`, `realization_report.json`,
  `plover_stenalgo_dictionary.json` and `steno-trainer/public/data/*.json` against a
  pre-change baseline — they must be identical.
- The hand-run ambiguity report (`python src/ambiguitychecker.py`, after Phonetic Theory
  Building (S5)) is the drift signal for homophone scope; its "overflow" metric counts
  lemma-homophone groups beyond the four-code budget.

## Conventions

- Phonemes use X-SAMPA notation (single ASCII chars, e.g., `@` for schwa, `R` for French R)
- Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda (consonants); `8` (ɥ) is a nucleus phoneme, `j`/`w` are consonants, all consonants after the first vowel go to the coda, and a vowel-less syllable goes entirely to the onset
- TSV files use tab separators; recent commits fixed spaces-vs-tabs issues
- `starboard3h.json` contains the pre-optimized keyboard mapping (26 keys: 22 phoneme keys + 4 reserved keys, 10 `*` and 15 `#` for the star/hash marks, 0/1 held for a possible third mark)
- Resource lexicon files in `resources/` are large (10-25MB TSV); `top500_books.txt` and `top500_film.txt` define frequent words
