# Same-Lemma Disambiguation (S3)

Per-stage call graph, Pipeline Call Graph and Glossary (Pass 1b). Terms follow
`00-skeleton.md` §3 (dataset states) and §4 (seed glossary). Anchors checked on branch
`docs-refactor` at 5ae0118. Counts come from read-only snippets run on 2026-09-22 against
the pickles and JSON files present then (another job was regenerating the pickles at
the same time, so the counts may drift a little).

Call codes: `S3.E.n` is Marker Elicitation (Phase E), `S3.G.n` is Marker Grouping
(Phase G), and `S3.P.n` is Marker Stroke Realization (Phase P).

## Overview

```
Marker Elicitation (Phase E) — python -m src.elicitation (src/elicitation.py:527)
S3.E.1 Homophone group building — buildLemmaHomophoneGroups (src/elicitation.py:61)
S3.E.2 Reading enumeration — wordFeatureCombinations / featureCombinationsByOrtho (src/elicitation.py:30, :86)
S3.E.3 Scale report — reportScale (src/elicitation.py:164)
S3.E.4 Questionnaire item selection — buildQuestionnaireItems (src/elicitation.py:220)
S3.E.5 Answer indexing — buildAnswersByOpposition (src/elicitation.py:279)
S3.E.6 Press-set resolution — resolveGroupPressSets (src/elicitation.py:374)
  S3.E.6.1 Per-reading press resolution — resolvePressByCombination (src/elicitation.py:312)
S3.E.7 Press-set conflict validation — validateElicitation (src/elicitation.py:425)
S3.E.8 Per-spelling frequency table — buildFrequencyByGroupOrtho (src/elicitation.py:449)
S3.E.9 Resolved press-set serialization — serializeResolvedPressSets (src/elicitation.py:471)
(side) S3.E.10 Questionnaire page — util/build_questionnaire_page.py main (:521)
(side) S3.E.11 Precedence-spec check — util/check_conjugation_disambiguation_order.py main (:130)
(history) S3.E.12 pers_3-default answer rewrite — util/build_pers3_default_answers.py main (:160)

Marker Grouping (Phase G) — python -m util.build_phase_g_assignment (util/build_phase_g_assignment.py:49)
S3.G.1 Press-set reload — loadResolvedPressSets / loadGroupOrthoFrequencies (src/phaseg.py:33, :48)
S3.G.2 Exact minimum-K grouping — minKeypressesSatWithPriorities (src/phasegsat.py:490)
  S3.G.2.1 Group shape dedup — groupSignatures (src/phasegsat.py:40)
  S3.G.2.2 Minimum-K scan — minKeypressesSat → _feasibleAssignment (src/phasegsat.py:417, :183)
  S3.G.2.3 Distinctness model — _buildDistinctnessModel (src/phasegsat.py:51)
  S3.G.2.4 Hard constraints — _aloneAndMustDifferPairs / _addMustDifferPairs (src/phasegsat.py:120, :108)
  S3.G.2.5 Soft preference tiers — _bestAssignmentWithPriorities (src/phasegsat.py:358)
  S3.G.2.6 Alphabetical tie-break — _breakTiesAlphabetically (src/phasegsat.py:153)
S3.G.3 Ground-truth verification — verifyKeypressAssignment (src/phaseg.py:160)
S3.G.4 Usage weights — frequencyWeightedChordSizes (src/phaseg.py:189)
S3.G.5 Assignment serialization — serializeAssignment (src/phasegsat.py:530)

Marker Stroke Realization (Phase P) — inline Dictionary.buildFinalTheory (dictionary.py:342)
                                    and report build util/build_phase_p_realization.py main (:38)
S3.P.1 Word lookup indexes — buildWordToStrokes / buildWordsByOrthoLemme (src/ambiguitychecker.py:553, :766)
S3.P.2 Keypress group population — buildKeypressGroupToWords (src/ambiguitychecker.py:803)
  S3.P.2.1 Entry-to-Word resolution — _resolveEntryWord (src/ambiguitychecker.py:776)
S3.P.3 Extra alternate population — buildKeypressGroupExtraAlternates (src/ambiguitychecker.py:844)
S3.P.4 Preferred key resolution — resolvePreferredKeysByGroup (src/ambiguitychecker.py:952)
S3.P.5 Coda key search — realizeKeypressGroupsAsExtraStroke (src/ambiguitychecker.py:987)
  S3.P.5.1 Candidate ranking — _bestCandidate (src/ambiguitychecker.py:1177)
  S3.P.5.2 Candidate feasibility — _feasible (src/ambiguitychecker.py:1099)
  S3.P.5.3 Candidate cost — _candidateCost (src/ambiguitychecker.py:1147)
  S3.P.5.4 Word finalization — _finalizeReadyWords (src/ambiguitychecker.py:1066)
  S3.P.5.5 Final verification and residual buckets — (src/ambiguitychecker.py:1219-1258)
S3.P.6 Final induced strokes (inline path only) — buildFinalInducedStrokes (src/ambiguitychecker.py:1261)
S3.P.7 Extra alternate strokes (inline path only) — buildExtraInducedStrokes (src/ambiguitychecker.py:1288)
S3.P.8 Report serialization (report path only) — build_phase_p_realization.main (util/build_phase_p_realization.py:74-112)
```

Same-Lemma Disambiguation (S3) starts from theory 1 and the hand-made elicitation
answers. It ends with final induced strokes: every Word's base strokes plus, when the
Word needs grammatical markers, one extra coda-bank stroke. Marker Elicitation (Phase
E) finds every homophone group (words with the same `lemmeGramCat` and the same
canonical Strokes). For each spelling it turns the person's per-opposition checkbox
answers into a list of alternate press-sets (resolved press-sets). Marker Grouping
(Phase G) maps the 13 live markers onto the smallest number K of keypress groups, so
that no two spellings of one group still press the same thing (K=7 today). Marker
Stroke Realization (Phase P) then gives each keypress group one physical coda-bank key.
It does this greedily, largest group first, under collision checks, and appends one
extra stroke per marked Word. The stage exists because theory 1 cannot tell apart the
inflected forms of one paradigm (dors/dort, finis/finit). Their `lemmeGramCat` is the
same, so Lemma-Homophone Marking (S4) does not handle them either.

## Calls

### Marker Elicitation (Phase E)

Entry: `python -m src.elicitation`, `__main__` at src/elicitation.py:527. Loads
`Dictionary.pickle` (the 4 `Syllable` class collections are restored, :538-543) and
`FirstTheory.pickle` (:545-546). Nothing is asked of the user: the run regenerates
questionnaire items and applies the stored elicitation answers.

### Homophone group building — buildLemmaHomophoneGroups (S3.E.1)   src/elicitation.py:61
Called by: Marker Elicitation (Phase E) entry (src/elicitation.py:548); also by
`check_conjugation_disambiguation_order.main` (:148) and `build_pers3_default_answers.main` (:169).
Input state: theory 1, 80,725 raw-Strokes keys, 167,639 Words.
Transformation: re-keys theory 1 by canonical form (`canonicalizeStrokes` keyboard.py:31),
because two raw keys can be the same physical chord. Each canonical bucket is then split
by `lemmeGramCat` (`groupWordsByLemme` word.py:414), keeping only sub-groups with more
than one Word. Different-`lemmeGramCat` homophones are not grouped here; they belong to
Lemma-Homophone Marking (S4).
Result: same-lemma homophone groups, `dict[(canonical Strokes, LemmeGramCat), list[Word]]`,
47,830 groups. Order: theory 1 insertion order, which is deterministic for a given pickle.
Helpers not expanded: `canonicalizeStrokes` (keyboard.py:31), `groupWordsByLemme` (word.py:414).
Notes: the key type is named `LemmaHomophoneGroupKey` (:24) even though it identifies a
same-lemma group (see skeleton §5).

### Reading enumeration — wordFeatureCombinations / featureCombinationsByOrtho (S3.E.2)   src/elicitation.py:30, :86
Called by: every Marker Elicitation (Phase E) step that walks a group (S3.E.3, S3.E.4, S3.E.6.1, S3.E.6).
Input state: one Word, or one homophone group's Word list.
Transformation: a Word with `_infoVerb` yields one reading per verb tag. The tags are
split into markers by `Word.splitInfoVerb` (word.py:102), e.g. `ind:pre:1p` →
{indicatif, présent, pers_1, nbr_p}. Only participle readings also receive the Word's
gender and number and a `VER` marker (:47-51), so a finite reading of the same Word
never inherits `m`/`s`. Subjonctif imparfait readings are dropped (:56), a scope
decision taken on 2026-09-19. A Word without verb tags yields one reading,
{gender, number}, which can be empty. `featureCombinationsByOrtho` groups the distinct
readings by spelling, so all Words that share an `ortho` are merged into one reading
list.
Result: `dict[WordOrtho, list[Reading]]` per group, where a Reading is a
`frozenset[str]` of markers.
Notes: after this merge, Marker Elicitation (Phase E) reasons per spelling, but Marker
Stroke Realization (Phase P) must map a spelling back to one Word. See spelling twins
and the S3.P.2.1 bug.

### Scale report — reportScale (S3.E.3)   src/elicitation.py:164
Called by: Marker Elicitation (Phase E) entry (:549).
Input state: same-lemma homophone groups.
Transformation: enumerates every cross-spelling reading pair (`enumerateOppositionSamples`
:107) and counts: distinct oppositions, tie oppositions (two spellings with the same
reading, which no marker can separate), maximum reading size, and marker pairs that
co-occur. It also runs two Welsh-Powell greedy colorings (`_greedyColorCount` :126) as a
rough K estimate.
Result: console output only. Nothing else consumes it.
Notes: the printed labels say "K lower bound" (:560-561), but the function's own
docstring (:127-129) says a greedy coloring gives an upper bound. Tie order follows set
iteration over strings, which changes per process; this is harmless because the output
is printed only.

### Questionnaire item selection — buildQuestionnaireItems (S3.E.4)   src/elicitation.py:220
Called by: Marker Elicitation (Phase E) entry (:570).
Input state: same-lemma homophone groups.
Transformation: produces one example pair per distinct opposition (an unordered pair of
different readings). The pair is scored by (count of "clean" spellings, meaning spellings
with only this one reading in the group, then the summed corpus frequency). The best
pair is kept, and items are ranked by frequency and given positional ids `q0…`.
Result: questionnaire items, 200 today. Written to `questionnaire.json` (:572-573).
Artifacts: writes `questionnaire.json` (gitignored).
Notes: the ids are renumbered on every run. `elicitation_answers.json` stores `id`,
`orthoA/B`, `lemma`, `reviewed` and `clean`, but resolution uses only
`atomsA/B` + `checkedA/B` (:578-584). The `reviewed` flag is ignored, so an unreviewed
answer counts the same as a reviewed one.

### Answer indexing — buildAnswersByOpposition (S3.E.5)   src/elicitation.py:279
Called by: Marker Elicitation (Phase E) entry (:585).
Input state: elicitation answers (200 records), turned into `AnsweredOpposition`
(`combinationA`=atomsA, `pressA`=checkedA, …).
Transformation: indexes the answers by opposition key `frozenset({readingA, readingB})`.
Two answers to the same key that disagree are reported as a duplicate and dropped.
Answers that agree are collapsed into one.
Result: `AnswerByOpposition` (200 keys, 0 duplicates today) plus the list of duplicates.
Artifacts: reads `elicitation_answers.json` (tracked; loaded at :576-577).

### Press-set resolution — resolveGroupPressSets (S3.E.6)   src/elicitation.py:374
Called by: Marker Elicitation (Phase E) entry (:586), and again inside S3.E.7.
Input state: same-lemma homophone groups + `AnswerByOpposition`.
Transformation: calls S3.E.6.1, then collapses the per-reading presses to one list per
spelling. It deduplicates and sorts by (size, sorted markers), so index 0 is the
smallest press-set: the **primary alternate**. A self-homograph spelling ("calmez":
impératif or indicatif 2p) therefore keeps one alternate per distinct reading press
instead of their union. This is the calmez/`-kt` fix. A spelling whose primary alternate
is empty (`∅`) is the group's canonical member.
Result: resolved press-sets, in memory `dict[LemmaHomophoneGroupKey, dict[WordOrtho,
list[frozenset[str]]]]`, 47,828 groups. 9,692 spellings have more than one alternate.
4,858 groups have no `∅` member, so every spelling in them is marked.

#### Per-reading press resolution — resolvePressByCombination (S3.E.6.1)   src/elicitation.py:312
Called by: Press-set resolution (S3.E.6); Marker Elicitation (Phase E) entry (:616, for
the `readings` field); `check_conjugation_disambiguation_order.main` (:161).
Input state: as S3.E.6.
Transformation: skips groups with fewer than 2 spellings (2 groups today, where two Words
share one spelling). For each cross-spelling pair of different readings, it looks up that
exact opposition's answer and unions each side's checked markers into that
(spelling, reading)'s running press. Tie oppositions (identical readings) are skipped
(:356-357). A missing opposition marks the whole group unresolvable (:360-363), and the
group is left out.
Result: `dict[group, dict[(ortho, Reading), frozenset[str]]]` + unresolved oppositions
(0 today).
Notes: a reading's press is scoped to its group, and is the union across every partner
spelling in that group. Groups that cannot be resolved are dropped silently from the
output. Their Words then keep their base strokes, and no later check sees them (see the
invariant note in S3.P.5.5).

### Press-set conflict validation — validateElicitation (S3.E.7)   src/elicitation.py:425
Called by: Marker Elicitation (Phase E) entry (:587).
Input state: as S3.E.6 (it recomputes S3.E.6 internally).
Transformation: within each resolved group, flags any press-set that is held (as any
alternate) by two different spellings: a `GroupConflict` (:414). Two alternates of the
same spelling may be equal.
Result: conflicts (0 today). The entry drops conflicting groups from the output (:611-614).
Notes: S3.E.6.1 runs three times per invocation (:586, inside :587, :616). This is
wasted work, but the results agree.

### Per-spelling frequency table — buildFrequencyByGroupOrtho (S3.E.8)   src/elicitation.py:449
Called by: Marker Elicitation (Phase E) entry (:615).
Input state: homophone groups + `Dictionary.frequentWords` (the top-200 brief candidates).
Transformation: gives each spelling the maximum `Word.frequency` among its Words. The
top-200 brief candidates are set to 0.0, so they do not inflate the keypress usage weights.
Result: `dict[group, dict[ortho, float]]`, used only by Marker Grouping (Phase G)'s
usage-weight report (S3.G.4).

### Resolved press-set serialization — serializeResolvedPressSets (S3.E.9)   src/elicitation.py:471
Called by: Marker Elicitation (Phase E) entry (:617).
Input state: conflict-free resolved press-sets + frequencies + per-reading presses.
Transformation: writes one entry per group: `strokes` (canonical), `lemmeGramCat`,
`pressSets` (ortho → list of sorted marker lists), `frequencies`, and `readings`. The
`readings` list is parallel to `pressSets` and gives, for each alternate, the readings
that resolved to it. Entries are sorted by `lemmeGramCat` only (a stable sort, so ties
keep theory 1 order).
Result: resolved press-sets on disk, 47,828 entries (about 32 MB).
Artifacts: writes `resolved_press_sets.json` (gitignored) at :620.
Notes: `readings` is read only by the trainer exporters, never by Marker Grouping
(Phase G) or Marker Stroke Realization (Phase P).

### Questionnaire page — build_questionnaire_page.main (S3.E.10)   util/build_questionnaire_page.py:521
Called by: a person, in the human loop (skeleton §1 step 4h).
Input state: questionnaire items.
Transformation: reads `questionnaire.json` at import time (:12) and injects the items and
the French marker labels (`LABELS` :15) into an HTML/JS page. On the page, each item shows
two spellings with their marker checkboxes. Answers are saved to the Artifact `db`
capability document `progress/answers` (:478, :511). A person then copies the answers into
`elicitation_answers.json` by hand. No code in the repo reads the `db` document back.
Artifacts: reads `questionnaire.json` / writes `elicitation_questionnaire.html`.

### Precedence-spec check — check_conjugation_disambiguation_order.main (S3.E.11)   util/check_conjugation_disambiguation_order.py:130
Called by: a person (optional validator, skeleton §1 "(opt)").
Input state: theory 1 + elicitation answers. It recomputes S3.E.1, S3.E.5 and S3.E.6.1
itself and does not read `resolved_press_sets.json`.
Transformation: `parsePrecedenceOrder` (:43) reads `conjugation_disambiguation_order.txt`
up to its `---` line. The line order is supposed to mean precedence, but the code uses
the parsed list only to build the marker vocabulary (:137), for an "unknown atoms"
report. **Precedence is neither enforced nor checked anywhere.** `classifyCombination`
(:63) puts each reading in one family, and `checkPressByOrthoCombination` (:90) applies
three rules to each (spelling, reading) press:
(1) a participle reading whose gender and number are ⊆ {m, s} must have an empty press;
(2) a non-empty impératif or infinitif press must be exactly that single marker;
(3) a non-empty subjonctif press must contain `subjonctif` plus at most one `pers_*` or
`nbr_*` clarifier.
Result: console summary + `conjugation_disambiguation_report.json` (gitignored). The
script only reports and never rewrites any answer.
Artifacts: reads `conjugation_disambiguation_order.txt`, `elicitation_answers.json`, pickles /
writes `conjugation_disambiguation_report.json`.
Notes: the elicitation code itself never consults the spec. The only thing that encodes
the precedence is which checkboxes the person ticked.

### pers_3-default answer rewrite — build_pers3_default_answers.main (S3.E.12)   util/build_pers3_default_answers.py:160
Called by: nobody. A one-off run on 2026-09-19.
Transformation: took `elicitation_answers_pers1default.json` and removed `pers_3` from
every press. Opposite sides left empty received their own `pers_1`/`pers_2`. It then
auto-repaired group conflicts through S3.E.7 and **overwrote** `elicitation_answers.json`
(:177-178).
Notes: history only. Rerunning it would undo later hand fixes (see the skeleton's
observations).

### Marker Grouping (Phase G)

Entry: `python -m util.build_phase_g_assignment`, `main` at util/build_phase_g_assignment.py:49.
A **marker** is one grammatical value from a reading (`pers_2`, `nbr_p`, `f`, …). A
marker is **live** if some resolved press-set contains it (13 today). The other 7
markers that appear in the questionnaire (`VER`, `indicatif`, `m`, `nbr_s`, `participe`,
`présent`, `s`) are **unpressable**, because nobody ever checked them. A keypress group
bundles markers: pressing it asserts every marker it carries. There is a **keypress
conflict** (`KeypressConflict` phaseg.py:150) when two different spellings of one
homophone group induce the same set of keypress groups.

### Press-set reload — loadResolvedPressSets / loadGroupOrthoFrequencies (S3.G.1)   src/phaseg.py:33, :48
Called by: Marker Grouping (Phase G) entry (:53-54).
Input state: resolved press-sets on disk.
Transformation: re-keys each entry by the opaque id `lemmeGramCat@strokes` (strokes
flattened to text) and turns alternates into frozensets. The frequencies go into a
parallel map.
Result: `PressSetsByGroup` (47,828 groups) + `FrequencyByGroup`. The entry also reads
`questionnaire.json` (optional, :57-61) to get the full marker inventory used to list
unpressable markers.
Artifacts: reads `resolved_press_sets.json`, `questionnaire.json`.

### Exact minimum-K grouping — minKeypressesSatWithPriorities (S3.G.2)   src/phasegsat.py:490
Called by: Marker Grouping (Phase G) entry (:63-65), with `ALONE_KEYS`={f},
`MUST_DIFFER_GROUPS`={{infinitif, pers_1, pers_2, pers_3}} and `PREFERENCE_TIERS`
(build_phase_g_assignment.py:39-45).
Input state: `PressSetsByGroup`.
Transformation: live markers are sorted alphabetically (:511). The problem is reduced to
group shapes (S3.G.2.1). Step 1 finds the true minimum K under the hard constraints only
(S3.G.2.2). Step 2 applies the soft tiers at that K, one after another (S3.G.2.5), then
the alphabetical tie-break (S3.G.2.6).
Result: `(numKeys=7, colorOf: marker → keypress id, achieved=[1, 1, 0])`.

#### Group shape dedup — groupSignatures (S3.G.2.1)   src/phasegsat.py:40
Transformation: reduces each group to its shape, a frozenset of per-spelling sets of
alternates (the code calls it `GroupSignature`). Spellings, strokes and lemmas are
dropped, and the shapes are deduplicated and sorted canonically.
Result: 294 distinct shapes, down from 47,828 groups. The module docstring (:17-20) still
says "47,799 groups … ~200".

#### Minimum-K scan — minKeypressesSat → _feasibleAssignment (S3.G.2.2)   src/phasegsat.py:417, :183
Transformation: for numKeys = 1, 2, …, 20, builds the distinctness model plus the hard
constraints and solves it. INFEASIBLE means try the next K. The first FEASIBLE K is the
proven minimum. UNKNOWN (the 30 s limit per solve) raises instead of guessing (:226-229).
This is how **K is chosen**: it is the smallest K that is feasible under the hard rules.
Result: K=7 today.

#### Distinctness model — _buildDistinctnessModel (S3.G.2.3)   src/phasegsat.py:51
Transformation: Booleans `x[m,k]` with exactly one keypress per marker. For each shape and
each press-set, `t[k]` = "this press touches keypress k" (a max over its markers). For
every pair of press-sets that belong to **different** spellings, at least one `k` must
have `t` values that differ (an exact XOR linearization, :96-103). Alternates of the same
spelling are exempt. This models exactly what `verifyKeypressAssignment` checks (S3.G.3).

#### Hard constraints — _aloneAndMustDifferPairs / _addMustDifferPairs (S3.G.2.4)   src/phasegsat.py:120, :108
Transformation: expands `aloneKeys` into (m, every other live marker) pairs, and
`mustDifferGroups` into all pairs within each group. Each pair gets
`x[m1,k] + x[m2,k] ≤ 1` for every k. These constraints can raise K.

#### Soft preference tiers — _bestAssignmentWithPriorities (S3.G.2.5)   src/phasegsat.py:358
Transformation: optimizes lexicographically at the fixed K. Tier 0 maximizes {p, nbr_p}
on the same keypress. Tier 1 maximizes {future, passé} on the same keypress. Tier 2
minimizes how many other markers share the keypress of {nbr_p, p} (`_sameKeyScoreExpr`
:308, `_exclusiveGroupExtraCountExpr` :329). Each tier's result is locked with an
equality constraint before the next tier runs (:405). These tiers cannot raise K.

#### Alphabetical tie-break — _breakTiesAlphabetically (S3.G.2.6)   src/phasegsat.py:153
Transformation: for each marker in alphabetical order, minimizes its keypress index and
then locks it. The solver is single-threaded with seed 0 (`_newDeterministicSolver` :139).
**Determinism:** the result is the lexicographic minimum over all optimal colorings, so
it is unique, provided every solve returns OPTIMAL. See the suspected bug about accepting
FEASIBLE.

### Ground-truth verification — verifyKeypressAssignment (S3.G.3)   src/phaseg.py:160
Called by: Marker Grouping (Phase G) entry (:69). Also by tests and the greedy
`runPhaseG`.
Transformation: for every group and every alternate, computes the induced press-set
(`inducedPressSet` :135, the union of the full keypress groups touched) and reports a
keypress conflict when two spellings induce the same set. Any conflict aborts the write
(:70-71).
Result: `[]` today.

### Usage weights — frequencyWeightedChordSizes (S3.G.4)   src/phaseg.py:189
Called by: Marker Grouping (Phase G) entry (:74).
Transformation: for each keypress group, sums the frequency of every spelling whose true
alternates touch it. The result is only reported: Marker Stroke Realization (Phase P)
does not read `frequencyWeightedChordSizes`, since it recomputes its own
frequency-weighted costs.

### Assignment serialization — serializeAssignment (S3.G.5)   src/phasegsat.py:530
Called by: Marker Grouping (Phase G) entry (:76-82).
Result: keypress groups, `phase_g_keypress_assignment.json` (tracked): `keypressCount` 7,
`markersByKeypress` {0: conditionnel+infinitif, 1: f, 2: future+passé+pers_3,
3: imparfait+subjonctif, 4: impératif+pers_1, 5: nbr_p+p, 6: pers_2}, the hard and soft
provenance, 7 unpressable markers, and usage weights.
Artifacts: writes `phase_g_keypress_assignment.json`.
Notes on **K = 5 / 6 / 7**: CLAUDE.md:56 says "K=5, proven optimal". The
build_phase_g_assignment.py:18 docstring says "still K=6". build_pers3_default_answers.py:9
says "model 2 (K=6)". phasegsat.py:7 says "K=6/7". ambiguitychecker.py:998 and :1060
mention "Phase G's 6 groups". The artifact history in git gives the real values: K=5
at 8330b8e and 0fa69af; K=6 from 4e73533 (the elicitation fix of the impératif answers)
through feb0e2b and 869a0c9; **K=7 from 688c74d** (the per-reading alternates fix),
unchanged through b1e02ed, 3b22e0f and a1d0fb5 (HEAD). The claim "the hard constraints
didn't cost anything extra" was checked at K=6. Nobody has re-checked it at K=7.
The greedy `src/phaseg.py` path is **not live** (see Dead-code observations). The live
path uses only phaseg's loaders, `liveMarkers`, `verifyKeypressAssignment`,
`inducedPressSet` and `frequencyWeightedChordSizes`.

### Marker Stroke Realization (Phase P)

The same sequence of calls runs on two code paths: inline in
`Dictionary.buildFinalTheory` (dictionary.py:373-389, which feeds theory 2 and every
exporter through util/_theoryio.py:82), and in the report build
`util/build_phase_p_realization.py` main (:58-72). Both read
`phase_g_keypress_assignment.json` and `resolved_press_sets.json`.

**The realization rule, in plain words.** Each keypress group gets one physical key-set.
The candidates are the coda-bank chords of the 20 consonant phonemes on the Starboard:
the single keys 16-25 and the digraphs (16,17), (16,18), (17,19), (18,19), (20,22),
(22,23), (24,25). Pairs of those are tried only when no single candidate fits. A Word
whose primary alternate touches groups {g1, g2, …} gets **one extra trailing stroke**:
the sorted union of those groups' keys, appended after its base strokes
(`_appendCodaExtraStroke` :892). Its existing last stroke is left unchanged. Groups are
decided greedily, largest population first. A candidate is feasible (S3.P.5.2) when it:
- differs from every key-set already chosen;
- is not a no-op for any Word;
- forms a legal chord with the Word's other groups;
- does not recreate an existing theory-1 key;
- does not cause a same-`lemmeGramCat` collision among Words that need the same full set
  of groups, or against an already-finalized Word.

Cost (S3.P.5.3) is the frequency-weighted average `getStrokeCost` of the real composed
extra chord. A human preferred key per marker (`PREFERRED_KEYS_BY_MARKER` :945:
impératif → 18 `-k`, pers_2 → 19 `-d`, pers_3 → 20 `-t`) wins whenever it is feasible.

### Word lookup indexes — buildWordToStrokes / buildWordsByOrthoLemme (S3.P.1)   src/ambiguitychecker.py:553, :766
Called by: both paths (dictionary.py:373-374; build_phase_p_realization.py:58-59).
Result: `Word → raw base strokes` and `(ortho, lemmeGramCat) → [Word]`, both in theory 1
order.
Helpers not expanded: both are one-line index builders.

### Keypress group population — buildKeypressGroupToWords (S3.P.2)   src/ambiguitychecker.py:803
Called by: both paths (dictionary.py:375; build_phase_p_realization.py:60).
Input state: resolved press-sets (JSON list) + `markersByKeypress`.
Transformation: for each spelling, uses only its **primary alternate** `alternates[0]`
(:832). An empty primary (the canonical member) is skipped. The spelling is resolved to one
Word (S3.P.2.1), which is appended to every keypress group whose markers intersect the
primary press-set.
Result: keypress group population `groupToWords` (affected Words per group today:
g5 48,724; g1 15,295; g2 11,735; g4 7,334; g6 6,707; g0 3,922; g3 3,882).

#### Entry-to-Word resolution — _resolveEntryWord (S3.P.2.1)   src/ambiguitychecker.py:776
Called by: S3.P.2 and S3.P.3.
Transformation: among the Words with this (ortho, lemmeGramCat), returns the **first**
Word whose canonical base strokes equal the entry's canonical `strokes`. If none matches,
it falls back to `candidates[0]` (:800).
Result: exactly one Word per spelling, even when the spelling has several Words.
Notes: see the spelling-twin bug below. There are 230 spellings where two Words match and
only the first one is marked.

### Extra alternate population — buildKeypressGroupExtraAlternates (S3.P.3)   src/ambiguitychecker.py:844
Called by: both paths (dictionary.py:376-378; build_phase_p_realization.py:65-67).
Transformation: for spellings with 2 or more alternates, maps each non-primary, non-empty
alternate to the set of keypress groups its markers touch.
Result: `extraGroupSetsByWord: Word → [frozenset[group id]]` (the second half of the
keypress group population state).

### Preferred key resolution — resolvePreferredKeysByGroup (S3.P.4)   src/ambiguitychecker.py:952
Called by: both paths (dictionary.py:379; build_phase_p_realization.py:68).
Transformation: maps each marker in `PREFERRED_KEYS_BY_MARKER` to the group that holds it
in this run, because group ids can change between runs of Marker Grouping (Phase G).
Markers that are not live are skipped.
Result: {4: (18,), 6: (19,), 2: (20,)} today.

### Coda key search — realizeKeypressGroupsAsExtraStroke (S3.P.5)   src/ambiguitychecker.py:987
Called by: both paths (dictionary.py:380-383; build_phase_p_realization.py:69-72).
Input state: keypress group population + theory 1 + keyboard layout + preferred keys.
Transformation: builds `wordToGroups` (`buildWordToGroups` :882), the per-phoneme coda
candidates (`codaKeysOf`, in `Phoneme.consonantPhonemes` string order, which is
deterministic) and `allWords`, the **set** of every Word in any group (:1047). It then
decides the groups in descending population order (:1205). For each group it takes
`ranked[0]` from S3.P.5.1 as the choice; if nothing is feasible, the group goes to
`unassignedGroups`. Words whose groups are all decided are then finalized (S3.P.5.4).
Last, it runs the final verification (S3.P.5.5).
Result: physical keypress assignment (`KeypressGroupPhysicalAssignment` :904). Today:
g0→21, g1→16, g2→20, g3→23, g4→18, g5→17, g6→19. All seven are single keys, and all
three preferences were honored.
Helpers not expanded: `_composedInduced` (:1077, the union of a candidate with a Word's
other decided groups), `_isRedundantForAnyWord` (:1084), `buildWordToGroups` (:882),
`_appendCodaExtraStroke` (:892), `Keyboard.getStrokeCost` (keyboard.py:547).

#### Candidate ranking — _bestCandidate (S3.P.5.1)   src/ambiguitychecker.py:1177
Transformation: tries every distinct single-phoneme coda chord and keeps the feasible
ones with their cost. Only if none is feasible does it try 2-phoneme unions
(`comboSize`=2). The list is sorted by cost (a stable sort, so ties keep phoneme order,
:1192). A preferred key that is already in the list moves to the front (:1195-1197). A
preferred key outside the list is inserted first if it is feasible (:1198-1200).
Otherwise the preference is recorded as not honored (:1201-1202).

#### Candidate feasibility — _feasible (S3.P.5.2)   src/ambiguitychecker.py:1099
Transformation: rejects a candidate if any of these holds:
(a) it equals a key-set already chosen (:1104);
(b) it is empty, or redundant for some Word;
(c) some Word's composed extra chord is not a legal keypress (`getStrokeCost` returns
None, :1112);
(d) some composed Strokes is an existing theory-1 key (raw comparison, :1114);
(e) there is an in-scope collision (`_isInScopeCollision` :968: different ortho, same
`lemmeGramCat`) among Words with the same full group set (:1125-1133);
(f) there is an in-scope collision with an already finalized Word (:1140-1144).
Cross-category and cross-lemma collisions never block a candidate.

#### Candidate cost — _candidateCost (S3.P.5.3)   src/ambiguitychecker.py:1147
Transformation: returns `round(Σ freq·cost(composed extra chord) / Σ freq)` over the
group's Words. When the total weight is zero, it uses the candidate's isolated cost. Using
the real composed chord lets a same-column combination earn the keyboard's discount.

#### Word finalization — _finalizeReadyWords (S3.P.5.4)   src/ambiguitychecker.py:1066
Transformation: when every group a Word needs has been processed, its composed stroke is
fixed and indexed in `finalizedWordsByStroke`. This catches cases where the union for a
multi-group Word equals another group's own key-set. It iterates the `allWords` set, but
the order changes only list order inside the index, not any decision.

#### Final verification and residual buckets — (S3.P.5.5)   src/ambiguitychecker.py:1219-1258
Transformation: for each Word in `allWords` (set iteration, :1227), composes the final
primary stroke `(word, 0)` and one stroke `(word, i)` per extra alternate (:1232-1241).
`residualTheoryCollisions` lists marked Words whose composed stroke is a theory-1 key
(raw comparison, sorted by ortho, :1243). `findCollidingInducedStrokes` (:727) then
pairs each key with the **first key seen** on the same stroke. Each pair goes into one
bucket: in-scope `residualCollisions` (:1248), `crossCategoryClashCollisions` (same bare
lemme, different `lemmeGramCat`, :1251), or `crossLemmaCollisions` (different lemme,
:1255). Pairs with the same ortho are dropped.
Result: residual buckets. Today: 0 theory collisions, 0 same-`lemmeGramCat`, 34 or 40
cross-category clashes, and 1,283 cross-lemma collisions. These buckets depend on the
run; see the bugs below.
Notes, **the "0 residual same-`lemmeGramCat` collisions" invariant**: this is
`len(assignment.residualCollisions) == 0`. It is checked **only** by the report build,
which prints and persists it (build_phase_p_realization.py:89-91, :108, :129), and by unit
tests on fixtures (src/test/ambiguitychecker_test.py:844 and others). Nothing asserts it on
the real lexicon. `buildFinalTheory` throws away `residualCollisions` and
`unassignedGroups` (dictionary.py:380-389). The check covers only the Words in
`allWords`, which excludes canonical members, the spelling twins that were not chosen,
and the Words of groups dropped by Marker Elicitation (Phase E). It also sees only
first-seen pairs. A read-only all-pairs check on canonical strokes over the whole
lexicon (committed chosen keys) finds **229** real same-`lemmeGramCat` collisions in the
final induced strokes. Examples: abasourdi/abasourdis and agi/agis, all caused by
spelling twins.

### Final induced strokes — buildFinalInducedStrokes (S3.P.6)   src/ambiguitychecker.py:1261
Called by: `Dictionary.buildFinalTheory` only (dictionary.py:384).
Input state: theory 1 + keypress group population + physical keypress assignment.
Transformation: for **every** Word in theory 1 (dict order, deterministic): if the Word
needs groups, appends one extra stroke holding the union of their chosen keys. Otherwise
the Word keeps its base strokes. Groups left unassigned add nothing, silently.
Result: final induced strokes, `dict[Word, Strokes]`, 167,639 Words, of which 79,449
carry an extra stroke. This is handed to Lemma-Homophone Marking (S4)
(`composeReservedKeyStrokes`, dictionary.py:385).

### Extra alternate strokes — buildExtraInducedStrokes (S3.P.7)   src/ambiguitychecker.py:1288
Called by: `Dictionary.buildFinalTheory` only (dictionary.py:389).
Transformation: for each extra alternate of a self-homograph, builds base strokes plus
one extra stroke with the union of the chosen keys of that alternate's groups.
Result: `dict[Word, list[Strokes]]`, appended after index 0 in theory 2. These strokes do
not go through Lemma-Homophone Marking (S4) (a documented scope gap).
Notes: the docstring (:1303) says the `*`/`#` track "isn't yet wired into
dictionary.py's persisted output". That is stale; see the skeleton.

### Report serialization — build_phase_p_realization.main (S3.P.8)   util/build_phase_p_realization.py:38
Called by: a person (skeleton §1 step 6).
Transformation: for each group, in id order: markers, `affectedWords`, `chosenKeys`,
`cost`, and ranked `alternates`. It then writes the four residual buckets as ortho pairs,
in whatever order S3.P.5.5 produced them.
Artifacts: reads pickles, `starboard3h.json`, `phase_g_keypress_assignment.json`,
`resolved_press_sets.json` / writes `phase_p_keypress_realization.json` (tracked).
Its only pipeline reader is export_keyboard_layout.py:128 (the trainer legend, which uses
only `keypressGroups`).

### Canonical member: where the unmarked spelling is chosen

The **live** choice comes entirely from the elicitation answers. For each opposition,
the person decides which side needs nothing (for example, the first answer record:
`il` {m,s} checked `[]` versus `ils` {m,p} checked `[p]`). Through S3.E.6.1 and S3.E.6,
a spelling whose union press is empty becomes the `∅` primary alternate, which is the
canonical member. S3.P.2 skips it, so it keeps its base strokes. No code computes it.
4,858 groups have no canonical member at all. `conjugation_disambiguation_order.txt` only
states the intended default ("m" / "m s" first). `check_conjugation_disambiguation_order.py`
checks this afterwards for participles only.
- `FEATURE_PRIORITY` (src/greedyoptimizer.py:16) is **not live**. It feeds only
  `_selectCanonicalIndex` (src/ambiguitychecker.py:557, used by the Phase 0 diagnostic
  `buildAtomicFeatureToWords` :568 → `ambiguitychecker.__main__` :1385-1389) and the
  orphaned `assignDiscriminatorKeypresses` (greedyoptimizer.py:196/:305).
- `GRAMCAT_PRIORITY` (greedyoptimizer.py:62) is live, but only in Lemma-Homophone Marking
  (S4) (`decideStarHashMark`, ambiguitychecker.py:227-228). It never picks the canonical
  member of a same-lemma group.

## New glossary terms

- **Primary alternate** — Index 0 of a spelling's sorted alternate list (smallest press-set
  first). It is the only one that drives Marker Stroke Realization (Phase P)'s key search.
  *`resolveGroupPressSets` elicitation.py:404-407; `buildKeypressGroupToWords` ambiguitychecker.py:832.*
- **Tie opposition** — Two different spellings in one homophone group with the same
  reading. No marker can separate them. It is skipped during resolution. *elicitation.py:183, :356.*
- **Unresolved opposition** — An opposition that some group needs but that has no answer
  (or has a disagreeing duplicate answer). Its whole group is dropped. *elicitation.py:360-363.*
- **Press-set conflict** — Two different spellings of one group that hold the same
  resolved press-set. The group is dropped. *`GroupConflict` elicitation.py:414.* Preferred
  over "group conflict".
- **Keypress conflict** — Two different spellings of one group that induce the same set
  of keypress groups after bundling. *`KeypressConflict` phaseg.py:150.*
- **Induced press-set** — Every marker asserted when a spelling's true markers are
  pressed through their keypress groups (the union of the touched groups).
  *`inducedPressSet` phaseg.py:135.*
- **Group shape** — A homophone group reduced to its set of per-spelling alternate sets,
  with spellings and strokes removed. Groups with the same shape pose the same grouping
  problem. *`GroupSignature` phasegsat.py:37.* Use this instead of "signature" (skeleton
  CONFLICT).
- **Hard grouping rule / soft preference tier** — Marker Grouping (Phase G) constraints
  that can raise K (`ALONE_KEYS`, `MUST_DIFFER_GROUPS`) versus lexicographic tie-breakers
  that cannot (`PREFERENCE_TIERS`). *build_phase_g_assignment.py:39-45.*
- **Candidate key-set** — A coda-bank chord of one consonant phoneme, or the union of two,
  considered for a keypress group. *`codaKeysOf` ambiguitychecker.py:1041-1045.*
- **Preferred key** — A human-chosen key-set for one marker's keypress group. It wins
  whenever it is feasible. *`PREFERRED_KEYS_BY_MARKER` ambiguitychecker.py:945.*
- **In-scope collision** — Two Words with different ortho, the same `lemmeGramCat` and the
  same composed stroke. It is the only kind that Marker Stroke Realization (Phase P)
  blocks. *`_isInScopeCollision` ambiguitychecker.py:968.*
- **Finalized word** — A Word whose needed keypress groups have all been decided, so its
  composed stroke can no longer change. *`_finalizeReadyWords` ambiguitychecker.py:1066.*
- **Spelling twins** — Two or more Words in one homophone group with the same ortho and
  `lemmeGramCat` but a different Word identity. Example: "finis" as participle m:p and
  "finis" as a finite form with no gender. Marker Elicitation (Phase E) merges them into
  one spelling. Marker Stroke Realization (Phase P) marks only the first one. *S3.P.2.1.*
- **Precedence spec** — `conjugation_disambiguation_order.txt`: the ordered marker
  combinations plus the special rules. It is authoritative intent, but the code checks
  only part of it. *util/check_conjugation_disambiguation_order.py:43.*

## Suspected bugs

- src/ambiguitychecker.py:1047, :1227 with :739-747 and :1248-1257 — **Nondeterministic
  residual buckets (the reported diff).** `allWords` is a `set[Word]`. `finalInduced` is
  filled in set iteration order. `findCollidingInducedStrokes` then emits only
  (first-seen key, later key) pairs for each stroke, and each pair is filtered into a
  bucket separately. `Word.__hash__` returns `_hash` (word.py:155). `_hash` is
  `hash(f"{ortho}{phonology}…")` (word.py:94), which Python salts per process
  (PYTHONHASHSEED), and the value is frozen into the pickles when they are written.
  Same pickles therefore give the same order, but a clean rebuild (pickles deleted and
  rewritten by a new process) gives new `_hash` values, a new set order and a different
  first-seen Word per stroke. So the pairs change: they come out reversed, for example
  ('affidées','affidés') becomes ('affidés','affidées'). Bucket membership changes too.
  For a stroke shared by A1 and A2 (same ortho) and B (another lemma), A1 seen first gives
  (A1,A2), which is dropped, plus (A1,B), which is cross-lemma. B seen first gives (B,A1)
  and (B,A2), both cross-lemma. That explains 34 vs 40 cross-category clashes and the
  1,283 cross-lemma pairs with different members.
  The chosen keys are not affected: the `keypressGroups` content in the committed and
  rebuilt JSON is identical, because `_feasible` uses only order-independent `any`/`all`.
  Theory 2 is not affected either, because `buildFinalInducedStrokes` iterates the dict
  order of theory 1. Fix direction: iterate `sorted(allWords, key=(ortho, lemmeGramCat,
  phonology, …))` and report every pair within a stroke bucket. Confidence: high.
- src/ambiguitychecker.py:739-747 with :1248-1250 — The first-seen pairing also gives
  **false negatives in the in-scope invariant**. Scenario: X and Z (same `lemmeGramCat`,
  different ortho) and Y (another lemma) share a final stroke. If Y is seen first, the
  output is (Y,X) and (Y,Z), both cross-lemma, and the real in-scope pair (X,Z) is never
  reported. Whether the invariant shows 0 therefore depends on hash order. Confidence:
  high (mechanism); no instance observed.
- src/ambiguitychecker.py:797-800 (`_resolveEntryWord`) — **Spelling twins: only the
  first Word is marked.** When two Words share (ortho, `lemmeGramCat`) and have the same
  canonical base strokes, `next(...)` returns the first, and the other keeps its bare base
  strokes. Scenario: "agis" has two Words (participle m:p and finite). Its primary press is
  {impératif}, and only one Word gets `-k`. The other "agis" Word sits on `a/vti`, the
  stroke of the canonical member "agi". Measured: 230 affected spellings and 229 real
  same-`lemmeGramCat` collisions in the final induced strokes. They are invisible to the
  "0 residual" invariant (neither Word is in `allWords`) and ignored by Lemma-Homophone
  Marking (S4), whose filter needs 2 or more distinct `lemmeGramCat`. The Plover export
  then keeps whichever Word is more frequent (export_plover_dictionary.py:56). Where
  another `lemmeGramCat` is also present, S4 adds `*` entries such as `kpi/mR*i` →
  "finis". Confidence: high.
- src/ambiguitychecker.py:1227-1241 — Extra alternates are verified only for Words in
  `allWords`, meaning Words with a non-empty primary. 2,749 spellings have an empty primary
  and non-empty alternates (e.g. "abaisse" [∅, {impératif}, {pers_1}, {subjonctif}]).
  `buildExtraInducedStrokes` still realizes their extra strokes, but no collision check or
  theory-1 check ever looks at them. A read-only check found 0 collisions of those strokes
  with theory 1 today. Confidence: medium (gap), low (current impact).
- dictionary.py:380-389 — `buildFinalTheory` ignores `assignment.unassignedGroups` and
  `residualCollisions`. If a keypress group cannot be realized, its Words silently lose
  that marker in theory 2 and the Plover dictionary, with no warning. Only the separate
  report build would show it. Confidence: medium (hazard, not triggered today).
- src/ambiguitychecker.py:1114, :1142, :1243-1247 — Collision tests compare **raw**
  Strokes (`stroke in theory`, `finalizedWordsByStroke`, `findCollidingInducedStrokes`),
  although the glossary requires canonical form. A composed stroke that equals the
  canonical form of a theory-1 key, but whose raw form differs (unsorted or repeated key,
  like "nie"), would pass. A read-only canonical check found 0 such cases today.
  Confidence: medium (mechanism), low (impact).
- src/phasegsat.py:117 with :128-135 — If a marker in `ALONE_KEYS` or `MUST_DIFFER_GROUPS`
  is not live (after an edit of the answers leaves nobody checking `infinitif`, for
  example), `x[m1, k]` raises `KeyError` instead of a clear error. Confidence: high
  (mechanism), low (likelihood).
- src/phasegsat.py:172, :274, :398 — A status of FEASIBLE (time limit hit) is accepted
  and its value locked (:178, :282, :405). A timeout can therefore lock a non-optimal tier
  score or tie-break, and the result is then neither proven nor reproducible. Confidence: low.
- util/check_conjugation_disambiguation_order.py:69-77, :100-126 — The checker covers
  much less than the precedence spec. (1) "Masculine must be free" is checked only for
  participle readings: ADJ/NOM gender readings are classified `finite_verb` and never
  checked, and neither are finite indicatif readings. (2) The spec says impératif and
  subjonctif are "mandatory" (conjugation_disambiguation_order.txt:55-58), but an empty
  press for either passes. (3) The line order is never checked. Scenario: an answer that
  leaves an impératif reading as the `∅` default produces no violation. Confidence: medium.

## Dead-code observations

- src/phaseg.py `runPhaseG` :247, `greedyColorMarkers` :117, `coOccurrencePairs` :75,
  `wouldCollideIfMergedPairs` :89, `_findSharedKeypressPair` :222, `PhaseGResult` :214 and
  `__main__` :294 are called only from src/test/phaseg_test.py and the module's own
  `__main__`. The greedy Marker Grouping (Phase G) is not live. `greedyColorMarkers` also
  breaks degree ties in set order, so it is not deterministic.
- src/phasegsat.py `minKeypressesSatPreferring` :455 and `_bestAssignmentPreferring` :232,
  plus the `mustShareKey` path of `_feasibleAssignment`, are reached only from the
  module's `__main__` :570 and tests.
- src/ambiguitychecker.py `findCollidingNewAdditions` :750 has test callers only.
  `_selectCanonicalIndex` :557, `buildAtomicFeatureToWords` :568, `findFeatureKeypresses`
  :623, `checkComposedChords` :669, `_appendCodaAddition` :593 and `_isFeasibleAddition`
  :601 are reached only from the Phase 0 diagnostic `__main__` :1326.
- src/greedyoptimizer.py `FEATURE_PRIORITY` :16 is off-pipeline (see the canonical member
  section).
- src/elicitation.py `reportScale` :164, `enumerateOppositionSamples` :107 and
  `_greedyColorCount` :126 are live but print only. Their output feeds nothing.
- util/build_pers3_default_answers.py is a one-shot script that is dangerous to rerun (it
  overwrites `elicitation_answers.json`).
- src/elicitation.py:586/:587/:616 compute `resolvePressByCombination` three times. It is
  not dead, but it is redundant.

## Doc drift

- CLAUDE.md:56 says Marker Grouping (Phase G) has "K=5, proven optimal". The artifact has
  K=7 (since 688c74d). build_phase_g_assignment.py:18-19 says "still K=6 … all three soft
  tiers fully achieved". The tiers are still achieved, but K is 7.
  ambiguitychecker.py:998 and :1060 say "Phase G's 6 groups".
- src/phasegsat.py:17-20 says "47,799 homophone groups … ~200 distinct problems". Today
  there are 47,828 and 294.
- src/elicitation.py:3-15 (module docstring) says "This module only measures" and that
  nothing touches the questionnaire. It now builds questionnaire items, resolves the
  answers and writes `resolved_press_sets.json`.
- src/elicitation.py:560-561 prints "K lower bound" for a greedy coloring. That is an
  upper bound on the chromatic number (docstring :127-129).
- util/check_conjugation_disambiguation_order.py:12 says a subjonctif press "must be
  exactly {"subjonctif"}". The code (:116-126) allows one extra `pers_*`/`nbr_*`
  clarifier, as the spec also does.
- util/check_conjugation_disambiguation_order.py:3-4 calls the file an ordered
  precedence vocabulary. The order is parsed but not used.
- CLAUDE.md:59 (item 7) says `FEATURE_PRIORITY` does live work (canonical-form picks). It
  does not: the canonical member comes from the elicitation answers.
- src/ambiguitychecker.py:1303 (`buildExtraInducedStrokes` docstring) and
  util/build_phase_p_realization.py:10-12 are stale about wiring into theory 2 (already
  in the skeleton).
- DESIGN_alternate_press_sets.md §4 lists realizing each alternate through the full
  composition search as open option (a). The code does not do that: alternates only reuse
  the keys that the primary search already chose, and they are verified only for Words
  that have a non-empty primary.
