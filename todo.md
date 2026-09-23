# Todo

Written to survive a `/clear` — read this file first in a fresh session.

## Suspected bugs (from docs refactor, 2026-09-22)

Found while writing `docs/PIPELINE.md` (full write-ups, evidence and confidence in
`docs/refactor/callgraph/90-findings.md`, same B-numbers). **Not yet reviewed by the user;
nothing has been fixed.** Tier 1 changes the Plover dictionary (or other exported output)
today; tier 2 changes reports or tracked artifacts; tier 3 is latent (no measured impact).

### Tier 1 — affects the Plover output today

- **B1** Spelling twins: only the first Word of a spelling gets its feature discriminating stroke —
  src/ambiguitychecker.py:797-800 (`_resolveEntryWord`) — Words sharing (ortho, `lemmeGramCat`) and
  strokes: `next(...)` marks one ("agis" participle vs finite). 230 same-lemmeGramCat collision pairs;
  99 pairs in 98 strokes reach theory 2 unmarked. Invisible to the 0-residual invariant.
- **B2** Synthetic verb forms get a vowel-less trailing syllable — src/verbparadigm.py:561, :611 —
  radical cut by character count keeps the infinitive's syllable boundary (`cannes` sub:pre:2s: 2
  strokes vs NOM 1). 3,843 new Words carry an extra stroke and miss their real homophones.
- **B3** Breakdown built from a LexiqueInfra association that disagrees with the phonology —
  lexique.py:1021, :1033 (with :770-883) — match uses Infra `phono`, `syll_cv` comes from `assoc`
  (`embêter` typed with closed `e`). 132 mixed-lexicon rows; 175 VER synthetic rows inherit it.
- **B4** Alternate entries of self-homographs take unrelated words' only stroke —
  src/ambiguitychecker.py:1288 (`buildExtraInducedStrokes`), dictionary.py:389 — alternate entry
  strokes skip the star/hash marks (`subits` loses to `subis`). 9 spellings have no Plover entry.
- **B5** Frequency ties make star/hash marks depend on input order — src/ambiguitychecker.py:224-232,
  `_starHashCompare` :242-258 — not antisymmetric on equal frequency (`pas`/`pâts`). Shuffling input
  changes marks in 619 of 4,450 lemma-homophone groups (14%); any lexicon row move can flip them.
- **B6** 1990-reform deletion/insertion rules miss inflected forms after lemma normalization —
  lexique.py:224-225 with :1197-1198 — rules keyed under `oldSpelling`, lemma already normalized
  (`balloter` beside `ballottait`). 67 rows over 24 lemmas keep pre-reform spellings in Plover.
- **B7** NOM/ADJ exception override keeps the source word's syllabification —
  util/generateMissingNomAdjForms.py:88, :94 — ortho/phon from the exception table, `syll_cv` from the
  source (`molle(s)` typed like `mou`). Among 12 NOM/ADJ synthetic rows with `syll_cv` ≠ `phon`.
- **B8** Phonetic stroke rule never checks that a stroke is pressable — src/keyboard.py:607-620 with
  dictionary.py:305 — no check against `_possibleKeypress` (`traumatisme` coda `zm` → 3-key
  right-pinky press). 529 Words, 39 distinct illegal strokes in the Plover output.
- **B9** Identity merge discards the later row's frequency and syllabification —
  dictionary.py:113-137 (`readCorpus`) — frequencies not summed, differing `syll_cv` dropped (24
  reform-rewrite identities: `gélinotte`, …). Undercounted frequency feeds the frequency-ratio rule
  (R4) and the Plover "most frequent" pick.
- **B10** Plover export breaks frequency ties by theory-1 order — util/export_plover_dictionary.py:56
  — `max(key=frequency)` keeps the first Word (`dégotés`/`dégottés`, both 0.0). Low impact;
  order-dependent like B5.

### Tier 2 — affects reports or tracked artifacts (not the Plover output)

- **B11** Residual-collision lists in the realization report change between clean rebuilds —
  src/word.py:94, :155; src/ambiguitychecker.py:739-747, :1248-1257 — salted `hash()` stored in the
  pickles sets `allWords` order and first-seen pairing. Cross-category clashes 34/40/38, cross-lemma
  1,283/1,292 across rebuilds; theory 2 and Plover unaffected (`PYTHONHASHSEED=0` workaround).
- **B12** The precedence-spec checker covers much less than the spec —
  util/check_conjugation_disambiguation_order.py:69-77, :100-126 — "masculine must be free" checked
  for participles only; mandatory impératif/subjonctif and line order unchecked. The validation
  report can be clean while answers contradict the spec.
- **B13** Verb paradigm completion is not idempotent — util/completeVerbParadigms.py:95-97 with
  :324-340 — `--apply` twice without deleting the pickles appends the same rows again to the tracked
  `LexiqueSynthetic.tsv` (duplicates merge by identity; only the file grows).
- **B14** Human views go stale with the caches — dictionary.py:498-505, :531 — `theory.tsv` is
  written only on a `FirstTheory.pickle` miss; `theory2.tsv` from possibly stale discriminating
  feature sets. Low: both gitignored and read by nothing.

### Tier 3 — latent (no measured current impact)

- **B15** Pickle caches are never invalidated — dictionary.py:451, :498 — not checked against the
  lexicon TSVs, `excluded_words.txt` or `starboard3h.json`; editing the layout without
  `rm -f *.pickle` yields a silently wrong Plover dictionary. Likelihood low while the layout is frozen.
- **B16** First-seen pairing can hide same-lemmeGramCat collisions — src/ambiguitychecker.py:739-747
  with :1248-1250 — X, Z (same `lemmeGramCat`) and Y on one stroke: if Y is seen first, (X,Z) never
  reaches `residualCollisions`. No instance observed.
- **B17** `buildFinalTheory` ignores unassigned Keypress Groups and residuals — dictionary.py:380-389
  — an unrealizable group's Words silently lose their feature discriminating stroke in theory 2 and
  Plover. Not triggered (all 7 groups have keys).
- **B18** Trainer legend can disagree with the dictionary — util/export_keyboard_layout.py:128 —
  legend reads the tracked realization report, the dictionary recomputes keys inline; rerunning
  Discriminating-Feature Grouping (Grouping Phase) without the report build shows old keys. Agree today.
- **B19** Null `chosenKeys` crashes the trainer legend — util/export_keyboard_layout.py:133-141, :144
  — an unassigned group raises `TypeError`. Not triggered.
- **B20** `_resolveEntryWord` silently falls back to the first candidate — src/ambiguitychecker.py:800
  — stale resolved discriminating feature sets (lexicon fix without rerunning Discriminating-Feature
  Elicitation (Elicitation Phase)) mark `candidates[0]` instead of failing.
- **B21** Extra alternates of empty-primary spellings are never verified —
  src/ambiguitychecker.py:1227-1241 — only Words in `allWords` get alternates checked; 2,749
  spellings have an empty primary ("abaisse"). 0 collisions with theory 1 today.
- **B22** Collision tests compare raw strokes — src/ambiguitychecker.py:1114, :1142, :1243-1247 —
  collisions are physical (canonical) but raw Strokes are compared. 0 cases today.
- **B23** Non-live hard-rule feature raises `KeyError` — src/featuregroupingsat.py:117 with :128-135
  — a feature in `ALONE_KEYS`/`MUST_DIFFER_GROUPS` that stops being live gives `KeyError` instead of
  a clear error.
- **B24** A solver timeout can lock a non-optimal result — src/featuregroupingsat.py:172, :274, :398
  — FEASIBLE is accepted and locked, so tier score/tie-break are neither proven nor reproducible.
- **B25** The frequency-ratio rule (R4) and the category-priority rule (R6) can form a cycle —
  src/ambiguitychecker.py:224 vs :229 — A<B (R6), B<C (R6), C<A (R4) → order-dependent sort. 0
  cycles among live representatives.
- **B26** Doublet merge checks only the representative's lemma — src/ambiguitychecker.py:321-326 —
  a rarer homograph carrying the reform-pair lemma makes the doublet look like a real ambiguity. 0
  instances.
- **B27** Word identity is fragile — src/word.py:94, :161 — separator-free `_hash` concatenation and
  `__eq__` on `_hash` only: Words from pickles of different processes never compare equal. Root
  cause of B11.
- **B28** `zip` truncation can leave a syllable unregistered — dictionary.py:177 — 99 Words have
  phonetic/orthographic syllable lists of different lengths; a unique extra syllable would make
  `buildTheory` (:310) raise `KeyError`. Not triggered.
- **B29** `lexicalPhonemeAmbiguityScore` looks up a word phonology as a syllable name —
  src/grammar.py:913, :931 — `getSyllable("apodiR")` → `None`, the branch adds 0 for polysyllabic
  words. Affects the fallback keymap only.
- **B30** `optimizeOrder` starts from set order — src/grammar.py:307-320 — the best permutation (and
  README.md's figures) can change with the hash seed. Fallback keymap only.
- **B31** Multiphoneme frequencies are always 0 — src/grammar.py:566, :574-584 — all 353 values are
  0.0; no reader.
- **B32** The layout solver wipes the layout before solving — src/cpsatsolver.py:422 (not run) —
  an infeasible or timed-out part leaves its bank empty and the next `buildTheory` raises `IndexError`.
- **B33** `lexique.py` rebuilds on import — lexique.py:1261-1263 — no `__main__` guard: importing it
  overwrites `LexiqueMixte.tsv`. No importers today.
- **B34** `Lexique` keeps its rows in class-level lists — lexique.py:957-958 — a second `Lexique()`
  in one process doubles every row. Not triggered.
- **B35** The sentence exporter's drill-item gate depends on another process —
  util/export_practice_sentences.py:158 — compares against `practice-words.json` from a separate
  theory-2 recompute; changed inputs between the runs reject valid sentences.

## Queued follow-ups (from docs refactor)

- **Code renames for "lemma" names that mean lemma + category** (decision a12; no code change
  yet): `LemmaHomophoneGroupKey` (src/elicitation.py:24) → `HomophoneGroupKey`; `groupWordsByLemme`
  (src/word.py:414) → `groupWordsByLemmeGramCat` (`groupWordsByBareLemme` is correctly named).
  Same pattern, also worth renaming: `buildLemmaHomophoneGroups` (src/elicitation.py:61) and
  `buildWordsByOrthoLemme` (src/ambiguitychecker.py:772, keyed by (ortho, `lemmeGramCat`)).
- **No command regenerates `starboard3h.json`** — the `optimizeKeyboard` call is commented out at
  dictionary.py:494 (and `toJSONFile` at :496). Add an explicit entry point for Keyboard Layout
  Optimization (S4) (decision b5: a real, rarely-run, costly step, not dead code).
- **Realization report vs inline path drift** — the trainer keyboard legend reads the tracked
  `realization_report.json`, while theory 2 and the Plover dictionary recompute the
  Discriminating-Feature Stroke Realization (Realization Phase) inline; nothing compares them
  (B18, B19). Decide in Dead-Code Removal (Pass 5).
- **`.claude/settings.local.json` still allow-lists the old `build_phase_p_realization`
  commands** — user to update to `util.build_realization_report`.
- **Runtime strings still say "Phase G/P"** — ask the user before changing them (it is a code
  change, not a comment edit): print messages and report keys at dictionary.py:537/539,
  src/featuregrouping.py:316/324, src/featuregroupingsat.py:591, util/build_realization_report.py:111/132,
  and the French questionnaire HTML at util/build_questionnaire_page.py:312. Renaming a report key
  changes the tracked `realization_report.json`. Also: the module docstrings of src/featuregrouping.py:5
  and src/featuregroupingsat.py:5 still cite "ATOMIC_KEYPRESS_REWIRE_PLAN.md's Phase G section", which
  that plan now titles "Grouping Phase".

## Live status (2026-09-20)

For the homophone-theory work (Phase 0 through Discriminating-Feature Stroke Realization
(Realization Phase) milestone 1 and the star/hash marks of Different-Lemma or
Grammatical-Category Disambiguation (S7)), **`ROADMAP.md`'s "Status update (2026-09-20)" section and
`ATOMIC_KEYPRESS_REWIRE_PLAN.md` are authoritative** — do not reconstruct state from the
session notes below. Before touching `resources/Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv`,
`LexiqueMixte.tsv`, or `LexiqueSynthetic.tsv`, read `LEXICON_RECOMPUTE_PIPELINE.md` — the
recompute chain has manual, order-dependent steps and two silent-failure traps. The only still-open items tracked in THIS file are the lexicon
data-quality bullets in "Still open" below and the `"p"` vs `"f_p"`/`"m_p"` feature-fusion
scoping (ROADMAP design decision 4); everything else here is history.

Branch: `phase-g-grouping` (drifted well past the Grouping Phase — also carries the Realization
Phase and the star/hash marks; merge to `main` when convenient, nothing depends on the name). 549 tests
pass (`pytest src/test/`). The reform1990 thread lives in
`scratch/reform1990/RESUME_2026-09-16.md`/`STATUS.md`.

### Done this session (2026-09-17/18 — history)

- **`resources/ambiguityIgnoreList.tsv`** (new file) — 79 hand-reviewed lemmas to exclude from
  ambiguity *counting* (lemma-homophone groups) (not from the lexicon/theory — words stay fully typable), tagged
  with a `reason` column (`archaic` / `anglicism_loan` / `unpopular_spelling` / `sociolect` /
  `data_artifact`) and a short note each. `src/ambiguitychecker.py` gained
  `loadIgnoredLemmas()` + a `classifyTheory(theory, ignoredLemmas=...)` filter param, wired into
  its `__main__`. Verified effect: the n>=5 lemma-homophone overflow group count drops from 58 to 20
  (max group size 8 → 7) once applied. 413 tests pass throughout.
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
  out of the `beau`/bau/bot/"bail,bau" Theory-1 collision entirely.
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
- **A round of lexicon re-validation for anomaly classes beyond what Phase 0's manual review
  already caught** — raised while chasing the `évaser` syllabification bug (2026-09-20, see
  `LEXICON_RECOMPUTE_PIPELINE.md`). At minimum:
  - words that lose their gender when moving from singular to plural, or the reverse
  - words that lose their number when moving from masculine to feminine, or the reverse
  - same-lemme words whose phonology varies inconsistently when a silent suffix letter is
    added (the `évaser` bug's own class — real corpus-sourced sibling forms disagreed with
    synthetically-generated ones on where a stem-final consonant syllabifies)
  - likely more checks worth designing once this one is scoped; not started.

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
homophonous masculine-plural competitor in their Homophone Group (`généraux` is
pronounced `ZeneRo`, not `ZeneRal` — phonetically distinct, never enters the group),
so nothing forces the algorithm to pick the gender-qualified feature; `cher`'s NOUN
lemmeGramCat (as opposed to its ADJECTIVE one, a separate `(lemme, cgram)` group) has
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
  `embrayes`, identical consonant-sequence-before-r radical shape, already split).
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
