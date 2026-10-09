# Implementation plan: extract user-preference parameters into `config.toml`

Repo: /home/jfsp/stenalgo (branch `main`, HEAD 3a84cc5). Python 3.14.7 (`tomllib` is stdlib).
Goal: one tracked TOML file at the repo root holding every user-preference parameter currently
hardcoded in Python, plus a typed, fail-loudly loader (`src/config.py`). Committed defaults must
reproduce today's outputs byte-identically (md5 protocol below). Nothing structural moves.

All line numbers below were verified against HEAD on 2026-09-23.

---

## 0. Key architectural facts driving the design (verified)

1. `lexique.py` executes everything at module level (no `__main__` guard; `lexique = Lexique()`
   at :1261) and its six `APPLY_1990_REFORM_*` flags are consumed at import time (:131, :313,
   :376, :483, :1229, :1238). It already imports `src.grammar`, so `import src.config` works.
2. `Starboard._fw` (FingerWeights) and `Starboard._possibleKeypress` (PositionWeights) are
   **class attributes built at class-definition time** (keyboard.py:325-366). Neither is
   serialized into `starboard3h.json` (it stores only `phonemesAssignedToStroke`) nor into the
   pickles — cost retuning needs no pickle rebuild.
3. `buildStrokes` (keyboard.py:496-518) iterates each finger's keypress dict **in insertion
   order**, so `getPossibleStrokes` output order depends on the per-finger combo order. The TOML
   must list combos in exactly the current literal order (tomllib preserves document order);
   a golden unit test pins it.
4. Import-cycle constraint: `src/word.py` will need CONFIG (frequency formula), and CONFIG
   validation needs the verb-tag vocabulary that today lives inside `Word.splitInfoVerb`
   (word.py:102-127). Resolution: extract the mode/tense atom tables into a new leaf module
   `src/verbfeatures.py` (imports nothing from `src/`). Layers: `word -> config -> verbfeatures`,
   `word -> verbfeatures`. `src/config.py` imports ONLY stdlib + `src.verbfeatures`.
5. `util/build_realization_report.py:28` imports `PREFERRED_KEYS_BY_MARKER` by name;
   `src/ambiguitychecker.py:36` imports `GRAMCAT_PRIORITY` from `src.greedyoptimizer`;
   `resolvePreferredKeysByGroup` (:785) uses it as a default parameter; tests reference
   `FingerWeights()`, `fw.pinky1keyHome`, `starboard._possibleKeypress`, and
   `wordFeatureCombinations(word)` (single arg). **Strategy: keep every constant NAME at its
   current location; only change its definition to derive from CONFIG.** Zero use-site churn,
   tests keep passing untouched.
6. `keypress_groups.json` serializes `aloneKeys`, `mustDifferGroups`, `preferenceTiers`
   (featuregroupingsat.py:427-465). The dataclasses must be constructed identically so the
   artifact stays byte-identical.
7. The `starboard3h.json` filename is hardcoded in **8** live sites, not 5:
   dictionary.py:623, src/ambiguitychecker.py:1180, util/build_realization_report.py:46,
   util/export_plover_dictionary.py:32, util/export_plover_system.py:16,
   util/export_keyboard_layout.py:25, util/export_practice_words.py:50,
   util/completeVerbParadigms.py:64.
8. `mypy src/` covers only `src/` — `lexique.py`, `dictionary.py`, `util/` are unchecked
   (config.py must be clean; util consumers just have to run).
9. Pickle trap (CLAUDE.md): `Dictionary.pickle` stores computed `Word.frequency`; any
   `[frequency]`/`[lexicon]` change silently keeps old values unless `rm -f *.pickle`.
10. ROADMAP.md no longer contains any subjonctif text (grep-verified); the scope citations in
    verbparadigm.py:399-400 and lexique.py:1159-1160 are stale. The live spec text is
    docs/specs/discriminating-features.md:44 ("Subjonctif imparfait is out of scope and dropped")
    and docs/PIPELINE.md (S1.9.2).

---

## 1. The TOML file — `config.toml` (repo root, tracked)

Exact content to commit (values copied mechanically from today's constants; comments carry the
dated rationales out of the code):

```toml
# config.toml — Stenalgo user preferences.
#
# Single source of truth for every tunable preference of the layout/theory pipeline.
# Loaded once at import by src/config.py (fail-loud). Committed values reproduce the
# committed outputs byte-identically; changing a value changes generated artifacts
# (LexiqueMixte.tsv, theory2.tsv, plover_stenalgo_dictionary.json, trainer data...)
# according to the "rebuild" note on each section — see docs/PIPELINE.md §Configuration.
#
# Structural facts (phoneme inventories, finger-to-key wiring, reserved keys 0/1/10/15,
# GramCat enum, exception sub-tables of the 1990 reform) deliberately stay in code.

# ─────────────────────────────────────────────────────────────────────────────
# Tense/mood scope of the theory.
# Rebuild: python lexique.py  →  rm -f Dictionary.pickle FirstTheory.pickle  →
#          python dictionary.py   (changes resources/LexiqueMixte.tsv, a tracked file;
#          LexiqueSynthetic.tsv may gain/lose rows via the S2 appenders; new
#          oppositions would need the docs/PIPELINE.md step-4h human loop).
#
# Lexique383/Verbiste "mode:tense" codes declared out of scope for the whole theory.
# Each entry is matched (a) exactly, as a Verbiste template slot code
# (src/verbparadigm.py allFiniteSlots), (b) as a prefix of Lexique383 infover tags
# ("sub:imp:1s"), and (c) as the atomized French feature pair {"subjonctif",
# "imparfait"} in src/elicitation.py wordFeatureCombinations.
#
# Subjonctif imparfait declared out of scope 2026-09-21 (elicitation-side exclusion
# since 2026-09-19): archaic/literary tense, not worth a keypress or synthetic
# completions — see docs/specs/discriminating-features.md and docs/PIPELINE.md S1.9.2.
[tense_scope]
out_of_scope_tag_prefixes = ["sub:imp"]   # must be "mode:tense" codes, both parts known

# ─────────────────────────────────────────────────────────────────────────────
# Practice-sentence vocabulary gate (trainer only — deliberately BROADER than the
# theory scope above: every subjonctif and the passé simple are kept out of drills).
# Rebuild: python -m util.export_practice_sentences   (after export_practice_words).
[practice_sentences]
out_of_scope_tag_prefixes = ["sub:", "ind:pas"]

# ─────────────────────────────────────────────────────────────────────────────
# Discriminating-feature marker preferences.
# Rebuild: python dictionary.py (theory-2 refresh) then the S8 exports — or one full
#          orchestrated run; the pickles stay valid.
[markers]
# Physical coda-bank key each marker should land on when feasible, keyed by marker
# (feature atom), not by group id (ids shift between Grouping Phase reruns).
# Human preference (2026-09-22 session): pers_3 on -t (mnemonic: many pers_3 forms
# end in a written "t"); impératif on -k and pers_2 on -d kept in that physical
# order, ahead of pers_3's -t. Honored by realizeKeypressGroupsAsExtraStroke
# whenever feasible; reported per marker by util/build_realization_report.py.
[markers.preferred_keys]
"impératif" = [18]   # -k
"pers_2"    = [19]   # -d
"pers_3"    = [20]   # -t

# ─────────────────────────────────────────────────────────────────────────────
# Discriminating-Feature Grouping (Grouping Phase) constraints (2026-09-19 session).
# Rebuild: python -m util.build_keypress_groups  →  python dictionary.py  →  exports
#          (keypress_groups.json is tracked and will change).
[grouping]
# HARD: can raise K or make the search infeasible.
alone_keys = ["f"]                                          # shares a keypress with nothing
must_differ_groups = [                                      # pairwise different keypresses
    ["infinitif", "pers_1", "pers_2", "pers_3"],
]
# SOFT, lexicographic tiers (tier 0 first; none can raise K).
[[grouping.preference_tiers]]     # 1. nbr_p shares a keypress with p
type = "sameKey"
pairs = [["p", "nbr_p"]]
[[grouping.preference_tiers]]     # 2. future shares a keypress with passé
type = "sameKey"
pairs = [["future", "passé"]]
[[grouping.preference_tiers]]     # 3. nbr_p/p's keypress stays exclusive to the two
type = "exclusiveGroup"
group = ["nbr_p", "p"]

# ─────────────────────────────────────────────────────────────────────────────
# Star/hash marking rules (Different-Lemma/GramCat Disambiguation, S7).
# Rebuild: python dictionary.py (theory-2 refresh) then the S8 exports; pickles stay
#          valid. Per-pair data lives in resources/markingOverrides.tsv (rule R3).
[star_hash]
# R4 "ratio exemption": pairs whose film-frequency ratio reaches this mark the rarer
# side and skip the category rules. Fitted 2026-09-20 (design session).
ratio_exemption_threshold = 10.0
# R6 category priority, higher = more canonical/unmarked. Fitted on the residual
# population after R4 and the homograph exemption: a single consistent linear order
# reproducing every observed pair-type's regret-optimal direction. Categories absent
# here fall back to per-pair frequency (R7).
[star_hash.gramcat_priority]
"ADV"     = 50
"PRO:pos" = 40
"NOM"     = 30
"VER"     = 20
"ADJ"     = 10
"ADJ:pos" = 0

# ─────────────────────────────────────────────────────────────────────────────
# Corpus frequency model. Rebuild: rm -f Dictionary.pickle FirstTheory.pickle →
#          python dictionary.py  →  exports  (frequency is INSIDE the pickles — the
#          cache never notices a change here; deleting it is mandatory).
[frequency]
# weighted = film_weight * freqfilms2 + book_weight * freqlivres.
# Film-only today ("formula to be optimized following the need of the typist",
# src/word.py): subtitle frequencies track spoken French, closer to dictation use.
film_weight = 1.0
book_weight = 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Dictionary loading (S3). Rebuild: rm -f *.pickle → python dictionary.py → exports.
[lexicon]
nb_frequent_words = 200                     # drills give these frequency 0 to avoid inflating weights
frequent_words_file = "resources/top500_film.txt"   # first line = corpus total, next N = frequent words

# ─────────────────────────────────────────────────────────────────────────────
# 1990 orthographic reform switches (S1). All on — the committed LexiqueMixte.tsv
# is generative under the new norm. Exception sub-tables (APPELER_EXCEPTIONS,
# JETER_FAMILY_EXCEPTIONS, ELER_ETER_DERIVED_NOUN_VERBS, INTERPELER_FIXED_FORMS)
# stay in code; pair data is resources/reform1990.tsv.
# Rebuild: python lexique.py → rm -f *.pickle → python dictionary.py → exports.
[reform1990]
lemmes = true          # reform lemmas normalize ({old: new} merged into spellingVariantLemme)
ortho = true           # rewrite ortho/orthosyll to the new spelling at output time
emprunt_pluriel = true # loanword plural regularization (barmen → barmans)
eler_eter = true       # -eler/-eter accent regularization (amoncelle → amoncèle)
interpeler = true      # interpeller → interpeler on the OQLF-listed fixed forms
absous_dissous = true  # absous/dissous → absout/dissout (VER rows only)

# ─────────────────────────────────────────────────────────────────────────────
# Keyboard ergonomics. Rebuild: python dictionary.py (theory-2 refresh) → exports;
#          pickles stay valid (weights are not serialized anywhere). Also prices the
#          (currently commented-out) layout solve — see src/cpsatsolver.py.
[keyboard]
layout_file = "starboard3h.json"   # the committed pre-optimized layout (S4 output)
multi_finger_discount = 0.85       # cost ×= discount ** (number of fingers used)

[keyboard.shape]                  # applied to onset/coda strokes only (thumbs have no columns)
zigzag_cost = 100                  # keys on different rows AND offset columns
gap_cost = 100                     # an empty row between the two keys
adjacent_triple_roll_bonus = -50   # 2,3,4-style three-key roll
spread_triple_penalty = 50         # 2,3,5 / 2,4,5 / 3,4,5-style spreads
quad_roll_bonus = -100             # 2,3,4,5-style four-key roll

[keyboard.finger_weights]          # cost tier per gesture (keys mirror FingerWeights fields)
noPress = 0
pinky1keyHome = 125
pinky1keyOffHome = 150
pinky2keysVertHome = 175
pinky2keysVertOffHome = 200
pinky2keysHorzBottom = 250
pinky2keysHorzTop = 275
pinky4keys = 325
ringMid1key = 125
ringMid2keys = 175
index1keyHome = 100
index1keyOffHome = 125
index2keysVert = 150
index2keysHorz = 175
index3keys = 200
thumb1key = 100
thumb2keys = 150

# Which key-combos each finger may press, and which tier prices them (insertion
# order matters: it orders getPossibleStrokes output — keep as listed).
[keyboard.finger_keypress_tiers.leftPinky]
"()" = "noPress"
"(0,)" = "pinky1keyOffHome"
"(1,)" = "pinky1keyOffHome"
"(2,)" = "pinky1keyHome"
"(3,)" = "pinky1keyHome"
"(0, 1)" = "pinky2keysVertOffHome"
"(2, 3)" = "pinky2keysVertHome"
"(0, 2)" = "pinky2keysHorzTop"
"(1, 3)" = "pinky2keysHorzBottom"
"(0,1,2,3)" = "pinky4keys"
[keyboard.finger_keypress_tiers.leftRing]
"()" = "noPress"
"(4,)" = "ringMid1key"
"(5,)" = "ringMid1key"
"(4,5)" = "ringMid2keys"
[keyboard.finger_keypress_tiers.leftMiddle]
"()" = "noPress"
"(6,)" = "ringMid1key"
"(7,)" = "ringMid1key"
"(6,7)" = "ringMid2keys"
[keyboard.finger_keypress_tiers.leftIndex]
"()" = "noPress"
"(8,)" = "index1keyHome"
"(9,)" = "index1keyHome"
"(10,)" = "index1keyOffHome"
"(8,9)" = "index2keysVert"
"(8,10)" = "index2keysHorz"
"(9,10)" = "index2keysHorz"
"(8,9,10)" = "index3keys"
[keyboard.finger_keypress_tiers.leftThumb]
"()" = "noPress"
"(11,)" = "thumb1key"
"(12,)" = "thumb1key"
"(11,12)" = "thumb2keys"
[keyboard.finger_keypress_tiers.rightThumb]
"()" = "noPress"
"(13,)" = "thumb1key"
"(14,)" = "thumb1key"
"(13,14)" = "thumb2keys"
[keyboard.finger_keypress_tiers.rightIndex]
"()" = "noPress"
"(15,)" = "index1keyOffHome"
"(16,)" = "index1keyHome"
"(17,)" = "index1keyHome"
"(16,17)" = "index2keysVert"
"(15,16)" = "index2keysHorz"
"(15,17)" = "index2keysHorz"
"(15,16,17)" = "index3keys"
[keyboard.finger_keypress_tiers.rightMiddle]
"()" = "noPress"
"(18,)" = "ringMid1key"
"(19,)" = "ringMid1key"
"(18,19)" = "ringMid2keys"
[keyboard.finger_keypress_tiers.rightRing]
"()" = "noPress"
"(20,)" = "ringMid1key"
"(21,)" = "ringMid1key"
"(20,21)" = "ringMid2keys"
[keyboard.finger_keypress_tiers.rightPinky]
"()" = "noPress"
"(22,)" = "pinky1keyHome"
"(23,)" = "pinky1keyHome"
"(24,)" = "pinky1keyOffHome"
"(25,)" = "pinky1keyOffHome"
"(22, 23)" = "pinky2keysVertHome"
"(24, 25)" = "pinky2keysVertOffHome"
"(22, 24)" = "pinky2keysHorzTop"
"(23, 25)" = "pinky2keysHorzBottom"
"(22,23,24,25)" = "pinky4keys"

# ─────────────────────────────────────────────────────────────────────────────
# CP-SAT solver knobs. The layout solve (S4) is currently commented out
# (dictionary.py:494) — the first six keys matter only when re-enabling it.
# The grouping time limit never changes results (an UNKNOWN status aborts loudly).
[solver]
stroke_assignment_penalty = 1      # base cost per stroke assignment
ambiguity_penalty = 30000          # weight of the syllabic-part ambiguity term
order_penalty = 500                # weight of the phoneme-order term
time_limit_s = 90.0                # layout solve, per syllabic part
log = false
max_multiphonemes = 2000           # ambiguity pairs entering the model
max_keys_per_stroke = 4            # legal chord size (range(1, N+1) in cpsatsolver)
grouping_time_limit_s = 30.0       # minKeypressesSat* timeLimitS (build_keypress_groups)
```

Notes on representation choices:
- `[tense_scope]` is a plain list of `"mode:tense"` code prefixes — the most compact form that
  all four sites can derive from (see §3). A structured `{mood=..., tense=...}` table was
  rejected: it duplicates what the `":"` split already encodes, and the code form is what both
  Lexique383 (`infover` column) and Verbiste template keys use.
- `[practice_sentences]` is a SEPARATE key (trainer scope is all-subjonctif + passé simple,
  deliberately not derivable from the theory's sub:imp-only scope).
- Marker/atom names in TOML (`"impératif"`, `pers_2`, `infinitif`...) use the elicitation
  vocabulary (docs/GLOSSARY.md), validated against `src/verbfeatures.KNOWN_FEATURE_ATOMS`.

---

## 2. Loader — `src/config.py` (new)

Shape:

```python
"""User preferences for the Stenalgo pipeline — typed loader for config.toml.

Module-level CONFIG is loaded once at import and is immutable. Every consumer keeps
its existing module-level constant names, now defined FROM CONFIG (see the per-file
change list). A malformed, missing, or unknown-key file raises ConfigError at import
with the file path and the offending key — the pipeline never runs on a bad config.
"""
import ast
import tomllib
from dataclasses import dataclass
from pathlib import Path

from src.verbfeatures import KNOWN_FEATURE_ATOMS, MODE_ATOMS, TENSE_ATOMS

class ConfigError(RuntimeError): ...

REPO_ROOT = Path(__file__).resolve().parent.parent      # cwd-independent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.toml"
```

Types (all `@dataclass(frozen=True)`):
- `TenseScope(out_of_scope_tag_prefixes: tuple[str, ...])` with methods:
  - `excludedFiniteSlotCodes() -> frozenset[str]` — the prefixes themselves;
  - `atomSets() -> tuple[frozenset[str], ...]` — `{MODE_ATOMS[m] , TENSE_ATOMS[t]}` per prefix
    (e.g. `{"subjonctif", "imparfait"}`);
  - `stripTags(infoVerb: str) -> str | None` — generalized `stripSubjonctifImparfait`
    (`kept = [t for t in infoVerb.split(";") if t and not t.startswith(prefixes)]`).
- `PracticeSentencesCfg(out_of_scope_tag_prefixes: tuple[str, ...])`
- `MarkersCfg(preferred_keys: dict[str, tuple[int, ...]])` (TOML document order preserved —
  `build_realization_report` iterates it for its console summary)
- `PreferenceTierSpec(kind: str, pairs: tuple[tuple[str, ...], ...] | None, group: tuple[str, ...] | None)`
- `GroupingCfg(alone_keys: frozenset[str], must_differ_groups: frozenset[frozenset[str]], preference_tiers: tuple[PreferenceTierSpec, ...])`
- `StarHashCfg(ratio_exemption_threshold: float, gramcat_priority: dict[str, int])`
- `FrequencyCfg(film_weight: float, book_weight: float)`
- `LexiconCfg(nb_frequent_words: int, frequent_words_file: str)`
- `Reform1990Cfg(lemmes, ortho, emprunt_pluriel, eler_eter, interpeler, absous_dissous: bool)`
- `ShapeCfg(zigzag_cost, gap_cost, adjacent_triple_roll_bonus, spread_triple_penalty, quad_roll_bonus: int)`
- `KeyboardCfg(layout_file: str, multi_finger_discount: float, shape: ShapeCfg,
  finger_weights: dict[str, int], finger_keypress_tiers: dict[str, dict[tuple[int, ...], str]])`
  (combo strings `"(0, 1)"` parsed with `ast.literal_eval` into `tuple[int, ...]`, order kept)
- `SolverCfg(stroke_assignment_penalty: int, ambiguity_penalty: int, order_penalty: int,
  time_limit_s: float, log: bool, max_multiphonemes: int, max_keys_per_stroke: int,
  grouping_time_limit_s: float)`
- `StenalgoConfig(...)` holding the ten sections above.

API:
- `loadConfig(path: str | Path = DEFAULT_CONFIG_PATH) -> StenalgoConfig` — pure, used by tests
  with tmp files.
- `CONFIG: StenalgoConfig = loadConfig()` at module bottom.

Validation (all inside `loadConfig`, all raising `ConfigError` with `path:section.key` context,
chaining `tomllib.TOMLDecodeError` for syntax errors):
- Strict schema: unknown top-level section or unknown key inside a known section → error
  listing the allowed keys (catches typos like `out_of_scopre`). Helper
  `_take(table, key, expected_type, where)` enforces presence + type.
- `tense_scope`: each prefix must split on `":"` into exactly 2 parts, mode in `MODE_ATOMS`,
  tense in `TENSE_ATOMS` (rejects `"subjonctif"`, `"sub:zz"`, `"sub:imp:1s"` with clear messages).
- `markers.preferred_keys`: keys in `KNOWN_FEATURE_ATOMS`; values are int lists, each int in
  the coda bank 16..25, non-empty.
- `grouping`: `alone_keys`/tier markers in `KNOWN_FEATURE_ATOMS`; tier `type` in
  `{"sameKey", "exclusiveGroup"}`; `sameKey` requires `pairs`, `exclusiveGroup` requires `group`.
- `star_hash.ratio_exemption_threshold`: positive float.
- `frequency`: non-negative weights, at least one strictly positive.
- `keyboard.finger_weights`: keys exactly the 17 tier names (`FINGER_WEIGHT_TIER_NAMES`
  constant in config.py — pinned to `FingerWeights`' fields by a unit test in
  src/test/config_test.py); values int.
- `keyboard.finger_keypress_tiers`: finger names exactly the 10 PositionWeights fingers;
  combo strings parse to sorted-unique tuples of ints in 0..25; every finger's table contains
  `"()"`→`"noPress"`; tier names exist in finger_weights.
- `keyboard.multi_finger_discount` in (0.0, 1.0].
- `solver`: penalties positive ints, `max_keys_per_stroke` in 2..10, time limits positive.
- `gramcat_priority` keys are NOT validated here (import cycle with `src.word`); validated at
  import of `src/greedyoptimizer.py` (see §3) and pinned by a unit test.

Deliberately NOT provided: env-var path override, layered configs, runtime mutation. The
singleton is the only consumption point; tests needing a different config call `loadConfig`
directly and pass values into the (parameterized) derivation functions.

## 2b. `src/verbfeatures.py` (new leaf module)

Extracted verbatim from `Word.splitInfoVerb` (word.py:102-127):

```python
"""Closed vocabulary: Lexique383/Verbiste verb-tag codes ↔ French feature atoms.
Leaf module (no src imports) — shared by Word.splitInfoVerb and src/config.py."""
MODE_ATOMS  = {"ind": "indicatif", "imp": "impératif", "sub": "subjonctif",
               "par": "participe", "cnd": "conditionnel"}          # insertion order = emit order
TENSE_ATOMS = {"pre": "présent", "pas": "passé", "imp": "imparfait", "fut": "future"}
KNOWN_FEATURE_ATOMS = frozenset(
    {"infinitif"} | set(MODE_ATOMS.values()) | set(TENSE_ATOMS.values())
    | {"pers_1", "pers_2", "pers_3", "nbr_s", "nbr_p"}             # verb person/number
    | {"m", "f", "s", "p", "VER"}                                   # gender/number/participle atoms
)
```

`Word.splitInfoVerb` keeps its `"inf"` early-return and its `participe` branch, but emits
mode/tense atoms by iterating `MODE_ATOMS`/`TENSE_ATOMS` in order (dict order reproduces the
current conditional-append order exactly — the emitted lists are identical; they feed
frozensets everywhere, but preserve order anyway). Needed because `src.word` will import
`src.config`, so `src.config` may not import `src.word`.

---

## 3. MARKING_OVERRIDES decision → `resources/markingOverrides.tsv` (TSV, not TOML)

Decision: move the 49-entry table (ambiguitychecker.py:129-179) to a TSV resource, NOT into
config.toml.

Justification:
- It is per-pair DATA, not a preference parameter: entries are individually sourced from a
  regret analysis ("built from a top-10-by-regret list ... 2026-09-20 ... not yet re-verified"),
  they grow/drift independently of the rule logic, and each deserves its own rationale note.
  TOML has no per-entry comment discipline that survives user edits; the repo already solved
  exactly this problem twice with note-carrying TSVs — `resources/lexiconExclusions.tsv`
  (replaced hardcoded lists 2026-09-18, `word reason note` columns) and
  `resources/reform1990.tsv` (8 columns incl. `note`, read by
  `loadReform1990DoubletPairs` ambiguitychecker.py:92-117 with comment-line + header handling).
- It keeps config.toml a readable parameter file rather than a 49-row dataset.
- File: `resources/markingOverrides.tsv`, header
  `orthoA\torthoB\tmarked\tnote`, `#` comment preamble carrying today's block comment
  (provisional per-pair overrides, design-session provenance), entries in today's dict order.
  Loader `loadMarkingOverrides(tsvPath: str = "resources/markingOverrides.tsv")` in
  ambiguitychecker.py, mirroring loadReform1990DoubletPairs's parse; validates
  `marked ∈ {orthoA, orthoB}` and rejects a pair listed twice with different targets.
  `MARKING_OVERRIDES: dict[frozenset[str], str] = loadMarkingOverrides()` keeps the name and
  module level (consumed at :218 by decideStarHashMark R3; referenced by tests via behavior).
  cwd-relative path, same convention as reform1990.tsv (documented "run from repo root").

---

## 4. Per-file change list (14 files)

Every change keeps the existing constant NAMES (use sites untouched); only definitions change.

1. **`src/config.py` (new)** — §2. **`src/verbfeatures.py` (new)** — §2b.
   **`config.toml` (new)** — §1. **`resources/markingOverrides.tsv` (new)** — §3.
2. **`src/word.py`**
   - :91-93: `self.frequency = self.frequencyFilm` → `self.frequency = (CONFIG.frequency.film_weight * self.frequencyFilm + CONFIG.frequency.book_weight * self.frequencyBook)`
     (add `from src.config import CONFIG` to imports). With 1.0/0.0 this is bit-identical:
     `1.0*x == x` and `x + 0.0*y == x` exactly for non-negative floats (frequencies are parsed
     from TSV, never negative). Keep the "Formula to be optimized..." comment, reworded to point
     at config.toml `[frequency]`.
   - :102-127 `splitInfoVerb`: emit via `MODE_ATOMS`/`TENSE_ATOMS` from `src/verbfeatures`
     (identical output lists; see §2b).
3. **`lexique.py`** (six flags + strip + doc citations)
   - :95 `APPLY_1990_REFORM_LEMMES: bool = CONFIG.reform1990.lemmes` (same for :145→`.ortho`,
     :326→`.emprunt_pluriel`, :420→`.eler_eter`, :505→`.interpeler`, :534→`.absous_dissous`);
     add `from src.config import CONFIG`; DELETE the stale "Off by default" comment blocks
     (the TOML now states the value and the sourcing); keep the mechanical/architecture notes
     that are still true.
   - :1154-1172: delete `Lexique.stripSubjonctifImparfait`; call site :1185 becomes
     `infoVerbOut = CONFIG.tense_scope.stripTags(word.info_verb)`. Copy the docstring content
     (2026-09-21 rationale) into config.toml's `[tense_scope]` comment (done in §1) and fix the
     stale "see ROADMAP.md" citation → docs/PIPELINE.md S1.9.2 + docs/specs/discriminating-features.md.
4. **`src/verbparadigm.py`** :397-403 — split structural vs scope:
   ```python
   # Structural exclusions (own generation paths): inf is an invariant single form;
   # participles go through the dedicated gender/number path.
   _STRUCTURAL_FINITE_SLOT_EXCLUDED_CODES = frozenset({"inf", "par:pre", "par:pas"})
   FINITE_SLOT_EXCLUDED_CODES = _STRUCTURAL_FINITE_SLOT_EXCLUDED_CODES | CONFIG.tense_scope.excludedFiniteSlotCodes()
   ```
   (`excludedFiniteSlotCodes()` returns `frozenset(("sub:imp",))` today; the membership check at
   :417 is unchanged). Fix the comment's ROADMAP.md reference (→ docs/PIPELINE.md, docs/specs/
   discriminating-features.md); keep the 2026-09-21 date.
5. **`src/elicitation.py`** :55-59 —
   ```python
   from src.config import CONFIG
   OUT_OF_SCOPE_ATOM_SETS: tuple[frozenset[str], ...] = CONFIG.tense_scope.atomSets()
   ...
   def wordFeatureCombinations(word: Word, _outOfScope: tuple[frozenset[str], ...] = OUT_OF_SCOPE_ATOM_SETS) -> ...:
       ...
       combinations_ = [c for c in combinations_ if not any(s <= c for s in _outOfScope)]
   ```
   With one atom set this is exactly `not ({"subjonctif","imparfait"} <= c)`; the added default
   parameter keeps every existing call/test compatible and makes non-default scopes testable.
   Keep the 2026-09-19 dated comment, reworded to name config.toml as the source.
6. **`util/export_practice_sentences.py`** :45 —
   `OUT_OF_SCOPE_TAG_PREFIXES = CONFIG.practice_sentences.out_of_scope_tag_prefixes`
   (tuple; `str.startswith` accepts a tuple — :77 unchanged). Docstring: mention the trainer-only,
   broader scope and its separate config key.
7. **`src/ambiguitychecker.py`**
   - :89 `RATIO_EXEMPTION_THRESHOLD = CONFIG.star_hash.ratio_exemption_threshold`
   - :129-179 `MARKING_OVERRIDES = loadMarkingOverrides()` (§3); delete the literal + block
     comment (moved to the TSV preamble).
   - :776-780 `PREFERRED_KEYS_BY_MARKER = dict(CONFIG.markers.preferred_keys)` — keep the
     2026-09-22 dated comment (the substantive half lives in config.toml).
   - :1180 CLI block: `Starboard.fromJSONFile(CONFIG.keyboard.layout_file)` (error message string
     interpolated with the configured name).
8. **`src/greedyoptimizer.py`** :14-21 —
   ```python
   GRAMCAT_PRIORITY = dict(CONFIG.star_hash.gramcat_priority)
   _unknown = set(GRAMCAT_PRIORITY) - {c.name for c in GramCat}     # fail loudly on typos
   if _unknown: raise ConfigError(f"config.toml [star_hash.gramcat_priority]: unknown GramCat names {_unknown}")
   ```
   (adds `from src.word import GramCat` — no cycle: word does not import greedyoptimizer).
   Keep the fitting-rationale comment; point at config.toml.
9. **`util/build_keypress_groups.py`** :41-47 —
   ```python
   ALONE_KEYS = CONFIG.grouping.alone_keys
   MUST_DIFFER_GROUPS = CONFIG.grouping.must_differ_groups
   PREFERENCE_TIERS = [tierFromSpec(spec) for spec in CONFIG.grouping.preference_tiers]
   ```
   with a local `tierFromSpec` building `SameKeyPreference(frozenset(map(frozenset, spec.pairs)))`
   / `ExclusiveGroupPreference(frozenset(spec.group))` (dataclasses stay in featuregroupingsat;
   config must not import ortools). Call `minKeypressesSatWithPriorities(...,
   timeLimitS=CONFIG.solver.grouping_time_limit_s)` explicitly. Serialization path untouched →
   keypress_groups.json byte-identical.
10. **`src/keyboard.py`**
    - `FingerWeights` → `@dataclass(frozen=True)` with the SAME 17 attribute names, each
      defaulted from `CONFIG.keyboard.finger_weights[name]` (class body runs after
      `from src.config import CONFIG`): `FingerWeights()` keeps working and now reflects the
      config (tests at keyboard_test.py:31-49 validate the committed values' orderings).
    - `Starboard._fw = FingerWeights()` unchanged; `Starboard._possibleKeypress` literal
      (:326-366) replaced by `_possibleKeypress = _positionWeightsFromConfig(FingerWeights())`
      — module function parsing `CONFIG.keyboard.finger_keypress_tiers` (ast.literal_eval combo
      keys, `getattr(fw, tierName)` values, document order preserved).
    - Module constants `ZIGZAG_COST, GAP_COST, ADJACENT_TRIPLE_ROLL_BONUS,
      SPREAD_TRIPLE_PENALTY, QUAD_ROLL_BONUS, MULTI_FINGER_DISCOUNT` from CONFIG; used by
      `_strokeZigZagCost`, `_strokeGapCost`, `getStrokeShapeCost`, and :569's
      `int(cost * MULTI_FINGER_DISCOUNT ** len(fingerInUse))`. The `syllabicPart in
      ["onset","coda"]` condition (:567) stays in code (thumb bank has no column geometry —
      structural).
11. **`src/cpsatsolver.py`** :25-30, :68 — hoist the six locals to module level from
    `CONFIG.solver.*`; `range(1, 5)` → `range(1, CONFIG.solver.max_keys_per_stroke + 1)`.
12. **`src/featuregroupingsat.py`** — NO signature changes; defaults `timeLimitS=30.0` stay
    (API compat for tests); the CLI passes the config value explicitly (see 9).
13. **`dictionary.py`**
    - :64 `nbFrequentWords: int = CONFIG.lexicon.nb_frequent_words`; :71
      `frequentWordsFile: str = CONFIG.lexicon.frequent_words_file`.
    - :623 `keyboardJSON = CONFIG.keyboard.layout_file`.
14. **Layout filename plumbing (config key `[keyboard] layout_file`)** — replace the literal in
    the remaining 5 sites: util/build_realization_report.py:46 (+ error message :48),
    util/export_plover_dictionary.py:32, util/export_plover_system.py:16,
    util/export_keyboard_layout.py:25, util/export_practice_words.py:50,
    util/completeVerbParadigms.py:64.
15. **`util/build_realization_report.py`** — no code change beyond the layout filename (it
    imports `PREFERRED_KEYS_BY_MARKER` by name; that now resolves to config-derived data).

Explicitly NOT changed: trainer knobs in export_practice_sentences/export_practice_words
(DEFAULT_LIMIT, CONTEXT_MOOD_PRIORITY, PRONOUNS, H_ASPIRE_LEMMAS, MOODS), reserved keys,
`nbKeysPerSyllabicPart`, `maxKeysPerPhoneme`, finger wiring (`_fingerAssignments`), phoneme
inventories, GramCat enum, the reform exception sub-tables, `check_conjugation_disambiguation_order.py`'s
parse quirk (deferred — see §7).

---

## 5. Tests

New `src/test/config_test.py` (≈15 tests):
1. `test_committed_config_parses_and_matches_defaults` — `loadConfig()` succeeds; spot-check
   `tense_scope == ("sub:imp",)`, `ratio_exemption_threshold == 10.0`, finger weight values,
   `layout_file == "starboard3h.json"`.
2. `test_missing_file_raises` / `test_malformed_toml_raises` (ConfigError names the path;
   wraps TOMLDecodeError line info).
3. `test_unknown_section_raises`, `test_unknown_key_raises` (typo detection).
4. `test_tense_scope_prefix_validation` — `"subjonctif"`, `"sub:zz"`, `"imp"`, `"sub:imp:1s"`
   all rejected with distinct messages.
5. `test_tense_scope_atom_derivation` — `atomSets() == (frozenset({"subjonctif","imparfait"}),)`.
6. `test_tense_scope_strip_tags` — `"sub:imp:1s;sub:pre:3s;"` → `"sub:pre:3s;"`;
   `"sub:imp:1s;"` → `None`; `""` → `""`.
7. `test_excluded_finite_slot_codes_union` — verbparadigm's `FINITE_SLOT_EXCLUDED_CODES ==
   {"inf","par:pre","par:pas","sub:imp"}`.
8. `test_gramcat_priority_names_are_valid` — `set(GRAMCAT_PRIORITY) <= {c.name for c in GramCat}`
   (guards the committed file; the runtime check lives in greedyoptimizer).
9. `test_marker_names_in_known_vocabulary` — markers/grouping keys ⊆ `KNOWN_FEATURE_ATOMS`.
10. `test_preferred_keys_in_coda_bank` — ints within 16..25.
11. `test_finger_tables_reference_known_tiers_and_fingers` (via loadConfig on the committed file).
12. `test_finger_weights_fields_match_config_names` — `dataclasses.fields(FingerWeights)` names
    == `config.FINGER_WEIGHT_TIER_NAMES` (pins the config↔keyboard contract).
13. `test_position_weights_golden_order_and_content` — build from the committed config and
    compare per-finger key order and values against the previous literal, hardcoded in the test
    (order matters: `list(pw.leftPinky.keys()) == [(), (0,), (1,), (2,), (3,), (0,1), (2,3), (0,2), (1,3), (0,1,2,3)]`, etc.).
14. `test_frequency_formula_film_only_is_bitwise_film` — `Word(..., frequencyFilm=3.5,
    frequencyBook=9.2).frequency == 3.5` (and a case with film=0: `0.0`).
15. `test_wordfeaturecombinations_custom_scope` — a synthetic atom set drops
    subjonctif-présent combinations while keeping indicatif ones (exercises the new default param).

Existing coverage that doubles as behavior-preservation proof: elicitation_test.py:64,72
(subjonctif-imparfait scope), keyboard_test.py FingerWeights/PositionWeights classes,
ambiguitychecker_test.py:185-188 (MARKING_OVERRIDES via decideStarHashMark, now reading the TSV).
All 522 existing tests must pass unchanged (except none need edits — names preserved).

Plus: `mypy src/` clean (config.py, verbfeatures.py included).

## 5b. Byte-identical rebuild verification (exact commands)

Baseline BEFORE any change (fresh, to eliminate doubt about on-disk artifacts — realization
report residual lists depend on pickle hashes, docs/PIPELINE.md fact 3):

```bash
cd /home/jfsp/stenalgo
git status --porcelain                # confirm clean tree first
python lexique.py                     # S1: proves today's rerun is byte-identical (PIPELINE.md S1)
md5sum resources/LexiqueMixte.tsv resources/LexiqueSynthetic.tsv > /tmp/stenalgo-baseline.md5
rm -f Dictionary.pickle FirstTheory.pickle
PYTHONHASHSEED=0 python dictionary.py # full orchestrated chain (S2-S8), seed inherited by children
md5sum theory.tsv theory2.tsv resolved_press_sets.json keypress_groups.json \
      realization_report.json plover_stenalgo_dictionary.json \
      plover_stenalgo/plover_stenalgo/_generated_keys.py \
      steno-trainer/public/data/keyboard-layout.json \
      steno-trainer/public/data/practice-words.json \
      steno-trainer/public/data/practice-sentences.json \
      steno-trainer/public/data/definitions.json >> /tmp/stenalgo-baseline.md5
```

After EACH behavior-touching commit (see §6) repeat the same block and
`md5sum -c /tmp/stenalgo-baseline.md5` — every line must say OK. Also run
`git status --porcelain` after the rebuild: NO tracked file may show a diff (LexiqueMixte.tsv,
LexiqueSynthetic.tsv, keypress_groups.json, realization_report.json,
plover_stenalgo_dictionary.json, _generated_keys.py, trainer data are tracked).
`pytest src/test/` and `mypy src/` after every commit.

Cheap intermediate check for commit C (pickles still valid — skip the rm):
`PYTHONHASHSEED=0 python dictionary.py` alone reuses the pickles, reruns theory 2 + exports.

## 5c. Rebuild implications per config section (for TOML comments — done in §1 — and docs)

| Section | Pipeline effect | Rebuild after a change |
|---|---|---|
| tense_scope | S1 row drop, S2 appender gating, S6 elicitation filter | `python lexique.py`; `rm -f *.pickle`; `python dictionary.py` (full); step-4h loop if new oppositions |
| practice_sentences | S8 sentence gate only | `python -m util.export_practice_sentences` |
| markers | S6 Realization key choice | `python dictionary.py` (fast, pickles reusable) + exports |
| grouping | S6 keypress groups | `python -m util.build_keypress_groups` → `python dictionary.py` → exports |
| star_hash | S7 marking | `python dictionary.py` (fast) + exports |
| frequency | Word.frequency inside Dictionary.pickle | `rm -f *.pickle` MANDATORY → `python dictionary.py` → exports |
| lexicon | S3 frequent words | `rm -f *.pickle` → `python dictionary.py` → exports |
| reform1990 | S1 orthography | `python lexique.py` → `rm -f *.pickle` → `python dictionary.py` → exports |
| keyboard weights/shape/discount | realization cost ranking (+ commented-out S4) | `python dictionary.py` (fast) + exports; no pickle rebuild |
| keyboard.layout_file | S5 layout load — a layout change | `rm -f *.pickle` → `python dictionary.py` → exports |
| solver | S4 solve (commented out) + grouping wall-time | only when S4 re-enabled; grouping limit never changes results |

---

## 6. Step ordering (recommended: 4 commits, 2 full rebuild cycles)

Recommended over all-at-once (localizes any md5 mismatch to one commit) and over
one-commit-per-group (each full rebuild is expensive; S1/S3-affecting groups are batched).

- **Commit A — infrastructure, zero behavior change.** Add `src/verbfeatures.py`,
  `src/config.py`, `config.toml`, `resources/markingOverrides.tsv` (data copied verbatim —
  MARKING_OVERRIDES literal still live, unused file for now), `src/test/config_test.py`
  (minus tests referencing consumers). `word.py`'s splitInfoVerb refactor onto verbfeatures
  tables (identical output). Verify: `pytest src/test/`, `mypy src/`. No rebuild needed.
- **Commit B — S1/S3-scoped consumers (the risky half).** lexique.py (flags + stripTags),
  verbparadigm split, elicitation filter, word.py frequency, dictionary.py lexicon defaults.
  Verify: `python lexique.py` → `git diff --stat resources/LexiqueMixte.tsv` EMPTY (proves
  tense-scope + reform extraction byte-preserving at S1 on its own); then the full baseline
  block (§5b) + md5 compare of every artifact.
- **Commit C — S6/S7/S8-scoped consumers (fast verify).** ambiguitychecker (RATIO,
  PREFERRED_KEYS, MARKING_OVERRIDES→TSV), greedyoptimizer, build_keypress_groups,
  keyboard.py ergonomics, cpsatsolver, dictionary.py + 6 util layout-file sites,
  export_practice_sentences. Delete the now-dead `MARKING_OVERRIDES` literal. Verify: pickles
  from commit B still valid — `PYTHONHASHSEED=0 python dictionary.py` + md5 compare (all of
  §5b's outputs; keypress_groups.json requires the grouping rerun inside the orchestrated run —
  run the orchestrated `python dictionary.py`, it reuses the pickles).
- **Commit D — docs.** CLAUDE.md (§7), docs/PIPELINE.md §Configuration + flag-citation updates,
  stale ROADMAP.md comment fixes (verbparadigm.py:399-400, lexique.py:1159-1160 — already
  handled in B, sweep any leftovers), final `pytest` + `mypy`.

Rollback safety: every commit leaves the tree runnable; config.toml with committed values
always reproduces committed outputs.

## 7. Documentation updates (commit D)

- **CLAUDE.md**: new subsection under "Architecture" (or after "Commands"): "User preferences
  (`config.toml`)" — one paragraph: what lives there, that src/config.py fails loudly at import,
  that changing it changes tracked artifacts per docs/PIPELINE.md's rebuild table, and the
  pickle warning for [frequency]/[lexicon]. Add a "Pitfalls" sentence: preference values are
  read once at import; Word.frequency lives inside Dictionary.pickle.
- **docs/PIPELINE.md**: new "## Configuration (config.toml)" section after "How to run a full
  rebuild": the §5c table, the loader contract (strict schema, ConfigError at import,
  module-level CONFIG), and notes: "All five APPLY_1990_REFORM_* flags are True" → "the six
  reform switches live in config.toml [reform1990]"; S1.9.2 / S6.Elicitation.2 / S2.1.3 /
  S8.8 scope citations gain "(config.toml [tense_scope] / [practice_sentences])".
- **Stale-comment sweep**: verbparadigm.py:399-400 and lexique.py:1159-1160 ROADMAP.md →
  docs/PIPELINE.md + docs/specs/discriminating-features.md (done in commit B); delete the six
  "Off by default" reform-flag comment blocks (done in B).
- Memory-of-staged-risks: the CLAUDE.md pitfalls bullet above is the durable home; no
  ROADMAP.md change needed.

## 8. Drive-by candidate — DEFER

`util/check_conjugation_disambiguation_order.py:43-57`: the prose header line
"features to discriminate" is parsed as junk combination #47 because the skip rules only cover
"Exhaustive"/"$and" prefixes. Defer to a separate one-line commit AFTER this refactor: the
output (`conjugation_disambiguation_report.json`) is gitignored and diagnostic-only, precedence
is never enforced (PIPELINE.md S6.Elicitation.6), and junk atoms in the vocabulary can only
make the "unknown atoms" check more permissive — zero pipeline effect. Folding it in would add
an unverified behavior change to an otherwise md5-provable refactor. Fix when touched: skip
lines until the first blank line (the header block is exactly 3 prose lines + blank).

## 9. Risks and mitigations

- **Finger-table ordering** changes getPossibleStrokes order → golden order test (§5 test 13);
  TOML lists combos in the current literal order.
- **Float exactness** (frequency formula, 0.85 discount): arguments in §4.2/§4.10; test 14
  plus the md5 protocol catch any slip.
- **Import cycles**: config imports only stdlib + verbfeatures; greedyoptimizer imports word
  (no reverse edge); keyboard imports config (config never imports keyboard — tier-name
  contract pinned by test 12).
- **lexique.py module-level execution** makes its flags untestable in pytest — hence the flags
  only feed `loadConfig`-provided booleans and the strip logic lives on TenseScope (test 6).
- **Forgot-a-site risk** for layout_file: the 8 sites are enumerated in §0.7; commit C
  greps `starboard3h.json` after the change to confirm only config.toml and docs mention it.
