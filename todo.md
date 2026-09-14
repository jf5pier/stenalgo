# Todo

Written to survive a `/clear` — read this file first in a fresh session before doing
anything else on the lexicon-defect triage work. Branch: `cl_test_coverage`.

## Session status as of this note

The lexicon/Verbiste-template defect triage (see `util/validateLexiconAgainstVerbiste.py`,
a read-only cross-checker never touched by any fix script) is functionally complete for
everything mechanical or single-answer-confirmable. Total flags: **536 → 134**, all 346
tests pass throughout, and `resources/LexiqueSynthetic.tsv` regenerates cleanly (0
orthosyll_cv/ortho mismatches across 51,963 rows, via
`rm -f resources/LexiqueSynthetic.tsv && python -m util.completeVerbParadigms --apply`).

**All of the above was committed** in `e3b0358` ("Fix Verbiste template/lexicon defects
flagged by cross-checker"). Do NOT re-stage/re-commit that work; check `git log` /
`git status` for what's new since.

Since that commit: `util/fixPayerDualFormGaps.py` was added and run with `--apply`,
appending generated pa:yer "i"/"y" counterpart rows (phon + syllable breakdown,
`source=synthetic`) to `resources/LexiqueSynthetic.tsv`. Per the user's explicit direction,
these went to `LexiqueSynthetic.tsv`, NOT `LexiqueMixte.tsv`.

**DECIDED, permanent: `resources/LexiqueSynthetic.tsv` will NOT be wired into
`resources/LexiqueMixte.tsv`.** This is no longer an open question — do not revisit it,
do not do the wiring. Consequence: `util/validateLexiconAgainstVerbiste.py`'s
WRONG_ENDING counts for pa:yer/ass:eoir will never drop by generating rows into
`LexiqueSynthetic.tsv` alone; that's expected and fine, not a bug to chase.

Remaining flags are two deferred architectural items (below) plus one non-issue kept only
for documentation (`pouvoir`/"puis") — no more open judgment calls or unexplained flags.

## Outstanding work (both items below are now resolved — kept for history/context)

- [x] **`-ayer` verbs (pa:yer template family) — fully done, all 77 gaps closed.** 34
  lemmas × 21 dual-alternation slots = 714 combinations: 76 both present, 45 only-i,
  32 only-y = 77 gaps, 561 legitimately absent (normal corpus sparsity, not a defect).
  `util/fixPayerDualFormGaps.py` (dry-run/`--apply`, idempotent) derived 71 of the 77
  by donor-borrowing (appending to `resources/LexiqueSynthetic.tsv`, requiring 100%
  donor agreement) — the "65 remain skipped" figure this file previously carried was
  stale, since this session's unrelated `pa:yer` E/e vowel-quality fix (done to unblock
  `python lexique.py`'s `LexiqueMixte.tsv` regeneration, nothing to do with this
  dual-form-gap track) happened to also fix most of the donor-agreement noise as a
  side effect. The final **3** were resolved by hand, same technique as the ass:eoir
  work: `paies` (payer, sub:pre:2s) turned out to be a tag-only gap (already existed
  as an `ind:pre:2s;` row, just missing the tag its y-form sibling `payes` already
  combined — fixed at the `Lexique383.tsv` level); `déblaye` (imp:pre:2s) and
  `effrayes` (ind:pre:2s) hit the documented merged-vs-split syllable-tokenization
  free variation (`PAYER_SYLLCV_AUDIT.md` finding #4) when averaged across all 11/6
  donors, but resolve cleanly once matched against the ONE structurally closest
  sibling instead of a blind majority vote (`déblaye` mirrors `délaye`, identical
  single-consonant radical shape, already merged; `effrayes` mirrors `débrayes`/
  `embrayes`, identical consonant-cluster-before-r radical shape, already split).
  `util/fixPayerDualFormGaps.py` now reports 0 generated/0 skipped. 346 tests pass,
  `python lexique.py` regenerates clean.
- [x] **`ass:eoir` (asseoir/rasseoir, 25 WRONG_ENDING flags) — done, in the same
  not-yet-wired state as pa:yer above.** `surseoir` uses its own separate `surs:eoir`
  template and was never in scope. Unlike pa:yer's 26-lemma donor pool, only 2 lemmas
  (`asseoir`, `rasseoir`) share `ass:eoir`, so `util/fixAsseoirDualFormGaps.py`'s
  donor-borrowing approach (same technique as `fixPayerDualFormGaps.py`) found **0
  confident donors for all 26 candidates** — most missing forms have no cross-lemma
  attested sibling to borrow phon/syllables from at all, not a confidence-threshold
  problem. `util/inventoryAsseoirFormsCoverage.py` is the read-only inventory
  (generalizes `inventoryPayerFormsCoverage.py` to ass:eoir's 2-way AND 3-way "-oi-"/
  "-ie-"/"-eye-" alternation — futur/cnd has 3 alternatives, not 2).
  **Resolved by hand** (`util/fixAsseoirDualFormGapsManual.py`, applied): derived all 26
  from (1) same-lemma sibling transformations already visible elsewhere in
  asseoir/rasseoir's own paradigm, (2) the "-eye-" alternant being structurally identical
  to pa:yer's own "y"-form futur/cnd (`Ej°R`+ending — same grapheme, same rule this
  session already established for pa:yer), (3) cross-checking the "-oi-" imparfait
  1p/2p against regular `-oyer` verbs elsewhere in the lexicon (employer/envoyer/
  nettoyer) for how `oy`+`-ions`/`-iez` behaves. Split into 2 tag-only fixes to existing
  `resources/LexiqueMixte.tsv` rows (a sibling alternant already carried a tag the other
  was missing, e.g. `assoyons` lacked `imp:pre:1p;` that `asseyons` already had for the
  identical homophonous form) and 21 new rows appended to
  `resources/LexiqueSynthetic.tsv` (`source=synthetic`, same convention as pa:yer's 53
  rows — every generated `orthosyll_cv` verified to flatten back to its own `ortho`).
  346 tests pass, `python lexique.py` still runs clean. **Same caveat as pa:yer**:
  `util/validateLexiconAgainstVerbiste.py`'s ass:eoir WRONG_ENDING count stays at 25
  until `LexiqueSynthetic.tsv` is wired into `LexiqueMixte.tsv` — confirmed unchanged
  after this fix, expected, not a bug.

## Resolved this session (context, not action items)

- **`pouvoir`/"puis" (ind:pre:1s)**: NOT a defect — "puis" is the genuine classical/
  formal-register alternate of "je peux" (already correctly present, tagged
  ind:pre:1s;ind:pre:2s;), phonologically distinct (/pɥi/ vs /pø/). Same "dual valid
  conjugation" class as pa:yer/ass:eoir but both forms already coexist correctly — nothing
  to generate. This is why it will always show up as 1 residual SUSPECTED_WRONG_LEMME flag;
  that's expected, not a bug.
- Circumflex-accent questions for the croître family + mouvoir (originally deferred,
  since resolved with the user's help against Bescherelle): `croître` itself needs the
  circumflex to avoid colliding with `croire` (croîs/croit/crut/cru), but its compounds
  (accroître/décroître/recroître) only keep it in infinitive-derived forms (3s présent,
  futur, conditionnel) — not présent 1s/2s or the participle. `croître`'s own participle
  is "crû, crue, crus, crues" (circumflex ONLY on masculine singular, same minimal-
  disambiguation convention as `mouvoir`'s "mû, mue, mus, mues"). Fixed via
  `util/fixCroitreMouvoirAccents.py` + `util/fixOuirConditionnelOrder.py` (the latter for
  a leftover `o:uïr` conditionnel-ordering issue found along the way).

## If resuming from scratch (no memory of this session)

1. Read this file fully first.
2. Run `pytest src/test/` (expect 346 pass) and
   `python -m util.validateLexiconAgainstVerbiste` (expect 134 total flags: 108 pa:yer +
   25 ass:eoir + 1 pouvoir/puis — both counts are permanently frozen at these numbers,
   since `LexiqueSynthetic.tsv` will NOT be wired into `LexiqueMixte.tsv`, see above) to
   confirm the working tree still matches this note.
3. Both `pa:yer` and `ass:eoir` dual-form-gap work is done (see above) — there is no
   open item left on this lexicon-defect-triage track. If picking this file up again,
   it's most likely to check for regressions, not to resume unfinished work.
