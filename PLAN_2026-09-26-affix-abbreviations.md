# Affix Abbreviation Discovery and Key Binding — handoff spec (2026-09-26)

**Audience: the model that implements this after a `/clear`.** Everything needed is here. The
design decisions (section 2) are the user's answers; don't re-ask them. When this spec leaves
something open, pick the default given here and say so in the final report.

---

## 0. Start-up checklist

1. Read these, in order: this file; `RESUME_2026-09-26-pluvier-affix-scan.md`;
   `scratch/pluvier_affix_scan.py` (283 lines, the prototype to build on); `CLAUDE.md`.
2. Environment:
   - Bare `python` is not on PATH. Use `env/bin/python` and run from the repo root.
   - Scripts under `scratch/` need `PYTHONPATH=.`. Modules run as `env/bin/python -m util.xxx`
     (there is no `util/__init__.py`; namespace-package `-m` already works for the other util
     CLIs).
   - The machine has **7 GB RAM**. Never load the theory in two processes at once; run heavy
     jobs one at a time.
   - Loading the disambiguated theory takes about 50 s. Cache the extracted records (see A1).
3. The user wants cheap subagents for mechanical work (haiku for waiting on runs and diffing,
   sonnet for scoped coding and tests). They commit directly on `main`, but **only when they ask**.
   Do not commit and do not push.
4. **Do not change any pipeline artifact.** Don't delete the pickles and don't rerun the
   pipeline. This iteration is measurement and proposals only (Decision 10). Every new output goes
   under `scratch/`, except the new source and test files.
5. Documentation style: name stages by name plus number ("Theory Export (S8)"), and phases by
   meaningful name only (see memory "Naming stages by name").

---

## 1. Goal

Find families of prefixes and suffixes whose strokes can be shortened, and propose, for each
family, a keypress (or a stroke) that stands for the affix.

The user's quality criteria:
- (Q1) it never adds strokes to a word, and it removes strokes in most cases;
- (Q2) a family's members are similar to each other (in sound or in spelling);
- (Q3) members that compete (biologie / biologique / biologiste) must not be merged into the same
  key.

Background: the theory has one base stroke per phonetic syllable
(`Dictionary.buildPhoneticTheory`, `dictionary.py:335-345`). The prototype scan found that only 6
Pluvier families save strokes when a whole replacement stroke is used. A one-syllable affix only
gains if its sound is **merged as a keypress into the neighbouring stroke**.

Two binding kinds:
- **Merged**: drop the affix's k syllable strokes and OR a keypress `K` into the neighbouring base
  stroke. Saves k strokes.
- **Dedicated**: replace the k syllable strokes with one stroke `D`. Saves k−1 strokes, so it only
  makes sense for k ≥ 2.

---

## 2. Decisions (the user's answers; binding)

1. **Added alongside.** The shortened outline is an *extra* Plover entry, and the full outline
   stays. The clash check runs against every existing full outline too.
2. **Key pool.** Phoneme keys only (`allowedKeys` in `starboard3h.json`: 2–9 onset, 11–14 nucleus,
   16–25 coda).
   - The affix's natural bank is preferred: **onset keys for a prefix** (the prefix merges into the
     first stem stroke), **coda keys for a suffix** (it merges into the last stem stroke).
   - Other banks are allowed with a penalty.
   - **Never** use the reserved keys 0, 1, 10 (`*`) or 15 (`#`).
3. **Before the `*`/`#` marking.** The shortened outlines conceptually join the base outlines
   before the grammatical-feature strokes (S6) and the `*`/`#` marks (S7). A clash with another
   word is therefore *not* fatal; it costs marks (section 5, A5).
4. **Morphological only.** A word carries an affix only if its stem is attested (section 4, A2).
5. **Family similarity.** Sound *or* spelling similarity qualifies a member.
6. **Competition: split, keeping a shared core.** Competing members get distinct keypresses of
   the form `core ∪ {discriminator key}`, where the core is shared by the whole family.
7. **Frequency: `Word.frequency`.** In `src/word.py:93-94` this is film-subtitle only today (the
   0.9 film / 0.1 book mix is commented out). Just read `Word.frequency`.
8. **Multi-syllable affixes: merged is preferred when it is clash-free and meaningful**
   (similarity ≥ `SIM_MIN`). Otherwise use a dedicated stroke.
9. **Similarity dominates physical comfort.** Comfort is only a tie-breaker.
10. **Suffixes reach inflected forms through the lemma** (section 4, A2c). This iteration is
    **measurement and proposals only**.

---

## 3. Files

New files:
- `src/affixes.py`: library code for Part A (records, candidates, morphology, families,
  competition, gain simulation).
- `src/affixbinding.py`: library code for Part B (similarity, keypress enumeration, legality,
  assignment).
- `util/affix_scan.py`: the CLI that runs A then B and writes every output.
- `resources/affixSeeds.tsv`: the prototype's `RULES` and `FAMILIES` moved to data, with columns
  `position  affix  pluvier_chord  family`.
- `src/test/affixes_test.py` and `src/test/affixbinding_test.py`.

Outputs (all under `scratch/`, untracked):
- `scratch/affix-records.pickle` (cache)
- `scratch/affix-candidates.tsv`
- `scratch/affix-families.tsv`
- `scratch/affix_bindings.json`
- `scratch/affix-bindings-report.md`

Code to reuse, not reimplement:

| Need | Use |
|---|---|
| Load both theories in one unpickle | `util/_theoryio.loadPhoneticAndDisambiguatedTheory(starboard)` → `(phoneticTheory: dict[Strokes, list[Word]], disambiguated: dict[Word, list[Strokes]])` |
| Keyboard | `Starboard.fromJSONFile("starboard3h.json")` (`src/keyboard.py:252`, may return None → assert) |
| Word → base strokes | `buildWordToStrokes(phoneticTheory)` (`src/ambiguitychecker.py:630`) |
| Canonical chord form | `canonicalizeStrokes` (`src/keyboard.py:31`): `tuple(sorted(set(stroke)))` per stroke. **Always compare canonical forms.** |
| Base vs extra split | `fullStrokes[len(baseStrokes):]` are the extra strokes (feature strokes and marks); the first mark's keys are merged into `fullStrokes[len(base)-1]` (see `Dictionary.writeDisambiguatedTheory`, `dictionary.py:434-463`) |
| Mark codes | `assignStarHashCombos(m)` (`src/ambiguitychecker.py:273`): codes `(), (*,), (#,), (*#,), (*#,*#), …`; `len(code)` = number of mark symbols |
| Key legality and cost | `Starboard.getStrokeCost(keys, syllabicPart)` (`src/keyboard.py:547`): **call it per bank** with only that bank's keys and `"onset"`/`"nucleus"`/`"coda"`; `None` = illegal |
| Banks | `starboard.keyIDinSyllabicPart` = `{"onset": [2..9], "nucleus": [11..14], "coda": [16..25]}` |
| Phoneme → keys | `starboard.getStrokesOfPhoneme(phoneme, part)[0]`, or read `phonemesAssignedToStroke` in `starboard3h.json` (a phoneme can appear in several banks) |
| Rendering | `util/_stenorender.renderFinalStrokesToRTFCRE(starboard, strokes)` for the report |
| Syllables | `word.phonemesToSyllableNames(withSilent=False)` (phonetic, one per base stroke); `word.orthosyllCV` (list of letter groups per syllable); `spans()` in the prototype turns the latter into letter offsets |
| Test Word factory | `_make_word(**overrides)` pattern in `src/test/ambiguitychecker_test.py:47` (fields `ortho, phonology, lemme, gramCat, orthoGramCat, gender, number, infoVerb, rawSyllCV, rawOrthosyllCV, frequencyBook, frequencyFilm`) |

Tunable constants go at the top of `src/affixes.py` and `src/affixbinding.py`, with these
defaults (report their values in the output headers):

```
MAX_AFFIX_SYLL = 3        MIN_STEM_LETTERS = 3      MIN_CARRIER_LEMMAS = 5
MIN_CANDIDATE_FREQ = 20.0  # summed Word.frequency of morphological carriers
FAMILY_LINK_SIM = 0.6      MAX_FAMILY_MEMBERS = 12   MIN_FAMILY_STROKEFREQ = 30.0
SIM_MIN = 0.5              GAIN_KEEP = 0.8           OTHER_BANK_WEIGHT = 0.5
NUCLEUS_VOWEL_WEIGHT = 0.5 UNEXPLAINED_KEY_PENALTY = 0.25   MAX_KEYPRESS_KEYS = 3
```

---

## 4. Part A: discovery (`src/affixes.py`)

### A1. Records and cache

```python
@dataclass(frozen=True)
class WordRecord:
    ortho: str; lemme: str; gramCat: str; frequency: float
    phonoSylls: tuple[str, ...]      # phonemesToSyllableNames(withSilent=False)
    orthoSylls: tuple[str, ...]      # "".join(group) for group in orthosyllCV (keep "#"-free letters)
    base: Strokes                    # canonicalizeStrokes(wordToStrokes[word])
    extra: Strokes                   # canonicalizeStrokes(disambiguated[word][0])[len(base):]
    isLemmaForm: bool                # ortho == lemme
```

- `extractRecords(phoneticTheory, disambiguated) -> list[WordRecord]`.
- Skip any word where `len(orthoSylls) != len(base)` or `len(phonoSylls) != len(base)`. Count the
  skipped words and print them.
- Pickle the records to `scratch/affix-records.pickle`. Reuse it unless `--refresh` is passed.
- Also build `canonOutlineToRecords: dict[Strokes, list[WordRecord]]` over the base outlines.
  It's the collision index.

### A2. Candidates

A candidate is keyed by `(position, k, phonoAffix, orthoAffix)`: `phonoAffix` is the k syllable
names joined by `.`, and `orthoAffix` is the k ortho syllables joined together.

a. **Prefixes.** For every record and every `1 ≤ k ≤ MAX_AFFIX_SYLL` with `k < len(base)`: take
   the first k syllables. The stem is `ortho[len(orthoAffix):]`.

b. **Suffixes.** Discover them on lemma-form records only (`isLemmaForm`). Take the last k
   syllables. The stem is `ortho[:-len(orthoAffix)]`.

c. **Suffix inheritance (Decision 10).** An inflected record `w` with lemma `L` inherits a suffix
   `σ` (k syllables at the end of `L`'s base, which has `n_L` strokes) as follows:
   - `w.base[:n_L-k] == L.base[:n_L-k]` (same stem strokes);
   - `w`'s span is the maximal contiguous run of indices `i` from `n_L-k` with
     `i < len(w.base)` and `w.base[i] == L.base[i]`;
   - the run length `k_w ≥ 1` is `w`'s saving, and the strokes after the run (the varying
     inflection tail) stay in place.

   Examples:
   - `nations` has the same base as `nation`, so it inherits the full span.
   - For `organisons` against `organiser` with σ = `ni.ser`: only `ni` is identical, so `k_w = 1`
     and the tail `z§` stays.

   If `L` has no lemma-form record, `w` inherits nothing.

d. **Morphological filter (Decision 4, hard filter).** The stem must be attested. Normalize with
   `norm(s)`: lowercase, strip accents, drop one final `e`.
   - Prefix: `stem` (or the lemma's stem, for inflected forms) must have
     `len(stem) ≥ MIN_STEM_LETTERS` and `norm(stem)` must be in `{norm(x.lemme)}`
     (e.g. re|faire, ré|organiser, r|appeler).
   - Suffix: `len(stem) ≥ MIN_STEM_LETTERS` and `norm(stem)` must be a normalized prefix of at
     least one **other** lemma, or equal to one (nation|al → nation; organi|sation → organiser).
     Use a sorted list of normalized lemmas with `bisect` for the prefix lookup.
   - Only carriers that pass the filter count. Keep `morphStem` for each carrier (it's needed for
     A4).

e. **Candidate stats:** carriers (the morphological ones plus the inheriting ones), distinct
   lemmas, summed frequency, and the top 6 examples by frequency.
   - Keep a candidate if distinct lemmas ≥ `MIN_CARRIER_LEMMAS` and summed frequency ≥
     `MIN_CANDIDATE_FREQ`.
   - Also mark `isSeed` when `orthoAffix` equals a seed affix of the same position. Seeds are
     kept even when they fall below the thresholds, and flagged.

### A3. Families (Decision 5)

Group candidates of the same position (k may differ).

- **Similarity:**
  `sim(a, b) = max(phonSim, orthoSim)`, plus `0.1 × jaccard(stems(a), stems(b))`, capped at 1.
  - `orthoSim` = 1 − Levenshtein / max length.
  - `phonSim` is the same over the phoneme strings (dots removed), with vowel substitution cost
    0.5 inside these classes: `{e,E,@,°,2,9}`, `{o,O}`, `{a}`, `{i}`, `{y,8}`, `{u}`,
    `{§}`, `{5,1}`.

  Write a small Levenshtein; add no new dependency.
- **Clustering:** average-linkage agglomerative with threshold `FAMILY_LINK_SIM` and
  `MAX_FAMILY_MEMBERS`. Process candidates in descending frequency order so that the result is
  deterministic.
- **Seeds:** the seed families from `resources/affixSeeds.tsv` are also reported as-is, as
  reference rows. Each discovered family lists which seed families it overlaps.
- **Family carriers:** the union of the members' carriers, deduplicated by record. A record
  matched by several members keeps the member with the **largest** span.

### A4. Competition (Decision 6)

Members `a1` and `a2` of one family compete if some normalized stem `s` has both `s+a1` and
`s+a2` as lemmas of **different** lemmas (for prefixes, `a1+s` and `a2+s`).

- Competition mass = Σ over stems of min(freq of the two lemma groups).
- Build the competition graph and colour it greedily: largest mass first, colours are
  **sub-groups**. A family with more than one sub-group needs a core plus one discriminator key
  per sub-group (B3).
- Test fixture: logie / logique / logiste over stems bio, socio → 3 sub-groups.

### A5. Gain simulation (Decisions 1, 3; used again in Part B)

`simulate(binding, carriers) -> list[CarrierResult]`. For each carrier `w` with span
`[i, i+k_w)` of its base:

- **Merged `K`:**
  - The neighbour is `base[i+k_w]` for a prefix, or `base[i-1]` for a suffix. It must exist.
  - Infeasible if `K & neighbour ≠ ∅`, or if the union is illegal: split the union by bank and
    call `getStrokeCost(bankKeys, bank)` per bank; any `None` means illegal.
  - New base = base with the span removed and the neighbour replaced by `sorted(neighbour | K)`.
- **Dedicated `D`:** new base = base with the span replaced by `D`.
- **Mark cost.** Look up the new base in `canonOutlineToRecords` together with the other
  carriers' new bases.
  - Collisions with records of the same `ortho` are ignored.
  - A collision with a record of the same lemma but a different spelling is **infeasible** if
    their full base outlines were different, because the shortening erased a distinction. If
    their full outlines were the same, it costs 0 (S6 already resolves it).
  - Otherwise, count `m` = distinct spellings in the cluster including `w`. `w` is assumed to be
    ranked last, so `markCost = max(0, len(assignStarHashCombos(m)[m-1]) - 1)`. The first mark
    merges into the last stroke for free.
- **Word gain** = `k_w − markCost` for merged, `(k_w − 1) − markCost` for dedicated.
  - Gain ≤ 0 or infeasible → the word gets no shortened entry. This is its fallback: the full
    outline still exists (Decision 1), so no word ever gets longer.
- **Plover word-boundary risk** (reported, not blocking): the shortened outline, followed by its
  extra strokes, can be split into two or more consecutive existing **full** outlines, so Plover
  could mis-split "X Y". Check splits at every stroke boundary against a set of every final
  outline. Count such cases.
- **Family metrics:**
  - `strokeFreqSaved = Σ freq × gain`;
  - `freqBenefiting`;
  - `benefitShare` = benefiting carriers ÷ carriers, by count and by frequency;
  - the number of fallbacks by reason (`keyOverlap`, `illegalChord`, `lostDistinction`,
    `markCostTooHigh`);
  - `boundaryRisks`.

### A6. Part A outputs

- `scratch/affix-candidates.tsv`: one row per candidate. Columns: `position, k, phono, ortho,
  isSeed, carriers, lemmas, freq, topExamples, generalizedFrom` (the last is empty except for
  A7's pooled candidates).
- `scratch/affix-families.tsv`: one row per family, sorted by the upper bound
  `Σ freq × k_w` (before any keypress is chosen). Columns: `family_id, position, members
  (ortho/phono/freq), subgroups, competing_pairs (top 5 with stems), carriers, freq,
  upperBoundStrokeFreq, seedOverlap, review` (the `review` column is empty, for the user's
  keep/drop mark).
- Keep families with `upperBoundStrokeFreq ≥ MIN_FAMILY_STROKEFREQ`.
- **Checkpoint:** print the top 30 families to the console. If there are fewer than 5 or more
  than 300 families, stop and report to the user before running Part B, because the thresholds
  are probably wrong. Otherwise continue.

### A7. Generalized-affix pooling (added 2026-09-27, after the consonant+ilité investigation)

Runs inside `buildCandidates`, right after the morphological filter (A2d) builds the raw
per-affix candidates and right before A2e's threshold stats/checks -- so a pooled candidate is
what the thresholds see, not each of the individual spelling variants it replaces.

Rationale: a suffix or prefix's spelling regularly varies only by the consonant right next to the
stem, with the rest of the affix (vowel, coda, everything further from the stem) identical --
`-bilité/-tilité/-cilité/-rilité/-gilité/-vilité/-nilité/-nilité` are all "-ité" preceded by a
theme vowel and the stem's final consonant, not eight unrelated suffixes. Measured on the
2026-09-14 lexicon: only `-bilité` alone clears `MIN_CANDIDATE_FREQ`; the other seven, each with a
handful of lemmas, never would on their own (`scratch/cilite-investigation-report.md`).

Algorithm: for every candidate with `k ≥ 2`, split its phono into the syllable nearest the stem
(`bi`/`ti`/`ci`/...) and the invariant tail beyond it (`li.te`). Split that variable syllable into
`(onset, rest)` at its first nucleus-vowel phoneme (`_onsetRest`) -- `bi → (b, i)`. Group
candidates by `(position, k, tail, rest)`: two candidates in the same group differ only in the
onset consonant. Groups of 2+ are merged into one pooled `Candidate` (`variants` lists the
original orthos, `isGeneralized = True`); the pooled candidate's ortho/phono fold `rest` in
(`·ilité` / `i.li.te`) so that two different tails sharing the same invariant part (`-ilité` vs
`-alité`) don't collide into the same synthetic key.

This is a **structural** grouping (by shared phonology), independent of and prior to A3's
**similarity-based** clustering — A7 catches variants A3's Levenshtein/phoneme-class similarity
would likely also cluster eventually, but without requiring each variant to separately clear the
Part-A thresholds first.

See the OQLF prefix/suffix table below (§11) for which of the resulting pooled/unpooled
candidates correspond to a named, semantically real French affix versus an accidental phonological
coincidence.

---

## 5. Part B: binding (`src/affixbinding.py`)

### B1. Similarity score (Decisions 2, 9)

For each family, the **salient phonemes** are the phonemes of the member `phono` strings,
weighted by the frequency share of the members that contain them. Consonants count fully and
vowels ×0.5.

Each phoneme `p` has one key set per bank (`phonemesAssignedToStroke`). A keypress `K` encodes `p`
in bank `b` when K contains all of `p`'s keys in `b`. The score is:

```
sim(K) = Σ_p weight(p) × max over banks b encoding p of bankWeight(b)
         − UNEXPLAINED_KEY_PENALTY × (#keys of K not covered by any encoded phoneme)
bankWeight = 1.0 natural bank (onset for prefix, coda for suffix),
             NUCLEUS_VOWEL_WEIGHT for a vowel on nucleus keys,
             OTHER_BANK_WEIGHT otherwise
```

Normalize by `Σ_p weight(p)` to get 0..1.

### B2. Merged candidates

- Enumerate every subset of the phoneme keys with 1 to `MAX_KEYPRESS_KEYS` keys (1,793 sets).
- Keep the ones with `sim ≥ SIM_MIN` and legal on their own (per-bank `getStrokeCost`).
- Simulate each surviving `K` on the family carriers (A5).
- Selection: among the candidates with `strokeFreqSaved ≥ GAIN_KEEP × best`, take the highest
  `sim`. Ties go to the lower comfort cost: the frequency-weighted mean of per-bank
  `getStrokeCost` of the merged neighbour strokes.
- Keep the top 5 alternatives for the report.

### B3. Competing sub-groups (Decision 6)

If the family has more than one sub-group:

1. The **core** `K0` is the B2 pick for the whole family. If it is already taken, use its best
   legal alternative.
2. Each sub-group `g` gets `K0 ∪ {d_g}`. `d_g` is chosen by the same similarity function
   restricted to the phonemes that distinguish `g`'s members from the other sub-groups (e.g.
   `k` for -logique, `s`/`t` for -logiste). The `d_g` keys must be pairwise distinct and
   disjoint from `K0`.
3. Re-simulate every sub-group with its own keypress.

### B4. Dedicated candidates (Decision 8)

Use a dedicated stroke only for families where some member has k ≥ 2 **and** no merged candidate
passed `SIM_MIN` with a gain > 0.

- Candidates:
  - each member syllable's own base stroke;
  - the unions of two of those strokes, when legal;
  - the stroke with the best-scoring natural-bank keys for the family's salient consonants.
- Reject a `D` that is itself an existing single-stroke full outline. That's the default, because
  it would be a word-boundary trap.
- Select by the same rule as B2.

### B5. Global assignment (greedy)

Process families in descending order of the best `strokeFreqSaved`. Each one takes its best
candidate that does not conflict with an assignment already made. A conflict is either:

- the same position and the same keypress (or the same dedicated stroke); or
- a mutual collision: re-simulate both families' carriers together, and any carrier whose gain
  drops to ≤ 0 because of the other family counts as a conflict.

On a conflict, try the next alternative. After 5 alternatives, the family stays unbound.

Words carrying both a prefix and a suffix binding are simulated independently in this iteration;
report their count.

### B6. Part B outputs

- `scratch/affix_bindings.json`: a list of objects with `family_id, position, members,
  subgroups[{members, kind: "merged"|"dedicated", keys, rtfcre, sim, comfortCost}],
  strokeFreqSaved, freqBenefiting, benefitShare, fallbacks{reason: count}, boundaryRisks,
  alternatives[top5]`, plus a header with every constant's value.
- `scratch/affix-bindings-report.md`: one section per bound family, in descending gain order.
  Each section shows:
  - the members;
  - the keys, with the RTFCRE rendering of `K` alone;
  - sim and gain;
  - 10 example words as `ortho: OLD/OUT/LINE → NEW/OUT/LINE`, rendered with
    `renderFinalStrokesToRTFCRE` on base+extra;
  - the fallback counts;
  - the alternatives.

  End it with a comparison table of the 6 prototype-positive seed families: prototype strict freq
  vs new `freqBenefiting`, with a one-line reason for each gap.

---

## 6. CLI

```
PYTHONPATH=. env/bin/python -m util.affix_scan [--refresh] [--part a|b|all] [--seeds-only]
```

- `--seeds-only` restricts the candidates to the seed affixes. It's a fast debug path.
- Print the timings. Expect about 1 minute for the first load and seconds with the cache. If B2
  is slow, first prune the keypress sets by `sim`, then simulate on the top-frequency 2,000
  carriers and re-simulate the finalists on all of them.

---

## 7. Tests (hand-built Word/Strokes fixtures, no pickles)

`src/test/affixes_test.py`:
- the morphological filter: `refaire` passes (faire is a lemma); `nation` fails as -tion (`na`
  has no attested stem).
- suffix inheritance: the plural inherits the full span; the conjugated form gets the partial
  span with the tail kept.
- competition colouring: logie / logique / logiste → 3 sub-groups; ation / ition → 1.
- the mark-cost formula for m = 2, 4, 5, 6 (→ 0, 0, 1, 2).
- a gain is never negative, and an infeasible carrier falls back.

`src/test/affixbinding_test.py`:
- a merged keypress overlapping the neighbour → infeasible;
- an illegal per-bank union → infeasible (use a real `Starboard.fromJSONFile("starboard3h.json")`,
  which is cheap);
- `sim` prefers a natural-bank key over the same phoneme's other-bank key;
- sub-group keypresses share the core and have distinct discriminators;
- the greedy assignment never gives two families the same position and keypress.

---

## 8. Verification (all must hold before the final report)

1. `env/bin/pytest src/test/` all pass. There were 649 tests plus the new ones. If
   `env/bin/pytest` doesn't exist, use `env/bin/python -m pytest`.
2. mypy: `src/` has about 127 pre-existing errors, so don't expect a clean full run. Run
   `env/bin/python -m mypy src/affixes.py src/affixbinding.py util/affix_scan.py` and fix every
   error reported *in these new files*.
3. The pipeline artifacts are untouched: `md5sum phonetic_theory.tsv disambiguated_theory.tsv
   resolved_press_sets.json keypress_groups.json realization_report.json
   plover_stenalgo_dictionary.json steno-trainer/public/data/*.json` matches
   `scratch/b43-fix-md5s.txt`, or at least matches the md5s taken **before** you start. Take a
   before-snapshot first, because later commits may have legitimately changed them.
4. Sanity checks on the output:
   - -ité, -tion and inter-/re- appear among the top families;
   - no bound family uses keys 0, 1, 10 or 15;
   - no `freqBenefiting` exceeds the family carrier frequency;
   - at least 10 hand-inspected examples in the report render correctly.

---

## 9. Final report to the user (then stop)

Give a short summary:
- the top 15 bound families (members, keys, RTFCRE, gain, benefit share);
- the unbound families that are notable, and why;
- the constants used;
- anything in this spec you had to decide yourself.

Do not commit. The user reviews the `review` column and decides the next iteration (Phase 3:
integration before S7, the exporters, the docs).

## 10. Out of scope

- Any change to the pipeline or the exports, `dictionary.py`, the docs under `docs/` (the
  `GLOSSARY.md` terms come with Phase 3), and `ROADMAP.md`.
- Composing prefix and suffix bindings in the same word.
- Optimizing the assignment with CP-SAT (only if the greedy B5 is clearly poor; report it
  instead).

## 11. Reference: OQLF's prefix/suffix table (added 2026-09-27)

[Office québécois de la langue française, "Tableau des préfixes et suffixes"](https://www.oqlf.gouv.qc.ca/prix-concours/creativite-lexicale/contenu-pedagogique/tableau-prefixes-suffixes.aspx)
(fetched 2026-09-27) lists the affixes a French speaker recognizes as *semantically load-bearing*
morphemes -- each with a meaning, not just a spelling pattern. Kept here (not in `docs/`, per §10)
because it's reference material for this measurement phase, not a pipeline artifact.

**Use:** a discovered family should map onto zero, one, or several of these named affixes -- never
straddle two of them by accident. It's the check the resume's "`-cier` does not fit with the `-ion`
endings" finding was reaching for by hand (`RESUME_2026-09-26-affix-scan-state.md`, "Open problems
... `unifyFamilies`"): `-tion`/`-ssion`/`-sion` are all the OQLF's `-ion` ("action ou résultat de");
`-cier`/`-cieux`/`-rrier`/`-rier` are not that suffix at all (they share only a trailing `s`/`j`
sound), so a merge that pools them under one keypress is pooling by phonological accident, not by
shared meaning. Whenever `unifyFamilies` or A7's structural pooling produces a family, cross-check
its members against this table (or against `-ité`, `-ment`, `-eur`/`-euse`, etc. as the closest
named affix) before accepting the merge; a family with no entry here backing it deserves the
per-member similarity floor the resume already flagged as missing.

The table, for reference (kept short -- OQLF's page has the full explanations):

**Prefixes:** a- (absence), anté- (before), anti- (against), auto- (self), co- (together), dé-
(removal/reversal), dis- (separation), ex- (outside of), extra- (beyond), in- (negation), inter-
(between), intra- (inside), mé- (badly), morpho- (form), multi- (several), pan- (all), pluri-
(multiple), post- (following), pré- (before), re- (repetition/return), semi- (half), sub- (below),
sur- (above/excess), trans- (across), ultra- (beyond), vidéo- (image).

**Suffixes:** -able (able to be), -age (action/result), -ant/-ante (performing/possessing), -ard/
-arde (performer/quality), -erie (state/activity/place), -er (verb formation), -eur/-euse
(performer), -eux/-euse (possessing a quality), -ien/-ienne (origin/practitioner), -ier/-ière
(relating to/place of), -if/-ive (state/quality), -ion (action or result), -ique (relating to),
-isme (movement/theory), -iste (adherent/practitioner), -ment (manner), -té (state/quality), -ure
(action/result/state).

**Cross-reference:** `Tao.md` (repo root; the "Transcription assistée par ordinateur" French
sténotypie manual) is this project's other reference point -- its lessons' "Abréviations et
distinctions" sections are the canonical, hand-designed French steno abbreviations for many of
these same suffixes. Where a `Tao.md` abbreviation exists for a named OQLF affix, it's a second
data point (traditional practice, not a corpus measurement) to compare a discovered family's
keypress choice against, and a way to gauge how much of the *semantically important* affix
inventory this scan's thresholds actually reach versus miss.

## 12. Etymological research on confusable short prefixes (added 2026-09-27)

The OQLF table (§11) is a pedagogical list, too coarse to resolve short prefixes that *look*
related (same first 1-3 letters, close phonology) but may or may not actually be the same
morpheme. Researched via [Wiktionnaire](https://fr.wiktionary.org)'s per-affix entries
(`fr.wiktionary.org/wiki/<affix>-`), which give étymologie + sens + explicit assimilation rules;
cross-checked against [CNRTL](https://www.cnrtl.fr/) and the
[Dictionnaire de l'Académie française, 9e édition](https://www.dictionnaire-academie.fr/). Two
different failure modes turned up, not one:

- **`co-`/`con-`/`com-`/`col-`/`cor-`: one prefix.** Wiktionnaire's `con-` entry states the
  assimilation rule directly: con- → co- before a vowel, col- before `l`, com- before `b`/`m`/`p`,
  cor- before `r` (Latin *cum-*, "with/together"). Implemented 2026-09-27 as `A8` (below) --
  citation-backed, not auto-discovered, because it's a consonant *insertion/deletion*, not a
  substitution A7 or A3's Levenshtein can bridge.
- **`in-`/`im-`/`il-`/`ir-` (negation): also one prefix by the identical assimilation rule --
  but deliberately NOT pooled.** There is a second, unrelated Latin `in-` meaning "into/within"
  (*intérieur*, *induire*) sharing the exact same spelling; no phonological rule distinguishes
  the two senses, so pooling by spelling/phonology alone would sometimes merge the wrong prefix
  into the family. Left as separate, un-pooled candidates.
- **`di-`/`dis-`: confirmed genuinely different (user correction, 2026-09-27), and worse than a
  simple false-merge risk.** Greek `di-` = "two" (*dioxyde*, *dimorphisme*); Latin `dis-` =
  "undo/opposite" (*disparaître*) -- but Wiktionnaire's `dis-` entry also gives `di-` as `dis-`'s
  OWN allomorph before b/d/g/l/m/n/r/v (*divulguer* < *dis-* + *vulgare*). So a `di-`-spelled word
  can be either prefix, undistinguishable by spelling or phonology alone -- a lexical ambiguity,
  not resolvable by any merge rule; never auto-pool `di-` with anything.
- **`sub-`/`su-`: murkier than distinct (user correction, 2026-09-27).** `su-` genuinely is a
  `sub-` allomorph before s-initial Latin roots (*suspect* < *sub-* + *specere*; also `suc-`/
  `suf-`/`sug-`/`sup-` before c/f/g/p), but most real French `su-` words (*super*, *sujet*,
  *sucre*, *sud*) are not `sub-` derivatives at all -- `su-` as a bare spelling is mostly
  coincidental. Same practical risk as `di-` (never auto-pool), different cause (mostly
  coincidence rather than a genuine second prefix).

### A8. Known-affix-group pooling (`src/affixes.py`, `KNOWN_PREFIX_ASSIMILATION_GROUPS`)

Runs alongside A7 in `buildCandidates`, before the thresholds: `poolKnownAffixGroups` pools the
raw k=1 prefix candidates whose ortho is in one of a small, hand-curated, citation-backed list of
groups (currently just `{co, con, com, col, cor}`). Unlike A7 (structural: same tail, onset
substituted) this is a lookup against real etymology, because the co-/con- relationship is a
consonant insertion/deletion A7's mechanism can't express. Verified on the real lexicon: pools to
423 lemmas, freq 3629.4 (`co+col+com+con+cor`). `in-`/`im-`/`il-`/`ir-` is deliberately absent from
the list (see above); `di-`/`dis-` and `sub-`/`su-` must never be added.

## 13. A9 — iterative breadth-first affix growth (added 2026-09-27)

A7 pools same-`k` candidates that differ only in the onset consonant of the syllable nearest the
stem (one fixed hop, one fixed generalization rule). The user asked (2026-09-27 session) for the
general case: starting from a validated affix (e.g. `-ité`), can the algorithm discover, by
growing outward one syllable at a time and generalizing over whatever it finds there (a single
phoneme value, a hand-pickable subset like `{i, a}` for `-ilité`/`-alité`, or the full attested
set like A7's onset pooling), that a wider pattern (`-Cilité`, then perhaps `-VCilité`) is itself
a low-conflict family, worth keeping either as its own keypress or merged into the parent's?

**The growth graph.** A node is a partially-generalized affix: a fixed tail (the validated base,
e.g. `lité`) plus zero or more absorbed slots going outward toward the stem, each slot a
non-empty subset of the phoneme values actually attested there (never a hypothesized value with
no carrier). A **growth edge** absorbs one more syllable, instantiated per attested value (this
is exactly today's per-word exhaustive discovery, scoped to one base candidate's own carriers). A
**generalize edge** unions sibling per-value leaves at that slot into one wildcarded group.

**Conflict, and why zero-conflict is the wrong bar (user's 2026-09-27 answer).** Generalizing a
slot away means the steno stroke no longer records which attested value filled it. That is only a
problem when two *different lemmas'* carriers, once you drop the slot's specific value, would
share the exact same remaining stem stroke — an unresolvable collision. The user's rule: **some
conflict is fine.** The carriers it would create a collision for simply don't get the abbreviated
entry (they keep their full, unabbreviated outline, per Decision 1) — they become **exceptions**.
The only requirement is that exceptions stay a small minority of the group's frequency, because
each exception is one more thing a person has to memorize instead of infer from the rule.
Concretely this reuses `SPLIT_MAX_LOSS` (2%, already the bound the family binder uses for the same
kind of decision — when to split a family into sub-groups) as `GROWTH_MAX_EXCEPTION_SHARE`, rather
than inventing a second constant for the same idea.

**Algorithm** (`growAffixes`, `src/affixes.py`, run after A7/A8, using only each base candidate's
own `carriers` — no full re-scan of the lexicon):

1. **Leaves.** For a base candidate, grow every carrier by one syllable (fails, and the carrier is
   dropped, once the record has no stem syllable left to absorb); bucket the grown carriers by the
   absorbed syllable's exact phono value.
2. **Generalize, greedily, by lowest resulting exception share.** Repeatedly merge the pair of
   current groups whose union has the lowest exception share (carriers on a stem stroke shared
   with a different-lemma carrier in the same union; only the union's highest-frequency lemma on
   that stroke keeps the abbreviation, the rest become exceptions), stopping a merge only when
   even the best remaining pair would exceed `GROWTH_MAX_EXCEPTION_SHARE`. This can merge a bare
   onset variant (A7's case), a hand-picked vowel subset (`{i, a}`), or the full attested set,
   whichever the data supports — it is not told in advance which shape to look for.
3. **Threshold each surviving group** exactly like any other candidate (`MIN_CARRIER_LEMMAS`,
   `MIN_STEM_ROOTS`, `MIN_CANDIDATE_FREQ`, computed on the carriers that are not exceptions); keep
   it as a new generalized Candidate (`isGeneralized`, `grownDepth`, `exceptionCount`,
   `exceptionFreq`) alongside the base candidate that produced it — both stay in the pool, so the
   existing family-clustering and sub-group binder (unchanged) still make the final
   keep-separate-or-merge-with-parent call, the same as any other pair of family members.
4. **Breadth-first, not depth-first.** All depth-1 groups across all bases are generalized and
   thresholded before any depth-2 growth is attempted, up to `GROWTH_MAX_DEPTH`. A group that
   fails its threshold is a dead end (deeper growth of a subset can only lose carriers, never
   gain them, since depth-*d* carriers are always a subset of depth-(*d*-1)'s); it is not kept and
   not grown further, but it does not block sibling groups at the same depth.

**Scope note.** The collision check inside `growAffixes` is a Part-A pre-filter, scoped to one
candidate's own carriers — it is not the authoritative safety check. That remains Part B's
`simulate()`/binder collision handling, which still runs on whatever grown candidates survive into
a family, exactly as it does for every other candidate.

**Implemented and tuned 2026-09-27.** Two bugs found against the real lexicon before it was usable:

- *Runtime* (`_growOneLevel`'s merge loop recomputed the full O(g^2) pairwise matrix every
  iteration, making one growth level O(g^3); fixed by an incremental scheme that only recomputes
  pairs touching the just-merged group, O(g^2) total).
- *Exception-share dilution* (the merge criterion measured a candidate merge's exception share
  against the merged group's own, ever-growing total frequency; once a group got big, one more
  straggler barely moved the ratio, so a greedy sequence swallowed almost everything — observed
  as a single suffix family absorbing 50+ unrelated variants). Fixed by measuring share against
  the *base candidate's* fixed total frequency instead (`_exceptionShare`'s `denom` parameter).

Even after both fixes, growth alone (any depth, `GROWTH_MAX_SLOT_VALUES=8` capping how wide one
wildcard group can get) still produced 500-800 families against the existing pipeline sanity bound
of 5..300 — capping growth depth from 3 to 1 barely moved the count, so the volume was not coming
from recursing deep, it was from trying to grow all ~140 kept candidates and keeping every
surviving group per base. User's answer (2026-09-27): hold grown candidates to a higher bar than
organically-discovered ones, rather than restricting which bases are eligible or keeping only one
group per base. Landed at **7x** `MIN_CARRIER_LEMMAS`/`MIN_STEM_ROOTS`/`MIN_CANDIDATE_FREQ`
(`GROWTH_MIN_*` constants) — the lowest multiple of the ones tried (2x: 561 families, 5x: 328, 6x:
311, 7x: exactly 300, the sanity bound's own ceiling) that stayed inside the existing bound.

**Verified on the real lexicon**: 300 families (at the ceiling), 674 tests pass, mypy clean, Part A
runtime ~72s (up from ~5-10s pre-A9; still a hand-run diagnostic, not a pipeline step). Confirmed
doing what it was designed for: growing the A7-pooled `·ilité` (k=3, 127 lemmas: `biliter, bilité,
cilité, cillité, gilité, nilité, quillité, rilité, tilité, vilité`) one syllable further finds
`·[a|bi|cia|gi|na|nna|ri|ti|tia|va]lité` (k=4, 44 lemmas: `réalité, responsabilité, personnalité,
culpabilité, spécialité, ...`) — a wildcard mixing a bare vowel (`a`) with several
consonant-initial syllables, discovered from the data rather than assumed in advance, exactly the
`-alité`/`-ilité`-style grouping the user asked whether the algorithm could find. A shallower
example: growing the base `·ité` (k=2, 510 lemmas) once finds `·[ber|cié|cu|ffron|fron|li|lli|nau|
ni|nni|ti|tié]té` (140 lemmas: `liberté, société, réalité, identité, unité, ...`).

Not yet done: Part B (family unification + binder) has not been re-run with A9 in the mix, so
whether grown candidates end up sharing a keypress with their parent or splitting off, and what the
real (Part-B-verified, not Part-A-heuristic) collision picture looks like, is still open.
