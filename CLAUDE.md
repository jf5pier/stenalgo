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

# Rebuild the Phase P physical-realization artifact
python -m util.build_phase_p_realization

# Regenerate steno-trainer's data exports (run after starboard3h.json or the lexicon changes)
python -m util.export_keyboard_layout
python -m util.export_practice_words
python -m util.export_practice_sentences
python -m util.export_definitions
```

## Architecture

### Processing Pipeline

The two homophone problems have separate mechanisms, decided by the 2026-09-18
elicitation-first pivot. **Authoritative status docs: `ROADMAP.md`'s "Status update"
section and `ATOMIC_KEYPRESS_REWIRE_PLAN.md`** — read those before touching the
disambiguation layers; older notes describing a solver-picks-features design are
superseded.

1. **Lexicon Building** (`lexique.py`) — Merges Lexique383 and LexiqueInfra into `resources/LexiqueMixte.tsv` (136k French words with frequencies, phoneme and grapheme syllable breakdowns)
2. **Dictionary Loading** (`dictionary.py`) — Indexes words by orthography, lemma, and frequency; identifies homophones; excludes words from `excluded_words.txt`
3. **Feature Extraction** (`src/featureextractor.py`) — Analyzes homophones and extracts discriminating features (grammatical category, gender, number, etc.); feeds the legacy path below
4. **Phoneme layout (solved, static)** — `src/cpsatsolver.py::optimizeKeyboard` (CP-SAT minimizing ambiguity/ergonomics/order violations) is real but its call is commented out; the live pipeline loads the committed `starboard3h.json` instead
5. **Same-lemma homophones (elicit → group → realize)**:
   - **Phase E** (`src/elicitation.py`) — the user's own marker presses, elicited pair-by-pair via a web questionnaire (`elicitation_answers.json` tracked; `resolved_press_sets*.json` gitignored, regenerable)
   - **Phase G** (`src/phaseg.py` greedy, `src/phasegsat.py` exact CP-SAT) — groups elicited markers onto abstract keypresses (K=5, proven optimal; adopted output `phase_g_keypress_assignment.json`)
   - **Phase P** (`src/ambiguitychecker.py::realizeKeypressGroupsAsExtraStroke`) — realizes each group as a physical coda-bank extra trailing stroke; canonical build `python -m util.build_phase_p_realization` → `phase_p_keypress_realization.json`. The must-stay-green regression: 0 residual same-`lemmeGramCat` collisions
6. **Lemma-homophones (`*`/`#` track)** (`src/ambiguitychecker.py`) — `decideStarHashMark` rule stack (homograph exemption → 1990-reform doublet → per-pair `MARKING_OVERRIDES` → 10x frequency-ratio exemption → same-`gramCat` → `GRAMCAT_PRIORITY`) → `rankHomophoneCluster`/`assignStarHashMarks` (N-ary, escalates with extra `*#` syllables) → `assignStarHashPhysicalStrokes`/`composeReservedKeyStrokes` (`STAR_KEY`=10, `HASH_KEY`=15, keys 0/1 held for a possible 3rd mark). Validated pure-function pipeline, **not yet wired into `dictionary.py`'s persisted output**
7. **Legacy path still live in `dictionary.py` `__main__` (superseded, retirement pending)** — `buildDiscriminatorSelection` + `satOptimizeDiscriminator` color solver-chosen same-lemma features onto the reserved keys and only print; `src/greedyoptimizer.py`'s `assignDiscriminatorKeypresses` is orphaned (implemented, tested, never called). `FEATURE_PRIORITY`/`GRAMCAT_PRIORITY` in `src/greedyoptimizer.py` still do live work (canonical-form picks)

### Core Data Model

- **`src/grammar.py`** — Phonology primitives: `Phoneme`, `Biphoneme`, `Multiphoneme`, `Syllable` and their collection classes. French uses 23 consonants + 16 vowels in X-SAMPA notation (single ASCII characters).
- **`src/word.py`** — `Word` dataclass with orthography, phonology, lemma, `GramCat` enum (21 grammatical categories), gender/number, verb conjugation info, corpus frequencies (books + film subtitles).
- **`src/keyboard.py`** — Abstract `Keyboard` base class; `Starboard` implementation with `FingerWeights`/`PositionWeights` cost models. Key type aliases: `Stroke`, `Strokes`, `Keypress`.

### Key Constants (cpsatsolver.py)

- `AMBIGUITY_PENALTY = 30000` — Cost for stroke ambiguities
- `ORDER_PENALTY = 500` — Cost for phoneme ordering violations
- `STROKE_ASSIGNMENT_PENALTY = 1` — Base cost per stroke assignment
- Solver timeout: 90 seconds

## Conventions

- Phonemes use X-SAMPA notation (single ASCII chars, e.g., `@` for schwa, `R` for French R)
- Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda (consonants)
- TSV files use tab separators; recent commits fixed spaces-vs-tabs issues
- `starboard3h.json` contains the pre-optimized keyboard mapping (26 keys, 4 reserved for control)
- Resource lexicon files in `resources/` are large (10-25MB TSV); `top500_books.txt` and `top500_film.txt` define frequent words
