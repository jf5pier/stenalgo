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

Everything applied is **uncommitted** (working-tree only), matching this session's earlier
established practice of holding commits for explicit instruction. Uncommitted tracked
files: `dictionary.py`, `requirements.txt`, `resources/Lexique383.tsv`,
`resources/LexiqueMixte.tsv`, `resources/verbiste/conjugations-fr.xml`,
`resources/verbiste/verbs-fr.xml`, `src/featureextractor.py`, `src/grammar.py`,
`src/greedyoptimizer.py`, `src/test/featureextractor_test.py`, `src/verbparadigm.py`,
`src/word.py`, `util/completeVerbParadigms.py`. Also uncommitted/untracked: every
`util/fix*.py` and `util/validateLexiconAgainstVerbiste.py` script written this session
(all dry-run-by-default, idempotent, documented in their own module docstrings — see git
diff / `ls util/fix*.py` for the full list, ~20 scripts). **Decide on committing** (this
plan's fixes, the pre-existing verbparadigm.py fixes 7-9 from before an earlier context
reset, and the regenerated LexiqueSynthetic.tsv) before doing much more work — the working
tree is large and uncommitted.

Remaining flags are two deferred architectural items (below) plus one non-issue kept only
for documentation (`pouvoir`/"puis") — no more open judgment calls or unexplained flags.

## Outstanding work

- [ ] **`-ayer` verbs (pa:yer template family, 108 WRONG_ENDING flags)**: both the "i"-form
  (balaie) and "y"-form (balaye) are phonologically distinct (/balɛ/ vs /balɛj/, confirmed
  with the user) and both need correct lexicon rows (ortho + phon + syllable breakdown)
  wherever missing — this is NOT a "pick the right spelling" template fix. Read-only
  inventory done (`util/inventoryPayerFormsCoverage.py`, dump written to
  `/tmp/payer_inventory.tsv` — regenerate if that scratch file is gone): 34 lemmas × 21
  dual-alternation slots = 714 combinations — 76 both present, 45 only-i-present (y
  missing), 32 only-y-present (i missing), 561 neither present (normal corpus sparsity,
  not a defect). **Next step**: generate the 77 missing counterpart rows (45+32),
  computing correct `phon`/syllable data (not just `ortho`) — dry-run first for approval,
  same workflow as every other fix this session.
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
