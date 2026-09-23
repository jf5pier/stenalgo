# Triage decisions log (append-only)

Format: `block-id | source file:lines | decision | destination | note`

## Scoping decisions (2026-09-22, before Pass 0)
- New docs under `docs/`; root keeps README.md, CLAUDE.md, TODO.md, ROADMAP.md, LICENSE.
- Dead code: remove with per-item approval.
- Triage also covers stale data files and untracked `scratch/`.
- Triage via multiple-choice rounds.
- Stages/phases/passes get descriptive names, code in parentheses, cited by name.
- `steno-trainer/user.json`, `user_fr.json`: personal Plover dictionaries, not committed in the snapshot (triage later).
