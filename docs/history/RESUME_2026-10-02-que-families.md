# RESUME 2026-10-02 — abbreviations branch: que-family regrouping (in progress)

Continues `RESUME_2026-10-01-abbreviations.md` (read it first for the mission,
the phase history, the round-2 decisions and the pitfalls; this file only
covers what happened after its item 12).

## 1. Where things are

- Worktree: `/home/jfsp/Steno/stenalgo-briefs` (branch `abbreviations`, tracks
  `origin/abbreviations`, last pushed tip `1076a3c`). Work and run everything
  from there. The main checkout `/home/jfsp/Steno/stenalgo` is on `main`.
- Interpreter: `/home/jfsp/Steno/stenalgo/env/bin/python` (bare `python` is
  not on PATH; the worktree has no `env/`).
- Gitignored build artifacts were copied from the main checkout into the
  worktree (Dictionary/PhoneticTheory/DisambiguatedTheory/AffixSelection
  pickles, phonetic_theory.tsv, disambiguated_theory.tsv, questionnaire.json,
  resolved_press_sets.json). On this branch `.gitignore` is older, so
  `AffixSelection.pickle` shows as untracked: NEVER `git add -A`.
- Untracked, not part of this work: `AffixSelection.pickle`, `log_last_session`,
  a stray box-drawing-named file in the root.
- UNCOMMITTED, UNTESTED code edits (see section 3): `src/expressionrules.py`,
  `scratch/select_expression_rules.py`. Neither the test suite nor the driver
  has been run since the edits. `mypy src/expressionrules.py` is clean.

## 2. Decisions made this session (2026-10-02)

- **Budget confirmed: 15** (`EXPR_RULE_BUDGET = 15`; sweep peak: 14.0% saving
  from attaches alone, 272 exceptions; past 15 the disjointness crowding
  degrades the strong families).
- **The que domain is regrouped by the FOLLOWING word's category**, replacing
  the old "lemma of the first unit" family (which merged `que je/l'/nous` into
  one family and split `qu'` off as an accidental `qu` family):
  - `que+def`: que le / la / l' / les
  - `que+indef`: qu'un / qu'une / que des (+ du)
  - `que+dem`: que ce / ces / cet / cette
  - `que+pron`: que je, tu, nous, vous; qu'il, elle, on, ils, elles
  - `que`: bare que / qu' before any other word
- **No family is guaranteed a slot.** Briefs, attaches and plain composition
  all compete in the same greedy/solver under the budget of 15.
- **`que+pron` is differentiated by briefs, not by `*`/`#` selectors**, so it
  gets no attach candidates. Briefs may span 2+ syllables; whether one is worth
  it is the solver's decision (marginal saving vs FORM_COST).
- Pool sizes for reference (2-token runs): que+def ~83M, que+indef ~21.6M,
  que+dem ~10M, que+pron ~188M (qu'il 67.9M, qu'elle 30.5M, que je 25.8M).
  que cet / que cette are below the candidate-pool floor.

## 3. Code edits made (uncommitted)

`src/expressionrules.py`:
- `EXPR_RULE_BUDGET` 30 -> 15 (comment updated).
- New `MAX_BRIEF_FAMILY_VARIANTS = 8`; `selectExpressionRules` now caps family
  absorption per kind (briefs 8, attaches `MAX_FAMILY_VARIANTS` = 4).
- `briefCandidates(pool, familyOf=None)`: briefs can carry a family so they
  compete with the family's attaches in one greedy.
- New `_fallbackPair`: a brief nested inside an attach span (or the reverse)
  is a fallback, not a territory contest; the mate check in the selection loop
  skips such pairs. Only partially-intersecting spans contest territory.
- New `assignBriefStrokes(selected, pool, ctx, freeChords, takenStrokes)`:
  derives each selected brief's stroke via `deriveBriefStroke`, descending
  frequency, shared taken set; sets `beta`/`exactDone`.
- `auditExpressionRules` composes selected briefs (with `beta`) as well as
  attaches.
- NOTE: my first edit to `territoryOverlap` swallowed its `def` line; repaired
  and syntax-checked, but re-read that function once to be sure.

`scratch/select_expression_rules.py`:
- New `queFamilyOf` classifier (sets QUE_DEFINITE/INDEFINITE/DEMONSTRATIVE/
  PRONOUNS); `familyOf` = `queFamilyOf(units) or lemma`; briefs get the que
  family; attach candidates of family `que+pron` are filtered out.
- New brief-stroke stage after Stage B (`assignBriefStrokes`); briefs with no
  derivable stroke are dropped; `selBriefTaken` holds every selected brief's
  stroke.
- Stage C collision loop: briefs are included in the composed rules and in the
  collision signatures; a colliding BRIEF family re-derives its strokes.
- `rulesJoint` and the forced-brief section's `withBriefs` include the
  selected briefs.

## 4. Next steps

1. Forced-brief section: make it use `selBriefTaken` as its initial
   `takenStrokes` (today it starts from an empty set and could reuse a stroke a
   selected brief holds), and exclude expressions already covered by selected
   briefs (the `covered` loop uses `rulesJoint`, which now includes them).
2. Check the report writers: `expr-rules.tsv` is built from
   `rulesFinal = [attach rules]` only; selected briefs need rows (family,
   strokes via `renderFinalStrokesToRTFCRE`, per-rule attribution from
   `traced.segments` with `seg.kind == "brief"`). The `expr-rules-final.json`
   dump and `expr-rules-proxy.tsv` need the `beta` strokes too.
3. Add tests in `src/test/expressionrules_test.py`: `_fallbackPair` (nested vs
   partial), `assignBriefStrokes` (distinct strokes, failure keeps beta None),
   the brief family cap (more than 4 brief variants absorbed), `queFamilyOf`
   (move the classifier into `src/` or test it via the driver's constants),
   `briefCandidates(familyOf=...)`, and the audit with briefs.
4. Run `PYTHONUNBUFFERED=1 env/bin/python -m pytest src/test/` (786 green
   before these edits), then the driver in the background with a log
   (~3-4 min): `PYTHONUNBUFFERED=1 /home/jfsp/Steno/stenalgo/env/bin/python
   scratch/select_expression_rules.py > scratch/que_run.log 2>&1`.
5. Read the result with the user: which of the 6 que families won slots, which
   mechanism each got (brief / attach / composition), total saving vs the
   16.4%/18.9% baseline in the previous resume, 0 shadows, 0 collisions. The
   previous baseline was with budget 15 attaches + 40 forced briefs.
6. Then the old list: residual collision polish ("ce n' est pas le" vs "ce qui
   n' est pas"), and Phase 4 (wiring into the theory build + Plover export;
   docs owed before any merge: CLAUDE.md, docs/PIPELINE.md, docs/GLOSSARY.md).

## 5. Stop and ask the user when

- Any push to origin or merge into main.
- The solver drops a high-mass que family entirely, or briefs for the pronoun
  family look unlearnable (e.g. free-chord strokes for most of the 8).
- Changing the family cut again (it is the user's own design).

## 6. Process notes

- User preferences (unchanged): delegate mechanical work to cheaper subagents;
  commit only when asked; push only when asked.
- Question UI: do not put carriage returns in AskUserQuestion labels; the user
  saw garbage characters in two consecutive questions this session.
