# Resume point — 2026-09-19, branch `phase-g-grouping` (E5/E6/Grouping Phase done, model comparison in progress)

Written so a fresh (cleared-context) session can pick up without re-deriving context.
Read together with `ATOMIC_KEYPRESS_REWIRE_PLAN.md` (authoritative plan),
`RESUME_2026-09-19.md` (same-day, EARLIER session: lexicon bug fixes, vocabulary
rename, E4 questionnaire fully answered — superseded here only for what changed
below), and `pers_1PreferedOver_pers_3KeyAssignation` (the model-comparison finding,
now with both models' numbers).

## Where things stand, in one paragraph

Starting from a fully-answered 194-question questionnaire (previous session), this
session implemented **E5 (validate)**, **E6 (persist)**, and **Grouping Phase (grouping)** —
the whole rest of the plan except Realization Phase. All three are working, tested, and
verified against the real 47,799-group lexicon. Along the way, two real bugs were
found and fixed (a group-scoping bug in E5's first draft, and a greedy-coloring
correctness gap in Grouping Phase that only pairwise pre-checks couldn't catch). The user
then asked to compare two elicitation calibrations — the one actually answered
(pers_1 preferred as silent default) versus a hypothetical one (pers_3 preferred as
default) — which is now done and **model 2 (pers_3 default) wins**: same 13 live
markers, K=6 instead of 7. Nothing has been decided yet about *adopting* model 2 as
primary; that's the next open decision. Branch `phase-g-grouping` was created (per
user request, expecting `dictionary.py` to be modified profoundly later) and `main`
was pushed to `origin/main` before branching. All work is committed on this branch,
not yet merged to `main`.

## File inventory (everything needed to continue)

**Planning docs (read first, in this order):**
- `ATOMIC_KEYPRESS_REWIRE_PLAN.md` — the authoritative plan (Elicitation/Grouping/Realization Phases).
- `RESUME_2026-09-19.md` — same-day earlier session (E4 done, lexicon fixes).
- `RESUME_2026-09-19-phaseG.md` — this file.
- `pers_1PreferedOver_pers_3KeyAssignation` — the two-model comparison finding, most
  important document for continuing the "which calibration to adopt" question.
- `GLOSSARY.md` — vocabulary reference (Cluster, Reading, Signature/Press-set).

**Code (all committed on `phase-g-grouping`):**
- `src/elicitation.py` — Elicitation Phase toolkit, now including:
  - `resolveGroupPressSets()` (E5/E6 shared step): per homophone group, unions each
    spelling's press-set from the specific pairwise-opposition answers relevant to
    that group. **Important correctness note**: this is scoped PER GROUP, not
    globally per reading — a reading can legitimately need different presses against
    different partners in different groups. An earlier draft got this wrong (resolved
    one global press-set per reading) and silently broke on any reading appearing in
    >1 distinct opposition; fixed in commit `f4d735b`.
  - `validateElicitation()` (E5): conflicts + unresolved oppositions, built on
    `resolveGroupPressSets`.
  - `buildAnswersByOpposition()`: indexes answered oppositions by the (readingA,
    readingB) pair they were asked about; flags genuine duplicates (same pair,
    disagreeing answers) without flagging a reading needing different presses against
    different partners (that's normal, not an error).
  - `serializeResolvedPressSets()` (E6): the persisted artifact.
  - `AnsweredOpposition`, `GroupConflict` dataclasses.
- `src/featuregrouping.py` — Grouping Phase, new this session:
  - `loadResolvedPressSets()`, `liveMarkers()`, `coOccurrencePairs()` (hard: markers
    ever pressed together can't share a keypress), `wouldCollideIfMergedPairs()`
    (derived: markers that never co-occur but would still collide if merged, via a
    clean "T∪{m1} vs T∪{m2}" set-comparison — the plan's own worked example).
  - `greedyColorMarkers()` (Welsh-Powell), `inducedPressSet()`, `verifyKeypressAssignment()`
    (ground-truth simulation), `_findSharedKeypressPair()` (repair-loop helper).
  - `runFeatureGrouping()`: colors, verifies, and on any conflict repeatedly forces apart one
    implicated marker pair and re-colors, until clean or no progress possible.
    **Important correctness note**: the pairwise pre-checks (`coOccurrencePairs`,
    `wouldCollideIfMergedPairs`) are NOT sufficient alone — found a real case
    (`abaisseraient` needs `{pers_3,nbr_p}`, `abaisserais` needs `{pers_2,pers_1}`,
    neither pair individually unsafe, but both spellings end up touching the same two
    keypresses) that only the verify-and-repair loop catches. Fixed in commit
    `d0c7ffb`. **Do not trust a "0 conflicts" Grouping Phase report from a version of this
    file older than that commit.**
- `util/build_pers3_default_answers.py` — one-off model-2 generator: `transform()`
  (strip pers_3, give pers_1/pers_2 self-markers where they were silently default),
  `repairConflicts()` (minimal, single-atom, single-opposition-record fix per
  distinct conflict pattern — corrected in commit `023cca1` after an earlier version
  over-broadcast fixes to every unrelated opposition mentioning the same reading).
- Tests: `src/test/elicitation_test.py` (18 tests), `src/test/featuregrouping_test.py` (16
  tests, including the `abaisser_VER` regression). 462 tests total, all passing.

**Data files (git-tracked, real data not build artifacts):**
- `elicitation_answers.json` — model 1 (pers_1 default), the actually-answered one.
  194 entries, 0 conflicts, K=7.
- `elicitation_answers_pers3default.json` — model 2 (pers_3 default), mechanically
  derived + one hand-picked minimal repair. 194 entries, 0 conflicts, K=6.
- `pers3default_repair_log.txt` — the single repair action taken (q101 subi/subit,
  added `pers_3`), with rationale for overriding the auto-repair's worse pick (`VER`).
- `pers_1PreferedOver_pers_3KeyAssignation` — the finding + full comparison.

**Generated/regenerable, gitignored:**
- `Dictionary.pickle`, `FirstTheory.pickle`, `FeatureDiscrimator.pickle`.
- `questionnaire.json`, `elicitation_questionnaire.html`,
  `elicitation_questionnaire_pers3default.html`.
- `resolved_press_sets.json` (model 1), `resolved_press_sets_pers3default.json`
  (model 2) — regenerate via `python -m src.elicitation` (writes model 1's) or the
  inline script pattern in this session's transcript (model 2's; not yet a proper
  `__main__` entry point — see "Next steps").

**Published artifacts (external, load-bearing):**
- **Model 1**: https://claude.ai/artifact/AbYKVAYSQ9petdsHAuKY2X — "Élicitation
  sténo", db version 23 as of this session's last write, 194/194 answered and
  reviewed. This is the ORIGINAL artifact from the earlier session; still live and
  correct.
- **Model 2**: https://claude.ai/artifact/MRLF9MBbbQm5KjoXFYpKKG — new artifact this
  session, db version 2, pre-populated with `elicitation_answers_pers3default.json`'s
  answers. Same page code, different db content.
- Known bug in the questionnaire page's JS (both artifacts share the same page code):
  a save-race where the async shared-DB load could overwrite in-progress local edits
  before "Enregistrer" — **fixed** in `util/build_questionnaire_page.py` (see
  `RESUME_2026-09-19.md` for the full story), but if the page is ever regenerated
  from an older version of that script the bug would return.

## Key numbers, both models (verified, not estimates)

|                              | Model 1 (pers_1 default) | Model 2 (pers_3 default) |
|------------------------------|---------------------------|---------------------------|
| Live markers                 | 13                        | 13                        |
| Keypresses (K)                | 7                         | **6**                     |
| Groups validated              | 47,799 / 47,799           | 47,799 / 47,799           |
| Conflicts                     | 0                         | 0                         |

Model 1 keypresses: `{imparfait,pers_2}`, `{conditionnel,future,passé}`,
`{infinitif,pers_3}`, `{impératif}`, `{f,nbr_p}`, `{p}`, `{pers_1,subjonctif}`.

Model 2 keypresses: `{imparfait,pers_2}`, `{infinitif,pers_1,pers_3}`,
`{conditionnel,impératif}`, `{future,passé,subjonctif}`, `{f,nbr_p}`, `{p}`.

Unpressable in both: `VER`, `indicatif`, `m`, `nbr_s`, `participe`, `présent`, `s`.

(Greedy-coloring bundling can vary slightly run to run — non-determinism from Python
set iteration order in `greedyColorMarkers`'s tie-breaks — but K and the
live/unpressable sets are stable.)

## Still open / not yet done

1. **Which model to adopt.** Model 2 has a strictly better K (6 vs 7) with the same
   live-marker count. Not yet decided whether to: (a) adopt model 2 as primary, (b)
   try further calibrations (e.g. pers_2 as default, or other person/mood
   preferences) before deciding, or (c) ask the user which one matches their actual
   writing reflexes better (K is not the only criterion — the plan's whole premise is
   that the mapping must follow how the user's brain actually works, not just
   minimize K).
2. **No proper `__main__`/script exists yet for regenerating model 2's
   `resolved_press_sets_pers3default.json` or re-running Grouping Phase on it** — this
   session did it via ad hoc inline Python each time. If model 2 is adopted, this
   should become a real reusable script (extend `util/build_pers3_default_answers.py`
   or add a `--model` flag somewhere) rather than repeating inline snippets.
3. **Grouping Phase is only greedy-optimal, not proven-minimal.** The plan's own suggested
   next step is a CP-SAT formulation reusing `_colorFeatures`/
   `_minSpecialKeypressesNeeded`'s scaffolding (`src/satoptimizer.py:155-259,262-279`)
   to search for something smaller than K=6/7. Not started.
4. **Grouping Phase's "report frequency-weighted chord sizes" requirement** (from the plan)
   is not implemented — `runFeatureGrouping` reports K and the keypress table but not
   frequency weighting.
5. **Realization Phase (physical realization)** is explicitly deferred per the plan; nothing
   done, nothing expected yet.
6. Two harmless untracked files sit in the repo root: `scratch/callgraph` (old pasted
   transcript, keep-or-delete-freely per earlier session) and
   `sameLemmeHomophoneResolution.txt` (a one-line stray note, never explained —
   worth asking the user about, or just leaving alone).
7. Branch `phase-g-grouping` has not been merged to `main` and not pushed to
   `origin`. The user asked for this branch specifically anticipating profound
   `dictionary.py` changes (for Realization Phase, presumably) — nothing has touched
   `dictionary.py` yet in this branch.

## How to regenerate model 2's derived files (until a real script exists)

```python
import json, pickle
from src.grammar import Syllable
from dictionary import Dictionary
from src.elicitation import (
    AnsweredOpposition, buildAnswersByOpposition, buildLemmaHomophoneGroups,
    resolveGroupPressSets, serializeResolvedPressSets,
)
from src.featuregrouping import runFeatureGrouping, liveMarkers

with open("Dictionary.pickle", "rb") as pfile:
    _d = pickle.load(pfile)
    Syllable.allPhonemeCol = pickle.load(pfile)
    Syllable.phonemeColByPart = pickle.load(pfile)
    Syllable.biphonemeColByPart = pickle.load(pfile)
    Syllable.multiphonemeColByPart = pickle.load(pfile)
with open("FirstTheory.pickle", "rb") as pfile:
    theory = pickle.load(pfile)
homophoneGroups = buildLemmaHomophoneGroups(theory)

records = json.load(open("elicitation_answers_pers3default.json"))
answered = [AnsweredOpposition(frozenset(r["atomsA"]), frozenset(r["checkedA"]),
                                frozenset(r["atomsB"]), frozenset(r["checkedB"]))
            for r in records]
answersByOpposition, dup = buildAnswersByOpposition(answered)
assert not dup
pressSetsByGroup, unresolved = resolveGroupPressSets(homophoneGroups, answersByOpposition)
assert not unresolved
serialized = serializeResolvedPressSets(pressSetsByGroup)
json.dump(serialized, open("resolved_press_sets_pers3default.json", "w"), ensure_ascii=False, indent=1)

pgSets = {f"{e['lemmeGramCat']}@{'|'.join(','.join(map(str,s)) for s in e['strokes'])}":
          {o: frozenset(p) for o, p in e["pressSets"].items()} for e in serialized}
allAtoms = {a for item in json.load(open("questionnaire.json"))
            for a in item["atomsA"] + item["atomsB"]}
result = runFeatureGrouping(pgSets, allAtoms)
print("K:", result.keypressCount, "live:", len(liveMarkers(pgSets)), "conflicts:", len(result.conflicts))
```

(`python -m src.elicitation` alone regenerates model 1's files; it hardcodes
`elicitation_answers.json`/`resolved_press_sets.json`, not model 2's.)
