# Roadmap

Forward-looking only: the phases not yet built, the open design decisions and the open
questions. What already shipped is documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
and [docs/PIPELINE.md](docs/PIPELINE.md); suspected bugs and small follow-ups live in
[TODO.md](TODO.md); history lives in git. Prior art informing these plans:
[docs/PRIOR_ART.md](docs/PRIOR_ART.md).

## Phases not started

### Phoneme-layer re-validation and layout freeze (Phase 3)

Goal: confirm `starboard3h.json` is still optimal against the current lexicon, and decide a
freeze/versioning policy before the theory reaches real learners.

- Re-enable and test `cpsatsolver.py::optimizeKeyboard` enough to confirm whether re-solving
  against today's lexicon changes the layout at all.
- Persist solver parameters + a lexicon hash next to the output going forward, so the layout
  is reproducible — there is currently no record of how `starboard3h.json` was generated.
- Decide when to freeze the phoneme layout and the special-keypress physical layout for
  learnability — a shifting layout is a real cost, distinct from "can we still improve it,"
  and matters more now that a microcontroller target is confirmed (firmware/hardware users
  tolerate drift even less than a Plover dictionary file does).
- Decide brief scope (theory-level briefs (Phase 5) below) before freezing — briefs interact
  with the stroke budget.
- Reserved-key headroom: same-lemma discrimination no longer touches the reserved keys at all
  (the Realization Phase realizes its 7 Keypress Groups on the coda bank), so the old
  "8→10 abstract keys for the conjugation track" watch-item is moot. What remains is the
  star/hash marks' 2 guaranteed keys (`STAR_KEY`/`HASH_KEY`, keys 0/1 held for a possible
  3rd mark), whose escalation is unbounded by design. Re-check headroom at freeze time.

### Theory-level briefs (Phase 5)

Goal: automatic, corpus-driven shortcuts for the most frequent words and 2–3 word phrases —
distinct from the personal theory layer (Phase 7).

- Every mature theory hand-tunes a brief table; it is the single biggest WPM and learnability
  lever (English Plover/Lapwing briefs; Pluvier and Regenpfeifer both layer manual briefs
  over generated outlines — see [docs/PRIOR_ART.md](docs/PRIOR_ART.md)). Leaving this to
  user-personal briefs alone delegates theory design onto individual learners.
- This project already has the assets for automatic briefing: corpus frequencies + working
  conflict machinery. Assign the shortest conflict-free strokes to the top-N words and
  frequent short phrases.
- Interacts with the phoneme-layer freeze (Phase 3) and the stroke budget — decide scope
  before freezing.

### Dictionary densification (Phase 6)

Goal: one entry per homophone-per-lemma pointing at a shared conjugation/paradigm table, plus
the ability to compose a base word's phonology + a grammatical-feature key into an
unrelated-sounding inflected form (généraux from général + m_p) — and the mirror-image
problem, compositional prefixes (re-, dé-, co-…), rather than enumerating every prefixed ×
conjugated form as flat entries.

- **Dual-target architecture**: a large static Plover dictionary, and a small dictionary +
  runtime rule engine for a microcontroller build modeled on Javelin. Both consume the same
  underlying paradigm-table data — design that shared representation first, then build the
  two exporters/consumers on top of it.
  - **Plover target**: extend today's offline gap-filling approach
    (`nomAdjParadigm.py`/`verbparadigm.py`-style learned transforms) to precompute every
    compositional entry directly into the dictionary — or, per `plover-python-dictionary`,
    reuse the same runtime rule engine as the microcontroller target instead of a flat
    exporter.
  - **Microcontroller/Javelin-style target**: paradigm/transform tables exposed as a compact,
    on-device-queryable ruleset (base form + feature → derived form at input time). Study
    Javelin's own dictionary/rule format as prior art
    ([docs/PRIOR_ART.md](docs/PRIOR_ART.md)) before designing this.
- **Prefix formation is a confirmed goal**, compositional rather than flat-enumerated:
  prefix strokes live on phoneme-layer keys (pseudo-phonemes), consuming phoneme-key budget.
  On the Plover target, compositional prefixes either still enumerate every prefixed form
  (the size cost this goal exists to avoid) or use `plover-python-dictionary` to compose at
  lookup time — pushing toward one shared rule engine rather than two independent exporters.
- Open: the prefix inventory to support, and whether prefixed forms interact with the
  lemma-homophone merges behind the star/hash code assignment.

### Personal theory layer (Phase 7)

Goal: user-added shortcuts/briefs for common words and 2-3 word expressions, layered on top
of the base theory (distinct from theory-level briefs (Phase 5)'s automatic, corpus-driven
briefs).

- Needs its own conflict-resolution against the base theory's stroke space (can't silently
  collide with an existing word's stroke).
- Not started; no existing code to build on here.

## Open decisions

- **Elicitation margin mechanism** — where a strict/lenient margin would live (global,
  per-gramCat, or per-Homophone Group) and its default. Carried from the pre-pivot design;
  still undecided.
- **Noun homophones inside verb phonetic-theory collisions** — a noun sharing a verb's phonetic-theory
  stroke (noun `parlé` in the [paʁle] collision): feature discriminating stroke (Same-Lemma
  and Grammatical-Category Disambiguation (S6)) or star/hash mark (Different-Lemma or
  Grammatical-Category Disambiguation (S7))? Still undecided.
- **Firmware button rewire (keys 2 and 10)** — the Gemini PR firmware sends keys 0/1/2/10 as
  number-bar bits (hardware-verified; see `GEMINI_PR_LABELS`, util/export_plover_system.py).
  Rewire two of them at the firmware level to send real letter/star bits instead, or keep
  translating in the key table? A product decision outside this repo's code.

## Open questions

1. **Javelin as prior art** — is there a specific fork/version of Javelin in mind, or
   specific features from it already known to be worth mirroring (rule syntax, on-device
   conjugation table storage, memory constraints)?
2. **Layout freeze** — no target point decided yet (see phoneme-layer re-validation and
   layout freeze (Phase 3)).
3. **Where prefix strokes live** (phoneme-layer pseudo-phonemes?) and their cost against the
   22-key phoneme budget.
4. **One shared runtime rule engine** (Plover python-dictionary + Javelin) vs. two exporters
   of a shared table format, for dictionary densification (Phase 6).

## Ideas

- **Star/hash marker strokes as a Plover macro plugin** — replace the ~48k static
  marker-stroke dictionary entries with a (word, marker) → inflected-form table lookup,
  mainly for the Javelin onboard-flash target where dictionary size matters. Plover's
  `ORTHOGRAPHY_RULES` cannot do this (French inflected forms are not derivable from the
  spelling); Javelin's equivalent has not been checked yet.
