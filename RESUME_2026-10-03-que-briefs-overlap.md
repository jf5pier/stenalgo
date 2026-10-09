> SUPERSEDED in part by `RESUME_2026-10-04-selector-order-and-variants.md` (slot budget is now 20, suffix-word list, selector order, order ban).

# RESUME 2026-10-03 — abbreviations branch: que families, attach-overlap policy (session paused for a memory-limit restart)

Continues `docs/history/RESUME_2026-10-02-que-families.md` (which continues `docs/history/RESUME_2026-10-01-abbreviations.md`: mission, phase history,
round-2 decisions, pitfalls). Read `NOTES_2026-10-03-attach-overlap-and-plover-decoder.md` for the design discussion.

## 0. UPDATE (later the same day) — read this first; sections 1-5 below are the state BEFORE it

Done, in order, with the user's go at each step:
1. Overlap refactor verified behaviour-neutral (md5s of the six `scratch/expr-*` outputs identical at limit 0).
2. Hostless adjacent attaches compose (`attachCluster`, `src/expressions.py`): attaches alone 14.4% -> ~22% of pool longform strokes,
   exceptions 305 -> ~175-206 (see the seed caveat below). Section 4's "key finding" is therefore resolved: `qu' il` / `que je` bare now save 1.
3. que briefs: user chose option 1, NO que briefs. `QUE_BRIEF_BUDGET` and the driver's que-brief stage are gone; `queFamilyOf` stays.
4. Option 2 (brief wins when its attach fails) was built, measured (+2.9% with briefs) and REJECTED/removed for decodability; details in
   the NOTES file, section 5.
5. `util/build_affix_rules.py` (MAIN checkout, not this worktree; committed there as `d571891`): `--workers` default is now `min(8, os.cpu_count())`.
   The docs' "~2.5 min on 16 cores" timings (CLAUDE.md, docs/PIPELINE.md, docs/ARCHITECTURE.md, the module docstring) were left unchanged.
6. Committed on `abbreviations` (not pushed). Tests: 807 pass. `mypy` run bare in this worktree needs checking (a bare call from the repo root
   with the worktree's mypy.ini was not verified at the end).

7. FIXED: the driver was hash-seed dependent (Stage C repair CP-SAT multi-worker, equal optima): now `num_workers = 1`, `random_seed = 0`.
8. FIXED: suffix `le`/`les` saved 0 because the prefix twin of the same expression always won at a trailing particle; `planStream` now
   yields to the suffix twin when nothing follows and a token precedes (`scratch/why_suffix_le.py`). Stage C feedback rounds raised 3 -> 6
   (the converged run needs 4).

CURRENT RESULT (deterministic, seeds 1 and 2 identical): attaches alone 23.3% of pool longform strokes (3.328e9), 123 exceptions, 0 shadows,
0 collisions; with the 40 forced briefs 4.088e9. Baseline md5s: `scratch/md5_expr_deterministic.txt`. 808 tests pass.

NEXT (ranked): (a) review the low-mass rules (`je ne`, `je me`, `ce qu' il`, `pas le`) and the slot list now that suffix `le`/`les` fire;
(b) max-1-key overlap study (section 5 item 5; just `EXPR_MAX_SHARED_KEYS`, needs the decoder decision, NOTES section 4);
(c) Phase 4: wiring into the build + Plover export + docs (CLAUDE.md, docs/PIPELINE.md, docs/GLOSSARY.md), required before any merge to main;
(d) drop the temporary `from __future__ import annotations` in `src/affixes.py` when main is merged. MAIN checkout: commit `d571891`
caps the affix search at 8 workers (done and committed there, not pushed). Nothing is pushed on either branch.

(Section 5 items 1-3 and the `le`/`les` part of 4 are done; see NEXT above.)

## 0b. UPDATE (end of the same day) — low-mass review and the family-merge experiment; read after section 0

State: branch `abbreviations`, HEAD `fb5b79d`; uncommitted: `scratch/select_expression_rules.py` (opt-in family merge, collapse/collision
prints), new untracked `scratch/trace_families.py`, `scratch/why_shadow.py`, `scratch/before_families/`, `scratch/after_families/`, run logs
`scratch/que_run_families*.log`. The tracked `scratch/expr-*` outputs were RESTORED from git: `md5sum -c scratch/md5_expr_deterministic.txt` passes.
The default driver run therefore reproduces the baseline (23.3%, 123 exceptions, 0 shadows, with briefs 4.088e9).

1. NEXT (a), low-mass review, done on the baseline outputs (no re-run). The `je`/`ce` families and `je ne`/`je me`/`ce qu' il` are no longer
   selected (un/une took their slots). Weak selected rules (strokes saved vs exception mass in `expr-rules.tsv`): `pas` prefix 5.5M vs 210M,
   `pas le` 3.2M vs 6.2M, `dans ce` 2.6M vs 7.4M, `dans` prefix 42M vs 365M. UNVERIFIED caveat: the pool composes bare n-grams, so the `pas`/`dans`
   exception mass may be the hostless-token artifact (section 4); not yet checked in running text, nor whether `strokeFreqSaved` is already net.
2. Family-merge experiment (user request): `un`/`une` as ONE family (both positions), and `le`/`la`/`l'`/`les` as ONE PREFIX-only family (their
   suffix rules keep their lemma families). Implemented in the driver only, now OPT-IN: `FAMILY_MERGE=1` (plus `DEF_SUFFIX_FAMILY=1` to also bundle
   the definite suffixes into a second family). Outputs of the merged run: `scratch/after_families/`, log `scratch/que_run_families3.log`.
   RESULT, WORSE: attaches alone 21.8% (3.124e9), exceptions 133, 1 shadow (`il y`), with briefs 3.871e9 (baseline 23.3%, 123, 0, 4.088e9).
3. Why (traced with `scratch/trace_families.py`, then the driver's new prints):
   - Selection and `pruneRedundantVariants` are NOT the cause: after selection `l'`, `le`, `les` prefix, `un` prefix, `une` prefix/suffix are all
     in their families. Stage C's "selector collapse" (driver, `select_expression_rules.py`) then drops them: `l'` prefix, `un` prefix, `une` prefix,
     `une` suffix. It also drops variants of untouched families (`il y`, `ne`, `je me`, `pas de`, `de`, `de la`, `n' y`): the mechanism is general,
     whether those drops also occur in the baseline was not checked.
   - Collisions (round 0 audit): `que la` vs `que l'` share the outline (10,18,19,20,23): `que` prefix carries `*` (key 10), the `la` variant has no
     selector and the `l'` variant has `*`, so the que `*` swallows the selector (INFERRED from the key sets, not traced rule by rule);
     `il y a un` vs `il y a une` the same way (the host `a` already carries marks; inferred). The other round-0 collisions are `il y a`/`il n' a`,
     `on ne`/`n' ont`, `que je ne`/`que je me`, `n' y a pas`/`n' y a pas de`, `ce n' est pas le`/`ce qui n' est pas`.
   - The `il y` shadow (VERIFIED, `scratch/why_shadow.py`): collapse drops the `il y` prefix rule (kept `il n'`), so `il y` composes the `il` prefix
     (7,22) onto the host `y` (13) = (7,13,22), the existing outline of the NOM `tine` (`tin`). Hard no (Q7). Round 0 had 0 shadows; it appears from round 1.
   - `la` suffix (461M, the best single rule before), `l'` suffix and `une` suffix lose the SLOT competition, not a bug: as free siblings of the
     `la`/`l'` families they cost no slot, as standalone families they do, and `je`, `ce`, `pas`, `le` suffix won those slots.
4. Open decision (user's): (1) revert both merges (the default now); (2) keep only `un`/`une`, which needs the collapse step improved first;
   (3) improve the collapse heuristic: it keeps only the highest-frequency colliding variant of a family; try another base/selector per variant
   before dropping any (a bigger change, touches every family; recommended). The user said "merge un/une for sure" BEFORE this result;
   confirm before treating it as final. Also unresolved: the `un`/`une` collapse log lines look inconsistent (`kept une` while `un` suffix is the
   higher-frequency variant and ends up the sole survivor).
5. Not verified: bare `mypy` in this worktree (no `mypy.ini` here; it exists on main). 808 tests were not re-run this session (no `src/` change).
6. PROCESS LESSON: never wait for a background job with `pgrep -f NAME`; it matches the waiting shell's own command line and never ends (it cost
   two false "still running" reports). Wait on the job's log (`until grep -q DONE LOG; do sleep 15; done`) or its task id. Now in CLAUDE.md.

## 1. Where things are

- Worktree `/home/jfsp/Steno/stenalgo-briefs`, branch `abbreviations` (HEAD `58d0480`, tracks origin, last pushed `1076a3c`;
  58d0480 is local only). Main checkout `/home/jfsp/Steno/stenalgo` is on `main`. Interpreter:
  `/home/jfsp/Steno/stenalgo/env/bin/python`, run with `PYTHONPATH=.` from the worktree. Driver runs need more memory than the
  previous session allowed (a run was killed/stopped at Stage C); run ONE heavy job at a time, in the background with a log.
- (Superseded by section 0: committed later.) Nothing was committed since `58d0480`. NEVER `git add -A` (untracked `AffixSelection.pickle`, `log_last_session`, a box-drawing-named file).
  Commit and push only when the user asks. No merge of main for now (user decision 2026-10-03).
- Tests: `PYTHONPATH=. env/bin/python -m pytest src/test/ -q` -> **804 passed** (resources present via the worktree). `mypy` clean on
  `src/expressions.py`, `src/expressionrules.py`, `src/test/expressions_test.py`, `src/test/expressionrules_test.py`.

## 2. Uncommitted changes (all intentional)

- `src/expressionrules.py`: `EXPR_RULE_BUDGET=15`; `MAX_BRIEF_FAMILY_VARIANTS=8`; briefs carry a family (`briefCandidates(familyOf=)`);
  `_fallbackPair` (a brief nested with an ATTACH is a fallback, not a territory contest; brief-in-brief and attach-in-attach still
  contest — fixed 2026-10-03); `assignBriefStrokes`; the audit composes selected briefs; `QUE_BRIEF_BUDGET=12`.
- `src/expressions.py`: **own overlap policy** — `EXPR_MAX_SHARED_KEYS = 0` and `attachKeysOverlap(neighbour, keys, maxShared=None)`
  ("refuse when more than maxShared syllabic keys are shared"); the composition no longer imports `ruleKeysOverlap` from `src.affixes`
  (main's affix layer decides its own partial-overlap mode; the expression layer must stay strict for a decoding Plover plugin).
- `src/affixes.py`: ONE TEMPORARY line, `from __future__ import annotations` at the top (this branch's affixes.py failed to import on
  Python 3.12: `Candidate` used before its class; main fixed it). Drop it when main is merged.
- `src/test/expressionrules_test.py` (+14 tests: brief families, `_fallbackPair`, `assignBriefStrokes`, audit with briefs) and
  `src/test/expressions_test.py` (+4 `attachKeysOverlap` tests).
- `scratch/select_expression_rules.py`: `queFamilyOf` (que+def / que+indef / que+dem / que+pron / que; `j'` added to the pronoun set),
  brief-stroke stage, forced-brief section starts from the selected briefs' strokes and skips their expressions, report writers
  (`expr-rules.tsv`, `expr-rules-proxy.tsv`, `expr-rules-final.json` with `beta`) carry the selected briefs, a que+pron brief stage
  (`QUE_BRIEF_BUDGET`) with a per-brief "fires / EATEN by attach" log line.
- `scratch/expr-*.tsv|json` regenerated by the last COMPLETE driver run (the one with the que-brief stage, before the overlap refactor).
- `TODO.md`: new section "Branch TODO — max-1-key overlap". New file `NOTES_2026-10-03-attach-overlap-and-plover-decoder.md`.
- Untracked helpers saved from the scratchpad: `scratch/md5_expr_before_overlap_refactor.txt` (md5s of the six `scratch/expr-*` outputs
  before the overlap refactor), `scratch/que_run_complete.log` (log of that complete run), `scratch/why_quil.py` (compose qu'/il/que je
  with the final rules and print segment outcomes; `PYTHONPATH=. env/bin/python scratch/why_quil.py`). `scratch/que_run.log` holds the
  PARTIAL log of the stopped rerun — ignore it.

## 3. Last complete driver result (15 attach slots, 27 attach rules, 8 que+pron briefs, 40 forced briefs)

- Attaches alone: 14.4% of pool longform strokes saved (2.064e9 of 1.430e10), 305 exceptions, 0 shadows, 0 collisions. With all briefs
  2.782e9 (~19.5%). Slots: de(de, d'), à, que(qu', que), ne(n', ne, n' y), dans, et, il, c', la, le (suffix+prefix), pas (pas, pas le),
  les (suffix+prefix), l', je (je, je ne, je me), ce (ce, ce qui, ce que, ce qu' il). Suffix `le` and `les` save 0 (never fire) — unexplained.
- All 8 que+pron briefs (qu'il `p-`, qu'elle `v-`, que je `kvt@a`, qu'on `R-`, qu'ils `k-s`, que nous, que vous, que tu) are EATEN: attaches
  are tried first. `que j'` is gone as a rule; `que j'ai` (4.5M, 3 units) is below the 5M floor and the que stage takes 2-unit
  expressions only.

## 4. Key finding (corrects an earlier claim in the session)

The pool composes BARE n-grams. `qu' il` -> `k-/il` (saving 0) and `que je` -> `k@a/vt@a` (saving 0) fail with `noNeighbour`: qu'/que and
il/je are BOTH attach rules, so the second consumes the host token and neither finds a content stroke. In running text they compose fine:
`qu' il est` -> `tiejkdtR` (3 strokes -> 1), `que je suis` -> `sp*@aijkdtR/-k`. The briefs add nothing in context; the "94M strokes
gained" estimate quoted earlier was a pool artifact. See NOTES section 5.

## 5. Open decisions / next steps (user's call; recommend in this order)

1. **Re-run the driver** (needs the higher memory limit; ~4-5 min, background, `PYTHONUNBUFFERED=1 ... > scratch/que_run.log`) and compare
   `md5sum -c scratch/md5_expr_before_overlap_refactor.txt`: the overlap refactor at limit 0 must be behaviour-neutral (the two
   Stage C rounds seen before the stop matched: collisions 2 then 3, 0 shadows). If identical, tell the user; otherwise find the diff.
2. **The user's request, not yet done**: read `planStream` and `composeOutlineTraced` (`src/expressions.py`) to find where adjacent attaches
   (qu' + il) are rejected. Want: two adjacent attaches compose with each other (merge into one stroke) unless their keys conflict; then
   evaluate `qu'il` as an attach rule with its own keypress. Also consider testing pool particle/pronoun n-grams WITH a trailing host token.
3. Decide the que briefs' fate (option 3 "leave it" now looks right: drop the 8 briefs and `QUE_BRIEF_BUDGET`, or keep only where the attach
   fails) and whether `que j'ai` gets a brief (floor/3-unit exception).
4. Investigate why suffix `le`/`les` save 0; low-mass rules (`je ne`, `je me`, `ce qu' il`, `pas le`).
5. Max-1-key overlap study (NOTES section 4; just set `EXPR_MAX_SHARED_KEYS`/`maxShared`; NOT implemented). Plover: a decoding dictionary
   plugin is required for attach families (NOTES section 3).
6. Old list: residual collision "ce n' est pas le" vs "ce qui n' est pas"; Phase 4 (wiring into the build + Plover export; docs owed:
   CLAUDE.md, docs/PIPELINE.md, docs/GLOSSARY.md) before any merge to main.

## 6. Merge notes (for when main is merged)

- Drop the temporary `from __future__` line in `src/affixes.py`; main's affix files will otherwise win the merge (trial merge-tree was clean).
- The expression layer is decoupled from main's `ruleKeysOverlap(partialOverlap=True)` default; nothing to patch there.
- Update doc paths in the older resumes (`/home/jfsp/stenalgo-fix` is stale).

## 7. Stop and ask the user when

- Any push, any merge into main, any change of the que family cut (the user's own design), changing the budget of 15, or touching main's affix code.

## 8. Process notes

- User preferences: commit/push only when asked; delegate mechanical work to cheaper subagents; no carriage returns in AskUserQuestion labels.
- Long runs: background + log; never chain `sleep`; wait with a Monitor until-loop on the log's last line.
