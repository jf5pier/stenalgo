# Optimisation exploration: which phonemes could be avoided or removed?

Hand-run, read-only analysis scripts (nothing here is part of the pipeline; no pipeline file is modified).
Question they answer: **if a phoneme is removed from the theory, or fused with another phoneme of the same syllabic part
(same keys), how much keyboard effort is saved and how many new outline collisions are created?**
A phoneme with a large cost drop and few added collisions is a candidate for removal or fusion, and so for freeing a key.

The code lives in `scratch/optimisation_exploration/` (committed there, outside the mypy and pytest scope) and writes to its `out/`.
All scripts run from the repo root (`python scratch/optimisation_exploration/optexp_X.py`). Paths below are relative to that directory.

## Prerequisites (all read, never written)

`starboard3h.json`, `Dictionary.pickle`, `PhoneticTheory.pickle`, `DisambiguatedTheory.pickle` (see `util/_theoryio.py`),
`plover_stenalgo_affix_dictionary.json`, `plover_stenalgo_brief_dictionary.json`, `resources/Lexique383.tsv` (cost script only).
The pickles and dictionaries must be current with the committed layout and lexicons. After any theory, layout, affix or brief
change, rebuild them and rerun the whole chain below: the outputs in `out/` are a snapshot of one theory state.

## Concepts

- **Removal model**: the phoneme is dropped from every syllable of every word, the syllable's keys are rebuilt by the keyboard, and in each
  later outline (feature, mark, merged outlines) the old base keys are replaced by the new ones; feature, mark and merge keys stay as they are
  (no re-disambiguation). Affix and brief outlines are fixed strings, rewritten stroke by stroke where the stroke holds the syllable's old keys (heuristic).
- **Phoneme variants**: consonants are reported as `X` (all parts), `X/onset`, `X/coda`; the part variant is only run when it differs from `X`. Vowels have one label.
- **Stages**: `S5_phonetic` (base strokes), `S6_feature` (+feature keys, no marks), `S7_marks` (+star/hash marks, long outlines), `merged`
  (final theory), `plus_affix`, `plus_briefs`. The intact theory has 0 collisions from S7 on.
- **Collision** = one canonical outline shared by two different spellings (as `src.ambiguitychecker.findFinalCollisions`). A "group" is one shared outline;
  "mass" (`excessFreq`) is the frequency per million of the non-top claimants, i.e. what would be mistyped.
- **Cost**: each spelling is typed with its most abbreviated outline (fewest strokes, then lowest `Starboard.getChordCost` summed over strokes);
  complexity = frequency-weighted mean cost per word (intact: 254.97 per word, 1.165 strokes per word).

## Run order

```
python scratch/optimisation_exploration/optexp_phoneme_counts.py        # ~1 min   -> out/phoneme_word_counts.tsv
python scratch/optimisation_exploration/optexp_phoneme_information.py   # ~18 min  -> out/phoneme_information_raw.tsv
python scratch/optimisation_exploration/optexp_phoneme_fusion.py        # long, prints one dict per pair -> out/phoneme_fusion.tsv  (needs the raw TSV)
python scratch/optimisation_exploration/optexp_phoneme_cost.py          # ~4 min   -> out/phoneme_cost.tsv, out/phoneme_cost_baseline.tsv
python scratch/optimisation_exploration/optexp_phoneme_report.py        #          -> out/phoneme_information.md, out/phoneme_information_by_stage.tsv
```

`information`, `cost` take `--phonemes @,a,R/onset` (subset, for a quick test) and `--workers N` (default 4, fork pool; each worker shares the loaded theory,
so mind the 14 GiB cgroup limit noted in memory before raising it). Each of the three heavy steps spends ~1 min loading and preparing the theory.
The report must be run last: it appends the fusion section to the md if `phoneme_fusion.tsv` exists and adds the two cost columns if `phoneme_cost.tsv` exists.

## The scripts

| Script | Role | Reads | Writes |
|---|---|---|---|
| `optexp_common.py` | Library: `loadAll()` (layout, dictionary, disambiguated and phonetic theories), `canon`, `MARKS` (keys 0, 1, 10, 15), `OUT`. | pipeline outputs | nothing |
| `optexp_phoneme_counts.py` | Per phoneme variant: distinct spellings, readings, summed `Word.frequency` (books + films). Feeds the "words with it / frequency" column. | theory | `phoneme_word_counts.tsv` |
| `optexp_phoneme_information.py` | Core simulation: collisions added by removing each phoneme, at each of the 6 stages. Also exports `prepare()`, `remap()`, `removed()`, `collisions()`, `G` used by the other scripts. | theory + affix/brief dictionaries | `phoneme_information_raw.tsv` (columns: groups, words, excessFreq, crossLemmaGroups, sameLemmaGroups, wordsEmptied, claims) |
| `optexp_phoneme_fusion.py` | For each *rare* phoneme P (removal creates < 100 colliding groups or < 1000 frequency mass at S7; `literal`=1 if it meets the strict 100/100 rule) and each partner Q of the same part: collisions when P is typed with Q's keys (`P_to_Q_*`) and when Q is typed with P's keys (`Q_to_P_*`). `0/0` on both sides means they already share a key. | raw TSV + theory | `phoneme_fusion.tsv` |
| `optexp_phoneme_cost.py` | Keyboard-complexity drop per removed phoneme, two variants: **all** (removed everywhere, collisions ignored) and **kept** (spellings whose typed outline then collides keep the phoneme, iterated to a fixpoint; `reverted` = number of spellings kept). Frequencies come from Lexique383 films, as `util.compare_theories`. | theory + dictionaries + Lexique383 | `phoneme_cost.tsv`, `phoneme_cost_baseline.tsv` |
| `optexp_phoneme_report.py` | Assembles everything: phoneme x stage table sorted by increasing "kept" cost drop, plus a fusion matrix per part. | all TSVs above | `phoneme_information.md` (the deliverable), `phoneme_information_by_stage.tsv` |
| `optexp_fusion_examples.py` | Debug aid: `python ... optexp_fusion_examples.py PART SRC DST` prints the 12 most frequent collisions created by typing SRC with DST's keys (word, outline, colliding spellings). Run it to see *why* a fusion costs what the matrix says. | theory | stdout |
| `optexp_elided_cost.py` | Unrelated side study (see below). | `plover_stenalgo_dictionary.json`, `opensubtitles-fr/sample.txt` | stdout |

## Reading the result (`out/phoneme_information.md`)

- Each stage cell is `extra colliding groups / extra mass`. Negative group counts at S5 are not errors: removing a phoneme can merge two outlines that were
  already colliding into one group.
- The last two columns are the cost drop in % of the mean cost per word. **Use "conflicts kept"**: it is what remains once the removal is made safe,
  while "all removed" ignores the collisions and is only an upper bound (e.g. the schwa `°` is 3.78% / 0.21%, `E` 2.11% / 0.07%).
- Table rows are sorted by increasing "conflicts kept" gain, so the bottom is where a removal pays most. Rank candidates by gain relative to added mass at `plus_briefs`.
- Typical decision reading: a phoneme with a tiny mass at `plus_briefs` and a non-trivial gain is a removal candidate; a rare phoneme whose fusion row is `0 / 0`
  already shares its key with the partner, so its key can be reused at no cost.

## Which scripts are deprecated?

None is superseded by a newer one: the five main scripts form a chain (each feeds the next) and `optexp_phoneme_cost.py` *complements* the collision tables rather than replacing them
(collisions say what a removal breaks, cost says what it gains). Notes:

- `optexp_phoneme_report.py`'s older behaviour (sort by `plus_briefs` mass) is superseded by the cost-based sort, which applies automatically once `phoneme_cost.tsv` exists.
- `optexp_elided_cost.py` is a one-off: it compares the chord cost of the elided forms (`j'`, `d'`, `l'` ...) with their full words (`je`, `de`, `le` ...) weighted by OpenSubtitles frequency. It hardcodes stroke strings of an earlier
  layout (`"vt@a"` etc.), is not parameterised and does not use the removal model; it is not needed for the phoneme-removal project and may be stale against the current layout. Keep for reference or drop.
- `optexp_fusion_examples.py` is a debugging companion of the fusion script, not a pipeline step.
- Not tracked artifacts: `out/cost.log` (an older run, mean cost 257.2, from before the current baseline), `out/run.log`, `out/fusion.log` (raw run output) and `out/prev/` (an older copy of the raw TSV) are leftovers and can be deleted.

## Known limits

- Affix and brief outlines are remapped heuristically, and the feature/mark/merge keys are not re-decided after a removal, so a real removal followed by a full pipeline rebuild could do slightly better
  (the S7 marks and merged feature keys could be recomputed). Treat the numbers as screening, then confirm a shortlisted phoneme with an actual `util.optimize_keyboard` / rebuild run.
- Collision mass uses `Word.frequency` (books + films); cost weights use Lexique383 films frequency; the two are not the same weighting.
- 880 spellings without a priceable outline are left out of the cost baseline (as `theorycompare` does).
