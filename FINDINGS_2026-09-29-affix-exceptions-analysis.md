> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Findings 2026-09-29: where the affix rules' exceptions come from (H/M/L sweep, fixed lexicon)

Written for a reader with no memory of the session. Data: `scratch/affix-sweep/{L,M,H}/affix-rules.tsv`
(committed 7c0ee5f), `scratch/affix-pool.pickle`. All numbers below are reproducible with the scripts
listed in section 7. Frequency units = the lexicon's carrier frequency (same as `strokeFreqSaved`).

## 1. L/M/H at a glance (30 rules each)
| | forms | word exceptions | exception freq | carrier words | credited saving @30 |
|---|---|---|---|---|---|
| L (alpha 1, excl 5, form 10) | 90 | 722 | 2,121 | 21,781 | 61.4k |
| M (1, 50, 100) | 79 | 950 | 3,297 | 31,368 | 68.7k |
| H (2, 150, 300) | 60 | 1,598 | 3,017 | 71,436 | 97.9k |
Per-rule table: `scratch/affix-sweep/weights-comparison.md`. All-rules covered/exception table (words + freq
per rule per setting): `scratch/coverage-exceptions.json` (fields covW covF excW excF othW othF; 30 rows each,
all matched) — **the user asked for this table and it was never displayed**.
Overlap: 8 rules in all three settings, 14 only L, 5 only M, 10 only H. H chooses broad high-frequency rules
(dé, en, re, é, in/im, ter, té); L chooses many narrow rules. No L/M/H choice made yet (I recommended H
because it has the fewest forms/exclusions; the user has not decided).

## 2. Exception kinds (H, 1,598 words / 3,017 freq)
- Physical trap (`standaloneTrap`): 911 words / 761 freq (57% of words, 25% of freq).
- Collision (`markCostTooHigh` / `lostDistinction`): 687 words / 2,256 freq (75% of freq).
The frequent exceptions are collisions with other words' outlines and have no first-stroke key signature.
Top H exception-frequency rules: e|hi|hy|i|y|î 537, cer|cé|… 520, é 502, ai|aî|… 326, re 288, dé 263 (these six
= 81%). Rule-by-rule exception freq of `cer`, `e|hi…`, `é`, `ai` is almost all collision.
Removing rules 1-4 by exception freq (`scratch/h_prune_experiment.py`): a rule's exceptions do NOT depend on
other selected rules (verified: 26-rule run = baseline minus exactly those rules). Refilled to 30: exceptions
1,338 w / 1,156 f, credited saving 91,387 (vs 97,884); 26 rules: 1,292 w / 1,132 f, saving 85,901.

## 3. `ment` in L (103 exceptions, freq 976.7) vs H (1)
L's rule is the merged `man|mand|mant|ment|ments|mmant|mment` (6 forms, 2,909 words, key (16,20)); H's is
`ment` alone (2 forms, 2,724 words, key (20,25)). L: 97 markCostTooHigh + 6 standaloneTrap; `moment` alone is
403 freq (41%). Causes (inferred from collision partners, not isolated): H excludes the man/mand/mant words
(they stay outside the rule, not exceptions), FORM_COST 300 forbids the 4 extra stem-pattern forms whose
shortened outlines collide, and the keys differ. List: `scratch/ment-exceptions.json`.

## 4. Splitting a rule into two keys — rejected by the user
Tested phoneme-based and first-stroke-key-based splits (`scratch/split_rules*.py`, logs `scratch/split-rules*.log`).
Exceptions fell 30-80% but each split adds a key + a condition; **user decision: forget splitting, it does not
make learning easier.** Do not retry. Useful residue: for `en`, the class "first stroke has coda k, n or m"
(keys 18, 22, 25) removes ALL 134 exceptions (4 left) — see 5.

## 5. Mechanism of the physical failures (`_newBase`, `src/affixes.py:1422`)
A RULE binding ORs its keys into the stem's first stroke (prefix: `base[hi]`; suffix: `base[lo-1]`).
- `keyOverlap`: ANY key of the rule already in that stroke (line 1438, `set(neighbour) & set(binding.keys)`),
  partial or complete. `illegalChord`: the union is not a legal chord.
- Fallback = the rule keys as a stand-alone stroke. For span 1 (every k=1 anchor) that gains nothing, so the
  code returns `standaloneTrap` and the word is an EXCEPTION (written with its ordinary outline).
- `en` (rule key coda k+n = keys 18+22; layout: coda 17=s 18=k 19=d 20=t 21=R 22=n 23=l 24=Z/G 25=m; ɲ = 20+22):
  134 exceptions = 84 keyOverlap (first stroke has coda n: entraîne, enchaîne, enseigne [ɲ], or coda k: entracte)
  + 50 illegalChord (first stroke has coda m/R…: enferme, enflamme, endorme). The vowel E is NOT the cause.
  For entraîne the overlap is PARTIAL (n present, k absent): merged chord (7,8,13,14,18,22) is legal and no
  other word has that outline — `keyOverlap` is a conservative modelling choice here, not a physical necessity.
  For a single-key rule, complete overlap really means union == bare stem outline (collides with the stem).
- DESIGN_2026-09-27-affix-rule-selection.md §4.2 says physical fallbacks "are not exceptions", but for span 1
  the standalone is unavailable so they ARE `standaloneTrap` exceptions. Possible design/implementation
  mismatch: ask the user before changing anything on that basis.

## 6. Scope conditions and the partial-overlap experiment (the pending proposal)
Scope condition (`scratch/scope_prune.py`, `scratch/scope-prune.json`): "rule does not apply when the first
stroke contains key K" for keys failing >=90% (>=2 trap words). 13/30 H rules get one, covering 584 of 911 trap
words; residual 1,014 words / 2,521 freq (-37% words, -16% freq); lost saving 11 of 113,914. Clean: en -> 0,
pa 88 -> 0, pro 52 -> 0, par 2 -> 0. Nothing for the collision exceptions.

Partial-overlap relaxation (`scratch/overlap_relax.py`, log `scratch/overlap-relax.log`; in memory, keys held
FIXED, only fail when ALL rule keys are already in the stroke, collision check kept): over the 25 listed H rules
exceptions 1,039 -> 783 words (en 134->56, in/im 88->39, pro 52->7, pa 88->64) but exception freq ~2,303 ->
~2,309 and saving 93,985 -> 93,975: the removed exceptions were rare words, the new ones frequent (ai|aî… freq
326 -> 422 and saving 4,197 -> 4,026; de (18,20) 0 -> 6). Rule changes are independent per rule (no cross-rule
effect); the deterioration is a rule colliding with itself. Relaxing changes key choice (chooseRuleKeypress and
its prefilter `_exceptionRateFloor`, `bindKeypresses`/`_jointLoss` all use the same overlap test), so the real
effect needs a full re-optimised sweep.

## 7. Scripts and outputs (all under scratch/, untracked except where noted)
Speedup (committed 93a36eb): `choose_bench.py` (+ `choose-baseline.json`), `bound_tightness.py`,
`profile_choose.py`, `profile_rules.py`. Analyses: `weights_comparison.py`, `coverage_exceptions.py`,
`ment_exceptions.py`, `ment_why.py`, `h_prune_experiment.py`, `split_rules.py`, `split_rules_keys.py`,
`en_detail.py`, `en_detail2.py`, `en_words.py`, `en_collide.py`, `scope_prune.py`, `overlap_relax.py`,
`cluster_fusion_scope.py`, `same_ortho_scope.py`. Rebuilding a selected rule from a TSV row: see the matching
loop in `scope_prune.py` (match `carriers` and `wordExceptions`), weights set via `R.EXCEPTION_ALPHA/EXCLUSION_COST/FORM_COST`.
Baseline sweep outputs (must stay identical with the flag OFF): `scratch/affix-sweep-baseline-2026-09-29/`.
