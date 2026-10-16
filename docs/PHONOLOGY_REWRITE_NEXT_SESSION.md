# Phonology rewrite — transition to a new session (written 2026-10-16)

Read, in this order: this file, `docs/PHONOLOGY_REWRITE_SESSION_2026-10-15.md` (study results, sections 1-7), `docs/PHONOLOGY_REWRITE_PLAN.md`
(decisions P1-P18; P18 restated 2026-10-15), `docs/PHONOLOGY_REWRITE_BLIND_SPOTS.md` ("Settled" section), glossary section "Phonology rewrite"
(long / reduced / short / shortest form). Nothing is committed: the docs, `docs/GLOSSARY.md` and the scratch scripts are untracked or modified.

## 1. Where the study stands

- Vocabulary (user): **long form** = full phonetic outline; **reduced form** = long form with optional phonemes dropped; **short form** = affix/brief/other
  rules on top; **shortest form** = best short form.
- Candidate set, chosen by the greedy search and judged on teachability: **`Z/onset, d/onset, °, E`**. On the FIXED layout, with the existing affix
  abbreviations and briefs as claimants and NOT regenerated: shortest form 250.812 vs 255.156 today vs Pluvier 253.186 (P18 target < 253.19 met).
  Larger sets (+`t/onset`, `l/onset`, `n/onset`) reach 249.155 but only 45-54% of the spellings carrying a variant are reduced (4-18% by frequency):
  the rule turns into a list. Not retained.
- Boundary risk (C4) of the 4-variant set: swallow pairs 13.7% (shipped single-stroke outlines: 31.8%); splittable multi-stroke outlines 70.0% vs 56.7%.
- The frequent function words (je, de, le, ne, ce, est, les, des, mais, elle...) are the exceptions to every drop rule; the gain comes from rare words.

## 2. What is NOT decided (answer to "which phonemes are optional for each word?")

**No per-word optional set exists yet.** The cheap route (`optexp_reduced_outlines.py`) applies a *global* set of variants and keeps, per spelling, the
phoneme whenever the reduced outline would collide (a fixed-point iteration against the fixed outlines of the shipped theory). That is an
estimate, not the P5 optional phoneme set: P5 requires the test to be symmetric (no frequency priority), over EVERY combination of the word's optional
phonemes against every combination of every other word's, on the full phonology with the keypress-group placeholders and the current marks (A3).
A word can have up to 4 optional phonemes (a spelling with Z, d, schwa and E at once); the number of combinations is the lever (P6 candidate cap).
Also open: which of the two outlines (full or reduced) counts as "typed" for the CP-SAT weights (P7 says both are valid; P11 weights by what is typed;
proposal: the cheapest valid outline is the typed one).

## 3. Decision taken at the end of this session (user)

Regenerating affix abbreviations and briefs on the reduced forms is **premature**: the layout may change. The next step is the CP-SAT input; only
after the solve is it worth rebuilding abbreviations and briefs. Order:

1. **Generate the alternate phonology of each affected word** (the P5 optional phoneme sets for the 4 variants, symmetric, all combinations, placeholders and marks
   included) and commit them as a sets file (B1/B12: `resources/` committed file, revalidated each build, rewrite applied in memory after the pickles load,
   behind `STENALGO_PHONOLOGY_REWRITE`). The phonology overrides of P3 (`je`→`Z`, `te`→`t`, ... elided ranking) belong to iteration 1 and interact with
   `°`/`Z/onset`/`d/onset`: decide whether they go in first.
2. **Build the CP-SAT input** (P11): rewritten phonology + keypress-group placeholders, frequency weights of what is typed (left-out occurrences and retired
   phonemes do not count), top-200 words weighted except the 34 briefed ones (A1; today `nbFrequentWords`, `dictionary.py:79`, weighs them 0). Entry point: a
   variant of `util.optimize_keyboard` / `src/cpsatsolver.py`; seeded from `starboard3h.json`; writes a separate layout file, never `starboard3h.json`.
3. **Solve** (A4): nucleus is OPTIMAL in 25 s; onset and coda do not converge in 30 min on 16 cores (gaps 47% and 7%), so long solves belong on the 192-core
   machine, to convergence, for the top candidates only. Harness used so far: a copy of `src/cpsatsolver.py` with `SOLVER_TIME = 1800.0`, `SOLVER_LOG = True`
   (statuses: 2 FEASIBLE, 4 OPTIMAL); `SOLVER_TIME = 90.0` is a local constant in `optimizeKeyboard`.
4. **Judge**: does the layout change, and acceptably (learnability: how many phonemes move; objective vs committed layout; P18 on a rebuild)?
5. **Then one of two branches**: (a) change the number of phoneme keys per part (onset 2-9, nucleus 11-14, coda 16-25, `keyIDinSyllabicPart`; P15, part split)
   and re-solve; or (b) keep the layout and move on to regenerating the affix abbreviations and briefs (`build_affix_rules`, `build_briefs --rederive`) on the reduced forms,
   then compare the shortest form (P18).

## 4. Tools and facts

- Scratch scripts (untracked, `scratch/optimisation_exploration/`): `optexp_reduced_outlines.py` (`--phonemes "A,B;C"`, `--long`, `--tag`; prints per-variant
  rule coverage; writes `out/dictionary_long_*.json` or `out/reduced_outlines_*.tsv`), `optexp_reduced_greedy.py` (~25 min per step), `optexp_reduced_boundary.py` (5 s).
  Real check: `python -m util.compare_theories ... --stenalgo-abbreviations affix_abbreviations.tsv --stenalgo-abbreviations briefs.tsv --stenalgo-abbreviations out/reduced_outlines_<tag>.tsv`
  (Pluvier arguments from CLAUDE.md, `../Pluvier/resources/`). Estimates match the real metric to ~0.2 per word.
- Pickles are current (2026-10-13); `starboard3h.json` is from 2026-10-02. Load of the exploration model: ~65 s.
- Process rules: never wait with `pgrep -f`/`pkill -f` (they match the shell itself); stop background jobs by task id.
- Known clashes dropped by the writer in the 4-variant set: `sRwiek` (dédiait/sciais) and, in larger sets, patois/plaza, extrusion/scrutions, suaient/suintaient.
- Open blind spots still unsettled: B2-B11, C1 (learnability beyond coverage counts: needs the user's view on exception lists), C2-C5, D1-D3.
