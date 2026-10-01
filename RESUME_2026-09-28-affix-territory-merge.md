> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Resume: one key per territory -- the `ment` / `·°ment` fix (2026-09-28)

> **SUPERSEDED (2026-09-28, later the same day):** committed as checkpoint `8630552` and never
> run. Follow `PLAN_2026-09-28-affix-single-generator-rewrite.md` instead.

**Read after `RESUME_2026-09-27-affix-phase3-4-budgeted-selection.md`; where they disagree, this
file wins.** It covers that file's §3 bug and §6 items 1-2.

> **STATUS: CODE WRITTEN, NOTHING RUN YET.** The shell was unavailable for this whole session
> (every Bash call failed the auto-mode safety check), so no pytest, no mypy, no `--part b` run.
> The code was only desk-checked. The tests below were traced by hand against the code but never
> executed. Start with §5.

## 1. The problem, re-diagnosed

The 2026-09-27 resume blamed the `ment`/`·°ment` split on a lattice dedup bug (§3 there). That
bug is real but is **not enough to explain it**:

1. **The dedup only catches identical carrier sets.** `ment` (2292 carriers) and `·°ment` (2275)
   share 83% of their words, not 100%. And `·°ment` is an A7 union across onsets, so it isn't a
   byte-for-byte copy of any one lattice child of `ment`. The previous resume's "compare children
   against the whole pool" fix is needed, but it may well leave this pair apart.
2. **Phase 3's objective rewards a second key on the same words.** `_marginal` credits
   `max(0, gain_r(w) - best_S(w))` per word, so `·°ment` earns its marginal by improving words
   `ment` already covers:
   - `doucement` saves one stroke under `ment` (its k=2 form excludes the `s°`/"ce" syllable) and
     two under `·°ment`.
   - `seulement`, `exactement` and `complètement` get both `-tm` and `-dt`: two outlines per word,
     two keys per morpheme.

   Nothing charges for that.

**The same pattern elsewhere in the 2026-09-27 top-30** (`scratch/affix-rules-report.md`):
- **`ter` (rule 8, `-dtm`) and `·[bai|…]ter` (rule 24, `-jkt`):** `arrêter` is `ter`'s top
  exception and rule 24's lead example. Rule 24 is an exception patch for rule 8, on a second key.
- **`ser`'s `-{k}sez` form (rule 13) and `·[…]sez` (rule 18, `w-t`):** `excusez` is abbreviated
  by both (`iedtl` vs `wiet`).

These two come from reading the report's examples; their overlap was not measured.

## 2. The decision taken: one key per territory

- **Definition.** Two same-position rules whose carrier words overlap by at least
  `TERRITORY_OVERLAP = 0.5` (frequency-weighted, as a share of the smaller rule) are one
  territory.
- **The rule.** A territory-mate may only join the selected rule as a form, sharing its key. It is
  never selected on its own.
- **Rejected alternative: "longest match wins" with two keys** ("-ement → `-dt`, other -ment →
  `-tm`"). The longer rule's own exceptions (`·°ment` had 33: `simplement`, `classement`,
  `rendement`…) would need a fallback to the shorter rule. That builds chained exception lists,
  which the 20–30 simple-rules learnability constraint rules out. Rules 18 and 24 show the
  optimizer would use that loophole to spend slots patching other rules' exceptions.

**Proposed by Claude, not yet confirmed by the user:** strict exclusivity (instead of longest
match) and the 0.5 threshold. Revisit both if the rerun disappoints.

## 3. What changed (uncommitted, branch `affix-abbreviation-rules`)

### `src/affixes.py`
- **`_mergeChildrenIntoPool(cands, children)`** (new; `growAffixesLattice` now returns through
  it). This is the previous resume's §3 fix: a grown child whose carriers+spans equal a seed
  node's is not added as a separate pool entry.
  - It becomes an alias of the seed (`seed.aliases`).
  - The seed inherits the child's lineage (`grownFromKey`/`rootKey`, only if it had none), so
    Phase 2's `descendantsOf(root)` now sees the seed as a candidate form.
  - It is safe: the dropped child never has children, since `seenExpand` blocks re-expanding a
    seed's carrier set. It can't create a cycle, since spans grow strictly along a lineage.
- Fixed `growAffixesLattice`'s docstring, which claimed it returns a tuple.

### `src/affixrules.py`
- **`TERRITORY_OVERLAP = 0.5`**, with a comment giving the rationale.
- **`Rule` gets two fields.**
  - `sources`: the roots whose subtrees fed the forms. It's `[root]` normally, and more than one
    root after a merge.
  - A cached `wordFreq()` map (`_wordFreq`, `compare=False`).
- **`buildCandidateRule`** now delegates to `_greedyForms(root, remaining)` with unchanged
  behaviour. The new **`buildMergedRule(roots, idx)`** runs the same greedy over the union of
  several roots' subtrees, trying each root as `forms[0]` and keeping the best proxy score. The
  greedy may still leave a root out.
- **New helpers.**
  - `territoryOverlap(a, b)`: returns 0 across positions.
  - `territoryMate(rule, selected)`: the most-overlapping selected rule at or above the
    threshold.
  - `creditedTotal(rules)`: the word-once-credited objective, now shared with `swapPass`.
  - `_bestSOf(rules)`.
- **`selectRules`.** At every stage-1 and stage-2 pop, before the expensive key search and again
  before acceptance, the root is checked against `selected`. If it has a territory-mate:
  - **Mate's lineage already contains the root** → drop it, no evaluation (the greedy already
    weighed it). Outcome `inLineage`.
  - **Otherwise** → `buildMergedRule(mate.sources + [root])`:
    - If the forms are unchanged, the outcome is `rejected`.
    - Otherwise run `chooseRuleKeypress` on the merged rule once (~1751 simulations). If it finds
      no legal key, the outcome is `noKey`.
    - It replaces the mate **in the same budget slot** only if `creditedTotal` rises and the
      merged rule doesn't overlap another selected rule. Outcome `merged`.
  - Either way the root never re-enters the heap.
  - A merge changes `total`/`bestS` but adds no curve point.
- **`SelectionResult.territoryEvents`** (a list of `TerritoryEvent`) records every territory-mate
  met during selection, for the report.
- **`swapPass`** refuses a swap that brings in a rule overlapping one that stays selected.

### `util/affix_scan.py`
`scratch/affix-rules-report.md` gains:
- `TERRITORY_OVERLAP` in the constants line.
- "Territory overlaps among selected rules": every pair at or above 0.05. **Every value must be
  below 0.5.** This is the regression check.
- "Territory-mates met during selection": counts per outcome, plus every non-`inLineage` event
  with its before/after total.

### Tests (new, never run)
- **`src/test/affixes_test.py::TestMergeChildrenIntoPool`**
  - An identical child becomes an alias and links the lineage-less seed.
  - A different child is added untouched.
- **`src/test/affixrules_test.py::TestTerritory`**
  - Overlap is weighted by frequency, as a share of the smaller rule.
  - Prefix and suffix rules never share a territory.
  - **`selectRules` merges a lineage-less `·°ment`-style mate into `ment` instead of selecting
    it alone.** This test monkeypatches `chooseRuleKeypress`. By hand trace: `·°ment` is accepted
    first (upper bound 160), `ment` hits it as a mate, and the merged rule scores 170 > 160, so the
    result is one rule with both forms and a single event, `merged`.
  - **`swapPass` never brings in a mate of a rule that stays.** Unfiltered, the pass would end
    with `[·°ment, ment]`; filtered, it ends with `[té, ·°ment]`.

This starts on the previous resume's §7.2 test gap (Phase 3 had no tests at all). It doesn't close
it: `bindKeypresses`/`_jointLoss` are still untested.

## 4. Expected effect, and what to watch

- **The raw total should drop.** The old total counted two-key coverage as pure gain. The 2–3
  slots freed from `·°ment`, rule 24 and rule 18 go to rules covering new words, which partly
  compensates.
- **Runtime.** Each non-lineage merge attempt costs one exact evaluation. Lineage mates cost
  nothing extra, and roots that are now dropped used to get exact evaluations of their own, so
  the total runtime should stay near ~14 min. Check the `phase 3:` timing line.
- **Risk: the merge may lose.** On 2026-09-27 a hand-merged `Rule(ment, [ment, sment])` scored
  7379 < `ment`'s 8176. That test wasn't fair: it dropped `ment`'s other three forms and skipped
  the greedy. `buildMergedRule` redoes it properly (greedy over both subtrees, `MAX_RULE_FORMS=4`).
  If it still loses, the event says `rejected`, `·°ment` is dropped, and `ment` stays alone. That
  is the intended outcome under strict exclusivity, not a failure.
- **Watch `MAX_RULE_FORMS`.** `ment` already used all 4 forms. If merges are rejected only
  because of the form cap, consider raising it for merged rules. That needs a decision: more forms
  make a rule harder to learn.

## 4b. A parallel investigation whose write-up is missing

Claude's project memory (`affix_abbreviation_plan.md`, modified 2026-09-28) records a 2026-09-27
investigation of the same bug. Its write-up, `RESUME_2026-09-27-affix-a7-orphan-pairs.md`, is
**not on disk**: not at the repo root, not in `scratch/`. This session couldn't search further
without a shell. The memory says:
- **187** A7-pooled vs lattice-grown same-signature pairs, so the problem is systemic.
- The cause: the stem-attestation filter runs at different k, so the carrier sets differ (~83%)
  and exact-set dedupe **cannot** fix it. That agrees with §1 above.
- A separate bug: **same-key pool overwrites**. Two real cases were found; `exa·` lost 78 of its
  82 carriers. This was not addressed here. The likely spot is `poolTailVariants`'s
  `pooled[(pos, k, phono, ortho)] = merged` (with `keepOriginals=True`) or
  `poolKnownAffixGroups`, where a pooled node lands on an existing key. Unverified.
- Its proposal: graft lineage onto the A7 node, exclude it from Phase 3 roots, and union carriers
  on same-key overwrites.

**How this session's work relates.** The territory rule (§2–3) is more general than "exclude A7
nodes from roots": it covers *any* same-territory pair, lineage-less or not, including the
`ter`/`·[…]ter` exception-patch case. It still lets the A7 node become a form via
`buildMergedRule`. `_mergeChildrenIntoPool` does the lineage graft, but only for exact matches.
**The same-key overwrite bug remains open**: find the pool overwrite, then union the carriers
instead of replacing them.

## 5. Next session: do these in order

1. Run the verification this session couldn't:
   ```bash
   env/bin/python -m pytest src/test/affixrules_test.py src/test/affixes_test.py -q
   env/bin/python -m pytest src/test/ -q          # 697 + 6 new expected
   env/bin/mypy src/                               # compare the error count to HEAD (memory: ~127 pre-existing)
   PYTHONPATH=. env/bin/python -m util.affix_scan --part b   # ~14 min; serialize (7 GB RAM)
   ```
   Keep the 2026-09-27 report for comparison first:
   `cp scratch/affix-rules-report.md scratch/affix-rules-report-20260927.md`.
2. **Check the new report:**
   - The territory-overlap section is empty at 0.5.
   - Look at `ment`: are `·°ment` or its `-ilement` form now inside the rule, and on one key?
   - Look at `ter`/`·[…]ter` and `ser`/`·[…]sez`: merged or rejected?
   - What filled the freed slots?
   - Did the savings curve change shape? That feeds the open 20-vs-30 budget question.
3. Ask the user to confirm the two proposals in §2 (strict exclusivity, threshold 0.5).
3b. Fix the same-key pool overwrite bug from §4b (`exa·`), with a unit test, then rerun step 1's
    `--part b`.
4. The previous resume's remaining items still stand: similarity as a tiebreaker (§2.4 there),
   the rest of the §7.2 tests, the `-iter`/`-oter`/`-eter` generalization, and then the STOP-2
   report.
