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
```

## Architecture

### Processing Pipeline

1. **Lexicon Building** (`lexique.py`) — Merges Lexique383 and LexiqueInfra into `resources/LexiqueMixte.tsv` (136k French words with frequencies, phoneme and grapheme syllable breakdowns)
2. **Dictionary Loading** (`dictionary.py`) — Indexes words by orthography, lemma, and frequency; identifies homophones; excludes words from `excluded_words.txt`
3. **Feature Extraction** (`src/featureextractor.py`) — Analyzes homophones and extracts discriminating features (grammatical category, gender, number, etc.) for disambiguation
4. **Optimization** (`src/cpsatsolver.py`, `src/cpsatoptimizer.py`) — CP-SAT constraint solver assigns phonemes to keys minimizing ambiguity, finger strain, and phoneme ordering violations
5. **Greedy Disambiguation** (`src/greedyoptimizer.py`) — Assigns discriminating features to homophone groups

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
