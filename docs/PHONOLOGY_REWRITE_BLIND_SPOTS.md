# Phonology rewrite — blind spots and missing questions

Written 2026-10-15: a review pass over `docs/PHONOLOGY_REWRITE_PLAN.md` (decisions PRP1–PRP18), checked against the code.
Each item gives the problem, the evidence, the question to put to the user, and a suggested default. Items are ordered by how much
of the plan they put at risk: section A can invalidate a premise of the plan, B is a decision the plan is missing, C is about
measuring, D is about everything downstream.

## Settled 2026-10-15 (user answers)

- **PRA1.** Only the words that later get a brief are left out of the layout solve: a brief chord is not phonetic and is re-assigned after any
  new layout. Measured on `briefs.tsv` against the first 200 words of `resources/top500_film.txt`: **34 of the 200 spellings are briefed**
  (avec, ici, était, alors, jamais, pourquoi, toujours, maintenant, merci, comment, beaucoup, après, bonjour...), about **6.9% of the top-200
  frequency mass**. The other 166 (je, de, est, pas, la, tu, le, vous, ne, il, et, à, un, ça, les, on, une, pour, des, en, qui, ce, mais...)
  are typed with their phonetic outlines and must weigh in the solve, at their typed outline's phonemes (so after the PRP3 overrides).
  Next: replace the `nbFrequentWords` cut (dictionary.py:79) by "briefed spellings excluded", and measure that change alone
  (re-solve, `compare_theories`) before any other change.
- **PRA2.** (revised) No resyllabification in the rewrite: a syllable left without nucleus stays an onset-only stroke. Merging it into the next
  syllable's onset is a later optimisation, applied downstream in the pipeline (a post-pass that merges strokes when the result is a legal chord
  and causes no collision); it is not part of the optionality test or the CP-SAT input.
- **PRA3.** The optionality test outline includes the word's current star/hash mark (fixed, from the current S7); a reduced outline whose
  mark changes after the rebuild is rechecked.
- **PRA5.** Briefs and the expression rule set are not targeted by the phonology and layout optimisation; they are regenerated (`--rederive`, rule
  review) after a new layout is chosen. Candidates are therefore measured without briefs (the metric "with and without briefs" is only reported
  for the adopted layout), and adopting a layout lists the brief and expression review as a follow-up step.
- **PRB1/PRB12.** The optional phoneme sets live in a committed file (the `affix_decisions.json` pattern), revalidated on every build (an invalid set is
  dropped with a warning naming the rederive command). The rewrite is applied in memory on top of the loaded phonetic theory and never pickled, so
  `PhoneticTheory.pickle` always holds the plain theory; the flag and the file md5s go into the `DisambiguatedTheory.pickle` fingerprint.
- **PRA4.** No noise sampling: it is a poor fit for CP-SAT exploration. Measured 2026-10-15 (30 min per part, 16 cores, start from `starboard3h.json`):
  nucleus OPTIMAL in 25 s; onset FEASIBLE, objective -16,900,917 against a proven bound of -24,721,421 (gap about 47%), only 0.08% better than the
  committed layout; coda FEASIBLE, 10,365,099 against 9,614,883 (gap 7%), no improvement on the committed layout. So the 90 s limit is not the
  obstacle: the onset and coda are hard to prove optimal. Strategy instead: keep the number of CP-SAT solves to a strict minimum, and run each to
  completion on a much more powerful separate machine (192 cores). All the selection work is a pre-analysis (the fast simulation, brought to the
  PRP5 semantics, PRC3) that ranks candidate phonologies by guessed effect on the theory cost; only the top 3 get a full solve. This replaces PRP14 step 2
  ("real CP-SAT solve ~5 min each") and the noise-floor idea.

## A. Premises at risk

<!-- tag: PRA1 | The layout solve weighs the frequent words except the briefed spellings (the top-200 cut weighed them all 0). -->
### PRA1. The CP-SAT ignores the most frequent words (64.4% of running text)
- **Problem.** `Dictionary.analyseSyllabification` (dictionary.py:209-210) sets a word's frequency to 0 in the syllable and phoneme
  statistics when it is one of the `nbFrequentWords = 200` first words of `resources/top500_film.txt`. Those statistics are the CP-SAT's
  phoneme weights (`Syllable.phonemeColByPart[...].frequency`, src/cpsatsolver.py) and the ambiguity tables. The 200 words make up
  **64.4%** of the film frequency (measured on the file). *je, de, le, te, se, ce, que, me, ne* are all among them.
- **Consequence.** The phonology overrides (PRP3) would not change the schwa's weight in the solve at all: *je* and the others already weigh 0.
  The typed-frequency weighting (PRP11) leaves out two thirds of what the success metric (PRP18) measures, because the metric
  weights every word by its full frequency.
- **Question.** Should the layout solve weigh the frequent words? If so, with full weight, or with their typed (reduced or brief) outline's
  phonemes? Why were they excluded in the first place (because they were expected to get briefs)?
- **Suggested default.** First measure the change on its own: re-solve with the frequent words included and nothing else changed, and compare
  with `compare_theories`. Then weight each frequent word by the phonemes of the outline it is actually typed with. A briefed word adds
  nothing to the phoneme weights, because its brief chord is not phonetic.

<!-- tag: PRA2 | No resyllabification: a syllable left without a nucleus stays an onset-only stroke; merging strokes is a later downstream post-pass. -->
### PRA2. Leaving out a vowel never merges syllables
- **Problem.** The exploration's removal model (`removed()` in `scratch/optimisation_exploration/optexp_phoneme_information.py`) keeps
  every syllable. A syllable whose schwa is removed becomes an onset-only stroke, and the stroke count only drops when a syllable becomes completely empty
  (`wordsEmptied`). Pluvier's schwa gain is mostly *fewer strokes*: *fenêtre* is the one stroke `WHAEUTS`, not `f`/`nEtR`.
  The plan never says what happens to a vowel-less syllable.
- **Question.** When an optional or retired vowel leaves a syllable without a nucleus, does it (a) stay an onset-only stroke, (b) join the
  next syllable's onset (`p°.ti` → `pti`, when the cluster is legal and in key order), or (c) join the previous syllable's coda?
  And is that resyllabification part of the reduced phonology outline that the conflict test checks?
- **Suggested default.** (b) when the merged onset is a legal chord in phoneme order, otherwise (a). Measure both variants: the stroke saving
  is the main reason to drop the schwa.

<!-- tag: PRA3 | The optionality test includes the word's current star/hash mark; a reduction that moves the mark is rechecked. -->
### PRA3. The optionality test cannot work for homophones unless marks are included
- **Problem.** PRP5 rules that conflicts are symmetric and checked on phonology + placeholders. Lemma-homophones (*mer/mère/maire*) already
  share that phonology, so their reduced phonology outlines are identical by construction and each blocks the others. No member of a
  homophone group (6,602 groups still collide at S6, before marks) could ever have an optional phoneme. In Q11 the user said the
  intermediate phonology is conflict-free "if the `*`/`#` are also included", but PRP5 does not state it.
- **Question.** Is the test outline = reduced phonology + placeholders + the word's current star/hash mark (from S7 on the full theory)?
  If a reduction later changes the S7 mark decisions, is the test rerun?
- **Suggested default.** Yes: marks are included as fixed keys taken from the current S7. After the rebuild, a reduced phonology outline whose
  mark changed is checked again.

<!-- tag: PRA4 | No noise sampling: few CP-SAT solves, each run to convergence on the 192-core machine, only for the top candidates of a fast pre-analysis. -->
### PRA4. The solver's objective is not the success metric, and the solve has noise
- **Problem.** The CP-SAT scores each part on its own: `getStrokeCost` per part × phoneme frequency, plus an ambiguity penalty and an order penalty.
  The metric is the frequency-weighted `getChordCost` of whole outlines, with the multi-finger discount `0.85^fingers` and Lexique383 film frequency,
  over the 108,150 words both theories cover. A better solver objective need not mean a better metric. The solve is also limited to 90 s per part
  and starts from the committed layout as a hint, so the solver cannot prove optimality and two runs can differ.
- **Question.** What is the noise floor? Should a candidate be compared with the committed layout, or with a re-solve of the **unchanged**
  phonology under the same solver settings?
- **Suggested default.** Before any candidate, re-solve the unchanged input 3 times and take the spread of the metric as the noise floor.
  Compare candidates with that re-solve, not with the committed layout. Raise PRP14's 0.1% stop threshold if it falls below the noise.

<!-- tag: PRA5 | Briefs and the expression rule set are regenerated after a layout is chosen; candidates are measured without them. -->
### PRA5. Committed hand decisions are tied to the layout
- **Problem.** `briefs.json` pins chords (`avec` → `v-k`). The expression rule set `scratch/expr-rules-final.json` stores physical keys
  (`de` → `[17, 24]`, `je` → `[4, 17, 24]`). In its default mode, the brief build leaves an invalid pin out with a warning; only
  `--rederive` moves a pin. Under a new layout, many pins and attach chords become illegal, taken, or simply no longer the best choice.
  The candidate rebuild in PRP14 (S5–S9e, default mode) would then measure a candidate that has lost some of its briefs: an unfair comparison,
  skewed differently for each candidate.
- **Question.** For each candidate evaluation, should briefs be re-derived (in a temporary copy) and the expression rule set rebuilt? What does
  adopting a layout cost the user (reviewing the brief and expression chords again)?
- **Suggested default.** Re-derive briefs in a temporary copy for every confirmed candidate. Measure the metric with and without briefs. Adopting a
  layout includes a brief and expression-rule review step, listed in the plan.

## B. Missing decisions

<!-- tag: PRB1 | The optional-phoneme sets live in a committed file, revalidated each build; an invalid set is dropped with a warning naming the rederive command. -->
### PRB1. Where the optional phoneme sets live, and how they are rechecked
PRP17 lists three pipeline inputs: the overrides, the decisions file and the layout. The optional phoneme sets come from a hand-run search on the
pre-rewrite theory, so the pipeline cannot recompute them without circularity. They need a committed file. Every build must also recheck them,
the way brief pins are validated: a word added by the Synthetic Lexicon Building (S2) or a lexicon fix can land on a reduced phonology outline.
*Default:* a committed optional-sets file; each build validates it and drops an invalid set with a warning naming the command that rederives it.
The file's md5 goes into the fingerprint (see PRB12).

<!-- tag: PRB2 | The same decisions file records the user's optional approval per phoneme and part; sets are derived for approved phonemes only. -->
### PRB2. Who approves optional-eligible phonemes
The decisions file (PRP13) covers retirement only. Nothing records the user's approval of a phoneme as optional-eligible (PRP6), or of the sets.
*Default:* the same decisions file, with an `optional` verdict per phoneme and part. Sets are derived for approved phonemes only.

<!-- tag: PRB3 | A global override row kind: per-part phoneme rewrites applied before the per-spelling rows, with their own collision check. -->
### PRB3. Rewrites that apply to every word
`8` → `y` (PRP2) applies everywhere, but the override file's row kinds (PRP3) are per spelling. *Default:* a third row kind, `global`: a phoneme
rewrite per part, applied before the per-spelling rows. It needs its own collision check, because it changes many words at once (*lui*, *huit*).

<!-- tag: PRB4 | A phoneme written in an override row is pinned: retirement and the optionality search never remove it. -->
### PRB4. Overrides against retirement and optionality
*je* is overridden to `Z`. Retiring `Z/onset` would leave *je* empty, so *je* becomes a residual word. *Default:* a phoneme written in an override row
is pinned: retirement and the optionality search never remove it.

<!-- tag: PRB5 | The retired-phoneme keypress is a provisional token chosen at the end; inside the stroke when legal for every residual word, else its own stroke. -->
### PRB5. When the retired-phoneme keypress exists, and how it is pressed
- Residual words' outlines are part of the theory that affix abbreviations, briefs and the expression layer are built on, yet PRP10 chooses the keypress
  **after** them. Either a provisional token goes through S5–S9 and is replaced at the end (with a final collision check), or the keypress is
  chosen before S9 from chords those stages can't use.
- PRP10 does not say whether the keypress is pressed **inside** the syllable's stroke (it must then form a legal chord with that syllable's other keys:
  pinky diagonals, `KeyConflicts`) or as a stroke of its own. "Any keys, other parts included" also breaks two of Stenalgo's strengths: fixed finger
  ownership of onset, nucleus and coda, and phoneme order.
- *Default:* a provisional token, chosen at the end. Inside the stroke when legal for every residual word, otherwise its own stroke. The report shows
  how many words fall into each case.

<!-- tag: PRB6 | Residual words rank last for the star/hash mark; when the group is full the word falls back to the retired-keypress outline. -->
### PRB6. The mark option: who takes the mark, and what happens when the budget is full
Under the star/hash option for residual words (PRP9), S7's rule stack may give the mark to the frequent **non**-residual word, which moves the cost to
the word that matters most. A group can also overflow the four-code budget. *Default:* a "residual word ranks last" rule, like the elided rule (PRP4).
When the group is full, that word falls back to the retired-keypress outline, and the report counts these cases.

<!-- tag: PRB7 | The test model reproduces merge eligibility per tense, and the merge ladder gets a level: a full outline beats a reduced outline. -->
### PRB7. Merged feature keys in the test model
PRP5 and PRP11 model the placeholders as merged into the last stroke. Passé simple and subjonctif never merge, and the words that lose on the merge precedence
ladder keep a separate feature discriminating stroke (`docs/MERGED_FEATURE_KEYS_PLAN.md`, MKD5 and MKD7). The ladder also has no rule for a reduced
phonology outline that meets a merged outline. *Default:* the test model reproduces merge eligibility per tense (placeholders in their own stroke for
the tenses that never merge). The ladder gets a level: a full outline beats a reduced phonology outline, so a reduction never takes an outline away.

<!-- tag: PRB8 | The Grouping Phase constraints must hold in the solve; placeholders are hinted from the current Realization keys; the multiphoneme statistics are recomputed on the reduced phonology. -->
### PRB8. Placeholder constraints and the CP-SAT's size
- The Grouping Phase's constraints must hold in the solve: `mustDifferGroups` (infinitif, pers_1, pers_2, pers_3) and `aloneKeys` (`f`), from
  `keypress_groups.json`.
- The placeholders have no hint. *Default:* the current Realization keys (`realization_report.json` `chosenKeys`).
- `MAX_MULTIPHONEMES = 2000` keeps only the most ambiguous multiphoneme pairs. Coda multiphonemes combined with placeholder combinations multiply,
  so truncation may silently drop the pairs that matter. The ambiguity statistics (`analyseMultiphonemeLexicalAmbiguity_serial`) must be recomputed
  on the reduced phonology + placeholders, and their run time is not measured.
- *Default:* measure the count of coda multiphoneme pairs and the statistics' run time before choosing the cap.

<!-- tag: PRB9 | The phoneme-order matrix is built from the typed phonology, the same one that sets the weights. -->
### PRB9. The phoneme-order input
The order penalty uses the biphoneme order matrix built from the full phonology. Dropped phonemes change which pairs are adjacent.
*Default:* build the matrix from the typed phonology, the same one that sets the weights.

<!-- tag: PRB10 | Report the metric for both short and full forms; the solve weights stay on the typed form; flag gains that depend on per-word knowledge. -->
### PRB10. Typed form against what learners actually type
Weighting by "the frequency it is actually typed with" (PRP11) and the short-form metric both assume the typist always uses the shortest valid
outline. A learner types the full form for a long time, and per-word optionality is hard to remember (PRC1). *Default:* report the metric for both
forms (short and full). The solve weights stay on the typed form, but the report flags phonemes whose gain depends on per-word knowledge.

<!-- tag: PRB11 | Ship the full outline and the fully reduced one; partial combinations are only checked for conflicts. -->
### PRB11. The number of outlines per word
An optional phoneme set of 6 gives up to 64 outlines per word, multiplied over 167k words. That swells the Plover dictionary, adds expression-decoder
readings, and grows the trainer's accepted outlines. *Default:* ship the full outline plus the fully reduced one. Partial combinations are only checked
for conflicts (so the definition still holds) unless the user wants them shipped.

<!-- tag: PRB12 | The rewrite is applied on top of the loaded phonetic theory, never pickled; the flag and the file md5s enter the fingerprints. -->
### PRB12. The fingerprint and the PhoneticTheory pickle
PRP17 says the rewrite is applied "when the phonetic theory is built, after the pickles load". But `PhoneticTheory.pickle` *is* the output of
`buildPhoneticTheory`, and it is not checked for staleness, so a pickle built with the flag off would be reused with the flag on.
*Default:* apply the rewrite on top of the loaded phonetic theory (never pickled), or fingerprint `PhoneticTheory.pickle` with the flag and the
md5s of the override, decision and optional-sets files.

<!-- tag: PRB13 | A spelling's outlines are the union over its readings; a collision with another reading of the same spelling is no conflict. -->
### PRB13. Readings and spelling twins
Optionality is computed per Word (reading); collisions are counted per spelling. Two readings of one spelling (a self-homograph), or the two spellings
of a 1990-reform doublet, can end up with different optional sets. *Default:* a spelling's outlines are the union over its readings. A reduction that
collides only with another reading of the same spelling is no conflict.

<!-- tag: PRB14 | Every greedy step rechecks the adopted optional sets against the new theory. -->
### PRB14. Rechecking adopted decisions after a layout change
The test is meant to be independent of the layout, but marks (PRA3) and merge eligibility (PRB7) come from the current theory. After a layout is adopted,
the next greedy step runs on the new theory, and earlier optional sets may no longer pass. *Default:* every greedy step starts by rechecking the
adopted sets (PRB1's validation).

<!-- tag: PRB15 | Retirements that only pay together are noted for iteration 2; in iteration 1 the user may add a hand-made combined candidate. -->
### PRB15. Retirements that only pay together
Greedy, one candidate at a time (PRP14), misses pairs that only pay off together: retiring `w`, `N` and `G` frees key 9 for another part, and that only
pays once all three are gone. *Default:* note it for iteration 2 (modifiers and part splits). In iteration 1, the user may add a hand-made
combined candidate.

## C. Measurement

<!-- tag: PRC1 | Report per-phoneme rule coverage; "optional by rule" only above a coverage threshold, else per-word knowledge. -->
### PRC1. Per-word optionality is not a rule a typist can learn
Pluvier's schwa rule is learnable: the schwa is never written. PRP5 decides optionality per word through a collision search, so "may I leave out the schwa
in *petit*?" has no rule-based answer. The cost metric assumes the typist knows the best outline of every word, so it overstates the practical gain,
against the stated goal of learnability. *Default:* the report gives, per phoneme and part, the **rule coverage**: the share of occurrences, by
frequency, that are optional, plus the number of exceptions. A phoneme is offered as "optional by rule, with N listed exceptions" only above a coverage
threshold (for example 90%). Below it, the gain is reported as per-word knowledge.

<!-- tag: PRC2 | One frequency source everywhere: Lexique383 film frequency, as in compare_theories. -->
### PRC2. Three different frequency sources
Collision mass uses `Word.frequency`. In the code that is the **film** frequency only (src/word.py:96), although
`docs/PHONEME_REMOVAL_EXPLORATION.md` says "books + films". Cost uses Lexique383 films. The CP-SAT uses film frequency minus the top-200 words (PRA1).
*Default:* use one source everywhere (Lexique383 film frequency, as in `compare_theories`), and fix the exploration doc's statement.

<!-- tag: PRC3 | Bring the screening model to the PRP5 semantics (symmetric, every combination, marks and placeholders) before the first greedy step. -->
### PRC3. The screen measures a different model
The exploration's "conflicts kept" model reverts a colliding spelling to its full phoneme, iterated to a fixed point. PRP5 is stricter: symmetric, every
combination, marks and placeholders included. The screening ranks (PRP14 step 1) will therefore overestimate gains, and not uniformly.
*Default:* bring the screen to PRP5's semantics before the first greedy step, and keep the old "kept" column for comparison.

<!-- tag: PRC4 | Reduced outlines give way to every shipped chord; boundary risks are counted, not a hard constraint, in iteration 1. -->
### PRC4. What the collision constraint covers
PRP18's hard constraint covers the theory, affixes and briefs. The shipped dictionaries also hold punctuation, commands, the number chords, spelling
(`export_plover_spelling` raises on any collision), the expression attach chords and the attach-merge chords. And a reduced phonology outline that loses
a stroke can equal the **first stroke** of another word's longer outline: a word-boundary risk that the brief generator already checks for
(`src/briefs.py`, "boundary risk") but the theory does not. *Default:* reduced phonology outlines give way to every shipped chord (as merged feature keys
do, `MERGED_FEATURE_KEYS_PLAN.md` MKD8). The report counts new boundary risks, which are not a hard constraint in iteration 1.

<!-- tag: PRC5 | Export the reduced outlines as alternate entries; also report the metric over all Stenalgo words. -->
### PRC5. The metric's word universe
`compare_theories` uses only the 108,150 words both theories cover, and it reads the reduced phonology outlines only if they are exported into
`plover_stenalgo_dictionary.json`. *Default:* export them as alternate entries (PRB11), and also report the metric over all Stenalgo words
(the exploration's 254.97 universe).

## D. Downstream impact not in the plan

<!-- tag: PRD1 | Trainer: iteration 1 only needs the new outlines accepted in drills (tagged reduced); new lessons come once a layout is adopted. -->
### PRD1. The trainer
The lessons teach every phoneme on its key, and the drills accept a word's outlines. Retired phonemes, optional phonemes, phonology overrides
(*je* = `vt-`) and retired-keypress outlines all need lesson content. Nothing in the plan covers the trainer. *Default:* in iteration 1 the trainer
only needs the new outlines accepted in drills (they are already tagged long, merged and affix; add `reduced`). New lessons come once a layout is adopted.

<!-- tag: PRD2 | Expression layer: rebuild the expression data and run the decode round trip as part of step 1's check. -->
### PRD2. The expression layer and the elision pair
The elision pair (`src/elision.py`) writes *je*/*j'* with one attach chord and a selector. Its attach keys are independent of the base outline, but the
attach-merge chords and the decoder's ranking depend on the base outlines that PRP3 and PRP4 change. *Default:* rebuild the expression data and run the
decode round trip (`scratch/decode_roundtrip.py`) as part of step 1's check.

<!-- tag: PRD3 | Rebuild time and review size: an "adopting a layout" checklist (rebuild, rederive, review, md5s, plover_plugin_test) in the plan. -->
### PRD3. Rebuild time and the size of the user's review
Each adopted layout re-runs the whole orchestrator (~19 min, `pipeline_timings.log` 2026-10-13), plus brief re-derivation and expression-rule review (PRA5),
plus your decisions in the decision file. *Default:* the plan's order of work gets an "adopting a layout" checklist (rebuild, rederive, review, md5s,
`plover_plugin_test`).

## Suggested order to settle these

PRA1, PRA2 and PRA3 change what step 1 and step 2 measure, so settle them before writing code. PRA4's noise floor is needed before any candidate is compared.
PRA5, PRB1 and PRB12 shape the pipeline integration. The rest can be settled as each step reaches them.
