# Phonology rewrite — session summary 2026-10-15 and next step

Written for a fresh session. Read, in this order: this file, `docs/PHONOLOGY_REWRITE_PLAN.md` (decisions PRP1–PRP18; PRP14 and PRP18 are
amended below), `docs/PHONOLOGY_REWRITE_BLIND_SPOTS.md` (section "Settled 2026-10-15"), `docs/PHONEME_REMOVAL_EXPLORATION.md`.
Nothing was committed. New untracked file: `scratch/optimisation_exploration/optexp_reduced_outlines.py` and its outputs in
`scratch/optimisation_exploration/out/` (`dictionary_long_*.json`, `reduced_outlines_*.tsv`).

## 1. Decisions taken this session

| Item | Decision |
|---|---|
| PRA1 | The CP-SAT must weigh the top-200 film words **except those that get a brief** (34 of 200, 6.9% of the top-200 mass). Today all 200 weigh 0 (`nbFrequentWords`, `dictionary.py:79`). Not implemented. |
| PRA2 | No resyllabification in the rewrite. A syllable left without nucleus stays an onset-only stroke; merging strokes is a later downstream optimisation (only when it causes no collision). |
| PRA3 | The optionality test includes the word's current star/hash mark (fixed from the current S7); recheck after a rebuild if the mark moved. |
| PRA4 | No noise sampling. Few CP-SAT solves, each run to convergence on a separate 192-core machine, only for the top 3 candidate phonologies chosen by a pre-analysis. Measured: nucleus OPTIMAL in 25 s; onset FEASIBLE after 30 min on 16 cores (best -16,900,917, bound -24,721,421, gap ~47%, only 0.08% better than the committed layout); coda FEASIBLE (10,365,099 vs bound 9,614,883, gap 7%, no improvement on the committed layout). |
| PRA5 | Briefs and expression rules are not targeted; they are regenerated after a layout is chosen. Candidates are measured without them. |
| PRB1/PRB12 | Optional-phoneme sets in a committed file, revalidated each build; the rewrite is applied in memory after the pickles load, never pickled; flag + file md5s in the `DisambiguatedTheory.pickle` fingerprint. |
| Metric | **Compare on the LONG form** (the dictionary alone), not the short form: briefs and affix abbreviations will be rebuilt for any new keyboard, so the short-form rules are not stable. The short form is reported only for information. |

## 2. Baselines (`util.compare_theories`, 108,150 words both theories cover, film frequency, cost on each theory's own keyboard)

The repo-root `theory_comparison.md` / `.json` were replaced this session by the user's run of 2026-10-13 21:19 (current with the briefs; the
copy I first read was stale, pre-briefs). The stale copies are in the session scratchpad (`old_cmp/`).

| | Stenalgo | Pluvier |
|---|---|---|
| short form (with affix + briefs) | 255.156 | 253.186 (258.332 with collision penalty; 252.641 with `S` on the cheaper pinky) |
| **long form (dictionary alone)** | **281.115** | **276.012** |
| strokes per word, short / long | 1.166 / 1.384 | 1.220 / 1.373 |

So the real gap is on the long form: Stenalgo is 5.1 points (1.8%) above Pluvier. PRP18 must be restated on the long form (see section 5).
An earlier figure of 271.70 (short form) in the plan was stale and has been corrected there; the short-form gap (255.156 vs 253.186) is small
but is the wrong thing to optimise.

## 3. The cheap route (no layout change, no rebuild)

`scratch/optimisation_exploration/optexp_reduced_outlines.py --long --phonemes "A,B;C"` (sets separated by `;`, variants `X`, `X/onset`, `X/coda`;
about 65 s to load, then a few seconds per set):

- removes the set of phoneme variants from every spelling at once, with the fixed-layout removal model of the exploration (syllable keys
  rebuilt by the keyboard);
- a spelling keeps its full phoneme when its reduced outline would collide (fixed-point iteration, as `optexp_phoneme_cost.py`);
- `--long`: the model is the dictionary alone (no affix or brief outline as claimant or typed form);
- writes `out/dictionary_long_<tag>.json` = the shipped `plover_stenalgo_dictionary.json` plus the reduced outlines (never a colliding one;
  independent check against the shipped dictionary and among the new outlines, plus a parse round trip);
- without `--long` it writes `out/reduced_outlines_<tag>.tsv` (affix_abbreviations.tsv format) for `--stenalgo-abbreviations` (short-form study).

The estimate of the script matches the real metric to within about 0.2 per word.

### Real long-form results

`python -m util.compare_theories --pluvier-dict ... --stenalgo-dict out/dictionary_long_<tag>.json --out DIR` (Pluvier arguments as in CLAUDE.md,
`../Pluvier/resources/`). Stenalgo collision groups: 0 in every run. Pluvier long form: 276.012.

| Removed together | Spellings given a reduced outline | Long-form cost | Drop vs 281.115 | Strokes/word |
|---|---|---|---|---|
| none (committed dictionary) | – | 281.115 | – | 1.384 |
| `Z/onset`, `d/onset` | 24,939 | 276.680 | 4.43 (1.6%) | 1.384 |
| `°` | 18,706 | 277.640 | 3.48 (1.2%) | 1.384 |
| `E` | 33,762 | 273.574 | 7.54 (2.7%) | 1.381 |
| `Z/onset`, `d/onset`, `°` | 38,882 | 274.559 | 6.56 (2.3%) | 1.382 |
| `Z/onset`, `d/onset`, `l/onset`, `i`, `n/onset` | 67,266 | 270.986 | 10.13 (3.6%) | 1.378 |
| `Z/onset`, `d/onset`, `l/onset`, `a` | 67,041 | 271.912 | 9.20 (3.3%) | 1.377 |
| `Z/onset`, `d/onset`, `l/onset`, `a`, `°` | 71,647 | 270.683 | 10.43 (3.7%) | 1.375 |
| `Z/onset`, `d/onset`, `°`, `E` | 59,337 | **269.119** | **12.00 (4.3%)** | 1.379 |

Two of the sets stay above Pluvier's long form (276.012): `Z/onset`+`d/onset` alone (276.680) and `°` alone (277.640). Every other set tested is below it,
and the best, `Z/onset, d/onset, °, E` (269.119), is 6.9 below. Pluvier's rule "the schwa is never written" is what `°` alone reproduces; it is not enough on
this layout. Sets are untuned: the search over combinations has not been done.

### Caveats

- **Learnability (PRC1, not measured):** a reduced outline is only worth its gain if the typist can derive it from a rule ("never write `E`
  ...") with a short list of exceptions. Next: per phoneme and part, the rule coverage (share of occurrences by frequency that are reduced) and the
  exceptions (`n spellings keep the phoneme`, e.g. 3,833 for the best set).
- **Boundary risk (PRC4, not measured):** a reduced outline can equal the first stroke of another word's longer outline.
- **Leftover clashes:** the model found a few clashes among the reduced outlines in two sets (`atchoum`/`plum`, `percera`/`persuadera`...);
  the writer drops them, so the dictionaries have none, but the optionality test (PRP5, symmetric, all combinations) is stricter than this model.
- **Marks:** this model checks collisions on the outlines of the final theory (marks included by construction: the claims are the S7/merged outlines).
- **The gain is on a FIXED layout.** A re-solved layout (CP-SAT) could do more or less; this is the cheap route's whole point.
- The old screen (`out/phoneme_cost.tsv`, "kept" column) overstated gains: it counted heuristic remaps of affix and brief outlines.
- Reduced outlines are scratch files only: nothing is wired into the pipeline, the plugin or the trainer.

## 4. Tools and facts worth knowing

- `Dictionary.pickle` / `PhoneticTheory.pickle` / `DisambiguatedTheory.pickle` are current (10-13). `starboard3h.json` is from 10-02.
- Long solve harness (scratchpad, not in the repo): a copy of `src/cpsatsolver.py` with `SOLVER_TIME = 1800.0`, `SOLVER_LOG = True`, driven by a 10-line script.
  Statuses in the log: 2 = FEASIBLE, 4 = OPTIMAL. `SOLVER_TIME = 90.0` is a hard-coded local constant in `optimizeKeyboard`.
- Pluvier clone is at `../Pluvier` (resources in `../Pluvier/resources`).
- Process rule (CLAUDE.md): never wait with `pgrep -f` in a loop.

## 5. Plan changes to make

- **PRP18**: restate the success metric on the **long form** (dictionary alone): today 281.115 vs Pluvier 276.012. Target < 276.012 (already reached by
  most reduced-outline sets above, on the fixed layout); stretch: as low as the model allows, with the learnability counts reported.
- **PRP14**: the greedy loop's step 2 (real CP-SAT) happens only for the top 3 candidates, on a 192-core machine, to convergence; the pre-analysis is
  the cheap route's long-form model, brought to PRP5 semantics (symmetric, every combination, marks and placeholders).
- **PRP7 reading:** the reduced outlines are valid next to the full ones. In the cheap route the full outline stays in the dictionary; the long form
  chosen by `compare_theories` is the cheapest one, i.e. the reduced one where it exists. If "long form" must mean the full phonetic outline
  regardless, the comparison needs an explicit rule-based definition (a decision for the user).

## 6. Next step (new session)

1. Finish this study on the long form: **rule coverage and exceptions per candidate phoneme** (PRC1) and **boundary risk** (PRC4) for the best sets;
   extend the search (greedy over phoneme variants: add the variant with the best marginal long-form gain, with `compare_theories` as the check;
   candidates from `out/phoneme_cost.tsv`: `d`, `Z`, `l`, `a`, `R`, `i`, `n`, `s`, `t`, `e`, `°`, `E`, with the part variants).
2. Decide with the user what "long form" means for a reduced outline (section 5, last point) and rewrite PRP18 and the Goal section of the plan.
3. Pick the shortlist of 3 phonologies and build the portable CP-SAT job for the 192-core machine (phonology, weights, hint layout, constraints, no time limit,
   log on; weigh the 166 non-briefed top-200 words, PRA1). Not before the learnability and boundary checks say the reduced forms are teachable.
4. Open items of the blind-spots doc still unsettled: PRB2–PRB11, PRC1–PRC5, PRD1–PRD3.

## 7. Addendum (later the same day)

- Vocabulary fixed by the user: long form = full phonetic; reduced form = optional phonemes dropped (the "new long form"); short form = affix/brief/other
  rules applied on the reduced form; shortest form = best short form. PRP18 restated accordingly (see the plan). Section 5's last point is resolved.
- PRC1 coverage of `Z/onset,d/onset,°,E` (long-form model): reduced share by frequency Z 23.1%, d 24.1%, ° 16.8%, E 49.1% (by spelling count 87-96%).
  Every frequent function word (je, de, le, ne, ce, est, les, des, mais, elle) is an exception: the gain comes from rare words, and the frequent
  ones are mostly covered by briefs anyway. `optexp_reduced_outlines.py` now prints this coverage per variant.
- **Shortest form on the reduced form (real `compare_theories`, run later 2026-10-15):** `optexp_reduced_outlines.py --phonemes "Z/onset,d/onset,°,E"`
  (short-form model: affix + briefs as claimants) gives 33,147 cheaper outlines (3,378 spellings keep the phoneme); passed as a third
  `--stenalgo-abbreviations` file: **short form 250.812** vs 255.156 today (−4.34, −1.7%), vs Pluvier 253.186 (258.332 penalized, 252.641 with `S` on the pinky).
  Strokes/word 1.166 (unchanged). So most of the 12-point long-form gain overlaps with affix/briefs; about a third survives, enough to pass PRP18's target (< 253.19).
  Reduced share by frequency in this model: ° 5.6%, E 24.1% (the frequent function words are all exceptions). One clash was dropped by the writer (`sRwiek`: dédiait/sciais).
  Same fixed layout, briefs/affixes not regenerated: an upper-bound-free estimate, to be confirmed by regenerating them on the reduced forms.
- **Greedy search on the short-form model** (`scratch/optimisation_exploration/optexp_reduced_greedy.py`, ~25 min per step, stopped after step 3 by decision):
  from `Z/onset,d/onset,°,E` (estimated drop 4.305) it adds `t/onset` (5.190), `l/onset` (5.728), `n/onset` (6.002); next candidates were `o`, `p`, `k/onset`.
  Real `compare_theories` shortest form (fixed layout, affix/briefs not regenerated): 4 variants 250.812; +`t/onset`,`l/onset` 249.467; +`n/onset` 249.155
  (today 255.156, Pluvier 253.186). Strokes/word 1.165 in all.
  Teachability worsens fast: with 7 variants only 45-54% of the spellings carrying a variant are reduced (by count) and 4-18% by frequency;
  15,566 spellings keep a phoneme (3,378 with 4 variants). Three clashes appear (patois/plaza, extrusion/scrutions, suaient/suintaient; the writer drops them).
  The 4-variant set already passes PRP18; extra variants buy 1-1.7 points for many more exceptions. PRC4 (boundary risk) still unmeasured.
- **PRC4 boundary risk of the 4-variant set** (`scratch/optimisation_exploration/optexp_reduced_boundary.py out/reduced_outlines_best4.tsv`, 5 s; live = dictionary +
  affix + briefs + the 33,146 reduced outlines; same notion as `src/briefs.py` BoundaryRisk): (a) a reduced outline R is part of a live multi-stroke X/R or R/Y whose
  other half is live: 4,527 (13.7%; baseline for the shipped single-stroke outlines: 31.8%, mostly the `*#` mark strokes);
  (b) a multi-stroke reduced outline splits into >= 2 live outlines: 22,291 of 31,865 (70.0%) against 56.7% for the shipped dictionary's multi-stroke outlines,
  of which 10,763 splits exist only thanks to another reduced outline. Verdict: not worse than the shipped theory on (a); (b) is +13 points, because 96% of the reduced
  outlines are multi-stroke and a dropped phoneme makes a stroke more likely to equal a short word. The real harm of a split is limited to a typist writing the two words in a row
  (Plover prefers the longest match); not scored, to be re-measured on the final set and with briefs regenerated.
