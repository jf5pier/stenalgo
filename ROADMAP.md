# Stenalgo Roadmap — From Phoneme Layout to a Complete, Learnable French Steno Theory

*Merges `ROADMAP.md` (2026-09-14, code audit + phase plan) and `ROADMAP_REVIEW.md`
(2026-09-15, external review + prior art). Supersedes both — the phase numbers below are a
resequencing, not an addition; nothing in this document depends on `Phase N` meaning the same
thing it did in the original roadmap.*

## Context

The phoneme→key layer is solved: `starboard3h.json` is a working, committed phoneme-to-key
mapping. What is not solved is turning that into a complete theory — every word in the lexicon
resolving to one unique, learnable stroke. Two homophone problems stand in the way, and as of
2026-09-15 they are understood to be different problems needing different mechanisms, not one
mechanism applied twice:

- **Same-lemma homophones** — inflected forms of one lemma (dors/dort, mange/manges). This is
  a *conjugation* problem: resolved with meaningful phoneme-key chords, not the reserved keys.
- **Lemma-homophones** — words whose lemmas differ but that sound alike (ver/vert/verre/vers/
  vair). This is a *spelling* problem: resolved with the two guaranteed reserved keys, `*`/`#`.

This inverts what the current code does (`satOptimizeDiscriminator`/
`assignDiscriminatorKeypresses` today spend the reserved keys on same-lemma features). The
inversion is deliberate — see [Design decisions](#design-decisions) — and fits a constraint
only identified on 2026-09-15: of the Starboard's 4 reserved keys, only 2 (`*`, `#`) are
guaranteed to stay available long-term.

A third, smaller problem is new to this document: **prefix formation** (re-, dé-, co-…), which
has no code and no roadmap slot yet.

## Terminology

**"Lemma-homophones"** (this document's term) = a set of homophone words whose **lemmas
differ** — ver/vert/verre/vers/vair. This is the cross-lemma case below.

Do not confuse this with **same-lemma homophones** (inflected forms of *one* lemma) — a
separate problem, solved by a separate mechanism (conjugation chords, not reserved keys).

## Current state, grounded in the code (audit)

**Phoneme layer**
- `Starboard` (`src/keyboard.py`): 26 keys, 4 reserved (`[0,1,10,15]`), 22 allowed for
  onset(8)/nucleus(4)/coda(10) phonemes.
- `cpsatsolver.py::optimizeKeyboard` is a real, well-specified CP-SAT model: minimizes
  ambiguity (weight 30000, dominant term), phoneme order-violation (weight 500), and
  frequency-weighted ergonomic stroke cost (weight 1). **The call to it is commented out** — the
  live pipeline just loads the static `starboard3h.json` instead of re-solving. No unit tests
  exist for this solver or its ambiguity math, and there is no record in-repo of exactly how/when
  `starboard3h.json` was generated.

**Theory building (today)**
- `Dictionary.buildTheory` groups words into homophone clusters **by the stroke sequence their
  phonology resolves to** under the current keyboard. `theory.tsv` (untracked) is the raw,
  unresolved table this produces: stroke → comma-joined list of homophone orthographies. It
  does not yet encode any special-key disambiguation — this is "theory 1."

**Same-lemma homophones ("theory 2," in progress)**
- `extractDiscriminatingFeatures` → `greedyOptimizeDiscriminator` (`src/greedyoptimizer.py`)
  split homophone clusters by `lemmeGramCat` (lemma **+** grammatical category, deliberate —
  see the cross-category gap below) and greedily assign a discriminating `WordFeature` to each
  word in a >1 sub-group. Output: `augmentedTheory: dict[tuple[WordFeature,...],
  list[tuple[Word,...]]]`.
- Two mechanisms exist to turn those abstract features into physical special-key strokes, and
  only one is wired in:
  - **`satOptimizeDiscriminator`** (`src/satoptimizer.py`) — CP-SAT graph coloring, computes
    the minimum number of abstract key-indices needed for zero conflicts (currently **10**, up
    from 8 as the lexicon grew). **Active pipeline step**, but its output is an abstract color
    index — it never produces a physical `Stroke`.
  - **`assignDiscriminatorKeypresses`** (`src/greedyoptimizer.py`) — greedy, *does* produce
    physical strokes on the 4 reserved keys, using a hand-authored `FEATURE_PRIORITY` table
    (French markedness) and a `_consistencyScore`. Fully implemented and unit-tested (12 tests),
    but **orphaned** — not called from `dictionary.py` (see `todo.md`). **It predates several
    later changes** (the lexicon's growth from 8 to 10 abstract colors, and now the 2026-09-15
    reserved-key redesign below) — its purpose and whether it's still the right mechanism for
    anything need revisiting rather than assumed, see Phase 2.
  - Nothing today bridges the two. The computed `augmentedTheory`/color assignment is only
    ever printed to the console — no file captures a resolved theory.
  - **This gap is largely resolved by the 2026-09-15 design decision below**: same-lemma
    discrimination moves off the reserved keys entirely and onto phoneme-key chords, which
    changes what "bridging" even means here — see Phase 2.

**Cross-grammatical-category clash (real, unhandled)**
- Grouping by `lemmeGramCat` means a lemma with two readings (e.g. "aller" verb vs. noun) is
  split into separate groups *before* any collision check runs. If each reading's sub-group has
  only 1 word, neither trips the `len > 1` discrimination trigger, so two mutually-homophonous,
  differently-spelled readings of the same lemma can pass through undiscriminated. Found and
  fixed once in the diagnostic table, not in the discrimination logic itself.

**Known, already-scoped bug affecting special-key count**
- Per `todo.md`: `Word.getFeatures()` offers both a bare feature (`"p"`) and a gender-qualified
  one (`"f_p"`/`"m_p"`) for the same distinction; the greedy selector picks by lexicon-wide
  popularity rather than reusability, sometimes costing a whole extra special key. Explicitly
  deferred, scope with the user first.

**Lemma-homophones (cross-lemma, don't share a lemma at all)**
- No code addresses this yet — only an aspirational README note about an extra phoneme or a
  `*`-style key.

**Conjugation tables / dictionary densification**
- `src/verbparadigm.py` / `src/nomAdjParadigm.py` already do real paradigm-table work
  (Verbiste-derived templates, learned per-suffix-class transforms, including transforming the
  phonology field itself) — but only to fill gaps in the *source lexicon*
  (`LexiqueSynthetic.tsv`) before theory-building, not to collapse per-form dictionary entries
  into one entry + a lookup at theory time.
- **`plover-python-dictionary`**: Lapwing's dictionaries run on this Plover plugin — i.e. Plover
  already supports *programmatic*, runtime-lookup dictionaries. The Plover target therefore
  need not be a flat precomputed dict; a runtime rule-engine dictionary could serve both the
  Plover target and the Javelin target from one engine design (reshapes Phase 6, formerly
  "shared paradigm-table representation," toward "one rule engine, two hosts").

**Compositional phonology generation (général + m_p → généraux)**
- Not built yet. `nomAdjParadigm.py`'s `deriveNomAdjEndingTables`/`generateMissingForm` already
  do "learn a phonology-transforming suffix rule from donor lemmas, synthesize a new form," but
  offline, writing a permanent lexicon row — not live at steno-input time.

**Prefix formation**
- Not built. French has limited prefix agglutination (re-, dé-, co-…); flat-enumerating every
  prefixed form × every conjugated form would make the dictionary very large. Same machinery
  family as conjugation (`verbparadigm.py`/`nomAdjParadigm.py` are the mirror-image problem).

**Personal theory / briefs**
- No trace anywhere in code or docs. Genuinely open — see Phase 5 and Phase 7, two different
  brief mechanisms that should not be conflated.

## Design decisions

Recorded here so they survive a `/clear` and aren't re-litigated each session.

1. **Special-key budget is 2 keys, not 4.** Of the Starboard's 4 reserved keys, only `*` and
   `#` are guaranteed to remain available long-term (one more than a traditional Ireland layout
   effectively offers, whose only free non-phoneme key is `*` — its `#` is the number bar). The
   other two reserved keys exist today but cannot be counted on.
2. **`*`/`#` serve lemma-homophones only.** 2 keys → 4 modifier values (no stroke, `*`, `#`,
   `*#`). No stroke goes to the most frequent lemma in a cluster, so up to **4 lemmas per
   cluster** are differentiable this way — the star-key "second-most-frequent" idea, extended
   to `#` and `*#`. Clusters with ≥5 members (ver/vert/verre/vers/vair…) need sequential `*`/`#`
   chords or curated exceptions; Phase 0 measures how much frequency mass this actually affects.
   These keys are explicitly **not** spent on conjugation or prefixes.
3. **Same-lemma homophones are a conjugation problem, solved with phoneme-key chords**, chosen
   so they (a) create no new stroke conflicts and (b) are *meaningful* — the phoneme is
   associable with the conjugation case or an orthographic feature (2nd person singular's usual
   final **-s** vs. 3rd person singular's final **-t**/**-d**: dors/dort, vends/vend — the chord
   carries the orthographically-marked, spoken-silent consonant). This matches how mature
   theories work: English fuses orthographic suffix keys into the final chord (`-S`, `-G`);
   LaSalle-lineage French theories use orthographic final-consonant markers.
4. **The `"p"`/`"f_p"`/`"m_p"` fusion bug is deferred**, not a blocker for any phase below.
5. **Prefix formation is a confirmed new goal**, compositional rather than flat-enumerated:
   prefix strokes live on phoneme-layer keys (pseudo-phonemes), consuming phoneme-key budget —
   paired with Phase 6 (densification).
6. **Dual-target architecture confirmed**: a large precomputed static dictionary for Plover, and
   a small dictionary + runtime rule engine for a microcontroller build modeled on **Javelin**.
   Both consume the same underlying paradigm-table data. `plover-python-dictionary` (above)
   means this may collapse further into one shared runtime rule engine behind two hosts, rather
   than a flat exporter + a separate runtime engine — an open question, not yet decided.

## Roadmap

Resequenced 2026-09-15 to measure before committing to physical assignment, and to stop
sequencing by implementation dependency alone once measured user value points elsewhere.

### Phase 0 — Measure: ambiguity checker + cluster statistics
Goal: know where the frequency-weighted ambiguity actually lives before building physical
assignment for either homophone track.
- Write the end-to-end zero-ambiguity checker now, rather than treating it as a Phase 1/2
  deliverable. It is the instrument that defines "done" for both. `buildTheory` already
  clusters words by resolved stroke, so dumping the distribution of clusters by (same-lemma vs
  lemma-homophone, cluster size, frequency mass) is hours of work, not a new subsystem.
- Two numbers this unblocks directly: how much frequency mass sits in lemma-homophone clusters
  with ≥5 members (beyond the `*`/`#` budget, Phase 4), and how often meaning-anchor candidate
  chords collide with real outlines (how constrained the conjugation track actually is, Phase
  2).
- Run the checker against the `aller` NOM/VER case (documented in `dictionary.py`) — expect it
  to fail there first.

**Progress (2026-09-17/18)**: `src/ambiguitychecker.py` (this phase's checker) now exists and
was used to manually walk every n>=5 lemma-homophone overflow cluster by hand with the user.
Result: `resources/ambiguityIgnoreList.tsv`, a curated, reason-tagged (`archaic`/
`anglicism_loan`/`unpopular_spelling`/`sociolect`/`data_artifact`) list of 79 lemmas to exclude
from the ambiguity *count* — too rare/foreign/archaic to ever realistically need their own
discriminator symbol. Loaded via `loadIgnoredLemmas()`, applied as a filter in `classifyTheory`.
Effect: n>=5 overflow clusters 58 → 20 (max cluster size 8 → 7). This is effectively a
hand-built first draft of Phase 4 building block 3 ("curated exception list for whatever
remains irreducible") arrived at from the measurement side rather than the assignment side —
worth reusing there rather than rebuilding. Also surfaced several real Lexique383 data-quality
bugs along the way (comma-joined dual-lemma `"bail,bau"`, a mispronounced `baud`, a handful of
suspected mistagged-verb "ghost lemmas" like `pars`/`sert`) — see `todo.md` for the open items,
none fixed yet.

### Phase 1 — Fix the cross-grammatical-category clash
Goal: close the gap where two different-category readings of the same lemma can be mutually
homophonous, differently spelled, and go undiscriminated.
- Extend the collision check to look across `lemmeGramCat` groups sharing the same lemma (or
  more generally, across all groups landing in the same phonetic-stroke cluster), not just
  within each group.
- Add a regression test using the `aller` NOM/VER case, or a synthetic minimal example.
- This is small once Phase 0's checker exists — it's the thing the checker will catch first.

### Phase 2 — Conjugation-chord assignment + lemma-homophone rank assignment
Goal: produce theory 2 — every word resolves to a unique stroke — with the two homophone
problems resolved by their own mechanism, then persist it.
- **Conjugation track**: assign each same-lemma feature a phoneme-key chord drawn from its
  meaning-anchor candidates (2ps → final `/s/`, 3ps → `/t|d/`, …). Hard constraint: the
  resulting outline collides with no other word's outline (checkable over the same stroke
  clustering `buildTheory` already computes). Objective: frequency-weighted `getStrokeCost` +
  markedness (`FEATURE_PRIORITY`) for which form gets the bare outline.
  `assignDiscriminatorKeypresses` is a candidate greedy prototype/baseline, but per the audit
  above it predates the lexicon's growth and the reserved-key redesign — confirm it still fits
  this track (or rewrite it) before leaning on it as a warm start. `_colorFeatures`
  (`src/satoptimizer.py`) demotes to a feasibility monitor rather than the driving mechanism.
- **Lemma-homophone track**: assign each lemma in a cluster one of the 4 `*`/`#` values by
  frequency rank (most frequent = no stroke). Small — mostly a convention plus an exceptions
  path for clusters of >4, informed by Phase 0's numbers.
- Both tracks are CP-SAT-shaped and can share one model with common conflict variables, though
  they no longer share a reserved-key budget.
- Persist the result: a real "theory 2" output file (replacing or supplementing `theory.tsv`)
  with one row per word, its phonetic stroke, and its resolved special-key/chord stroke.
- Gate: Phase 0's checker goes green against the persisted output.

### Phase 3 — Re-validate and version the phoneme layer
Goal: confirm `starboard3h.json` is still optimal against the current lexicon, and decide a
freeze/versioning policy before the theory reaches real learners.
- Re-enable and test `cpsatsolver.py::optimizeKeyboard` enough to confirm whether re-solving
  against today's lexicon changes the layout at all.
- Persist solver parameters + a lexicon hash next to the output going forward, so the layout is
  reproducible — there is currently no record of how `starboard3h.json` was generated.
- Decide when to freeze the phoneme layout and the special-key physical layout for learnability
  — a shifting layout is a real cost, distinct from "can we still improve it," and matters more
  now that a microcontroller target is confirmed (firmware/hardware users tolerate drift even
  less than a Plover dictionary file does).
- Decide brief scope (Phase 5) before freezing — briefs interact with the stroke budget.
- Watch special-key headroom: 4 reserved keys give 16 possible strokes; the lexicon already grew
  from needing 8 to 10 abstract keys for the conjugation track alone. Worth a threshold/
  monitoring approach now.

### Phase 4 — Lemma-homophone strategy at scale
Goal: a full strategy for homophones that don't share a lemma, informed by Phase 0's measured
frequency mass rather than assumed.
**Prioritized building blocks** — star-key/rank marker and spelling-rule clusters first;
grammatical-category auto-split and a curated exception list are lower priority, likely still
needed for whatever the other two can't cover:
1. The `*`/`#` rank marker from Phase 2, generalized to the full lemma-homophone population.
2. Generalized spelling-rule-based key clusters (groups of words sharing a silent-letter/ending
   pattern) for structured cases.
3. *(lower priority, likely still needed for leftovers)* grammatical category as a free
   discriminator (`GramCat` is already a `WordFeature` candidate), and a curated manual
   exception list for whatever remains irreducible.

If Phase 0 shows lemma-homophony carries most of the frequency-weighted ambiguity, this phase is
the real prize and Phases 1–2's payoff is smaller than their earlier position in the roadmap
suggested — that's the point of measuring first.

### Phase 5 — Theory-level briefs
Goal: automatic, corpus-driven shortcuts for the most frequent words and 2–3 word phrases —
distinct from Phase 7's user-personal briefs.
- Every mature theory hand-tunes a brief table; it is the single biggest WPM and learnability
  lever (English Plover/Lapwing briefs; Pluvier and Regenpfeifer both layer manual briefs over
  generated outlines). Leaving this to user-personal briefs alone delegates theory design onto
  individual learners.
- This project already has the assets for automatic briefing: corpus frequencies + working
  conflict machinery. Assign the shortest conflict-free chords to the top-N words and frequent
  short phrases.
- Interacts with the Phase 3 layout freeze and the stroke budget — decide scope before freezing.

### Phase 6 — Dictionary densification: conjugation tables, compositional generation, prefixes
Goal: one entry per homophone-per-lemma pointing at a shared conjugation/paradigm table, plus
the ability to compose a base word's phonology + a grammatical-feature key into an
unrelated-sounding inflected form (généraux from général + m_p) — and the mirror-image problem,
compositional prefixes (re-, dé-, co-…), rather than enumerating every prefixed × conjugated
form as flat entries.
- **Dual-target architecture** (decisions §6): a large static Plover dictionary, and a small
  dictionary + runtime rule engine for a microcontroller build modeled on Javelin. Both consume
  the same underlying paradigm-table data — design that shared representation first, then build
  the two exporters/consumers on top of it.
  - **Plover target**: extend today's offline gap-filling approach
    (`nomAdjParadigm.py`/`verbparadigm.py`-style learned transforms) to precompute every
    compositional entry directly into the dictionary — or, per `plover-python-dictionary`,
    reuse the same runtime rule engine as the microcontroller target instead of a flat exporter.
  - **Microcontroller/Javelin-style target**: paradigm/transform tables exposed as a compact,
    on-device-queryable ruleset (base form + feature → derived form at input time). Study
    Javelin's own dictionary/rule format as prior art before designing this.
- Prefixes belong here: same machinery family as conjugation tables. On the Plover target,
  compositional prefixes either still enumerate every prefixed form (the size cost this goal
  exists to avoid) or use `plover-python-dictionary` to compose at lookup time — pushing toward
  one shared rule engine rather than two independent exporters.
- Open: the prefix inventory to support, and whether prefixed forms interact with lemma-
  homophone spelling clusters (Phase 4).

### Phase 7 — Personal theory layer
Goal: user-added shortcuts/briefs for common words and 2-3 word expressions, layered on top of
the base theory (distinct from Phase 5's automatic, corpus-driven briefs).
- Needs its own conflict-resolution against the base theory's stroke space (can't silently
  collide with an existing word's stroke).
- Not started; no existing code to build on here.

### Ongoing — testing & documentation hygiene
- No tests currently cover `cpsatsolver.py`/`cpsatoptimizer.py` ambiguity math. Add as each
  phase lands, not deferred to the end.
- `README.md`'s roadmap checklist predates and only partially reflects the current
  `greedyoptimizer.py`/`satoptimizer.py`/`verbparadigm.py` machinery — worth a pass to reconcile
  once Phases 0–2 land, so the README stops undercounting what's already built.

## Prior art (researched 2026-09-15)

- **[Pluvier](https://github.com/Vermoot/Pluvier)** — the closest analog: a French,
  "real-time friendly, conflict-free" theory for Plover, dictionary programmatically generated
  from Lexique (same corpus family as this project), rules derived from the Québec
  LaSalle/TAO method ([blog post](http://plover.stenoknight.com/2021/11/pluvier-french-dictionary-generator.html)),
  Ireland layout, manual briefs layered on top of generated outlines. Work-in-progress (~80
  commits, no releases). Its homophone stance is "distinct outline per word via rules + briefs,"
  with frequency-prioritized disambiguation still open — this project's core problem appears
  unsolved there too. Its translated LaSalle rule docs are mineable; "optimization-first, custom
  ergonomics, systematic feature-based disambiguation on a 26-key board" is this project's
  differentiation — no community project found uses constraint solvers or optimizes finger
  strain.
- **[Lapwing theory](https://plover.wiki/index.php/Lapwing_theory)** (Aerick, 2022) — the model
  for "systematic conflict-free theory as a maintained artifact with pedagogy"
  ([Lapwing for Beginners](https://lapwing.aerick.ca/lapwing-for-beginners/),
  [dictionaries](https://github.com/aerickt/steno-dictionaries)); exists precisely because
  Plover theory had conflicts. Its [Javelin appendix](https://lapwing.aerick.ca/Appendix-C.html)
  runs Lapwing on embedded firmware — the dual-target pattern (one dictionary, Plover *and*
  onboard) already proven in English.
- **[Javelin](https://github.com/jthlim/javelin-steno)** (Jeffrey Lim) — embedded steno engine
  firmware with onboard dictionaries (standalone, no host Plover), two dictionary formats, a
  firmware builder; runs on Uni v4/Polyglot/Asterisk
  ([overview](https://stenokeyboards.com/blogs/posts/embedded-steno),
  [wiki](https://plover.wiki/index.php/Javelin)). This is the prior art Phase 6 should be
  designed against.
- **[Regenpfeifer](https://github.com/mkrnr/plover_regenpfeifer)** — same genre for German:
  programmatically generated, rule-based dictionary for Plover; the author's
  [design writeup](https://stenoblog.com/working-on-a-german-steno-theory/) covers rule-based
  word→stroke conversion at theory scale.
- **[Plover discussion #1372](https://github.com/openstenoproject/plover/discussions/1372)** —
  codifying English Plover-theory rules as a script;
  [Di's steno-dictionaries](https://github.com/didoesdigital/steno-dictionaries) are the
  maintained-artifact + tooling precedent (Typey Type).
- Historical context: **Grandjean** (legacy French stenotype, available as a Plover plugin) is
  the anti-pattern — not conflict-free, needs host-side homonym disambiguation software.
  **Michela** (Italian parliamentary machine steno) is the existence proof that a fully
  systematic national-language machine theory supports professional realtime. The
  [steno layouts page](https://plover.wiki/index.php/Steno_layouts_and_supported_languages)
  catalogs the language-plugin landscape; Plover's
  [Designing Steno Systems](https://plover.readthedocs.io/en/latest/system_dev.html) gives the
  layout/theory/dictionary decomposition.
- **Academic literature on automated steno-theory generation: essentially none found** (nearest
  formal work is HCI chorded-keyboard assignment research). The niche is open.

## Open questions

1. **Javelin as prior art** — is there a specific fork/version of Javelin in mind, or specific
   features from it already known to be worth mirroring (rule syntax, on-device conjugation
   table storage, memory constraints)?
2. **Reserved-key set flexibility** — `_reservedKeys` is a hardcoded `Starboard` class
   attribute, though the assignment algorithms already read it dynamically and are tested
   against custom sets. Make it user-configurable now, or revisit once the feature set
   stabilizes?
3. **Layout freeze** — is there a target point (e.g. "once Phase 0–2 land") to lock the phoneme
   + special-key physical layout for real learners, separate from continuing lexicon curation
   indefinitely?
4. **`theory.tsv` fate** — should the new resolved theory output replace `theory.tsv`, or live
   alongside it as a raw/debug view?
5. **Conjugation modifier form** — fused into the word's final chord (English `-S`/`-G` style —
   faster, but the base chord must have that key free in its zone) vs. a separate modifier
   stroke (slower, cleaner conflict model)?
6. **The anchor table** — which phoneme/orthographic anchor per feature (2ps → `/s/`, 3ps →
   `/t|d/`; do nominal plurals also take `/s/`? feminine — the silent final -e has no phoneme,
   is schwa `@` the anchor?).
7. **Lemma-homophone clusters with >4 members** — sequential `*`/`#` chords vs. curated
   exceptions, once Phase 0 measures the frequency mass at stake.
8. **Where prefix strokes live** (phoneme-layer pseudo-phonemes?) and their cost against the
   22-key phoneme budget.
9. **One shared runtime rule engine** (Plover python-dict + Javelin) vs. two exporters of a
   shared table format, for Phase 6.

## Verification approach (once implementation starts on any phase)

- `pytest src/test/` must stay green throughout; add targeted tests per phase as noted above.
- Phase 0's end-to-end zero-ambiguity checker is the meaningful verification for Phases 1 and 2
  — run `python dictionary.py` and confirm the resolved theory has no remaining stroke
  collisions, rather than treating this check as a Phase 2-only deliverable.
- For Phase 3, compare `optimizeKeyboard()`'s fresh solve against `starboard3h.json` to quantify
  drift before deciding on a refresh/freeze policy.
