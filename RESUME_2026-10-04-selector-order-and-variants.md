# RESUME 2026-10-04 — abbreviations branch: suffix words, budget 20, selector order, order ban, variant selection

Continues `RESUME_2026-10-03-que-briefs-overlap.md` (read it and its predecessors for the mission, the phase history and the pitfalls).
Numbers and the run-by-run comparison: `RESULTS_2026-10-04-slot-budget-sweep.md`. Vocabulary (Stage A/B/C, proxy, absorbed, collapsed, stack,
family, selector...): `docs/GLOSSARY.md`, section "Expression abbreviation layer". Open items: `TODO.md` (two new branch sections).

## 1. State

- Worktree `/home/jfsp/Steno/stenalgo-briefs`, branch `abbreviations`. Commits of this session: `51d18a7` (suffix words, unigram evidence, budget 20),
  `9e8e5d7` (selector order, order ban, 3+-grams as briefs), then the final commit of this session (docs, switches, selector override).
  Nothing is pushed. Interpreter `/home/jfsp/Steno/stenalgo/env/bin/python`, `PYTHONPATH=.`. Tests: 818 pass. One heavy job at a time, in the
  background with a log (the driver takes about 5 minutes: `PYTHONPATH=. env/bin/python scratch/select_expression_rules.py [budget]`).
- Committed result (budget 20): attaches alone 25.7% (3.672e9 of 1.430e10 pool longform strokes), 155 exceptions, 0 shadows, 0 collisions;
  with the 40 forced briefs 4.288e9; 24 selected rules in 20 slots. `scratch/expr-*` hold this run (md5 of `expr-rules.tsv`: a2a334eab8524d88b0ed51426de6deb6).
- NEVER `git add -A`: untracked `AffixSelection.pickle`, `log_last_session`, the box-drawing-named file, the `scratch/que_run_*.log` logs and the
  experiment folders stay out of commits. Commit and push only when asked. No merge of main for now.

## 2. Decisions taken this session (user)

- Suffix quality is LEXICAL: only the post-verbal negation adverbs (`pas plus jamais rien guère point personne aucunement nullement`) and the
  auxiliary adverbs (`déjà bien trop encore toujours souvent mal`, suffix-only) may be suffix attaches (`SUFFIX_WORDS`, `src/expressionrules.py`).
  `que`, `de`, `le`... are prefix-only. Sources and what was used from each: `docs/PRIOR_ART.md`. Their evidence is the unigram count
  (`scratch/top_ngrams/1gram_top300.tsv`), but none of the adverbs wins a slot even at budget 30.
- Slot budget 15 -> 20 (`EXPR_RULE_BUDGET`). Sweep: 15: 22.8%, 20: 25.6%, 25: 26.2% (1 brief shadow `un petit`), 30: 27.2% (same shadow).
- Selector order: `freq + stackMass` (the variant that stacks most takes the bare slot) and, for gendered families, m/s, f/s, m_or_f/s, m/p, f/p, m_or_f/p
  (`GENDER_NUMBER`, keyed by the variant's last unit). No default family is gendered (`le la l' les` merge only with `FAMILY_MERGE=1`, measured worse).
- Order ban (`orderBan`, `Rules.orderBan`): the less frequent order of an adjacent attach pair seen in both orders is not attached (`que ce`, `s' il`).
  Removed the `ce que` ~ `que ce` collision (key union is commutative; no selector order can fix that kind).
- 3+-unit expressions are briefs, never attaches (`MAX_ATTACH_UNITS = 2`; `ce qu' il` is no longer an attach).
- Stage C selector collapse stays (it drops `je me`, `il n'`, `il y`). Measured marginals: `je me` -1.07e7, `il n'` -9.6e6, `il y` +3.4e6 strokes; `il` and `je`
  are worth 1.2e8 and 9e7. `il` + `n'` + host STACK (one stroke, same saving as a dedicated `il n'`), so no dedicated chord is needed for it.
  Only `n' y` is a multi-unit attach at budget 20 (`y` is not an attach rule itself).

## 3. Experiments (all OFF by default, env switches in `scratch/select_expression_rules.py`)

| Switch | Meaning | Result vs committed (25.7%, 155 exc., 0 coll.) |
|---|---|---|
| `KEEP_COLLAPSED=1` | keep the colliding variants | 25.6%, 157, 2 collisions |
| `SELECTOR_RETRY=1` | before collapsing, try the variant's other selectors (`ExprRule.selector`, `variantSelectors`) | 25.5%, 156, 0 (rescues `je me`, `il n'`; `il y` still dropped) |
| `ATTRIBUTE="je me,il n'"` | report the marginal pool saving of named rules | report only |
| `IL_N_Y=1` (`longRuns`) | allow `il n' y` as a 3-unit attach | identical (never selected: the il family hit its cap of 4 first) |
| `IL_Y_FAMILY=standalone` | `il y` + `il n' y` as their own family | 25.6%, 157 (the family wins no slot) |
| `FAMILY_MERGE=1`, `DEF_SUFFIX_FAMILY=1` | older merge experiment | worse (resume 2026-10-03, 0b) |

Not built: Option A (CP-SAT chooses the selector permutation with a cut loop for 3-way stacks). Not justified by savings; only by "no variant dropped by construction".
Every experiment overwrites the tracked `scratch/expr-*` files: `git checkout scratch/expr-*.tsv scratch/expr-rules-final.json` restores the committed run.

## 4. A correction to remember

I once said `il n' y` stayed "below FORM_COST". WRONG: `FORM_COST` is 100.0 (negligible). The real cause is the cap: Stage A absorbs a family's siblings in
DESCENDING FREQUENCY up to 4 (the selector count) with the optimistic PROXY marginal; the `il` family filled up with `il n'`, `il y`, `il ne` (marginal 0, dropped), `il s'`
and `il n' y` (frequency 6.4e6, marginal 9.6e6) was never evaluated. Stage C then collapses `il n'` and `il y`, so the cap was spent on variants that do not survive.

## 5. NEXT (user's order)

1. **Preselect more than 4 candidates per family** (TODO.md, "which variants fill a family's four selector slots"): keep a reserve list; when Stage C collapses a
   variant, evaluate the effect and promote the next reserve into the freed selector. Companion idea: pick the cap's four variants by marginal gain, not frequency
   (ideally the exact composed saving, not the proxy). Touch points: the family-bundling block of `selectExpressionRules`, `ExprRule.forms`, the Stage C loop in
   the driver (`selector collapse` step), `variantSelectors`/`ExprRule.selector`.
2. Stage C rework options (selector retry is built, CP-SAT permutation is not); decoder question for a keypress that doubles as the expression's standalone stroke
   (TODO.md, "attach keypress reused as a standalone stroke", e.g. `bien que` against `bien`).
3. Max-1-key overlap study (`EXPR_MAX_SHARED_KEYS`), needs the decoder decision (NOTES section 4). Review of the low-mass rules and a host + adverb pool for the adverbs.
4. Phase 4 (build + Plover export + docs: CLAUDE.md, docs/PIPELINE.md, GLOSSARY done for the vocabulary) before any merge to main; drop the temporary
   `from __future__ import annotations` in `src/affixes.py` when main is merged.

## 6. Stop and ask the user when

Any push, any merge into main, any change of the que family cut, changing the slot budget again (20 now), or touching main's affix code.
