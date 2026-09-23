# Bundle C — RESUME_*.md session-handoff notes

Doc and Data Inventory (Pass 3). Read-only survey of the 13 root `RESUME_*.md` files plus
`scratch/reform1990/RESUME_2026-09-16.md` and `scratch/reform1990/STATUS.md`. All are
session-handoff notes written for a fresh (`/clear`ed) session to resume without
re-deriving context. Cross-checked against `docs/PIPELINE.md`, `docs/GLOSSARY.md`,
`docs/specs/star-hash-marking.md`, `docs/specs/discriminating-features.md`, `todo.md`,
`ROADMAP.md`, and code (`grep`).

All 15 files are `git ls-files`-tracked (not untracked, despite
`RESUME_2026-09-22-trainer-features.md`'s own item 8 claiming otherwise — stale note).

General finding: every file describes work that is either (a) fully superseded by a later
stage of the same design thread (the pre-elicitation solver-based design, superseded by
the 2026-09-18 elicitation-first pivot; see `docs/GLOSSARY.md`/DECISIONS.md), or (b)
fully landed and now re-documented in `docs/PIPELINE.md`/`docs/specs/*` or `ROADMAP.md`'s
"Status update" sections. No file holds a fact that is both durable and undocumented
elsewhere, **except** the still-open lexicon-defect items already tracked live in
`todo.md`'s "Still open from this session" section (baux/baud/ghost-lemmas) — those are
restated in `todo.md` already, so the RESUME copies are pure duplicates, not the only copy.

## RESUME_2026-09-17.md

Verdict: pure history — delete.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-176 | Shared-discriminator rewire (`buildDiscriminatorSelection`, ortho-collapse bucketing) and 7 lexicon data-quality fixes (dégueu/déjanté/zakouski/nues gender-number gaps, casher/kasher paradigm consolidation, fayotte). Documents the "delete all 3 pickles" gotcha. | history | delete | The rewired code (`buildDiscriminatorSelection`/`satOptimizeDiscriminator`) is now explicitly non-live per `CLAUDE.md` ("test-only... no longer runs in `dictionary.py` `__main__`"); the 7 lexicon fixes are long since committed to the TSVs themselves. The 3-pickle gotcha is already in `CLAUDE.md` ("Pitfalls" paragraph). |

References to this file (outside `docs/refactor/`): none in code; cited only by other RESUME files (`RESUME_2026-09-18.md`, `RESUME_2026-09-19-cpsat.md`) and `docs/GLOSSARY.md` (as an example of the legacy-note genre). No fix needed on deletion — those are historical cross-references, not live links.

## RESUME_2026-09-18.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-176 | Design review of the (now-superseded) atomic-keypress solver plan: union-injectivity model, reserved-keys-vs-coda-bank split, several "rules proposed, not yet confirmed." | superseded | delete | The whole solver-picks-features design this file reasons about was replaced by the Elicitation Phase (2026-09-18 pivot itself, ironically dated the same day). `docs/specs/discriminating-features.md` §1 states this explicitly. |

One fact worth checking it isn't lost: "reserved keys `[0,1,10,15]` stay exclusive to the `*`/`#` track" — already the live design, stated in `docs/specs/star-hash-marking.md` §1 ("Two reserved keys only"). No unique fact survives only here.

References: none in code; cross-referenced by `RESUME_2026-09-19-cpsat.md`, `RESUME_2026-09-19-phaseP-plan.md` (design decision #1, itself superseded/restated in the spec).

## RESUME_2026-09-19.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-205 | Early Elicitation Phase session: questionnaire live, 6 lexicon phonology bugs found/fixed (bitter exclusion, -ai passé-simple/futur-simple fixes for aurai/serai/minerai/enfonçai/enverrai, tapas, rescapes, portraire), subjonctif-imparfait scoped out, migration method for re-keying answers by opposition identity. | history | delete | All fixes are committed in the TSVs; the migration method was a one-time procedure, not a reusable tool. Two flagged-but-unconfirmed items (`régnions`/`régnons`, `entêtai`/`entêtez`) — checked: not mentioned in `todo.md` or `docs/specs/*`, but the whole opposition set has been re-elicited multiple times since (K went 5→6→7); if these questions still exist in `questionnaire.json` today they were presumably answered. Not independently verifiable without rerunning the pipeline (out of scope for this read-only pass). |

Questions for triage should include: are `régnions`/`régnons` and `entêtai`/`entêtez` still flagged anywhere live, or resolved? (see Questions list below).

References: cited by `RESUME_2026-09-19-phaseG.md`/`-cpsat.md`/`-phaseP-plan.md` (chain of same-day session notes) and `docs/GLOSSARY.md` (example only).

## RESUME_2026-09-19-phaseG.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-205 | E5/E6/Grouping Phase (greedy) build; two-model (pers_1-default vs pers_3-default) comparison; adopts model 2 (K=6 vs 7). | superseded | delete | Superseded by `RESUME_2026-09-19-cpsat.md` (CP-SAT beats greedy, K recomputed to 6 then 7 after later fixes) and ultimately by `docs/specs/discriminating-features.md` §3 (current K=7, current table). The greedy path (`src/featuregrouping.py`) is explicitly "not live" per `CLAUDE.md`. |

References: `RESUME_2026-09-19-cpsat.md` (direct continuation), `docs/GLOSSARY.md` (example).

## RESUME_2026-09-19-phaseP-plan.md

Verdict: pure history — delete (self-superseded).

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-229 | Original Realization Phase milestone-1 plan (before it was built). File's own line 11-18 says it was "EXECUTED... diverged... Read the new file first." | superseded | delete | Self-declared superseded by `RESUME_2026-09-19-phaseP.md`. Current design fully in `docs/specs/discriminating-features.md` §4. |

References: `RESUME_2026-09-19-phaseP.md` (supersedes it), `docs/GLOSSARY.md` (example).

## RESUME_2026-09-19-phaseP.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-100 | Realization Phase milestone 1 done: 6 groups get physical coda keys, 3-bucket collision classifier (`_isInScopeCollision`), the "finalized word pool" fix and its regression test. | history | delete | Design fully covered by `docs/specs/discriminating-features.md` §4-5; the 3-bucket classifier is `docs/specs/star-hash-marking.md` §1's "problem" section (same taxonomy, current names). |
| 100-221 | Specific 2026-09-19 numbers (K=6, per-group keys, 29/1252 collision counts) and the regression-test warning ("don't re-simplify the finalized-word-pool check"). | history / current fact (stale numbers) | delete | K is now 7 (`docs/specs/discriminating-features.md` §3); the numbers are stale. The regression-test warning is preserved by the actual test (`TestRealizeKeypressGroupsAsExtraStroke::test_multi_group_composition_does_not_coincide_with_another_group`, still in the suite) — code is the durable record, not this prose. |

References: `RESUME_2026-09-20-starhash-priority.md` ("defines the three collision buckets"), `RESUME_2026-09-21-collision-residual.md`, `docs/GLOSSARY.md` (example). None are load-bearing links (all say "read together with" for background, not "see X for the current spec").

## RESUME_2026-09-19-cpsat.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-360 | CP-SAT exact Grouping Phase solver build session: `featuregroupingsat.py` design, K=5→6 after an impératif-answer-quality fix, lexicographic multi-tier preferences, an INVALID stroke-pairing addendum (explicitly marked invalid in the file itself), regeneration commands. | superseded | delete | K is now 7 (one more elicitation fix landed after this). The addendum's own item 6 says "the stroke-pairing analysis below is invalid as written" — self-flagged dead content. `src/featuregroupingsat.py` itself, `keypress_groups.json`, and `docs/specs/discriminating-features.md` §3 are the living record. |

References: `RESUME_2026-09-19-phaseP-plan.md`, `docs/GLOSSARY.md` (example), `docs/refactor` callgraph notes.

## RESUME_2026-09-20-starhash-priority.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-227 | Frequency-regret design session for star/hash marking: cost model, 10x-ratio-exemption rule derivation, threshold sensitivity table (10x/30x/100x), Rule-3 doublet-exemption investigation (naive version rejected via real Ngram data, correct version found later same session). | design rationale | delete (already extracted) | This is exactly the material `docs/specs/star-hash-marking.md` §2 ("Cost model: why these rules") already distills, including the 10x sensitivity numbers and the Ngram-based Rule-3 rejection story. Confirmed via Spec Extraction (Pass 2) per `docs/refactor/DECISIONS.md`. |
| 228-327 | "What's genuinely still open" — closes out every item as done in a same-day follow-up, except: (1) whether buckets 2/3 share one physical mechanism (pooling assumption never re-confirmed), (2) override list still provisional/never regenerated at 10x in isolation, (3) not yet wired into `dictionary.py`'s persisted output (later done — see `docs/specs`). | history/superseded | delete | (3) is done (wired). (1) and (2) are real caveats about `MARKING_OVERRIDES`'s provenance — `docs/specs/star-hash-marking.md` §3 already flags the override list as "provisional... never regenerated from one canonical run" (nearly verbatim), so this is a duplicate, not new information. |

Questions for triage: is the "buckets 2/3 share one mechanism" pooling assumption (item 1) worth a line in the spec's "Known gaps," or is it moot now that `decideStarHashMark` demonstrably handles both buckets identically in code?

References: `RESUME_2026-09-19-phaseP.md` (defines collision buckets it builds on), `RESUME_2026-09-21-collision-residual.md` (continues from it), `docs/GLOSSARY.md` (example).

## RESUME_2026-09-21-collision-residual.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-50 | Two real bugs fixed (theory 2 not wired into either exporter — `FirstTheory.pickle` used instead of theory 2). | history | delete | Fixed and committed; current exporters correctly use `loadFinalTheory` per `docs/PIPELINE.md` §S8.1. |
| 50-158 | The "~52 groups" residual investigation task, with a repro script and named example pairs (`quatre`/`carte`, `ski`/`gui`, `merde`/`merdre`, same-lemma cases). | history (task since closed) | delete | `ROADMAP.md`'s "Status update (2026-09-21)" section documents the root cause found and fixed (`canonicalizeStrokes`, raw-Strokes-vs-RTFCRE mismatch) and explicitly cites this file as the task it closes out, naming `quatre`/`carte` as the worked example. Fully superseded, not orphaned. |

References: `ROADMAP.md` (follow-up, cites this file by name), `docs/GLOSSARY.md` (example). No stale-link risk — `ROADMAP.md`'s reference is itself historical prose ("Follow-up to `RESUME_2026-09-21-collision-residual.md`'s open task"), fine to leave a dangling filename in old ROADMAP prose or fix to "the 2026-09-21 residual investigation" when this file is deleted.

## RESUME_2026-09-21-plover-integration.md

Verdict: delete after confirming no unique fact — pure history.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-91 | Plover system-plugin architecture research (why no custom machine plugin needed, Plover source reading notes) and the Javelin firmware context. | design rationale | delete | Architecture conclusion ("system plugin + existing Gemini PR machine plugin + KEYMAPS entry is sufficient") is implicit in the shipped code (`plover_stenalgo/`) and `docs/PIPELINE.md` §S8.4-8.5; not restated in prose anywhere else, but is discoverable from the code with effort. Low risk to lose as prose. |
| 92-157 | **Hardware verification saga**: keys 0/1/2/10 wired to Gemini number-bar bits `#A`/`#B`/`#C`/`#1` (not letters/star), only key 15 is a real star bit; verified via a from-scratch PowerShell serial probe since Plover-in-WSL/plugin-manager paths all failed. | current fact | keep — already in code | `util/export_plover_system.py:19` has "Ground truth captured 2026-09-21 by sniffing raw Gemini PR packets directly" as a comment header for `GEMINI_PR_LABELS`. The fact lives in code; this file is the narrative of how it was obtained (methodology, not needed after the fact). Delete. |
| 159-235 | Plugin installation mechanics (Plover's git-based installer needs a real remote, not a UNC path; separate GitHub mirror `jf5pier/stenalgo-plover` must be hand-synced), the "@" red herring (duplicate-key and out-of-order-key stroke bugs, fixed in `strokesToRTFCRE`). | current fact (external dependency) | **docs/ARCHITECTURE.md** — one line | The `plover_stenalgo/` ↔ `stenalgo-plover` GitHub mirror hand-sync requirement is a real, easy-to-forget operational fact with no other home (not in code, not in `docs/PIPELINE.md`). Worth one line in an artifacts/deployment section. |
| 236-247 | Still-open items: 47.4k same-steno collisions (now fixed by theory-2 wiring, see above), firmware button-script reassignment decision (still a real open product decision — no automated fix possible), Track A (javelin-steno-pico runtime-vs-compile-time protocol switch, explicitly out of repo scope). | history / open item | **ROADMAP.md** or delete | The firmware-reassignment decision (should keys 2/10 be rewired at the firmware level?) is a genuine unresolved product question outside this repo's code — worth one line in `ROADMAP.md` if not already there (checked: not present). Everything else is resolved. |

References: none in code; `docs/GLOSSARY.md` (example only). No stale-link risk.

## RESUME_2026-09-21-steno-trainer.md

Verdict: pure history — delete (entirely superseded, self-declared).

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-99 | steno-trainer 4-phase plan status + the original "calmez → `-kt`" over-marking bug report. | superseded | delete | File's own line 8: "every item in this file is resolved" — Phase 2 committed, the bug fixed and documented in `RESUME_2026-09-22-alternate-strokes.md`, Phases 3/4 shipped per `RESUME_2026-09-22-trainer-features.md`. |

References: `RESUME_2026-09-22-alternate-strokes.md` (supersedes items 1/2), `docs/GLOSSARY.md` (example). No stale-link risk.

## RESUME_2026-09-22-alternate-strokes.md

Verdict: pure history — delete.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-126 | Self-homograph alternate-strokes fix (root fix `688c74d` + 3 follow-on commits), current K=7 keyboard table, 3 elicitation-answer fixes, reading-labels feature + a Realization Phase entry-matching bug fix (`_resolveEntryWord` canonicalization), `être`/`q32` conflict fix. | history | delete | All commits landed on `main`; the K=7 table matches `docs/specs/discriminating-features.md` §3's current table exactly. The `_resolveEntryWord` canonicalization fix is now just how the code works (`src/ambiguitychecker.py`, `S6.Realization.2.1` per `docs/PIPELINE.md`). |

One item worth checking: "`q31`/`q49` review, flagged `clean: false`, not blocking" — recurs in `RESUME_2026-09-22-trainer-features.md` item 7 as still "optional, carried over." Only living copy needed; see next entry.

References: `RESUME_2026-09-22-trainer-features.md` (continuation), `docs/GLOSSARY.md` (example).

## RESUME_2026-09-22-trainer-features.md

Verdict: delete after moving ~4 genuinely open items.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-46 | 5 commits: IPA toggle, sentence mode, star/hash-merged-into-last-phoneme-stroke (`composeReservedKeyStrokes` change), context words, definition mode + hints toggle. | history | delete | Fully covered by `docs/specs/star-hash-marking.md` §5 (merged mark) and `docs/PIPELINE.md` §S8.6-8.9 (trainer exporters). |
| 51 | 182 nouns have no gender in `Lexique383` (`maison`, `voiture`, `main`, …) → no le/la context in singular; "a lexicon fix (gender fill) would fix it." | current fact / open item | **todo.md** ("Still open" lexicon bullets) | Not present anywhere in `todo.md`'s existing lexicon-defect list (baux/baud/ghost-lemmas) — a genuinely new, undocumented gap of the same kind. Concrete, actionable, no other home. |
| 52-53 | Definition search is exact-spelling only, no accent-insensitive/prefix fallback. | current fact / open item | **todo.md** or steno-trainer's own notes | Minor UX gap, no other home; low priority but cheap to note. |
| 54-55 | Hyphenated compounds (`celle-ci`, `là-haut`) drilled as two chords in sentence mode; Plover would output two words. | current fact / open item | **todo.md** | Real, specific sentence-mode limitation, undocumented elsewhere. |
| 58-64 | Plover marker-strokes-as-macro-plugin idea (replace ~48k static entries with a (word, marker)→form table lookup, mainly for the Javelin onboard-flash target); Plover's `ORTHOGRAPHY_RULES` can't do it since French forms aren't derivable from spelling; Javelin's equivalent not yet checked. | design rationale / forward-looking | **ROADMAP.md** | Already summarized in memory `dual_target_architecture` ("marker strokes as a Plover macro plugin" idea, 2026-09-22) — but that's session memory, not a repo doc; `ROADMAP.md` is the right forward-looking home so the idea survives outside the assistant's own memory file. |
| 56-57 | `football` = `kp@et/svel` "reported as bizarre" — investigated, matches the layout, user never explained what looked wrong. | history (non-issue) | delete | No actionable content — a closed non-finding. |
| 68 | Confirms this file and 2 others were untracked at time of writing. | stale fact | n/a | Already contradicted: `git ls-files` shows all 15 RESUME files tracked today. |

References: none in code; `docs/GLOSSARY.md` (example). No stale-link risk on deletion.

## scratch/reform1990/RESUME_2026-09-16.md

Verdict: pure history — delete with `scratch/reform1990/` (see Bundle D for the directory-wide recommendation).

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-96 | Session-pause snapshot: which `APPLY_1990_REFORM_*` flags were flipped on for a one-off test, an ambiguity-metric comparison (traditional vs full-reform: -13 lemma-homophone clusters, +1 cross-category clash, overflow mass exactly flat), and a note that the flags default to `False` and should be flipped back. | history / current fact (the default) | delete; the default-off fact is already current-state | The "all 6 flags are `False` by default, opt-in" fact is verifiable directly in `lexique.py` (grep `^APPLY_1990`) — no doc needed. The comparison numbers are one-off exploratory data, not reproducible without rerunning (flagged in the file itself as `/tmp`-only, unlikely to still exist). |

References: `todo.md` ("Live status" section: "The reform1990 thread lives in `scratch/reform1990/RESUME_2026-09-16.md`/`STATUS.md`" — this is a currently-live pointer), `RESUME_2026-09-20-starhash-priority.md`. **Fixing needed on deletion**: `todo.md`'s own live-status paragraph points here; if these two files are deleted, that sentence in `todo.md` needs to change (e.g. to "see git history around commit `2127790`" or simply be dropped since the thread is closed per todo.md's own text: "All 12 sourced 1990-reform word-list categories... now resolved").

## scratch/reform1990/STATUS.md

Verdict: pure history — delete with `scratch/reform1990/`.

| Lines | Summary | Category | Recommended action → destination | Reason |
|---|---|---|---|
| 1-761 | Full sourcing/verification history for the 1990-spelling-reform word-list resource (`resources/reform1990.tsv`): Wiktionnaire scraping, edit-distance heuristic matcher, per-category verification against OQLF/Journal-officiel sources, category-by-category resolution log. | history | delete | `resources/reform1990.tsv` (270 sourced rows, tracked) is the durable artifact this whole research thread produced; it's self-contained (each row presumably carries its own provenance/exception flags per `docs/specs/star-hash-marking.md` §3's description of `isException`). The research trail that built it is not needed to use or maintain it going forward. Not spot-checked line-by-line (761 lines) given the file's own framing as an append-only work log — no evidence any decision recorded here is *not* also reflected in the current `reform1990.tsv`/`lexique.py` flags, which are the real source of truth per `CLAUDE.md`'s "code is the source of truth" convention applied throughout this repo. |

References: `RESUME_2026-09-20-starhash-priority.md` ("full research trail... see `scratch/reform1990/STATUS.md`"), `todo.md` (same live pointer as above). Same fix-on-deletion note as the sibling file.

## Questions for triage

1. Delete all 15 RESUME/STATUS files in one commit, or keep any (e.g. the plover-integration hardware-verification saga, or the reform1990 sourcing trail) as an intentionally-archived record under `docs/refactor/` or a `history/` folder instead of deleting outright?
2. `todo.md`'s "Live status" paragraph points to `scratch/reform1990/RESUME_2026-09-16.md`/`STATUS.md` — update or remove that sentence when those files are deleted?
3. Move the 4 flagged genuinely-open items from `RESUME_2026-09-22-trainer-features.md` (182 ungendered nouns, definition-search fallback, hyphenated-compound sentence drilling, Plover-macro-plugin idea) into `todo.md`/`ROADMAP.md` before deleting that file — confirm destination and priority tier.
4. Are `régnions`/`régnons` and `entêtai`/`entêtez` (flagged as possibly-non-homophone questionnaire items in `RESUME_2026-09-19.md`) still open, or were they resolved in a later elicitation round? Worth a quick grep of `questionnaire.json`/`elicitation_answers.json` before deleting the only file that names them.
5. Add one line to `ROADMAP.md` about the firmware button-script decision (should keys 2/10 be physically rewired to send a real letter/star bit) before deleting `RESUME_2026-09-21-plover-integration.md`, the only place this open product question is recorded?
6. Add one line to `docs/ARCHITECTURE.md` (or wherever artifact/deployment operations end up) noting the `plover_stenalgo/` ↔ `github.com/jf5pier/stenalgo-plover` manual-sync requirement, the only place that operational fact is recorded?
7. Is the buckets-2/3-share-one-mechanism pooling assumption (from `RESUME_2026-09-20-starhash-priority.md`) worth a line in `docs/specs/star-hash-marking.md`'s "Known gaps," or is it settled by the code (`decideStarHashMark` demonstrably handles both) and safe to drop?

## Main-thread correction (spot-check)
The claim "no RESUME file is referenced from code" is wrong. `.py` comments/docstrings citing RESUME files
(must be repointed — ask first — before the files are deleted):
- lexique.py:69 → RESUME_2026-09-17.md (and SHARED_DISCRIMINATOR_REWIRE_PLAN.md)
- src/greedyoptimizer.py:54, src/ambiguitychecker.py:86, :100 → RESUME_2026-09-20-starhash-priority.md (→ docs/specs/star-hash-marking.md)
- src/ambiguitychecker.py:996 → RESUME_2026-09-18
- src/test/elicitation_test.py:308, src/test/ambiguitychecker_test.py:1046 → RESUME_2026-09-21-steno-trainer.md (calmez regression → docs/specs/discriminating-features.md)
- util/build_realization_report.py:3 → RESUME_2026-09-19-phaseP-plan.md
- util/build_keypress_groups.py:26 → RESUME_2026-09-19-phaseG.md
