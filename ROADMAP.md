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

## Status update (2026-09-21)

Follow-up to `RESUME_2026-09-21-collision-residual.md`'s open task (investigate the ~52-pair
non-exempt residual left in the `*`/`#`-marked lexicon). Root cause and fix, in three parts:

- **Root cause (found)**: `theory`'s raw `Strokes` tuples preserve per-phoneme insertion order
  and can repeat a key (one phoneme's dedicated key already covered by another phoneme's
  multi-key digraph in the same syllable) — fine for `strokesToString`'s human-readable
  rendering, but every collision-detection consumer (`groupHomophonesByReservedStroke`,
  `buildLemmaHomophoneGroups`) compared/hashed that raw tuple directly, while the actually
  *typed* stroke (`Starboard.strokesToRTFCRE`) is `sorted(set(stroke))` — order- and
  repeat-insensitive, since a stroke is a simultaneous chord. Pairs like `quatre`/`carte`
  (same keys, different phoneme order) or `ski`/`gui` (the `sk` cluster's keys happen to equal
  `g`'s 2-key digraph) were physically colliding but invisible to both the `*`/`#` grouping
  *and* Phase E's elicitation-cluster discovery, so they silently collided at render time,
  never reaching `decideStarHashMark` or the questionnaire at all.
- **Fix 1 (code)**: `src/keyboard.py` gained `canonicalizeStrokes()` (sort+dedupe per stroke);
  `groupHomophonesByReservedStroke` (`src/ambiguitychecker.py`) and `buildLemmaHomophoneGroups`
  (`src/elicitation.py`) now compare canonical strokes. `dictionary.py::buildTheory` and
  `strokesToString` are untouched — this only changes collision-detection identity, not stored
  data. Fixed ~46 cross-lemma pairs automatically (no new elicitation needed, `decideStarHashMark`
  is deterministic) and surfaced 82 previously-invisible same-lemma clusters needing new
  elicitation answers (small: 29, then 10, then 6 residual oppositions after the phonology
  fixes below removed the rest).
- **Fix 2 (phonology/syllabification exceptions, `src/word.py`)**: three of the surfaced
  clusters turned out to be genuine base-keyboard-layout ambiguities (a real phoneme silently
  swallowed by an adjacent digraph sharing one of its keys), not decideStarHashMark issues, and
  not fixable by *marking* at all in one case — same phenomenon, three shapes:
  - `fix_rdre_coda_syllable_break` — `-rdre` verbs (perdre, mordre, tordre, ...): infinitive's
    coda repeats /R/ onto one dedicated key (`perdre` = `p_E_R_d_R_#`), collapsing onto
    `perdent`/`perde`/`perdes` (single /R/). Splits the coda at the same point
    `perdez`/`perdons` already split at.
  - `fix_glide_low_vowel_syllable_break` — `-uer` verbs' passé-simple/participe-présent/
    subjonctif-imparfait forms (tua, tuant, continua, ...): /ɥ/'s 2-key digraph is a superset
    of bare /a/'s and /@/'s own keys, so `tua`/`tuant`/`continua`/`continuant`/... all
    collapsed onto each other. Splits the vowel into its own syllable.
  - `fix_ayer_conditionnel_onset_glide` — `-ayer` verbs' conditionnel 1p/2p (paieriez,
    paierions, essaieriez, ...): onset /R/ (one key) is a subset of onset /j/'s 2-key digraph,
    so `paieriez` collapsed onto `payer`/`payez`/... — verified via Wiktionnaire's IPA
    (`paieriez` [pɛʁje] genuinely has /ʁ/, `payez` [pɛje] doesn't: not a phonology bug in the
    data, a keyboard-layout one). A first attempt re-keyed the ending's /j/ as nucleus /i/+/e/
    instead of onset /j/, but Starboard's nucleus /i/+/e/ chord turned out to already be
    dedicated to the single phoneme /E/, so `paieriez` just collapsed onto `paierais`/
    `paierait`/`paieraient` instead — same bug, relocated. Settled on the same syllable-break
    approach as the other two instead. All three restricted to conjugated verb forms
    (`infoVerb is not None`) and/or the word's own final syllable, verified against the actual
    lexicon before implementing — an earlier unrestricted attempt at the `-uer` fix would have
    also split unrelated high-frequency words (`situation`, `persuader`, ...) that happen to
    contain the same phoneme shape mid-word with nothing colliding.
  - Recompute chain after these: `python dictionary.py` (~2.5 min, deletes and rebuilds
    `Dictionary.pickle`/`FirstTheory.pickle`) → `python -m src.elicitation` → re-answer any
    newly-surfaced oppositions → `python -m util.build_phase_p_realization`.
- **Fix 3 (elicitation)**: the `renvoyer` (infinitif/subjonctif-imparfait vs participle forms)
  and `-oyons`/`-oyions`-family clusters (`croyons`/`croyions`, `voyons`/`voyions`, ...,
  previously invisible for the same reason as fix 1) needed real new elicitation answers, not a
  phonology fix — answered directly by the user, no new questionnaire round needed for those.
- **Result**: non-exempt residual collision count **52 → 2**. Both remaining are unrelated to
  this fix: `tocard`/`toquard` (a genuine spelling-variant collision, pre-existing, out of
  scope) and `suffi`/`suffît` (same-lemma, phonology already identical before this session —
  a pre-existing elicitation gap, not a canonicalization artifact; flagged for a future
  session, not chased down here).
- **`tocard`/`toquard`**: added `toquard` (lemme-keyed, covers NOM+ADJ, singular+plural) to
  `resources/ambiguityIgnoreList.tsv` as `unpopular_spelling` (~10x rarer than `tocard`).
  Note this file is read only by `src/ambiguitychecker.py`'s own standalone `classifyTheory`
  report (`loadIgnoredLemmas`, called from that file's own `__main__` only) — verified via
  grep that `lexique.py`, `dictionary.py` and every `util/export_*.py` script never touch it.
  It stops the pair from being counted as an outstanding ambiguity in that report; it does
  **not** change the actual typed theory (`toquard` still physically collides with `tocard`
  in the real Plover dictionary — a genuine `*`/`#` mark would be needed for that).
- **Subjonctif imparfait removed from the corpus entirely (2026-09-21)**: the `suffi`/`suffît`
  investigation above led to auditing this tense more broadly — `src/elicitation.py` had
  already excluded it from ever getting a discriminator since 2026-09-19 (archaic/literary,
  "not worth a keypress"), but the words themselves were still in the lexicon, silently
  colliding with whatever else shared their stroke (not just `suffi`/`suffît` — the audit
  found this was a significant, previously-uncounted source of the residual: real-ambiguous
  collision count dropped **4,983 → 134** once these were gone, since a lot of coincidental
  cross-lemma collisions involved a `sub:imp` form on one side).
  - `lexique.py::Lexique.stripSubjonctifImparfait` (called from `outputMixedLexique`) strips
    `sub:imp:*` tags from a row's `infover` before writing `LexiqueMixte.tsv`, dropping the row
    entirely if that was its only reading (a verb's other in-scope readings sharing the same
    corpus row, e.g. `sub:imp:1s;sub:pre:3s;`, are kept). Regenerating dropped 1,199 of 137,656
    rows.
    `resources/LexiqueSynthetic.tsv` (hand-completed paradigm gaps, not wired into `lexique.py`,
    see `util/completeVerbParadigms.py`'s own header note) was filtered the same way directly
    (16,170 of 58,395 rows dropped, all `sub:imp`-only — no mixed rows needed stripping).
  - `src/verbparadigm.py::FINITE_SLOT_EXCLUDED_CODES` gained `"sub:imp"`, so
    `util/completeVerbParadigms.py --apply` won't regenerate these slots into
    `LexiqueSynthetic.tsv` in a future paradigm-completion run.
  - Corpus size: 184,524 → 167,639 words. `src/elicitation.py`'s
    `{"subjonctif", "imparfait"} <= c` filter (2026-09-19) is now provably unreachable (no such
    combination exists anymore) but was left in place rather than removed as part of this
    change — harmless, and out of this session's scope.
  - Recompute chain (same as fix 2 above): `python lexique.py` → `python dictionary.py` →
    `python -m src.elicitation` → `python -m util.build_phase_p_realization`.

## Status update (2026-09-20)

Written to keep this file honest without a full rewrite: the "Current state" audit and
"Roadmap" sections below are dated 2026-09-15/17/18 and describe the plan **as originally
conceived**; a lot has since shipped, pivoted, or been discarded. `ATOMIC_KEYPRESS_REWIRE_PLAN.md`
is the authoritative, currently-maintained plan for the same-lemma and lemma-homophone tracks —
this section summarizes where things actually stand and points there for detail.

### What was done

- **Phase 0 (measure)** — `src/ambiguitychecker.py` built; walked every n≥5 lemma-homophone
  overflow cluster by hand with the user, producing `resources/ambiguityIgnoreList.tsv` (79
  curated exclusions: archaic/loanword/unpopular-spelling/sociolect/data-artifact). Overflow
  clusters dropped 58 → 20 (max size 8 → 7).
- **Phase 1 (cross-category clash)** — `detectCrossCategoryClash` implemented and tested; the
  `aller` NOM/VER-style gap is now caught mechanically.
- **Elicitation-first pivot (2026-09-18)** — see "tried and discarded" below: the original
  Phase 2 plan (solver picks features, then shape constraints to make it learnable) was
  replaced with **Phase E** (elicit the user's own marker choices pair-by-pair) → **Phase G**
  (group elicited markers onto abstract keypresses) → **Phase P** (physical realization).
  `ATOMIC_KEYPRESS_REWIRE_PLAN.md` is the authoritative record.
- **Phase E (elicitation)** — E0-E6 complete: questionnaire built, published as a web
  Artifact, fully answered by the user (several revisions as lexicon bugs were found and
  fixed live), validated, persisted as `resolved_press_sets.json`.
- **Phase G (grouping)** — abstract keypress grouping solved for the same-lemma track;
  greedy result later proven exactly optimal via an exact CP-SAT solver
  (`src/phasegsat.py`); model 2 (`pers_3` default) adopted after a two-model comparison.
- **Phase P milestone 1 (physical realization, same-lemma track)** —
  `realizeKeypressGroupsAsExtraStroke` (`src/ambiguitychecker.py`): all 6 Phase G groups now
  have a real physical coda-bank key, **zero same-`lemmeGramCat` collisions left**, verified
  against the full ~136k-word/47,799-group lexicon. Output artifact:
  `phase_p_keypress_realization.json`.
- **The `*`/`#` lemma-homophone track** (bucket 2 cross-category clash + bucket 3 cross-lemma
  collision) — designed and fully implemented 2026-09-20, closing out this roadmap's original
  Phase 2/4 lemma-homophone goals:
  - `decideStarHashMark` — pairwise marking decision (homograph exemption → spelling-doublet
    exemption → per-pair overrides → 10x frequency-ratio exemption → same-`gramCat`
    per-pair-optimal → `GRAMCAT_PRIORITY` categorical rule), within **0.53%** of the
    theoretical optimum keystroke cost (0.208–0.526% across three independent measurements).
  - N-ary generalization (`rankHomophoneCluster`/`assignStarHashMarks`/`assignStarHashCombos`)
    — resolves the "clusters with ≥5 members" open question (§7 below): escalates past the
    4-reading single-stroke budget by giving each further reading one more whole `*#` extra
    syllable (`(*#,*#)`, `(*#,*#,*#)`, …), unbounded.
  - Physical realization on the Starboard's reserved keys: `*` = key 10, `#` = key 15
    (`STAR_KEY`/`HASH_KEY`), validated against the live lexicon (biggest real cluster: 7
    readings, the `au`/`eau`/`oh`/`haut`/`ho`/`ô`/`aux` set).
  - Composition with Phase P's own extra stroke
    (`groupHomophonesByReservedStroke`/`composeReservedKeyStrokes`) — the two tracks
    concatenate safely (structurally disjoint key ranges); validated zero-collision against
    1079 real groups in the elicited population.
  - Rule 3 (spelling-doublet exemption), correctly sourced from `resources/reform1990.tsv`
    (`loadReform1990DoubletPairs`) rather than the disproven heuristic.
- **The `*`/`#` pipeline wired into `dictionary.py`'s persisted output (2026-09-20)** —
  `Dictionary.buildFinalTheory`/`writeFinalTheory` compose theory 1 with Phase P
  (`realizeKeypressGroupsAsExtraStroke`, generalized to the whole lexicon via the new
  `buildFinalInducedStrokes`) and the `*`/`#` track (`composeReservedKeyStrokes`) into one
  per-word final-stroke table, persisted as `theory2.tsv` (gitignored, regenerable) when
  `phase_g_keypress_assignment.json` and `resolved_press_sets.json` are present. Resolves
  open question 4 (`theory.tsv`'s fate) below. Verified **zero residual real collisions**
  (184,524 words) after excluding `reform1990.tsv` spelling-doublet pairs, which are
  correctly left unmarked by design (Rule 2). This also retires the superseded
  solver-picks-features step that used to run in `dictionary.py`'s `__main__`
  (`buildDiscriminatorSelection` + `satOptimizeDiscriminator`, console-print-only, vestigial
  conflict count) — removed rather than redirected, since Phase E/G/P + the `*`/`#` track
  now own this job end to end. `satOptimizeDiscriminator`'s own `FEATURE_FAMILIES`/polarity
  machinery (`src/satoptimizer.py`) is now only self-referential (no external caller left);
  cleanup still tracked below.

### What was tried and discarded

- **The original Phase 2 plan itself** — CP-SAT/greedy solver (`satOptimizeDiscriminator`/
  `assignDiscriminatorKeypresses`) picks each word's discriminating features, then shape
  constraints around the outcome to make it learnable. Discarded 2026-09-18: a keypress's
  meaning under that coloring was "whatever was cheapest that run," not a fixed, learnable
  slot. Replaced by elicitation-first (the user's own reflexes are the spec; only the
  grouping of elicited markers is optimized afterward).
- **`assignDiscriminatorKeypresses`** (`src/greedyoptimizer.py`) — fully implemented,
  unit-tested, but orphaned (never wired into `dictionary.py`); superseded by elicitation for
  the same-lemma track (elicitation's default-form answers replace `FEATURE_PRIORITY`'s job
  there). Not fully dead: `FEATURE_PRIORITY` still does live work in
  `_selectCanonicalIndex`/the `*`/`#` track's own no-stroke pick.
  `GRAMCAT_PRIORITY` (new, same file) mirrors its convention for the lemma-homophone track.
- **The original `findKeypressGroupRealizations`** — merged a discriminator into a word's
  *last existing* stroke and tested each Phase G group in isolation. Discarded during Phase P
  execution: produced false collisions and false non-collisions once a word needed more than
  one group at once. Replaced by `realizeKeypressGroupsAsExtraStroke` (brand-new trailing
  stroke, per-word multi-group composition).
- **Rule 3 v1 — "many collisions in one lemma pair ⇒ probably a spelling-reform doublet."**
  Tested against real Google Books Ngram data on the 5 largest examples of the pattern found;
  only 2 of 5 were genuine doublets (the other 3 are distinct lexemes that happen to be
  near-total homophones). Disproven and discarded 2026-09-20, replaced by directly
  cross-referencing `resources/reform1990.tsv` (a real, already-sourced list already in-repo).
- **An early "mark NOM" conclusion for the NOM/VER category-pair type** — fit on bucket-3-alone
  raw data, dominated by easy/extreme-ratio pairs. Reversed once the ratio-10x exemption
  isolated the actual hard residual: the regret-optimal direction is "mark VER." Superseded;
  discard if seen in older notes.
- **30x/100x thresholds for the ratio exemption** — tested as alternatives to 10x. Both worse
  on every metric measured (higher total gap%, and both produce the same 3-cycle in the
  `GramCat` ranking that 10x avoids). 10x confirmed as the correct choice, not a compromise.

### What's left to do

- Regenerate `MARKING_OVERRIDES` (the ~51-pair per-pair override list) from a single canonical
  run purely at the 10x threshold — currently built from a top-10-by-regret cross-check
  against 30x/100x, not one clean run.
- Confirm (not just assume) that bucket 2 and bucket 3 share one physical marking mechanism —
  implemented that way, but the underlying design question was never explicitly re-confirmed.
- The `-er`/`-ers` noun wishlist item (reuse `Infinitif`/`Infinitif:p` atomic markers instead of
  a generic `*`/`#` mark for a whole NOM/VER homophone sub-class) — raised, not sized or
  verified against real data.
- **Phase 3** (re-validate/version the phoneme layer, layout freeze) — not started.
- **Phase 5** (automatic theory-level briefs) — not started.
- **Phase 6** (dictionary densification: paradigm tables, compositional generation, prefixes,
  dual-target Plover/Javelin architecture) — not started.
- **Phase 7** (personal theory layer / user briefs) — not started.
- Still-deferred data-quality items from Phase 0's manual review (comma-joined dual-lemma rows,
  a mispronounced entry, suspected mistagged-verb "ghost lemmas") — flagged, not fixed.
- The `"p"`/`"f_p"`/`"m_p"` feature-fusion bug (design decision 4) — still deferred.
- Open decisions carried from `ATOMIC_KEYPRESS_REWIRE_PLAN.md` (both still open there despite
  Phase E being "done"): §E's strict/lenient margin mechanism (where the margin lives — global /
  per-gramCat / per-cluster — and its default), and §G's cluster-scoping for noun homophones
  inside verb clusters (noun `parlé` in the [paʁle] cluster: marker track vs `*`/`#` track).
- Now that wiring has landed: `FEATURE_FAMILIES`/`associationScore`/polarity machinery
  (`src/satoptimizer.py`) has no external caller left (only self-referential within
  `satOptimizeDiscriminator`, itself no longer called from `dictionary.py`) — decide whether
  to delete it outright; plus two known diagnostic-path bugs in `src/ambiguitychecker.py`
  (`_isFeasibleAddition` misses new-vs-new composed-chord collisions; `checkComposedChords`
  reads `feasibleComboPhonemes[0][0]`, half of a 2-phoneme combo).
- Housekeeping: merge `phase-g-grouping` (which long outgrew Phase G) to `main`.
- No tests yet for `cpsatsolver.py`/`cpsatoptimizer.py`'s ambiguity math (still true, see
  "Ongoing" below).
- **Integrate the pipeline steps currently sitting in separate helper scripts/functions
  outside `dictionary.py`** (`lexique.py`, `util/completeVerbParadigms.py`,
  `src/elicitation.py`, `util/build_phase_g_assignment.py`,
  `util/build_phase_p_realization.py`) into one orchestrated entrypoint, so a lexicon
  change can't leave part of the chain silently stale. See `LEXICON_RECOMPUTE_PIPELINE.md`
  for the full dependency table and the two silent-failure traps (stale
  `Dictionary.pickle`/`FirstTheory.pickle` cache; `phase_p_keypress_realization.json`
  going stale independently of `theory2.tsv`) that motivated this.

## Terminology

**"Lemma-homophones"** (this document's term) = a set of homophone words whose **lemmas
differ** — ver/vert/verre/vers/vair. This is the cross-lemma case below.

Do not confuse this with **same-lemma homophones** (inflected forms of *one* lemma) — a
separate problem, solved by a separate mechanism (conjugation chords, not reserved keys).

## Current state, grounded in the code (audit)

*Dated 2026-09-15/17/18 — describes the plan as originally conceived. The phoneme-layer audit
below still holds; the same-lemma/lemma-homophone audit does not (see "Status update" above and
`ATOMIC_KEYPRESS_REWIRE_PLAN.md` for what actually shipped).*

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
  does not yet encode any special-keypress disambiguation — this is "theory 1."

**Same-lemma homophones ("theory 2," in progress)**
- `extractDiscriminatingFeatures` → `greedyOptimizeDiscriminator` (`src/greedyoptimizer.py`)
  split homophone clusters by `lemmeGramCat` (lemma **+** grammatical category, deliberate —
  see the cross-category gap below) and greedily assign a discriminating `WordFeature` to each
  word in a >1 sub-group. Output: `augmentedTheory: dict[tuple[WordFeature,...],
  list[tuple[Word,...]]]`.
- Two mechanisms exist to turn those abstract features into physical special keypresses, and
  only one is wired in:
  - **`satOptimizeDiscriminator`** (`src/satoptimizer.py`) — CP-SAT graph coloring, computes
    the minimum number of abstract key-indices needed for zero conflicts (**10** at this
    audit's date, **11** after the 2026-09-18 coverage-first switch, up from 8 as the lexicon
    grew; a fresh 2026-09-20 run reports **0** conflicting feature-sets — the figure has
    stopped being meaningful, see the retirement item in "What's left to do"). **Active
    pipeline step**, but its output is an abstract color
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

**Known, already-scoped bug affecting special-keypress count**
- Per `todo.md`: `Word.getFeatures()` offers both a bare feature (`"p"`) and a gender-qualified
  one (`"f_p"`/`"m_p"`) for the same distinction; the greedy selector picks by lexicon-wide
  popularity rather than reusability, sometimes costing a whole extra special keypress. Explicitly
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

1. **Reserved-key budget is 2 keys, not 4.** Of the Starboard's 4 reserved keys, only `*` and
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
**Status: DONE** — see "Status update" above.

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
**Status: DONE** (`detectCrossCategoryClash`) — see "Status update" above.

Goal: close the gap where two different-category readings of the same lemma can be mutually
homophonous, differently spelled, and go undiscriminated.
- Extend the collision check to look across `lemmeGramCat` groups sharing the same lemma (or
  more generally, across all groups landing in the same phonetic-stroke cluster), not just
  within each group.
- Add a regression test using the `aller` NOM/VER case, or a synthetic minimal example.
- This is small once Phase 0's checker exists — it's the thing the checker will catch first.

### Phase 2 — Conjugation-chord assignment + lemma-homophone rank assignment
**Status: PIVOTED + DONE, not as originally planned.** The "conjugation track" below (solver
picks a meaning-anchor chord, e.g. 2ps → final `/s/`) was discarded 2026-09-18 for
elicitation-first (Phase E/G/P in `ATOMIC_KEYPRESS_REWIRE_PLAN.md`) and is now DONE that way —
Phase P milestone 1. The "lemma-homophone track" below is now DONE as the `*`/`#` track
(`decideStarHashMark` and friends) — see "Status update" above; it ended up needing no CP-SAT at
all (frequency-rank + a categorical rule, exactly as this section anticipated as a fallback).
Persistence (this section's last bullet) is the one piece still not done — see "what's left."

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
  with one row per word, its phonetic stroke, and its resolved special-keypress/chord stroke.
- Gate: Phase 0's checker goes green against the persisted output.

### Phase 3 — Re-validate and version the phoneme layer
**Status: NOT STARTED.**

Goal: confirm `starboard3h.json` is still optimal against the current lexicon, and decide a
freeze/versioning policy before the theory reaches real learners.
- Re-enable and test `cpsatsolver.py::optimizeKeyboard` enough to confirm whether re-solving
  against today's lexicon changes the layout at all.
- Persist solver parameters + a lexicon hash next to the output going forward, so the layout is
  reproducible — there is currently no record of how `starboard3h.json` was generated.
- Decide when to freeze the phoneme layout and the special-keypress physical layout for learnability
  — a shifting layout is a real cost, distinct from "can we still improve it," and matters more
  now that a microcontroller target is confirmed (firmware/hardware users tolerate drift even
  less than a Plover dictionary file does).
- Decide brief scope (Phase 5) before freezing — briefs interact with the stroke budget.
- Watch special-keypress headroom — **reframed by the pivot**: same-lemma discrimination no
  longer touches the reserved keys at all (Phase P realized its 6 groups on the coda bank),
  so the old "8→10 abstract keys for the conjugation track" watch-item is moot. What remains
  is the `*`/`#` track's 2 guaranteed keys (`STAR_KEY`/`HASH_KEY`, keys 0/1 held for a
  possible 3rd mark), whose escalation is unbounded by design. Re-check headroom at freeze
  time.

### Phase 4 — Lemma-homophone strategy at scale
**Status: DONE, though building blocks 2/3 below weren't literally built as described.** The
actually-shipped design (`decideStarHashMark`'s rule stack — ratio exemption, spelling-doublet
exemption, per-pair overrides, `GRAMCAT_PRIORITY` categorical rule) supersedes this section's
"generalized spelling-rule-based key clusters" and "grammatical category as a free
discriminator" building blocks with an equivalent (arguably stronger — within 0.53% of the
theoretical optimum, measured) approach. See "Status update" above.

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
**Status: NOT STARTED.**

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
**Status: NOT STARTED.**

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
**Status: NOT STARTED.**

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
  once Phases 0–2 land, so the README stops undercounting what's already built. (CLAUDE.md's
  pipeline section was reconciled 2026-09-20; `todo.md`'s live status too. README is the
  remaining one.)

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

1. **Javelin as prior art** — still open. Is there a specific fork/version of Javelin in mind,
   or specific features from it already known to be worth mirroring (rule syntax, on-device
   conjugation table storage, memory constraints)?
2. **Reserved-key set flexibility** — **de facto resolved, not revisited as a design choice**:
   `STAR_KEY=10`/`HASH_KEY=15` are hardcoded module constants in `src/ambiguitychecker.py`, not
   user-configurable. Keys 0/1 (left pinky, also reserved) are unassigned, held for a possible
   future 3rd logical mark.
3. **Layout freeze** — still open; no target point decided yet.
4. **`theory.tsv` fate** — still open, and now the concrete next step: wire the `*`/`#`
   pipeline and Phase P's own output into `dictionary.py`'s persisted output (see "Status
   update" above). Not yet decided whether this replaces `theory.tsv` or lives alongside it.
5. **Conjugation modifier form** — **resolved by Phase P's implementation**: a brand-new
   trailing stroke (extra "syllable"), never merged into the word's last existing chord — the
   separate-modifier-stroke option, not the fused English `-S`/`-G` style.
6. **The anchor table** — **moot, resolved by the elicitation pivot**: there is no
   phoneme/orthographic anchor table to design: the user's own elicited press-per-opposition
   answers (Phase E) directly are the mapping, replacing the need to guess anchors a priori.
7. **Lemma-homophone clusters with >4 members** — **resolved**: `assignStarHashCombos`
   escalates past the 4-reading single-stroke budget by giving each further reading one more
   whole `*#` extra syllable (`(*#,*#)`, `(*#,*#,*#)`, …), unbounded (see "Status update"
   above). No curated-exception fallback was needed.
8. **Where prefix strokes live** (phoneme-layer pseudo-phonemes?) and their cost against the
   22-key phoneme budget — still open; Phase 6 not started.
9. **One shared runtime rule engine** (Plover python-dict + Javelin) vs. two exporters of a
   shared table format, for Phase 6 — still open; Phase 6 not started.

## Verification approach (once implementation starts on any phase)

- `pytest src/test/` must stay green throughout; add targeted tests per phase as noted above.
- Phase 0's end-to-end zero-ambiguity checker is the meaningful verification for Phases 1 and 2
  — run `python dictionary.py` and confirm the resolved theory has no remaining stroke
  collisions, rather than treating this check as a Phase 2-only deliverable.
- For Phase 3, compare `optimizeKeyboard()`'s fresh solve against `starboard3h.json` to quantify
  drift before deciding on a refresh/freeze policy.
