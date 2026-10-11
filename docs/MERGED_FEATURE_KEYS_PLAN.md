# Merged feature keys — plan

Written 2026-10-11 from a design interview with the user (grill session). Read this file first in a fresh session;
vocabulary in `docs/GLOSSARY.md` (**Merged feature keys**, **Merged outline**, **Absorbed feature key**,
**Merge precedence ladder**, **Merge-eligible tense**). Background measurement: `docs/CONJUGATION_FUSION_STATS.md`
(`python -m util.analyze_conjugation_fusion`, all groups, marks ignored).

## Goal

Whenever possible, a word's feature keys (the keys of its feature discriminating stroke) are pressed together with its
last phoneme stroke, saving one stroke. When the merged outline would conflict, the word keeps its current outline
(base strokes + feature discriminating stroke). The long outline always stays a valid alternate entry; the merged outline
is the primary one, in the main Plover dictionary and in the trainer.

Ceiling (measured 2026-10-11, film frequency over all 267,040 theory words): 13.0–15.2% of running words carry a feature
discriminating stroke today; the eligible tenses below are 10–13% of running words, the most a merge can save before
conflicts. The excluded tenses keep 1.5–2.7% of running words on the extra stroke.

## Decisions (settled, do not reopen)

| # | Decision |
|---|---|
| D1 | Terms: merged feature keys, merged outline, absorbed feature key (glossary). Avoid "conjugation fusion". |
| D2 | All 7 keypress groups can merge, gender (f) and number (p) included. |
| D3 | The long outline stays a valid alternate entry of every merged word. |
| D4 | Merged outline = primary outline in `plover_stenalgo_dictionary.json` and in the trainer (not a separate dictionary). |
| D5 | **Merge-eligible tenses**: présent, impératif, infinitif, participe, nominal (f/p). **Never merge**: future, passé simple, conditionnel, imparfait, subjonctif. Decided per entry from the tense of its reading, not from the keys it presses. |
| D6 | Every entry (alternate readings of self-homographs included, `dis` has 4) merges independently. |
| D7 | **Merge precedence ladder** for a merged outline meeting another outline: (1) phonetic first: the word for which the shared keys are sounds wins (`sec` beats `sais`, `livre` beats `livres`, `dites` beats `dis`); (2) features second: same base, same lemme+category, the word with an absorbed feature key loses (`fasse` beats `fassent`); (3) marks third: same base and same feature keys across lemmas/categories never block, star/hash marks separate them. Frequency does not decide. |
| D8 | A merge always gives way to the number chords, spelling chords, punctuation, commands and expression briefs (nothing shipped changes). |
| D9 | One feature = one physical key, merged or not, **except f and plural**: they may get a dedicated **merge key-set**, used only when merged; their feature discriminating stroke keeps 16 and 17. |
| D10 | No per-word chord-cost veto: an eligible entry merges whenever it wins the ladder and the merged stroke is pressable. |
| D11 | Keys 0 and 1 are not touched. The Grouping Phase (K=7, the user's elicitation answers) stays fixed. |
| D12 | Words whose BASE last stroke is already unpressable (~893, `-ismes`; TODO "unpressable base codas") are set aside: automatic fallback, reported apart, fixed later. |
| D13 | A reading's share of its spelling's frequency comes from a reading-share table (iteration 0); equal split until it exists. Never read the `frequencies` field of `resolved_press_sets.json` (bug B48). |
| D14 | Everything is simulated offline in an analysis script first; the pipeline is changed only for the chosen variant. |
| D15 | Haiku is the default worker (under 100k tokens per session); Sonnet writes code, takes judgement steps, prepares gates, and redoes a Haiku task whose result fails its acceptance check. The user decides at every gate. |

## Open questions answered by experiment

| Q | Alternatives | Iteration |
|---|---|---|
| Tie at ladder level (1) (`laisses` `mties`+d vs `laides` `mtied`+s) | (a) both fall back; (b) more frequent merges; (c) `GRAMCAT_PRIORITY` (src/greedyoptimizer.py, rule R6), then the precedence spec `conjugation_disambiguation_order.txt` (`parsePrecedenceOrder`, util/check_conjugation_disambiguation_order.py), then frequency | 3 |
| Merge before or after S7 (star/hash marks) | A: after, marks are part of the compared outlines (a mark can make room); B: before, compare unmarked outlines, S7 then marks the merged theory | 4 |
| f / plural merge key-sets | keep 16/17; dedicated merge key-sets (joint choice for f, p, f+p) | 5 |
| Re-search the other 5 groups' keys | only if residual conflicts justify it | 5c |
| Merge before or after S9 (affix abbreviations) | before: abbreviations rebuilt on the merged theory, they give way (`fais` beats the abbreviation of `happait`); after: merges avoid abbreviation outlines | 6 |

## Metrics (one table per iteration, same columns every time)

Frequency = Lexique383 `freqfilms2` (film), split over a spelling's entries with the reading-share table (D13).

Hard constraints (a variant violating one is rejected, not weighed):
- **H1** 0 collisions: no outline shared by two spellings across every shipped dictionary (theory with alternates and
  marks, numbers, spelling, punctuation, commands, Pluvier punctuation/numbers, expression briefs).
- **H2** 0 unpressable merged strokes (`Starboard.getStrokeCost(stroke, "coda") is None`), D12 words reported apart.
- **H3** number, spelling, punctuation, command and brief outputs unchanged.
- **H4** the same-lemmeGramCat invariant (docs/specs/discriminating-features.md §5) still holds.

Primary:
- **M1** frequency-weighted strokes per word over all theory words (primary outline of each entry); also the unweighted
  mean. Report the delta against today's theory.

Indicators:
- **M2** merge rate: merged / eligible entries needing a feature stroke, by count and by frequency; per keypress group and per tense.
- **M3** exceptions: eligible entries that fell back, with the reason (ladder level 1/2, tie, other dictionary,
  unpressable); how many among the 1,000 and 5,000 most frequent words (Lexique rank), and the top 30 by frequency.
- **M4** chord cost: frequency-weighted mean `getStrokeCost` of the merged last stroke vs (base last stroke + feature stroke).
- **M5** star/hash load: lemma-homophone groups, escalated codes, frequency-weighted mark keys typed.
- **M6** affix abbreviations: count and frequency-weighted strokes saved (iteration 6 on).
- **M7** `python -m util.compare_theories` summary against Pluvier (final iterations only; command in CLAUDE.md).

## Iterations

Each iteration ends with its metrics table appended under **Results** below and, when marked GATE, a question to the
user (AskUserQuestion); the answer is written under the iteration's result as "Gate decision". The winner of a gate is
fixed for every later iteration. Waiting on long jobs: on their log, never with `pgrep -f` (CLAUDE.md "Process rules").

### Iteration 0 — reading-share table [Haiku, Sonnet check]

Why: Lexique gives one frequency per spelling; a reading's share is unknown. The lexicon prior (frequency of the
unambiguous forms of each reading type) works for présent/imparfait/nominal but credits impératif with 0.02% of running
words (no imperative is unambiguous in Lexique: `dis`, `fais`, `regarde`), against 1.6–2.3% with an equal split.

- [ ] **0.1 [Haiku]** Download the French Universal Dependencies treebanks (GitHub `UniversalDependencies/UD_French-ParisStories`,
  `UD_French-Rhapsodie` (spoken), `UD_French-GSD`, `UD_French-Sequoia`) into a gitignored `ud-french/`. Write
  `util/build_reading_shares.py`: for every VERB/AUX/NOUN/ADJ token, map the UD features to Lexique's reading notation
  (Mood=Ind+Tense=Pres → `ind:pre`, Tense=Imp → `ind:imp`, Tense=Past → `ind:pas`, Tense=Fut → `ind:fut`; Mood=Sub →
  `sub:pre`/`sub:imp`; Mood=Cnd → `cnd:pre`; Mood=Imp → `imp:pre`; VerbForm=Inf → `inf`; VerbForm=Part → `par:pas`/`par:pre`;
  Person+Number → `1s`…; NOUN/ADJ Gender+Number → `nom:fs`…), look up the lowercased form's Lexique ambiguity class
  (the set of its `infover` readings, or its genre/nombre cells), and count the observed reading per class. Spoken
  treebanks first; fall back to all treebanks, then to the Lexique prior, for classes with fewer than 20 tokens.
  Output: `resources/readingShares.tsv` (class, reading, count, share, source) and a NOTICE with the treebank licences
  (as `resources/morphalouNomAdjForms.NOTICE.md`). Budget: under 100k tokens.
- [ ] **0.2 [Sonnet]** Acceptance: plausible shares for `dis`, `fais`, `sois`, `regarde`, `finis` (impératif well above 0);
  coverage = share of the frequency of ambiguous theory entries whose class is UD-backed. Then recompute the
  "discriminator need" table (below, Results 2026-10-11) with the new shares and replace the three-column version.
  mypy strict and a unit test for the UD→Lexique mapping.

### Iteration 1 — simulator and baseline [Sonnet writes, Haiku runs]

- [ ] **1.1 [Sonnet]** `util/analyze_merged_feature_keys.py` (hand-run diagnostic; reuse the loading and rendering of
  `util/analyze_conjugation_fusion.py`: `loadPhoneticAndDisambiguatedTheory`, `buildKeypressGroupToWords`,
  `buildKeypressGroupExtraAlternates`, `renderFinalStrokesToRTFCRE`). Options: `--eligible` (tense list, default D5),
  `--tie fallback|frequency|precedence`, `--order after-s7|before-s7`, `--merge-keys f=…,p=…`, `--out`.
  Per entry: candidate merged outline = base strokes with the last stroke ∪ the entry's group keys (∪ its merged
  star/hash symbol when `after-s7`; an escalated code's */# marker strokes stay after). Occupied outlines: every final
  outline of the theory (alternates included) plus the reserved chords of the other dictionaries (D8; read the shipped
  JSONs). Resolve each contested merged outline with the ladder (D7; an occupying base outline has only phonetic keys, so
  it always wins level 1), ties by `--tie`. Losers keep the long outline, which is already unique, so one pass suffices.
  Writes the metrics table (M1–M5) as Markdown and a TSV of every entry (word, reading, tense, merged?, reason, outlines).
- [ ] **1.2 [Sonnet]** Regression check: with every tense eligible, no ladder (any conflict counts) and marks ignored, the
  script reproduces the counts of `docs/CONJUGATION_FUSION_STATS.md` (127,839 clean of 139,757).
- [ ] **1.3 [Haiku]** Run the baseline: D5 eligibility, current keys, `after-s7`, tie (a). Paste the table under Results.

### Iteration 2 — check of the eligibility choice [Haiku]

- [ ] Run all-eligible against D5. Report, per excluded tense: strokes it would save, conflicts it causes for the eligible
  ones. GATE only if a figure contradicts D5 (e.g. an excluded tense that would merge almost for free); otherwise no gate.

### Iteration 3 — level-1 tie rule [Sonnet adds rule (c), Haiku runs] GATE

- [ ] Tie rules (a), (b), (c). Report M1–M3 and the list of tied pairs that each rule resolves differently (top 30 by frequency).

### Iteration 4 — merge before or after S7 [Sonnet] GATE

- [ ] `before-s7`: merge on unmarked outlines, then recompute the star/hash marks on the merged entries
  (`composeReservedKeyStrokesForEntries`, src/ambiguitychecker.py, with the merged strokes as each entry's stroke and
  the phoneme stroke count unchanged). Compare with `after-s7` on M1–M5; show the words that merge only under `after-s7`
  (a mark made room, the `sais`/`sec*` case) and the mark changes `before-s7` causes.

### Iteration 5 — keys [Sonnet search, Haiku runs] GATE after 5b, GATE after 5c

- [ ] **5a [Haiku]** Absorption risk per coda key: frequency-weighted share of eligible entries whose last phoneme stroke
  already holds the key, and pressability of the key with the 50 most frequent last-stroke codas.
- [ ] **5b [Sonnet]** Joint search of the f and plural merge key-sets (group 1 f, group 5 nbr_p+p; the merge key-set is
  per group, so nbr_p uses group 5's). Candidates: coda keys 18–25 and the coda digraphs of the Realization Phase; f may keep
  16. Constraints: f, p and f+p distinct, pressable with the stems, distinct from the other 5 groups' keys and every union
  that occurs; f's key before p's in coda order (soft: report violations). Objective: M1 under the settled semantics,
  M4 as tie-breaker. Make the evaluation incremental (only entries needing group 1 or 5 change) so the full candidate
  grid runs in minutes. Report the top 5 pairs with M1–M4. Expected side effect: `fasse`/`fassent` and most of group 3's
  same-lemma conflicts disappear (they come from the absorbed plural `s`).
- [ ] **5c [Sonnet]** Only if the residual conflicts of the other 5 groups justify it (gate 5b decides): re-search their
  keys with the merge objective under today's Realization constraints (one key per group in both strokes, D9).

### Iteration 6 — merge before or after S9 [Sonnet] GATE

Needs the merged theory inside the pipeline (step I1 below, behind a flag), because S9 recomputes the disambiguated
theory through `util/_theoryio.py`.
- [ ] Run `python -m util.build_affix_rules` (delete `AffixSelection.pickle` first) and `python -m util.export_affix_dictionary`
  on the merged theory (before), and alternatively filter merges against today's abbreviations (after). Report M1, M6,
  the merges lost (after) and the abbreviations lost (before); list any affix decision that turns PENDING.

### Implementation (after gate 5, detailed then) [Sonnet; Haiku for rebuilds, tests and md5s]

- [ ] **I1** The merge in the pipeline, behind a constant defaulting to off (md5-identical rebuild when off): a function
  next to `realizeKeypressGroupsAsExtraStroke` (src/ambiguitychecker.py) applied on the inline path
  (`Dictionary.buildDisambiguatedTheory`) and in `util/build_realization_report.py`; the long outline becomes an
  alternate entry; S7 placement per gate 4.
- [ ] **I2** S8: `export_plover_dictionary` (merged primary, long alternate), `realization_report.json` (merge key-sets),
  `export_keyboard_layout` (conjugation-feature legend with the merge keys), `export_practice_words` / `export_lessons`
  (a lesson on merged keys and on the tenses that never merge), then the complement, number and spelling exporters (they
  must still pass their own collision checks), `export_expression_data` + `export_plover_plugin` (fingerprint).
- [ ] **I3** S9 per gate 6.
- [ ] **I4** Docs: docs/PIPELINE.md, docs/specs/discriminating-features.md (new section), GLOSSARY code references,
  CLAUDE.md commands, TODO.md.
- [ ] **I5** Verification: `pytest src/test/` and bare `mypy`; full rebuild per the docs/PIPELINE.md rebuild table; H1–H4
  as unit tests on the exported dictionaries; M7.

## Delegation notes

- A Haiku task gets a self-contained brief: the exact command, the files it may write, the table template to fill, and the
  acceptance check (row counts, totals equal to the previous run's where they must be, H1–H4). It stays under 100k tokens:
  it never reads the large TSVs or pickles into its context, only script output.
- Sonnet redoes or fixes a Haiku task whose output fails its acceptance check, writes all code (mypy strict, CLAUDE.md
  typing conventions) and words each gate as a question with a recommended answer.
- Cost per simulator run: about 3 min (the existing diagnostic); S9 runs about 2.5 min plus the S7/S8 rebuilds.

## Related, not prerequisites

- B48 (TODO "Suspected bugs"): the `frequencies` field of `resolved_press_sets.json` is 0 for frequent words.
- TODO "unpressable base codas": the D12 words; rerun the simulator after that fix.

## Results

### 2026-10-11 — discriminator need (before iteration 0)

Share of all theory running words (film frequency, 267,040 words, 135,785 in Lexique383) needing each discriminator, from
`resolved_press_sets.json` press-sets (they agree with `disambiguated_theory.tsv` for 207,699 of 207,984 words; the rest
are spelling twins). Columns: lexicon prior | equal split | primary reading only. Any feature stroke: 13.5 | 15.2 | 13.0%.

| Pressed discriminator | Group, key | Share |
|---|---|---|
| p | 5, 17 | 3.57 / 3.59 / 3.56% |
| pers_2 | 6, 19 | 3.61 / 2.96 / 1.36% |
| pers_1 | 4, 18 | 2.65 / 2.65 / 2.21% |
| infinitif | 0, 21 | 2.01% |
| impératif | 4, 18 | 0.02 / 1.63 / 2.25% |
| subjonctif | 3, 23 | 0.29 / 1.11 / 0.21% |
| f | 1, 16 | 0.83 / 0.85 / 0.82% |
| nbr_p | 5, 17 | 0.47% |
| pers_3 | 2, 20 | 0.52 / 0.35 / 0.46% |
| passé | 2, 20 | 0.02 / 0.24 / 0.08% |
| future | 2, 20 | 0.19% |
| conditionnel, imparfait | 0, 3 | 0.00% (never pressed) |

| Tense of the reading needing one | Share (and % of that tense's own frequency, equal split) |
|---|---|
| présent | 5.63 / 4.53 / 2.92% (45%) |
| nominal f/p | 3.71% (17%) |
| infinitif | 2.01% (83%) |
| impératif | 0.02 / 1.63 / 2.25% (100%) |
| subjonctif | 0.29 / 1.11 / 0.21% (100%) |
| participe passé | 0.58% (21%) |
| imparfait | 0.56% (44%, pressed through the person keys) |
| future | 0.44% (58%) |
| conditionnel | 0.25% (52%) |
| passé simple | 0.03 / 0.34 / 0.09% (86%) |

Method: frequency per (ortho, lemme_cgram) from Lexique383; a spelling's frequency split over its press-set alternates by
the column's rule, then over each alternate's feature combinations; the lexicon prior is the summed frequency of the
Lexique forms with a single `infover` reading (verbs) or a single genre/nombre cell (NOM/ADJ). Iteration 0 replaces it.
