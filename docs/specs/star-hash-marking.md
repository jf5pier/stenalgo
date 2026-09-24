# Spec: star/hash marking

Scope: Different-Lemma or Grammatical-Category Disambiguation (S7). It decides which
member of a lemma-homophone group is typed plainly and which get a star/hash mark (`*`, `#`,
`*#`, or an escalated code), and how that mark becomes physical keys.

The code is the source of truth: `src/ambiguitychecker.py` (`decideStarHashMark` →
`composeReservedKeyStrokes`) and `GRAMCAT_PRIORITY` in `src/greedyoptimizer.py`. For the
per-call walkthrough (line numbers, data volumes, dataset state before and after each call),
see [PIPELINE.md §Different-Lemma or Grammatical-Category Disambiguation (S7)](../PIPELINE.md#different-lemma-or-grammatical-category-disambiguation-s7).
Terms are defined in [GLOSSARY.md](../GLOSSARY.md).

## 1. The problem

Discriminating-Feature Stroke Realization (Realization Phase) separates only Words that share
a `lemmeGramCat`. Words from different lemmas or grammatical categories can still end with
the same final induced strokes: `ver`/`vert`/`verre`/`vers`/`vair`, `à`/`a`/`ah`/`ha`, and
same-lemma category clashes such as `appel` NOM / `appelle` VER.

A **lemma-homophone group** is a set of Words that share one canonical final induced
Strokes and span **≥ 2 `lemmeGramCat`s and ≥ 2 spellings** (`groupHomophonesByReservedStroke`).
Groups with one `lemmeGramCat` belong to the Realization Phase. All-homograph groups type
the same text anyway, so they are dropped.

Constraints the design must meet:

- **Two reserved keys only.** Of the Starboard's four reserved keys, only `*` (key 10,
  `STAR_KEY`) and `#` (key 15, `HASH_KEY`) are guaranteed to stay available. Keys 0 and 1
  (left pinky) are held for a possible third mark and never used. These keys are spent only
  on lemma-homophones, never on conjugation features or prefixes.
- **A static, per-word choice.** The writer cannot decide at write time which reading was
  meant, so every Word's mark is a fixed convention, not a runtime probability.
- **Learnable.** A handful of memorable rules, not a per-lemma lookup table.

## 2. Cost model: why these rules

The rules were chosen by **regret minimization**, not by classifying homophones. For a
clashing pair A/B with film frequencies `fA` and `fB` (`Word.frequency` is the
film-subtitle frequency):

- the cost of marking A is `fA`, one extra key per occurrence;
- the unreachable optimum is `min(fA, fB)`, which marks whichever word is rarer on its own
  but needs one memorized decision per pair;
- the **gap** is `cost − optimum` — the **regret** of the chosen assignment; "regret" and
  "gap" name the same quantity — and **gap%** is `gap / (fA + fB)` summed over all pairs.

A category rule (always mark category X against Y) costs some gap in return for being
memorable. The adopted design lands at about **0.5 % gap** from the per-pair optimum (0.526 %
at design time, 0.499 % on a fresh rebuild, 2026-09-20).

**Why 10×.** Pairs whose frequency ratio is ≥ 10 are pulled out of the category fit and
resolved per pair: the rarer word is marked, and the frequency gap is its own mnemonic. At
10× they hold 88.8 % of the clashing volume. Of the thresholds tested (10×, 30×, 100×), 10×
gives both the lowest total gap% and the **only** residual that fits one linear category
order. At 30× and 100×, borderline deverbal `-é(s)`/`-ée(s)` pairs come back into the
residual and form a cycle (NOM > ADJ > VER > NOM).

**Why this category order.** On the residual left after the 10× cut, the single linear order
`ADV > PRO:pos > NOM > VER > ADJ > ADJ:pos` (canonical → marked) matches every observed
category pair's regret-optimal direction.

## 3. The pairwise rule stack — `decideStarHashMark(a, b)`

The first rule that matches decides. "Mark X" means X is the less canonical Word and gets the
star/hash mark. Rule ids R1–R7 follow code order and are always cited with the rule's name.

| # | Rule | Condition | Outcome |
|---|---|---|---|
| R1 | homograph exemption | `a.ortho == b.ortho` | no mark: same typed output |
| R2 | reform-doublet exemption | `{a.lemme, b.lemme}` is a 1990-reform pair | no mark: one word, two spellings |
| R3 | per-pair override | `MARKING_OVERRIDES[{a.ortho, b.ortho}]` exists | mark the stored spelling |
| R4 | frequency-ratio rule | `max(f)/min(f) ≥ 10` (`RATIO_EXEMPTION_THRESHOLD`; a zero frequency counts as infinite ratio) | mark the rarer |
| R5 | same-category rule | `a.gramCat == b.gramCat` (exact enum: `ADJ` ≠ `ADJ:pos`) | mark the rarer |
| R6 | category-priority rule | both categories are in `GRAMCAT_PRIORITY` | mark the lower priority |
| R7 | frequency fallback | at least one category is missing from the table | mark the rarer |

Details:

- **Doublet pairs** come from `resources/reform1990.tsv` (`loadReform1990DoubletPairs`): every
  row except those flagged `isException=True` (such as `fût`/`fut` and `croît`/`croit`, which
  clash with an unrelated word). The pairs are **lemma** spellings, compared against
  `Word.lemme`. A doublet visible only at the verb-lemma level (`boursoufler`/`boursouffler`)
  therefore needs an override for its adjective forms (`boursouflée`/`boursoufflée`).
- **`GRAMCAT_PRIORITY`** (higher = more canonical): `ADV` 50, `PRO:pos` 40, `NOM` 30, `VER` 20,
  `ADJ` 10, `ADJ:pos` 0. Every other category (`PRE`, `ONO`, `ART:def`, `PRO:per`, `AUX`,
  `CON`, …) falls to the frequency fallback (R7), even when the other side is `NOM`.
- **Overrides** (`MARKING_OVERRIDES`, keyed by the unordered pair of spellings, value = the
  spelling that gets the mark) cover the pairs where R4–R7 still leave regret > 0 against
  the per-pair optimum. The entries are mostly deverbal masculine/feminine plurals
  (`portés`/**`portées`**) and a few near-homographs (`sales`/**`salles`**,
  `new`/**`news`**). The list is provisional: it was built from 2026-09-20 data and never
  regenerated from one canonical run. The current list lives in the code.
- **Ties.** In R4, R5 and R7, equal frequencies mark the first argument (`fA <= fB`).
- R4 is called a "ratio exemption" in the code: it exempts the pair from the category rules
  (R5–R6), **not** from marking.

## 4. From pairs to a whole group — ranking and codes

`assignStarHashMarks`, for one lemma-homophone group:

1. **Homograph merge.** Members with the same `ortho` collapse into one entry. Its
   representative is the most frequent member.
2. **Doublet merge.** Entries whose representatives' lemmas form a reform-doublet pair are
   merged (union-find). Each merged set is represented by its most frequent Word.
3. **Rank** the representatives, most canonical first: a sort with `decideStarHashMark` as the
   comparator (`rankHomophoneCluster`, `_starHashCompare`).
4. **Codes by rank** (`assignStarHashCombos`):

   | rank | 0 | 1 | 2 | 3 | 4 | 5 | … |
   |---|---|---|---|---|---|---|---|
   | code | `()` | `*` | `#` | `*#` | `*# *#` | `*# *# *#` | one more `*#` per rank |

   The first four are the **four-code budget** (none, `*`, `#`, both — every combination
   of the two reserved mark keys). Past it come
   **escalated codes**: rank r ≥ 4 is `*#` repeated r − 2 times. There is no upper bound.
5. Every Word of a merged set gets its representative's code, so homographs and doublets
   share one code. A group made only of doublets ends with a single code, `()`, and those
   Words keep one shared stroke by design.

The **canonical member** (rank 0, code `()`) keeps its final induced strokes unchanged.

## 5. Physical strokes

`starHashCodeToStrokes` maps `*` → key 10, `#` → key 15 and `*#` → keys 10 and 15 in one
stroke. `composeReservedKeyStrokes` then combines these with the Word's final induced strokes:

- The **first** symbol is pressed together with the word's **last phoneme stroke** (the last
  of its phonetic-theory base strokes), not with a feature discriminating stroke that follows it.
  This is a **merged star/hash mark**.
- Each further symbol of an escalated code becomes its own trailing **\*/# marker stroke**.

Formally, with `s` = final induced strokes, `x` = star/hash strokes and `last` = the Word's
base stroke count − 1:
`s[:last] + (s[last] ∪ x[0],) + s[last+1:] + x[1:]`.

`util/_stenorender.py` writes these the way Plover does: `p*a/-s`, `swa#`, `*ae#/*#`.

**Collision safety.** The Realization Phase picks only coda phoneme keys, and keys 10 and 15
are never in `Keyboard.allowedKeys`. Removing the reserved keys, and the reserved-only
trailing strokes, gives back the final induced strokes exactly. So two groups cannot collide
after composition, and inside a group every code is distinct. This covers **primary** strokes
only: alternate entries (Alternate entry strokes, S6.Realization.7) carry no star/hash mark
(see Known gaps).

## 6. Worked examples

Plover strokes are from `plover_stenalgo_dictionary.json`, 2026-09-22 data.

1. **Category-priority rule (R6) beats frequency.** `appel` NOM (80.9) vs `appelle` VER
   (485.8): the ratio is 6.0 < 10 and the categories differ, NOM 30 > VER 20, so `appelle` is
   marked even though it is 6× more frequent. `appel` → `a/piel`, `appelle` → `a/p*iel`.
2. **Homograph merge, frequency-ratio rule (R4) and frequency fallback (R7).** Group /a/:
   `à` PRE 12,190; `a` (AUX 6,351, also VER and NOM, one entry after the homograph merge);
   `ah` ONO 577; `ha` ONO/NOM 22. `à` vs `a`: ratio 1.9, and PRE is not in the table, so the
   frequency fallback (R7) marks `a`. `ah` vs `a`: ratio 11, so the frequency-ratio rule (R4)
   marks `ah`. `ha` loses to every other entry by R4. Result: `à` `a`, `a` `*a`, `ah` `a#`,
   `ha` `*a#`.
3. **Five readings, one escalation.** Group /vɛʁ/: `vers` (PRE/NOM) `()` → `vieR`; `verre`
   `*` → `v*ieR`; `ver` `#` → `vie#R`; `vert` `*#` → `v*ie#R`; `vair` `*# *#` → `v*ie#R/*#`.
   Inflected forms whose feature discriminating stroke follows keep the merged mark on the
   phoneme stroke: `verts` → `+10/17`, `vairs` → `+15/17` in `disambiguated_theory.tsv`.
4. **Deep escalation.** Group /o/ (11 Words, 8 representatives): `au` `ae`, `oh` `*ae`,
   `aux` `ae#`, `eau` `*ae#`, `haut` `*ae#/*#`, `ho` `*ae#/*#/*#`, `ô` `*ae#/*#/*#/*#`,
   `aulx` `*ae#/*#/*#/*#/*#`.
5. **Doublet.** `bizut` (2.05) and `bizuths` (0.0) have lemmas `bizut`/`bizuth`, a reform
   pair. They are merged and both get `()`: one stroke, and Plover keeps `bizut`.
6. **Merged mark before a feature discriminating stroke.** `pâts` → `p*a/-s`: the `*` rides on
   the phoneme stroke `pa`, and `-s` is the feature discriminating stroke.

## 7. Invariants

- Inside a lemma-homophone group, every merged entry gets a distinct code. After composition,
  two members of one group share a primary stroke only if they are homographs or a doublet
  pair (21 doublet strokes stay shared by design).
- Removing keys 10 and 15 and the reserved-only strokes from a composed stroke gives back the
  final induced strokes exactly.
- Keys 0 and 1 are never emitted.
- Canonical members' strokes are unchanged from the Realization Phase output.

## 8. Known gaps (tracked in `TODO.md`, "Suspected bugs")

- **B5**: on equal frequency, R4, R5 and R7 mark the first argument, so the comparator is not
  antisymmetric and the result depends on input order (`pas`/`pâts`, both 0.0). Shuffling the
  input changes the marks in 619 of the 4,450 groups.
- **B25**: R4 and R6 can form a cycle (A < B by R6, B < C by R6, C < A by R4), which again
  makes the order depend on input. There are 0 such cycles among live representatives.
- **B26**: the doublet merge checks only the representatives' lemmas (0 live instances).
- **B4**: alternate entries carry no star/hash mark and can take another word's only stroke.
  9 spellings have no Plover entry as a result (`subits`/`subis`, `pais`/`paie`,
  `amplis`/`emplis`).
- **B1**: spelling twins (Words sharing a spelling and a `lemmeGramCat`) are not fully
  separated by the Realization Phase, and the one-`lemmeGramCat` filter keeps them out of this
  stage: 99 pairs in 98 strokes reach the disambiguated theory unmarked.

One design caveat without a bug number: bucket 2 (different-gramCat, same lemma) and
bucket 3 (cross-lemma) pairs are pooled through one physical marking mechanism
(`decideStarHashMark` treats both identically). That pooling was an implementation
convenience and was never explicitly re-confirmed as a design decision.
