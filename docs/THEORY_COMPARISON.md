# Theory comparison tool (Stenalgo vs Pluvier) — reference

Hand-run diagnostic, outside `dictionary.py`. It compares two steno theories, each with its own keyboard, over one word universe and
one frequency list. Written 2026-10-10 to compare Stenalgo (Starboard, `starboard3h.json`) with Pluvier (Ireland layout); the pieces are
generic enough to take another theory (see "Reusing it"). Findings of the first runs: `docs/PLUVIER_COMPARISON_2026-10-10.md`.
Pipeline entry: `docs/PIPELINE.md`, section "Theory comparison with Pluvier".

## Run

```bash
P=/home/jfsp/Steno/Pluvier/resources
python -m util.compare_theories \
    --pluvier-dict $P/dicofr.json --pluvier-dict $P/dicofr-plural.json \
    --pluvier-dict $P/verbs.json  --pluvier-dict $P/tao_la_salle_simple.json \
    --pluvier-dup $P/dup.json \
    [--stenalgo-abbreviations affix_abbreviations.tsv] [--stenalgo-dict plover_stenalgo_dictionary.json] [--stenalgo-layout starboard3h.json] \
    [--lexicon resources/Lexique383.tsv] [--phoneme-keys resources/pluvierPhonemeKeys.tsv] \
    [--freq films|livres] [--out DIR]
```

`--pluvier-dict` is repeated, LOWEST priority first: a later file takes an outline from an earlier one (the TAO briefs go last, like the generator's
`append_tao`); `--pluvier-dup` is optional. **Do not load `dicofr.json` alone**: the generator leaves the most frequent words out of it (they are the TAO briefs),
and the first run, which did, understated Pluvier's coverage (72% of frequency instead of 94%). ~40 s with the four files, no pickle, deterministic (two runs, byte-identical output). Writes `theory_comparison.json` and `theory_comparison.md` in `--out`
(default the repo root: untracked, delete or move them) and prints the table. The header of the JSON records the md5 of every input (`inputs.pluvierDicts`, a list) and the
Pluvier git commit (clone at `/home/jfsp/Steno/Pluvier`, upstream https://github.com/Vermoot/Pluvier, commit `47ab823`, 2024-04-06).
The repo-root `dicofr.json` is an untracked variant that differs from the clone's: always pass the clone's file explicitly.

`--stenalgo-abbreviations` adds the **short form** of Stenalgo next to the long form (the dictionary alone): `loadAbbreviations` reads the `short` column of `affix_abbreviations.tsv`, `withAbbreviations`
gives each word its long and short outlines and `choose` takes the cheapest (fewest strokes, then Starboard cost). The report gets `stenalgoShort` {`strokesPerWord`, `complexity`, `abbreviatedWords`, `abbreviatedFrequencyShare`}
in `commonWords` and `fullCoverage`, and three rows in the markdown. The expression layer is not in it (phrases have no per-word outline).
Pluvier's two forms need no option: `longForm` (`src/theorycompare.py`) picks the LONGEST outline of each word (most strokes, then cheapest); `choose` already picks the briefest (the short form). Report key `pluvierLong` {`wordsWithSeveralOutlines`, `wordsWithDifferentLongAndShort`, `strokesPerWord`, `complexity` on Starboard / tall-`S` / Ireland}. Collisions are not recomputed for the long form.

## Code map

| File | Role |
|---|---|
| `util/compare_theories.py` | the command: loads both theories, prices them, assembles and renders the report (`compare`, `renderMarkdown`, `main`; `--stenalgo-abbreviations` = the short form) |
| `src/theorycompare.py` | the metrics, pure functions and small dataclasses (`Lexicon`, `TheoryView`, `buildLayeredView` / `loadPluvierTheory` for the Pluvier layers, `coverage`, `lemmaCoverage`, `verbCoverageByTense`, `collisions`, `strokesPerWord`, `outlineCosts`, `complexity`, `markedForResolution`, `strokesPerWordResolved`, `costsResolved`, order-violation helpers, `PluvierEncoder`) |
| `src/irelandkeyboard.py` | `IrelandKeyboard`: Ireland chord parsing (`parseChord`, `renderChord`) and a cost model in the Starboard currency |
| `src/keyboard.py` `Starboard.getChordCost` | additive method: cost of a whole chord with no syllabic part (below) |
| `resources/pluvierPhonemeKeys.tsv` | Pluvier phoneme -> Ireland keys per syllabic part (`part phonemes keys source`), copied from the Pluvier clone; rows marked `added` are this repo's |
| `src/test/irelandkeyboard_test.py`, `theorycompare_test.py`, `compare_theories_test.py` | 32 tests: tiny hand-built theories with asserted numbers, the Ireland cost against `FingerWeights`, `getChordCost` against `getStrokeCost`, a smoke run on fixture files |
| `scratch/compare_top_words.py`, `scratch/compare_s_key_gap.py` | the two follow-up diagnostics of the first findings (top-N word comparison; the `S`-key price gap) |

Reused, unchanged: `util/export_plover_complements.py` (`convertStroke`, `starboardKeys`, `GEMINI`), `plover_stenalgo/plover_stenalgo/stroke.py`
(`parseStroke` for Stenalgo outlines), `Starboard.getStrokeCost` / `getStrokeShapeCost`, `FingerWeights`, `Starboard._possibleKeypress`.

## Definitions

- **Universe and frequency.** The Lexique383 spellings (lower-cased); frequency of a spelling = the SUM of its rows' `freqfilms2`
  (`--freq livres`: `freqlivres`). Every mean is frequency-weighted: `sum(x*f)/sum(f)`, with `math.fsum` over sorted words.
- **A theory** is `word -> outlines`; the word's outline is the CHOSEN one: fewest strokes, ties by Starboard chord cost (unpriceable last),
  then by text. Stenalgo has one outline per word in practice; Pluvier averages two.
- **Coverage.** Spellings of the universe with at least one outline, per theory, both, each only, neither (count, count with frequency > 0,
  frequency share). Words that appear only in Pluvier's collision record (`dup.json`) lost every outline and count as not covered
  (reported as `wordsOnlyInCollisionRecord`).
- **Pluvier layers.** Each file is outline -> word. `buildLayeredView` applies them in order (a later layer takes an outline from an earlier one, the word that
  loses it becomes a claimant of that outline); the generator's `dup.json` (outline -> every word that claimed it while `dicofr.json` was generated) adds its words as claimants. A claimant with no outline left is
  LOST and counts as not covered (`wordsOnlyInCollisionRecord`, `coverage.lostToCollisionsOnly`). The layer order only decides who loses a contested outline: reversing `dicofr` and `verbs` moved the headline figures by about 1 point.
- **Collisions** (on the words covered by both). A word collides when its chosen outline is claimed by another word. Pluvier: the claimants are the owner, the words displaced by a higher layer and the words of `dup.json`. Stenalgo: measured, by
  grouping the dictionary entries by their parsed key ids (a duplicate JSON key or two spellings of one chord sequence would show).
- **Strokes per word.** Number of `/`-separated chords of the chosen outline.
- **Chord cost.** `Starboard.getChordCost(stroke)` (`None` = unpressable): the finger-table cost of every finger over ALL keys of the chord,
  plus the shape cost (`getStrokeShapeCost`) of the onset keys 2..9 and of the coda keys 16..25 taken separately, then `int(cost * 0.85 ** nbFingers)`.
  It equals `getStrokeCost(stroke, part)` for a stroke inside one part (tested). A word's cost is the sum over its chords. Three prices:
  - Stenalgo on Starboard: `getChordCost` of the parsed chords;
  - Pluvier on Starboard: each Ireland chord converted key to key with the Gemini mapping, then `getChordCost`;
  - Pluvier on Ireland: `IrelandKeyboard.getChordCost`.
  The unpriceable share (unpressable chords) is reported next to every mean; `pressableInBoth` repeats the Stenalgo and Pluvier-on-Starboard means over
  the words priceable in both.
- **Ireland model** (`src/irelandkeyboard.py`, assumptions in its docstring). Each Ireland key sits on the Starboard key of the same finger
  and row (`S=2 T=4 K=5 P=6 W=7 H=8 R=9 *=10|15 A=11 O=12 E=13 U=14 -F=16 ... -Z=25`), so the same finger tables and shape terms apply. `S` is a tall key priced as TWO possible keys (top 2, bottom 3), the cheaper choice kept, shape terms included; `*` is a tall key outside the shape ranges (as on the Starboard) and goes to the left index unless only the right index is free;
  three keys of a pinky
  (or a diagonal pinky pair) are priced as `pinky4keys` (illegal on Starboard, physically fine on Ireland). The finger assignment is the standard one and was checked against `Starboard._fingerAssignments` and the Gemini conversion (`scratch/validate_ireland_fingers.py`; same finger and row for all 22 keys), not against an ergonomic study; the number bar is ignored (`dicofr.json` has no `#`).
- **Pluvier on the Starboard, tall `S`.** The Gemini mapping puts the Ireland `S` on the bottom pinky key 3, which charges zig-zag and gap terms the real
  key does not have. The report therefore also prices each converted chord with `S` on the cheaper of the pinky keys 2 and 3 (`pluvierOnStarboardTallS`), the fair Starboard price.
- **Collision-resolved metrics** (`withoutCollisions`). If the colliding words each took one more stroke: strokes per word + 1 and cost + the cheapest
  single-key chord of the keyboard (85 on both). Two rules, `winnerKeeps` (the most frequent claimant of an outline, ties alphabetical, keeps it; the others are marked)
  and `everyClaimant` (all, an upper bound). The keeper is chosen among all claimants, also those outside the compared words. A `*` mark instead of a stroke is not modelled.
- **Lemma coverage.** A lemma = (lemme, grammatical category) from Lexique383. Counted and weighted by lemma frequency:
  lemmas with at least one form covered (some form covered) and lemmas with every form covered (all forms covered).
  Code: `lemmaCoverage` src/theorycompare.py.
- **Verb coverage by mood and tense.** The 11 Lexique383 tense keys from VER and AUX rows' `infover` column:
  ind:pre, ind:imp, ind:pas, ind:fut, cnd:pre, sub:pre, sub:imp, imp:pre, inf, par:pre, par:pas. Per tense:
  the number of forms and the frequency share covered by each theory. Stenalgo covers almost no subjonctif imparfait by design.
  Code: `verbCoverageByTense`, `tenseKeys` src/theorycompare.py.
- **Phoneme order.** Per syllable (Lexique383 `syll` of the spelling's most frequent row), consecutive phonemes whose exclusive keys (shared keys dropped) are not
  left to right are a violation. Reported: share of words with at least one, mean violations per word, share not encodable (a phoneme missing from the table).
  Stenalgo keys: `getStrokesOfPhoneme(...)[0]` of the layout (the ideal encoding of the phonology, not the shipped outline). Pluvier keys: `pluvierPhonemeKeys.tsv`, a per-syllable encoding
  (diphthongs, then pairs, then single phonemes). Pluvier's real generator (`src/steno_encoding.py` `CHUNKS`) has whole-syllable exceptions that are NOT reproduced: the table
  encoding equals a shipped outline for only 2.77% of words (34.4% of frequency, four layers), so the Pluvier order figure is an approximation. The report prints that validity share.

## Report layout

**Markdown** (`theory_comparison.md`): tables with Stenalgo and Pluvier columns side by side; short form and long form rows paired (short first); `—` = does not apply, `0` = real zero; coverage cells read "count (freq share)". Sections in order: word coverage, lemma coverage, verb coverage by mood and tense, then on words covered by both: collisions, strokes and cost (headline row: cost on its own keyboard, Stenalgo on Starboard and Pluvier on Ireland; then both on Starboard; the tall-`S` variant as a footnote), one-more-stroke resolution, phoneme order. One "how to read" sentence per section.

**JSON** (`theory_comparison.json`): `inputs` (paths, md5; `pluvierDicts` with the commit of each file's clone) · `theories` (notes per theory: entries, duplicate keys, unparsable outlines, apostrophe forms, one-letter words,
`wordsOnlyInCollisionRecord`; Pluvier also `layerEntries` and `outlinesTakenByAnotherLayer`) · `coverage` · `lemmaCoverage` · `verbCoverageByTense` · `collisionsOnCommonWords` · `commonWords` and `fullCoverage` (the same block for the common words and for each theory's whole coverage):
`strokesPerWord`, `complexity` {`stenalgoOnStarboard`, `pluvierOnStarboard`, `pluvierOnStarboardTallS`, `pluvierOnIreland`, `pressableInBoth`}, `phonemeOrder`,
`withoutCollisions` {`extraStrokeCost`, `winnerKeeps`, `everyClaimant`, each with `markedWords`, `strokesPerWord`, `complexity`}, `stenalgoShort`, `pluvierLong` (its `withoutCollisions.<rule>` has `costOnStarboard` and `costOnIreland`) · `pluvierEncodingMatchesDicofr` (the key keeps its first name; it compares the table encoding with the word's outlines in ANY Pluvier layer).

## Reusing it

- **Another theory or layout.** Build a `TheoryView` (`buildStenalgoView` for outline -> word dictionaries with a parser to key ids, `buildPluvierView` for the dicofr + collision record shape),
  provide a stroke-cost function (`CostFn = Callable[[str], int | None]`) and call the metric functions; they never read files. A new keyboard needs a model with a
  `getChordCost`-style function in the same currency, as `IrelandKeyboard` does.
- **Another frequency.** `--freq livres`, or any `Lexicon` (`freq`, `syll` dicts).
- **Another Pluvier snapshot or file set.** Pass its files in priority order (and `dup.json`); check `pluvierEncodingMatchesDicofr` and the apostrophe/one-letter counts, and update the commit note in `resources/pluvierPhonemeKeys.tsv` if the tables are re-copied.
- **A Starboard layout change.** Re-run; nothing is cached. `getChordCost` reads only the class-level finger tables.

## Not done / ideas

- The CP-SAT score of each theory+layout (the report is a dict of named metrics so a `cpsatScore` can be added; the fixed-seed scoring trick of the 2026-10-10 optimisation runs, `cpsat_fixed`, evaluates a given layout under the model).
- A `*`-on-the-last-chord resolution instead of an extra stroke.
- The 11,526 spellings that lost every Pluvier outline given an extra stroke (they would raise Pluvier's coverage and change its averages).
- Pluvier's `CHUNKS` exceptions in the phoneme encoding (or decoding the shipped outlines back to phonemes) for a valid Pluvier order metric.
- A `--top N` option on the command line (the top-N comparison lives in `scratch/compare_top_words.py`).
