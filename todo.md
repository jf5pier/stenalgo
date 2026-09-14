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
- [ ] **`ass:eoir` (asseoir/rasseoir/surseoir, 25 WRONG_ENDING flags)**: same situation as
  `-ayer` above. Both the "-oi-" model (assois/assoirai/assoie) and the "-ie-" model
  (assieds/assiérai/asseye) are already attested in `resources/LexiqueMixte.tsv` as
  separate rows for the SAME slots (e.g. both "assois" and "assieds" tagged ind:pre:1s;
  both "assoirai" and "assiérai" tagged ind:fut:1s) — phonologically distinct (/aswa/ vs
  /asje/), not homophones, so both are genuinely valid and neither should be discarded.
  Needs the same treatment as pa:yer: a read-only per-slot inventory (which of the two
  models exists vs. is missing, per lemma) before generating any missing counterpart
  rows. Breakdown of the 25 flags: ind:pre 9, sub:pre 5, ind:fut 4, cnd:pre 3, imp:pre 2,
  ind:imp 2.

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
   25 ass:eoir + 1 pouvoir/puis) to confirm the working tree still matches this note.
3. Decide with the user whether to commit the existing work before starting new fixes.
4. Pick up pa:yer or ass:eoir using the exact same workflow as every prior batch: dry-run
   script, present for approval, `--apply`, re-run tests + validator, confirm the
   targeted flag count drops as expected before moving on.
