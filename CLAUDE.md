# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stenalgo is a stenotype keyboard layout and theory generator for French. It uses constraint programming (Google OR-Tools CP-SAT solver) to optimize steno keyboard key assignments, minimizing both physical finger strain and mental complexity of the resulting stenographic theory. The primary target keyboard is the Starboard (26-key custom steno keyboard).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
# Prerequisites: a Python 3.12+ environment. Outputs: installed packages; no repo files.

# Run tests
pytest src/test/
# Prerequisites: dependencies installed. Outputs: console report only.

# Run a single test
pytest src/test/word_test.py::TestWord::test_method_name
# Prerequisites: dependencies installed. Outputs: console report only.

# Type checking
mypy src/
# Prerequisites: dependencies installed. Outputs: console report only.

# The pipeline in dependency order, run from the repo root (prefix PYTHONHASHSEED=0 when
# tracked outputs must be byte-reproducible); python dictionary.py orchestrates all of it.

python lexique.py                            # Lexicon Building (S1)
# Prerequisites: resources/Lexique383.tsv, LexiqueInfraCorrespondance.tsv, verbiste/*.xml.
# Outputs: resources/LexiqueMixte.tsv.

python -m util.build_synthetic_lexicon       # Synthetic Lexicon Building (S2), converged
# Prerequisites: LexiqueMixte.tsv (and PhoneticTheory.pickle for S2.1; rebuilt in memory if absent).
# Outputs: appends to resources/LexiqueSynthetic.tsv; if any round appended rows, deletes
# Dictionary.pickle/PhoneticTheory.pickle and reruns the S3-S5 build.

python -m util.optimize_keyboard             # Keyboard Layout Optimization (S4); rare, costly
# Prerequisites: Dictionary.pickle (or the lexicons, for an in-memory build), starboard3h.json.
# Outputs: starboard3h_optimized.json (--output PATH to choose; starboard3h.json is overwritten
# only by an explicit --output starboard3h.json). ~90 s per syllabic part, plus model building.
# After adopting a layout: rm -f Dictionary.pickle PhoneticTheory.pickle, then rebuild.

python -m util.build_phonetic_theory        # Dictionary Loading (S3) + Phonetic Theory
                                             # Building (S5)
# Prerequisites: the lexicons and starboard3h.json; rm -f Dictionary.pickle PhoneticTheory.pickle
# after ANY lexicon or layout change (the cache is never checked for staleness).
# Outputs: Dictionary.pickle, PhoneticTheory.pickle, phonetic_theory.tsv.

python -m src.elicitation --ask              # Elicitation Phase: Questionnaire Generation
# Prerequisites: Dictionary.pickle + PhoneticTheory.pickle.
# Outputs: questionnaire.json, elicitation_questionnaire.html.
# Then answer the page and copy the answers into elicitation_answers.json (human step).

python -m src.elicitation --resolve          # Press-Set Resolution, then the Grouping Phase
                                             # and the realization report
# Prerequisites: both pickles, elicitation_answers.json.
# Outputs: resolved_press_sets.json, keypress_groups.json, realization_report.json.

python -m util.build_disambiguated_theory   # Different-Lemma or Grammatical-Category
                                             # Disambiguation (S7): refreshes
                                             # disambiguated_theory.tsv

python -m util.export_plover_dictionary      # Theory Export (S8), Plover branch
# Prerequisites: both pickles, starboard3h.json, keypress_groups.json,
# resolved_press_sets.json, resources/reform1990.tsv.
# Outputs: plover_stenalgo_dictionary.json.

python -m util.export_plover_system
# Prerequisites: starboard3h.json. Outputs: plover_stenalgo/plover_stenalgo/_generated_keys.py.

python -m util.export_keyboard_layout        # Theory Export (S8), trainer branch
# Prerequisites: starboard3h.json; realization_report.json (marker legend; optional).
# Outputs: steno-trainer/public/data/keyboard-layout.json.

python -m util.export_practice_words
# Prerequisites: both pickles, starboard3h.json, keypress_groups.json,
# resolved_press_sets.json. Outputs: steno-trainer/public/data/practice-words.json
# (+ practice-words.json intermediate at the repo root).

python -m util.export_practice_sentences
# Prerequisites: practice-words.json (from export_practice_words), starboard3h.json,
# util/candidate_sentences.jsonl. Outputs: steno-trainer/public/data/practice-sentences.json.

python -m util.export_definitions
# Prerequisites: the export_practice_words inputs. Outputs: steno-trainer/public/data/definitions.json.

python dictionary.py                         # the orchestrator over everything from S2 to S8
# Prerequisites: as above (skips nothing; aborts on the first failing step).
# Outputs: all of the S2-S8 outputs above, in dependency order; per-step wall times
# appended to pipeline_timings.log (gitignored).
```

(Diagnostics, hand-run, stay out of the list above: `python -m src.ambiguitychecker`,
`python -m util.check_conjugation_disambiguation_order`, the featuregroupingsat K-scan
(`python src/featuregroupingsat.py`), the layout dumper (`python -m src.keyboard`).)

## Architecture

**Full reference: `docs/PIPELINE.md`** (call graph, rebuild order, dataset states, the
"Recomputing after a fix" checklist) and **`docs/GLOSSARY.md`** (canonical vocabulary).
Architecture and design rationale: `docs/ARCHITECTURE.md`. The eight stages:

1. **Lexicon Building (S1)** — `python lexique.py` → `resources/LexiqueMixte.tsv` (136,456 rows)
2. **Synthetic Lexicon Building (S2)** — `util/completeVerbParadigms.py` etc., run converged by `python -m util.build_synthetic_lexicon` (which the `python dictionary.py` orchestrator calls) → `resources/LexiqueSynthetic.tsv`
3. **Dictionary Loading (S3)** — inside `python -m util.build_phonetic_theory` → 167,639 Words, syllable inventory (cached in `Dictionary.pickle`)
4. **Keyboard Layout Optimization (S4)** — CP-SAT layout solve; rare and costly — `python -m util.optimize_keyboard` (seeds from the committed `starboard3h.json`, writes `starboard3h_optimized.json`)
5. **Phonetic Theory Building (S5)** — `Dictionary.buildPhoneticTheory` → the phonetic theory (`PhoneticTheory.pickle` + `phonetic_theory.tsv`; base strokes only, no homophone marks)
6. **Same-Lemma and Grammatical-Category Disambiguation (S6)** — three phases: Elicitation (`python -m src.elicitation --ask` / `--resolve`), Grouping (`python -m util.build_keypress_groups`), Realization (feature discriminating strokes; inline in `Dictionary.buildDisambiguatedTheory` + `python -m util.build_realization_report`)
7. **Different-Lemma or Grammatical-Category Disambiguation (S7)** — star/hash marks (`decideStarHashMark` rule stack), composed on the phonetic theory by `python -m util.build_disambiguated_theory` → the disambiguated theory (`disambiguated_theory.tsv`)
8. **Theory Export (S8)** — Plover (`util/export_plover_*`) and steno-trainer (`util/export_*`) branches; nothing reads `disambiguated_theory.tsv`, every exporter recomputes the disambiguated theory via `util/_theoryio.py`

Pitfalls: `dictionary.py` reuses `Dictionary.pickle`/`PhoneticTheory.pickle` whenever they exist and never checks them against the lexicon or layout (`rm -f *.pickle` after any lexicon or layout change — the Synthetic Lexicon Building (S2) wrapper deletes and rebuilds the pickles itself for rows its appenders add, but hand-made lexicon or layout edits remain the caller's responsibility; the orchestrator aborts on the first failing step); pin `PYTHONHASHSEED=0` when the tracked realization report must be reproducible; the NOM/ADJ cross-checkers need the external Morphalou 3.1 CSV (see `docs/PIPELINE.md` Synthetic Lexicon Building (S2)). The legacy discriminator path (`buildDiscriminatorSelection`, `satOptimizeDiscriminator`, `assignDiscriminatorKeypresses`) no longer runs: those functions are gone; `src/featureextractor.py` feeds only Synthetic Lexicon Building (S2)'s gating and the `ambiguitychecker` diagnostic, and of `src/greedyoptimizer.py` only `GRAMCAT_PRIORITY` is live (category-priority rule (R6)). Suspected bugs are listed in `TODO.md` ("Suspected bugs").

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

- `pytest src/test/` must pass after any `.py` change (538 tests at the time of writing).
- Behaviour-preserving changes are proven by a full rebuild following the rebuild table in
  `docs/PIPELINE.md` with `PYTHONHASHSEED=0`, comparing the md5s of `phonetic_theory.tsv`, `disambiguated_theory.tsv`,
  `resolved_press_sets.json`, `keypress_groups.json`, `realization_report.json`,
  `plover_stenalgo_dictionary.json` and `steno-trainer/public/data/*.json` against a
  pre-change baseline — they must be identical.
- The hand-run ambiguity report (`python -m src.ambiguitychecker`, after Phonetic Theory
  Building (S5)) is the drift signal for homophone scope; its "overflow" metric counts
  lemma-homophone groups beyond the four-code budget.

## Conventions

- Phonemes use X-SAMPA notation (single ASCII chars, e.g., `@` for schwa, `R` for French R)
- Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda (consonants); `8` (ɥ) is a nucleus phoneme, `j`/`w` are consonants, all consonants after the first vowel go to the coda, and a vowel-less syllable goes entirely to the onset
- TSV files use tab separators; recent commits fixed spaces-vs-tabs issues
- `starboard3h.json` contains the pre-optimized keyboard mapping (26 keys: 22 phoneme keys + 4 reserved keys, 10 `*` and 15 `#` for the star/hash marks, 0/1 held for a possible third mark)
- Resource lexicon files in `resources/` are large (10-25MB TSV); `top500_books.txt` and `top500_film.txt` define frequent words
