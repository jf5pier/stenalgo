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
| PRP1 | Terms as in the glossary section above. "Reduced form", "conflict-avoiding long form", "late keypress", "early brief" are avoided. |
| PRP2 | Iteration 1 = phonology overrides + optional phonemes + retired phonemes (+ `8` → `y` as a plain override). Phoneme modifiers (nasal `~` decomposition, `O`/`o` and `E`/`e` neutralized pairs, `w` → `u`) are iteration 2, designed together with the part-split search (PRP15). |
| PRP3 | **Phonology overrides**: one committed, hand-edited file (`resources/phonologyOverrides.tsv`), applied before the optionality search. Row kinds: `phonology` (spelling → new phonology: `je` `Z`, `te` `t`, `se` `s`, `le` `l`, `ce` `s`, `de` `d`, `me` `m`, `ne` `n`, `que` `k`; `8` → `y`) and `elided` (the elided form ranks below its base form). |
| PRP4 | Elided forms take the star/hash: a new S7 rule "an elided form ranks below its base form"; the remaining ties (`ce`/`se`/`c'`/`s'` all on `s-`, the whole four-code budget) go to the existing rule stack. `j'`, `c'`, `qu'` get base-dictionary outlines through it. The expression layer's elision pair (A') is unaffected and out of scope. |
| PRP5 | **Optional phoneme test**: decided on the full phonology of the current theory, after the current S6 Realization and S7, with the 7 keypress groups written as keypress-group placeholders (pseudo-phonemes, one symbol per group, e.g. `! $ % ? & ± £`). An occurrence is optional only when every combination of the word's optional phonemes gives a reduced phonology outline that conflicts neither with an existing outline nor with any outline another word gets by leaving out any combination of its own optional phonemes (optional phoneme set). Landing on an existing outline means the phoneme is not optional there: it must be written. Conflicts are symmetric: no frequency priority (the elision overrides are decided earlier, PRP3). |
| PRP6 | The optionality search covers only a few candidate phonemes at a time, chosen greedily from the highest-benefit rows of the exploration tools (improved as needed). |
| PRP7 | Both outlines are valid for an optional phoneme: the full one and every reduced phonology outline of its optional phoneme set. |
| PRP8 | **Retired phonemes** (per part: `Z/onset`, `Z/coda`) get no layout key; they are proposed by a recommendation system (in scope), never retired without the user's decision. |
| PRP9 | A residual word is written either with its **retired-keypress outline** or, without the phoneme, with a star/hash mark: the user's choice per retired phoneme. No scoring formula decides between them (the learning cost of a rare keypress vs of a new mark form is unknown); the report gives the metrics (PRP12). |
| PRP10 | **Retired-phoneme keypress**: at most one per retired phoneme and part, preferably one shared by several retired phonemes; any keys, other parts included; chosen last, after the theory, affix abbreviations, briefs and expression-layer chords have claimed their chords; it must add no collision. |
| PRP11 | **CP-SAT input**: the rewritten phonology plus the keypress-group placeholders (coda pseudo-phonemes, merged into the last stroke as merged feature keys are). Each phoneme is weighted by the frequency it is actually typed with (left-out optional occurrences and retired phonemes do not count). The solver also places the placeholders, so it sees absorbed feature keys (plural on the `-s` key) and can move group keys when coda phonemes move. The feature groupings themselves (7 groups, `keypress_groups.json`) are unchanged and out of scope. |
| PRP12 | **Decision report**, one Markdown file per greedy step, per candidate retired phoneme and part, both options side by side: residual words (count, frequency mass, top 30); whole-theory cost gain and the cost each option adds back; keypress option: chord, sharing, uses per million; mark option: new marks, how many merge vs need a bare mark stroke, four-code budget use; emergent rules: residual words grouped by GramCat, feature combination, lemma family and spelling ending, groups ≥ 20% of the residual frequency flagged. No semantic grouping (no resource). |
| PRP13 | **Decisions file**: committed, the `affix_decisions.json` pattern: per candidate `keypress` / `mark` / `reject`; undecided = PENDING = not retired (safe default). Only the user edits it; the tools never do. |
| PRP14 | **Greedy loop**, one step per run: (1) the fast simulation (exploration removal model, current layout, ~4 min for all rows) scores every remaining candidate; (2) the top 3 get a real CP-SAT solve + S5–S9e rebuild + `compare_theories` (~13 min each: CP-SAT ~5, rebuild ~7, comparison 40 s); (3) the PRP12 report; (4) the user decides (PRP13); (5) the next step rescores given the adopted decisions. Stop when the best real gain is below 0.1% of the cost or on the user's word. |
| PRP15 | Part split (`keyIDinSyllabicPart`: onset 2–9, nucleus 11–14, coda 16–25, reserved 0, 1, 10, 15): no automatic search in iteration 1; a hand-edited seed (e.g. key 9 `wNG` → coda) is evaluated as one more candidate. Automatic search: iteration 2, with the modifiers. |
| PRP16 | **Realization after the solve**: the layout JSON stores the CP-SAT's key per keypress group; on the rebuild the Realization Phase adopts it, checks it, and falls back to its own choice per group that leaves a residual collision; its report names the groups that fell back. Without stored group keys it behaves as today. |
| PRP17 | **Pipeline integration**: the recommender, the optionality search, the decision report and the new CP-SAT entry are hand-run tools (like `util.optimize_keyboard`). The orchestrator only reads committed inputs: the override file, the decisions file and the adopted `starboard3h.json`. The rewrite is applied when the phonetic theory is built, after the pickles load (`Dictionary.pickle` / `PhoneticTheory.pickle` are not staleness-checked), behind `STENALGO_PHONOLOGY_REWRITE` (default off: today's md5s unchanged); the flag and the md5s of the two committed files go into the `DisambiguatedTheory.pickle` fingerprint. |
| PRP18 | **Success** (restated 2026-10-15): the **shortest form built on the reduced form** (reduced outlines, then affix abbreviations and briefs regenerated) must beat the shortest form built on the long form: `compare_theories` short form, cost on its own keyboard, 255.156 today (run of 2026-10-13) vs Pluvier 253.186 (258.33 collision-penalized, 252.64 with `S` on the cheaper pinky). Target < 253.19. Hard constraint: 0 collisions in the final theory. Vocabulary: long / reduced / short / shortest form (GLOSSARY). Reduced-form-only scores (cheap route: 269.119 for `Z/onset,d/onset,°,E` vs long form 281.115) are screening numbers, not comparable to Pluvier's long form (276.012). Reported, not scored: strokes per word, phoneme-order violations, learnability counts (overrides, exceptions per rule, retired phonemes, residual words, new marks, new keypresses). |
| PRP19 | **`ce`/`se`/`c'`/`s'` on `s`** (user ruling 2026-10-20): `ce` bare `s-`, `c'` star `s*`, `se` hash `s#`, `s'` star+hash `s*#`. Basis: `ce` is more frequent than `se` (film+books 13.4k vs 9.4k per million, film 7958 vs 2814); the elided forms follow, `c'` (the base `ce`'s elision) on the star, `s'` on both. All four codes used; the plain letter `c`, also on `s-`, goes to the existing rule stack. Instance of PRP4 for a shared base. |
<!-- tag: PRP1 | Vocabulary of the GLOSSARY phonology-rewrite section; "conflict-avoiding long form", "late keypress", "early brief" are avoided. -->
<!-- tag: PRP2 | Iteration 1 scope: phonology overrides + optional phonemes + retired phonemes (+ 8 -> y as a plain override); phoneme modifiers and the part-split search are iteration 2. -->
<!-- tag: PRP3 | Phonology overrides: one committed hand-edited TSV (phonology and elided row kinds), applied before the optionality search. -->
<!-- tag: PRP4 | Elided forms rank below their base form (a new S7 rule); remaining ties go to the existing rule stack; the expression layer's elision pair is out of scope. -->
<!-- tag: PRP5 | Optional phoneme test on the full phonology, after S6/S7, with keypress-group placeholders; an occurrence is optional only when every reduction combination is conflict-free, symmetrically. -->
<!-- tag: PRP6 | The optionality search covers a few candidate phonemes at a time, chosen greedily from the exploration tools' highest-benefit rows. -->
<!-- tag: PRP7 | Both outlines are valid for an optional phoneme: the full one and every reduced outline of its optional phoneme set. -->
<!-- tag: PRP8 | Retired phonemes (per part) get no layout key; they are proposed by a recommender, never retired without the user's decision. -->
<!-- tag: PRP9 | A residual word is written with a retired-keypress outline or, without the phoneme, with a star/hash mark: the user's per-phoneme choice, no scoring formula. -->
<!-- tag: PRP10 | Retired-phoneme keypress: at most one per retired phoneme and part, chosen last, must add no collision. -->
<!-- tag: PRP11 | CP-SAT input: the rewritten phonology plus the placeholders, each phoneme weighted by the frequency it is actually typed with; the solver also places the placeholders. -->
<!-- tag: PRP12 | Decision report, one Markdown file per greedy step: residual words, cost gain, both options priced, emergent rules; no semantic grouping. -->
<!-- tag: PRP13 | Decisions file (the affix_decisions.json pattern): keypress/mark/reject per candidate; undecided = PENDING = not retired; only the user edits it. -->
<!-- tag: PRP14 | Greedy loop: the fast simulation scores every candidate, the top 3 get a real solve + rebuild + comparison, the report, the user's decision, then a rescore. -->
<!-- tag: PRP15 | Part split: no automatic search in iteration 1; a hand-edited seed is evaluated as one more candidate; automatic search is iteration 2, with the modifiers. -->
<!-- tag: PRP16 | Realization after the solve: the layout stores the group keys; Realization adopts, checks, and falls back per group that leaves a residual collision. -->
<!-- tag: PRP17 | Pipeline integration: the new tools are hand-run; the orchestrator reads committed inputs; the rewrite applies at theory build behind STENALGO_PHONOLOGY_REWRITE (default off). -->
<!-- tag: PRP18 | Success (restated 2026-10-15): the shortest form built on the reduced form must beat the shortest form built on the long form (target < 253.19 vs Pluvier); 0 collisions hard constraint. -->
<!-- tag: PRP19 | ce s, c' s*, se s#, s' s*# (user ruling 2026-10-20); ce is more frequent than se; the letter c goes to the rule stack. -->

## Out of scope

The context-aware `je`/`j'` choice in a plugin (A'); changing the feature groupings; semantic grouping of residual words;
phoneme modifiers and the automatic part-split search (iteration 2).

## Order of work (iteration 1)

1. Phonology override file + the S7 "elided ranks last" rule, behind the flag; verify the flag-off md5s against a baseline and
   measure the override gain alone with `compare_theories`.
2. Keypress-group placeholder phonology (current theory, after S7) and the optional phoneme set search on 1–3 candidates.
3. CP-SAT entry with typed-frequency weights and placeholders; layout JSON carries the group keys; Realization adopt/check/fallback (PRP16).
4. Retirement recommender: fast-simulation screen, residual words, both options priced, PRP12 report, PRP13 decisions file.
5. Retired-phoneme keypress selection after S9e and the expression layer (PRP10).
6. Greedy loop runs; adopt a layout only when PRP18 says it wins.

## Open items

**Review pass 2026-10-15: `docs/PHONOLOGY_REWRITE_BLIND_SPOTS.md`** (blind spots and missing questions, PRA1–PRD3). Settle PRA1
(the CP-SAT ignores the top-200 words), PRA2 (no resyllabification) and PRA3 (marks in the optionality test) before any code.

- How to price a new star/hash form against a rare new keypress in learning terms (PRP9): unknown; the report only gives the figures.
- Optional phoneme set search size: the combinations of other words' optional phonemes grow fast; the candidate cap (PRP6) is the lever.
