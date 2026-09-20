# Todo

Written to survive a `/clear` — read this file first in a fresh session.

## Live status (2026-09-20)

For the homophone-theory work (Phase 0 through Phase P milestone 1 and the `*`/`#`
lemma-homophone track), **`ROADMAP.md`'s "Status update (2026-09-20)" section and
`ATOMIC_KEYPRESS_REWIRE_PLAN.md` are authoritative** — do not reconstruct state from the
session notes below. The only still-open items tracked in THIS file are the lexicon
data-quality bullets in "Still open" below and the `"p"` vs `"f_p"`/`"m_p"` feature-fusion
scoping (ROADMAP design decision 4); everything else here is history.

Branch: `phase-g-grouping` (drifted well past Phase G — also carries Phase P and the
`*`/`#` track; merge to `main` when convenient, nothing depends on the name). 549 tests
pass (`pytest src/test/`). The reform1990 thread lives in
`scratch/reform1990/RESUME_2026-09-16.md`/`STATUS.md`.

### Done this session (2026-09-17/18 — history)

- **`resources/ambiguityIgnoreList.tsv`** (new file) — 79 hand-reviewed lemmas to exclude from
  ambiguity-cluster *counting* (not from the lexicon/theory — words stay fully typable), tagged
  with a `reason` column (`archaic` / `anglicism_loan` / `unpopular_spelling` / `sociolect` /
  `data_artifact`) and a short note each. `src/ambiguitychecker.py` gained
  `loadIgnoredLemmas()` + a `classifyTheory(theory, ignoredLemmas=...)` filter param, wired into
  its `__main__`. Verified effect: the n>=5 overflow cluster count drops from 58 to 20 (max
  cluster size 8 → 7) once applied. 413 tests pass throughout.
- **`resources/lexiconExclusions.tsv`** (new file) + `lexique.py` refactor — moved the two
  hardcoded `problemList`/`foreignList` Python literals (124 words total, no per-word reason
  ever recorded) into this tsv with a best-effort `reason` column (`foreign_word` /
  `unsupported_phoneme` / `unpopular_spelling` / `data_defect`) and a `loadLexiconExclusions()`
  loader; `ignoredList` is now a `frozenset` built from it. **This is functionally a different
  mechanism from `ambiguityIgnoreList.tsv`** — these words are dropped from the lexicon
  entirely (never reach `LexiqueMixte.tsv`), not just from the ambiguity metric. Verified
  byte-identical `LexiqueMixte.tsv` regeneration (md5sum match) against the pre-refactor file,
  including with all six 1990-reform flags currently on. `problemList`'s reasons are honestly
  flagged as "unverified legacy entry" in the tsv where the original per-word reasoning was
  never recorded anywhere in git history — provisional, not authoritative, said so in the
  file's own header.
- Confirmed `resources/LexiqueSynthetic.tsv` is unaffected and independently regenerable:
  none of the 7 scripts that write it reference `problemList`/`foreignList`/`ignoredList`, the
  file itself is currently clean (matches HEAD), and `python -m util.completeVerbParadigms
  [--apply]` (documented below and in the "Earlier resolved track" section) is a working
  dry-run/apply CLI — confirmed the CLI works; a full dry-run wasn't run to completion (it's a
  multi-minute whole-corpus cross-check, same order of magnitude as the ~90s CP-SAT solver step)
  since nothing about it was actually at risk from this session's changes.

### Still open from this session (small, well-scoped, not started) — LIVE

- **`baux`'s lemme is the raw Lexique383 string `"bail,bau"`** (comma-joined dual-lemma
  notation Lexique383 uses when a wordform is ambiguous between two lemmas). Should just be
  `"bail"` — `baux` is the irregular plural of `bail` (a lease); the separate rare noun `bau`
  (ship's crossbeam) doesn't actually pluralize as `baux`. Need to find where `lexique.py`
  reads `corpus_word["lemme"]` and handle/strip the comma-joined case (at least for this row;
  worth checking if other rows in `Lexique383.tsv` have the same comma convention).
- **`baud`'s phonology is wrong for the sense actually in use.** Lexique383 has TWO distinct
  French words spelled `baud`: an obsolete hunting term for a scent-hound (pronounced `[bo]`,
  silent d, genuine homophone of `beau`/`bau`) and the modern telecom/metrology unit
  (pronounced `[bod]`, d pronounced, NOT a homophone of `beau`). `LexiqueMixte.tsv`'s `baud`
  row uses the hunting-dog pronunciation (`phon=bo`) for what's almost certainly always the
  telecom sense in any real corpus text — should be `bod`. Fixing this would also pull `baud`
  out of the `beau`/bau/bot/"bail,bau" ambiguity cluster entirely.
- **Suspected "ghost lemma" artifacts**, currently just tagged `data_artifact` in
  `ambiguityIgnoreList.tsv` (so they don't inflate the ambiguity metric) but NOT actually fixed
  at the data level: `pars` (tagged NOM, freq 15.78 — almost certainly the mistagged common verb
  form "je pars/tu pars" of `partir`), `sert` (same pattern, negligible freq), plus `bute`,
  `mar`, `lack`, `fy` (near-zero-frequency, unclear real-word status) and `mise`/`vins`
  (near-duplicate ADJ rows). Worth a broader check for other cases where a common verb
  conjugation got filed under a spurious NOM lemma in Lexique383's own tagging.
- `problemList`'s 27 migrated entries in `resources/lexiconExclusions.tsv` mostly have
  guessed/unverified reasons (see file header) — worth revisiting per-word if anyone has time,
  not urgent since behavior is unchanged from before the migration.

## History — superseded status snapshots (nothing live below this line)

- The old `cl_test_coverage` branch was merged into `main` and deleted locally;
  `origin/cl_test_coverage` may still exist remotely, unpruned.
- Earlier still: the origin/`cl_test_coverage` reconciliation kept
  `satOptimizeDiscriminator` (not `assignDiscriminatorKeypresses`) as
  `dictionary.py`'s active pipeline step; committed the then-orphaned
  `src/satoptimizer.py`; added `.gitignore` and deleted stale scratch/backup cruft;
  fixed the `male`/`males` lexicon bug (`2eab659`, long since pushed). All committed —
  see git history for detail; any test/keypress counts quoted in those old notes are
  stale.

### One open item: `"p"` vs `"f_p"`/`"m_p"` feature-selection fusion (not started, scoped only)

Found while investigating why `dictionary.py`'s discriminator-feature printout showed
odd groupings (e.g. feature-set using bare `m_s`/`p`/`f_s` instead of the fully
gender-qualified `m_s`/`f_s`/`m_p`/`f_p` feature-set that 2269 other words already
use). Root cause, concretely: `src/word.py:134`'s `Word.getFeatures()` always offers
BOTH the bare `"p"`/`"m"`/`"f"` AND the gender-qualified combo (`"f_p"`, `"m_p"`, ...)
as candidate discriminating features whenever a word's gender+number are both known.
`src/greedyoptimizer.py`'s `greedyOptimizeDiscriminator` picks whichever candidate
ranks higher in `orderedFeaturesSelected` (sorted by how many words a feature
discriminates **lexicon-wide**) — so the generic `"p"` (huge global count, since it
matches every plural word regardless of gender) wins over the more specific `"f_p"`
even in homophone groups where they'd be equally sufficient locally. Net effect: the
same semantic distinction ("this is the feminine plural") ends up encoded as two
different, non-reusable features (`"p"` in some groups, `"f_p"` in others) — feature
proliferation that forces the downstream `satOptimizeDiscriminator` special-keypress
allocator to spend an extra key/stroke on `"p"` instead of reusing the key already
assigned to `"f_p"`.

Why this specific case surfaced: words like `général`/`générale`/`générales` have no
homophonous masculine-plural competitor in their stroke cluster (`généraux` is
pronounced `ZeneRo`, not `ZeneRal` — phonetically distinct, never enters the group),
so nothing forces the algorithm to pick the gender-qualified feature; `cher`'s NOUN
reading (as opposed to its ADJECTIVE reading, a separate `(lemme, cgram)` group) has
no attested masculine-plural noun row at all, same effect. Neither is a data bug —
verified against `Lexique383.tsv`/`LexiqueMixte.tsv` directly, the underlying words and
tags are all correct. (Also checked along the way: `mal`/`male`/`males` — the `male`
rows WERE a real bug, already fixed and committed this session, see above. `marri`/
`marris`/`marrie` — a legitimate, if very rare, adjective paradigm, not a bug.)

**Not yet decided or implemented**: whether/how to make the greedy selector (or the
`orderedFeaturesSelected` priority order it consumes) prefer the gender/number-
qualified combo over the bare gender-or-number feature whenever both would
sufficiently discriminate within the current group, without breaking cases where the
bare feature is actually needed (e.g. gender known but number unknown, or vice versa).
Scope this with the user before touching `src/word.py` or `src/greedyoptimizer.py`.

## Earlier resolved track (lexicon-defect triage — kept for history, no action items)

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

## If resuming from scratch (no memory of any session)

1. Read this file fully first, starting from "Live status" at the top — that's the
   live section. Everything below "Earlier resolved track" is historical context only.
2. Run `pytest src/test/` (expect 549 pass as of 2026-09-20; older notes in this file
   quote smaller historical counts) and
   `python -m util.validateLexiconAgainstVerbiste` (expect 136 total flags now, not
   134 — adding 2 tags to ass:eoir's `assoyons`/`assoirais` rows during that track
   incidentally made the validator flag those rows too, against its single-canonical-
   spelling assumption; same known non-issue class as the rest of ass:eoir/pa:yer, not
   a regression). Both counts are otherwise frozen, since `LexiqueSynthetic.tsv` will
   NOT be wired into `LexiqueMixte.tsv` (permanent decision, see above).
3. Only open item: the `"p"` vs `"f_p"`/`"m_p"` feature-fusion task above. Everything
   else in this file is done.
