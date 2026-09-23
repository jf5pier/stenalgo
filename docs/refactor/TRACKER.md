# Docs refactor tracker

Resume prompt after `/clear`: *"Continue the docs refactor — read docs/refactor/TRACKER.md."*

Full plan: `~/.claude/plans/i-want-to-do-greedy-blum.md` (approved 2026-09-22).
Branch: `docs-refactor` (off `main` at 43bc6f5). This whole `docs/refactor/` folder is
deleted in Final Check and Cleanup (Pass 7).

## Ground rules
- No live behaviour change. Proof: `bash docs/refactor/rebuild_and_hash.sh > docs/refactor/<label>.md5`
  then `diff docs/refactor/baseline.md5 docs/refactor/<label>.md5` must be empty.
- `pytest src/test/` baseline: **593 passed**.
- Naming: every stage/phase/pass is cited by a descriptive name with its code in
  parentheses — "Marker Grouping (Phase G)", "Lexicon Building (S1)" — never the bare code.
- Dead code: removed only with per-item user approval, one commit per group.
- Suspected bugs go to `todo.md` (`## Suspected bugs (from docs refactor)`), never fixed here.
- Triage: AskUserQuestion rounds of up to 4 blocks; log every answer in `DECISIONS.md` immediately.
- Comment/docstring edits in `.py` files pointing at removed docs: ask first.

## Status
| Pass | Status | Notes |
|---|---|---|
| Setup and Baseline (Pass 0) | done | snapshot commit 5ae0118; `baseline.md5` (PYTHONHASHSEED=0, reproduced twice) |
| Pipeline Call Graph and Glossary (Pass 1) | in progress | Skeleton (1a) + 4 stage files (1b) done; Merge (1c) running → docs/PIPELINE.md, docs/GLOSSARY.md, callgraph/90-findings.md, 91-review-questions.md |
| Spec Extraction (Pass 2) | todo | |
| Doc and Data Inventory (Pass 3) | todo | outputs in `inventory/` |
| Interactive Triage (Pass 4) | todo | log in `DECISIONS.md` |
| Dead-Code Removal (Pass 5) | todo | `deadcode.md` |
| Doc Rewrite (Pass 6) | todo | |
| Final Check and Cleanup (Pass 7) | todo | |

## Baseline notes
- Without a pinned seed, clean rebuilds change `phase_p_keypress_realization.json`'s residual
  lists (Word.__hash__ is a salted hash stored in the pickles). The committed copy was built
  from older pickles; `rebuild_and_hash.sh` hashes the seed-0 version then restores the
  committed file. Plover dictionary and trainer exports are identical to the committed ones.
- A full rebuild takes ~7.5 min.

## Next action
Merge (Pass 1c) result → Glossary Review (Pass 1d) with the user, using
`callgraph/91-review-questions.md`; then add suspected bugs from `callgraph/90-findings.md`
to todo.md after walking the user through them.
