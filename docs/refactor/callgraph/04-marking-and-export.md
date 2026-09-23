# Lemma-Homophone Marking (S4)

Per-stage call graph, Pass 1b. Anchors checked against branch `docs-refactor` at 5ae0118
(working tree of 2026-09-22). Numbers marked "live data" come from a read-only in-memory
recompute of the final induced strokes from the `FirstTheory.pickle`,
`phase_g_keypress_assignment.json` and `resolved_press_sets.json` present on disk at
about 20:13 on 2026-09-22 (K=7). A concurrent rebuild may shift them slightly.

## Overview

```
S4.1  Theory 2 assembly — Dictionary.buildFinalTheory (dictionary.py:342)
 ├─ S4.2  Marker Stroke Realization (Phase P), inline — dictionary.py:365-384 (summary only)
 ├─ S4.3  Reform-doublet loading — loadReform1990DoubletPairs (src/ambiguitychecker.py:94)
 ├─ S4.4  Reserved-key composition — composeReservedKeyStrokes (src/ambiguitychecker.py:410)
 │   ├─ S4.5  Lemma-homophone cluster detection — groupHomophonesByReservedStroke (:380)
 │   ├─ S4.6  Physical mark assignment — assignStarHashPhysicalStrokes (:369)
 │   │   ├─ S4.7  Mark code assignment (homograph/doublet merge) — assignStarHashMarks (:292)
 │   │   │   ├─ S4.8  Cluster ranking — rankHomophoneCluster (:261)
 │   │   │   │   └─ S4.9  Ranking comparator — _starHashCompare (:242)
 │   │   │   │       └─ S4.10 Pairwise marking decision (the rule stack) — decideStarHashMark (:183)
 │   │   │   └─ S4.11 Mark code sequence (escalation) — assignStarHashCombos (:272)
 │   │   └─ S4.12 Mark code realization — starHashCodeToStrokes (:361)
 │   └─ S4.13 Mark merge into the last phoneme stroke — composeReservedKeyStrokes body (:434-445)
 ├─ S4.14 Self-homograph alternate strokes — buildExtraInducedStrokes (:1288) (summary only)
S4.15 Theory 2 report — Dictionary.writeFinalTheory (dictionary.py:392)
S4.16 (off-pipeline) Cross-category clash detector — detectCrossCategoryClash (:59)
```

Lemma-Homophone Marking (S4) takes the final induced strokes, meaning every Word's base
strokes plus at most one Marker Stroke Realization (Phase P) extra stroke. It finds every
group of words that still share one canonical final stroke **and** span at least two
`lemmeGramCat`s and at least two spellings. Each group is a lemma-homophone cluster. The
stage merges homographs and 1990-reform doublets, then ranks the cluster from most
canonical to most marked with a pairwise rule stack (S4.10). It gives each rank a mark
code: `()`, `*`, `#`, `*#`, then escalated `*#` codes. The mark's first symbol goes on the
word's last phoneme stroke, and any further symbols become bare mark strokes. The result
is theory 2 (`dict[Word, list[Strokes]]`), which exists only in memory, plus the
human-readable `theory2.tsv`. The stage exists because Marker Stroke Realization
(Phase P) separates only words with the same `lemmeGramCat`. Collisions across lemmas
("ver/vert/verre") and across categories of one lemma ("appel"/"appelle") are left to
this stage.

Live-data scale: 167,639 Words; **4,450 lemma-homophone clusters**. Cluster sizes (Words):
2: 2,947, 3: 989, 4: 341, 5: 104, 6: 40, 7: 19, 8: 7, 10: 1, 11: 2. Codes given out:
`()` 5,530, `*` 4,886, `#` 579, `*#` 146, `(*#,*#)` 51, `(*#)×3` 9, `(*#)×4` 3, `(*#)×5` 2.
In total 5,676 words are marked and 86 bare mark strokes are added.

## Calls

### Theory 2 assembly — Dictionary.buildFinalTheory (S4.1)   dictionary.py:342
Called by: Phonetic Theory Building (S2) `__main__` at dictionary.py:532 (runs only when
both `phase_g_keypress_assignment.json` and `resolved_press_sets.json` exist, :531), and by
every Theory Export (S5) exporter through `loadFirstAndFinalTheory` (S5.1)
util/_theoryio.py:82.
Input state: theory 1 (`dict[Strokes, list[Word]]`, 80,725 raw-Strokes keys / 167,639
Words); keyboard layout; paths to the keypress groups and the resolved press-sets.
Transformation: (1) Loads `markersByKeypress` (7 keypress groups) from the Marker Grouping
(Phase G) artifact (:365-369) and the resolved press-sets list (:370-371). (2) Runs
Marker Stroke Realization (Phase P) inline (S4.2, :373-384), which produces the final
induced strokes. (3) Calls `composeReservedKeyStrokes` (S4.4, :385-388) with the reform
doublet pairs (S4.3) and `phonemeStrokeCounts` = each Word's theory-1 stroke count. Those
counts switch on merge mode (S4.13). (4) Calls `buildExtraInducedStrokes` (S4.14, :389)
to get self-homograph alternates. (5) Returns
`{word: [primaryComposed[word]] + extraByWord.get(word, [])}` (:390). Index 0 is the
primary stroke, which carries the marks. Later indices are unmarked alternates.
Result: theory 2, one entry per Word (167,639), iterated in theory-1 order. The live
`theory2.tsv` has 181,869 rows, so there are 14,230 alternate strokes.
Artifacts: reads `phase_g_keypress_assignment.json`, `resolved_press_sets.json`,
`resources/reform1990.tsv` (via S4.3, path relative to the working directory).
Helpers not expanded: `buildWordToStrokes` src/ambiguitychecker.py:553.
Notes: The method never uses `self`, so it can be a free function. That is a refactor
candidate: exporters must unpickle the whole `Dictionary` just to call it.

### Marker Stroke Realization (Phase P), inline — (S4.2)   dictionary.py:373-384
Called by: Theory 2 assembly (S4.1).
Input state: theory 1, keypress groups, resolved press-sets.
Transformation: **Summary only; see the Marker Stroke Realization (Phase P) section of the
Same-Lemma Disambiguation (S3) call graph.** In order: `buildWordToStrokes` :553,
`buildWordsByOrthoLemme` :766, `buildKeypressGroupToWords` :803, `buildKeypressGroupExtraAlternates`
:844, `resolvePreferredKeysByGroup` :952, `realizeKeypressGroupsAsExtraStroke` :987, then
`buildFinalInducedStrokes` :1261 over the **whole** lexicon.
Result: final induced strokes (`dict[Word, Strokes]`, 167,639 Words, theory-1 order) and a
physical keypress assignment. Live chosen keys by group: 0→21, 1→16, 2→20, 3→23, 4→18,
5→17, 6→19. These are identical to the tracked report (see S5.6).

### Reform-doublet loading — loadReform1990DoubletPairs (S4.3)   src/ambiguitychecker.py:94
Called by: Theory 2 assembly (S4.1), dictionary.py:386.
Input state: `resources/reform1990.tsv` (lines starting with `#` are comments; the first
remaining line is the header).
Transformation: For each row whose `isException` column is not `"True"`, it adds
`frozenset({oldSpelling, newSpelling})`. Exception rows (`fût`/`fut`, `croît`/`croit`) are
reform pairs that collide with an unrelated word, so they are left out.
Result: `frozenset[frozenset[str]]`, 259 pairs live. These are **spellings of lemmas**.
S4.7 and S4.10 compare them against `Word.lemme`, not against `ortho`.
Artifacts: reads `resources/reform1990.tsv`.
Notes: Some reform pairs are listed only at verb-lemma level, for example
`boursoufler/boursouffler`. So an adjective doublet such as `boursouflée/boursoufflée`
(lemmas `boursouflé*`) is not caught, and it is handled by a `MARKING_OVERRIDES` entry
instead (see S4.10).

### Reserved-key composition — composeReservedKeyStrokes (S4.4)   src/ambiguitychecker.py:410
Called by: Theory 2 assembly (S4.1), dictionary.py:385.
Input state: final induced strokes; doublet pairs; `phonemeStrokeCounts`
(`dict[Word, int]`).
Transformation: Starts from `composed = dict(finalInduced)` (:434). For every
lemma-homophone cluster (S4.5), it gets each member's physical mark strokes (S4.6). Words
whose extra is `()` keep their final induced strokes. The rest are rewritten by the merge
rule (S4.13).
Result: `dict[Word, Strokes]` for every Word: marked words carry reserved keys 10/15, and
unmarked words keep their final induced strokes unchanged.
Notes: The docstring gives the collision-safety argument (:422-429). Reserved keys 10/15
are never in `Keyboard.allowedKeys` (keyboard.py:376), so removing them, and dropping
reserved-only trailing strokes, gives back the final induced strokes exactly. The
argument holds for primary strokes only. It does not cover alternates (S4.14).

### Lemma-homophone cluster detection — groupHomophonesByReservedStroke (S4.5)   src/ambiguitychecker.py:380
Called by: Reserved-key composition (S4.4), :435.
Input state: final induced strokes.
Transformation: Buckets Words by `canonicalizeStrokes(finalInduced[word])` (:396). It keeps
a bucket only if it has ≥ 2 Words (:400), ≥ 2 distinct `lemmeGramCat` (:402) and ≥ 2
distinct `ortho` (:404). Within a bucket, Words keep final-induced (= theory-1) order.
Result: `dict[Strokes, list[Word]]`, 4,450 lemma-homophone clusters live.
Helpers not expanded: `canonicalizeStrokes` keyboard.py:31.
Notes: A bucket with a single `lemmeGramCat` and several spellings is dropped on purpose
("Phase P's job"). Live data has **98** such buckets, for example `agi` vs a second,
zero-frequency `agis` Word (`ind:pas:2s`) that `_resolveEntryWord` did not map to the
press-set. They reach the Plover dictionary as collisions settled by frequency. All 98
losing spellings can still be reached through another Word's stroke, so nothing is lost
today. Also note the "≥ 2 `lemmeGramCat`" test: clusters where the lemma is the same but
the category differs ("appel" NOM / "appelle" VER) are in scope, which fits naming note 2
in the skeleton.

### Physical mark assignment — assignStarHashPhysicalStrokes (S4.6)   src/ambiguitychecker.py:369
Called by: Reserved-key composition (S4.4), :436.
Input state: one lemma-homophone cluster (`list[Word]`), doublet pairs.
Transformation: `{word: starHashCodeToStrokes(code)}` over `assignStarHashMarks` (S4.7,
S4.12).
Result: `dict[Word, Strokes]` of mark strokes. `()` means no mark.

### Mark code assignment — assignStarHashMarks (S4.7)   src/ambiguitychecker.py:292
Called by: Physical mark assignment (S4.6), :376.
Input state: one lemma-homophone cluster, in theory-1 order.
Transformation, step by step:
1. **Homograph merge** (:307-311): group by `ortho` in first-seen order. Each ortho group's
   *representative* is `max(group, key=frequency)`. On a tie, the first in list order wins.
2. **Doublet merge (union-find)** (:313-330): for every pair of ortho-group
   representatives `i<j`, if `{rep_i.lemme, rep_j.lemme}` is a doublet pair, union the two
   groups. The code uses path-halving `find` and does `parent[ri] = rj` without ranks.
   Only the representatives' lemmas are checked, not the other members' lemmas.
3. Merged groups (dict keyed by root, in first-seen order) → the **mark representative**
   of each group = `max(group, key=frequency)` (:332).
4. `ranked = rankHomophoneCluster(mergedRepresentatives)` (S4.8);
   `codes = assignStarHashCombos(len(ranked))` (S4.11); representatives are zipped to codes
   in rank order (:333-335).
5. Every Word of a merged group gets its representative's code, stored by `ortho`
   (:337-343).
Result: `dict[Word, tuple[str, ...]]`. All homographs share one code, and so do all
reform doublets. Live data: 18 clusters end with a single code (all doublets), and
21 composed strokes stay shared by a doublet pair.

### Cluster ranking — rankHomophoneCluster (S4.8)   src/ambiguitychecker.py:261
Called by: Mark code assignment (S4.7), :333.
Input state: the mark representatives. Their spellings are all distinct and no two form
a doublet pair.
Transformation: `sorted(words, key=cmp_to_key(_starHashCompare))` (S4.9), with the most
canonical first. CPython's sort is stable, but that guarantees a unique result only if
the comparator is a consistent total order. It is not (see Suspected bugs 1-2).
Result: ranked list; position 0 is the canonical member.

### Ranking comparator — _starHashCompare (S4.9)   src/ambiguitychecker.py:242
Called by: Cluster ranking (S4.8).
Transformation: If `a is b` it returns 0. Otherwise `marked = decideStarHashMark(a, b)`
(S4.10). If `marked is None` (rule 1 or rule 2), it compares by higher frequency first,
then by `ortho` ascending, then returns 0. Otherwise it returns `+1` when `a` is the
marked word and `-1` when `b` is.
Result: -1/0/+1.
Notes: The `None` branch never runs in the pipeline, because S4.7 has already merged
every homograph and doublet pair, so rules 1 and 2 cannot fire. The **real** tie case is
different: equal frequency under rules 4, 5 or 7. There, `decideStarHashMark` marks
its *first* argument, so `compare(a,b)` and `compare(b,a)` both return +1. See Suspected
bug 1.

### Pairwise marking decision (the marking rule stack) — decideStarHashMark (S4.10)   src/ambiguitychecker.py:183
Called by: Ranking comparator (S4.9), :253.
Input state: two Words from one cluster, and the doublet pairs.
Transformation: the **marking rule stack**, checked in this order. The first rule that
matches decides. "Mark X" means X is the less canonical word. Frequency is always
`Word.frequency` = `frequencyFilm` only (word.py:93); book frequency is ignored.

| # (this doc) | Code line | Condition | Outcome |
|---|---|---|---|
| R1 homograph exemption | :211 | `wordA.ortho == wordB.ortho` | `None` (no mark) |
| R2 reform-doublet exemption | :214 | `frozenset({wordA.lemme, wordB.lemme}) in doubletPairs` (259 pairs; the default argument is empty) | `None` |
| R3 per-pair override | :217-219 | `MARKING_OVERRIDES.get(frozenset({wordA.ortho, wordB.ortho}))` is not None (49 entries, :130-180, keyed by **ortho** regardless of lemma/category) | mark the word whose `ortho` equals the stored value |
| R4 frequency-ratio rule | :221-225 | `lo, hi = min/max(freqA, freqB)`; `ratio = hi/lo`, or `inf` if `lo == 0`; `ratio >= RATIO_EXEMPTION_THRESHOLD` (= **10.0**, :91) | mark the rarer word: `wordA if freqA <= freqB else wordB` (tie → **wordA**) |
| R5 same-category rule | :224-225 (the same `if`, `or wordA.gramCat == wordB.gramCat`) | the two `GramCat` enums are equal (so `ADJ` ≠ `ADJ:pos`) | same as R4: mark the rarer word, tie → wordA |
| R6 category-priority rule | :227-230 | both `gramCat.name`s are in `GRAMCAT_PRIORITY` (src/greedyoptimizer.py:62) | mark the lower-priority word: `wordA if pA < pB else wordB` |
| R7 frequency fallback | :232 | either category is missing from the table | mark the rarer word, tie → wordA |

`GRAMCAT_PRIORITY` (higher = more canonical): `ADV` 50, `PRO:pos` 40, `NOM` 30, `VER` 20,
`ADJ` 10, `ADJ:pos` 0. Any other category (`PRE`, `ONO`, `ART:def`, `PRO:per`, `AUX`,
`CON`, …) falls to R7. So R6 can never apply to them, not even a `PRE` vs `NOM` pair.

`MARKING_OVERRIDES` (unordered spelling pair → spelling to mark): sales/**salles**,
entrés/**entrées**, alentours/**alentour**, virés/**virées**, portés/**portées**,
envolés/**envolées**, dorés/**dorées**, closes/**clauses**, comptés/**comtés**,
montés/**montées**, remontés/**remontées**, hautes/**hôtes**, retenus/**retenues**,
éteints/**étains**, new/**news**, plongés/**plongées**, survenus/**survenues**,
gelés/**gelées**, usagés/**usagers**, accros/**accrocs**, percés/**percées**,
levés/**levers**, traversés/**traversées**, rangés/**rangées**, réaux/**réal**,
rentrés/**rentrées**, impairs/**impers**, coronaires/**coroners**, crus/**crues**,
nazes/**nases**, balèzes/**balaises**, lares/**lards**, perçants/**persans**,
troués/**trouées**, craints/**crins**, visés/**visées**, ancrés/**encrés**,
jetés/**jetées**, rués/**ruées**, dévonienne/**dévonien**, pincés/**pincées**,
monomoteurs/**monomoteur**, hautains/**hautins**, boursouflée/**boursoufflée**,
bouillis/**bouillies**, bivalves/**bivalve**, nichés/**nichées**,
stabilisante/**stabilisant**, camés/**camées**.

Result: the Word to mark, or `None`.
Live rule usage among representative pairs in all clusters: R4 4,284 · R5 854 · R6 838 ·
R7 93 · R3 45 · R2 0 (21 doublet pairs exist but are merged first) · R1 0.
Notes: R4 is called an "exemption" in the code and the docs. It exempts a pair from the
*category* rule, **not** from marking: the rarer word is still marked. Any zero-frequency
word loses to any word with a non-zero frequency through R4 (`ratio = inf`). Two
zero-frequency words also go to R4, and there the first argument is marked.

### Mark code sequence (escalation) — assignStarHashCombos (S4.11)   src/ambiguitychecker.py:272
Called by: Mark code assignment (S4.7), :334.
Transformation: The base budget is `[(), ('*',), ('#',), ('*#',)]`. After that, each further
rank adds `('*#',) * n` with `n = 2, 3, 4, …` (:284-288). The list is truncated to the
cluster's rank count.
Result: codes in increasing markedness: rank 0 `()`, 1 `*`, 2 `#`, 3 `*#`, 4 `*# *#`,
5 `*# *# *#`, and so on. There is no upper bound. The live maximum is 8 representatives,
giving code `(*#)×5`.

### Mark code realization — starHashCodeToStrokes (S4.12)   src/ambiguitychecker.py:361
Called by: Physical mark assignment (S4.6).
Transformation: Each symbol becomes one Stroke through `_STAR_HASH_KEYS` (:354):
`*` → `(10,)`, `#` → `(15,)`, `*#` → `(10, 15)`. `STAR_KEY = 10` (:351), `HASH_KEY = 15`
(:352). Keys 0/1 (left pinky, also reserved at keyboard.py:320) are held for a possible
third mark and are never used.
Result: Strokes of reserved-only strokes; `()` for the canonical member.

### Mark merge into the last phoneme stroke — composeReservedKeyStrokes body (S4.13)   src/ambiguitychecker.py:437-444
Called by: Reserved-key composition (S4.4).
Input state: a marked Word's final induced strokes `s` (the base strokes, optionally
followed by one Phase P coda stroke) and its mark strokes `extra`.
Transformation: If `phonemeStrokeCounts is None` (tests only), it appends:
`s + extra`. Otherwise (the pipeline), with `last = phonemeStrokeCounts[word] - 1`, it
builds `s[:last] + (s[last] + extra[0],) + s[last+1:] + extra[1:]`. The first mark
symbol's keys are added to the **last phoneme stroke**, not to the Phase P stroke. The
Phase P stroke (if any) keeps its place, and the escalated code's remaining symbols
follow as bare mark strokes.
Result: e.g. `pâts` `((4,12),(17,))` + `*` → `((4,12,10),(17,))` rendered `p*a/-s`;
`aulx` `((12,14),)` + `(*#)×5` → `((12,14,10,15),(10,15),(10,15),(10,15),(10,15))` rendered
`*ae#/*#/*#/*#/*#`.

### Self-homograph alternate strokes — buildExtraInducedStrokes (S4.14)   src/ambiguitychecker.py:1288
Called by: Theory 2 assembly (S4.1), dictionary.py:389.
Transformation: **Summary; belongs to Marker Stroke Realization (Phase P).** For each
non-primary press-set alternate, it builds the base strokes plus that alternate's union of
chosen keys, and skips an alternate whose key set is empty. It **does not** go through
Lemma-Homophone Marking (S4).
Result: `dict[Word, list[Strokes]]`, appended after index 0 in theory 2.
Notes: This known scope gap has a concrete cost today. An unmarked alternate can take
the only stroke of an unrelated word. In the Plover dictionary, `subits` (ADJ,
`s@i/svi/-s`) loses to `subis`'s participle-plural alternate. `pais` (`pie/-k`) loses to
`paie`, and `amplis` (`@/pmti/-s`) loses to `emplis`. The same happens to bénits, brandys,
bégaies, baillez, baryes and repais: 9 spellings with no Plover entry (see S5.3).

### Theory 2 report — Dictionary.writeFinalTheory (S4.15)   dictionary.py:392
Called by: `__main__` dictionary.py:533, right after S4.1.
Input state: theory 1 and theory 2.
Transformation: Writes a header `ortho lemme gramCat strokes extraStrokes`, then Words
sorted by `(lemme, gramCat.name, ortho)`, with one row per stroke in the Word's list.
`strokes` holds the base strokes as phoneme letters (`strokesToString`). `extraStrokes`
starts with `+k,…` when the mark was merged: those are the keys added to the last phoneme
stroke, `set(full[len(base)-1]) - set(base[-1])`. After that come the trailing strokes as
raw key-index lists, joined with `/`.
Result: `theory2.tsv` (gitignored, 181,869 data rows). Example rows: `aile … iel +10`,
`ailes … iel +10/17`, `hèle … iel +15`, `elles … iel 17`.
Artifacts: writes `theory2.tsv`.
Notes: This is a terminal human view. Nothing reads it (every exporter recomputes theory
2; see S5.1).

### (off-pipeline) Cross-category clash detector — detectCrossCategoryClash (S4.16)   src/ambiguitychecker.py:59
Called by: `classifyStrokeCluster` :448 ← `classifyTheory` :483 ← `ambiguitychecker`
`__main__` :1355 (diagnostic "Phase 0 ambiguity report"), and tests. **Not called by
the pipeline.**
Transformation: Groups the words of one stroke cluster by bare `lemme`, then by
`lemmeGramCat`. It flags a lemma when it has ≥ 2 `lemmeGramCat` sub-groups, every
sub-group is a singleton, and the spellings differ ("aller" NOM vs VER style).
Result: `list[Lemme]`.
Notes: In the pipeline, cross-category clashes are handled implicitly: S4.5's
"≥ 2 `lemmeGramCat`" filter admits them. The Phase P report's
`crossCategoryClashCollisions` bucket (:1249) is computed separately, by an inline test.

### Worked examples (live data, 2026-09-22)

1. **Two-word cluster, R6 category rule.** Cluster `((12,), (4,13,14,23))`: `appel` NOM
   80.88 and `appelle` VER 485.77. The ratio is 6.0 < 10 and the categories differ, both
   in the table: NOM 30 > VER 20, so **`appelle` is marked** even though it is 6× more
   frequent. Plover: `a/piel` → appel, `a/p*iel` → appelle. `appelle`'s alternates
   `a/piel/-k` and `a/piel/-l` carry no mark (S4.14).
2. **Four-slot cluster with homograph merge, R4 and R7.** Cluster `((12,),)`: `à` PRE
   12,190.4; `a` AUX 6,350.91, VER 5,498.34 and NOM 81.36 (homographs, representative AUX);
   `ah` ONO 576.53; `ha` ONO 21.54 and NOM 2.94 (representative ONO). `à` vs `a`: ratio 1.9,
   PRE is not in the table → R7 → `a` is marked. `ah` vs `a` has ratio 11.0 → R4, and `ha`
   loses to everyone by R4. Rank: à `()`, a `*`, ah `#`, ha `*#`. Plover: `a`→à,
   `*a`→a, `a#`→ah, `*a#`→ha.
3. **Escalated cluster.** Cluster `((12,14),)` (11 Words, 8 representatives): au ART:def
   3,737.75 `()`; oh ONO 897.52 `*` (oh NOM 0.01 merged); aux ART:def 835.65 `#` (vs oh:
   ratio 1.07, neither category in the table → R7); eau NOM 290.61 `*#`; haut (NOM 75.22
   representative; ADV, ADJ merged) `*# *#`; ho ONO 20.06 `(*#)×3`; ô ONO 16.08 `(*#)×4`;
   aulx NOM 0.0 `(*#)×5`. Plover: `ae`, `*ae`, `ae#`, `*ae#`, `*ae#/*#`, … `*ae#/*#/*#/*#/*#`.
   (ROADMAP.md:183 calls a 7-reading version of this cluster the largest.)
4. **1990-reform doublet.** Cluster `((3,5,13),(7,9,11,13))`: `bizut` (lemma bizut) 2.05
   and `bizuths` (lemma bizuth) 0.0. `{bizuth, bizut}` is a reform pair, so S4.7 merges them
   and both get `()`. They still collide, and the Plover dictionary keeps `bizut`; `bizuths`
   has no entry.
5. **Frequency tie decided by input order.** Cluster `((4,12),(17,))`: `pas` NOM 0.0 and
   `pâts` NOM 0.0. `lo = 0` gives R4, the tie marks the first argument, and CPython's
   insertion sort calls `compare(later, earlier)`. So the later Word in theory-1 order is
   marked: `pâts` → `p*a/-s`. With the list reversed, `pas` is marked instead.
6. **The `aile`/`ailes`/`elles`/`hèle` change** (see the diagnosis in Suspected bug 1).
   Theory-1 cluster `((13,14,23),)`: elle PRO:per 4,520.53, elles PRO:per 420.51, ailes NOM
   18.45, aile NOM 15.0, hèle VER 0.05.
   *Before a1d0fb5* (`elles` had its own lemma): Phase P gave `elles` no key, so the
   final induced cluster `iel` = {elle, elles, aile, hèle}. elle vs elles → R5; elles vs
   aile → R4 (28×); aile vs hèle → R4. Codes: elle `()`, elles `*`, aile `#`, hèle `*#`.
   ailes (key 17 from Phase P) was alone in its cluster.
   *After* (`elles` folded into lemma `elle`, commit a1d0fb5): `elles` gets key 17 and
   joins `ailes`. Cluster `iel` = {elle `()`, aile `*`, hèle `#`}; cluster `iel/-s` = {elles
   `()`, ailes `*`}. Plover diff 3b22e0f → a1d0fb5: `iel/#`→aile became `*iel`, `iel/*`→elles
   became `iel/-s`, `iel/*#`→hèle became `ie#l`, `iel/-s`→ailes became `*iel/-s`.

## New glossary terms
- **Lemma-homophone cluster** — The unit of Lemma-Homophone Marking (S4): Words that share
  one canonical final induced stroke, with ≥ 2 `lemmeGramCat` and ≥ 2 spellings.
  *`groupHomophonesByReservedStroke` ambiguitychecker.py:380.* (Adopts the skeleton's
  proposal for "cluster" sense 3b.) Avoid "homophone group" for it, which is the
  same-`lemmeGramCat` unit.
- **Mark representative** — The highest-frequency member of a merged homograph/doublet
  group inside a cluster. Only representatives are ranked, and every member takes its
  code. *`assignStarHashMarks` :311, :332.*
- **Marking rule stack (R1-R7)** — The ordered pairwise rules of `decideStarHashMark`:
  R1 homograph exemption, R2 reform-doublet exemption, R3 per-pair override, R4
  frequency-ratio rule, R5 same-category rule, R6 category-priority rule, R7 frequency
  fallback. *ambiguitychecker.py:183-232.* The code docstring numbers R1-R6 the same way,
  with R7 as the unnumbered fallback. RESUME_2026-09-20-starhash-priority.md and the
  comments at :392/:431 use another numbering (ratio = Rule 1, homograph = Rule 2,
  doublet = Rule 3). Cite the rules by name.
- **Frequency-ratio rule** — R4: when one word's film frequency is ≥ 10× the other's
  (or the other is 0), the rarer word is marked. It is called the "10x ratio exemption"
  in the code and docs. Avoid "exemption", because the pair is still marked: the rule
  only skips the category rule.
- **Bare mark stroke** — A trailing stroke containing only reserved keys (`*#`). Only
  escalated codes produce one, for their 2nd and later symbols. *composeReservedKeyStrokes
  :444; _stenorender.py:11.*
- **Film frequency** — `Word.frequency` = `frequencyFilm` (word.py:93), the only frequency
  used by marking decisions and by every "keep the most frequent" exporter rule.

## Suspected bugs
- src/ambiguitychecker.py:224-225, :232 — On a frequency tie, `decideStarHashMark` marks its
  first argument, so `_starHashCompare` is not antisymmetric (`cmp(a,b) == cmp(b,a) == +1`)
  and the ranking depends on input order. Scenario: `pas`/`pâts` (both 0.0): input
  `[pas, pâts]` marks `pâts`; `[pâts, pas]` marks `pas`. Live data has 648 tied
  representative pairs in 618 of 4,450 clusters. Shuffling each cluster's input changes
  the marks in **619 clusters (14%)**, almost all zero-frequency rare words. Confidence:
  high (reproduced in memory).
  **Nondeterminism diagnosis:** marking is *not* nondeterministic from run to run. Nothing
  on this path iterates a hash-ordered set of Words: `Word.__hash__` is salted per
  process, but it is used only for lookups, and every order comes from lists and dicts in
  insertion order, which descends from lexicon row order. It *is* order-dependent,
  however: any change that reorders a cluster's members can flip marks between tied
  words. That includes a lexicon row move, appended `LexiqueSynthetic` rows, a Word
  moving to another theory-1 key, or a new Word joining the cluster. The reported
  `aile`/`ailes`/`elles`/`hèle` change is **not** such a flip. It is fully explained by the
  input change in a1d0fb5 (`elles` folded into lemma `elle`, which moves `elles` into the
  plural cluster). The Plover dictionaries at 3b22e0f and a1d0fb5 show exactly the
  predicted before/after marks (worked example 6), and the current rebuild reproduces
  a1d0fb5 byte for byte for these words. Fix direction (not applied): break ties by
  `frequencyBook`, then by `ortho`, inside R4/R5/R7.
- src/ambiguitychecker.py:224 vs :229 — R4 and R6 can form a cycle, and
  `sorted(cmp_to_key(...))` over a cyclic comparator gives an order-dependent ranking.
  Scenario: A ADV f=1, B NOM f=2, C VER f=10: A before B (R6), B before C (R6), C before A
  (R4, ratio 10). Live data has 0 cycles among representatives. Confidence: high that it can
  happen, low impact today.
- src/ambiguitychecker.py:321-326 — The doublet union-find checks only each ortho group's
  representative lemma. If a lower-frequency homograph carries the lemma that forms the
  reform pair, the doublet is missed and the pair is marked as a real ambiguity. Scenario:
  ortho group {x/L1 (freq 5), x/L2 (freq 0)}, and y/L2′ with {L2, L2′} a reform pair → y is
  marked against x. There are 0 instances in live data. Confidence: low.
- src/ambiguitychecker.py:1288 / dictionary.py:389 — Unmarked self-homograph alternates can
  take the only stroke of an unrelated word, making it untypeable in Plover (`subits`,
  `pais`, `amplis`, and 6 more; see S4.14). This is a known scope gap, now with measured
  cost. Confidence: high.
- src/ambiguitychecker.py:402 — 98 same-`lemmeGramCat` final-stroke collisions (e.g. `agi`
  and the zero-frequency `agis` `ind:pas:2s` Word) survive both Marker Stroke Realization
  (Phase P) and this stage. The "0 residual same-`lemmeGramCat` collisions" regression
  does not see them, because it counts only the Words Phase P touched. No spelling is
  lost today. Confidence: medium (to cross-check with the S3 agent's `_resolveEntryWord`
  findings).

## Dead-code observations
- `detectCrossCategoryClash` :59 (with `classifyStrokeCluster` :448 and `classifyTheory`
  :483) — reached only from the diagnostic `__main__` :1355 and tests.
- `decideStarHashMark` R1 (:211) and R2 (:214), and `_starHashCompare`'s `None` fallback
  (:254-257) — cannot be reached from the pipeline, because `assignStarHashMarks` merges
  homographs and doublets before ranking. They are kept for the pairwise API and tests.
- `MARKING_OVERRIDES` entries never reached with live data (their pairs are no longer in
  any lemma-homophone cluster; most are now same-`lemmeGramCat` and handled by Marker
  Stroke Realization (Phase P)): {new, news}, {réaux, réal}, {dévonien, dévonienne},
  {stabilisant, stabilisante}. 45 of the 49 entries are reached.
- `composeReservedKeyStrokes`'s appended mode (`phonemeStrokeCounts is None`, :440-441) —
  used only by tests (src/test/ambiguitychecker_test.py:393, :411, :422, :430).

## Doc drift
- src/ambiguitychecker.py:245-250 (`_starHashCompare` docstring) says the frequency-then-ortho
  fallback keeps `sort()` "stable and deterministic". That fallback only covers `None`,
  which cannot happen in the pipeline. The real tie case (R4/R5/R7) has no tie-break.
- src/ambiguitychecker.py:206-208 says a category pair outside the 6-entry table was "not
  observed in the design session's residual". Live data sends 93 representative pairs to
  that fallback (R7), for example `aux` ART:def vs `oh` ONO and `à` PRE vs `a` AUX.
- src/ambiguitychecker.py:200 and ROADMAP.md:175 call R4 a "frequency-ratio exemption".
  The code marks the rarer word. See the S5 doc drift for exporters that take the word
  literally.
- ROADMAP.md:183-184: "biggest real cluster: 7 readings (au/eau/oh/haut/ho/ô/aux)". Live
  data: that cluster has 8 representatives (plus `aulx`), and the largest clusters have 11
  Words.
- src/ambiguitychecker.py:392 ("Rule 2", homograph) and :431 ("Rule 3", doublet) use the
  RESUME numbering, not the docstring's R1/R2 (already in the skeleton).
- dictionary.py:357-360 (`buildFinalTheory` docstring) says the `*`/`#` track "isn't wired
  into a self-homograph's alternates yet". That is accurate, but it does not mention that
  alternates can now take an unrelated word's only stroke (S4.14).

---

# Theory Export (S5)

## Overview

```
S5.1  Theory 2 loading — loadFirstAndFinalTheory / loadFinalTheory (util/_theoryio.py:68, :48)
       └─ _loadDictionaryAndFirstTheory (:17) → Dictionary.buildFinalTheory (Lemma-Homophone Marking (S4).1)
S5.2  Stroke rendering — renderFinalStrokesToRTFCRE (util/_stenorender.py:39)
       ├─ _renderMarkedStroke (:26)
       └─ Starboard.strokesToRTFCRE (src/keyboard.py:683)
S5.3  Plover dictionary export — export_plover_dictionary.main (util/export_plover_dictionary.py:35)  → S5.1, S5.2
S5.4  Plover key table export — export_plover_system.main (util/export_plover_system.py:38)
S5.5  Plover system plugin — plover_stenalgo/plover_stenalgo/system.py (+ pyproject entry point)
S5.6  Trainer keyboard legend — export_keyboard_layout.main (util/export_keyboard_layout.py:148)
S5.7  Trainer word drill — export_practice_words.main (util/export_practice_words.py:208)  → S5.1, S5.2
S5.8  Trainer sentences — export_practice_sentences.main (util/export_practice_sentences.py:145)  → S5.1, S5.2, reads S5.7 output
S5.9  Trainer definitions — export_definitions.main (util/export_definitions.py:46)  → S5.1, S5.2
```

Theory Export (S5) turns theory 2 into the files people actually use: the Plover
dictionary (RTFCRE steno → spelling), the Plover key table and system plugin, and four
JSON files for the steno-trainer web app. **Confirmed:** every exporter that needs theory 2
(S5.3, S5.7, S5.8, S5.9) recomputes it in its own process. Each one unpickles the
`Dictionary` and theory 1, then calls `Dictionary.buildFinalTheory`, which reruns Marker
Stroke Realization (Phase P) and Lemma-Homophone Marking (S4). No exporter reads
`theory2.tsv`. A full export therefore computes theory 2 four times. The key table (S5.4)
and the trainer keyboard legend (S5.6) read only `starboard3h.json`, and the legend also
reads the tracked Phase P report.

## Calls

### Theory 2 loading — loadFirstAndFinalTheory / loadFinalTheory (S5.1)   util/_theoryio.py:68, :48
Called by: Plover dictionary export (S5.3) through `loadFinalTheory`; trainer exporters
(S5.7, S5.8, S5.9) through `loadFirstAndFinalTheory`. Marker Stroke Realization (Phase P),
report build (`util/build_phase_p_realization.py:44`) uses `loadFirstTheory` (:42) only.
Input state: `Dictionary.pickle`, `FirstTheory.pickle`, keypress groups, resolved press-sets
on disk.
Transformation: It checks that both JSON inputs exist and raises otherwise (:76-79).
`_loadDictionaryAndFirstTheory` (:17) aliases `__main__.Dictionary`, because the pickle
was written by `dictionary.py` run as `__main__`. It then unpickles the five
`Dictionary.pickle` objects, restoring the `Syllable` class state, and then theory 1.
Finally it calls `dictionary.buildFinalTheory(theory, keyboard, …)` (:82), which is
Lemma-Homophone Marking (S4).1.
Result: (theory 1, theory 2); `loadFinalTheory` drops theory 1.
Artifacts: reads `Dictionary.pickle`, `FirstTheory.pickle`, `phase_g_keypress_assignment.json`,
`resolved_press_sets.json`, `resources/reform1990.tsv`.
Notes: The docstring (:3) says the loader was factored out of
`build_phase_p_realization.py`. That script now uses only `loadFirstTheory`.

### Stroke rendering — renderFinalStrokesToRTFCRE (S5.2)   util/_stenorender.py:39
Called by: S5.3 (:45), S5.7 (:231), S5.8 (:164), S5.9 (:65).
Input state: one theory-2 Strokes.
Transformation: For each stroke it takes `keys = sorted(set(stroke))`, so it renders the
canonical form, then applies three branches:
1. **Bare mark stroke** (every key is 10 or 15): the display names are concatenated, giving
   `*`, `#` or `*#` (:43-44).
2. **Merged mark stroke** (a mix of reserved and phoneme keys): `_renderMarkedStroke` (:26)
   applies Plover's `plover_stroke` hyphen rule. Implicit-hyphen keys are the nucleus keys
   (11-14) plus `STAR_KEY` 10. `firstRightKey = max(implicit) + 1` = 15. A `-` goes before
   the first key ≥ 15 only when the stroke has no implicit-hyphen key. Each display name
   has its hyphens stripped. Examples: `*iel`, `ie#l`, `swa#`, `pvR-#`.
3. **Plain stroke**: `Starboard.strokesToRTFCRE` (keyboard.py:683) buckets the keys by
   syllabic part, strips hyphens, and inserts `-` as the nucleus when the stroke has no
   vowel key.
The strokes are joined with `/`.
Result: an RTFCRE string using Stenalgo key names (the KEYS order in S5.4).
Helpers not expanded: `Starboard.keyDisplayName` keyboard.py:654 (reserved names
`{0:"&", 1:"%", 10:"*", 15:"#"}` at :652; onset `x-`, coda `-x`, and nucleus keys split by
thumb).

### Plover dictionary export — export_plover_dictionary.main (S5.3)   util/export_plover_dictionary.py:35
Called by: `python -m util.export_plover_dictionary`.
Input state: theory 2 (S5.1).
Transformation: It renders every stroke of every Word (S5.2) into
`stenoToWords[steno]`, skipping an exact duplicate Word (:50). For each steno string it
keeps `max(words, key=frequency)` (:56); on a tie, the first in theory-2 (= theory-1)
order wins. Collisions are counted and the top 10 are printed.
Result: Plover dictionary, `dict[str, str]`, written with `sort_keys=True`, `indent=1`.
Live: 163,238 entries; 5,139 contain `*`/`#`; 58 end in a bare `*#` stroke. 29 spellings of
the lexicon have **no** entry. That is 20 reform-doublet or near-doublet losers
(`bizuths`, `dégottés`, `toquade`, `cuissot`, …) plus the 9 alternate-shadowed spellings
from Lemma-Homophone Marking (S4).14.
Artifacts: writes `plover_stenalgo_dictionary.json` (tracked).

### Plover key table export — export_plover_system.main (S5.4)   util/export_plover_system.py:38
Called by: `python -m util.export_plover_system`.
Input state: keyboard layout (`starboard3h.json`).
Transformation: `KEYS` = `Starboard.keyDisplayNames()` (keyboard.py:679) in key-index order:
`& % k- s- p- v- m- t- R- w- * @- a- -i -e # -j -s -k -d -t -R -n -l -Z -m`.
`IMPLICIT_HYPHEN_KEYS` = the nucleus key names plus `names[10]` (`*`) (:44-46).
`GEMINI_PR_KEYMAP` zips the names with the hard-coded, hardware-sniffed `GEMINI_PR_LABELS`
(:28-35). Keys 0, 1, 2 and 10 are sent as number-bar bits `#A #B #C #1`, and key 15 (`#`)
is the only real star bit `*4`.
Result: Plover key table.
Artifacts: writes `plover_stenalgo/plover_stenalgo/_generated_keys.py` (tracked).
Notes: The implicit-hyphen set here must match `_renderMarkedStroke`'s
(`nucleus ∪ {STAR_KEY}`, S5.2). The two are computed separately in two files, so a layout
change that moved `*` or the nucleus keys would need both updated.

### Plover system plugin — plover_stenalgo (S5.5)   plover_stenalgo/plover_stenalgo/system.py
Called by: Plover, through the entry point `[project.entry-points."plover.system"]
"Stenalgo French" = "plover_stenalgo.system"` (plover_stenalgo/pyproject.toml:12-13).
What it registers: a system module exposing `KEYS`, `IMPLICIT_HYPHEN_KEYS` (from S5.4),
`SUFFIX_KEYS = ()`, `NUMBER_KEY = None`, `NUMBERS = {}`, `UNDO_STROKE_STENO = "*"` (:26),
no orthography rules, `KEYMAPS = {"Gemini PR": GEMINI_PR_KEYMAP}` (only the built-in Gemini
PR machine is remapped; there is no machine plugin), and `DEFAULT_DICTIONARIES =
("user.json", "commands.json")`. It has no dependencies; `__init__.py` is empty.
Notes: A bare `*` is the undo stroke. That is safe because the first mark symbol is always
merged into a phoneme stroke, and escalated bare strokes are always `*#`, never a bare `*`.
`plover_stenalgo_dictionary.json` is not in `DEFAULT_DICTIONARIES`, so the user adds it by
hand.

### Trainer keyboard legend — export_keyboard_layout.main (S5.6)   util/export_keyboard_layout.py:148
Called by: `python -m util.export_keyboard_layout`.
Transformation (lighter depth): For each key it writes the index, display name, 1-key
phonemes, hand/row/col (from the hand-coded grid, `_handAndGridPosition` :51), finger,
syllabic part, the reserved flag and the Gemini label. It adds multi-key phoneme layers
(`_phonemeLayers` :81) and `conjugationMarkers` (`_conjugationMarkers` :117). The latter
reads **`phase_p_keypress_realization.json`** (:128) and emits, for each keypress group,
its `chosenKeys`, key names and French marker labels, sorted by keys. It does not call
`buildFinalTheory`.
Result: `steno-trainer/public/data/keyboard-layout.json`.
Notes, **drift check (verified):** the Plover dictionary and the other trainer files get
their marker keys from the inline Marker Stroke Realization (Phase P) (S4.2), but this
legend gets them from the tracked report. Today they agree: inline and report both have
0→21, 1→16, 2→20, 3→23, 4→18, 5→17, 6→19, and so does the committed HEAD report. The
working-tree report is currently modified (not committed). Risk: if Marker Grouping
(Phase G) or the press-sets change and `util/build_phase_p_realization.py` is not rerun,
the legend will show keys that differ from the keys the dictionary and drills use.
Nothing detects the mismatch. Confidence: medium.

### Trainer word drill — export_practice_words.main (S5.7)   util/export_practice_words.py:208
Called by: `python -m util.export_practice_words [--limit N]`.
Transformation (lighter depth): `buildReadingsByWord` (:175) maps each resolved press-set
entry's `readings` (one per alternate) to a real Word via `_resolveEntryWord`, the same
matcher Phase P uses. `chordsWithReadings` (:194) pairs each theory-2 stroke with its
readings. If the counts don't line up, every stroke gets all of
`wordFeatureCombinations(word)` and the Word is counted as "misaligned". Records are keyed
by **(ortho, steno)**. A second Word with the same key merges its label and context
(:233-245). Each record carries `before`/`after` context words (`formatContext` :133),
the French label (`formatReadingsLabel` :112), the dotted phonology, the steno, the
sorted key strokes and the film frequency. Records are sorted by (−frequency, ortho,
steno) and truncated to 10,000.
Result: `steno-trainer/public/data/practice-words.json` (10,000 drill items).

### Trainer sentences — export_practice_sentences.main (S5.8)   util/export_practice_sentences.py:145
Called by: `python -m util.export_practice_sentences`; it must run after S5.7.
Transformation (lighter depth): It builds `chordsByOrtho` from theory 2 (S5.1, S5.2). For
each LLM-annotated candidate in `util/candidate_sentences.jsonl` (276 lines),
`resolveToken` (:74) narrows the chords by lemma, category, infoVerb tag and
gender/number. It rejects `sub:`/`ind:pas` tags, unknown forms, ambiguous stenos, and
chords that are not an S5.7 drill item (`(ortho, steno)` from `practice-words.json`, :158).
Result: `steno-trainer/public/data/practice-sentences.json` (217 sentences live).
Notes: The drill-item gate compares against a file written by **another process's**
recompute of theory 2. If any input changed between the S5.7 and S5.8 runs, valid
sentences are rejected as "not a drilled word".

### Trainer definitions — export_definitions.main (S5.9)   util/export_definitions.py:46
Called by: `python -m util.export_definitions`.
Transformation (lighter depth): It groups every theory-1 Word by its **canonical base**
steno (`canonicalizeStrokes` + `strokesToRTFCRE`). For each Word it lists the spelling,
phonology, frequency, and `[steno, label index]` for each theory-2 stroke. It merges
identical rows (`_mergeIdenticalRows` :35), sorts by (−frequency, ortho), and writes
compact positional JSON with a shared label table.
Result: `steno-trainer/public/data/definitions.json` (whole lexicon).

## New glossary terms
- **Implicit-hyphen key** — A key whose presence in a stroke means no `-` separator is
  needed before the right-bank keys (Plover's term). Here: nucleus keys 11-14 and `*` (10).
  *export_plover_system.py:44; _stenorender.py:27.*
- **Merged mark stroke** — The rendered form of a last phoneme stroke carrying the first
  mark symbol (`*iel`, `ie#l`, `pvR-#`). *_renderMarkedStroke _stenorender.py:26.* (The
  rendering counterpart of the seed term **Merged mark**.)
- **Gemini PR keymap** — The mapping from Stenalgo key names to Gemini PR wire labels,
  taken from hardware sniffing. *GEMINI_PR_LABELS export_plover_system.py:28.*
- **Drill item** — One `practice-words.json` record, keyed by (ortho, steno). *export_practice_words.py:225.*
  Avoid "Chord" for it: `Chord` in export_practice_sentences.py:50 is the in-memory
  (Word, strokes, steno, readings) record.
- **Conjugation-marker legend** — The trainer's keypress-group → key legend, read from the
  Phase P report. *`_conjugationMarkers` export_keyboard_layout.py:117.*

## Suspected bugs
- util/export_keyboard_layout.py:128 — The legend reads the tracked Phase P report while the
  dictionary recomputes Phase P inline, and no check compares the two. Scenario: Marker
  Grouping (Phase G) is rerun, the report is not rebuilt, and the legend shows old keys.
  They agree today (verified). Confidence: medium.
- util/export_keyboard_layout.py:133-141 — `chosenKeys: null` for an unassigned group would
  raise `TypeError` (already in the skeleton). Confidence: high; likelihood: low.
- util/export_plover_dictionary.py:56 — `max(..., key=frequency)` settles steno collisions
  by theory-1 order on a tie. For example, the reform pair `dégotés`/`dégottés` (both 0.0)
  keeps whichever row comes first in the lexicon. It is order-dependent in the same way as
  Lemma-Homophone Marking (S4)'s tie. Confidence: high; impact: low.
- util/export_practice_sentences.py:158 — The drill-item gate depends on `practice-words.json`
  from a separate recompute (see S5.8). Confidence: medium; impact: low.

## Dead-code observations
- util/_theoryio.py:42 `loadFirstTheory` has one caller left
  (`build_phase_p_realization.py:44`); `loadFinalTheory` :48 has one caller (S5.3). Both are
  thin wrappers and could be folded into `loadFirstAndFinalTheory` during the refactor.
  They are still live.
- No unreachable exporter code was found.

## Doc drift
- util/export_plover_dictionary.py:12-14 and util/export_practice_words.py:13-15 say
  collisions remain for "one word >10x rarer than the other". They do not: R4 (the
  frequency-ratio rule) *marks* the rarer word. The collisions that remain are homographs,
  reform doublets, same-`lemmeGramCat` residuals (Lemma-Homophone Marking (S4).5 notes) and
  alternate shadowing (S4.14).
- util/export_practice_words.py:4-6 says records are deduplicated "on `ortho`… keeping the
  highest-frequency one". The code keys by (ortho, steno) (:225) and merges labels.
- util/_theoryio.py:1-4 says it was factored out of `build_phase_p_realization.py`, which
  "duplicated this exact block". That script now uses only `loadFirstTheory`.
- util/export_keyboard_layout.py:15-17 calls the Phase P report "optional". Without it the
  legend is silently empty, and LEXICON_RECOMPUTE_PIPELINE.md calls the same file a
  "reference artifact" (already in the skeleton).
- The "run dictionary.py once first to generate it" message for `starboard3h.json` appears at
  export_plover_dictionary.py:38, export_plover_system.py:41, export_keyboard_layout.py:151,
  export_practice_words.py:216, export_practice_sentences.py:153 and export_definitions.py:49.
  `dictionary.py` never writes that file (already in the skeleton).
