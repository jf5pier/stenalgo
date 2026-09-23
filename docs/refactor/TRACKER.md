# Docs refactor tracker

Resume prompt after `/clear`: *"Continue the docs refactor — read docs/refactor/TRACKER.md."*

Full plan: `~/.claude/plans/i-want-to-do-greedy-blum.md` (approved 2026-09-22).
Branch: `docs-refactor` (off `main` at 43bc6f5). This whole `docs/refactor/` folder is
deleted in Final Check and Cleanup (Pass 7).

## Ground rules
- No live behaviour change. Proof: `bash docs/refactor/rebuild_and_hash.sh > docs/refactor/<label>.md5`
  then `diff docs/refactor/baseline.md5 docs/refactor/<label>.md5` must be empty.
- `pytest src/test/` baseline: **593 passed**.
- Naming: every stage/pass is cited by a descriptive name with its code in parentheses —
  "Lexicon Building (S1)", "Spec Extraction (Pass 2)" — never the bare code. Phases get meaningful
  names only, no letter codes: "Discriminating-Feature Grouping (Grouping Phase)". Canonical
  vocabulary: `docs/GLOSSARY.md` (decisions in `DECISIONS.md`, Glossary Review (Pass 1d)).
- Agent work: use cheaper models or lower effort for mechanical work (renames, comment edits),
  and offer a "wrap up leaner" option before launching long agents (user preference).
- Dead code: removed only with per-item user approval, one commit per group.
- Suspected bugs go to `todo.md` (`## Suspected bugs (from docs refactor)`), never fixed here.
- Triage: AskUserQuestion rounds of up to 4 blocks; log every answer in `DECISIONS.md` immediately.
- Comment/docstring edits in `.py` files pointing at removed docs: ask first.

## Status
| Pass | Status | Notes |
|---|---|---|
| Setup and Baseline (Pass 0) | done | snapshot commit 5ae0118; `baseline.md5` (PYTHONHASHSEED=0, reproduced twice) |
| Pipeline Call Graph and Glossary (Pass 1) | done | docs/PIPELINE.md, docs/GLOSSARY.md, callgraph/90-findings.md; todo.md "Suspected bugs" (B1–B35) and "Queued follow-ups"; new terminology in all Markdown and in `.py` comments/docstrings; file renames (below) |
| Spec Extraction (Pass 2) | done | docs/specs/star-hash-marking.md, docs/specs/discriminating-features.md; comment-only docstring fixes (DECISIONS p2-q1) |
| Doc and Data Inventory (Pass 3) | done | leaner run (2 Sonnet agents); `inventory/{A,B,C,D}.md`; main-thread spot-check corrections appended in A.md (GramCat count) and C.md (9 `.py` RESUME links) |
| Interactive Triage (Pass 4) | todo | log in `DECISIONS.md` |
| Dead-Code Removal (Pass 5) | todo | `deadcode.md` |
| Doc Rewrite (Pass 6) | todo | |
| Final Check and Cleanup (Pass 7) | todo | |

## Baseline notes
- Without a pinned seed, clean rebuilds change `realization_report.json`'s residual
  lists (Word.__hash__ is a salted hash stored in the pickles). The committed copy was built
  from older pickles; `rebuild_and_hash.sh` hashes the seed-0 version then restores the
  committed file. Plover dictionary and trainer exports are identical to the committed ones.
- A full rebuild takes ~7.5 min.
- File renames in df71a24 (full table in `docs/GLOSSARY.md` "Renamed files"): `src/phaseg.py` →
  `src/featuregrouping.py`, `src/phasegsat.py` → `src/featuregroupingsat.py` (and their tests),
  `util/build_phase_g_assignment.py` → `util/build_keypress_groups.py`,
  `util/build_phase_p_realization.py` → `util/build_realization_report.py`,
  `phase_g_keypress_assignment.json` → `keypress_groups.json`,
  `phase_p_keypress_realization.json` → `realization_report.json`. `baseline.md5` was refreshed
  after the renames (identical hashes, new file names).

## Next action
**Interactive Triage (Pass 4)** — AskUserQuestion rounds of up to 4 blocks, order: README → ROADMAP →
todo.md → CLAUDE.md → plan/design docs (inventory/B.md) → RESUME files (inventory/C.md, only the
blocks with unique facts: RESUME_2026-09-22-trainer-features.md's 4 open items) → data files and
scratch (inventory/D.md). Source of questions: each inventory file's "Questions for triage" list.
Log every answer in DECISIONS.md immediately. No doc edits during this pass.

## Notes for later passes
- Dead-Code Removal (Pass 5): Keyboard Layout Optimization (S4) is **not** dead code (decision
  b5). The greedy `src/featuregrouping.py` path is test-only — a removal candidate.
- Doc Rewrite (Pass 6) link check: `src/ambiguitychecker.py` still cites
  `RESUME_2026-09-20-starhash-priority.md` (:86, :99); point those at `docs/specs/star-hash-marking.md`
  if the RESUME file is deleted.
