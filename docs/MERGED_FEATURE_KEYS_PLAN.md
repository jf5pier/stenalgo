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
| D5 | **Merge-eligible tenses**: présent, impératif, infinitif, participe, nominal (f/p), and since gate 2 (2026-10-12) imparfait, future, conditionnel. **Never merge**: passé simple, subjonctif. Decided per entry from the tense of its reading, not from the keys it presses. |
| D6 | Every entry (alternate readings of self-homographs included, `dis` has 4) merges independently. |
| D7 | **Merge precedence ladder** for a merged outline meeting another outline: (1) phonetic first: the word for which the shared keys are sounds wins (`sec` beats `sais`, `livre` beats `livres`, `dites` beats `dis`); a tie at level 1 (each word's feature keys are the other's sounds) goes to the more frequent word (gate 3); (2) features second: same base, same lemme+category, the word with an absorbed feature key loses (`fasse` beats `fassent`); (3) marks third: same base and same feature keys across lemmas/categories never block, star/hash marks separate them. Frequency decides nothing else. The merge runs after S7: marks are part of the compared outlines (gate 4). |
| D8 | A merge always gives way to the number chords, spelling chords, punctuation, commands and expression briefs (nothing shipped changes). |
| D9 | One feature = one physical key, merged or not, f (16) and plural (17) included: no dedicated merge key-set (gate 5b); the other groups' keys are not re-searched (5c skipped). |
| D10 | No per-word chord-cost veto: an eligible entry merges whenever it wins the ladder and the merged stroke is pressable. |
| D11 | Keys 0 and 1 are not touched. The Grouping Phase (K=7, the user's elicitation answers) stays fixed. |
| D12 | Words whose BASE last stroke is already unpressable (~893, `-ismes`; TODO "unpressable base codas") are set aside: automatic fallback, reported apart, fixed later. |
| D13 | A reading's share of its spelling's frequency comes from the reading-share table `resources/readingShares.tsv` (iteration 0, `util/build_reading_shares.py`), looked up by the entry's reading set in LexiqueMixte + LexiqueSynthetic (not Lexique383's `infover`, which misses readings). Never read the `frequencies` field of `resolved_press_sets.json` (bug B48). |
| D14 | Everything is simulated offline in an analysis script first; the pipeline is changed only for the chosen variant. |
| D15 | From 2026-10-12 the work is done inline in one session (no Haiku/Sonnet subagents: each would re-read the context cold); long rebuilds run in the background. The user decides at every gate. (Iterations 0–5 used Haiku workers and Sonnet for code and gates.) |
| D16 | The reserved chords of D8 come from their sources, never from the shipped JSONs (built after the theory, from it): `reservedNumberStrokes`, `reservedSpellingStrokes`, the punctuation/command/Lapwing chords converted from the layout before their theory filter, and `scratch/expr-briefs.tsv`. One function, used by the pipeline and the simulator. |
| D17 | The merge rules live in one module, `src/mergedfeaturekeys.py`, used by the pipeline (I1) and the simulator (which keeps only options, metrics and search); the simulator's runs before and after the move must match. |
| D18 | Gates 3–5 are not rerun after the D5 change; one confirmation run with the decided settings becomes the new baseline and the simulator's defaults. |
| D19 | The trainer shows the merged outline and also accepts the long one: an `alternates` field in the practice-word and lesson JSONs, checked by the trainer. |
| D20 | The accord and verbe lessons teach the merged outlines in place (verbe-01 explains the merge once); one new lesson at the end of the verbe track, "quand les marques ne fusionnent pas", covers subjonctif, passé simple and the frequent fallbacks. |
| D21 | Order, one commit per step: (1) `src/mergedfeaturekeys.py`, simulator switched to it, same numbers; (2) confirmation run (D18); (3) I1 behind a constant off by default, md5-identical rebuild when off; (4) iteration 6 gate; (5) I2 (D19, D20), I3, I4, I5. |

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

- [x] **0.1 [Haiku]** Download the French Universal Dependencies treebanks (GitHub `UniversalDependencies/UD_French-ParisStories`,
  `UD_French-Rhapsodie` (spoken), `UD_French-GSD`, `UD_French-Sequoia`) into a gitignored `ud-french/`. Write
  `util/build_reading_shares.py`: for every VERB/AUX/NOUN/ADJ token, map the UD features to Lexique's reading notation
  (Mood=Ind+Tense=Pres → `ind:pre`, Tense=Imp → `ind:imp`, Tense=Past → `ind:pas`, Tense=Fut → `ind:fut`; Mood=Sub →
  `sub:pre`/`sub:imp`; Mood=Cnd → `cnd:pre`; Mood=Imp → `imp:pre`; VerbForm=Inf → `inf`; VerbForm=Part → `par:pas`/`par:pre`;
  Person+Number → `1s`…; NOUN/ADJ Gender+Number → `nom:fs`…), look up the lowercased form's Lexique ambiguity class
  (the set of its `infover` readings, or its genre/nombre cells), and count the observed reading per class. Spoken
  treebanks first; fall back to all treebanks, then to the Lexique prior, for classes with fewer than 20 tokens.
  Output: `resources/readingShares.tsv` (class, reading, count, share, source) and a NOTICE with the treebank licences
  (as `resources/morphalouNomAdjForms.NOTICE.md`). Budget: under 100k tokens.
- [x] **0.2 [Sonnet]** Acceptance: plausible shares for `dis`, `fais`, `sois`, `regarde`, `finis` (impératif well above 0);
  coverage = share of the frequency of ambiguous theory entries whose class is UD-backed. Then recompute the
  "discriminator need" table (below, Results 2026-10-11) with the new shares and replace the three-column version.
  mypy strict and a unit test for the UD→Lexique mapping.

### Iteration 1 — simulator and baseline [Sonnet writes, Haiku runs]

- [x] **1.1 [Sonnet]** `util/analyze_merged_feature_keys.py` (hand-run diagnostic; reuse the loading and rendering of
  `util/analyze_conjugation_fusion.py`: `loadPhoneticAndDisambiguatedTheory`, `buildKeypressGroupToWords`,
  `buildKeypressGroupExtraAlternates`, `renderFinalStrokesToRTFCRE`). Options: `--eligible` (tense list, default D5),
  `--tie fallback|frequency|precedence`, `--order after-s7|before-s7`, `--merge-keys f=…,p=…`, `--out`.
  Per entry: candidate merged outline = base strokes with the last stroke ∪ the entry's group keys (∪ its merged
  star/hash symbol when `after-s7`; an escalated code's */# marker strokes stay after). Occupied outlines: every final
  outline of the theory (alternates included) plus the reserved chords of the other dictionaries (D8; read the shipped
  JSONs). Resolve each contested merged outline with the ladder (D7; an occupying base outline has only phonetic keys, so
  it always wins level 1), ties by `--tie`. Losers keep the long outline, which is already unique, so one pass suffices.
  Writes the metrics table (M1–M5) as Markdown and a TSV of every entry (word, reading, tense, merged?, reason, outlines).
- [x] **1.2 [Sonnet]** Regression check: with every tense eligible, no ladder (any conflict counts) and marks ignored, the
  script reproduces the counts of `docs/CONJUGATION_FUSION_STATS.md` (127,839 clean of 139,757).
- [x] **1.3 [Haiku]** Run the baseline: D5 eligibility, current keys, `after-s7`, tie (a). Paste the table under Results.

### Iteration 2 — check of the eligibility choice [Haiku]

- [x] Run all-eligible against D5. Report, per excluded tense: strokes it would save, conflicts it causes for the eligible
  ones. GATE only if a figure contradicts D5 (e.g. an excluded tense that would merge almost for free); otherwise no gate.

### Iteration 3 — level-1 tie rule [Sonnet adds rule (c), Haiku runs] GATE

- [x] (run 2026-10-11, gate 2026-10-12) Tie rules (a), (b), (c). Report M1–M3 and the list of tied pairs that each rule resolves differently (top 30 by frequency).

### Iteration 4 — merge before or after S7 [Sonnet] GATE

- [x] (run 2026-10-11, gate 2026-10-12) `before-s7`: merge on unmarked outlines, then recompute the star/hash marks on the merged entries
  (`composeReservedKeyStrokesForEntries`, src/ambiguitychecker.py, with the merged strokes as each entry's stroke and
  the phoneme stroke count unchanged). Compare with `after-s7` on M1–M5; show the words that merge only under `after-s7`
  (a mark made room, the `sais`/`sec*` case) and the mark changes `before-s7` causes.

### Iteration 5 — keys [Sonnet search, Haiku runs] GATE after 5b, GATE after 5c

- [x] **5a [Haiku]** Absorption risk per coda key: frequency-weighted share of eligible entries whose last phoneme stroke
  already holds the key, and pressability of the key with the 50 most frequent last-stroke codas.
- [x] (run 2026-10-11, gate 2026-10-12) **5b [Sonnet]** Joint search of the f and plural merge key-sets (group 1 f, group 5 nbr_p+p; the merge key-set is
  per group, so nbr_p uses group 5's). Candidates: coda keys 18–25 and the coda digraphs of the Realization Phase; f may keep
  16. Constraints: f, p and f+p distinct, pressable with the stems, distinct from the other 5 groups' keys and every union
  that occurs; f's key before p's in coda order (soft: report violations). Objective: M1 under the settled semantics,
  M4 as tie-breaker. Make the evaluation incremental (only entries needing group 1 or 5 change) so the full candidate
  grid runs in minutes. Report the top 5 pairs with M1–M4. Expected side effect: `fasse`/`fassent` and most of group 3's
  same-lemma conflicts disappear (they come from the absorbed plural `s`).
- [x] **5c [Sonnet]** (skipped, gate 5b) Only if the residual conflicts of the other 5 groups justify it (gate 5b decides): re-search their
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

### 2026-10-11 — iteration 0: reading-share table

`python -m util.build_reading_shares [--validate]` (about 10 s) → `resources/readingShares.tsv` (91 classes, 45 with
several readings, 171 rows) + `resources/readingShares.NOTICE.md`; tests `src/test/build_reading_shares_test.py`.

Changed from the 0.1 brief (gate answer (a), 2026-10-11):
- The four UD treebanks alone underrate the impératif. The spoken ones are 87k tokens of narrative monologue
  (`fais` 0/38 impératif, `regarde` 0/9), so the first source is now film dialogue: every 400th line of OPUS
  OpenSubtitles v2018 fr (267k lines, gitignored `opensubtitles-fr/`). spaCy `fr_core_news_md` cannot tag it ("Regarde !"
  → Ind 3s; "Fais gaffe", "Viens ici" get no verb at all), so a dialogue heuristic labels each token. A subject clitic gives the person.
  A subjectless clause start or a `-moi`/`-le` suffix gives the impératif, and coordination keeps the earlier subject. An auxiliary
  before the form gives the participle; after `que` the mood stays open and is split with weights fitted on the UD tokens that follow `que`.
  A form is counted only when a single verb lemma carries ≥ 80% of its film frequency (this drops `juge`, `voyage` and `suis`).
- Source order per class (≥ 20 tokens): subtitles, UD spoken, UD all, then a Luce choice model fitted on the
  observed classes (replaces the Lexique prior, which credits the impératif with ~0).
- Classes come from LexiqueMixte + LexiqueSynthetic, the theory's reading sets. With Lexique383 classes, 27k theory
  readings (45k frequency) had no share (`importe` lacks `sub:pre:1s/3s` there); now 0 do.

Acceptance:
- Heuristic against UD gold (`--validate`, verb tokens of multi-reading classes): `ind:1s`/`ind:2s` 98–99% right, `ind:3s`
  87–89%, `sub:3s` 76–79%, impératif recall 58% (spoken, no punctuation) and 89% (written). Impératif precision is
  poor on written news (noun subjects before a comma) but good on subtitles. In a random sample of 50 subtitle tokens
  labelled impératif, 45 were right; the 5 noun homographs (`juge`, `police`...) are now filtered out.
- Shares (impératif first): `dis` 0.50 (ind:pre:1s 0.28, 2s 0.16, passé simple 0.06); `fais`, `viens` 0.26 (1s 0.46,
  2s 0.27); `regarde` 0.25 (1s 0.32, 3s 0.43, subjonctif 0.01); `finis` 0.25 (participe 0.25); `sois` 0.53
  (sub 1s 0.21, 2s 0.27).
- Coverage: of the film frequency of multi-reading rows (verbs and NOM/ADJ), 97.4% has data-backed shares (subtitles
  68.5%, UD spoken 28.9%, UD all 0.6%), 1.9% pooled. Nearly all of the pooled part is `suis` credited to suivre (1,819/M in Lexique).

### 2026-10-11 — discriminator need (recomputed with the reading shares)

Share of all theory running words (film frequency, 267,040 words, 135,785 in Lexique383) needing each discriminator, from
`resolved_press_sets.json` press-sets (they agree with `disambiguated_theory.tsv` for 207,699 of 207,984 words; the rest
are spelling twins). Columns: **reading shares** (D13) | lexicon prior | equal split | primary reading only. Any feature
stroke: **14.4** | 13.5 | 15.2 | 13.0%.

| Pressed discriminator | Group, key | Share |
|---|---|---|
| p | 5, 17 | **3.57** / 3.57 / 3.59 / 3.56% |
| pers_1 | 4, 18 | **3.17** / 2.65 / 2.65 / 2.21% |
| pers_2 | 6, 19 | **2.36** / 3.61 / 2.96 / 1.36% |
| infinitif | 0, 21 | 2.01% |
| impératif | 4, 18 | **1.62** / 0.02 / 1.63 / 2.25% |
| f | 1, 16 | **0.82** / 0.83 / 0.85 / 0.82% |
| pers_3 | 2, 20 | **0.51** / 0.52 / 0.35 / 0.46% |
| nbr_p | 5, 17 | 0.47% |
| subjonctif | 3, 23 | **0.29** / 0.29 / 1.11 / 0.21% |
| future | 2, 20 | 0.19% |
| passé | 2, 20 | **0.04** / 0.02 / 0.24 / 0.08% |
| conditionnel, imparfait | 0, 3 | 0.00% (never pressed) |

| Tense of the reading needing one | Share (and % of that tense's own frequency, reading shares) | Tense's whole mass |
|---|---|---|
| présent | **4.89** / 5.63 / 4.53 / 2.92% (44%) | 11.03% |
| nominal f/p | 3.71% (17%) | 21.42% |
| infinitif | 2.01% (83%) | 2.43% |
| impératif | **1.62** / 0.02 / 1.63 / 2.25% (100%) | 1.62% |
| participe passé | **0.58** / 0.58 / 0.59 / 0.57% (19%) | 3.00% |
| imparfait | 0.56% (44%, pressed through the person keys) | 1.27% |
| future | 0.44% (58%) | 0.77% |
| subjonctif | **0.29** / 0.29 / 1.11 / 0.21% (100%) | 0.29% |
| conditionnel | 0.25% (52%) | 0.48% |
| passé simple | **0.05** / 0.03 / 0.34 / 0.09% (47%) | 0.10% |

Method: frequency per (ortho, lemme_cgram) from Lexique383, split over a spelling's press-set alternates and then over
each alternate's feature combinations. **Reading shares**: the share of the combination's reading in the class of the
entry's Mixte + Synthetic reading set (`par:pas` and `nom:` cells summed when gender or number is open). The lexicon prior
uses the summed frequency of the Lexique forms with a single `infover` reading or a single genre/nombre cell. The
eligible tenses of D5 (présent, impératif, infinitif, participe, nominal) are now 12.8% of running words, the ceiling of
the merge; the excluded tenses keep 1.6%.

### 2026-10-11 — iteration 1: simulator and baseline

`python -m util.analyze_merged_feature_keys [--eligible …|all] [--tie fallback|frequency|precedence]
[--order after-s7|before-s7] [--merge-keys f=…,p=…] [--search] [--regression] [--out DIR]` (about 2 min; outputs
`OUT/metrics.md` + `OUT/entries.tsv`, runs under `scratch/merged-keys/`); tests `src/test/analyze_merged_feature_keys_test.py`.
Alternate ↔ press-set alignment: 0 mismatches over 311,373 entries (267,406 words); 82 reading-share misses.

1.2 regression (`--regression`): 139,757 words needing a group, 127,961 without a conflict (= clean 127,839 +
abbrevOnly 122), 11,348 conflicts (= 4,107 + 141 + 2,247 + 4,853), 448 unpressable: identical to
docs/CONJUGATION_FUSION_STATS.md.

1.3 baseline (D5, current keys, after-s7, tie (a) fallback), `scratch/merged-keys/baseline/metrics.md`:

| Metric | Value |
|---|---|
| H1 new collisions / H2 unpressable merged | 0 / 0 (one outline already shared today) |
| M1 strokes per running word | 1.5101 → **1.3977 (−7.45%)**; unweighted per word 3.657 → 3.381 |
| M2 merge rate | 89,980 of 96,161 eligible entries (93.6%); by frequency 11.2% of 13.3% of running words (84.3%) |
| M2 per group (freq) | inf 93.0%, f 91.7%, pers_3/passé/future 72.4%, impératif/pers_1 85.7%, plural 81.5%, pers_2 77.6% |
| M2 per tense (freq) | présent 83.2%, impératif 81.0%, infinitif 93.0%, participe 97.9%, nominal 81.1% |
| M3 fallbacks (freq of running words) | occupied 1.8% (31 of the top 1,000 spellings), tie 0.2% (11), level 1 146 entries, level 2 7, base unpressable 437 (D12), other dictionary 1 (`tuer` = an expression brief) |
| M4 merged stroke cost | 364.5 vs 393.7 (last base stroke + feature stroke) |
| M5 marks | unchanged (after-s7): 10,795 marked entries, 158 escalated codes, 0.0618 mark keys per word |

Largest fallbacks (all occupied by a phonetic outline): `es` (`aide`), `sais` (`sec`, `cède`), `allez` (`alloc`), `aux`
(`hausse`), `aller` (`alors`), `dis` (`dyke`), `enfants` (`enfance`), `va` (`vaque`), `seule` (`semble`), `femmes`
(`phasmes`), `mains` (`mince`); ties: `toutes`/`toussent`, `minutes`/`minutent`, `laisse`/`leks`, `trouve`/`troupes`.

### 2026-10-11 — iteration 2: eligibility check (`--eligible all`)

M1 −8.07% (against −7.45%). Per excluded tense, the share of running words its merges would save, and the eligible merges
it would take:

| Excluded tense | Saved (running words) | Eligible merges lost |
|---|---|---|
| imparfait | 0.49% | none |
| future | 0.44% | none |
| conditionnel | 0.25% | none |
| subjonctif | 0.22% | 355 entries, 0.48% (`ils`/`hisse`, `elles`/`aient`, `films`/`filment`, `belles`/`baisse` become ties) |
| passé simple | 0.02% | none |

This contradicts D5 for imparfait, future and conditionnel: they would merge almost for free (98.7–100% merge rate).
GATE question queued; D5 kept until answered.

Breakdown (share of running words; merged with one group / with several): imparfait 0.47% / 0.09% (93% / 62%, `étaient`
2+5 = `-st`), future 0.39% / 0.05% (100% / 100%), conditionnel 0.23% / 0.02% (100% / 100%), subjonctif 0.19% / 0.08%
(84% / 70%). Imparfait and conditionnel press only person keys (their ending `-ie` carries the tense), future presses
`-t` (shared with pers_3, passé): merging them gives no key a new meaning.

**Gate decision (2026-10-12):** imparfait, future and conditionnel become merge-eligible; subjonctif and passé simple
stay excluded. D5 updated.

### 2026-10-11 — iteration 3: tie rule (gate decided)

| Rule | M1 | Merged (freq of running words) | Ties left |
|---|---|---|---|
| (a) fallback | −7.45% | 11.2% | 832 entries (0.2%) |
| (b) frequency | **−7.59%** | 11.5% | 409 (0.0%) |
| (c) GRAMCAT_PRIORITY, precedence spec, frequency | −7.55% | 11.4% | 425 (0.1%) |

(b) and (c) resolve 332 of the 831 tied entries differently, listed in `scratch/merged-keys/tie-differences.md`. (c) ranks
NOM above VER, so `troupes` (20.6) takes `tR@ejsk` from `trouve` (160, présent + impératif), `sortes` from `sortent`,
`commandes` from `commences`. (b) gives the frequent verb forms. Recommendation: (b).

**Gate decision (2026-10-12):** (b) frequency. D7 updated.

### 2026-10-11 — iteration 4: merge before or after S7 (gate decided)

| Order | M1 | Merged (freq) | Mark keys per word | Long outlines whose marks change |
|---|---|---|---|---|
| after-s7 | **−7.45%** | 11.2% | 0.0618 (unchanged) | 0 |
| before-s7 | −7.33% | 11.1% | 0.0745 | 19 entries, 1.4% of running words: `a` (avoir) `*a` → `*a#`, `ah` `*a#` → `*a`, `ère`, `fie` |

627 entries (0.17% of running words) merge only under after-s7, where a mark made room: `ans` `*@s` (`anse` keeps `@s`),
`mots` `m*aes`, `prêts` `pR*ies`, `noms`, `mètres`, `tue`, `verres`, `eaux`, `risque`. None merge only under before-s7
(`scratch/merged-keys/order-differences.md`). Recommendation: after-s7.

**Gate decision (2026-10-12):** after-s7. D7 updated.

### 2026-10-11 — iteration 5a/5b: merge key-sets for f and plural (gate decided)

`python -m util.analyze_merged_feature_keys --search` (after-s7, tie (a), D5; ~25 min), full tables in
`scratch/merged-keys/search/search.md`. 5a: every coda key and digraph is pressable with the 50 most frequent last-stroke
codas of the f/plural entries, except `-Z` (24: 38/50, 81.7% of their frequency), `-Zm`, `-n`, `-l` and `-m` (94–98%).
Keys already in the last stroke of f/plural entries: `-l` 18.3%, `-R` 15.6%, `-t` 8.5%, `-s` 6.0%, `-j` 5.4%, `-Z` 2.1%.

5b: 272 (f, p) pairs over the 10 coda keys and the 7 Realization Phase digraphs; 146 rejected because f, p or f+p equals
the key-set of another occurring group set; 126 evaluated.

| Merge key-sets | M1 | f/plural merged (freq) | M4 merged-stroke cost |
|---|---|---|---|
| today f=16 p=17 | −7.45% | 82.9% | 364.5 |
| best: f=17 p=18+19 (and f=20+22 p=18+19, f=16+17 p=18+19) | **−7.65%** | 88.4% | 376.8 |
| best without the other groups' keys: f=17 p=16 (swap) | −7.58% | 85.6% | 360.0 |
| f=22 p=16 | −7.56% | 85.2% | 360.5 |
| f=22 p=17 (f moves to `-n` only) | −7.47% | 83.5% | 367.3 |

The ceiling of a dedicated key-set is +0.2 points of M1 (≈ 0.3% of running words more merged). The best pairs give the
plural `-kd`, the keys of impératif/pers_1 and pers_2 (allowed: no entry needs both groups 4 and 6). Recommendation:
keep f=16, p=17 (no new key to learn, lowest effort), unless +0.2 points is worth a two-key plural. 5c looks
unlikely to pay: the residual is mostly "occupied" (1.8% of running words, phonetic outlines); other keys would hit
other phonetic outlines, and for f/plural the whole grid moved M1 by at most 0.2 points.

**Gate decision (2026-10-12):** keep f=16, p=17, no merge key-set; 5c skipped. D9 updated.
