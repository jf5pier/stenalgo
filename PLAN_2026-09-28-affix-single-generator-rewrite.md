> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

# Plan: single-generator affix lattice, no A7, relaxed thresholds, weight sweep (2026-09-28)

**Audience: the model (Sonnet) that implements this after a `/clear`.** The decisions in §1 are
the user's. **Don't re-ask them, and don't redesign.** If something is ambiguous, pick the
default given here, note it in your report, and continue. Stop at each **STOP** marker.

This plan **supersedes**:
- `RESUME_2026-09-28-affix-territory-merge.md`. Its territory merge was committed as checkpoint
  `8630552` and is never run; this plan removes most of it.
- §5-6 of `RESUME_2026-09-27-affix-phase3-4-budgeted-selection.md`.

`DESIGN_2026-09-27-affix-rule-selection.md` still holds wherever this file doesn't override it:
- D1-D6;
- slots;
- the rule score;
- the `"rule"` binding;
- the Phase 3 lazy greedy and swap pass;
- Phase 4.

## 0. Start-up

1. Read, in order:
   - this file;
   - `DESIGN_2026-09-27-affix-rule-selection.md` §1-§6 and §9;
   - `/home/jfsp/RESUME_2026-09-27-affix-a7-orphan-pairs.md` §2-§3 (background: why A7 and the
     lattice make near-duplicate nodes; F5 = the same-key overwrite bug);
   - all of `src/affixes.py`, `src/affixrules.py`, `util/affix_scan.py`,
     `src/test/affixes_test.py` and `src/test/affixrules_test.py`.
2. Environment:
   - Use `env/bin/python`; bare `python` is not on PATH. Run from the repo root.
   - Run the CLI as `PYTHONPATH=. env/bin/python -m util.affix_scan ...`.
   - The machine has 7 GB RAM: run one heavy job at a time.
   - Run long jobs with `run_in_background` and wait on the PID or a log sentinel. Never use a
     `pgrep -f` loop.
3. Rules:
   - **Don't commit or push**; the user decides. The branch is `affix-abbreviation-rules`.
   - **Don't touch the pipeline**: `dictionary.py`, `util/build_*`, the exporters, the pickles at
     the repo root, `docs/`. This is measurement tooling only; every output goes under
     `scratch/`.
   - `--legacy` must keep working unchanged (it still uses `poolTailVariants`).
4. Baseline:
   - `env/bin/python -m pytest src/test/ -q` must pass before you start and after you finish.
   - `env/bin/python -m mypy src/affixes.py src/affixrules.py util/affix_scan.py`: note the
     error count at HEAD and don't add new errors.

## 1. The user's decisions (binding, 2026-09-28)

- **U1. Remove A7** (`poolTailVariants`) from the non-legacy path, for both k≥2 and k=1.
  **Also remove the raw k≥2 enumeration** from the non-legacy path. There is **one generator**:
  - k=1 seeds, one per (position, phono, ortho);
  - plus the curated A8 groups (`poolKnownAffixGroups`, kept);
  - plus the variant merges of U3;
  - then lattice growth.

  Rationale: A7, the raw k=2/3 candidates and the lattice each produced the same patterns with
  slightly different carrier sets (twins like `ment` / `·°ment`, `blement` / `·blement`), so no
  identity dedupe could unify them.
- **U2. Lemma stops gating which words a pattern covers.** Remove the stem-attestation filter
  (`passesPrefixFilter` / `passesSuffixFilter`) and `MIN_STEM_LETTERS` as carrier gates. A word
  carries a pattern when its syllables match it and at least one stem syllable is left over.
  Lemma **keeps** its other two roles:
  - **paradigm inheritance**: suffix carriers are lemma forms, and inflected forms inherit the
    span (`inheritedSpan`);
  - **the collision definition**: `_exceptionShare` counts only different-lemma collisions;
    same-lemma collisions are resolved by S6.

  Keep the old attestation test **as a reported statistic only**: `attestedShare` per node,
  the frequency share of carriers whose stem would have passed the old filter.
- **U3. Spelling variants** (the same sound spelled differently: `ment`/`mant`,
  `tion`/`ssion`, `té`/`ter`/`tée`) are fused into one keypress **only if**:
  - (a) fusing creates no new conflicts; and
  - (b) fusing doesn't impede the growth of the main affix.

  If either fails, they stay separate. Grammatical category matters through (a): different
  roles (noun `côté` vs verb `coter`) show up as different-lemma collisions. Splitting identical
  endings by category (`-ment` nouns vs adverbs) is **out of scope**.
- **U4. Participles keep their own shape**: keep `isIterParticiple`. `habitées` may join the
  `-ité` rule even though `habiter` is covered by a `-ter` rule.
- **U5. Relax the hard thresholds.** Pure pruning thresholds become low, measured bounds.
  Learnability moves from generation-time gates into the score, which the user will calibrate
  by reviewing a weight sweep (U6). These **stay** as definitions:
  - `MIN_CARRIER_LEMMAS` and `MIN_STEM_ROOTS`: a "rule" with fewer lemmas is a set of briefs;
  - `TOP_WORDS_EXCLUDED`;
  - `MAX_EXCEPTION_RATE = 0.05`: the user's hard gate at rule level.
- **U6. Review at different weights.** Run the selection at three weight settings and produce
  a comparison for the user.
- **Unchanged from 2026-09-27:** D1-D6 of the DESIGN. Grown affixes belong to their parent's
  rule (D4), and the writer uses the longest form (D5).

## 2. What to build

### 2.1 Phase 1 generator (`src/affixes.py`, non-legacy path of `buildCandidates`)

1. **Enumerate k=1 only** when `legacy=False` (keep `range(1, min(MAX_AFFIX_SYLL, n-1)+1)`
   for legacy).
   - Prefix: every carrier record with `n ≥ 2`, stem = `r.ortho[len(oa):]`. Drop the lemma
     fallback, which existed only for attestation.
   - Suffix: lemma forms plus `isIterParticiple`, as today, with no `passesSuffixFilter`.
   - Compute `attestedShare` with the old filters (same `LemmaIndex`) and store it on
     `Candidate` as a new field `attestedShare: float = 0.0`. Compute it in `_finishStats` or
     next to it. Grown nodes need it too: use each carrier's stem at that node's span.
2. **Don't call `poolTailVariants`** when `legacy=False`. Keep `poolKnownAffixGroups` (A8).
3. **Variant merges (U3a).** Create them right where `poolTailVariants` was called, before
   inheritance, so merged nodes inherit too.
   - Group the k=1 candidates by `(position, phono)`. For each group with 2 or more distinct
     orthos, build merged candidates greedily:
     1. Sort the parts by `freq`, descending.
     2. Start a group with the largest part.
     3. Tentatively add each next part (the test is in step 4).
     4. Build one merged `Candidate` per resulting group of 2 or more parts.
     5. Repeat on the parts left over.
   - Merged node: `k=1`, the same `phono`, `ortho = "|".join(sorted orthos)`,
     `isGeneralized=True`, `variants` = the part orthos, `isSeed` = any part is a seed.
     Carriers are the union, deduped by `rec.idx`, keeping the larger span.
   - **Parts are never consumed.** They stay as separate candidates.
   - After the inheritance loop and `_finishStats`, apply the **conflict test** to each merged
     node:

     ```
     newConflict = excFreq(merged) − Σ excFreq(part)
     ```

     `excFreq` is computed with `_exceptionShare(pos, carriers, denom=merged.freq)`, and the
     parts use the same denominator. Keep the merged node iff
     `newConflict ≤ VARIANT_MAX_NEW_CONFLICT_SHARE × merged.freq`. The new constant defaults
     to `0.02`.
   - Use the same test inside the greedy of step 3, on pre-inheritance carriers (cheap).
     The post-inheritance check is authoritative.
   - Record `mergeParts: list[key]` and `newConflictFreq` on the merged node for the report.
4. **Emit thresholds** in the `kept` loop, non-legacy: emit iff
   `isSeed or (lemmas ≥ MIN_CARRIER_LEMMAS and stemRoots ≥ MIN_STEM_ROOTS)`. Drop the
   `MIN_CANDIDATE_FREQ` gate there; legacy keeps it.
5. **Lattice growth** (`growAffixesLattice` / `_growLatticeLevel`), non-legacy:
   - Emit a child iff `lemmas ≥ MIN_CARRIER_LEMMAS and stemRoots ≥ MIN_STEM_ROOTS`. Drop the
     `GROWTH_MIN_MARGINAL` emit gate.
   - Expand iff `UB ≥ GROWTH_MIN_EXPAND`. This is a new constant, measured in §3 step 1;
     start at `5.0`.
   - `GROWTH_MAX_DEPTH`: 3 → **4** (k up to 5 from k=1 seeds).
   - `MAX_SLOT_EXCLUSIONS`: 2 → **3**.
   - `GROWTH_MAX_EXCEPTION_SHARE`: 0.02 → **0.05**, aligned with the rule-level
     `MAX_EXCEPTION_RATE`. Collisions it lets through become word exceptions and are scored.
   - Legacy uses its own constants: if a constant is shared, fork it, e.g.
     `LEGACY_GROWTH_MAX_EXCEPTION_SHARE`, so `--legacy` output doesn't change.
6. **No silent key overwrites** (the F5 bug).
   - While growing, keep `keyOwner: dict[key, carrierSetKey]` for seeds and emitted children.
   - When a new child's `(position, k, phono, ortho)` equals an existing key:
     - **Different carrier set:** rename the child *before* it is expanded or stored by
       appending `⟨<parent.ortho>⟩` to `cand.ortho`, and count it.
     - **Same carrier set:** it is a duplicate, so treat it like `_dedupeByCarrierSet`
       (alias it, don't emit twice).
   - Seeds are k=1 and children are k≥2, so seeds and children can't collide. Collisions
     can happen between the descendants of a merged node and those of its parts.
7. **Delete `_mergeChildrenIntoPool`.** Seeds and children can't share a carrier set any more
   (different k). Assemble the pool as before and assert that no key is overwritten.
8. **Anchors.** Add a field `isAnchor: bool` to `Candidate`: True for k=1 seeds, A8 groups and
   surviving variant merges; False for grown nodes. Only anchors become rule roots (D4: a grown
   node is only ever a form of its anchor's rule). That removes the nested-root "patch" rules
   seen on 2026-09-27 (rule 24 `·[…]ter`, rule 18 `·[…]sez`).

### 2.2 Phase 2: rules and rival resolution (`src/affixrules.py`)

1. `buildCandidateRule` is unchanged (greedy over the anchor's descendants), but is **called
   only for anchors**.
   - `MAX_RULE_FORMS`: 4 → **6**, as a compute safety cap only. `FORM_COST` carries the
     learnability cost, and the sweep varies it.
2. **Delete the territory merge** from checkpoint `8630552`:
   - `buildMergedRule`;
   - `handleTerritory`;
   - the merge branch of `selectRules`;
   - `TerritoryEvent` outcomes other than skip;
   - `Rule.sources` if nothing else needs it.

   Keep `territoryOverlap` / `territoryMate` for the overlap report and as a safety guard.
   Rename `TERRITORY_OVERLAP` → `RULE_OVERLAP_MAX = 0.5`. In `selectRules` and `swapPass`, a
   popped rule that overlaps a selected rule by at least `RULE_OVERLAP_MAX` is **skipped**
   (no merge), and the skip is recorded. Expect about zero skips: anchors are near-disjoint by
   construction, and rival resolution handles merged-vs-parts.
3. **Rival resolution (U3b)**, a new function
   `resolveVariantRivals(anchors, pk, ctx, keypresses) -> (keptAnchors, decisions)`, run
   before `selectRules`:
   - For each surviving merged anchor M, let `main` = its largest part (by freq).
   - Only resolve groups within reach: M or `main` must be in the top `RIVAL_RESOLVE_TOP = 60`
     anchors by proxy upper bound (the heap's stage-0 key). For groups out of reach, drop M;
     the decision is `"outOfReach"`.
   - Build `R_M` and `R_main` with `buildCandidateRule`, then `chooseRuleKeypress` both.
     Cache the rules and reuse them in `selectRules`; don't evaluate twice.
   - **Keep M and drop its parts from the anchor set** iff `R_M.keys is not None` and
     `R_M.score ≥ R_main.score × (1 − VARIANT_GROWTH_TOLERANCE)`, with the tolerance
     defaulting to `0.0`. That means fusing costs the main affix nothing.
   - Otherwise drop M and keep the parts.
   - Record every decision: parts, `newConflictFreq`, `R_M.score` vs `R_main.score`, forms of
     both, and the outcome.
4. `selectRules` takes the resolved anchor set; nothing else about the lazy greedy, swap pass
   or Phase 4 changes.

### 2.3 CLI and report (`util/affix_scan.py`)

1. Part A prints and records:
   - the pool size;
   - the anchor count;
   - merged anchors (kept / dropped by the conflict test);
   - key-collision renames;
   - Part A time and peak RSS (`resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`).
2. `affix-candidates.tsv` gains the columns `isAnchor`, `attestedShare`, `mergeParts` and
   `newConflictFreq`.
3. The rules report gains:
   - per rule: `attestedShare`, top-3 `gramCat` shares of its carriers, merge parts if any;
   - a "Variant rivals" section listing every `resolveVariantRivals` decision;
   - the overlap section, with the new name and threshold;
   - a line counting the selected rules with `attestedShare < 0.5` (candidate pseudo-affixes
     like `ma-`; the user will judge them).
4. **Sweep mode:** `--sweep` runs Phases 2-4 in-process once per setting, reusing records, the
   pool, `SimContext`, `PhonemeKeys` and the keypress list.
   - Set the module globals `R.EXCEPTION_ALPHA`, `R.EXCLUSION_COST` and `R.FORM_COST` before
     each run, and rebuild every `Rule` (scores depend on the weights).
   - Settings (stroke-frequency units; the top rules score about 5,000-9,000):

     | name | EXCEPTION_ALPHA | EXCLUSION_COST | FORM_COST |
     |---|---|---|---|
     | L (today) | 1.0 | 5 | 10 |
     | M | 1.0 | 50 | 100 |
     | H | 2.0 | 150 | 300 |

   - Outputs go to `scratch/affix-sweep/<name>/affix-rules.tsv` and `.../affix-rules-report.md`.
     Also write `scratch/affix-sweep/comparison.md`, containing:
     - per setting: total credited saving at 20 and at 30 rules, number of forms, exclusions,
       word exceptions, and rules with `attestedShare < 0.5`;
     - a table of all rules selected in any setting × the rank in each setting (or "—");
     - for each rule selected in every setting whose forms differ between settings, the
       forms side by side.

## 3. Order of work

1. **Before changing code**, save the baselines:
   - Copy the 2026-09-27 outputs `scratch/affix-rules.tsv`, `affix-rules-report.md` and
     `affix-candidates.tsv` into `scratch/baseline-20260927/`.
   - Write `scratch/probe_dump_a7.py`. It builds the current pool
     (`A.buildCandidates(records, seedPairs)` from the cached `scratch/affix-records.pickle`)
     and pickles every A7 node (`isGeneralized and not slots and grownFromKey is None`, k≥1)
     as `{key: (freq, frozenset(rec.idx of carriers))}` to `scratch/old-a7-nodes.pickle`.
     Run it.
2. Implement §2.1 and its tests (§4). Then run Part A only
   (`--part a`, with `GROWTH_MIN_EXPAND` at 30, then 10, then 5), serially, and record for
   each run: pool size, time, peak RSS.
   - Pick the lowest value with pool ≤ 50,000, Part A ≤ 10 min and RSS ≤ 4 GB.
   - **STOP 1 (only if no value fits these budgets):** report the numbers to the user and wait.
     Otherwise continue and note the choice.
3. Run the Phase 1 acceptance checks (§5 items 1-4) on that pool.
4. Implement §2.2-§2.3 and their tests. Run pytest and mypy.
5. Run the full selection at setting L once (`--part b`), then check §5 items 5-8.
6. Run `--sweep` in the background. It takes about 3× one full run; one full run was about
   14 min on 2026-09-27, but the pool will be larger.
7. **STOP 2:** report to the user (§6). Don't commit.

## 4. Tests (hand-built fixtures, `excludeTopWords=False`, follow the existing style)

- `buildCandidates` (non-legacy):
  - only k=1 seeds are anchors;
  - no A7 node exists;
  - a word whose stem is **not** an attested lemma is still a carrier (an `heureusement`-style
    fixture);
  - `attestedShare` reflects the old filter.
- Variant merge:
  - two spellings with the same phono and no cross-lemma stem collision → a merged anchor
    whose carriers are the union, and the parts still exist;
  - a fixture where merging makes two different lemmas share their remaining stem stroke →
    the merge is dropped.
- A lattice key collision with a different carrier set → the child is renamed, never
  overwritten, and its own children point at the renamed key.
- `resolveVariantRivals`, with `chooseRuleKeypress` monkeypatched as the checkpoint's tests do:
  - M kept (parts removed) when `R_M.score ≥ R_main.score`;
  - M dropped when lower;
  - `"outOfReach"` when outside `RIVAL_RESOLVE_TOP`.
- `selectRules`:
  - a grown node is never a rule root;
  - an overlapping rule is skipped, not merged.
- Delete or rewrite the checkpoint's `TestTerritory` merge tests and
  `TestMergeChildrenIntoPool` to match.
- Legacy: the existing legacy tests pass unchanged.

## 5. Acceptance checks (write the results into the STOP 2 report)

1. **Old A7 coverage.** For each node in `scratch/old-a7-nodes.pickle` with freq ≥ 30, find
   the new-pool node that covers the largest share of its carrier frequency. List every old
   node covered at less than 0.9, with its best new node. Explain the misses, don't hide them.
2. **Seeds reachable.** Every `(position, affix)` in `resources/affixSeeds.tsv` with k≥2 must
   match some new-pool node's ortho (exact, or as one variant of a slot). List the misses.
3. **The `-ité` chain.** `scratch/affix-lattice-trace.txt` shows a `…bilité`-type node under
   the `té` anchor (or its merged anchor).
4. **Collisions.** The number of key-collision renames, and 0 silent overwrites (assert).
5. **The `ment` rule.** There is exactly one selected rule whose forms cover
   `…ment`. Both `heureusement` (an A7-only word on 2026-09-27) and `tellement` (lattice-only)
   are carriers with gain > 0, or are listed as exceptions with a reason. No `·°ment` exists.
6. **Overlap.** No two selected same-position rules overlap at or above `RULE_OVERLAP_MAX`;
   list every pair at or above 0.05.
7. **Exception rate.** Every selected rule's exception rate is ≤ 5%.
8. **Comparison.** Compare rank by rank against `scratch/baseline-20260927/affix-rules.tsv`:
   which rules left, which arrived, and the total at 30 then vs now.

## 6. STOP 2 report to the user

Keep it short and concrete:
- the pool numbers from step 2;
- §5 items 1-8;
- the variant-rival decisions (which fusions were kept, e.g. whether `ment|mant` or
  `tion|ssion` exists and was kept);
- the three-setting comparison: point at `scratch/affix-sweep/comparison.md` and summarise
  what changes between L, M and H;
- the pseudo-affix count (`attestedShare < 0.5`) per setting, with the examples.

The user then picks the weights, or asks for another setting. Don't pick for them.

## 7. Pitfalls

- **Don't reintroduce twins.** Every pattern must come from one mechanism: a seed, A8, a
  variant merge, or growth. If you find yourself adding a pre-threshold pooling step, stop.
- **Rivals.** Merged anchors and their parts are rivals, not a family. Never select both;
  rival resolution runs before selection, and the overlap skip is only the safety net.
- **Sweep weights are module globals.** Rebuild each `Rule` per setting, and don't cache exact
  scores across settings.
- **Out of scope:** splitting `-ment` nouns from adverbs, derivational pairs (`-ble` ↔
  `-bilité`), and composing prefix and suffix rules on one word. Don't implement them; mention
  any cases you notice in the report.
- **Budget RAM.** A lower `GROWTH_MIN_EXPAND` grows the pool monotonically. Measure before
  going lower, and never run two heavy jobs at once.
