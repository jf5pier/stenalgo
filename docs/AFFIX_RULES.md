# Affix abbreviation rules

Status: the analysis picks 30 rules (`scratch/affix-sweep-partial/D/affix-rules.tsv`, `affix-rules.json`, `affix-rules-report.md`) and
the committed `affix_rules.json` feeds an OPTIONAL abbreviation dictionary (`util/export_affix_dictionary.py`, see "The optional
abbreviation dictionary" below). Nothing in the phonetic theory, the disambiguated theory or the main Plover dictionary depends on it.

An **affix rule** puts a frequent affix syllable (`re-`, `-ment`, `-tion`...) on ONE dedicated keypress that is
merged into the neighbouring syllable's stroke, so a word such as `regarder` saves a stroke. The generator
finds the candidate rules, a budgeted selection keeps 30, and every rule gets the keypress that saves the most.
Vocabulary: [GLOSSARY.md](GLOSSARY.md) ("Affix ..." entries). Design history: `DESIGN_2026-09-27-affix-rule-selection.md`,
`PLAN_2026-09-28-affix-single-generator-rewrite.md`, the `RESUME_2026-09-*` notes.

## Code map

| Module | Role |
|---|---|
| `src/affixes.py` | word records, k=1 anchors, spelling-variant merges (fusions), the generic growth lattice, `simulate` (gain of a keypress binding on carriers, collisions cost marks) |
| `src/affixscopes.py` | THE DECIDED SCOPES: the 30 anchors' growth forms and the approved fusions (`SCOPES`, `APPROVED_FUSIONS`, `fusionVerdict`) |
| `src/affixrules.py` | rule = anchor + forms; exact keypress choice (`chooseRuleKeypress`), scope fallbacks (`resolveFallbacks`), rival resolution, budgeted selection (30 rules), key sharing |
| `src/affixabbrev.py` | the abbreviations themselves: per word the best allowed short outline, collision-free against the stable theory |
| `util/export_affix_dictionary.py` | writes `plover_stenalgo_affix_dictionary.json` and `affix_abbreviations.tsv` from `affix_rules.json` |
| `util/affix_scan.py` | the driver: Part A builds the pool, Part B selects and binds; `--sweep` runs the weight settings |

Tests: `src/test/affixes_test.py`, `affixrules_test.py`, `affixscopes_test.py`, `affixabbrev_test.py`.

## How a rule is built

1. **Anchor**: a k=1 candidate (position, spelling, phonology), for example suffix `ment` /m@/ with its carriers
   (the words ending in it). Spellings with the same sound can be **fused** into one anchor
   (`am|an|ant|em|en|...` /@/) that shares one key.
2. **Growth form**: the anchor fused with the NEIGHBOUR syllable (before a suffix, after a prefix) on the same
   stroke, k=2 (`·[C*[ai]]tion`: `-ation`, `-ition` on one stroke). The engine always keeps at least one stem syllable.
3. **Scope**: the condition that selects the growth form's carriers. Decided per anchor by the user (2026-09-30),
   as a pattern on the neighbour's SOUND (X-SAMPA), a few literals, or no growth. Written in `src/affixscopes.py`
   (`ScopeForm`: anchor spelling, neighbour sound regex, neighbour spelling regex, all must hold). Rank-1 `-ment` is the one
   spelling-based scope (`C{1,2}[eui]+`).
4. **Fallback**: a carrier a form names but that gains nothing under the rule's keys (collision, no legal chord)
   keeps the anchor alone. It is counted, and priced `EXCLUSION_COST` per word, so a scope that falls back often loses.
5. **Keypress**: `chooseRuleKeypress` tests every legal keypress on the pooled carriers (fallbacks resolved per
   key) and keeps the best score; a rule must keep its exception rate under `MAX_EXCEPTION_RATE`.
6. **Selection**: lazy greedy over the roots, each word credited once at its best rule, 30 rules; two rules may share
   a keypress when a joint simulation loses little (`bindKeypresses`).

Score of a rule = benefit (strokes saved x frequency) - `EXCEPTION_ALPHA` x exception frequency - `EXCLUSION_COST` x
(slot exclusions + fallbacks) - `FORM_COST` x (forms - 1). Sweep setting **D** is the user's decided values:
alpha 2, fallback price 5, form cost 100 (settings L, M, H are the older experiments).

## What is decided (the table lives in `src/affixscopes.py`)

- 30 anchors have an explicit entry: either a list of growth forms or `[]` (no growth: `re|reh`, `de|des|dé|déh`, `é`,
  `ter`, `pa`, `par`, `sa|sah`, `pro`, `ce`, `pou|pu`, `ger`, `cher`). Rationale and measurements per rank:
  `scratch/scope-decisions-2026-09-30.md`, `RESUME_2026-09-30-ment-regex-scope.md`.
- An anchor listed there does NOT grow through the generic lattice; its rule has exactly its listed forms.
  Anchors outside the table (low-ranked) still use the generic lattice.
- **Fusions** (user, 2026-10-01): a merged anchor containing a decided anchor is judged on the decided growth only, with the
  other spellings anchor-only (`scratch/fusion-check-2026-10-01.md`, `scratch/fusion_growth.py`).

  | Merged anchor | Decision |
  |---|---|
  | `am|an|ant|em|en|ench|enh|ham|han|hen` (`en` +2,648 words) | fused, approved growth `C{1,2}@` stays on `en` words |
  | `ner|nez|nner|nnée|née|nées` | fused, `né` growth stays on `né` words |
  | `der|dé|dée` | fused; the `gaR|m@` scope extended from `dez` to `dez|der|dé` (regarder, demander, regardé) |
  | `ccion|cion|cyon|sion|ssion|tion|tions` | fused, `C*[ai]` growth stays on `tion`/`tions` |
  | `é`, `au`+`o`, `ger`, `cher`, `ver`, `pa`, `ment` with their other spellings | no fusion (`fusionVerdict` = "apart") |

  A merged anchor that is itself one of the 30 (`re|reh`, `ain|hin|im|in`...) stays fused. Any other merge containing a decided
  anchor is dropped; merges without a decided part keep the engine's own rival test (`resolveVariantRivals`).

## Running it

```bash
# pool (Part A, ~30 s; rerun after ANY change to src/affixscopes.py, the lexicon or the layout)
PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python -m util.affix_scan --refresh --part a --partial-overlap
# selection + binding at the decided weights (Part B, ~25 min)
PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python -m util.affix_scan --part b --reuse-pool --sweep --partial-overlap --settings D
# outputs: scratch/affix-sweep-partial/D/affix-rules.tsv (+ fallbacks column) and affix-rules-report.md
```

`--partial-overlap` sets `src.affixes.RULE_PARTIAL_OVERLAP` (a rule merges unless ALL its keys are in the neighbouring stroke).
Pool pickles and `scratch/*-before/` snapshots are untracked (over 5 MB); never run `git clean -x`.

## Result of the D sweep (2026-10-01)

30 rules, total score 111,966, all of them decided anchors or approved fusions (`-ment` 8,503, `en` fusion 7,185, `re` 6,102,
`-tion` fusion 5,543, `é` 5,443...). Fallbacks are small (`-té` 76, `en` 34, `-ment` 32, `-tion` 14). No rule uses an
enumerated syllable list. The earlier (pre-fusion) combined simulation of the 30 scopes (`scratch/combined_scopes.py`) showed
key-sharing collisions (`en`/`é`, `i`/`cer...`) that the sweep's key re-selection removed.

## The optional abbreviation dictionary (usable output)

The theory is complete and stable without the affix rules, so the abbreviations are an OPTIONAL layer added after it
(user decision, 2026-10-01): nothing in S1-S8 changes if they are ignored, and the long outlines stay as the fallback for a
learner who does not remember the rules.

```bash
python -m util.export_affix_dictionary      # also the last step of `python dictionary.py`
# needs: the stable theory (as util.export_plover_dictionary), the committed affix_rules.json
# outputs: plover_stenalgo_affix_dictionary.json (short outline -> word), affix_abbreviations.tsv (long, short, saved, rule, k, freq)
```

- `affix_rules.json` (repo root, committed input like `starboard3h.json`) lists the 30 rules (rank, position, anchor spelling and
  phonology, keys). It is written by the sweep (`scratch/affix-sweep-partial/D/affix-rules.json`) and copied to the root by hand
  when a sweep is adopted. A lexicon or layout change means rerunning the affix scan first.
- `src/affixabbrev.py` builds the pool from the stable theory's records, takes each rule's carriers and forms, and computes the short
  outline with the rule's keys (`affixes._newBase`). Per word: one abbreviation, the one saving the most strokes (growth form, then
  anchor alone; a tie goes to the better-ranked rule).
- An abbreviation exists only if its outline equals no outline of the stable theory (all words, all readings) and no more frequent
  spelling's abbreviation. It keeps the word's own star/hash and feature marks, and never adds a mark, so it cannot disturb the theory.
  The exporter also fails if one collides with `plover_stenalgo_dictionary.json`.
- Result on the current lexicon: 59,358 abbreviations for 65,646 carrier words (51,119 save 1 stroke, 8,239 save 2); 83 carriers have
  no allowed form and 1,381 lost a shared outline to a more frequent spelling; strokes saved x frequency = 98,125 (the sweep's per-rule
  benefits add up to 115,682 because they count shared words once per rule and allow marks). The main dictionary is unchanged. Use it in
  Plover as a second dictionary of higher priority; remove it and nothing else changes.

## Pitfalls

- The engine keeps one stem syllable, so a word made of the anchor plus one syllable cannot fuse (`enfant`): the combined
  script counted 227 `en` words, the engine 214.
- Scope matching reads the CARRIER's syllables (`rec.orthoSylls`, `phonoSylls`); a word whose syllable counts differ
  between spelling and strokes is skipped.
- `SCOPES` is keyed by (position, spelling, phonology) of the pool's anchor, exactly as printed in the rules report; a typo
  silently leaves the anchor on the generic lattice (check with the pool's `isScoped` count: 23 scoped forms).
- Tests that exercise the generic lattice or the engine's rival test use the real `ment` key and clear the table with
  `monkeypatch.setattr("src.affixscopes.SCOPES", {})`.
- Unscoped low-ranked anchors may still reach the 30 when a decided rule drops out (an old `ra` rule did); check the
  report for roots that are not in the table.
