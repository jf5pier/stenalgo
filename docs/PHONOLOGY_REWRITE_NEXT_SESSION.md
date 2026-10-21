# Phonology rewrite — transition to a new session (written 2026-10-16)

Read, in this order: this file, `docs/PHONOLOGY_REWRITE_SESSION_2026-10-15.md` (study results, sections 1-7), `docs/PHONOLOGY_REWRITE_PLAN.md`
(decisions PRP1-PRP18; PRP18 restated 2026-10-15), `docs/PHONOLOGY_REWRITE_BLIND_SPOTS.md` ("Settled" section), glossary section "Phonology rewrite"
(long / reduced / short / shortest form). Nothing is committed: the docs, `docs/GLOSSARY.md` and the scratch scripts are untracked or modified.

## 1. Where the study stands

- Vocabulary (user): **long form** = full phonetic outline; **reduced form** = long form with optional phonemes dropped; **short form** = affix/brief/other
  rules on top; **shortest form** = best short form.
- Candidate set, chosen by the greedy search and judged on teachability: **`Z/onset, d/onset, °, E`**. On the FIXED layout, with the existing affix
  abbreviations and briefs as claimants and NOT regenerated: shortest form 250.812 vs 255.156 today vs Pluvier 253.186 (PRP18 target < 253.19 met).
  Larger sets (+`t/onset`, `l/onset`, `n/onset`) reach 249.155 but only 45-54% of the spellings carrying a variant are reduced (4-18% by frequency):
  the rule turns into a list. Not retained.
- Boundary risk (PRC4) of the 4-variant set: swallow pairs 13.7% (shipped single-stroke outlines: 31.8%); splittable multi-stroke outlines 70.0% vs 56.7%.
- The frequent function words (je, de, le, ne, ce, est, les, des, mais, elle...) are the exceptions to every drop rule; the gain comes from rare words.

## 2. What is NOT decided (answer to "which phonemes are optional for each word?")

**No per-word optional set exists yet.** The cheap route (`optexp_reduced_outlines.py`) applies a *global* set of variants and keeps, per spelling, the
phoneme whenever the reduced outline would collide (a fixed-point iteration against the fixed outlines of the shipped theory). That is an
estimate, not the PRP5 optional phoneme set: PRP5 requires the test to be symmetric (no frequency priority), over EVERY combination of the word's optional
phonemes against every combination of every other word's, on the full phonology with the keypress-group placeholders and the current marks (PRA3).
A word can have up to 4 optional phonemes (a spelling with Z, d, schwa and E at once); the number of combinations is the lever (PRP6 candidate cap).
Also open: which of the two outlines (full or reduced) counts as "typed" for the CP-SAT weights (PRP7 says both are valid; PRP11 weights by what is typed;
proposal: the cheapest valid outline is the typed one).

## 3. Decision taken at the end of this session (user)

Regenerating affix abbreviations and briefs on the reduced forms is **premature**: the layout may change. The next step is the CP-SAT input; only
after the solve is it worth rebuilding abbreviations and briefs. Order:

1. **Generate the alternate phonology of each affected word** (the PRP5 optional phoneme sets for the 4 variants, symmetric, all combinations, placeholders and marks
   included) and commit them as a sets file (PRB1/PRB12: `resources/` committed file, revalidated each build, rewrite applied in memory after the pickles load,
   behind `STENALGO_PHONOLOGY_REWRITE`). The phonology overrides of PRP3 (`je`→`Z`, `te`→`t`, ... elided ranking) belong to iteration 1 and interact with
   `°`/`Z/onset`/`d/onset`: decide whether they go in first.
2. **Build the CP-SAT input** (PRP11): rewritten phonology + keypress-group placeholders, frequency weights of what is typed (left-out occurrences and retired
   phonemes do not count), top-200 words weighted except the 34 briefed ones (PRA1; today `nbFrequentWords`, `dictionary.py:79`, weighs them 0). Entry point: a
   variant of `util.optimize_keyboard` / `src/cpsatsolver.py`; seeded from `starboard3h.json`; writes a separate layout file, never `starboard3h.json`.
3. **Solve** (PRA4): nucleus is OPTIMAL in 25 s; onset and coda do not converge in 30 min on 16 cores (gaps 47% and 7%), so long solves belong on the 192-core
   machine, to convergence, for the top candidates only. Harness used so far: a copy of `src/cpsatsolver.py` with `SOLVER_TIME = 1800.0`, `SOLVER_LOG = True`
   (statuses: 2 FEASIBLE, 4 OPTIMAL); `SOLVER_TIME = 90.0` is a local constant in `optimizeKeyboard`.
4. **Judge**: does the layout change, and acceptably (learnability: how many phonemes move; objective vs committed layout; PRP18 on a rebuild)?
5. **Then one of two branches**: (a) change the number of phoneme keys per part (onset 2-9, nucleus 11-14, coda 16-25, `keyIDinSyllabicPart`; PRP15, part split)
   and re-solve; or (b) keep the layout and move on to regenerating the affix abbreviations and briefs (`build_affix_rules`, `build_briefs --rederive`) on the reduced forms,
   then compare the shortest form (PRP18).

## 4. Tools and facts

- Scratch scripts (untracked, `scratch/optimisation_exploration/`): `optexp_reduced_outlines.py` (`--phonemes "A,B;C"`, `--long`, `--tag`; prints per-variant
  rule coverage; writes `out/dictionary_long_*.json` or `out/reduced_outlines_*.tsv`), `optexp_reduced_greedy.py` (~25 min per step), `optexp_reduced_boundary.py` (5 s).
  Real check: `python -m util.compare_theories ... --stenalgo-abbreviations affix_abbreviations.tsv --stenalgo-abbreviations briefs.tsv --stenalgo-abbreviations out/reduced_outlines_<tag>.tsv`
  (Pluvier arguments from CLAUDE.md, `../Pluvier/resources/`). Estimates match the real metric to ~0.2 per word.
- Pickles are current (2026-10-13); `starboard3h.json` is from 2026-10-02. Load of the exploration model: ~65 s.
- Process rules: never wait with `pgrep -f`/`pkill -f` (they match the shell itself); stop background jobs by task id.
- Known clashes dropped by the writer in the 4-variant set: `sRwiek` (dédiait/sciais) and, in larger sets, patois/plaza, extrusion/scrutions, suaient/suintaient.
- Open blind spots still unsettled: PRB2-PRB11, PRC1 (learnability beyond coverage counts: needs the user's view on exception lists), PRC2-PRC5, PRD1-PRD3.

## 5. Update 2026-10-20: step 1 of the order of work is built (overrides + elided ranking), measured, uncommitted

- Code: `src/phonologyrewrite.py` (rules loader, in-memory rewrite, `STENALGO_PHONOLOGY_REWRITE`, default off), `resources/phonologyOverrides.tsv`
  (9 `phonology` rows, 9 `elided` rows), the hook `_rewritten` in `util/_theoryio.py` (both theory loaders; never pickled; flag and file md5 in the
  DisambiguatedTheory fingerprint), `_placeElidedRightAfterBase` and `ELIDED_BASES` in `src/ambiguitychecker.py`, tests `src/test/phonologyrewrite_test.py`.
  Flag off: `pytest src/test/` 1641 passed, `mypy` clean, no output touched.
- PRP4 refinement found while testing: `d'`, `n'`, `m'` carry the lemma of their base in the lexicon (`l'`, `s'`, `t'` have their own), which makes
  the pair a same-lemma one (S6, no star/hash). The rewrite gives every elided form its own lemma (`d'` lemme `d'`).
- PRP19 holds on the real S7: `ce` `s`, `c'` `s*`, `se` `s#`, `s'` `s*#` (the letter `c` falls to `s*#/*#`, two strokes; `j` takes `vt#`, `qu` `k*#`).
- Measured (flag on, the shipped affix abbreviations and briefs NOT regenerated, `scratch/overrides/export_flag_dictionary.py` +
  `compare_theories --stenalgo-dict`): 0 collisions, dictionary alone (long form) 281.115 -> 273.076, **short form 255.156 -> 247.116** (Pluvier 253.186,
  PRP18 target met by the overrides alone), 1.166 strokes per word unchanged. The earlier cheap-route set (`Z/onset,d/onset,°,E`, 250.812) is superseded
  as a baseline; the optional sets must now be searched on top of these overrides.
- `me`/`m'`/`mm` (2026-10-21, solved): `me` came out `m*`, `m'` bare. Cause: the lexicon's junk NOM `me` (freq 2.6, plural `mes`) is merged with the pronoun
  `me` by the same-spelling homograph exemption, so the node inherited `mes`'s conflicts with mais/met/mets, and mais (5179) took the bare code first;
  `m'` conflicts only with me/mm and, coloured greedily after me, reused the bare code. Fix: a `drop` row kind in `resources/phonologyOverrides.tsv`
  (`drop me NOM`). Real S7 now: me `m`, m' `m*`, mm `m*#`; every base (je te se le ce de me ne que) is bare, every elided form follows its ruling.
  pytest 1643 passed, mypy clean (flag off).
  Still open: The expression layer, the trainer exports and the `.stenalgo` data were not rebuilt under the flag. `j'`, `c'`, `qu'` have frequency 0 (no lexicon row).
- Schwa-merge study (rejected as a main lever, 0.4 cost per word on the short form): `docs/SCHWA_MERGE_STUDY_2026-10-20.md`.
- Next: step 2 (optional-phoneme sets on top of the overrides), then the rest of the CP-SAT input (placeholders, PRP16 group keys).

## 6. Update 2026-10-21: the layout statistics from a theory are built and proven (uncommitted)

- **PRA1 decision (user, 2026-10-21): the top-200 cut stays as today** (weight 0, the other briefs avec/ici... are generated later by the pipeline),
  **except the nine spellings whose phonology the overrides force** (`je te se le ce de me ne que`): they count with their forced phonology. The "weigh
  the whole top-200" suggestion of PRA1 is NOT applied. The elided forms (`j' c' qu' ...`) are not in the top-200 and count by themselves.
- Code: `src/layoutstatistics.py` (`buildSyllableStatistics`, `wordsOfTheory`, `layoutInput`, `ambiguityTables`, `canonicalStatistics`, save/load),
  `Dictionary.analyseSyllabification` is now a caller of it, `util/build_layout_statistics.py` (writes the gitignored, self-contained
  `LayoutStatistics.pickle`, ~700 KB), `util/optimize_keyboard.py --statistics PATH`, proof `util/check_layout_statistics.py`, tests
  `src/test/layoutstatistics_test.py`. `Dictionary.pickle` is never touched.
- Proof (`python -m util.check_layout_statistics`): (1) a fresh lexicon build reproduces `Dictionary.pickle`'s statistics (0 differences of content, order lists
  identical); (2) the words of the ORIGINAL `PhoneticTheory.pickle` reproduce them too (0 differences; 268402 distinct words in both). Two optimizer outputs
  are not deterministic across processes and are compared loosely: the best-permutation string (it starts from a set, so it follows the hash seed; its scores
  agree) and the pairwise order scores (differences ~1e-13).
- Rewrite effect on the onset weights (nucleus and coda unchanged): Z +25,988, d +25,221, l +16,954, n +13,357, s +10,772, m +4,929, k +4,101, t +4,006
  (268401 words: `me` NOM dropped). The `Z` onset weight goes from 21,988 to 47,977.
- Environment note: this session's shell had no `python` and no ortools; a venv in the scratchpad was built from `requirements.txt`. With that venv,
  bare `mypy` reports 87 errors, all in `src/cpsatsolver.py` and `src/featuregroupingsat.py` (the ortools 9.15 stubs have no `CpModel.Add`...), none in the new code.
- **Remote-run tooling (built the same day, uncommitted)**: `SolverSettings` in `src/cpsatsolver.py` (time, workers, seed, log, incumbent file, report file; the
  defaults are the historical run), `optimize_keyboard --parts/--time/--workers/--seed/--log/--incumbent-dir/--report`, `util/merge_layouts.py` (per-part layouts back into
  one, validated: each part's phonemes assigned once, keys of the part only; refuses to overwrite the seed), `util/package_remote_solve.py` (a 0.2 MB tar.gz with
  `run_remote.sh`, which runs one process per part with the cores split 5:5:2, then merges). Tested from an extracted package with no repo files visible:
  90 s per part gave `result/merged.json`. `src/test/remote_solve_test.py` guards the import closure (no `dictionary`, `ambiguitychecker`, `_theoryio`).
- Observed with the rewritten statistics, a few minutes each (NOT a result, only the noise to expect): onset objective 799,396 (16 cores, 90 s), 1,021,702 (4 workers, 60 s),
  281,040 (6 workers, 90 s); coda 10,188,503 in all three runs (probably the seed's own cost: no improvement found); nucleus 57,565,840 in all three. The onset
  bound stays very negative (about -30 M) at these times, so its relative gap is meaningless short of a long run; gaps of 47% (onset) and 7% (coda) were seen at 30 min on 16 cores.
  A 20 s limit finds no onset or coda solution at all (UNKNOWN, no layout written).
- **Incumbent files, known gaps** (`--incumbent-dir`, one `incumbent_<part>.json` per part, a full layout file that `util.merge_layouts` accepts, rewritten at most every
  5 s on improvement): (1) the write is not atomic (a kill during it can leave a truncated file); (2) an improvement inside the 5 s window of the last write is lost if
  the process dies before the next one; (3) only the latest solution is kept; (4) no resume: `optimize_keyboard` always hints from `starboard3h.json` (`SEED_PATH`), so a
  restart cannot start from merged incumbents. Planned: atomic write (temp file + `os.replace`), a final flush, and `--seed-layout PATH`.
- Still to do: the control solves of the original statistics (the noise floor, PRA4) before reading any layout difference as an effect of the rewrite; the optional-phoneme
  sets and keypress-group placeholders in the statistics (PRP5, PRP11), PRP16 group keys.
