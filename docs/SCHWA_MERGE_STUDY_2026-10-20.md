# Schwa compression study (first-syllable schwa dropped, onset merged forward), 2026-10-20

Status: exploration only, nothing in the pipeline changed. Branch `phonology-rewrite`. Script and outputs are untracked under
`scratch/optimisation_exploration/` (`optexp_schwa_merge.py`, `out/schwa_merge_*`, `out/reduced_outlines_schwamerge.tsv`,
`out/schwa_candidates.tsv`, `out/baseline_ambiguity.txt`, `out/baseline_compare/`). The script and the report were written by a Sonnet
subagent and reviewed here; the numbers below are its, spot-checked against the sanity words.

## Hypothesis
In a word whose first syllable is `C°` (onset + schwa, no coda, at least two syllables), the schwa is never typed and the onset is
merged into the next syllable's onset (`petit` `p°ti` -> `pti`, `demain` `d°m5` -> `dm5`, `cela` `s°la` -> `sla`). The compressed form
is used where it creates no new conflict; for the layout solve the compressed form carries 95% of the word's frequency and the long
form 5%.

## Method
- Candidates: 11,825 spellings (12,513 words), 2.44% of film frequency. 152 distinct merged onsets, all legal chords.
- Safe scenario: compress only where the new outline is conflict-free against every other spelling's long, compressed, affix and brief
  outline (fixed point, as `optexp_reduced_outlines.py`). Forced scenario: compress every legal candidate. "Safe+S5": safe, minus the
  spellings that would join another lemme's S5 cluster.
- Conflict = S5 phonetic-theory stroke key shared by two or more distinct bare lemmes (before S6/S7 marks).
- Savings priced against the short form (affix + briefs) and against the dictionary alone; confirmed with `util.compare_theories`
  on the safe TSV (-0.3995 cost, as the script's estimate).

## Results
Per word. Baselines: short form 1.165 strokes and 254.97 cost; dictionary alone 1.375 strokes and 279.75 cost.

| Scenario | Strokes saved | Cost saved (100%) | Cost saved (95/5) |
|---|---|---|---|
| Forced, vs short form | 0.0027 | 0.79 | 0.75 |
| Safe, vs short form | 0.0020 | 0.40 | 0.38 |
| Safe+S5, vs short form | 0.0016 | 0.31 | 0.29 |
| Forced, vs dictionary alone | 0.0244 | 3.55 | 3.37 |
| Safe, vs dictionary alone | 0.0175 | 2.37 | 2.25 |
| Safe+S5, vs dictionary alone | 0.0142 | 1.90 | 1.81 |

Conflicts (S5 lemma-homophone clusters, before disambiguation):

| Scenario | Clusters | Mass | New (n / mass) | Enlarged (n / mass) |
|---|---|---|---|---|
| Before | 8,040 | 569,080 | | |
| Forced | 8,815 | 595,281 | 1,060 / 28,533 | 174 / 38,975 |
| Safe | 8,104 | 573,337 | 270 / 7,005 | 22 / 7,045 |
| Safe+S5 | 8,039 | 569,075 | 0 | 0 |

Complexity: keys per stroke 4.69 long, 4.78 compressed (frequency-weighted); at most one phoneme-order violation per merged onset.
Boundary risk (a compressed outline in a swallowing pair): 11.97% of the safe rows, against 31.77% for the shipped single-stroke
outlines; 1,425 rows are multi-stroke and splittable.

## Findings
1. Against the shipped short form the merge saves about 0.4 cost per word (0.15%), far from the 2.4 needed to beat Pluvier (PRP18). The
   frequent candidates already have briefs or affix forms (`petit` `p-`, `besoin` `w-`, `monsieur` `m-js`, `cela` `s-l`). The gain is real
   only against the dictionary-only long form.
2. A chord has no key order, so merging `R` into a consonant onset collides with the unprefixed word: `reprend`/`prend`, `revêt`/`vrai`,
   `remous`/`nous`, `reviens`/`viens`. `R°` (re- words) is also the largest candidate group.
3. `de-` words collide with frequent function words: `devait`/`des`, `devant`/`dans`, `devis`/`dit`; `ceci` collides with `si`, `ci`,
   `scie`; `depuis` with `duit`. The top-100 file (`out/schwa_merge_top100_conflicts.tsv`) lists the clusters by summed frequency, with
   the winner and the lost cost of each.
4. Sanity words `petit demain besoin regarde monsieur cela celui venir` are safe (`regarde` goes from 2 strokes to 1); `ceci` and `depuis`
   revert.

## Caveats and open items
- Before-figures discrepancy to resolve: this script's baseline (8,040 clusters, 569,080 mass, 35 overflow clusters) differs from
  `python -m src.ambiguitychecker` (7,769, 563,931, 24 overflow). Absolute counts are not comparable until explained; deltas are consistent
  within the script.
- The zero-candidate check ran on the function path only; the expression layer `.stenalgo` file is not checked.
- The candidate onset distribution in `out/schwa_candidates.tsv` counted rows, not spellings (R alone exceeded the total): redo before use.
- Proposed policy, not decided: compress only where safe; exclude the bare `re-` prefix; decide forced cases one by one from the top-100
  list (the loser's cost is tiny where the winner is far more frequent).
- Plover has no command to mark a word boundary after a stroke; a swallowed entry can only be undone (`*`) and retyped, or avoided by
  design (an empty `{}` stroke between). Unverified against Plover's source (not installed here).
- The 95/5 weights table is `out/schwa_merge_cp_sat_weights.tsv`; a solve using it is PRP11 work, not done.
