# Consonant+ilité pooling investigation (2026-09-27)

Question (RESUME_2026-09-26-affix-scan-state.md, "Investigate: can every consonant+ilité join
the `bilité` family without conflict"): pool `bilité`, `tilité`, `cilité`, `rilité`, `gilité`,
`milité`, `vilité`, `nilité` (all suffix candidates, k=3, phono `C.li.te`) into one candidate and
bind the pooled family to one keypress; measure what's lost.

Method: temporarily zeroed the Part-A thresholds (`MIN_CARRIER_LEMMAS`/`MIN_STEM_ROOTS`/
`MIN_CANDIDATE_FREQ`) to pull in the below-threshold variants, built one `Family` directly from
the 7 that exist as candidates (no `nilité`... it exists too, see below), and ran the normal
`familyOptions`/`simulate` pipeline unchanged. Script kept at hand, not committed (measurement
only, per the module docstrings).

## What was pooled

| member | lemmas | freq | examples |
|---|---:|---:|---|
| bilité | 110 | 111.0 | responsabilité, possibilité, culpabilité, sensibilité |
| tilité | 7 | 6.3 | hostilité, fertilité, inutilité, subtilité |
| rilité | 2 | 1.6 | stérilité, puérilité |
| gilité | 1 | 1.2 | fragilité |
| vilité | 1 | 0.0 | servilité |
| cilité | 2 | 0.0 | gracilité, indocilité |
| nilité | 1 | 0.0 | juvénilité |

All 7 candidates exist (the resume's list of 8 included `milité`, which no longer has a lemma-form
carrier in the current lexicon -- likely a spelling-variant/lexicon change since the note was
written; not investigated further, doesn't change the verdict). Combined: 124 lemmas, freq 120.0,
252 pooled carriers, upper bound 360.1 stroke-units.

## Result: clean pool, one keypress, all 3 strokes

`buildFamily` over the 7 candidates finds **zero competing pairs** and **one stem-competition
subgroup** (all 7 members together) -- no two members ever share a stem, so nothing forces a
split before simulation even runs.

`familyOptions` picks a single merged keypress for the whole pooled family without any subgroup
split:

- keys `(16, 20, 23)` = `-jtl` (rtfcre), sim 0.741, comfort 539.1
- **strokeFreqSaved 357.2**, freqBenefiting 119.1 of 120.0 family freq (**99.2% by frequency**,
  ~97% by word count)
- fallbacks: `{'keyOverlap': 2}` only -- two rare words where the merge key collides with a key
  already used by the neighbouring stroke (no gain for those two, not a correctness problem)
- **zero** `lostDistinction`, **zero** `markCostTooHigh`, **zero** boundary risks

Every carrier that benefits gets `gain=3` (the full k=3 span), because `MERGED` binding absorbs
the whole affix span into the neighbouring stroke regardless of which member it is.

## Why no conflict: the consonant is never load-bearing

The pooled key encodes only `li.te` (plus one extra key for comfort); it does **not** encode which
consonant preceded it. That's safe here because the stem *before* the consonant syllable already
disambiguates every pair that could otherwise collide -- checked directly on the pair the resume
named:

- `facilité` (`faciliter`): stem `fa`, base strokes `(fa)(ci)(li)(té)`
- `fragilité`: stem `fra`, base strokes `(fra)(gi)(li)(té)`

`fa` and `fra` are different neighbour strokes (`(2,4,12)` vs `(2,4,8,12)`), so the merged outlines
never collide even though `ci` (facilité) and `gi` (fragilité) both vanish into the same key. This
generalizes: nothing in the 252-carrier pool produced a `lostDistinction` fallback, so no pair of
real French words differs *only* in the C+ilité consonant with an otherwise-identical stem.

## (a) Does the consonant stay as a stroke, or get absorbed?

**Absorbed.** The winning binding is `MERGED`, not a core+discriminator split, so all 3 affix
strokes (consonant syllable + `li` + `té`) disappear into the neighbouring stroke -- 3 strokes
saved per word, not 2. A discriminator-per-consonant split was never needed: `familyOptions` only
reaches for `subgroupOption` when `collisionSubgroups` finds real collisions (`SPLIT_MAX_LOSS`
exceeded), and here `conflictShare == 0.0` for every one of the top 5 merged alternatives.

## (b)/(c) Versus the existing `lité` (k=2) binding

The production scan already binds a much larger `lité`-family (`S016`: `lité, rité, bilité, nité,
cité, sité, vité, mité, dité, bité`, keys `[14,20,23]` = `etl`, strokeFreqSaved 1500.6) which
**already includes `bilité` as a k=3 member** (unified there by `unifyFamilies`, not because of
this investigation) and covers every C+ilité word at least as a 2-stroke `lité` (k=2) carrier,
since a word's last two syllables (`li.te`) are literally the `lité` candidate regardless of the
preceding consonant.

So pooling does not create carriers that didn't already exist -- it **upgrades** the 6 small
variants (`tilité, rilité, gilité, vilité, cilité, nilité`: 14 lemmas, freq ~9.1 combined,
currently either falling back to the 2-stroke `lité` gain or, if not covered there either,
un-abbreviated) from 2-stroke to 3-stroke savings, at **zero measured conflict cost**. The
absolute win is small in isolation (~9 stroke-units) but the pattern -- pool spelling variants of
one suffix's leading consonant before running the thresholds, rather than requiring each spelling
to independently clear `MIN_CARRIER_LEMMAS`/`MIN_CANDIDATE_FREQ` -- generalizes to any suffix
family with a variable onset consonant, and is worth doing as a real Part-A step (see the resume's
"generalized affix" TODO) rather than a one-off pool.

## Verdict

Pooling all consonant+ilité variants into one family and binding it to one keypress is safe and
strictly better than leaving the small variants unbound or under-abbreviated: no lost distinctions,
no extra marks, no boundary risks, 99.2%-by-frequency coverage, full 3-stroke gain for every
member including the tiny ones. Recommend implementing the "generalized affix" pooling step
(pool candidates sharing a tail before the Part-A thresholds) rather than merging by hand.
