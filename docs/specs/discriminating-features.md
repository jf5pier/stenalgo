# Spec: discriminating features

Scope: Same-Lemma and Grammatical-Category Disambiguation (S6). This stage separates the
inflected forms of one paradigm that theory 1 types identically (`dors`/`dort`,
`chante`/`chantes`/`chantent`, `il`/`ils`). It works in three phases:

1. **Discriminating-Feature Elicitation (Elicitation Phase)** records which grammatical
   features the user would press to tell two forms apart, then derives each spelling's
   **discriminating feature sets**.
2. **Discriminating-Feature Grouping (Grouping Phase)** packs the atomic features onto the
   fewest **Keypress Groups** that still separate every spelling.
3. **Discriminating-Feature Stroke Realization (Realization Phase)** gives each Keypress Group
   one coda-bank key and adds one **feature discriminating stroke** to every Word that needs
   features.

The code is the source of truth: `src/elicitation.py`, `src/featuregroupingsat.py`,
`util/build_keypress_groups.py` and `src/ambiguitychecker.py`
(`realizeKeypressGroupsAsExtraStroke` and its helpers). For the per-call walkthrough, see
[PIPELINE.md §Same-Lemma and Grammatical-Category Disambiguation (S6)](../PIPELINE.md#same-lemma-and-grammatical-category-disambiguation-s6).
Terms are defined in [GLOSSARY.md](../GLOSSARY.md). Clashes across lemmas or grammatical
categories are out of scope here: they are handled by the star/hash marks
([star-hash-marking.md](star-hash-marking.md)).

## 1. Design choices

- **Elicitation first (2026-09-18 pivot).** Which form is "plain" and which features mark the
  others is the user's own judgement, recorded answer by answer. The solver does not choose
  features. Earlier designs where a solver picked features (`satOptimizeDiscriminator`,
  `FEATURE_PRIORITY`) are superseded.
- **Phoneme keys, not reserved keys.** Features are written with coda-bank consonant keys in
  one trailing stroke. The reserved `*`/`#` keys are kept for lemma-homophones.
- **Meaningful keys where possible.** Some features have a preferred key: impératif → `-k`,
  pers_2 → `-d`, pers_3 → `-t`.
- **Scope = one `lemmeGramCat`.** A **homophone group** is the set of Words with the same
  `lemmeGramCat` and the same canonical theory-1 Strokes. There are 47,830 groups.

## 2. Elicitation Phase

### 2.1 Feature combinations

Each Word yields one **feature combination** (a set of atomic features) per verb tag, for
example `ind:pre:1p` → {`indicatif`, `présent`, `pers_1`, `nbr_p`}. Participle combinations
also carry the Word's gender, number and `VER`. A Word without verb tags yields {gender,
number}. Subjonctif imparfait is out of scope and dropped. All Words with the same spelling in
a group pool their combinations, so from here on the phase reasons **per spelling**.

### 2.2 What an answer means

An **opposition** is a pair of different feature combinations, carried by two different
spellings of one group. The questionnaire (`questionnaire.json`, 200 items) shows one example
pair per distinct opposition. An answer (`elicitation_answers.json`, tracked) records, for each
side, the atomic features the user would **press** to write that side:

```json
{"orthoA": "il",  "atomsA": ["m","s"], "checkedA": [],
 "orthoB": "ils", "atomsB": ["m","p"], "checkedB": ["p"]}
```

Read it as: "Between {m, s} and {m, p}, write the {m, s} form plainly and press `p` for the
{m, p} form." Only `atomsA/B` and `checkedA/B` are used. The spellings, `lemma` and `reviewed`
fields are for display only. Since one answer covers every group with the same opposition, 200
answers resolve every group (47,828 of the 47,830: the other 2 have a single spelling).

Rules an answer set must respect:

- The two sides of an opposition must end up different once each side's checked features are
  applied. An opposition between identical combinations (a **tie opposition**) is skipped: no
  feature could separate those two spellings.
- A missing answer (an **unresolved opposition**) drops the whole group, which keeps its bare
  theory-1 strokes. The Elicitation Phase reports these. Today there are 0.

### 2.3 Precedence spec

[`conjugation_disambiguation_order.txt`](../../conjugation_disambiguation_order.txt) (repo
root) is the **authoritative** guide for answering. It lists the feature combinations from
"should need the fewest features" (`m`, `m s`, `f`, …, then indicatif présent 3s, 1s, …) to
"most", plus special rules:

- impératif is always identified by the `impératif` feature alone, and it is mandatory;
- infinitif is always identified by `infinitif` alone;
- subjonctif is mandatory, and may be clarified by one `pers_*` or `nbr_*` feature.

`util/check_conjugation_disambiguation_order.py` checks only part of it (tracked as B12): masculine
singular participles must press nothing, and a non-empty impératif/infinitif/subjonctif set must
have the shapes above. The line order itself is not enforced by code. It guides the person
answering.

### 2.4 Discriminating feature sets (Press-Set Resolution)

For each group, and for each (spelling, feature combination):

- the **discriminating feature set** is the union of the features checked for that side, over
  every opposition against the group's other spellings;
- a spelling's sets are deduplicated and sorted by (size, features). Index 0, the smallest, is
  the **primary alternate**;
- a **self-homograph** (one spelling, several combinations: `calmez` = impératif 2p or
  indicatif présent 2p) keeps **one alternate per combination** instead of their union. Either
  is enough to write it (the "calmez fix", which replaced the over-marking `-kt`). For scale:
  this multi-combination shape affected 8,413 of 47,827 groups (~17.6 %) when the fix landed
  (2026-09-22 measurement).

**Canonical member.** A spelling whose primary alternate is empty (`∅`) needs no feature. It
keeps its theory-1 strokes and is the group's canonical member. This choice comes **only from
the answers**: no code computes a default, and `FEATURE_PRIORITY` plays no part. 4,858 groups
have no `∅` member, so every spelling in them gets a feature discriminating stroke.

**Validation.** No discriminating feature set may be held, as any alternate, by two different
spellings of one group (a **discriminating feature set conflict**). Two alternates of the same
spelling may be equal. There are 0 conflicts today. A conflicting group would be dropped.

Output: `resolved_press_sets.json` (gitignored, regenerable). It holds one entry per group:
canonical `strokes`, `lemmeGramCat`, `pressSets` (spelling → list of alternates), the
per-spelling `frequencies` (the 200 frequent words count 0), and `readings` (the combinations
behind each alternate, used by the trainer).

## 3. Grouping Phase

A **live** atomic feature is one that appears in some resolved set. There are 13 today. The
other 7 questionnaire features (`VER`, `indicatif`, `m`, `nbr_s`, `participe`, `présent`,
`s`) are **unpressable**, because nobody checked them.

A **Keypress Group** is a set of live features pressed together. Pressing it asserts every
feature it carries. A spelling's **induced discriminating feature set** is the union of the
features of every Keypress Group its set touches.

**Requirement (hard, exact).** In every group, two **different** spellings never induce the
same Keypress-Group set (a **keypress group conflict**). Alternates of one spelling are
exempt. The phase finds the **minimum number of Keypress Groups K** that meets this
requirement, using exact CP-SAT (`minKeypressesSatWithPriorities`) over the 294 distinct
**homophone group sets of feature sets**. The first feasible K is proven minimal.

**Hard grouping rules** (user requirements, `util/build_keypress_groups.py`; they may raise K):

- `f` shares its Keypress Group with no other feature (`ALONE_KEYS`);
- `infinitif`, `pers_1`, `pers_2` and `pers_3` are on pairwise different groups
  (`MUST_DIFFER_GROUPS`).

**Soft preference tiers** (lexicographic at the minimum K; they never raise K):

1. `nbr_p` shares a group with `p`;
2. `future` shares a group with `passé`;
3. the `{nbr_p, p}` group carries no other feature.

**Determinism.** After the tiers are applied, each feature in alphabetical order is given the
lowest group index and locked there (single-threaded, seed 0). The result is unique as long as
every solve reaches OPTIMAL (B24).

**Ground truth.** Before writing, `verifyKeypressAssignment` recomputes every induced set and
refuses to write if there is any conflict.

**Current result** (`keypress_groups.json`, tracked): K = 7, all soft tiers achieved.

| group | features | key (Realization Phase) |
|---|---|---|
| 0 | conditionnel, infinitif | 21 `-R` |
| 1 | f | 16 `-j` |
| 2 | future, passé, pers_3 | 20 `-t` |
| 3 | imparfait, subjonctif | 23 `-l` |
| 4 | impératif, pers_1 | 18 `-k` |
| 5 | nbr_p, p | 17 `-s` |
| 6 | pers_2 | 19 `-d` |

K has changed as the answers changed: 5, then 6 (impératif answer fix, 4e73533), then 7
(per-combination alternates, 688c74d). Group ids are not stable between runs, so code looks up
features, not ids.

## 4. Realization Phase

**The rule.** Each Keypress Group gets one physical **key-set** from the coda bank. The
candidates are single consonant keys 16–25 and the consonant digraphs (16,17), (16,18),
(17,19), (18,19), (20,22), (22,23) and (24,25). A union of two candidates is tried only when no
single one fits. A Word whose **primary** alternate touches groups {g1, g2, …} gets **one**
feature discriminating stroke, the sorted union of those groups' keys, **after** its base
strokes. Its last base stroke is not changed.

**Search** (`realizeKeypressGroupsAsExtraStroke`, greedy): groups are decided in descending
population order. A candidate is **feasible** unless:

- (a) it equals a key-set already chosen;
- (b) it is empty or redundant for some Word;
- (c) some composed feature discriminating stroke is illegal;
- (d) some composed Strokes equals an existing theory-1 key;
- (e) it creates a **same-lemmeGramCat collision** (different spelling, same `lemmeGramCat`)
  among Words needing the same group set;
- (f) it creates one against an already finalized Word.

Collisions across categories or lemmas never block a candidate: those belong to the star/hash
marks. Among feasible candidates, the lowest frequency-weighted cost of the real composed
stroke wins, and ties keep phoneme order. A feasible **preferred key** (impératif → 18,
pers_2 → 19, pers_3 → 20) always wins. Today every group gets a single key and all three
preferences are honored.

**Alternate entries.** Every non-primary alternate of a self-homograph becomes an extra
dictionary entry: the base strokes plus that alternate's feature discriminating stroke
(`calmez` → `kal/me/-d` and `kal/me/-k`). Alternate entries are not extra strokes of the
primary. They are second entries for the same spelling.

**Two call sites.** The **inline path** (inside `Dictionary.buildFinalTheory`) feeds theory
2 and every export. The **report build** (`python -m util.build_realization_report`) writes the
tracked **realization report** `realization_report.json`, which only the trainer keyboard legend
reads. The two can drift if the report is not rebuilt (B18).

## 5. Invariant

**0 residual same-lemmeGramCat collisions**: after realization, no two Words with different
spellings and the same `lemmeGramCat` share a final induced stroke. This must stay green.
It is checked as `len(residualCollisions) == 0`, printed and persisted by the report build and
asserted by unit tests. The inline path does not check it.

Known holes in the check: it sees only Words that got groups and only the first pair seen on
each stroke (B16). Spelling twins (Words sharing a spelling and a `lemmeGramCat`, only the
first of which gets its stroke) leave 230 same-lemmeGramCat pairs that the check cannot see
(B1).

## 6. Worked examples

Plover strokes from `plover_stenalgo_dictionary.json`, 2026-09-22 data.

| Word | features pressed | Plover |
|---|---|---|
| `il` / `ils` | ∅ / p | `il` / `il/-s` |
| `chantait` (ind. imparfait 3s) | ∅ (canonical) | `pm@/tie` |
| `chantais` (ind. imparfait 1s/2s) | pers_1 or pers_2 | `pm@/tie/-k`, `pm@/tie/-d` |
| `chantaient` | pers_3 + nbr_p | `pm@/tie/-st` |
| `chante` | ∅; alternates impératif, pers_1 (same group, one entry), subjonctif | `pm@t`, `pm@t/-k`, `pm@t/-l` |
| `chantes` | pers_2; alternate pers_2 + subjonctif | `pm@t/-d`, `pm@t/-dl` |
| `calmer` / `calmé` / `calmée` / `calmées` | infinitif / ∅ / f / f + p | `kal/me/-R`, `kal/me`, `kal/me/-j`, `kal/me/-js` |
| `calmez` (self-homograph) | impératif or pers_2 | `kal/me/-k`, `kal/me/-d` |

## 7. Rebuild

After `elicitation_answers.json` or the lexicon changes, run `python -m src.elicitation`,
then `python -m util.build_keypress_groups`, then `python -m util.build_realization_report`,
then the exports. See [PIPELINE.md §How to run a full rebuild](../PIPELINE.md#how-to-run-a-full-rebuild).
Test a suspected answer fix in memory first, and report any exceptions before writing it to
disk.
