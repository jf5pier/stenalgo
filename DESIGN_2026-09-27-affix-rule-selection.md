# Design: affix rule lattice + budgeted rule selection (2026-09-27)

**Audience: the model that implements this after a `/clear`.** The user agreed to this design
on 2026-09-27; the decisions in §1 are theirs. **Don't re-ask them, and don't redesign.** If
something here is ambiguous, pick the default given, note it in your phase report, and
continue. Stop at each **STOP** marker and report to the user before going on.

## 0. Start-up

1. Read, in order:
   - this file;
   - `RESUME_2026-09-27-affix-growth-search-design.md` (the problem this solves; its §5-6 "menu"
     is superseded by this file);
   - `PLAN_2026-09-26-affix-abbreviations.md` §2 (the 10 binding decisions), §4 A5 (gain
     simulation), §4 A7, §13 (A9);
   - all of `src/affixes.py`, `src/affixbinding.py` and `util/affix_scan.py`. They are short:
     read them in full.
2. Environment:
   - Use `env/bin/python`; bare `python` is not on PATH. Run from the repo root.
   - Run the CLI as `PYTHONPATH=. env/bin/python -m util.affix_scan ...`.
   - The machine has 7 GB RAM: run one heavy job at a time. Part A takes about 72 s from the
     records cache.
   - To wait on a background run, use `run_in_background` or a PID. Never use a `pgrep -f`
     loop.
3. **Do not commit or push.** **Do not touch the pipeline** (`dictionary.py`, `util/build_*`,
   the exporters, the pickles, `docs/`). This is measurement tooling only. Every output goes
   under `scratch/`.
4. The tests currently pass: `env/bin/python -m pytest src/test/` gives 674.
   `env/bin/python -m mypy src/affixes.py src/affixbinding.py util/affix_scan.py` is clean.
   Both must stay that way. `mypy src/` as a whole has about 127 pre-existing errors; don't
   chase those.
5. Before changing any code, run the md5 check in §7.3 and save the result as your baseline.

## 1. The user's decisions (binding)

- **D1. Budget.** The theory will contain at most **20-30 rules in total**, prefixes and
  suffixes together. Everything else is dropped.
- **D2. A rule is one thing the human must recognise.** Two unrelated families that happen to
  share one keypress are still **two rules**. Keypress sharing must never influence whether a
  family is kept: each family is judged on its own. **Sideways merging (`unifyFamilies`) takes
  no part in selection.**
- **D3. Learnability means fewer rules with simple logic.** A human can't evaluate a regex in
  their head. Allowed slot forms are exact values, "any onset + fixed vowel(+coda)", and
  wildcards with a *short* exception list (e.g. "any consonant except m" + `ilité`). Arbitrary
  sets of unrelated syllables (`{bER, fR§, ky, li, ni, no, sje, ti}`) are forbidden.
- **D4. Grown affixes belong to their parent's family, as one rule.** `-ité`, `-lité`, `-ilité`
  and `-bilité` all make one rule with one key K. The theory keeps the full outline and adds
  the cheapest collision-free abbreviation.
- **D5. Cut rule (option "a").** K replaces **only a whole form of the family**. The writer
  learns "K = -ité / -ilité / -bilité" and uses the **longest form the word ends with** (for a
  prefix, the longest form it starts with). K never cuts at an arbitrary syllable boundary.
  - Example: `disponibilité` (`dis.po.ni.bi.li.te`), whose longest form is `-bilité`, becomes
    `/dis/po/niK/` if merging K into `ni` is legal, else `/dis/po/ni/-K`.
  - It is **never** `/dis/poK/`, because `ni` is not part of any form.
- **D6. Exceptions lower a rule's score.** An exception is a family word that can't use the
  rule as the writer would apply it. Both kinds of exception count against the score:
  - **Word exceptions:** the word collides with another word.
  - **Slot exclusions:** "except m".

## 2. Architecture change in one paragraph

Today the flow is: A7 and A9 each commit greedily (A9's agglomeration absorbs leaves), then A3
clusters, then `growthMerges` and `unifyFamilies` merge greedily, then `assignGreedy` gives
each family a unique key. The new flow separates **generation** from **commitment**:

1. **Phase 1:** generate a large, overlapping pool of pattern nodes, a lattice where nothing
   absorbs anything.
2. **Phase 2:** turn each root node plus its descendants into one candidate **rule**.
3. **Phase 3:** select at most `RULE_BUDGET` rules by a lazy greedy that credits each word once,
   at its best selected rule.
4. **Phase 4:** assign keypresses to the selected rules; two rules may share a key when that is
   collision-free (D2).

The old path (`growthMerges` → `unifyFamilies` → `assignGreedy`) stays in the code behind a
`--legacy` CLI flag so the two can be compared. **Don't delete it.**

## 3. Phase 1: the pattern lattice (Part A, `src/affixes.py`)

### 3.1 Slots

A node's pattern is the base affix plus zero or more absorbed **slots**, each one syllable,
going toward the stem. Add a small frozen dataclass:

```python
@dataclass(frozen=True)
class Slot:
    kind: str                 # "exact" | "onset" | "any"
    value: str = ""           # exact: the syllable phono (e.g. "li"); onset: the rest (nucleus+coda, e.g. "i")
    excluded: tuple[str, ...] = ()   # values removed from an onset/any wildcard (onset consonants for
                                     # "onset", whole syllable phonos for "any"); len <= MAX_SLOT_EXCLUSIONS
```

A syllable s matches:

- `exact(v)` iff `s == v`;
- `onset(r, excl)` iff `_onsetRest(s)[1] == r` and `_onsetRest(s)[0] not in excl`. Allow an empty
  onset too (`réalité`'s `a`) only if `r` matches; an empty onset is written `""` in `excl`;
- `any(excl)` iff `s not in excl`.

Store the slots on `Candidate` as a new field `slots: tuple[Slot, ...] = ()`. The order is
**outward from the base**: `slots[0]` is next to the base affix, and the last slot is next to
the stem. Keep `phono`/`ortho` as human-readable labels:

- exact `li`;
- onset → `[C]i`, or `[C-m]i` with exclusions;
- any → `*`, or `*-{x,y}` with exclusions.

`phono` must stay **unique per distinct pattern**, because it is part of the candidate key.

### 3.2 Growth step (replaces the greedy agglomeration in `_growOneLevel`)

For a node P, grow each carrier by one syllable with the existing `_growCarrier`. Then emit
**all** of the following child nodes. None of them consumes another; they overlap on purpose.

1. **Exact leaf:** one child per distinct absorbed syllable phono.
2. **Onset group:** one child per distinct `rest`, grouping the absorbed syllables that share
   it, provided at least 2 distinct onsets occur.
3. **Any group:** one child with every absorbed syllable (this is the "full wildcard" the user
   wants tested).

For each onset/any group, make the exclusions **before** the exception check:

- Compute each value's contribution to collisions: the frequency of word exceptions that
  `_exceptionShare` attributes to carriers of that value, when that value is in the group.
- While the group's exception share (against the fixed denominator `denom` = P's grown-carrier
  frequency, as today) exceeds `GROWTH_MAX_EXCEPTION_SHARE`, remove the value with the largest
  contribution and add it to `excluded`.
- If that needs more than `MAX_SLOT_EXCLUSIONS` exclusions, drop the group.
- The removed value's words are simply not carriers of this child. They may still be carriers
  of that value's exact leaf.

For an exact leaf, check `_exceptionShare` the same way (no exclusions are possible). Drop the
leaf if it is above the share.

Delete the pairwise greedy merge loop (`pairScore` …) and `GROWTH_MAX_SLOT_VALUES`. Under D3,
arbitrary subsets are no longer generated at all.

### 3.3 Keep / expand criteria (replace the 7× `GROWTH_MIN_*` thresholds)

The old 7× thresholds existed only to keep Part A under a 300-family ceiling. With D1 (only
20-30 rules ship) that ceiling no longer matters. Delete `GROWTH_MIN_*`.

For a child C of parent P, with carriers W_C (after exclusions and word exceptions are
removed):

- **Marginal gain:** `marginal(C) = Σ_{w∈W_C} f_w × (span_C(w) − span_P(w))`. This is the extra
  stroke-frequency C adds over its parent. It usually equals `Σ f_w`, since the span grows by 1.
- **Emit** C as a candidate iff all of these hold:
  - `marginal(C) ≥ GROWTH_MIN_MARGINAL` (default `MIN_FAMILY_STROKEFREQ` = 30.0);
  - lemmas ≥ `MIN_CARRIER_LEMMAS`;
  - stemRoots ≥ `MIN_STEM_ROOTS` (1× the base constants).
- **Expand** C, i.e. grow it again at the next depth, iff its **subtree bound**
  `UB(C) = Σ_{w∈W_C} f_w × (min(GROWTH_MAX_DEPTH − C.grownDepth, stemSyllablesLeft(w) − 1))`
  is ≥ `GROWTH_MIN_MARGINAL`. `stemSyllablesLeft(w)` is the number of syllables before the
  affix span for a suffix (after it, for a prefix); keep at least one stem syllable, as
  `_growCarrier` already does.
  - A node can be expanded without being emitted. This is the point of the bound: `-lité` must
    survive long enough to reach `-ilité` even if it looks weak on its own.
- Keep `GROWTH_MAX_DEPTH = 3` and the breadth-first order of `growAffixes`.

### 3.4 Dedupe and lineage

- **Dedupe key:** `(position, frozenset((c.rec.idx, c.start, c.span) for c in carriers))`. When
  two nodes have the same carriers and spans (for example `[C]i.te` grown from `-té` and A7's
  pooled `·ité`), keep the one with the simpler pattern: fewer slots, then exact before onset
  before any, then fewer exclusions. Record the other's key in the kept node's `aliases` (a new
  field, `list[tuple[str, int, str, str]]`).
- **`grownFromKey`** keeps pointing at the exact parent. **Also** add
  `rootKey: tuple[str, int, str, str]`, the ungrown ancestor at the top of the chain. Phase 2
  needs it.

### 3.5 A7 becomes non-consuming

`poolTailVariants` currently **deletes** the individual variants it pools (`del pooled[key]`).
This is why exact `li.te` never existed: it was absorbed into `·ité`. Change it to **keep** the
originals alongside the pooled candidate. Each original still faces the ordinary thresholds.
Leave A8 (`poolKnownAffixGroups`) consuming: it is a curated allomorph list, one prefix by
etymology.

### 3.6 Part A output and checkpoint

- `scratch/affix-candidates.tsv` gains these columns: `slots`, `grownFrom`, `root`, `aliases`,
  `marginal`, `exceptionCount`, `exceptionFreq`.
- The old "5..300 families" checkpoint in `util/affix_scan.py` (line ~244) no longer applies to
  the new path. Replace it: stop and warn if the candidate pool exceeds `MAX_POOL` (default
  20,000) or Part A takes more than 10 minutes. Keep the old checkpoint under `--legacy`.
- Add to `scratch/affix-lattice-trace.txt` the full chain for the regression case: every node
  whose ortho ends in `té` and whose lineage contains `li`, printed as a tree with lemmas,
  freq, marginal and UB.

### STOP 1: report to the user

Report all of the following:

- the pool size, and the Part A runtime;
- whether these nodes exist, with their lemmas, marginal and lineage:
  - exact `li.te` (k=2, suffix);
  - a child of it matching `[C]i.li.te` (≈ `-ilité`);
  - a deeper child (≈ `-bilité` / `-Xlité`);
- a few examples of exclusions actually made (`[C-m]…`);
- how many `any` groups survived.

**Don't start Phase 2 until the user says so.**

## 4. Phase 2: rules (new, `src/affixbinding.py` or a new `src/affixrules.py`)

### 4.1 Rule definition

A **rule** is `(root, forms, K)`:

- `root` is a pool node;
- `forms` is a set of pool nodes, each the root itself or a lattice descendant of it (same
  `rootKey` lineage, or aliased to one);
- `K` is one keypress.

Per D5, a family word w (a carrier of any form) is written with the **longest form it matches**
(its largest span among the forms). This is what `poolCarriers` already does ("largest span
wins"). Reuse it.

Forms don't count toward the budget (D4). A rule costs one unit of `RULE_BUDGET` whatever its
number of forms. But each form is one more ending to remember, so it costs `FORM_COST`
(§4.3), and a rule has at most `MAX_RULE_FORMS` (default 4) forms.

**Out of scope for v1:** sibling variants that aren't in a lineage relation (`-able`/`-ible`,
`-eur`/`-euse`). They are separate roots and therefore separate rules. List the cases where two
selected rules look like such siblings (A3 `candidateSim` ≥ `FAMILY_LINK_SIM`) in the report,
for the user to rule on. **Don't merge them.**

### 4.2 How a word is written under a rule (changes to `simulate`)

For a carrier w with its longest-form span `[lo, hi)`:

1. **Merged:** OR K into the neighbouring stem stroke, as today (`_newBase`, MERGED).
2. If merged is infeasible for a **physical** reason (`keyOverlap` or `illegalChord`), **fall
   back to standalone**: the span is replaced by the single stroke `(K,)`, which saves
   `span − 1`. This is the existing DEDICATED path with `D = K`.
   - Standalone is unavailable (the word gets `reason="standaloneTrap"`) if `(K,)` is itself an
     existing single-stroke outline (`ctx.singleStrokeOutlines`), or if span = 1 (no saving).
   - Physical fallbacks are **not** exceptions. The writer can feel that the chord is
     impossible.
3. Collision handling is unchanged (`lostDistinction`, `markCostTooHigh`, mark costs,
   `boundaryRisk`). A word that collides is a **word exception**. Under D5 it does **not** fall
   back to a shorter form: it keeps only its full outline.

Implement this as a new binding kind, e.g. `Binding(position, "rule", K)`, handled in
`_newBase`/`simulate`. Leave MERGED/DEDICATED behaviour unchanged for `--legacy`.

### 4.3 Rule score (D6)

All terms are in stroke-frequency units, the same units as `strokeFreqSaved`:

```
score(rule) = Σ_{w benefiting} f_w × gain_w
            − EXCEPTION_ALPHA × Σ_{w word-exception} f_w
            − EXCLUSION_COST × (total slot exclusions over the rule's forms)
            − FORM_COST × (len(forms) − 1)
```

Defaults: `EXCEPTION_ALPHA = 1.0`, `EXCLUSION_COST = 5.0`, `FORM_COST = 10.0`. These are
placeholders, tunable, and reported in the output header.

- **Word exceptions** count collision fallbacks only (`lostDistinction`, `markCostTooHigh`,
  `standaloneTrap`). They don't count `keyOverlap`/`illegalChord` words that went standalone.
- Also report, per rule, the word-exception count and the top 10 exception words by frequency.
  The user will read these.

### 4.4 Building one candidate rule per root

Every pool node is a potential root. For root R:

1. Start with `forms = {R}`.
2. Repeatedly add the descendant (or alias-descendant) of R that most increases `score`. At
   this stage, use the **Part-A proxy score**: `Σ f × span` minus `EXCEPTION_ALPHA ×`
   `_exceptionShare` frequency, minus the form and exclusion costs. The keypress isn't known
   yet.
3. Stop when no addition increases the score, or when `MAX_RULE_FORMS` is reached.
4. Then choose K with the existing Part B machinery. Use `mergedOptions`/`rankOptions`
   (similarity-ranked keypresses, `SIM_MIN`, `GAIN_KEEP` band), but evaluate them with the new
   `"rule"` binding and rank finalists by `score` instead of `strokeFreqSaved`. Keep the top
   `MAX_ALTERNATIVES` keys.
5. The rule's exact score is the score with its best K.

Step 4 is the expensive one (Part B simulation). **Do it lazily**, only for roots that reach
the top of the Phase 3 heap. Never do it for the whole pool.

## 5. Phase 3: budgeted selection

Maximise `Σ_w f_w × max_{r∈S} gain_r(w)` minus each selected rule's cost terms, subject to
`|S| ≤ RULE_BUDGET` (default 30, both positions together).

- Each word is credited once, at its best selected rule of the same position.
- Prefix and suffix rules on the same word are independent, as today; composing them is out of
  scope.

The algorithm is a lazy greedy (a standard approach for this "facility location" coverage
objective):

1. Put every root on a max-heap keyed by an **optimistic** bound: the Part-A proxy score of its
   §4.4 step-3 rule, with no collisions and every carrier merged. This really is an upper bound
   on the exact score, because gain_w ≤ span_w.
2. Pop the top root.
   - If its entry is stale, recompute its **marginal** value against the current selection and
     push it back. The marginal value is `Σ_w f_w × max(0, gain_r(w) − best_S(w))` minus the
     rule's own costs (exceptions, exclusions, forms). Compute the exact rule with §4.4 step 4
     the first time it is needed, and cache it.
   - If its entry is fresh (computed against the current selection) and its marginal is > 0,
     **accept** it and update `best_S(w)` for its words.
3. Stop at `RULE_BUDGET` or when nothing has a positive marginal.
4. **Swap pass:** for each selected rule, try replacing it with each of the 20 best unselected
   exact-evaluated rules. Keep any swap that raises the total. Repeat until nothing improves or
   3 passes have run.

Notes:

- **Nested roots.** A rule rooted at `-té` with forms `{-ité, -ilité}` and a rule rooted at
  `-lité` overlap. Word-once crediting makes the second nearly worthless once the first is
  chosen. That is intended.
- **Output the savings curve**: the total after each accepted rule, 1..40 (run to 40 for the
  report even though the budget is 30). The user decides between 20 and 30 by looking at it.

## 6. Phase 4: keypress binding with sharing

For the selected rules, in descending order of score, give each its best K from its
alternatives:

- **Sharing a K with an already-bound rule of the same position is allowed** (D2), provided a
  joint `simulate` of both rules loses no more than `SPLIT_MAX_LOSS` (2%) of either rule's
  gain.
- Reuse the joint-simulation idea of `_mutualConflict`, but test "loss ≤ 2%" instead of "any
  carrier drops".

Recompute each rule's score after binding. If any rule lost more than 10% versus its
selection-time score:

1. remove it;
2. rerun Phase 3 from the current selection, with that rule marked "ineligible under current
   bindings";
3. rebind.

Do at most 3 iterations, and report any that happen.

## 7. Outputs, tests, verification

### 7.1 Outputs (all under `scratch/`)

- **`affix-rules.tsv`**, one row per selected rule. Columns:
  - `rank`, `position`;
  - `root`, `forms` (labels, with slots and exclusions);
  - `keys`, `rtfcre`, `sharedWith`;
  - `score`, `strokeFreqSaved`;
  - `wordExceptions`, `exceptionFreq`, `topExceptions`, `slotExclusions`;
  - `carriers`, `lemmas`, `examples`;
  - `review` (left empty for the user).
- **`affix-rules-report.md`:**
  - a header with every constant's value;
  - the savings curve 1..40;
  - one section per rule: its forms; 10 example words rendered `OLD → NEW` with
    `renderFinalStrokesToRTFCRE`, including at least one standalone-fallback example if any
    exists; its top exceptions;
  - the sibling-pair list from §4.1;
  - any Phase 4 rebind iterations.
- The CLI is `util/affix_scan.py`. The new path is the default; `--legacy` runs the old Part B
  (`growthMerges`/`unifyFamilies`/`assignGreedy`) unchanged.

### 7.2 Tests (hand-built fixtures, no pickles; follow the existing `_make_word`/record patterns in `src/test/affixes_test.py`)

- Slot matching: exact, onset (including an empty onset), any, and exclusions.
- The growth step emits exact + onset + any children **without consuming** each other.
- An onset group whose one colliding value is excluded survives with `excluded == ("m",)`. With
  more than `MAX_SLOT_EXCLUSIONS` needed, it is dropped.
- A7 keeps the original variants next to the pooled candidate.
- Dedupe keeps the simpler pattern and records the alias.
- The subtree bound lets a node with a low marginal but a high UB be expanded without being
  emitted.
- D5: a word matching forms `-ité` and `-ilité` is cut at `-ilité`. A form it doesn't match is
  never used, and no cut falls outside a form.
- Standalone fallback: `keyOverlap` gives standalone with gain `span − 1` and is not counted as
  an exception. If `(K,)` is an existing single-stroke outline, the result is a
  `standaloneTrap` exception.
- Selection: two rules covering the same words. The second one's marginal is its extra gain
  only; the budget is respected; the swap pass never lowers the total.
- Phase 4: two non-colliding rules may share K; two colliding rules may not.

### 7.3 Verification (all must hold before the final report)

1. `env/bin/python -m pytest src/test/` passes: 674 plus the new tests.
2. `env/bin/python -m mypy src/affixes.py src/affixbinding.py util/affix_scan.py` (plus
   `src/affixrules.py` if you create it) is clean.
3. The pipeline artifacts are untouched. Run `md5sum phonetic_theory.tsv disambiguated_theory.tsv
   resolved_press_sets.json keypress_groups.json realization_report.json
   plover_stenalgo_dictionary.json steno-trainer/public/data/*.json`; the result must be
   identical to the baseline you took at the start.
4. `--legacy` still runs and gives the same family count as before your changes (300 at Part A).
5. **Regression case, the acceptance test:**
   - there is a selected rule whose forms include an `-ité` form and an `-ilité`-type form;
   - `disponibilité` renders as `/dis/po/niK/` or `/dis/po/ni/-K`, **never** with `ni` absorbed;
   - `-liste` is not a form of that rule (it may be its own rule, or absent).
6. No selected rule uses keys 0, 1, 10 or 15. No slot has more than `MAX_SLOT_EXCLUSIONS`
   exclusions. No rule has more than `MAX_RULE_FORMS` forms.

### STOP 2: final report to the user

Report:

- the selected rules (at most 30): root, forms, K and RTFCRE, score, exceptions;
- the savings curve;
- which rules share keys;
- the sibling-pair list;
- the constants used;
- every default you had to pick yourself.

**Don't tune `EXCEPTION_ALPHA`/`EXCLUSION_COST`/`FORM_COST` beyond the defaults without asking.**
Instead, list the 3-5 rules whose selection is most sensitive to them (those near the budget
line).

## 8. New constants (top of their module, reported in output headers)

`src/affixes.py`: `MAX_SLOT_EXCLUSIONS = 2`, `GROWTH_MIN_MARGINAL = MIN_FAMILY_STROKEFREQ`,
`MAX_POOL = 20000`. Keep `GROWTH_MAX_DEPTH = 3` and `GROWTH_MAX_EXCEPTION_SHARE = 0.02`. Remove
`GROWTH_MIN_CARRIER_LEMMAS`/`GROWTH_MIN_STEM_ROOTS`/`GROWTH_MIN_CANDIDATE_FREQ` and
`GROWTH_MAX_SLOT_VALUES`. `--legacy` doesn't need them: legacy only changes Part B. If keeping
`--legacy`'s Part A family count at 300 needs them, keep them for `--legacy` only and say so.

Rules module: `RULE_BUDGET = 30`, `MAX_RULE_FORMS = 4`, `EXCEPTION_ALPHA = 1.0`,
`EXCLUSION_COST = 5.0`, `FORM_COST = 10.0`, `SWAP_CANDIDATES = 20`, `SWAP_PASSES = 3`,
`REBIND_MAX_LOSS = 0.10`, `REBIND_ITERATIONS = 3`.

## 9. Pitfalls

- **Keep candidate keys unique.** Two different patterns must never share
  `(position, k, phono, ortho)`, because a dict overwrite silently loses one. This bit A7
  before. Put exclusions in the `phono` label.
- **Keep carrier spans consistent with the pattern.** A grown carrier's `start`/`span` must
  cover exactly base + slots. Check that `sum(len(orthoSylls[start:start+span]))` matches
  on a few records.
- **Don't let exact leaves explode the pool unchecked.** The marginal floor + UB are the only
  guards. If the pool passes `MAX_POOL`, stop and report; don't invent a new threshold.
- **Inherited (inflected) carriers** have partial spans (PLAN A2c). A form's span for such a
  carrier is capped at its inherited run. Never extend past it.
- **Part B runtime.** Exact rule evaluation costs about 1 s per rule. If more than about 500
  get evaluated, the lazy bound is too loose. Report it rather than silently subsampling.
