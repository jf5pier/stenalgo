# Abbreviation rules — complexity of the problem (2026-10-01)

Whole-expression briefs ("il est" → one stroke) and attach keypresses
("de la + mot" → extra keys on mot's first stroke; "ne + verbe + pas" → extra
keypress at the end of verbe). Companion document: the phased plan in
`PLAN_2026-10-01-abbreviations-algorithm.md`; open design choices in
`QUESTIONS_2026-10-01-abbreviations.md`.

## 1. Ground data and decision variables

A word's final outline is `Strokes = tuple[Stroke]`, one stroke per syllable
(`getStrokeOfSyllableByPart`, src/keyboard.py:648), plus disambiguation marks
merged into the last stroke by `composeReservedKeyStrokesForEntries`
(src/ambiguitychecker.py:428-481; the merge arithmetic at line 480 is
`strokes[:last] + (strokes[last] + extra[0],) + strokes[last+1:] + extra[1:]`).
An expression's longform outline is the concatenation of its member words'
final outlines. Frequencies come from `scratch/top_ngrams/*.tsv`, whose
word-unit rule already matches the theory's unit count (elision particles
count as words: `c'est` = 2 units, `il n'y a pas` = 5).

Decisions to make:

- **Briefs**: for each candidate expression `e` (pool ≈ 1,200–1,500 from
  tao ∩ n-grams + top slices), whether it gets a whole-expression brief, and
  which brief stroke `β(e)` from a small mnemonic derivation family.
- **Attach rules**: for each candidate particle/particle-group `p` ("de la",
  "ne…pas", …), whether it becomes an attach rule, with position class
  `π(p) ∈ {prefix, suffix, circumfix}` fixed per candidate.
- **Keypresses**: for every selected rule, the constant keypress
  `κ(r) ∈ K`, from the legal-keypress universe (~1,751 chords over the 22
  phoneme keys; `enumerateKeypresses`, src/affixbinding.py:103-110).

## 2. Objective

Maximize

```
Σ_tokens freq · (strokes_longform − strokes_with_rules)   ← savings
  − λ · |rules|                                           ← learnability
  − Σ per-rule form costs (exceptions, fallbacks, forms)
```

the `ruleScoreFromResults` shape (src/affixrules.py:172-188: benefit −
EXCEPTION_ALPHA·exceptionFreq − EXCLUSION_COST·exclusions − FORM_COST·extra
forms; decided weights 2 / 5 / 100), extended with a composition-credit term
(open question 5).

## 3. Hard constraints

1. **Constant keypress**: one `κ(r)` per rule for all hosts — never per-host.
2. **Chord legality**: every produced stroke legal per bank
   (`SimContext.isLegal` → `getStrokeCost`, src/affixes.py:1398-1417).
3. **Collision-freedom**: every new canonical outline distinct from every
   `phoneticTheory` key and every `disambiguatedTheory` value (primary and
   alternates) — the `_feasible` pattern (src/ambiguitychecker.py:1040-1078),
   including the union trap (lines 1000-1008): two rules individually clean
   can collide as a union on one host.
4. **Rule budget**: integer cardinality constraint (interaction with
   RULE_BUDGET = 30 is open question 4).
5. **Well-defined composition algebra** (the semantics Phase 1 pins down):
   - Segment the token stream longest-match-first over briefed expressions;
     unsegmented words keep their outlines.
   - Prefix attach merges `κ` into the segment's **first** stroke; suffix into
     the **last** — same tuple arithmetic as ambiguitychecker.py:480.
   - *Brief meets suffix keypress*: the brief stroke is the host's last stroke
     ⇒ `β'(e) = sorted(β(e) ∪ κ)`. "il y a" + ne…pas lands in ONE stroke if
     the union is legal and collision-free.
   - *Prefix and suffix both attach*: ≥2 strokes → different strokes; single
     stroke (a brief) → one chord.
   - *Failure ladder* (reusing `_newBase`, src/affixes.py:1420-1453): key
     overlap or illegal union → standalone attach stroke (the RULE-kind
     fallback, saves span−1) → else full-form exception (gain 0, counted
     against the 5% exception gate, MAX_EXCEPTION_RATE, affixrules.py:30).
   - *Confluence*: merges are set-unions at fixed stroke indices, so
     application order is irrelevant; the normal form is unique. Multi-stroke
     briefs additionally carry boundary risk (`hasBoundaryRisk`,
     src/affixes.py:1456-1466): a 2-stroke form splittable into two existing
     outlines is ambiguous with writing the two words separately.

## 4. Why this is combinatorially hard — six interacting sources

**(a) Candidate space.** ~1,200–1,500 expressions (567 tao entries, 121
multi-word, 101 already matched in the current slices; top: en 362M, dans
254M, pour 210M, pas 206M) × 8–16 brief-stroke derivations × ~1,751 keypresses
per attach rule ⇒ joint space beyond 2^1200. No exact search; laziness
(evaluate expensive stages only for heap tops, as `selectRules` does) is the
only affordable strategy.

**(b) Rule-class contests with supermodular complementarity.** The same tokens
are contestable: "n'est pas" (18.3M) as a brief vs `ne + est + pas` via the
attach rule; "de la" (202M) as a brief vs a prefix attach on hosts. Worse
than overlapping: complementarity is supermodular — adding brief("il y a",
10.2M) RAISES the value of attach(ne…pas), because "il n'y a pas" (1.76M)
compresses to one stroke. Supermodularity breaks the approximation guarantees
greedy enjoys on submodular objectives; the mitigations are marginal-credit
bookkeeping (`bestS` in `selectRules` — each carrier's gain counted once) plus
swap-repair passes, with residual risk stated honestly in the report.

**(c) Keypress assignment as coloring with host-dependent forbidden lists.**
A keypress shared by two rules is fine on disjoint hosts and fatal on
co-occurring ones (the union trap again). This is graph/list coloring — what
`featuregroupingsat._buildDistinctnessModel` (src/featuregroupingsat.py:48-103)
encodes for the elicitation markers — except our colors carry forbidden lists
that depend on which hosts each rule touches. And the mnemonic objective
(keypress shares keys with the longform) actively misleads as a selector:
measured on the `re` prefix, the top-similarity key (rank 27/1751) had an
18.7% exception rate while a near-zero-similarity key (rank 926) scored 41%
higher (src/affixrules.py:205-213). Similarity stays a label for human
review, never a gate.

**(d) Collision audit surface.** 190,254 disambiguated entries (~167k words
with alternates) + 79,624 phonetic outlines. Each candidate outline needs
canonicalized distinctness against all of them (cheap hash lookups, but it
multiplies the candidate space) — this is why keypress choice cannot be
factored out of selection.

**(e) Composability as an endogenous objective.** Value(rule) is a function of
the selected set: the fixed-point property means greedy stages must recompute
marginals against the *current* selection (exactly `selectRules`' stage-2
"recomputed fresh" rule, affixrules.py:503-508). A precomputed pairwise
interaction table would be both huge (O(|rules|²) compositions) and wrong once
a third rule changes a shared host's outline.

**(f) Non-numeric learnability constraints.** The constant-keypress
requirement is the single biggest combinatorial restriction — it turns
per-host optimization into covering-with-a-shared-resource and makes
exceptions (hosts where the constant key fails) a first-class cost. The rule
budget is an integer constraint on a set whose members' values interact.
Human checkability demands deterministic output and explainable per-rule
provenance — the priority-tier + alphabetical tie-break discipline of
featuregroupingsat (`_breakTiesAlphabetically`, line 150).

## 5. Structural summary

Selecting briefs under collision-freedom is weighted independent set; with the
budget it is budgeted maximum coverage. Choosing a dictionary of briefs +
attach rules minimizing total output strokes is the frequency-weighted
smallest-grammar problem — NP-hard and poorly approximable in general. Joint
keypress assignment with co-occurrence distinctness is graph coloring with
instance-dependent lists. No single exact formulation is tractable; the plan
therefore stages the problem (see the companion document) so that each stage
is either a known-good greedy (selection), an enumeration with gates
(keypresses), or an exact solve at tractable scale (the CP-SAT repair pass).
