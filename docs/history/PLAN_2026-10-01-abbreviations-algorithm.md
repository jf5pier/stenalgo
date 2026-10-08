# Abbreviation rules — phased algorithm plan (2026-10-01)

Companion documents: complexity analysis in
`PLAN_2026-10-01-abbreviations-complexity.md`; open design choices in
`QUESTIONS_2026-10-01-abbreviations.md`. This round: documents only; the
phases below start after the question file is answered (round 2).

Goal: common words/expressions in fewer strokes via (a) whole-expression
briefs (one stroke, e.g. "il est", "il y a") and (b) attach keypresses
(constant extra keys merged into a host's first/last stroke, e.g. "de la +
mot", "ne + verbe + pas"), composable ("il y a" + ne…pas ⇒ "il n'y a pas" in
one stroke when the union is legal and free).

## Decisions registered (round 2, 2026-10-01 — see the questions file)

- Composition first (Q1); separate expression budget ~10–20 (Q4); explicit
  pair bonus for composability, weight set in Phase 2 (Q5); queue floors
  ≥2 strokes and ≥5M occurrences (Q6); no shadowing — canonical distinctness
  from all live outlines (Q7); multi-stroke briefs allowed with
  `hasBoundaryRisk` gates (Q8); mnemonic AND free-chord derivations,
  `keySimilarity` a label only (Q9); attach rules productive over any host
  (Q10); 2010–2019 window ranks candidates (Q11); standalone-stroke fallback
  on merge failure (Q12).
- **Rule families (Q2)**: base keypresses on the 22 phoneme keys; `*` (10)
  and `#` (15) may join a keypress only to give semantically related
  particles ONE shared rule with mark-style variant selectors
  (`du / de la / de l' / des` = one rule + `*`/`#` variants); keys 0/1 stay
  excluded. Phase 1 must extend the algebra and Phase 2 the selection model
  with this family notion (one learnable unit, several variant strokes).
- Circumfix semantics DECIDED (Q3, 2026-10-01, user pick after the Phase 2
  experiments): **Option C — decomposition with disjoint keys**. A
  circumfix stays two attach rules (prefix + suffix); Stage C's repair
  forces co-occurring families onto syllabically disjoint keypresses so
  both merge into one stroke (ne…pas contexts 31%→78% fully saved, pool
  12.4%→13.2%). A dedicated one-keypress circumfix rule (Option B) was
  measured and rejected: its edge over C is only the residual 8.5% of
  ne…pas mass, at the price of a new learnable unit, a budget slot, and
  non-contiguous expressions in the algebra.

## Phase 0 — dependency merge + candidate pool

**Inputs**: branches `abbreviations` (ae6ad5d) and `affix-abbreviation-rules`
(755b4f2, 8 commits: growth scopes, fusions, sweep speedups — the scope engine
this work builds on); `scratch/tao_abbreviations.txt` (567 entries, 121
multi-word); `scratch/top_ngrams/*.tsv` + orgtre intermediates;
PhoneticTheory/DisambiguatedTheory pickles; `util/ngram_data.py`.

**Work**:
1. Merge `affix-abbreviation-rules` into `abbreviations` (a merge, not a
   rebase — both sides have real commits; check `git merge-tree` first; the
   conflict surface is src/affix*.py vs scratch/util additions, likely
   disjoint).
2. Close the 466/567 tao coverage gap: widen the slices or add a point-query
   mode to `scratch/rebuild_ngrams.py` scanning the orgtre intermediates for
   exact entries.
3. Build `scratch/expr_candidates.tsv`: expression (word-units), frequency,
   per-word phonologies, longform Strokes, stroke/syllable counts, flags
   (in-tao, elision-bearing, particle-glued).

**Reuse**: `rebuild_ngrams.py` word-unit normalization as-is; the theory
pickles for outline lookup.

**Verification**: coverage count against 567; every candidate resolves to a
Strokes sequence (drop + log words missing from the theory); top-20
frequencies spot-checked against the Ngram Viewer client (`util/ngram_data.py
query`, corpus id 30).

## Phase 1 — composition algebra

**Inputs**: `expr_candidates.tsv`; constraint set §3.5 of the complexity doc.

**Work**: the rewrite semantics as a spec plus a pure function
`composeOutline(rules, tokens) -> Strokes | Failure` implementing:
longest-match segmentation, brief substitution, attach merges (prefix → first
stroke, suffix → last stroke, union on single-stroke hosts), the fallback
ladder, and the canonical normal form.

**Reuse**: merge arithmetic from `composeReservedKeyStrokesForEntries`
(src/ambiguitychecker.py:480); the merge/fallback ladder from `_newBase`
(src/affixes.py:1420-1453); `withMarks` (src/affixes.py:128) for mark
interaction; `canonicalizeStrokes` (src/keyboard.py:35) for identity.

**Verification**: unit tests on the canonical examples — "il y a" ⇒ 1 stroke;
"il n'y a pas" ⇒ 1 stroke or the documented 2-stroke fallback; "de la + mot"
⇒ first-stroke merge; both-sides attach on a brief; key-overlap and
illegal-chord fallbacks; confluence (order-independence property test).

## Phase 2 — selection, keypress assignment, collision audit

**Inputs**: Phase 1 algebra; Phase 0 pool; `SimContext` over the full theory.

**Stage A — selection: greedy budgeted, in the `selectRules` tradition.**
One priority queue where briefs and attach rules compete by marginal
frequency-weighted saving under the budget; `bestS`-style credit (a token's
saving counts once); `territoryMate`/RULE_OVERLAP_MAX = 0.5 skips the losing
side of contests like "n'est pas"; `swapPass` (3 passes × 20 candidates)
repairs supermodular mis-orderings.
*Why not CP-SAT for selection*: the objective is non-linear through
composition (no static weights precomputable), the expensive exact stage must
run lazily for heap tops only, and the CP-SAT template's strength (exact min-K
over ~7 markers with hard distinctness) does not transfer to ~1,300 candidates
× 1,751 keys.

**Stage B — keypress and brief-stroke assignment.** Attach rules:
`chooseRuleKeypress` as-is (every legal keypress, stage-1 on sample carriers,
5% exception gate; `keySimilarity` as a label, never a gate). Briefs: the
analogous "keypress" is the whole brief stroke; enumerate from mnemonic
derivation families (unions of member words' first-stroke keys;
initial+final skeleton; vowel skeleton; rule-key ⊕ salient host keys), each
checked for legality and similarity-labeled.

**Stage C — joint repair + audit.** With the selection fixed, a CP-SAT pass
in the `featuregroupingsat` tradition (`_buildDistinctnessModel` + priority
tiers + `_breakTiesAlphabetically`) re-assigns keypresses to remove union-trap
collisions among co-occurring rules, deterministically. Full collision audit
via the `_feasible` pattern against phoneticTheory + disambiguatedTheory (all
entries), plus `hasBoundaryRisk` on every multi-stroke output.

**Verification**: invariants (one keypress per rule across all hosts; global
outline injectivity; budget respected); determinism (fixed sort keys, re-run
stability); monotonicity spot-check (removing any selected rule lowers the
total).

## Phase 3 — simulation + report

**Inputs**: selected rule set; the Phase 1 composer.

**Work**: generalize `SimContext`/`simulate` (src/affixes.py:1383-1523): a
whole-expression brief is the degenerate carrier (`start=0, span=len(base)`)
— the existing Carrier mechanics apply unchanged, including `baseIndex`
cross-collisions and mark costs; attach rules compose through the Phase 1
function. Cross-rule interactions (composability, co-collision) come free
from `simulate`'s shared `pending` index.

**Outputs**: `scratch/expr-rules.tsv` mirroring affix-rules.tsv columns
(rank, kind, expression, keys, rtfcre, score, strokeFreqSaved,
keySimilarity, wordExceptions, topExceptions, examples) plus a `composedWith`
column and a small composability matrix (which rule pairs compose, with
worked examples like "il n'y a pas").

**Verification**: totals recomputed by `simulate`; hand-check a 10-rule
sample including one fallback case; report round-trips (parse → identical
Strokes); before/after aggregate strokes-per-million-words on the top slices.

## Phase 4 — wiring into the theory build (named, out of scope for now)

Integrate into the disambiguated theory build (`util/build_disambiguated_theory.py`)
and the Plover export (`util/export_plover_dictionary.py`): tokenizer-level
expression matching with elision handling, dictionary-entry conflicts, and
regression tests over the full theory. Nothing in the current pipeline reads
affix or abbreviation rules — this phase is where that changes, for both
workstreams together.

## Rule-of-thumb priorities (from the measured data)

1. "de la" (202M), "de l'" (118M), "à la" (80M), "c'est" (79M), "qu'il"
   (68M) — the top of the 2-gram file is where a handful of rules buys the
   most strokes; prefix-attach candidates dominate.
2. "n'est pas" (18.3M), "il y a" (10.2M) — the brief/attach contest cases.
3. "ce n'est pas" (5.8M), "il n'y a pas" (1.76M) — pure composition wins:
   worth strokes only if their factors are already rules.
