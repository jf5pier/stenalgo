# Resume: affix abbreviation scan, state after review round 1 (2026-09-26)

Continuation notes for after a `/clear`. Spec: `PLAN_2026-09-26-affix-abbreviations.md` (its 10
decisions still bind). Nothing committed; measurement and proposals only. Use `env/bin/python`,
run from the repo root, serialize heavy runs (7 GB RAM).

## Status
Implemented and working: `src/affixes.py` (Part A + gain simulation), `src/affixbinding.py`
(Part B + family unification), `util/affix_scan.py` (CLI), `resources/affixSeeds.tsv`,
`src/test/affixes_test.py`, `src/test/affixbinding_test.py`. `pytest src/test/` = 665 pass; mypy
clean on the three new modules; pipeline artifact md5s unchanged (baseline
`scratch/affix-md5-before.txt`).

2026-09-27: added generalized-affix pooling (A7 -- see `PLAN_2026-09-26-affix-abbreviations.md`
§4 "A7" for the algorithm and §11 for the new OQLF prefix/suffix reference table + `Tao.md`
cross-reference, both added this session) to `src/affixes.py`
(`poolTailVariants`/`_onsetRest`, called from `buildCandidates` right before the thresholds).
Candidates of the same position/k whose syllable nearest the stem differs only in its onset
consonant (same nucleus+coda, same invariant tail beyond it -- `bi`/`ti`/`ci`/.../`li.te`) are
pooled into one candidate before `MIN_CARRIER_LEMMAS`/`MIN_STEM_ROOTS`/`MIN_CANDIDATE_FREQ` apply,
so rare spelling variants clear the thresholds together. Verified on the real lexicon: 347
generalized candidates now kept (candidates.tsv has a `generalizedFrom` column); `-ilité` pools 10
variants (`biliter, bilité, cilité, cillité, gilité, nilité, quillité, rilité, tilité, vilité`,
127 lemmas, freq 126.0) automatically, matching the manual investigation below. Caught and fixed
a key-collision bug in the first version (two different tails' pooled candidates could compute
the same synthetic ortho/phono and silently overwrite each other in the dict -- fixed by folding
the shared `rest` phono into both the ortho label and the phono key). `pytest src/test/` = 670
pass (5 new tests, `TestGeneralizedAffixPooling`). `python -m util.affix_scan --part a` still
completes (267 families, within the 5..300 sanity bound); Part B (full binder + unify, ~5 min)
not re-run after this change.

```
PYTHONPATH=. env/bin/python -m util.affix_scan [--refresh] [--part a|b|all] [--seeds-only] [--no-unify]
```
Part A ~5 s from the records cache (first load ~45 s); Part B ~1 min without unification,
~5 min with it. Outputs under `scratch/`: `affix-records.pickle`, `affix-families.pickle`,
`affix-candidates.tsv`, `affix-families.tsv` (empty `review` column for the user),
`affix-merges.tsv`, `affix_bindings.json`, `affix-bindings-report.md`.

## Changes made after the user's first review (all in the code now)
1. Competition (A4) counts only lemma-form carriers (no same-verb inflection "competition").
2. Family membership: a member needs >= 5% of the top member's lemma count (`MEMBER_MIN_SHARE`);
   this removed `rai`/`ran` from the re- family. Extra filter `MIN_STEM_ROOTS=5` (no visible effect).
3. **User rule: one family = one keypress.** The binder tries a single keypress for the whole
   family first and splits into sub-groups (shared core + discriminator key) only when more than
   `SPLIT_MAX_LOSS=2%` of frequency is lost to collisions (`lostDistinction`/`markCostTooHigh`).
   Sub-groups now come from the collisions the simulation reports (`CarrierResult.partners`,
   `collisionSubgroups`); the stem-based competition colouring survives only as the diagnostic
   column `stemCompetitionSubgroups` (`Family.stemSubgroups`).
4. Mark cost now charges only marks beyond what the word's old homophone cluster already pays.
5. Nested affixes link (`NESTED_SIM=0.8`, up to 3 extra letters): -ité inside -bilité, -tion
   inside -ation.
6. `unifyFamilies` (B): merges same-position families when one keypress for the union keeps
   `MERGE_KEEP=0.9` of the ORIGINAL separate gains, cosine of salient phonemes >= 0.75, union
   `sim` >= max(SIM_MIN, 0.9 x weaker part), <= 16 members, single sub-group. Last run: 85
   merges accepted, 147 rejected; 175 families, 156 bound.

## Open problems the user raised or that I found (do these next)
- **-cier does not fit with the -ion endings** (user) -- CROSS-CHECKED 2026-09-27 against the OQLF
  table, `scratch/oqlf-crosscheck-report.md`. Of the 36 merges chained into the post-A7 run, ~7 are
  clean (`-ment`, `-ion`, `-ant/-ance/-ence`, `-able/-ible`, `-eur/-euse`, `-ure/-tude`, `-al`),
  ~13 are a real affix polluted by riders (worst: `S038+S102+S109+S079`, `-ité`/`-iste` mixed with
  unrelated `-ette`/`-el`/`-uel`), ~16 are pure phonological accidents with no OQLF backing at all
  (almost all short common-syllable **prefixes**: `se-/es-/su-`, `ja-/je-/jo-`, `fa-/fi-/fo-`,
  etc. -- `unifyFamilies` didn't create this, it compounds already-loose A2d families).
  Tried a hard per-member `candidateSim` floor as an automatic merge gate: it correctly rejects the
  bad chains, but it ALSO rejects good ones (`-tion`/`-isation`, `-ment`/`-ablement`) because
  length-normalized Levenshtein punishes a short affix against a longer elaboration of the *same*
  affix. Reverted the gate; shipped `orphanMembers()` (`src/affixbinding.py`) as a non-blocking
  diagnostic instead -- every merge in `affix-merges.tsv` now has an `orphanMembers` column for
  manual review. `pytest src/test/` = 672 pass.
- **Other unrelated merges** in `scratch/affix-bindings-report.md`: -ment with -mir/-mie/-miner
  (S002+S029+S056), `si`/`ci`/`assu` at sim 0.27, `voir` with `rie`/`rir` -- same pattern, now
  visible via the `orphanMembers` column above instead of needing to hand-inspect the report.
- **Loose prefix families (root cause of most "no OQLF backing" merges above).** A2d's
  morphological filter lets bare common syllables (`se-`, `ja-`, `fa-`, `vi-`, ...) through as
  "prefix" candidates with no real meaning; `unifyFamilies` then pools several of them together
  because their aggregate phoneme profile is close. Not fixed -- worth tightening A2d itself
  (require the stem to be a MUCH more clearly independent word, or drop single-syllable prefix
  candidates below a stricter lemma-diversity bar) rather than patching it at the merge stage.
- **`re-`/`ré-`/`ren-`/`rem-` (user's question) -- already fine, no fix needed.** Verified
  against real records: `rencontre`'s `ren` syllable is phono `@` (schwa), the same phoneme class
  as plain `re`'s `R°` and `ré`'s `Re` -- `candidateSim`'s existing vowel-class substitution
  already unifies them (`P002` in the real family set already contains all four). My first answer
  claiming this needed new nasal-vowel handling was wrong; corrected after checking the data.
- **`co-`/`con-`/`com-`/`col-`/`cor-` (user's follow-up "is there another one like re-?") --
  DONE 2026-09-27.** Researched via a subagent (Wiktionnaire, CNRTL, Académie française); see
  `PLAN_2026-09-26-affix-abbreviations.md` §12 for full citations. Confirmed one prefix
  (Latin assimilation rule), unlike three other candidates the user separately flagged as
  probably-different (`in-`/`im-`/`il-`/`ir-` -- same rule but a second unrelated "into" `in-`
  makes it unsafe to pool; `di-`/`dis-`; `sub-`/`su-`). Implemented as `A8`
  (`poolKnownAffixGroups`/`KNOWN_PREFIX_ASSIMILATION_GROUPS` in `src/affixes.py`) -- a small
  citation-backed lookup table, not a general mechanism (a general "consonant-insertion" pooler
  would also have caught `in-`/`im-`/`il-`/`ir-` and reintroduced the homograph risk). Verified on
  the real lexicon: pools to 423 lemmas, freq 3629.4. `pytest src/test/` = 674 pass.
- **Consonant+ilité variants (user's question).** The scan already generates `cilité`, `tilité`,
  `gilité`, `rilité`, `milité`, `vilité`, `nilité` as 3-syllable suffix candidates (the
  syllabifier attaches the consonant to the next vowel: fa|ci|li|té), but they all fall below
  the candidate thresholds (lemmas >= 5, stem roots >= 5, freq >= 20). Measured over lemma-form
  words ending -ilité: bilité 119 words / freq 89; tilité 10 / 9.4; rilité 3; gilité 2; cilité 4 /
  1.6; milité 1; vilité 2; nilité 2. So only `bilité` survives, and the `lité` (k=2) candidate
  already covers the -ilité words with one syllable less. TO DO: a "generalized affix" step that
  pools candidates sharing a tail (C+ilité, i.e. same last 2 syllables `li.te` with different
  first-syllable onset) into one candidate before the thresholds, then binds them to one keypress.
  Decide with the user whether a pooled `-ilité` should save 3 strokes for bilité-type words
  (the merged key encodes `li.te`, the consonant syllable stays) or only 2.
- **Investigate: can every consonant+ilité join the `bilité` family without conflict, and what is
  lost by doing so?** (user request) -- DONE 2026-09-27, `scratch/cilite-investigation-report.md`.
  Verdict: yes, clean. Pooling `bilité, tilité, rilité, gilité, vilité, cilité, nilité` (7 of the 8
  named candidates still exist; `milité` no longer has a lemma-form carrier) into one family gives
  zero competing pairs, one merged keypress (`-jtl`, sim 0.741), strokeFreqSaved 357.2,
  freqBenefiting 99.2% by frequency, only 2 `keyOverlap` fallbacks, zero `lostDistinction`/
  `markCostTooHigh`/boundary risks. The consonant is fully absorbed (3-stroke gain, not 2) because
  the stem before it always already disambiguates carriers (checked `facilité`/`fragilité`
  directly: different neighbour strokes `fa` vs `fra`). Net new win over what production's `lité`
  (k=2) binding already covers is small (~9 stroke-units, the 6 tiny variants upgraded from 2- to
  3-stroke savings) but the pattern generalizes -- recommends a real "generalized affix" Part-A
  step (pool same-tail candidates before the thresholds) rather than one-off hand pooling.

- Verb-inflection families (-ter/-té/-tant, -ser, -der, -rer...) are still in the scan, and some
  still get 2 keypresses (`etZm;@tZm`). Question asked earlier and unanswered: exclude
  conjugation endings from the scan since S6 already carries them?
- Sub-syllabic prefixes (r- before a vowel-initial stem, user's remark on `rai-`) not built.
  `ren-`/`rem-` still in the re- family; `re` appears 3 times (3 pronunciations `R°`, `R2`, `Re`).
- Loose morphological filter (spec A2d) lets false families through: a- (avoir/voir), -ter, -ser.
- `records`: 381 words skipped (prototype: 56) because syllable letters do not concatenate to the spelling.
- Keypresses have low similarity (mostly 0.35-0.75); discriminator keys are unexplained by design.

## Decisions I took beyond the spec (report these to the user)
Cap of 1500 candidates per position for clustering; `sim` normalization includes the
unexplained-key penalty; sub-group `sim` scores the shared core only; first-pass simulation
samples the top 2000 carriers, finalists use all; dedicated strokes have no `SIM_MIN`; the
B5 conflict test follows the spec literally; inherited partial suffix spans get the whole
family's keypress; original mark keys are re-applied to the new last stroke when rendering.

## A9 -- iterative breadth-first affix growth (added 2026-09-27, see PLAN §13)

Implemented and tuned against the real lexicon: `growAffixes`/`_growOneLevel`/`_growCarrier`/
`_exceptionShare` in `src/affixes.py`, run at the end of `buildCandidates`. Starting from any kept
candidate, grows it one syllable at a time (up to `GROWTH_MAX_DEPTH=3`) and generalizes over
whatever is found there via greedy conflict-based merging (exception share vs the *base
candidate's* fixed frequency, capped at `GROWTH_MAX_EXCEPTION_SHARE=0.02`, mirroring
`affixbinding.SPLIT_MAX_LOSS`; merges also capped at `GROWTH_MAX_SLOT_VALUES=8` distinct values).
Grown candidates are held to **7x** `MIN_CARRIER_LEMMAS`/`MIN_STEM_ROOTS`/`MIN_CANDIDATE_FREQ`
(`GROWTH_MIN_*`) -- needed because 1x-2x flooded the family count (561-828 vs the 300 sanity
ceiling; capping growth depth to 1 barely helped, so the volume came from trying all ~140 bases
and keeping every surviving group per base, not from recursing deep). `pytest src/test/` = 674
pass, mypy clean, Part A: 300 families (at the ceiling), candidates 1016, runtime ~72s (up from
~5-10s pre-A9). Verified real find: growing the A7-pooled `·ilité` (127 lemmas) one syllable
further gives `·[a|bi|cia|gi|na|nna|ri|ti|tia|va]lité` (44 lemmas: réalité, responsabilité,
personnalité, culpabilité, spécialité) -- a vowel (`a`) pooled with several consonant-initial
syllables, found from the data, matching the user's `-alité`/`-ilité` question.

**Part B run 2026-09-27, found a real bug, fixed it (see below).** First run: the un-grown `·ilité`
family got fuzzy-merged (by `unifyFamilies`, unrelated to A9) into a 10-member grab-bag (`·ilité,
·alité, ·aliste, lette, ·icité, rette, tuel, tel, quette, nnette`) BEFORE it ever had a chance to be
compared against its own A9-grown child `·[a|bi|cia|gi|na|nna|ri|ti|tia|va]lité` -- `unifyFamilies`
only compares each family to its top-`MERGE_PARTNERS` nearest neighbours by raw phoneme-salience
cosine per round, greedily accepts the globally-best pairs, and once a family is consumed into a
merge its original identity is gone for later rounds. Traced via `scratch/affix-merges.tsv`: the
chain merged at cosines 0.77-0.82, each retaining ~98-100% of separate gain (MERGE_KEEP=0.9 was
never the problem -- these merges were nearly free, just semantically unrelated), and the true
parent/child pair (`·ilité` vs its own grown extension) never appeared in the log at all.

**Fix, implemented and verified 2026-09-27:**
1. **`growthMerges`** (`src/affixbinding.py`, new function, run before `unifyFamilies` in
   `util/affix_scan.py`'s `partB`): uses `Candidate.grownFromKey` (new field, set by
   `_growOneLevel`, the exact base a grown candidate came from) to try merging a grown candidate's
   family with its true base's family FIRST, before the generic cosine search can consume either
   into an unrelated chain. Held to `GROWTH_MERGE_KEEP=0.98` (much stricter than the general
   `MERGE_KEEP=0.9`), since this is a KNOWN relationship, not an inferred one -- a merge here should
   be nearly free.
2. **`unifyFamilies` tightened**: `MERGE_SIM_MIN` 0.75 -> 0.85, `MERGE_MAX_MEMBERS` 16 -> 8
   (mirrors `GROWTH_MAX_SLOT_VALUES=8`'s "unlearnable width" principle).

**Verified on the real lexicon**: `growthMerges` correctly traced `S064`'s real lineage and
correctly REJECTED the merge (gain would drop to 82.5% of separate, well under 98%) -- the right
call, not a bug. `unifyFamilies` merges dropped from 70 accepted/224 rejected to **10 accepted/35
rejected**; `·ilité`'s grab-bag shrank to a defensible 3 members (`·ilité, ·alité, ·icité`), still
one keypress (`-stl`), still saving 3 strokes for `responsabilité`. 674 tests pass, mypy clean, 300
families at Part A (unchanged, growth logic itself untouched).

**Known remaining gap (not fixed, flagged to the user):** `S064` and `-ilité`'s family (`S050`)
still both claim `responsabilité` with different results (`S050`: 3 strokes via `-stl`; `S064`: 4
strokes via `-jst`, worse) -- `growthMerges` never compares them because there is no *direct*
lineage edge between them: `S064` actually grew from a different intermediate wildcard candidate
that happens to heavily overlap `-ilité`'s carriers by coincidence of two independent growth paths,
not a traced parent/child relationship. General overlap reconciliation (pick one winner per word
across ANY two candidates with high carrier overlap, not just true lineage pairs) is unbuilt and is
the natural next task if this line of work continues.

**Two follow-up questions answered 2026-09-27, both led to real findings:**

1. **"Does `-ité` ever grow into `-ilité`?" No, and the reason is a real algorithm gap.**
   `-ilité` is one of 8 individually hand-typed variant seeds in `resources/affixSeeds.tsv`
   (`ité, rité, ilité, bilité, bité, vité, cité, sité`, one comment tag, no growth relationship at
   all). The organic path would be `-té`(k=1, real, 566 lemmas) -> grow absorbing "li" -> `-lité`
   (k=2) -> grow absorbing "i" -> `-ilité`(k=3). Checked `scratch/affix-candidates.tsv`: `-lité`
   (exact `li.te`, k=2) **does not exist anywhere** -- growth's greedy merge pooled "li" together
   with 7 phonetically unrelated syllables (`bER, fR§, ky, ni, no, sje, ti`) into one wildcard at
   the first merge step, because that pairing happened to be cheap (low exception share), before
   "li" ever got a chance to survive alone as a candidate a later growth step could extend. This is
   the real gap: `growAffixes` does a single GREEDY agglomeration per base (one committed
   partition), not the breadth-first exploration of parallel hypotheses the user originally asked
   for (2026-09-27, earlier in the session) -- a true BFS would keep both the merged-wildcard
   branch and the singleton-"li" branch alive, each independently growable. Not fixed; a real
   algorithm limitation, not a threshold or premise problem.
2. **"Why did S026+S064 lose 17.5% gain -- new conflicts?" No conflicts at all -- a bug in
   `growthMerges`' own accounting, now fixed.** Reconstructed the exact computation
   (`scratch/investigate_growth_merge.py`): zero carriers lost gain, zero fallback reasons. Since
   `S064`'s 96 carriers are a strict subset of `S026`'s 306 (S064 grew FROM S026), the naive
   `ga + gb` baseline (649.1 + 344.7 = 993.8) double-counted the overlap -- crediting the same 96
   words once at their shallow (k=2) saving and again at their deep (k=3) saving, though a word can
   only ever be typed one way. The fair baseline (each word counted once, at its best available
   saving) is 821.5, and the union's real gain (820.4) retains 99.9% -- essentially lossless. Fixed
   `growthMerges` (`src/affixbinding.py`) to compute the baseline as a per-carrier max across the
   two options instead of a naive sum. Verified: growth merges went from 1 accepted/26 rejected
   (buggy) to **5 accepted/20 rejected** (correct) -- `S004+S045`, `S008+S073`, `S022+S082`,
   `S026+S064`, `S034+S057` all now correctly accepted (all >=98% retention); the remaining 20
   rejections show genuine large losses (e.g. `S001+S008`: 8294.4 -> 6231.7, 75% retention),
   confirmed real, not measurement artifacts. 674 tests pass, mypy clean.

## Not started (spec section 10 / later phases)
Integration before S7, exporters, docs (`docs/GLOSSARY.md` terms), ROADMAP, any pipeline
change, prefix+suffix composition in one word. Do not commit or push unless asked.
