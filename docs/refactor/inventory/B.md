# Doc and Data Inventory — Bundle B

Read-only triage. These five files are all pre-elicitation-pivot (2026-09-18) or
implementation-session planning docs for Same-Lemma and Grammatical-Category Disambiguation (S6).
Verdict for the bundle as a whole: **almost entirely superseded**. The elicitation-first pivot
(ATOMIC_KEYPRESS_REWIRE_PLAN.md's own "session-2 pivot" section) replaced the solver-picks-features
design these files build on; `docs/specs/discriminating-features.md` already states the live design
and explicitly calls the old design "superseded." Recommend deleting most of these outright and
extracting only what's genuinely irrecoverable elsewhere.

## ATOMIC_KEYPRESS_REWIRE_PLAN.md (393 lines)

Verdict: the authoritative historical record of the pivot itself and of Realization Phase
milestone 1's design derivation (star/hash rule stack, N-ary escalation, composition proof) — all
now stated as current fact in docs/specs/star-hash-marking.md and discriminating-features.md, in
most cases word-for-word carried forward. A few structural facts (worked examples' derivation
reasoning, the vocabulary table) are not duplicated and are worth a pointer, not a copy.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-36 | Header: supersedes the original plan; the "session-2 pivot" narrative (parler walkthrough that motivated elicitation-first) | history | ARCHITECTURE.md (one paragraph, design rationale) or delete | The *reasoning* for why elicitation beats solver-picks-features isn't restated anywhere else; discriminating-features.md §1 states the *decision* ("Elicitation first (2026-09-18 pivot)... Earlier designs... are superseded") but not the parler walkthrough that motivated it. Worth one paragraph, not the full file |
| 38-79 | Vocabulary table (Cluster/Marker/Reading/Keypress/Press/No-conflict rule) + worked example tables ([paʁl], [paʁle] readings) | superseded, terminology now differs | delete | GLOSSARY.md already maps every one of these to current terms (Cluster→avoid, Marker→Atomic feature, Reading→Feature Combination, Keypress→Keypress Group, Press→Discriminating feature set); the worked examples are subsumed by discriminating-features.md §6's own worked-example table using current vocabulary |
| 80-99 | Context: reserved-key decision, `_colorFeatures` critique, Part 2's diagnostic-only status | history | delete | The reserved-key decision is current fact, already in star-hash-marking.md §1 ("Two reserved keys only"); `_colorFeatures`/satoptimizer.py critique is dead-design commentary |
| 100-116 | "Status of the original plan's sections" — table mapping old plan §s to disposition | history | delete | Pure bookkeeping for a plan that's since fully executed; no durable fact |
| 117-125 | Prerequisite fix DONE (`atomicFeatures()` tokenizer fix, commit `29da8d2`) | history | delete (or one line in a changelog if one exists) | Shipped and superseded; the resulting behavior (features split only on `:`) is implicit in the current codebase, not something a doc needs to assert |
| 127-185 | "Elicitation Phase" and "Grouping Phase" sections (E0-E6, grouping rules, implementation seed) | already covered by docs/specs/discriminating-features.md | delete | discriminating-features.md §2-3 states the live mechanism (Questionnaire Generation/Answer Collection/Press-Set Resolution; hard/soft grouping rules; K=7 result) more precisely and with current names |
| 186-260 | "Realization Phase" — milestone 1 done, star/hash rule stack design derivation (regret minimization, frequency-ratio rule, category order, N-ary escalation, composition proof), worked validation numbers | already covered by docs/specs/star-hash-marking.md | delete (verify no orphaned facts first — see below) | star-hash-marking.md §2-6 states this design with the same numbers (0.526%/0.499%/0.208% gap, 10x threshold reasoning, `au`/`eau`/`oh`/... 8-word group) and current rule names (R1-R7) |
| 200-204 | The `-er`/`-ers` noun wishlist item (reuse Infinitif features instead of a star/hash mark for a NOM/VER sub-class) | duplicate of ROADMAP.md 247-249 | ROADMAP.md or TODO.md (already flagged in Bundle A's ROADMAP.md row) | Exact duplicate of the ROADMAP.md wishlist item flagged in Bundle A; keep in exactly one place |
| 261-320 | Still-open bugs from this design phase: `_isFeasibleAddition` misses new-vs-new collisions, `checkComposedChords` half-combo bug, wiring/persistence still open (at time of writing) | superseded / partially already in todo.md | verify against todo.md's B-list, then delete | These read like early drafts of some B-numbered bugs (compare to B22 "collision tests compare raw strokes" and B25/B26); need a line-by-line check that nothing here is missing from todo.md before deleting |
| 320-368 | Open decisions (§E strict/lenient margin — still open per ROADMAP.md; §F questionnaire format — resolved, web Artifact; §G noun-in-verb-cluster scoping — still open per ROADMAP.md), established facts, non-goals, old call graph | mixed: 2 still-open decisions + rest superseded | ROADMAP.md (only §E and §G, already listed there as carried-forward open decisions) / delete rest | ROADMAP.md "What's left to do" (240-262 in Bundle A's numbering) already restates §E and §G as still open — exact duplicate; the call graph and non-goals are dead-design bookkeeping |

**Unique durable facts found:** none beyond the parler-walkthrough rationale (flagged above) — this
file's substantive content (rule stack, N-ary escalation, composition safety) is fully present in
star-hash-marking.md with the same measured numbers, confirmed by DECISIONS.md's own Pass 2 note
("prose mismatches found were all already superseded").

## SHARED_DISCRIMINATOR_REWIRE_PLAN.md (467 lines)

Verdict: **entirely dead design**. This plan wires `selectSharedDiscriminators`/
`buildDiscriminatorSelection`/`satOptimizeDiscriminator` — the solver-picks-features machinery the
2026-09-18 pivot explicitly discarded. PIPELINE.md confirms: "The legacy discriminator path
(`buildDiscriminatorSelection`, `satOptimizeDiscriminator`, `assignDiscriminatorKeypresses`) no
longer runs in `dictionary.py` `__main__`... `src/featureextractor.py` feeds only Synthetic
Lexicon Building (S2)'s gating and the `ambiguitychecker` diagnostic." No part of this plan
describes the live pipeline.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-459 | Whole file: two competing feature-selection algorithms, wiring plan, ortho-collapse correctness fix, secondary consumers, re-run/compare checklist, open decisions on selection-criterion ordering | superseded | delete | Describes `extractDiscriminatingFeatures`/`greedyOptimizeDiscriminator`/`satOptimizeDiscriminator`/`selectSharedDiscriminators`, none of which is in the live `dictionary.py __main__` path per PIPELINE.md and GLOSSARY.md ("Discriminator... Avoid"). Confirms `src/featureextractor.py` is retained only for Synthetic Lexicon Building (S2) gating and a diagnostic — this plan's whole subject (wiring the *theory-building* use of that selection) never shipped and can't ship under the current design |
| 407-441 | §7 "Selection-criterion ordering" — the one part that shipped (coverage-first swap in `selectSharedDiscriminators`, confirmed with real before/after numbers, 20→14 low-coverage features, 9→11 special keypresses) | history | Synthetic Lexicon Building (S2) note in PIPELINE.md, if not already covered, else delete | This IS a real, landed code change, but it only matters for `src/featureextractor.py`'s remaining live callers (S2 gating / ambiguitychecker diagnostic) — worth one line in PIPELINE.md's S2 section confirming today's ordering is coverage-first, since PIPELINE.md doesn't currently say which ordering `extractDiscriminatingFeatures`/`selectSharedDiscriminators` use |

**Unique durable fact found:** the coverage-first vs complexity-first ordering decision (line
416-441) — if `src/featureextractor.py`'s live diagnostic/gating path still uses this ordering,
it's a real fact about currently-running code that PIPELINE.md doesn't currently state. **Verify
against the code** before deciding whether to preserve it.

## DESIGN_alternate_press_sets.md (236 lines)

Verdict: describes the "calmez fix" (self-homograph gets one alternate per feature combination
instead of their union) — **implemented and shipped**, and now stated as current fact in
discriminating-features.md §2.4 ("self-homograph... keeps one alternate per combination instead
of their union"). The design file is useful history for *why*, but the *what* is fully covered.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-19 | Header: status implemented, the bug being fixed (union over-marking), scope of the fix across 4 files | history | delete | Implementation confirmed shipped; discriminating-features.md states the resulting design, not the bug history |
| 21-32 | The bug restated with numbers (8,413 of 47,827 groups, ~17.6%, affected) | already covered by docs/specs/discriminating-features.md | delete (or keep the 17.6% figure as a footnote if not elsewhere) | discriminating-features.md doesn't currently cite this percentage; it's a genuinely useful scale figure not duplicated anywhere else — **flag as possibly-unique** |
| 34-51 | Chosen direction: keep every per-reading press-set as its own theory line, new `PressSetsByOrtho` shape | already covered by docs/specs/discriminating-features.md | delete | discriminating-features.md §2.4's "self-homograph" definition and the alternate-entries mechanism in §4 state this design directly |
| 53-121 | `src/elicitation.py` implementation detail (code snippet, `resolveGroupPressSets` walkthrough, validation logic, test updates) | superseded by shipped code | delete | Implementation detail belongs in code comments/docstrings, not a design doc, once shipped; GLOSSARY.md's "Alternate" and "Discriminating feature set conflict" entries already cite the live function names and line numbers |
| 122-173 | `src/featuregrouping.py` and `src/featuregroupingsat.py` implementation detail (GroupSignature reshape, distinctness model changes) | superseded by shipped code | delete | Same — GLOSSARY.md's "Homophone group set of feature sets" entry already documents the live `GroupSignature` shape (`frozenset[frozenset[str]]` at the group level, cited from `src/featuregroupingsat.py:37`) |
| 174-222 | §4 "open question" — how Realization Phase should realize multiple alternates physically (option a: realize every alternate; option b: dedup after induction) | already covered by docs/specs/discriminating-features.md, resolved | delete | discriminating-features.md §4 "Alternate entries" states option (a) as the shipped design ("Every non-primary alternate... becomes an extra dictionary entry"); the open question is closed |
| 223-236 | Suggested implementation order (6 steps) | history | delete | Sequencing scaffold for a now-completed implementation; no durable content |

**Unique durable fact found:** the 17.6% (8,413/47,827 groups) scale figure for how common the
multi-reading-spelling shape was before the fix (lines 30-32) — not restated in
discriminating-features.md. Minor, but flag it as a candidate one-line addition ("this shape
affects ~17.6% of homophone groups") if the user wants scale context preserved.

## NOTES_2026-09-17_polarity_and_homograph_merge.md (182 lines)

Verdict: pure session notes, two threads (A: person-polarity family in `src/satoptimizer.py`,
dead code per PIPELINE.md; C: the `Word.mergeInfoVerb` homograph-merge fix, which shipped and is
now documented as "Identity merge" in GLOSSARY.md and "Verb-tag fold-in" (S3.2.1.2) in
PIPELINE.md). Thread B (a printed-table UI change in `dictionary.py`) is also dead — that table
belonged to the superseded discriminator-selection path.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-46 | Thread A: adding person (`pers_1/2/3`) to the polarity/family machinery in `src/satoptimizer.py`, `associationScore`'s min-per-family rule | superseded | delete | `src/satoptimizer.py`'s polarity/family machinery (`FEATURE_FAMILIES`, `associationScore`) has no live caller — ROADMAP.md's own "What's left to do" says so ("has no external caller left... only self-referential"); this fix improved dead code |
| 48-65 | Thread B: iterative changes to `dictionary.py`'s printed "Special keypress mapping" table (driven by `satOptimizeDiscriminator`'s `keyAssignment`) | superseded | delete | This printed table belonged to the retired solver-picks-features step (PIPELINE.md: "This also retires the superseded solver-picks-features step that used to run in `dictionary.py`'s `__main__`") |
| 66-116 | Thread C: the `rudoie` investigation — root cause (LexiqueSynthetic rows appended as separate Word instances instead of merging), the `Word.mergeInfoVerb` fix, verification | already covered by docs/PIPELINE.md, docs/GLOSSARY.md | delete | PIPELINE.md's "Verb-tag fold-in — Word.mergeInfoVerb (S3.2.1.2)" and GLOSSARY.md's "Identity merge" entry both document this mechanism as shipped, current fact, with the same rationale (LexiqueSynthetic rows folding into existing Words by identity) |
| 117-148 | "NOT yet done" flags (full pipeline not re-run yet, pickle gotcha applies, scale not spot-checked beyond rudoie/parle, frequency-handling decision made implicitly but not confirmed) | history, resolved | delete | All since re-run — PIPELINE.md's "Identity merge" section (S3.2.1) states the final numbers (10,990 rows fold; "the first row's syllabification and frequency win," matching item B9) — the frequency-handling question this file flagged as "not explicitly confirmed" is now confirmed (and flagged as a bug, B9) |
| 149-182 | Repo git-status snapshot at end of session | history | delete | Pure bookkeeping, no durable content |

**Unique durable fact found:** none — the shipped fix (Thread C) is fully and more precisely
documented in PIPELINE.md/GLOSSARY.md, including the bug this file's own "frequency handling
decision" flagged (now B9 in todo.md). Threads A and B are dead-code history with no forward value.

## PLAN_2026-09-18_low_value_discriminators.md (130 lines)

Verdict: **entirely dead design**. An investigation plan for reducing low-coverage features in the
same solver-picks-features path SHARED_DISCRIMINATOR_REWIRE_PLAN.md describes, itself already
"unblocked" by that plan's coverage-first ordering change (which did ship, see B row above). The
whole investigation targets `selectSharedDiscriminators`, `dictionary.py`'s "Special keypress
mapping" table and `satOptimizeDiscriminator`'s `keyAssignment` — none live today.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-46 | Context: rudoie/exclut low-count discriminator cases, root-cause split into Category A (data-bug phantom splits) / B (algorithmic, complexity-first ordering) / C (irreducible rare grammatical slots) | superseded | delete | Category A's root cause (rudoie) is the same bug as NOTES_2026-09-17's Thread C, already fixed and documented (see above). Categories B and C are diagnostic framing for a table (`dictionary.py`'s "Special keypress mapping") that no longer exists in the live pipeline |
| 48-107 | Investigation steps (get current low-count list, classify each feature, validate Category A at scale, quantify Category B), solutions to evaluate per category | superseded | delete | All steps operate on `dictionary.py`'s `LOW_COUNT_THRESHOLD`/`featureWords` printed table and `selectSharedDiscriminators`'s output — both retired from the live path per PIPELINE.md |
| 109-130 | Files in scope, verification steps (pickle deletion, pytest, "track count of features discriminating <60 words") | superseded | delete | Same — targets dead code paths |

**Unique durable fact found:** none. Everything of lasting value (the `rudoie` root cause, the
coverage-first ordering decision) is either already in PIPELINE.md/GLOSSARY.md or flagged as a
possible one-line addition in the SHARED_DISCRIMINATOR_REWIRE_PLAN.md row above.

## Questions for triage

1. Confirm deletion of the whole bundle except the handful of flagged extracts: ATOMIC_KEYPRESS_
   REWIRE_PLAN.md's parler-walkthrough rationale (1 paragraph), the coverage-first ordering fact
   from SHARED_DISCRIMINATOR_REWIRE_PLAN.md §7 (1 line, if still live in `src/featureextractor.py`),
   and DESIGN_alternate_press_sets.md's 17.6% scale figure (1 line). Everything else in this bundle
   is superseded design/implementation detail already captured in docs/specs/*.md and docs/PIPELINE.md.
2. Verify: does `src/featureextractor.py`'s still-live path (Synthetic Lexicon Building (S2) gating,
   `ambiguitychecker` diagnostic) actually still use the coverage-first ordering from
   SHARED_DISCRIMINATOR_REWIRE_PLAN.md §7, or was that also superseded? If live, PIPELINE.md's S2
   section should state it; if dead, drop the flagged extract too.
3. ATOMIC_KEYPRESS_REWIRE_PLAN.md lines 261-320 list bugs from the design phase that may or may not
   match today's B-numbered list exactly (`_isFeasibleAddition` new-vs-new collisions,
   `checkComposedChords` half-combo). Worth a line-by-line diff against todo.md before deleting —
   should this check happen now, or is it already covered (the bugs look like early drafts of B22/
   B25/B26)?
4. The `-er`/`-ers` noun wishlist item appears in both ROADMAP.md and ATOMIC_KEYPRESS_REWIRE_PLAN.md
   verbatim — confirm ROADMAP.md is the one surviving copy.
5. None of these 5 files is referenced by PIPELINE.md, GLOSSARY.md or the specs except as
   "superseded" pointers (discriminating-features.md doesn't even cite them by name). OK to delete
   outright rather than archive under `docs/refactor/`?
</content>
