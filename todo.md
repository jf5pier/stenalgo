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
appending **53** generated pa:yer "i"/"y" counterpart rows (phon + syllable breakdown,
`source=synthetic`) to `resources/LexiqueSynthetic.tsv`. Per the user's explicit direction,
these went to `LexiqueSynthetic.tsv`, NOT `LexiqueMixte.tsv` — so
**`util/validateLexiconAgainstVerbiste.py`'s WRONG_ENDING count for pa:yer will NOT drop**
until `LexiqueSynthetic.tsv` is wired into `LexiqueMixte.tsv` (deliberately deferred, see
`completeVerbParadigms.py`'s module docstring — do not do this wiring without explicit
instruction, it's a separate scope decision). This latest change (the new script +
`LexiqueSynthetic.tsv` append) is **uncommitted** — decide with the user whether/when to
commit it, same practice as before.

Remaining flags are two deferred architectural items (below) plus one non-issue kept only
for documentation (`pouvoir`/"puis") — no more open judgment calls or unexplained flags.

## Outstanding work

- [ ] **`-ayer` verbs (pa:yer template family, 108 WRONG_ENDING flags)**: both the "i"-form
  (balaie) and "y"-form (balaye) are phonologically distinct (/balɛ/ vs /balɛj/, confirmed
  with the user) and both need correct lexicon rows (ortho + phon + syllable breakdown)
  wherever missing — this is NOT a "pick the right spelling" template fix. Read-only
  inventory: `util/inventoryPayerFormsCoverage.py` (dump written to
  `/tmp/payer_inventory.tsv` — regenerate if that scratch file is gone): 34 lemmas × 21
  dual-alternation slots = 714 combinations — 76 both present, 45 only-i-present (y
  missing), 32 only-y-present (i missing), 561 neither present (normal corpus sparsity,
  not a defect).
  **Progress**: `util/fixPayerDualFormGaps.py` (dry-run/`--apply`, idempotent) derives
  `phon`/`syll_cv`/`orthosyll_cv` endings per (slot, i/y-form) from every already-attested
  donor lemma, requiring 100% agreement (`MIN_MATCH_RATE = 1.0`, same bar as
  `completeVerbParadigms.py`) before generating a row, and appends results to
  `resources/LexiqueSynthetic.tsv` (per user direction — NOT `LexiqueMixte.tsv`). Applied
  once already: **53 rows generated and appended**. **65 remain skipped**: their
  `syll_cv`/`orthosyll_cv` donor agreement is <100% because the syllable-boundary encoding
  depends on the lemma's radical shape (number of trailing consonants before the vowel,
  e.g. "pa-" vs "débr-" vs "expr-") — a real structural difference, not noise. **Next
  step** (per user's own steer): improve the derivation by grouping donors by radical
  consonant-cluster shape before computing the per-slot ending, then re-run
  `util/fixPayerDualFormGaps.py --apply` for the remaining ~65. Re-running the script as-is
  today is a safe no-op (idempotent — checks both `LexiqueMixte.tsv` and the current
  `LexiqueSynthetic.tsv` before generating). Remember: even once all 118 are generated,
  the validator's WRONG_ENDING count won't move until `LexiqueSynthetic.tsv` is wired into
  `LexiqueMixte.tsv` (separate, deliberately out-of-scope decision — ask before doing it).
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
   25 ass:eoir + 1 pouvoir/puis — both counts are frozen until LexiqueSynthetic.tsv gets
   wired into LexiqueMixte.tsv, see above) to confirm the working tree still matches
   this note.
3. Decide with the user whether to commit the existing work before starting new fixes.
4. Only pa:yer's remaining ~65 dual-form gaps are still open (ass:eoir is done, see
   above). Pick up pa:yer using the exact same workflow as every prior batch: dry-run
   script, present for approval, `--apply`, re-run tests + validator, confirm the
   targeted flag count drops as expected before moving on. Otherwise, the next real
   decision is whether to wire `LexiqueSynthetic.tsv` into `LexiqueMixte.tsv` at all —
   ask the user first, it's explicitly out of scope until then.
