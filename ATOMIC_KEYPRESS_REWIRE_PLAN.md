# Plan: same-lemma homophone discrimination via elicited atomic-feature keypresses

Originally written 2026-09-18 as "wire Part 2's atomic-feature keypress search into a real
joint solver"; **amended later the same day after two further design sessions — this version
is authoritative.** It absorbs `RESUME_2026-09-18.md`'s review decisions (that file stays as
the record of the review session; its old "where they conflict, this file wins" rule is now
**inverted** — the plan wins) and adds the session-2 pivot described next. Conventions
unchanged: grounded in code audit, phased changes, open decisions recorded rather than
silently picked.

## The session-2 pivot: elicitation before optimization

The original plan (like the pipeline it set out to fix) let the solver pick each word's
discriminating features, then tried to make the outcome learnable by shaping constraints
around it. Session 2 inverted this: **the user's own writing reflexes are the spec.** The
mapping must follow how the brain works, so the user is asked — pair by pair — how they
would discriminate the homophones; only what remains (grouping markers onto keypresses) is
optimized, afterwards, over that data.

The parler walkthrough that settled it:

- "je parle" — phonology only; indicatif présent is the default expectation (typed bare).
- "tu parles" — press `pers_2` (the written *-s* is what the writer is conscious of).
- "ils parlent" — press `pers_3:nbr_p`: `pers_3` alone may not discriminate (it also
  matches "il parle") even though `nbr_p` alone might. **Over-specific presses happen and
  must still produce the right spelling.**
- "que je parle" — possibly press `subjonctif` defensively, even though it is spelled the
  same as the default form.
- "parlé" (noun and participe passé) — `m:s`, or nothing; `parler` / `parlai` / `parlez` —
  `infinitif` / `passé` / `pers_2:nbr_p` or just `nbr_p`.

Consequences adopted below: the input artifact is **elicited** rather than taken from
`buildDiscriminatorSelection`; the default (∅) form of each cluster comes from the same
data (`FEATURE_PRIORITY` has no role left on this track); ambiguity handling is a
**calibratable strict/lenient mix** (open decision §E); the abstract solver shrinks to
grouping (Grouping Phase).

## Vocabulary (fixed by the user; used throughout)

- **Cluster** — homophones sharing one lemma, e.g. {parle, parles, parlent} ([paʁl]). All
  members share one sound-stroke; only markers can separate them. **Marker chords compete
  only inside a cluster**: different sound-strokes never collide — parlent [paʁl] and
  parlez [paʁle] are different clusters, and no press can ever conflict across them.
- **Marker** (the code's atom / atomic feature) — one grammatical value: `pers_2`,
  `nbr_p`, `subjonctif`, `m`, …
- **Reading** — one grammatical analysis of a spelling. Homographs that are also
  homophones give one cluster member several readings ("parle" = ind-prés-1s /
  ind-prés-3s / subj-prés-1s / subj-prés-3s). Readings of the same spelling never
  conflict with each other — they produce the same output text.
- **Keypress** (chord) — the abstract unit a marker maps to; physical keys are Realization Phase.
  **∅** — no extra press: a cluster's default form is typed with the bare sound-stroke.
- **Press** — the marker-set the writer actually presses for a word. May be
  over-specific; decoding is superset-tolerant: pressed markers + sound-stroke must
  identify exactly one spelling (or the §E fallback), extra true markers are ignored.
- **No-conflict rule** (the earlier docs' "union-injectivity") — no press may be
  compatible with readings of two different spellings of the same cluster.

## Running examples

[paʁl]:

| spelling | readings |
|---|---|
| parle | ind prés 1s/3s, subj prés 1s/3s (homograph) |
| parles | ind prés 2s, subj prés 2s |
| parlent | ind prés 3p |

[paʁle]:

| spelling | readings |
|---|---|
| parler | infinitif |
| parlai | passé simple 1s |
| parlé / parlée / parlés / parlées | participe m:s / f:s / m:p / f:p (parlé also: noun) |
| parlez | ind prés 2p, impératif 2p |

The real under-specific cases (what §E calibrates): `pers_3` alone for *parlent* also
matches *parle*; `nbr_p` alone for *parlez* also matches *parlés* / *parlées*.

## Context (condensed from the original, corrected)

- `ROADMAP.md`'s 2026-09-15 decisions: the 4 reserved keys `[0,1,10,15]` belong
  exclusively to the lemma-homophone (`*`/`#`) track (different lemmas, same sound; up
  to 4 lemmas per cluster); same-lemma conjugation discrimination uses meaningful
  phoneme-key chords. Never implemented — `satOptimizeDiscriminator`
  (`src/satoptimizer.py`) still colors same-lemma `WordFeature`s onto the reserved-key
  space (11 abstract special keypresses as of the coverage-first switch,
  `PLAN_2026-09-18_low_value_discriminators.md`).
- The symptom that motivated all this: `_colorFeatures`' coloring lets any two features
  share a key whenever nothing flags them opposed, so a key's meaning is whatever was
  cheapest that run — not a fixed, learnable slot. Corrected framing after the pivot: a
  keypress means **a set of markers the writer never presses separately**; learnability
  comes from the elicited data, not from an objective term.
- `src/ambiguitychecker.py`'s Part 2 (`buildAtomicFeatureToWords` `:202-224`,
  `findFeatureKeypresses` `:257-294`, `checkComposedChords` `:303-346`) stays
  diagnostic-only for now and becomes the Realization Phase seed. Its three audited gaps
  (independent per-atom scan; `comboSize` hardcoded 2; not cost-aware) are
  physical-layer concerns.

## Status of the original plan's sections

| Old § | Disposition |
|---|---|
| 0 baseline commit | Still pending; now includes this amendment + the resume |
| 1 tokenizer fix | **DONE** (commit `29da8d2`) — record below |
| 2 granularity (open decision A) | Superseded — elicitation + grouping resolve it; A marked resolved |
| 3 joint model | Superseded — Grouping Phase (abstract) + Realization Phase (physical) replace it |
| 4 N-way cap | ≤4 is structurally safe (`splitInfoVerb`); E3 confirms cheaply |
| 5 two-stroke fallback | Deferred to Realization Phase (open decision B with it) |
| 6 wiring/persistence | Deferred to Realization Phase |
| 7 consumers | Split: Elicitation Phase tool + tests now; `dictionary.py` wiring deferred |
| 8 re-run/compare | Reinterpreted — E3 scale report + Grouping Phase report now; old §8 checks move to Realization Phase |
| A | Resolved — the sharing mechanism (Grouping Phase constraints) does what family-codes were after |
| B, C | Deferred to Realization Phase |
| D | Corrected: `FEATURE_PRIORITY` is **live** in Part 2 (import `src/ambiguitychecker.py:36`, used by `_selectCanonicalIndex` `:191-199`), not orphaned. Elicitation's default-form answers eliminate its job on this track; retiring `src/greedyoptimizer.py` means rehoming it |

## Prerequisite fix — DONE (commit `29da8d2`)

`atomicFeatures()` (`src/word.py`) now splits only on `:` so `pers_3` stays one token.
Fixing it surfaced the same bug in `Word.getFeatures()`' gender/number combos, now
`:`-joined (`m:s`, `VER:m:s`); `not_m_s` is the one deliberate exception (a standalone
canonical-form flag, not a compound). `FEATURE_FAMILIES`' obsolete combo entries and the
`VER_`-prefix special case removed. Regression tests added
(`src/test/word_test.py::TestAtomicFeatures`, `TestGetFeatures`); 428 tests green; no new
mypy errors.

## Elicitation Phase — elicitation (new; comes first)

**E0. Baseline commit.** This amendment + the resume note. Delete stale
`anchor_feasibility.tsv` (generated pre-`29da8d2`; current code writes
`feature_keypress_feasibility.tsv`). Move `callgraph` to scratch/ or delete.

**E1. Rebuild caches.** Delete **all three** pickles (`Dictionary.pickle`,
`FirstTheory.pickle`, `FeatureDiscrimator.pickle`) before building anything: selection
data derives from `Word.getFeatures()`, which `29da8d2` changed (three-pickle gotcha,
`RESUME_2026-09-17.md`).

**E2. Enumerate.** From the rebuilt data: every same-sound cluster; every spelling pair
within each cluster × every reading combination — the homograph repetition, so the
sampling is exhaustive.

**E3. Report scale.** Cluster count; total pair count; **distinct feature oppositions**
(the actual number of questions the user would face); max compound size (expect ≤4);
which markers ever get pressed together (Grouping Phase's co-occurrence input); greedy-coloring
lower bound on K computed with and without the pressed-together rule, so its price is
known up front.

**E4. Questionnaire.** One question per **distinct opposition**, illustrated with a real
example pair; the answer propagates automatically to every pair sharing that opposition,
across all lexemes and models. Homophony is per **model** — French has 100+ verb models
and the same case is homophonous in one model and not another (parler/parlé homophones;
finir/fini not) — so enumeration comes from lexicon data, never from ending patterns.
Format open — §F.

**E5. Validate.** Per cluster under the §E calibration: every press implied by the data
lands on exactly one spelling (lenient: a well-defined fallback). Conflicts are re-asked
with the full cluster in view ("you said `nbr_p` alone for *parlez*; *parlés* /
*parlées* also match — settle it").

**E6. Persist the elicitation artifact.** Per-opposition answers + per-cluster resolved
press-sets. This — not `buildDiscriminatorSelection` output — feeds Grouping Phase.

## Grouping Phase — grouping (the reduced abstract solver)

- A marker gets a keypress **iff some elicited press contains it**. Markers no press ever
  contains are unpressable by construction — "no keypress = unmarked default" falls out
  of the data mechanically (e.g. mode markers wherever mode never changes spelling, as
  with "que je parle" typed bare).
- Constraints: (a) markers pressed together somewhere never share a keypress; (b) sharing
  must not break any cluster's no-conflict property, checked mechanically against the
  elicited press-sets. Competition alone does **not** forbid sharing: in [paʁl], `pers_2`
  (parles) and `nbr_p` (inside parlent's `pers_3:nbr_p`) may share a keypress **iff**
  parlent is never pressed with `nbr_p` alone — validation decides from the data, case by
  case. (This resolves the resume's proposed "share only if neither compete nor
  co-occur" rule in a narrower form: its compete clause, read graph-coloring-style, would
  have forbidden exactly this share.)
- Objective: minimize K (number of keypresses); report frequency-weighted chord sizes —
  full cost optimization is Realization Phase.
- Implementation seed: the `_colorFeatures` schema + `_minSpecialKeypressesNeeded`
  feasibility loop (`src/satoptimizer.py:155-259`, `:262-279`), with per-cluster
  set-distinctness constraints over press-sets instead of coloring edges. Synthetic tests
  mirroring `src/test/satoptimizer_test.py`, plus a new test module for the Elicitation Phase tool
  (enumeration, opposition dedup, validator).
- Report: K, the keypress → markers table, the unpressable-marker list.

## Realization Phase — physical realization (milestone 1 DONE -- see `RESUME_2026-09-19-phaseP.md`)

Milestone 1 is complete and verified against the real lexicon: all 6 Grouping Phase groups
have a physical coda key, 0 same-lemmeGramCat collisions left. The bullets below are
the original planning notes, kept for historical context; two design points changed
during execution (extra trailing stroke, not merged into the last one; per-word
multi-group composition, not each group tested in isolation) -- see the resume file
for what actually got built and why. Still-open items from this list: the `*`/`#`
track itself (the "restrict `satOptimizeDiscriminator`" bullet) and the
`theory.tsv`-replacement wiring (ROADMAP.md open question 4) remain deferred.

**Wishlist for the `*`/`#` track (not scoped yet):** nouns ending in `-er` that take
the plural `-ers` (French verbal nouns derived from an infinitive, e.g. `dîner`/
`dîners`) could be disambiguated from their VER/infinitif homophone reading by reusing
the existing `Infinitif` / `Infinitif:p`(pluriel) atomic-feature markers instead of a
generic `*`/`#` mark -- a derivational-pattern rule that resolves a whole NOM/VER
homophone sub-class at once rather than needing per-pair marking. Raised
2026-09-20 during the cross-category/cross-lemma regret analysis; not sized or
verified against real data yet.

**The `*`/`#` track's marking rule is now designed AND implemented** (design
2026-09-20, implementation 2026-09-20 -- see `RESUME_2026-09-20-starhash-priority.md`
for the full design derivation). `src/ambiguitychecker.py`'s `decideStarHashMark(wordA,
wordB) -> Word | None` decides which side of a bucket-2/bucket-3 colliding pair gets
the mark: homograph exemption → per-pair `MARKING_OVERRIDES` (the ~51 known aggregate-
rule misfires) → frequency-ratio exemption (≥10x rarer ⇒ mark it, `RATIO_EXEMPTION_
THRESHOLD`) → same-`gramCat` per-pair-optimal → `GRAMCAT_PRIORITY` (`src/
greedyoptimizer.py`, `ADV > PRO:pos > NOM > VER > ADJ > ADJ:pos`) → frequency fallback
for any category pair outside that table. Gets within 0.526% of the theoretical best
possible keystroke cost across both bucket 2 and bucket 3 (0.499% re-verified on a
freshly rebuilt `Dictionary.pickle`/`FirstTheory.pickle`, and 0.208% spot-checked
against live bucket-3 `crossLemmaCollisions` data directly through the new function).
Tests: `src/test/ambiguitychecker_test.py::TestDecideStarHashMark`.

The 2026-09-20 discrepancy (bucket 2's real population is 74 pairs, not the 29
documented above) is **resolved, not a bug**: reconciled against a freshly rebuilt
`Dictionary.pickle` the same day -- still 74 pairs, 0 NOM/VER pairs, confirming it was
stale documentation, not a stale-pickle artifact. The 29-pair count above is outdated.

**The N-ary case (clusters of >2 colliding lemmas) and the physical realization are
now also implemented** (same 2026-09-20 follow-up session). `rankHomophoneCluster`
orders a whole cluster canonical-first using `decideStarHashMark` pairwise as a total-
order comparator; `assignStarHashCombos(groupSize)` returns the marking codes
`(), (*,), (#,), (*#,)` for up to 4 readings, escalating to `(*#,*#)`, `(*#,*#,*#)`, ...
(one more whole extra syllable per reading) beyond that; `assignStarHashMarks`
collapses homograph readings to one slot first so they don't force needless
escalation. Physical realization: `*` = key 10 (left index, off-home), `#` = key 15
(right index, off-home) — both in `Keyboard._reservedKeys` and a legal cross-hand
chord together (`*#`) — via `starHashCodeToStrokes` / `assignStarHashPhysicalStrokes`.
Validated against the live lexicon: the biggest real cluster (after homograph
collapse) is 7 distinct readings (the classic `au`/`eau`/`oh`/`haut`/`ho`/`ô`/`aux` set),
needing at most 4 extra `*#` syllables anywhere in the whole lexicon — nothing
pathological. Keys 0/1 (left pinky, also reserved) remain unassigned, held for a
possible future 3rd logical mark.

**Composition with Realization Phase is now also implemented** (same 2026-09-20 follow-up
session). Investigation first: checked how often a word needs both mechanisms at once
by looking at `assignment.crossLemmaCollisions`/`crossCategoryClashCollisions`
directly -- turns out it's the norm, not an edge case, for the currently-elicited
population: **100%** of those pairs involve a word that already carries its own Realization Phase
extra stroke, because those two fields are computed from Realization Phase's own `finalInduced`
in the first place. The two mechanisms compose by simple concatenation (Realization Phase's
stroke first, then */# after it) and can never create a NEW cross-cluster collision:
Realization Phase only ever picks coda-phoneme keys, structurally disjoint from the 2 dedicated
reserved keys (`STAR_KEY`=10/`HASH_KEY`=15 are excluded from `Keyboard.allowedKeys`),
so appending after an already-different prefix keeps the whole `Strokes` tuple
different. Implementation: `groupHomophonesByReservedStroke(finalInduced)` groups
words by shared post-Realization-Phase stroke, keeping only genuine distinct-`lemmeGramCat`/
distinct-`ortho` groups (excludes Realization Phase's own same-paradigm residuals and all-
homograph groups); `composeReservedKeyStrokes(finalInduced)` appends
`assignStarHashPhysicalStrokes`'s extra syllable(s) on top. Validated against the live
lexicon: 1079 genuine */# groups found inside Realization Phase's own elicited population, 0
accidental collisions with existing theory strokes, and 0 genuine (distinct-spelling)
collisions left anywhere after composition. Tests:
`TestGroupHomophonesByReservedStroke`, `TestComposeReservedKeyStrokes`.

**Rule 3 (the spelling-doublet exemption) is now also implemented**, this time
correctly sourced (same 2026-09-20 follow-up session). `loadReform1990DoubletPairs()`
parses `resources/reform1990.tsv` into `{oldSpelling, newSpelling}` pairs (excluding
`isException=True` rows -- the file's own documented cases like `fût`/`fut` that
collide with a genuinely distinct word despite being a reform pair). `decideStarHashMark`,
`rankHomophoneCluster`, `assignStarHashMarks`, `assignStarHashPhysicalStrokes`, and
`composeReservedKeyStrokes` all take an optional `doubletPairs` parameter (default
`frozenset()`, opt-in, no behavior change unless passed) checked right after the
homograph exemption: `frozenset({wordA.lemme, wordB.lemme}) in doubletPairs` → no mark
needed. `assignStarHashMarks` also collapses doublet-pair readings to one representative
(union-find over `orthoGroups`, same treatment as homograph collapsing) so they don't
consume a cluster slot or force needless escalation. Validated against the live
lexicon: of 259 loaded doublet pairs, 11 bucket-3 pairs are genuinely exempted this way
(`dessoûler`/`dessouler`, `tocard`/`toquard`, `béluga`/`beluga`, `dégoter`/`dégotter`,
...), saving 13 real words an unnecessary `*`/`#` stroke, with zero regressions
elsewhere in the composed output. Tests: `TestLoadReform1990DoubletPairs`, plus doublet
cases added to `TestDecideStarHashMark`/`TestAssignStarHashMarks`.

**Still open:** none of this (`decideStarHashMark` through `composeReservedKeyStrokes`)
is wired into an actual `theory.tsv`-replacement / persisted output yet -- it's a pure
function pipeline validated by ad hoc scripts, not yet the thing `dictionary.py`'s
pipeline actually calls. That's the one remaining piece from this whole `*`/`#` design
thread, and it's a bigger, previously-deferred question (ROADMAP.md open question 4)
rather than a small follow-up.

- Cross-cluster new-vs-new collisions: `_isFeasibleAddition`
  (`src/ambiguitychecker.py:243`) misses collisions between two newly composed chords —
  final stroke (12,16)+{18} and (12,18)+{16} both land on (12,16,18). The `*`/`#`
  reserved-key modifications also create strokes absent from `theory`; the composition
  order of the two tracks is undefined and interacts.
- Pressability filtering: **the KeyError half is FIXED** (landed with Realization Phase
  milestone 1, commit `31b3a3c`) — `getStrokeCost` (`src/keyboard.py`) now returns
  `None` for illegal per-finger unions (coda m=(25,) + n=(22,) → right pinky {22,25},
  not in `_possibleKeypress.rightPinky`) instead of raising, and both callers
  (`cpsatsolver.py`, `greedyoptimizer.py::_buildStrokePool`) drop `None`-cost strokes;
  covered by `keyboard_test.py::TestGetStrokeCost`. Still open from this bullet:
  `checkComposedChords` takes `feasibleComboPhonemes[0][0]` — half of a 2-phoneme
  combo.
- Cost object = the full merged final stroke (base ∪ additions), not just the added
  keys; two-stroke fallback lives in stroke-SEQUENCE space (`theory` keys are `Strokes`
  tuples, multi-stroke entries already exist).
- Part 2's three gaps (independent scan / comboSize 2 / not cost-aware) get fixed here by
  the joint physical model, over the Grouping Phase output.
- Wiring + persistence: call from `dictionary.py` `__main__` (alongside
  `buildDiscriminatorSelection`'s existing call at `:463`), fed by the E6 artifact;
  persist stroke→word output (finally resolving `ROADMAP.md` open question 4 on
  `theory.tsv`'s fate); restrict `satOptimizeDiscriminator` to the `*`/`#` track — its
  input today is same-lemma only, so "restrict" really means "build a new input source",
  and that track may not need CP-SAT at all (frequency-rank within each cluster
  independently).
- Old §B (two-stroke cutoff rule) and §C (onset phonemes as candidates) land here.
- Old §8 checks land here: reserved-key special-keypress count drops to what the `*`/`#
  track alone needs (from today's 11); spot-check family polarity by hand; no word
  becomes newly unresolved without an explicit accept (Category-C exception-list
  precedent).
- Mechanical invariants: stroke→word injectivity from persisted output; one keyset per
  keypress; every delivered stroke per-finger pressable.

## Open decisions

- **§E — strict/lenient calibration (decided in principle, mechanism open).** Session 2
  decided: a **mix, calibratable** between the extremes. Proposed mechanism: an ambiguous
  press resolves to the most frequent matching spelling only when it outranks every other
  match by a configurable margin; the margin runs from 1 (any lead suffices = fully
  lenient) to ∞ (strict). Open: where the margin lives (global constant / per gramCat /
  per cluster) and its default.
- **§F — questionnaire format.** CLI, or an interactive web page (storage lets the user
  answer from anywhere and resume; could be hosted as an artifact page). Needed before E4
  is built.
- **§G — noun homophones inside verb clusters.** The [paʁle] walkthrough includes noun
  *parlé* (its own lemma) among the verb forms, marked `m:s` on the normal track. Under
  the strict same-lemma cluster definition it would fall to the `*`/`#` track instead.
  Check how the lexicon clustering treats it today; the user's reflex says the marker
  track. Whichever way, record it in the cluster definition.
- Deferred: §B two-stroke cutoff, §C onset candidates (Realization Phase).

## Established facts (carried from the review session)

- **Atom inventory ≈ 19-20**: pers_1/2/3, nbr_s, nbr_p, s, p, m, f, indicatif,
  subjonctif, conditionnel, impératif, infinitif, présent, imparfait, future, passé, VER
  (+ participe, not_m_s if ever selected). `future` (not `futur`) is `splitInfoVerb`'s
  spelling (`src/word.py:119`) — internally consistent, cosmetic only.
- **Max compound size ≤ 4 structurally** (`splitInfoVerb`, `src/word.py:98-123`); the
  `rudoie` 4-atom precedent (`subjonctif:présent:pers_3:nbr_s`) is the ceiling.
- **s/p vs nbr_s/nbr_p dissolves at the abstract layer** — grouping merges the notation
  pair whenever the data permits; only a naming choice remains. `_VALUE_TABLES`
  (`src/satoptimizer.py:28-31`) already encodes the identity.
- **`FEATURE_PRIORITY` is live** (`src/ambiguitychecker.py:36` → `_selectCanonicalIndex`);
  the plan's original "orphaned" claim was wrong.
- **`anchor_feasibility.tsv` is stale** (pre-`29da8d2`, over-split tokens); E0 deletes it.
- **Expected K ≈ 4-8** (hypothesis): person trio + number pair + gender pair are the
  obvious cliques; mode values rarely compete in French same-lemma homophony. E3's lower
  bounds make this measurable before Grouping Phase runs.
- **Three-pickle staleness gotcha** documented in `RESUME_2026-09-17.md`.

## Non-goals (updated)

- No changes to the `*`/`#` lemma-homophone track's own logic beyond confirming its sole
  claim to the 4 reserved keys (Realization Phase).
- No re-optimization of the phoneme→key layout (`starboard3h.json`,
  `cpsatsolver.py::optimizeKeyboard`, still commented out per `ROADMAP.md`).
- No prefix-formation work (`ROADMAP.md` Phase 6) — same machinery family, out of scope.
- `FEATURE_FAMILIES` / `associationScore` / polarity machinery: no job left on this track
  once elicitation + grouping land; separate cleanup, not blocking.
- The physical layer (Realization Phase) stays out of scope until E and G report.

## Call graph today (kept for the Realization Phase wiring)

```
dictionary.py (__main__)
│
├─ augmentedTheory = buildDiscriminatorSelection(theory, discrimFeatureWords)   :463
│
└─ satOptimizeDiscriminator(augmentedTheory, theory, numSpecialKeypresses=None) :497
     │
     └─ _colorFeatures(...) → keyAssignment: dict[WordFeature, int]
          -- colors ALL same-lemma WordFeatures onto the 4 reserved keys.
          -- feeds the printed "Special keypress mapping" table. Nothing persisted.

src.ambiguitychecker (__main__, run separately, never called from dictionary.py)
│
├─ augmentedTheory = buildDiscriminatorSelection(theory)                       :412
│
├─ atomicFeatureToWords = buildAtomicFeatureToWords(augmentedTheory)           :414
├─ featureKeypresses = findFeatureKeypresses(atomicFeatureToWords, ...)        :415
│    -- independent per-atom scan, comboSize capped at 2, not cost-aware
├─ composedReport = checkComposedChords(featureKeypresses, ...)                :416
│    -- audits composed chords after the fact, no repair
│
└─ prints a feasibility report + feature_keypress_feasibility.tsv
     -- DEAD END: nothing consumes this. dictionary.py never calls it.
```
