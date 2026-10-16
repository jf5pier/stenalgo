# Phonology rewrite — plan

Written 2026-10-15 from a design interview with the user (grill session). Read this file first in a fresh session;
vocabulary in `docs/GLOSSARY.md`, section "Phonology rewrite (optional and retired phonemes)" (**Optional phoneme**,
**Optional phoneme set**, **Retired phoneme**, **Residual word**, **Retired-phoneme keypress**, **Reduced phonology outline**,
**Retired-keypress outline**, **Keypress-group placeholder**, **Phonology override**, **Phoneme modifier**). Background
measurement: `docs/PHONEME_REMOVAL_EXPLORATION.md` (scripts in `scratch/optimisation_exploration/`). Architecture
decision: `docs/adr/0001-optionality-before-layout-solve.md`.

## Goal

Shorten Stenalgo's strokes (fewer phonemes per stroke) without giving up what it does better than Pluvier: no collisions,
phoneme order aligned with the keyboard, phonemes easy to learn, onset/nucleus/coda keys owned by fixed fingers.
The phonology given to the layout solve (S4) and to Phonetic Theory Building (S5) is rewritten so that some phoneme
occurrences are optional or retired; the CP-SAT then puts rarely typed phonemes on costlier chords. The output is a
candidate layout that the rest of the pipeline consumes unchanged.

Motivation (`theory_comparison.md`, run of 2026-10-13 21:19 with the affix abbreviations and the briefs, the 108,150 words both theories cover,
film frequency): Stenalgo short form costs 255.156 per word on its own keyboard against Pluvier's 253.186 (258.332 when Pluvier's colliding
words pay an extra stroke); Stenalgo has fewer strokes (1.166 against 1.220) but longer chords. An earlier version of this section quoted
271.70, from a run made before the briefs existed: stale. The headline target below is therefore already met; what remains is the stretch target.

Exploration facts behind the decisions (`scratch/optimisation_exploration/out/phoneme_information.md`, baseline 254.97/word):
- Schwa `°`: 3.78% cost drop if removed everywhere, only 0.21% once colliding spellings keep it, because the 10 kept
  spellings are *je, le, de, ce, te, se...* (105k per million): they collide with their elided forms. Phonology overrides recover that gap.
- `Z/onset`: 1.54% with 317 spellings kept; `Z` (both parts) 1.56% with 964; `Z/coda` alone only 0.02%. The `Z/onset` and `°`
  gains overlap (both come largely from *je*): gains of separate candidates do not add up.

## Decisions (settled, do not reopen)

| # | Decision |
|---|---|
| P1 | Terms as in the glossary section above. "Reduced form", "conflict-avoiding long form", "late keypress", "early brief" are avoided. |
| P2 | Iteration 1 = phonology overrides + optional phonemes + retired phonemes (+ `8` → `y` as a plain override). Phoneme modifiers (nasal `~` decomposition, `O`/`o` and `E`/`e` neutralized pairs, `w` → `u`) are iteration 2, designed together with the part-split search (P15). |
| P3 | **Phonology overrides**: one committed, hand-edited file (`resources/phonologyOverrides.tsv`), applied before the optionality search. Row kinds: `phonology` (spelling → new phonology: `je` `Z`, `te` `t`, `se` `s`, `le` `l`, `ce` `s`, `de` `d`, `me` `m`, `ne` `n`, `que` `k`; `8` → `y`) and `elided` (the elided form ranks below its base form). |
| P4 | Elided forms take the star/hash: a new S7 rule "an elided form ranks below its base form"; the remaining ties (`ce`/`se`/`c'`/`s'` all on `s-`, the whole four-code budget) go to the existing rule stack. `j'`, `c'`, `qu'` get base-dictionary outlines through it. The expression layer's elision pair (A') is unaffected and out of scope. |
| P5 | **Optional phoneme test**: decided on the full phonology of the current theory, after the current S6 Realization and S7, with the 7 keypress groups written as keypress-group placeholders (pseudo-phonemes, one symbol per group, e.g. `! $ % ? & ± £`). An occurrence is optional only when every combination of the word's optional phonemes gives a reduced phonology outline that conflicts neither with an existing outline nor with any outline another word gets by leaving out any combination of its own optional phonemes (optional phoneme set). Landing on an existing outline means the phoneme is not optional there: it must be written. Conflicts are symmetric: no frequency priority (the elision overrides are decided earlier, P3). |
| P6 | The optionality search covers only a few candidate phonemes at a time, chosen greedily from the highest-benefit rows of the exploration tools (improved as needed). |
| P7 | Both outlines are valid for an optional phoneme: the full one and every reduced phonology outline of its optional phoneme set. |
| P8 | **Retired phonemes** (per part: `Z/onset`, `Z/coda`) get no layout key; they are proposed by a recommendation system (in scope), never retired without the user's decision. |
| P9 | A residual word is written either with its **retired-keypress outline** or, without the phoneme, with a star/hash mark: the user's choice per retired phoneme. No scoring formula decides between them (the learning cost of a rare keypress vs of a new mark form is unknown); the report gives the metrics (P12). |
| P10 | **Retired-phoneme keypress**: at most one per retired phoneme and part, preferably one shared by several retired phonemes; any keys, other parts included; chosen last, after the theory, affix abbreviations, briefs and expression-layer chords have claimed their chords; it must add no collision. |
| P11 | **CP-SAT input**: the rewritten phonology plus the keypress-group placeholders (coda pseudo-phonemes, merged into the last stroke as merged feature keys are). Each phoneme is weighted by the frequency it is actually typed with (left-out optional occurrences and retired phonemes do not count). The solver also places the placeholders, so it sees absorbed feature keys (plural on the `-s` key) and can move group keys when coda phonemes move. The feature groupings themselves (7 groups, `keypress_groups.json`) are unchanged and out of scope. |
| P12 | **Decision report**, one Markdown file per greedy step, per candidate retired phoneme and part, both options side by side: residual words (count, frequency mass, top 30); whole-theory cost gain and the cost each option adds back; keypress option: chord, sharing, uses per million; mark option: new marks, how many merge vs need a bare mark stroke, four-code budget use; emergent rules: residual words grouped by GramCat, feature combination, lemma family and spelling ending, groups ≥ 20% of the residual frequency flagged. No semantic grouping (no resource). |
| P13 | **Decisions file**: committed, the `affix_decisions.json` pattern: per candidate `keypress` / `mark` / `reject`; undecided = PENDING = not retired (safe default). Only the user edits it; the tools never do. |
| P14 | **Greedy loop**, one step per run: (1) the fast simulation (exploration removal model, current layout, ~4 min for all rows) scores every remaining candidate; (2) the top 3 get a real CP-SAT solve + S5–S9e rebuild + `compare_theories` (~13 min each: CP-SAT ~5, rebuild ~7, comparison 40 s); (3) the P12 report; (4) the user decides (P13); (5) the next step rescores given the adopted decisions. Stop when the best real gain is below 0.1% of the cost or on the user's word. |
| P15 | Part split (`keyIDinSyllabicPart`: onset 2–9, nucleus 11–14, coda 16–25, reserved 0, 1, 10, 15): no automatic search in iteration 1; a hand-edited seed (e.g. key 9 `wNG` → coda) is evaluated as one more candidate. Automatic search: iteration 2, with the modifiers. |
| P16 | **Realization after the solve**: the layout JSON stores the CP-SAT's key per keypress group; on the rebuild the Realization Phase adopts it, checks it, and falls back to its own choice per group that leaves a residual collision; its report names the groups that fell back. Without stored group keys it behaves as today. |
| P17 | **Pipeline integration**: the recommender, the optionality search, the decision report and the new CP-SAT entry are hand-run tools (like `util.optimize_keyboard`). The orchestrator only reads committed inputs: the override file, the decisions file and the adopted `starboard3h.json`. The rewrite is applied when the phonetic theory is built, after the pickles load (`Dictionary.pickle` / `PhoneticTheory.pickle` are not staleness-checked), behind `STENALGO_PHONOLOGY_REWRITE` (default off: today's md5s unchanged); the flag and the md5s of the two committed files go into the `DisambiguatedTheory.pickle` fingerprint. |
| P18 | **Success** (restated 2026-10-15): the **shortest form built on the reduced form** (reduced outlines, then affix abbreviations and briefs regenerated) must beat the shortest form built on the long form: `compare_theories` short form, cost on its own keyboard, 255.156 today (run of 2026-10-13) vs Pluvier 253.186 (258.33 collision-penalized, 252.64 with `S` on the cheaper pinky). Target < 253.19. Hard constraint: 0 collisions in the final theory. Vocabulary: long / reduced / short / shortest form (GLOSSARY). Reduced-form-only scores (cheap route: 269.119 for `Z/onset,d/onset,°,E` vs long form 281.115) are screening numbers, not comparable to Pluvier's long form (276.012). Reported, not scored: strokes per word, phoneme-order violations, learnability counts (overrides, exceptions per rule, retired phonemes, residual words, new marks, new keypresses). |

## Out of scope

The context-aware `je`/`j'` choice in a plugin (A'); changing the feature groupings; semantic grouping of residual words;
phoneme modifiers and the automatic part-split search (iteration 2).

## Order of work (iteration 1)

1. Phonology override file + the S7 "elided ranks last" rule, behind the flag; verify the flag-off md5s against a baseline and
   measure the override gain alone with `compare_theories`.
2. Keypress-group placeholder phonology (current theory, after S7) and the optional phoneme set search on 1–3 candidates.
3. CP-SAT entry with typed-frequency weights and placeholders; layout JSON carries the group keys; Realization adopt/check/fallback (P16).
4. Retirement recommender: fast-simulation screen, residual words, both options priced, P12 report, P13 decisions file.
5. Retired-phoneme keypress selection after S9e and the expression layer (P10).
6. Greedy loop runs; adopt a layout only when P18 says it wins.

## Open items

**Review pass 2026-10-15: `docs/PHONOLOGY_REWRITE_BLIND_SPOTS.md`** (blind spots and missing questions, A1–D3). Settle A1
(the CP-SAT ignores the top-200 words), A2 (no resyllabification) and A3 (marks in the optionality test) before any code.

- How to price a new star/hash form against a rare new keypress in learning terms (P9): unknown; the report only gives the figures.
- Optional phoneme set search size: the combinations of other words' optional phonemes grow fast; the candidate cap (P6) is the lever.
