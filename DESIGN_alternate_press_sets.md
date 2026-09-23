# Design: per-reading alternate press-sets (fixes the `calmez` → `-kt` over-marking bug)

Status: **implemented** (sections 1-4, option (a) for section 4). Companion to
`RESUME_2026-09-21-steno-trainer.md` item 2; supersedes the "pick the smallest press-set" fix
floated there in favor of keeping every valid reading's press as its own theory line.

Implemented in: `src/elicitation.py` (`resolveGroupPressSets`/`serializeResolvedPressSets`/
`validateElicitation`), `src/featuregrouping.py` (all constraint/verification functions), `src/featuregroupingsat.py`
(`GroupSignature`/`groupSignatures`/`_buildDistinctnessModel`), `src/ambiguitychecker.py`
(`buildKeypressGroupToWords` now consumes only the primary alternate; new
`buildKeypressGroupExtraAlternates` + `realizeKeypressGroupsAsExtraStroke`'s new
`extraGroupSetsByWord` parameter realize every other alternate as its own additional physical
stroke, checked against every other word but never against the same word's own other readings),
and `util/build_realization_report.py` (wires the new function through). All touched test
suites updated and passing (571 tests); mypy error count on touched files unchanged from
baseline. Not yet done: regenerating the actual committed `resolved_press_sets.json` /
`keypress_groups.json` / `realization_report.json` artifacts against the
real lexicon (steps 4 and 6 of the suggested order below) — that's a real pipeline run, left for
a deliberate follow-up rather than folded into this implementation session.

## The bug, restated

`resolveGroupPressSets` (`src/elicitation.py:309-356`) keys a homophone group's resolved
press-sets by **orthography only**. When one spelling carries two feature combinations
(homograph readings of the same spelling — "calmez" = impératif 2p *or* indicatif présent 2p),
the loop unions **every** combination's elicited press against every sibling spelling into one
`pressSetByOrtho[ortho]`. The user separately answered "press `impératif`" for the imperative
reading and "press `pers_2`" for the indicative reading — each independently sufficient — and
the union forces both (`-kt`) where either alone would do. Confirmed **not** an elicitation-data
problem (the answers were each minimal); confirmed systemic — 8,413 of 47,827 resolved groups
(~17.6%) show the same shape, essentially every verb with a same-spelling indicatif/impératif
or indicatif/subjonctif pair.

## Chosen direction (per user)

Instead of collapsing a multi-reading spelling to one "canonical" press-set (arbitrary, and
throws away a working discriminator), **keep every distinct per-reading press-set as its own
theory line**. "calmez" becomes two valid physical realizations — `kal/me/-k` *and* `kal/me/-t`
— both decoding to the same output text. This matches `ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s own
vocabulary: *"Readings of the same spelling never conflict with each other — they produce the
same output text."* Nothing needs to arbitrate between them; either is intuitively correct.

## New shared data shape

Everywhere a homophone group currently maps `ortho -> one press-set`, it becomes
`ortho -> list[press-set]` (a non-empty, deduplicated list of alternates; the overwhelmingly
common case is a 1-element list, unchanged from today).

```
PressSetsByOrtho = dict[WordOrtho, list[frozenset[str]]]
```

## 1. `src/elicitation.py`

**`resolveGroupPressSets`**: for each ortho, compute a press-set **per combination** (the
existing union-across-siblings logic, just not merged across the ortho's own combinations),
then dedupe by value:

```python
for homophoneGroupKey, words in homophoneGroups.items():
    combinationsByOrtho = featureCombinationsByOrtho(words)
    orthos = sorted(combinationsByOrtho)
    if len(orthos) < 2:
        continue
    pressByOrthoCombination: dict[tuple[WordOrtho, FeatureCombination], set[str]] = {
        (ortho, c): set() for ortho in orthos for c in combinationsByOrtho[ortho]
    }
    groupIsResolvable = True
    for orthoA, orthoB in combinations(orthos, 2):
        for combinationA in combinationsByOrtho[orthoA]:
            for combinationB in combinationsByOrtho[orthoB]:
                if combinationA == combinationB:
                    continue
                oppositionKey = frozenset({combinationA, combinationB})
                pressByCombination = answersByOpposition.get(oppositionKey)
                if pressByCombination is None:
                    unresolvedOppositions.append(oppositionKey)
                    groupIsResolvable = False
                    continue
                pressByOrthoCombination[(orthoA, combinationA)] |= pressByCombination[combinationA]
                pressByOrthoCombination[(orthoB, combinationB)] |= pressByCombination[combinationB]
    if not groupIsResolvable:
        continue
    pressSetsByGroup[homophoneGroupKey] = {
        ortho: sorted(
            {frozenset(pressByOrthoCombination[(ortho, c)]) for c in combinationsByOrtho[ortho]},
            key=lambda s: (len(s), sorted(s)),
        )
        for ortho in orthos
    }
```

Unresolvable handling is unchanged (any missing opposition still voids the whole group — no
partial per-combination resolution).

**`serializeResolvedPressSets`**: `"pressSets"` becomes `{ortho: [[atom,...], [atom,...], ...]}`
— every ortho's value is a list of lists (was a flat list). `"frequencies"` is untouched (still
one scalar per ortho — frequency is a property of the spelling, not of a reading).

**`validateElicitation` / `GroupConflict`**: a real conflict is now "two *different* orthos
share an identical press-set value among any of their alternates" (same-ortho alternates
colliding with each other is expected and fine — same output text, nothing to distinguish):

```python
owner: dict[frozenset[str], set[WordOrtho]] = defaultdict(set)
for ortho, alternates in pressSetByOrtho.items():
    for alt in alternates:
        owner[alt].add(ortho)
for pressSet, orthos in owner.items():
    if len(orthos) > 1:
        conflicts.append(GroupConflict(homophoneGroupKey, pressSet, tuple(sorted(orthos))))
```

**Tests to update**: `parler_group`'s "parle" (2 combinations: pers_1-reading and the
pers_3s-reading, which already resolves to `frozenset()` today) is the in-repo example of this
exact shape. `test_resolveGroupPressSets_matches_validateElicitations_own_resolution` and
`test_serializeResolvedPressSets_is_json_ready` need their expected value for `"parle"` changed
from `frozenset({"pers_1"})` / `["pers_1"]` to `[frozenset({"pers_1"}), frozenset()]` /
`[["pers_1"], []]` — this is a nice existing example showing "parle" can be typed either
`pers_1`-marked or fully bare.

## 2. `src/featuregrouping.py` (greedy Grouping Phase)

`PressSetsByGroup = dict[str, dict[str, list[frozenset[str]]]]`; `loadResolvedPressSets` parses
the nested list.

- **`liveMarkers`**: unaffected in spirit, just add one more loop level (flatten alternates).
- **`coOccurrencePairs`**: unaffected in spirit — atoms co-occurring **within one alternate**
  still can't share a keypress; loop over `(ortho, alt)` pairs instead of `(ortho, pressSet)`.
- **`wouldCollideIfMergedPairs`**: real semantic change. Only compare alternates belonging to
  **two different orthos** — same-ortho alternates are allowed to look "mergeable" (they're
  meant to converge). Iterate `combinations(orthos, 2)`, then all `(altA, altB)` from those two
  orthos' lists, keeping today's "`onlyInA`/`onlyInB` both size 1" check.
- **`verifyKeypressAssignment`**: for each ortho, compute the *set* of induced values across all
  its alternates; build `owner: dict[induced, set[ortho]]` across the whole group (adding an
  ortho at most once per distinct induced value it reaches); `len(owner[value]) > 1` is a real
  `KeypressConflict`. Mirrors the `validateElicitation` conflict logic above.
- **`_findSharedKeypressPair`**: needs the specific `(ortho, alternate)` pair that produced the
  colliding induced value on each side (not just "the ortho's one true set") — walk each
  conflicting ortho's alternates to find which one induced the reported value, then search that
  alternate's true markers as today.
- **`frequencyWeightedChordSizes`**: attribute the ortho's full frequency to every keypress
  touched by **any** of its alternates (a mild over-count when an ortho has >1 live alternate —
  acceptable given this was already flagged as Realization Phase input, not something Grouping Phase optimizes).

## 3. `src/featuregroupingsat.py` (exact CP-SAT Grouping Phase) — the harder half

Today, `GroupSignature = frozenset[frozenset[str]]` is just "the set of distinct press-sets held
by a group's spellings," and `_buildDistinctnessModel` forces **every pair within a signature**
to induce different touched-keypress sets. That's now wrong: alternates of the *same* spelling
must be **exempt** from this pairwise-distinctness requirement.

Proposed: make a signature a set of *per-spelling* alternate-sets, so the model can tell which
press-sets are allowed to collide:

```python
GroupSignature = frozenset[frozenset[frozenset[str]]]  # { spelling's {alt1, alt2, ...}, ... }

def groupSignatures(pressSetsByGroup):
    return sorted(
        {frozenset(frozenset(alts) for alts in pbo.values()) for pbo in pressSetsByGroup.values()},
        key=...,
    )
```

`_buildDistinctnessModel` then needs distinctness constraints only **across** spellings: for
every pair of *different* spelling-buckets in a signature, every `(altA from bucket A, altB from
bucket B)` pair must still induce different touched-keypress sets — no constraint at all between
two alternates of the *same* bucket. Same XOR-linearization block as today, just scoped to
cross-bucket pairs instead of all pairs. Model size grows mildly (most spellings still have
exactly one alternate), stays tractable at the ~200-distinct-signature scale the module already
banks on.

## 4. `src/ambiguitychecker.py::realizeKeypressGroupsAsExtraStroke` (Realization Phase) — open question

This is the part I have **not** fully worked out and want your read on before implementing.

Today the whole function is built around `wordToGroups: dict[Word, frozenset[int]]` — **one**
fixed set of Grouping-Phase group ids per `Word`, used to compose that word's one physical extra
stroke, with heavy machinery (`_finalizeReadyWords`, composed-cost ranking, the full
finalized-word collision re-check) all assuming that 1:1 shape.

With alternates, a `Word` (well, really a `(word, combination)` reading — but Realization Phase works at
the ortho/Word level, not per-combination) can need **either of two different group-sets** to be
uniquely identified — e.g. "calmez" needs `{group(impératif)}` *or* `{group(pers_2)}`, not both.
That turns `wordToGroups` into a 1:many relation, and every downstream piece that composes a
word's "other already-decided groups" into one physical chord needs to pick **which** of the
word's alternative group-sets it's composing for.

Two ways to go:

- **(a) Realize every alternate physically.** For each `(ortho, alternate group-set)`, run the
  existing composition/collision logic as if that alternate were the word's only need, so a
  homographic ortho gets multiple physical strokes (all outputting the same text) — matches the
  "separate theory line per reading" goal exactly, but means threading a `word -> list[frozenset[int]]`
  mapping through `buildWordToGroups`, `_finalizeReadyWords`, the composed-cost ranking, and the
  final full-assignment verification pass (which currently checks one composed stroke per word;
  needs to check one per alternate instead).
- **(b) Only physically realize alternates that are actually *distinct* after the Grouping-Phase
  keypress bundling** (some alternates may induce the *same* physical keys once bundled onto
  keypresses, in which case there's only one real stroke to realize, not two) — a
  dedup-after-induction step before handing groups to the composer, which could simplify (a)
  by shrinking the list Realization Phase has to realize per word.

I'd lean toward (a) with the (b) dedup as an optimization on top, but this is the piece most
likely to hide a subtlety I haven't hit yet (e.g. interaction with the "biggest, most-constrained
groups processed first" ordering, or with the final full-assignment verification pass), so I
want to scope/read this function in more depth — and possibly write a couple of exercising unit
tests against `ambiguitychecker_test.py`'s existing fixtures — before committing to an approach.

## 5. Downstream consumers (not yet audited in detail)

- `util/build_realization_report.py` — canonical build entrypoint; needs to iterate realized
  alternates per word instead of one stroke per word when writing `realization_report.json`.
- Plover dictionary / theory export (`dictionary.py`'s theory writer, `util/export_plover_dictionary.py`) —
  structurally fine with multiple stroke keys mapping to the same output text (that's already how
  Plover dictionaries work), just needs to actually emit both entries once Realization Phase produces them.
- `util/export_practice_words.py` / steno-trainer — a UX question for later, not a data-model one:
  does drilling "calmez" show/accept either stroke, or pick one canonically for the drill? Related
  to `RESUME_2026-09-21-steno-trainer.md` item 1 (the trainer already has no way to show *which*
  grammatical reading is intended) — worth folding into that same UI work rather than solving here.

## Suggested implementation order

1. `src/elicitation.py` + its tests (self-contained, no other file depends on the old shape
   except through `resolved_press_sets.json`'s schema).
2. `src/featuregrouping.py` + its tests.
3. `src/featuregroupingsat.py` + its tests (the CP-SAT model change).
4. Regenerate `resolved_press_sets.json` (`python -m src.elicitation` or whatever the E6 CLI
   entrypoint is) and re-run Grouping Phase to produce a new `keypress_groups.json`,
   diffing keypress counts/marker groupings against today's committed artifact.
5. Scope and implement `ambiguitychecker.py`'s Realization Phase change (section 4) once 1-3 are solid and
   we've picked (a) vs (a)+(b) above.
6. Rebuild `realization_report.json` (`python -m util.build_realization_report`),
   confirm the 0-residual-same-lemma-collision regression still holds, and check the "calmez"
   case now round-trips through `util/export_practice_words.py` as two strokes.
