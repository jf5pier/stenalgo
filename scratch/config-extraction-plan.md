# Extract user-preference parameters to a root `config.toml`

Plan written 2026-09-23, not yet executed. Companion document with the full
ready-to-paste TOML, loader code sketch and exact verification commands:
`scratch/config-extraction-plan-full-detail.md`.

## Context

The pipeline's user-preference decisions are hardcoded Python constants scattered across ~14 modules. Worst case: the subjonctif-imparfait out-of-scope decision (2026-09-21) is enforced independently in **four places in two vocabularies** (Lexique `sub:imp` codes vs French feature atoms), so re-scoping tenses for a different typist means coordinated code edits in S1, S2, S5 and the trainer export. Same for marker mnemonics (`PREFERRED_KEYS_BY_MARKER` is commented "Human preference (2026-09-22 session)"), the frequency model (`src/word.py`: "Formula to be optimized following the need of the typist" — the code even carries a commented-out `0.9*film + 0.1*book` alternative), and the ergonomic weights.

Outcome: one tracked, human-editable **`config.toml`** at the repo root + a typed fail-loudly loader (`src/config.py`). Committed values reproduce today's outputs **byte-identically** (md5-verified full rebuild). A different user edits the TOML, not the code.

## Approved scope (user, 2026-09-23)

- **In**: A tense/mood scope · B marker & marking preferences · C corpus & orthography policy · E ergonomic/solver weights
- **Out**: D trainer export knobs (DEFAULT_LIMIT, CONTEXT_MOOD_PRIORITY, PRONOUNS, H_ASPIRE_LEMMAS) and all structural facts (phoneme inventories, GramCat, reserved keys, finger wiring, key partition, reform exception sub-tables)

## Key architectural facts (verified against HEAD d2d4fa0)

1. **Import cycle**: `word.py` needs CONFIG (frequency) but CONFIG validation needs the verb-tag vocabulary inside `Word.splitInfoVerb` (`src/word.py:102-127`) → extract those tables to a new **leaf module `src/verbfeatures.py`**. Layers: `word → config → verbfeatures`.
2. **`lexique.py` executes at module level** (no `__main__` guard; `Lexique()` at :1261); its six reform flags are consumed at import. It already imports `src.grammar`, so importing `src.config` works.
3. **`Starboard._fw` / `_possibleKeypress` are class attributes** (`src/keyboard.py:325-366`) built at class-definition time; neither is serialized into `starboard3h.json` nor the pickles — ergonomic retuning needs no pickle rebuild.
4. **`buildStrokes` iterates each finger's keypress dict in insertion order** (`src/keyboard.py:496-518`) → `getPossibleStrokes` order depends on combo order. The TOML must list combos in the exact current literal order; a golden test pins it.
5. **Keep every constant NAME at its current location; only definitions change** to derive from CONFIG. `PREFERRED_KEYS_BY_MARKER` is imported by name (`util/build_realization_report.py:28`), `GRAMCAT_PRIORITY` (`src/ambiguitychecker.py:36`), tests use `FingerWeights()`, `wordFeatureCombinations(word)` — all stay untouched.
6. `'starboard3h.json'` is hardcoded in **8 sites**, not 5: `dictionary.py:623`, `src/ambiguitychecker.py:1180`, `util/build_realization_report.py:46`, `util/export_plover_dictionary.py:32`, `util/export_plover_system.py:16`, `util/export_keyboard_layout.py:25`, `util/export_practice_words.py:50`, `util/completeVerbParadigms.py:64`.
7. ROADMAP.md citations at `verbparadigm.py:399` and `lexique.py:1159` are stale (no subjonctif text there); live spec = docs/specs/discriminating-features.md:44, docs/PIPELINE.md S1.9.2.
8. Pickle trap: `Word.frequency` and frequent-word data live **inside `Dictionary.pickle`** — `[frequency]`/`[lexicon]` changes are invisible to the cache; `rm -f *.pickle` is mandatory.

## New files

### `config.toml` (repo root, tracked) — sections

| Section | Keys | Today's values (→ source) |
|---|---|---|
| `[tense_scope]` | `out_of_scope_tag_prefixes` | `["sub:imp"]` — canonical `"mode:tense"` code prefixes; one entry drives all 4 sites |
| `[practice_sentences]` | `out_of_scope_tag_prefixes` | `["sub:", "ind:pas"]` — deliberately broader trainer scope, separate key |
| `[markers.preferred_keys]` | marker → key list | `"impératif"=[18], "pers_2"=[19], "pers_3"=[20]` (`src/ambiguitychecker.py:776`) |
| `[grouping]` | `alone_keys`, `must_differ_groups`, `[[grouping.preference_tiers]]` (`type`/`pairs`/`group`) | from `util/build_keypress_groups.py:41-47` |
| `[star_hash]` + `[star_hash.gramcat_priority]` | `ratio_exemption_threshold` = 10.0; ADV 50 … ADJ:pos 0 | `src/ambiguitychecker.py:89`, `src/greedyoptimizer.py:14` |
| `[frequency]` | `film_weight`=1.0, `book_weight`=0.0 | reproduces `src/word.py:93` film-only bitwise (`1.0*x == x`, `x+0.0*y == x` for non-negative floats) |
| `[lexicon]` | `nb_frequent_words`=200, `frequent_words_file`="resources/top500_film.txt" | `dictionary.py:64,71` |
| `[reform1990]` | 6 booleans (lemmes, ortho, emprunt_pluriel, eler_eter, interpeler, absous_dissous), all true | `lexique.py:95,145,326,420,505,534`; kills the stale "Off by default" comments |
| `[keyboard]` | `layout_file`, `multi_finger_discount`=0.85 | 8 sites → one key |
| `[keyboard.shape]` | zigzag/gap 100, adjacent_triple_roll_bonus −50, spread_triple_penalty 50, quad_roll_bonus −100 | `src/keyboard.py:571-604` |
| `[keyboard.finger_weights]` | 17 tier names incl. `noPress`=0 (keys mirror `FingerWeights` attribute names) | `src/keyboard.py:47-70` |
| `[keyboard.finger_keypress_tiers.<finger>]` | 10 finger sub-tables; combo strings `"(0, 1)"` → tier names, **in the current literal order** | `src/keyboard.py:326-366` |
| `[solver]` | penalties 1/30000/500, time_limit_s 90, log, max_multiphonemes 2000, max_keys_per_stroke 4 (from `range(1,5)`), grouping_time_limit_s 30 | `src/cpsatsolver.py:25-30,68`; `src/featuregroupingsat.py:359,398` |

Every section header comment carries: the dated rationale moved from the code + which rebuild it triggers (table below). Full file content: companion doc §1.

### `src/config.py` — typed loader
- Frozen dataclasses per section; `TenseScope` owns the derivations: `excludedFiniteSlotCodes()` (prefixes as slot codes), `atomSets()` (`{MODE_ATOMS[m], TENSE_ATOMS[t]}` per prefix → `{"subjonctif","imparfait"}`), `stripTags(infoVerb)` (generalized `stripSubjonctifImparfait` — testable without importing lexique.py).
- `loadConfig(path=DEFAULT_CONFIG_PATH)` (pure; tests use tmp files) + module-level `CONFIG = loadConfig()`. Path anchored `Path(__file__).resolve().parent.parent / "config.toml"` (cwd-independent).
- **Fail loudly**: `ConfigError(RuntimeError)` naming `path:section.key`; strict schema — unknown section/key rejected with allowed list; value validation (tense prefixes must be known `mode:tense` codes; marker/atom names ⊆ `KNOWN_FEATURE_ATOMS`; preferred keys in coda bank 16..25; finger tables reference known tiers/fingers with `()`→`noPress` per finger and sorted-unique ints 0..25; frequency weights ≥0, one >0; discount ∈ (0,1]). Combo strings parsed with `ast.literal_eval`, document order preserved.
- `gramcat_priority` keys NOT validated here (cycle with `src.word`) — validated at import of `src/greedyoptimizer.py` + pinned by a test.
- No env override, no layering, no mutation.

### `src/verbfeatures.py` — leaf vocabulary module
`MODE_ATOMS`/`TENSE_ATOMS` extracted verbatim from `splitInfoVerb` (dict insertion order reproduces today's emit order) + `KNOWN_FEATURE_ATOMS` (mood/tense atoms + infinitif, pers_1-3, nbr_s/nbr_p, m/f/s/p, VER). `Word.splitInfoVerb` re-emits via these tables (identical output).

### `resources/markingOverrides.tsv` — MARKING_OVERRIDES moves to TSV (not TOML)
The 49-entry per-pair table (`src/ambiguitychecker.py:129-179`, rule R3) is **data with per-entry provenance**, not a preference — repo precedent is note-carrying TSVs (`lexiconExclusions.tsv`, `reform1990.tsv`). Format: `#` preamble (today's block comment) + `orthoA<TAB>orthoB<TAB>marked<TAB>note` rows in today's order. Loader `loadMarkingOverrides()` mirrors `loadReform1990DoubletPairs` (:92-117); validates `marked ∈ {orthoA, orthoB}`, rejects conflicting duplicate pairs. `MARKING_OVERRIDES = loadMarkingOverrides()` keeps name and site (:218).

## Per-file changes (definitions only; names preserved)

1. `src/word.py` — :93 `self.frequency = CONFIG.frequency.film_weight * self.frequencyFilm + CONFIG.frequency.book_weight * self.frequencyBook`; :102-127 `splitInfoVerb` emits via verbfeatures.
2. `lexique.py` — six flags ← `CONFIG.reform1990.*`; delete `stripSubjonctifImparfait`, call site :1185 → `CONFIG.tense_scope.stripTags(...)`; delete stale "Off by default" comments; fix ROADMAP citations.
3. `src/verbparadigm.py:397` — split structural vs scope: `_STRUCTURAL_FINITE_SLOT_EXCLUDED_CODES = frozenset({"inf","par:pre","par:pas"})` (own generation paths, stays in code) ∪ `CONFIG.tense_scope.excludedFiniteSlotCodes()`; :417 check unchanged.
4. `src/elicitation.py:55` — module `OUT_OF_SCOPE_ATOM_SETS = CONFIG.tense_scope.atomSets()`; filter `not any(s <= c for s in _outOfScope)` via new defaulted parameter (keeps `wordFeatureCombinations(word)` single-arg calls/tests working).
5. `util/export_practice_sentences.py:45` — ← `CONFIG.practice_sentences.out_of_scope_tag_prefixes` (tuple; :77 `startswith` unchanged).
6. `src/ambiguitychecker.py` — :89 ← config; :129-179 ← TSV loader; :776 `dict(CONFIG.markers.preferred_keys)`; :1180 layout file ← config.
7. `src/greedyoptimizer.py:14` — `dict(CONFIG.star_hash.gramcat_priority)` + import-time unknown-GramCat-name check (`from src.word import GramCat` — no reverse edge).
8. `util/build_keypress_groups.py:41-47` — ← config via local `tierFromSpec` (builds `SameKeyPreference`/`ExclusiveGroupPreference`; config must not import ortools); pass `timeLimitS=CONFIG.solver.grouping_time_limit_s` explicitly. Serialization untouched → keypress_groups.json byte-identical.
9. `src/keyboard.py` — `FingerWeights` → frozen dataclass, same 17 attribute names defaulted from CONFIG; `_possibleKeypress` built by `_positionWeightsFromConfig(FingerWeights())`; module constants for the 5 shape costs + discount (used by `_strokeZigZagCost`, `_strokeGapCost`, `getStrokeShapeCost`, :569). The `syllabicPart in ["onset","coda"]` condition (:567) stays (thumb bank has no column geometry — structural).
10. `src/cpsatsolver.py` — :25-30 hoisted to module level from CONFIG; :68 `range(1, CONFIG.solver.max_keys_per_stroke + 1)`. `src/featuregroupingsat.py` signatures unchanged (defaults stay for API compat).
11. `dictionary.py` — :64/:71 ← `CONFIG.lexicon.*`; :623 layout file ← config.
12. Remaining 6 layout-file sites (see fact 6) ← `CONFIG.keyboard.layout_file`.

## Staged execution (each stage = natural commit boundary; verify before proceeding)

- **Stage 1 — infrastructure, zero behavior change**: verbfeatures.py, config.py, config.toml, markingOverrides.tsv (data copied verbatim; old literal still live), config_test.py, splitInfoVerb refactor. Verify: `pytest src/test/` + `mypy src/`.
- **Stage 2 — S1/S3 consumers (risky half)**: lexique flags + stripTags, verbparadigm split, elicitation filter, word frequency, dictionary lexicon defaults. Verify: `python lexique.py` → `git diff` on LexiqueMixte.tsv **empty** (proves S1 preservation alone), then full rebuild + md5 compare.
- **Stage 3 — S6/S7/S8 consumers (fast verify)**: ambiguitychecker, greedyoptimizer, build_keypress_groups, keyboard ergonomics, cpsatsolver, layout-file plumbing (grep `starboard3h.json` afterwards — only config.toml + docs may mention it), practice sentences; delete the dead MARKING_OVERRIDES literal. Verify: pickles still valid → `PYTHONHASHSEED=0 python dictionary.py` + md5 compare.
- **Stage 4 — docs**: CLAUDE.md (preferences paragraph + pitfalls: config read once at import; `[frequency]`/`[lexicon]` live inside the pickles), docs/PIPELINE.md §Configuration with the rebuild table + scope-citation updates.

### Rebuild implications per section (→ TOML comments + PIPELINE.md table)

| Section | Rebuild after a change |
|---|---|
| tense_scope | `python lexique.py`; `rm -f *.pickle`; `python dictionary.py` (LexiqueMixte.tsv is tracked; step-4h human loop if new oppositions) |
| practice_sentences | `python -m util.export_practice_sentences` |
| markers, star_hash, keyboard weights/shape | `python dictionary.py` (fast, pickles reusable) + exports |
| grouping | `python -m util.build_keypress_groups` → `python dictionary.py` → exports (keypress_groups.json tracked) |
| frequency, lexicon | `rm -f *.pickle` **mandatory** → `python dictionary.py` → exports |
| reform1990 | `python lexique.py` → `rm -f *.pickle` → `python dictionary.py` → exports |
| keyboard.layout_file | `rm -f *.pickle` → `python dictionary.py` → exports (a layout change) |
| solver | only when the commented-out S4 solve is re-enabled; grouping limit never changes results |

## Tests & verification

New `src/test/config_test.py` (~15 tests): committed-config parse + value spot-checks; missing/malformed file → ConfigError with path; unknown section/key (typo guard); tense-prefix validation (`"subjonctif"`, `"sub:zz"`, `"sub:imp:1s"` rejected); atom derivation == `{"subjonctif","imparfait"}`; `stripTags` cases; verbparadigm union == the 4-code set; GramCat names valid; marker names ⊆ KNOWN_FEATURE_ATOMS; preferred keys in 16..25; finger tier/finger validation; **FingerWeights-fields ↔ config-names contract**; **PositionWeights golden order+content** (per-finger key sequences hardcoded in the test — order matters); frequency film-only bitwise identity; custom-scope `wordFeatureCombinations`.

All 522 existing tests must pass **unchanged** (elicitation_test.py:64,72, keyboard_test.py, ambiguitychecker_test.py:185-188 double as behavior-preservation proof). `mypy src/` clean.

**md5 protocol** (from a clean tree, BEFORE any change, and repeated after Stages 2 and 3):
```bash
git status --porcelain                 # clean tree first
python lexique.py                      # S1 rerun must be byte-identical
md5sum resources/LexiqueMixte.tsv resources/LexiqueSynthetic.tsv > /tmp/stenalgo-baseline.md5
rm -f Dictionary.pickle FirstTheory.pickle
PYTHONHASHSEED=0 python dictionary.py
md5sum theory.tsv theory2.tsv resolved_press_sets.json keypress_groups.json \
      realization_report.json plover_stenalgo_dictionary.json \
      plover_stenalgo/plover_stenalgo/_generated_keys.py \
      steno-trainer/public/data/*.json >> /tmp/stenalgo-baseline.md5
```
After each stage: rebuild the same way, `md5sum -c /tmp/stenalgo-baseline.md5` — every line OK; `git status --porcelain` shows no tracked diff (LexiqueMixte.tsv, LexiqueSynthetic.tsv, keypress_groups.json, realization_report.json, plover dict, _generated_keys.py, trainer data are all tracked).

## Deferred (separate follow-up)

The `conjugation_disambiguation_order.txt` parse quirk (prose line "features to discriminate" parsed as junk combination #47 in `util/check_conjugation_disambiguation_order.py:43-57`) — diagnostic-only, gitignored report, zero pipeline effect; fixing it here would add an unverified behavior change to an otherwise md5-provable refactor.
