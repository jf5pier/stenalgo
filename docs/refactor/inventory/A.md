# Doc and Data Inventory — Bundle A

Read-only triage. Verdicts and destinations are recommendations for the user to confirm in
`docs/refactor/DECISIONS.md`.

## README.md

Verdict: outdated project pitch + a stale lexicon count; the homophone section was already
updated to new terminology and is close to reusable as-is.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-36 | Title, objective, context/intro to steno and the project's goal | current fact | README.md (What/quickstart) | Still accurate framing; trim for the 60-80 line budget |
| 38-62 | "Minimizing complexity": finger strain + mental strain criteria | design rationale | docs/ARCHITECTURE.md (design rationale) | Matches CLAUDE.md's own framing; belongs with the stage overview, not the pitch |
| 64-73 | "Lexicon built" checklist item, cites 136,348 words | stale fact | docs/ARCHITECTURE.md or delete | **Stale**: PIPELINE.md and a fresh grep both show 136,456 rows in `LexiqueMixte.tsv`; README was never updated after a lexicon fix |
| 76-187 | Phoneme/biphoneme order example, ASCII bar charts and pairwise-order matrix for one worked layout run | design rationale | docs/ARCHITECTURE.md (phoneme order tables) | Illustrates `optimizeBiphonemeOrder`/layout statistics (Keyboard Layout Optimization (S4)); not regenerated data, should be labeled "worked example," not current output |
| 189-214 | Starboard single-keypress and 2-keypress ASCII keymap diagrams | current fact | docs/ARCHITECTURE.md (keyboard) | Matches `starboard3h.json`'s committed layout; worth a "generated from X, may drift" note |
| 216-219 | "Mapping of phonemes to physical keys" status note | current fact | README.md (status) or ARCHITECTURE.md | Accurate, consistent with PIPELINE.md's "no command regenerates starboard3h.json" |
| 221-227 | "Identifying homophones" — S6/S7 two-mechanism summary | already covered by docs/specs/discriminating-features.md, docs/specs/star-hash-marking.md | README.md (short pointer only) | Content duplicates the specs almost exactly (already uses current stage names); keep one sentence + links in README, drop the rest |
| 229-237 | "Treatment of verbs, prefixes, suffixes" — paradigm tables and prefix goal, not done | current fact / forward-looking | ROADMAP.md | Describes Phase 6 (densification/prefixes); belongs with forward-looking roadmap content, not the pitch page |
| 239-258 | Academic references (Lexique383, film-frequency paper, LexiqueInfra) | current fact | README.md or docs/ARCHITECTURE.md | Durable citation list; keep verbatim wherever it lands |

**Unique durable fact found:** none beyond the citations (already the only place they live).

## ROADMAP.md (674 lines)

Verdict: one live roadmap buried under ~500 lines of superseded status history; the file says
so itself ("describes the plan as originally conceived... a lot has since shipped, pivoted, or
been discarded"). Needs a hard split into forward-only content and an archived history doc/commit
trail.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-29 | Header: merge note, two homophone problems restated, reserved-key framing | history / design rationale | docs/ARCHITECTURE.md (design rationale) | The two-mechanism split is current and already stated better in discriminating-features.md/star-hash-marking.md §1; the "this inverts the code" framing is now just history |
| 30-138 | Status updates 2026-09-22 and 2026-09-21 (star/hash merge, canonicalization fix, subjonctif-imparfait removal) | history | already covered by docs/specs/star-hash-marking.md, docs/PIPELINE.md — file as history/commit-log entries or delete | Fully superseded prose the user already confirmed in Spec Extraction (Pass 2); merged-mark behavior, canonicalization and the corpus-size change are now stated as current fact elsewhere |
| 139-279 | Status update 2026-09-20 ("what was done" / "tried and discarded" / "what's left to do") | history, with one live sublist | "what's left to do" (240-279) → TODO.md; rest → history | The done/discarded bullets are pure history (rule stack, N-ary escalation, etc. now in star-hash-marking.md); the "what's left" bullets are still real open items (MARKING_OVERRIDES regeneration, bucket confirmation, `-er`/`-ers` wishlist, Phase 3/5/6/7 not started, satoptimizer.py cleanup, one orchestrated entrypoint) |
| 281-289 | "Terminology" — lemma-homophone vs same-lemma homophone definitions | already covered by docs/GLOSSARY.md | delete | GLOSSARY.md's "Lemma-homophone" and "Same-Lemma and Grammatical-Category Disambiguation (S6)" entries are the canonical, more precise version |
| 291-383 | "Current state, grounded in the code (audit)" — dated 09-15/17/18, explicitly superseded by its own header note | superseded | delete (or fold one paragraph into ARCHITECTURE.md history note) | The file itself says "does not hold" for everything except the phoneme-layer audit; keeping it invites re-reading stale claims |
| 384-413 | "Design decisions" 1-6 (reserved-key budget=2, `*`/`#` scope, conjugation-as-phoneme-keys since superseded by elicitation, fusion bug deferred, prefix goal, dual-target architecture) | design rationale, mixed with one superseded item | docs/ARCHITECTURE.md (decisions 1, 2, 6) / ROADMAP.md forward items (4, 5) / delete (3, superseded by elicitation-first pivot) | Decision 3 ("phoneme-key strokes chosen for orthographic meaning") is exactly what elicitation-first replaced; decisions 1/2/6 are still true constraints worth keeping as rationale |
| 415-583 | Roadmap Phases 0-7 with statuses (0/1/2/4 done, 3/5/6/7 not started) | forward-looking, mixed with done history | ROADMAP.md (phases 3, 5, 6, 7 and their "what's left" only); done phases → history | Phases 0/1/2/4's bodies duplicate the "what was done" section above; only the not-started phases and their goals are forward-looking content worth keeping live |
| 585-592 | "Ongoing" — untested cpsatsolver ambiguity math, README reconciliation note | forward-looking (partially stale) | TODO.md | The README reconciliation bullet is now done for the pipeline section (per this same bullet's own note) but not for the rest of README (confirmed above — README still has the 136,348 stale count) |
| 594-637 | Prior art survey (Pluvier, Lapwing, Javelin, Regenpfeifer, Grandjean, Michela) | design rationale | docs/ARCHITECTURE.md or ROADMAP.md (kept as an appendix) | Durable research, not tied to any status; matches memory's steno-prior-art note — no newer prior art doc exists, so this is the only copy |
| 639-665 | "Open questions" 1-9, several marked resolved inline | forward-looking, mixed | ROADMAP.md (only the still-open ones: 1 Javelin specifics, 3 layout freeze, 8 prefix strokes, 9 shared runtime engine) | Questions 2, 4, 5, 6, 7 are marked resolved in their own text and duplicate content now in PIPELINE.md/specs |
| 667-674 | "Verification approach" — pytest + Phase 0 checker + Phase 3 drift comparison | current fact | ROADMAP.md or CLAUDE.md | Still accurate process guidance |

**Unique durable facts found (not stated elsewhere in docs/ or code comments):**
- The `-er`/`-ers` noun wishlist item (reuse `Infinitif`/`Infinitif:p` instead of a star/hash mark
  for a whole NOM/VER sub-class) — lines 247-249, not sized/verified, not in todo.md.
- `MARKING_OVERRIDES` is admittedly not from one canonical run (lines 242-244) — matches
  star-hash-marking.md §3's own "provisional" note, but the *regenerate-it* action item itself
  only lives here.
- The Phase 6 dual-target/Javelin architecture decision (409-413) — matches the user's memory
  note but this is the only in-repo copy of the full reasoning.

## todo.md (384 lines)

Verdict: the live half (suspected bugs B1-B35, queued follow-ups) is exactly TODO.md's future
content and needs no rewrite; everything from "Live status (2026-09-20)" onward is historical
session log that should be compressed to a paragraph or dropped.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 5-121 | Suspected bugs B1-B35, tiered by impact, found during the docs refactor | current fact | TODO.md (keep, this file becomes TODO.md) | Live, current, cross-referenced from PIPELINE.md/GLOSSARY.md/specs by B-number; do not touch content |
| 122-144 | Queued follow-ups: renames (decision a12), no command regenerates starboard3h.json, realization-report drift, stale `.claude/settings.local.json` allow-list, "Phase G/P" strings still in runtime code | current fact | TODO.md (keep) | Live action items, still accurate per grep-checkable facts (file renames already done per DECISIONS.md, but the *string* renames listed here are explicitly still pending) |
| 146-161 | "Live status (2026-09-20)" pointer to ROADMAP.md/ATOMIC_KEYPRESS_REWIRE_PLAN.md as authoritative, branch name `phase-g-grouping`, test count 549 | history (stale pointer) | TODO.md, trim | Branch name and authority pointer are stale now that PIPELINE.md/specs are canonical (per DECISIONS.md); test count is a snapshot, not worth keeping |
| 163-225 | "Done this session" / "Still open from this session" (2026-09-17/18): `ambiguityIgnoreList.tsv`, `lexiconExclusions.tsv` refactor, open lexicon data-quality items (`baux` lemma, `baud` phonology, ghost lemmas `pars`/`sert`, broader re-validation checklist) | history, with live sub-items | TODO.md (only the still-unfixed data-quality bullets: `baux`, `baud`, ghost lemmas, broader re-validation checklist); rest → history | The "still open" bullets read as live per the file's own framing but were never folded into the B-numbered bug list — worth confirming with the user whether they're still unfixed |
| 227-238 | "History — superseded status snapshots" (old branch merges) | history | delete | File already labels this dead |
| 239-275 | The `"p"`/`"f_p"`/`"m_p"` feature-fusion bug, scoped but not started, tied to `src/greedyoptimizer.py`'s legacy selector | history / possibly superseded | Confirm with user, then TODO.md or delete | This bug lives in the superseded solver-picks-features machinery (`greedyOptimizeDiscriminator`); PIPELINE.md says only `GRAMCAT_PRIORITY` from that file is still live — this specific bug may no longer be reachable from the live pipeline. **Flag as a triage question**, not auto-classified |
| 276-370 | "Earlier resolved track" + "Outstanding work (now resolved)" + "Resolved this session" — pa:yer/ass:eoir dual-form gaps, Verbiste cross-checker triage | history | delete or fold into one line in Synthetic Lexicon Building (S2)'s section of PIPELINE.md | Already summarized as the one-shot fix scripts table in PIPELINE.md §S1 "One-shot fix scripts" |
| 371-384 | "If resuming from scratch" bootstrap instructions | history (stale) | delete | Superseded by this docs refactor itself; test counts and file-count claims are snapshots from 2026-09-20 |

**Unique durable facts found:**
- The `baux` comma-joined-lemma bug and the `baud` [bo]/[bod] pronunciation-sense bug (194-206) —
  concrete, still-unfixed lexicon defects not tracked anywhere else (not in the B-numbered list).
- The ghost-lemma list `pars`/`sert`/`bute`/`mar`/`lack`/`fy`/`mise`/`vins` (207-213) — same status.

## CLAUDE.md

Verdict: mostly current and accurate; one stale count (GramCat), the Architecture section
duplicates PIPELINE.md/GLOSSARY.md content that could shrink to a pointer.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-8 | Title + "Project Overview" paragraph | current fact | CLAUDE.md (keep) / mirror in README.md | Accurate, terse |
| 10-38 | Commands block (install, tests, mypy, lexicon build, pipeline scripts, elicitation/grouping/realization commands, exports) | current fact | CLAUDE.md (keep) | Cross-checked against PIPELINE.md's "How to run a full rebuild" table — commands and module paths match |
| 42-58 | "Processing Pipeline" 8-stage numbered summary with parenthetical code pointers | duplicate of docs/PIPELINE.md | CLAUDE.md (shrink to 1-2 lines + link) | This is a compressed restatement of PIPELINE.md's stage list; keeping both risks drift (PIPELINE.md is supposed to be the call-graph source of truth per its own header) |
| 60-65 | Core Data Model (grammar.py, word.py, keyboard.py one-liners) | current fact | docs/ARCHITECTURE.md (data model section) | Matches the ARCHITECTURE.md destination's stated scope ("data model") directly |
| 67-72 | Key Constants (AMBIGUITY_PENALTY=30000, ORDER_PENALTY=500, STROKE_ASSIGNMENT_PENALTY=1, 90s timeout) | current fact, verified | docs/ARCHITECTURE.md (design rationale) | Confirmed against src/cpsatsolver.py:25-27 — values are correct as stated |
| 74-95 | Conventions: X-SAMPA, syllable decomposition rule, `starboard3h.json` key layout (26 keys, reserved keys), TSV formatting, resource file sizes | current fact | docs/ARCHITECTURE.md / CLAUDE.md | All checks out (main-thread correction: CLAUDE.md already says 22 GramCat values; GLOSSARY.md:398's "(CLAUDE.md says 21)" note is the stale text) |

**No new unique durable facts** — CLAUDE.md is itself mostly a compressed pointer to facts that
live more precisely in PIPELINE.md/GLOSSARY.md now.

## LEXICON_RECOMPUTE_PIPELINE.md

Verdict: fully superseded by PIPELINE.md's "How to run a full rebuild" table and its "Five facts"
list, which cover the same two silent-failure traps with more precision (line numbers, current
call names). Safe to retire once RECOMPUTE.md exists.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-16 | Header + motivating incident (évaser bug, resolved_press_sets.json staying stale) | history | docs/RECOMPUTE.md (keep as a short motivating example) | Concrete, useful teaching example; not duplicated verbatim elsewhere, worth keeping as color even though the mechanism is now documented better |
| 18-28 | Full chain table (lexicon merge → paradigm completion → theory 1 → Elicitation → Grouping → Realization report → theory 2) | duplicate of docs/PIPELINE.md | docs/RECOMPUTE.md (rewrite from PIPELINE.md's table, don't hand-maintain a second copy) | PIPELINE.md's "How to run a full rebuild" table (steps 0-9) is the same information, kept current, with file:line anchors |
| 30-43 | Two silent-failure traps (pickle cache, realization_report.json separately tracked) | already covered by docs/PIPELINE.md | delete | PIPELINE.md's "Five facts" #2 and #4 state the same two traps with more detail (line numbers, which exporter reads what) |
| 45-53 | "What's usually safe to skip" — Grouping Phase rarely needs rerunning for a lexicon fix | current fact | docs/RECOMPUTE.md | Not stated elsewhere; a genuinely useful operational shortcut worth keeping |
| 55-73 | Checklist for a fix that changes theory-1 collisions (7 numbered steps) | current fact | docs/RECOMPUTE.md | Operational recipe, complements but doesn't duplicate PIPELINE.md's step table (this one is fix-specific ordering advice, not the general rebuild) |
| 75-78 | "Open follow-up" — pointer to ROADMAP.md's orchestration-script item | duplicate | delete | Already captured in ROADMAP.md "what's left to do" and now flagged in this inventory's ROADMAP.md row 139-279 |

**No new unique durable facts** beyond what's in the "safe to skip" and "checklist" rows, both
routed to RECOMPUTE.md above.

## steno-trainer/README.md

Verdict: current, accurate, scoped to its own subdirectory; only touches the main pipeline at the
export commands, which match PIPELINE.md exactly. No action needed beyond leaving it in place.

| Lines | Summary (plain words) | Category | Recommended action → destination | Reason |
|---|---|---|---|---|
| 1-17 | What the trainer is, modes (Words/Sentences/Definitions), hints/IPA toggles | current fact | steno-trainer/README.md (keep) | Matches memory's steno-trainer-deploy note; no changes needed |
| 18-32 | Stack (Elm + a small JS serial shim) | current fact | steno-trainer/README.md (keep) | Scoped to this subproject, not part of the main pipeline doc set |
| 34-52 | Data section: which JSON files, regenerate commands, sentence source (`candidate_sentences.jsonl`, LLM-annotated) | current fact | steno-trainer/README.md (keep) | Export commands (`export_keyboard_layout`, `export_practice_words`, `export_practice_sentences`, `export_definitions`) match CLAUDE.md and PIPELINE.md's Theory Export (S8) trainer branch exactly, including the ordering dependency |
| 54-63 | Local development instructions | current fact | steno-trainer/README.md (keep) | Standalone, no cross-file dependency |
| 65-85 | Known limitations (Chromium-only, secure-context requirement, per-stroke feedback, Gemini PR keymap caveat) | current fact | steno-trainer/README.md (keep) | Matches memory's plover_integration note (hardware-verified keymap caveat) |

**No new unique durable facts** — self-contained and already correct.

## Questions for triage

1. ROADMAP.md: confirm the split — keep only Phases 3/5/6/7 + open questions 1/3/8/9 as the live
   roadmap; archive everything else (lines ~30-413, most of 415-583) as history. OK to gut this
   aggressively, or keep a compressed "what shipped" appendix?
2. README.md's 136,348-word count (line 73) is stale (actual: 136,456). Fix now or leave for the
   rewrite pass?
3. todo.md lines 194-213 (`baux`, `baud`, ghost-lemma data bugs): still unfixed? Should they get
   B-numbers and move into the "Suspected bugs" list, or are they already superseded?
4. todo.md lines 239-275 (the `"p"`/`"f_p"`/`"m_p"` feature-fusion bug): is this still reachable
   from the live pipeline, or dead along with the superseded `greedyOptimizeDiscriminator` selector
   it's scoped against? (`GRAMCAT_PRIORITY` in the same file is confirmed live; the rest of that
   module's status is unclear from PIPELINE.md alone.)
5. CLAUDE.md's Architecture section (lines 42-58) duplicates PIPELINE.md's stage list almost
   verbatim — shrink to a pointer, or is some redundancy wanted for a reader who won't open
   PIPELINE.md?
6. (Corrected by main thread) CLAUDE.md already says 22 GramCat values; the stale text is
   GLOSSARY.md:398's "(CLAUDE.md says 21)" note — drop it in Doc Rewrite (Pass 6)?
7. LEXICON_RECOMPUTE_PIPELINE.md: confirm it's fully retired once docs/RECOMPUTE.md exists (only
   two rows have unique content — the évaser example and the "safe to skip" note — everything else
   is already superseded by PIPELINE.md).
8. ROADMAP.md's `-er`/`-ers` noun wishlist item and the `MARKING_OVERRIDES` regeneration item: keep
   in the new ROADMAP.md, or move to TODO.md since they're concrete, scoped action items rather than
   open-ended roadmap phases?
</content>
