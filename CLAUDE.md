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
mypy                                          # the scope is set in mypy.ini: src/, util/, dictionary.py, lexique.py
# Prerequisites: dependencies installed. Outputs: console report only.

# The pipeline in dependency order, run from the repo root; python dictionary.py orchestrates all of it.

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
# After adopting a layout: rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle, then rebuild.

python -m util.build_phonetic_theory        # Dictionary Loading (S3) + Phonetic Theory
                                             # Building (S5)
# Prerequisites: the lexicons and starboard3h.json; rm -f Dictionary.pickle PhoneticTheory.pickle
# after ANY lexicon or layout change (those two caches are never checked for staleness;
# DisambiguatedTheory.pickle fingerprint-checks itself, see Pitfalls below).
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
                                             # disambiguated_theory.tsv and writes the
                                             # fingerprinted DisambiguatedTheory.pickle
                                             # the S8 exporters load

python -m util.export_plover_dictionary      # Theory Export (S8), Plover branch
# Prerequisites: both pickles, starboard3h.json, keypress_groups.json,
# resolved_press_sets.json, resources/reform1990.tsv.
# Outputs: plover_stenalgo_dictionary.json.

python -m util.export_plover_system
# Prerequisites: starboard3h.json. Outputs: plover_stenalgo/plover_stenalgo/_generated_keys.py.

python -m util.export_plover_complements
# The system's own punctuation and cursor commands, converted key to key from Plover English / Lapwing (the `position` rows of
# resources/outlineClassification.tsv; French spacing, collision filter). Prerequisites: starboard3h.json, plover_stenalgo_dictionary.json.
# Outputs: plover_stenalgo_punctuation.json, plover_stenalgo_commands.json (listed above the theory in the plugin's DEFAULT_DICTIONARIES),
# plover_stenalgo_pluvier_punctuation.json (the Pluvier chords: shipped in the package and listed in the defaults below the Plover punctuation, so Plover's chord wins a shared one).

python -m util.export_plover_numbers
# The number dictionaries, converted key to key (the number bar is the Stenalgo `#` key): Pluvier's bar digits (Plover mapping, 1023 subsets; the top `S` is the Stenalgo `k-`: `k-#` = 1)
# and Lapwing's numpad (resources/reference/lapwing-numbers.json, hours in French). Prerequisites: starboard3h.json, plover_stenalgo_dictionary.json, the punctuation and commands files.
# Outputs: plover_stenalgo_pluvier_numbers.json, plover_stenalgo_lapwing_numbers.json (shipped by export_plover_plugin; the Pluvier one is listed above the Lapwing one = the default).

python -m util.export_expression_data [OUT]   # expression layer data for the Plover plugin
# Prerequisites: the committed rule set (scratch/expr-rules-final.json, expr-briefs.tsv, expr_candidates.tsv),
# both pickles, starboard3h.json, plover_stenalgo_dictionary.json (the word index is read from it).
# Outputs: plover_stenalgo_expressions.stenalgo (0.3 MB; default next to the repo root, OUT to choose).
# It must travel with the plover_stenalgo_dictionary.json it was built against: a fingerprint refuses a mismatch.

python -m util.export_plover_plugin
# Copies the stdlib-only decoder modules src/{strokes,expressionmodel,keyconflicts,elision,expressiondecoder,
# expressionranking,expressiondata}.py into plover_stenalgo/plover_stenalgo/_core/ (tracked; a test fails when stale), and
# plover_stenalgo_dictionary.json + plover_stenalgo_expressions.stenalgo + plover_stenalgo_punctuation.json + plover_stenalgo_commands.json + plover_stenalgo_pluvier_punctuation.json + plover_stenalgo_pluvier_numbers.json + plover_stenalgo_lapwing_numbers.json into plover_stenalgo/plover_stenalgo/dictionaries/
# (gitignored package assets, fingerprint-checked; run it after export_expression_data, then build/install the plugin).

python -m util.sync_plover_mirror MIRROR_CLONE [--push]
# Copies the plugin package, data included, into a clone of github.com/jf5pier/stenalgo-plover (the Plover install source)
# and commits there; --push publishes it. Run after export_expression_data.

python -m util.export_keyboard_layout        # Theory Export (S8), trainer branch
# Prerequisites: starboard3h.json; realization_report.json (marker legend; optional).
# Outputs: steno-trainer/public/data/keyboard-layout.json.

python -m util.export_practice_words
# Prerequisites: both pickles, starboard3h.json, keypress_groups.json,
# resolved_press_sets.json. Outputs: steno-trainer/public/data/practice-words.json.

python -m util.export_practice_sentences
# Prerequisites: steno-trainer/public/data/practice-words.json (from export_practice_words),
# starboard3h.json, util/candidate_sentences.jsonl.
# Outputs: steno-trainer/public/data/practice-sentences.json.

python -m util.export_definitions
# Prerequisites: the export_practice_words inputs. Outputs: steno-trainer/public/data/definitions.json.

python -m util.export_lessons
# Prerequisites: both pickles, starboard3h.json, resolved_press_sets.json,
# realization_report.json. Outputs: steno-trainer/public/data/lessons.json.

python -m util.build_affix_rules             # Affix Abbreviation Building (S9a), optional layer after S8
# Prerequisites: both pickles, starboard3h.json, the committed affix_decisions.json (the user's fusion/growth verdicts).
# Outputs: affix_rules.json, affix_rules_report.md, AffixSelection.pickle (gitignored cache: absent = full ~2.5 min (measured on 16 cores; the default is at most 8 workers, --workers N; ~5.5 min serial)
# selection; present = reused, or reselected from its cached rule evaluations when the decisions changed; rm it after any
# lexicon or layout change). Asks nothing: undecided items get the safe default and are listed as PENDING.

python -m util.review_affix_rules            # hand-run, interactive: decides the PENDING affix items (y/n/s/q; growth before fusion), writes
                                             # affix_decisions.json after every answer and reselects by itself until nothing is pending

python -m util.export_affix_dictionary       # Affix Abbreviation Building (S9b)
# Prerequisites: both pickles, the committed affix_rules.json. Outputs: plover_stenalgo_affix_dictionary.json,
# affix_abbreviations.tsv.

python -m util.export_affix_lessons          # Affix Abbreviation Building (S9c): the trainer's affixes lesson track
# Prerequisites: both pickles, starboard3h.json, the committed affix_rules.json. Outputs: steno-trainer/public/data/affix-lessons.json
# (30 rule lessons + one on conjugated forms; the other trainer JSONs are untouched).

python -m util.export_affix_abbreviations   # Affix Abbreviation Building (S9d): the Definitions page's "Abbrev." column
# Prerequisites: affix_abbreviations.tsv (S9b). Outputs: steno-trainer/public/data/affix-abbreviations.json.

python -m util.export_expression_lessons     # Expression Abbreviation Lessons (S10a): the trainer's expressions lesson track
# Prerequisites: both pickles, starboard3h.json, the committed expression rule set (scratch/expr-rules-final.json, expr-briefs.tsv,
# expr_candidates.tsv). Outputs: steno-trainer/public/data/expression-lessons.json (one lesson per rule family, composed phrases, the briefs).

python -m util.export_expression_sentences   # Expression Abbreviation Lessons (S10b): the practice sentences with abbreviations
# Prerequisites: the S10a inputs plus practice-words.json (export_practice_words) and util/candidate_sentences.jsonl.
# Outputs: steno-trainer/public/data/expression-sentences.json (practice-sentences.json is untouched).

python -m util.export_expression_definitions # Expression Abbreviation Lessons (S10c): the Definitions page's attach words and composed phrases
# Prerequisites: the S10a inputs. Outputs: steno-trainer/public/data/expression-definitions.json (definitions.json is untouched).

python -m util.export_punctuation_lessons    # Punctuation and Command Lessons (S10d): the trainer's ponctuation and commandes tracks, Plover and Pluvier styles
# Prerequisites: plover_stenalgo_{punctuation,commands,pluvier_punctuation}.json (util.export_plover_complements), starboard3h.json, practice-words.json,
# the authored resources/punctuationLessons.json and util/punctuation_examples.jsonl. Outputs: steno-trainer/public/data/punctuation-lessons.json.

python -m util.export_number_lessons        # Number Lessons (S10e): the trainer's chiffres track, Lapwing numpad and Pluvier number bar (its own trainer button)
# Prerequisites: plover_stenalgo_{lapwing,pluvier}_numbers.json (util.export_plover_numbers), plover_stenalgo_punctuation.json, starboard3h.json, practice-words.json,
# the authored resources/numberLessons.json. Outputs: steno-trainer/public/data/number-lessons.json.

python dictionary.py                         # the orchestrator over everything from S2 to S10
# Prerequisites: as above (skips nothing; aborts on the first failing step).
# Outputs: all of the S2-S9 outputs above, in dependency order; per-step wall times
# appended to pipeline_timings.log (gitignored).
```

(Diagnostics, hand-run, stay out of the list above: `python -m src.ambiguitychecker`,
`python -m util.check_conjugation_disambiguation_order`,
`python -m util.validate_affix_markings` (the affix abbreviations keep every route's marks; ~25 s), the featuregroupingsat K-scan
(`python src/featuregroupingsat.py`), the layout dumper (`python -m src.keyboard`),
the Ngram toolbox (`python -m util.ngram_data download|extract-lexique|scan|query|purge`
— purge is manual-only by policy; the ~5 GB v3 shards live in gitignored
`googlebooks-fre-1grams/`), the variant-set builder (`python -m util.build_spelling_variants`
— emits the draft `resources/spellingVariants.tsv`; discovered sets never auto-activate),
and the Synthetic pruner (`python -m util.prune_spelling_variants`, dry-run by default),
and the affix-rule decisions (`affix_decisions.json`, see `docs/AFFIX_RULES.md`).)

## Architecture

**Full reference: `docs/PIPELINE.md`** (call graph, rebuild order, dataset states, the
"Recomputing after a fix" checklist) and **`docs/GLOSSARY.md`** (canonical vocabulary).
Architecture and design rationale: `docs/ARCHITECTURE.md`. The nine stages:

1. **Lexicon Building (S1)** — `python lexique.py` → `resources/LexiqueMixte.tsv` (136,203 rows); enforces `resources/spellingVariants.tsv` (one canonical spelling per variant set; `src/spellingvariants.py` hooks reconcile both the lemme normalization and the 1990-reform ortho rewrites, so the canonical may sit on either side of a reform pair)
2. **Synthetic Lexicon Building (S2)** — `util/completeVerbParadigms.py` etc., run converged by `python -m util.build_synthetic_lexicon` (which the `python dictionary.py` orchestrator calls) → `resources/LexiqueSynthetic.tsv`
3. **Dictionary Loading (S3)** — inside `python -m util.build_phonetic_theory` → 167,639 Words, syllable inventory (cached in `Dictionary.pickle`)
4. **Keyboard Layout Optimization (S4)** — CP-SAT layout solve; rare and costly — `python -m util.optimize_keyboard` (seeds from the committed `starboard3h.json`, writes `starboard3h_optimized.json`)
5. **Phonetic Theory Building (S5)** — `Dictionary.buildPhoneticTheory` → the phonetic theory (`PhoneticTheory.pickle` + `phonetic_theory.tsv`; base strokes only, no homophone marks)
6. **Same-Lemma and Grammatical-Category Disambiguation (S6)** — three phases: Elicitation (`python -m src.elicitation --ask` / `--resolve`), Grouping (`python -m util.build_keypress_groups`), Realization (feature discriminating strokes; inline in `Dictionary.buildDisambiguatedTheory` + `python -m util.build_realization_report`)
7. **Different-Lemma or Grammatical-Category Disambiguation (S7)** — star/hash marks (`decideStarHashMark` rule stack), composed on the phonetic theory by `python -m util.build_disambiguated_theory` → the disambiguated theory (`disambiguated_theory.tsv`)
8. **Theory Export (S8)** — Plover (`util/export_plover_*`, plus the expression-layer dictionary plugin: `docs/PIPELINE.md` S8.10) and steno-trainer (`util/export_*`) branches; nothing reads `disambiguated_theory.tsv`, every exporter recomputes the disambiguated theory via `util/_theoryio.py`
9. **Affix Abbreviation Building (S9)** — optional layer after S8, the theory is unchanged: S9a `util/build_affix_rules.py` selects 30 affix rules from the committed verdicts `affix_decisions.json` (cache `AffixSelection.pickle`; `util/review_affix_rules.py` is the hand-run interactive review of the pending decisions), S9b `util/export_affix_dictionary.py` writes the abbreviation dictionary; see `docs/AFFIX_RULES.md` (reference) and `docs/AFFIX_DESIGN.md` (philosophy, design choices, algorithms)

Pitfalls: `dictionary.py` reuses `Dictionary.pickle`/`PhoneticTheory.pickle` whenever they exist and never checks them against the lexicon or layout (`rm -f *.pickle` after any lexicon or layout change — `DisambiguatedTheory.pickle`, unlike the two, IS fingerprint-checked against its inputs (md5s of the lexicons, `starboard3h.json`, `keypress_groups.json`, `resolved_press_sets.json`) and reloads only on a match, so it needs no manual rm; the Synthetic Lexicon Building (S2) wrapper deletes and rebuilds the pickles itself for rows its appenders add, but hand-made lexicon or layout edits remain the caller's responsibility; the orchestrator aborts on the first failing step). Editing `resources/spellingVariants.tsv` or `resources/reform1990.tsv` counts as a lexicon change: rerun `python lexique.py`, prune the Synthetic file (`python -m util.prune_spelling_variants --apply`), then rebuild (the dropped spellings must not survive in `LexiqueSynthetic.tsv`; the S2 appenders read through the same choke point, so a dropped spelling that coincides with a conjugated form of a kept verb — `boite`/`boiter` — stays exempt, see `isDroppedOrthoRow`). The NOM/ADJ cross-checkers need the external Morphalou 3.1 CSV (see `docs/PIPELINE.md` Synthetic Lexicon Building (S2)). The legacy discriminator path (`buildDiscriminatorSelection`, `satOptimizeDiscriminator`, `assignDiscriminatorKeypresses`) no longer runs: those functions are gone; `src/featureextractor.py` feeds only Synthetic Lexicon Building (S2)'s gating and the `ambiguitychecker` diagnostic, and of `src/greedyoptimizer.py` only `GRAMCAT_PRIORITY` is live (category-priority rule (R6)). Suspected bugs are listed in `TODO.md` ("Suspected bugs").

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

## Process rules

- Never wait for a background job with `pgrep -f NAME` (or `pkill -f NAME`) in a Monitor or until-loop: the pattern matches the waiting shell's own command line, so the loop never ends and reports a finished job as still running. Wait on the job's log (`until grep -q DONE LOG; do sleep 15; done`) or on its task id.

## Verification approach

- `pytest src/test/` must pass after any `.py` change (1225 tests at the time of writing, expression layer, affix layer and lessons exporter included).
- `mypy` (bare, scope and options in `mypy.ini`) must report no issues after any `.py` change.
- Behaviour-preserving changes are proven by a full rebuild following the rebuild table in
  `docs/PIPELINE.md`, comparing the md5s of `phonetic_theory.tsv`, `disambiguated_theory.tsv`,
  `resolved_press_sets.json`, `keypress_groups.json`, `realization_report.json`,
  `plover_stenalgo_dictionary.json` and `steno-trainer/public/data/*.json` against a
  pre-change baseline — they must be identical. After a change that reaches the affix layer (S9) also compare
  `affix_rules.json`, `affix_rules_report.md`, `plover_stenalgo_affix_dictionary.json`, `affix_abbreviations.tsv` and `steno-trainer/public/data/affix-lessons.json`.
- After a change that reaches the trainer's affix lessons also compare `steno-trainer/public/data/affix-lessons.json`.
- The hand-run ambiguity report (`python -m src.ambiguitychecker`, after Phonetic Theory
  Building (S5)) is the drift signal for homophone scope; its "overflow" metric counts
  lemma-homophone groups beyond the four-code budget.

## Conventions

- Phonemes use X-SAMPA notation (single ASCII chars, e.g., `@` for schwa, `R` for French R)
- Syllables decompose into Onset (consonants) → Nucleus (vowels) → Coda (consonants); `8` (ɥ) is a nucleus phoneme, `j`/`w` are consonants, all consonants after the first vowel go to the coda, and a vowel-less syllable goes entirely to the onset
- TSV files use tab separators; recent commits fixed spaces-vs-tabs issues
- `starboard3h.json` contains the pre-optimized keyboard mapping (26 keys: 22 phoneme keys + 4 reserved keys, 10 `*` and 15 `#` for the star/hash marks, 0/1 held for a possible third mark)
- Resource lexicon files in `resources/` are large (10-25MB TSV); `top500_books.txt` and `top500_film.txt` define frequent words

### Typing conventions (keep `mypy` clean)

`mypy.ini` sets `check_untyped_defs`, so unannotated test and helper bodies are checked too. `mypy --strict`
is clean on production code (`src/`, `util/`, `dictionary.py`, `lexique.py` outside `src/test/`); keep it so
(the tests still carry about 1400 strict-only missing-annotation errors, tolerated for now).

- Annotate every new production function (parameters and return). Nested helpers and `__eq__`/`__lt__` too:
  `__eq__(self, other: object) -> bool`, `__lt__(self, other: "Cls") -> bool`.
- Parameterize generics: `dict[str, Any]`, `list[int]`, `Counter[str]`, never a bare `dict`/`list`/`tuple`/`Counter`.
- Do not reuse a variable name for a different type in one function (loop variables included); rename instead.
  Most of the historical errors were this.
- Narrow Optionals before use: `Starboard.fromJSONFile` returns `Self | None`, and `Decisions.growthForms`,
  `proposeGrowth`, `loadStore` etc. can return `None`. In tests use `assert x is not None` (or a small helper).
- Import a name from the module that defines it, not from a module that merely re-imports it
  (`canonicalizeStrokes` from `src.keyboard`, `routesOf` from `src.affixes`, `Lemme` from `src.word`,
  `MAX_ALTERNATIVES` from `src.affixbinding`): mypy rejects implicit re-exports.
- Do not write `_ = obj.method()` for a method that returns `None`; mypy flags it once the method is annotated.
- Types that would create an import cycle go under `if TYPE_CHECKING:` (see `util/_theoryio.py`).
- ortools stubs type solver statuses and `cp_model.OPTIMAL`-style constants as different enums, so
  `status == cp_model.OPTIMAL` needs `# type: ignore[comparison-overlap]` (false positive, works at runtime).
- Test data that is deliberately simplified (fake stroke tuples, `Word(**defaults)` dicts) is annotated `Any`
  (`defaults: dict[str, Any]`); an intentionally unused argument is the module-level `NONE: Any = None`.
- Run bare `mypy`, not `mypy src/`: the latter skips `util/`, `dictionary.py` and `lexique.py`.
