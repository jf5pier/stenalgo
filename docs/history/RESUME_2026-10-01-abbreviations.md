# RESUME 2026-10-01 — abbreviations branch (whole-word/multi-word shortcut strokes)

## 1. Mission

Build the abbreviation-rule system for the French steno theory: whole-expression
briefs ("il est", "il y a" → one stroke) and attach keypresses (constant extra
keys merged into a host's first/last stroke: "de la + mot", "ne + verbe + pas"),
composable ("il y a" + ne…pas ⇒ "il n'y a pas" in 1 stroke when legal). Round 1
(documents) is DONE; round 2 (Q&A) is DONE; next is Phase 0 of the algorithm.
Done overall = selected, collision-free, human-reviewable rule set reported like
the affix rules (`scratch/expr-rules.tsv`), later wired into the theory build.

## 2. Where things are

- Worktree: `/home/jfsp/stenalgo-fix` (a git worktree; the main checkout
  `/home/jfsp/stenalgo` is busy on `affix-abbreviation-rules` — do not touch it).
- Branch: `abbreviations` (from `main` @2a6bad2). Base/main last merged state:
  main @a3c8d4e contains the lesson-generator merge (pushed to origin).
- Commits on branch (chronological): `b5aca46` (n-gram data + tao list +
  queryViewer corpus-30 fix), `923c657` (rebuilt TSVs, particle word-units),
  `3143632` (planning docs), `242b3d8` (round-2 answers registered),
  `39f92d7` (merge of `affix-abbreviation-rules` @813ed6e), `76321f2`
  (Phase 0: coverage + candidate pool), `198ab48` (Phase 1: composition
  algebra), `6006f4c` (Phase 2 Stage A: proxy selection), `d691b1a` (Q2
  rule families), `2ce23f7` (Stage B: keypress assignment), `766c0bf`
  (Stage C: joint repair + audit), `dc243c6` (attach-stacking disjointness
  fix), `cb6f6a7` (Q3 decision registered), `96f63a9` (Phase 3 report).
- Interpreter: `/home/jfsp/stenalgo/env/bin/python` (bare `python` not on PATH).
- **Committed 2026-10-02 and pushed**: `c52fd93` "Add forced briefs with
  multi-stroke eligibility, pool fragment fix, budget sweep" —
  `src/expressionrules.py`
  (FORCED_BRIEF_BUDGET=40 + `deriveBriefStroke`), `src/test/
  expressionrules_test.py` (5 new brief tests; suite 786 green), `scratch/
  build_expr_candidates.py` (bare-fragment fallback fix), `scratch/
  select_expression_rules.py` (forced-brief section, budget CLI arg,
  repairCandidates=200, forced-brief eligibility longformStrokes >= 2),
  regenerated outputs `scratch/expr-rules-proxy.tsv`,
  `expr-rules.tsv`, `expr-rules-final.json`, `expr-savings.tsv`,
  `expr-composability.tsv`, new `scratch/expr-briefs.tsv`, and this file.
- Untracked leftovers, NOT part of this work (do not commit with them):
  `RESUME_2026-09-30-lesson-generator.md`, `scratch/t5_verify.log`,
  `scratch/merge_lesson_generator_pytest.log`, `scratch/queryviewer_patch_pytest.log`,
  `scratch/top_ngrams.log`, `scratch/stageb_run.log`, `scratch/stagec_run.log`,
  `scratch/briefs_run.log` (the 2026-10-02 eligibility-fix driver rerun),
  `scratch/preclear_pytest.log`.
- No background jobs running.

## 3. State

- **Planning round 1 complete** (committed 3143632): complexity analysis
  (`PLAN_2026-10-01-abbreviations-complexity.md`), 5-phase algorithm
  (`PLAN_2026-10-01-abbreviations-algorithm.md`), 12 questions
  (`QUESTIONS_2026-10-01-abbreviations.md`). All cited code refs verified by
  exploration agents (e.g. RULE_BUDGET=30 at src/affixrules.py:25,
  `_newBase` src/affixes.py:1420, `_feasible` src/ambiguitychecker.py:1040,
  merge arithmetic ambiguitychecker.py:480).
- **Round 2 answers received 2026-10-01** (uncommitted; see §4) — planning is
  finished; implementation has NOT started.
- Data: `scratch/top_ngrams/` holds the rebuilt TSVs (1gram_top300,
  2gram_top{100,300}, 3gram_top{100,200}, 4gram_top100, 5gram_top50,
  apostrophe_words.tsv, fragment_completions.tsv) + orgtre sources. 101/567
  tao entries matched in the slices (depth-limited); 121 tao entries are
  multi-word.
- Verified this session: 964 tests pass on main post-merge; abbreviation
  branch is docs+scratch only so far (no src changes beyond the
  util/ngram_data.py corpus default in b5aca46).

## 4. Decisions and constraints (round-2 answers, 2026-10-01)

Full table: end of `QUESTIONS_2026-10-01-abbreviations.md`. Essentials:

- Composition first (attach beats brief when both cover the tokens).
- **Rule families (user's own design)**: base keypresses on the 22 phoneme
  keys; `*`(10)/`#`(15) may join ONLY as variant selectors so related particles
  share one rule (`du/de la/de l'/des` = one rule + marks); keys 0/1 excluded.
  Phase 1 algebra + Phase 2 selection must model families.
- Q3 (circumfix: one suffix keypress vs prefix+suffix pair) OPEN — settle in
  Phase 1 experiments.
- Separate budget ~10–20 expression rules (30 affix rules untouched); briefs
  priced FORM_COST tradition; explicit composability pair bonus (weight = Phase
  2 tunable); queue floors ≥2 strokes AND ≥5M occurrences; NO shadowing
  (canonical distinctness from all 190k live outlines); multi-stroke briefs OK
  with hasBoundaryRisk; mnemonic AND free-chord derivations (keySimilarity is a
  label, never a gate — measured: top-similarity keys can score worst);
  productive host scope (any host); 2010–2019 frequency window;
  standalone-stroke fallback on merge failure.
- User preferences: delegate mechanical work to cheaper subagents; commit only
  when asked; push only when asked; branch work per line; French corpora.

## 5. Next steps

1. ~~Commit the round-2 planning docs~~ DONE (242b3d8).
2. Phase 0 DONE (2026-10-01):
   a. ~~Merge `affix-abbreviation-rules`~~ DONE (39f92d7, merge-tree clean,
      no conflicts). `pytest src/test/` green — **740 tests, not ~964**:
      the lesson-generator merge (a3c8d4e) is on main but in NEITHER this
      branch nor the affix branch (fork point 2a6bad2 predates it); the ~224
      lesson tests arrive only when this branch eventually merges to main.
   b. ~~tao coverage gap~~ DONE: `scratch/rebuild_ngrams.py --query
      scratch/tao_abbreviations.txt --fill` → `scratch/tao_coverage.tsv`.
      561/564 unique terms covered (567 lines, 3 case-variant dups): 427
      orgtre + 134 viewer-filled (per-bin share→count scale anchored on
      locally-found terms); 3 still MISSING are proper nouns below the
      viewer's threshold (tourigny, sévigny, souligny — irrelevant at a ≥5M
      floor). Side fix: `util/ngram_data.py` queryViewer crashed on accented
      terms (unencoded URL); now percent-encodes and a new `viewerShares()`
      returns parsed shares (19 ngram_data tests pass).
   c. ~~expr_candidates.tsv~~ DONE: `scratch/build_expr_candidates.py` →
      1151 rows kept (422 single-word tao terms, 729 multi-token), 25
      dropped+logged to `scratch/expr_candidates_drops.txt` (proper nouns,
      scan junk, "de l"/"à l" apostrophe-loss artifacts, euphonic-t
      "a-t-il"). Token→theory resolution: whole token → hyphen split →
      elision split (fragment `l' d' n' s' m' t'` → bare `jusqu` → full form
      `ce/je/que` fallback, flag `fragMissing`) → œ→oe lexicon spellings.
      Longform = primary alternative of the disambiguated theory rendered via
      `renderFinalStrokesToRTFCRE`. Top-20 spot check: 18/20 freq/share
      ratios within 3.4–4.3e10; outliers explained (case-folded orgtre counts
      for c'est/mais; the viewer returns nothing for the trailing fragment
      "de l'").
3. Phase 1 (composition algebra) IMPLEMENTED (2026-10-01, uncommitted):
   `src/expressions.py` — spec in the module docstring (4-step rewrite
   semantics: attach-first matching, brief matching over the residual stream,
   merges by token-index adjacency, the `_newBase` failure ladder) plus
   `composeOutline(rules, tokens, ctx) -> Strokes | Failure` and
   `composeOutlineTraced` (segments/saving/exceptions/boundaryRisk for
   Phase 3). 23 tests in `src/test/expressions_test.py` covering the plan's
   verification list (il y a 1 stroke; il n'y a pas 1 stroke; de la
   first-stroke merge; both-sides attach; overlap/illegal/noNeighbour/spanOne/
   standaloneTrap ladder; confluence over rule permutations; family variant
   smoke; Failure cases). Full suite 763 green; mypy clean on the new module.
   **Design decision made (flagged to user)**: reserved mark keys (* / #)
   are TRANSPARENT to the overlap and legality checks — SimContext.isLegal
   rejects any stroke carrying key 10/15 (they sit outside the syllabic
   banks; live strokes like a=((12,10),) are "illegal" under it), so Q2's
   selector-bearing keypresses could never merge otherwise; collisions from
   a selector coinciding with a host mark are left to the Phase 2 audit.
   Q3 stays open: the algebra treats a circumfix as its decomposition
   (prefix+suffix attach rules, optionally one family); the one-keypress-vs-
   pair comparison needs Phase 2's keypress assignment to be data-driven.
4. Phase 2 Stage A (proxy selection) IMPLEMENTED (2026-10-01, uncommitted):
   `src/expressionrules.py` + `src/test/expressionrules_test.py` (14 tests;
   suite 777 green, mypy clean). Q6 floors (briefs: >=2 strokes AND >=5M;
   attaches: >=5M only — 1-stroke particles stay eligible, the plan's
   "ne + verbe + pas" route; flag to user). Candidates: briefs (whole
   multi-unit expressions) + attach runs keyed by (run, position) with
   standalone-frequency superseding nested evidence. Marginals via REAL
   Phase-1 segmentations (proxySaving over planStream with placeholder
   chords), once-credit per expression, span-intersection territory skip
   (composing pairs like ne+pas never skip), budget EXPR_RULE_BUDGET=15
   (user fixes the number), PAIR_BONUS_WEIGHT=0 (Q5, off until tuned).
   Driver `scratch/select_expression_rules.py` (particle set = function-word
   gramCats, printed for vetting) → `scratch/expr-rules-proxy.tsv`: 15
   single-word particle attaches win on marginal freq x strokes (de-PREFIX
   5.8e8, la-SUFFIX 4.6e8, ...); briefs lose to singles; composition
   interactions priced (de-prefix suppresses la-suffix mid-stream).
   **Superseded by item 5** (families now modeled; proxy made
   adjacency-honest).
5. **Q2 family bundling IMPLEMENTED (2026-10-01, uncommitted)** on top of
   Stage A: attach candidates carry a family (driver: the LEMMA of the
   run's first unit — de/d'/de la/de l' -> "de"); a family is ONE budget
   slot; on acceptance the head greedily absorbs siblings whose fresh
   marginal clears FORM_COST, capped at MAX_FAMILY_VARIANTS=4 (the
   none/*/#/*# selector budget); closed families never re-open;
   `pruneRedundantVariants` afterwards drops absorbed variants whose
   removal costs nothing (greedy absorption is myopic: "et à" was covered
   by et-P + à-P composing — but "que je" SURVIVES: it wins "que je me"
   1.3M contexts that the later "je me" selection strands). Also fixed:
   `proxySaving` now honours the ladder's structural noNeighbour (an
   attach with no host keeps its longform — mid-stream la-suffix after a
   consumed de saves nothing), which reordered the whole selection.
   Driver output `scratch/expr-rules-proxy.tsv`: 32 rules in 15 slots
   (de={de-P, d'-P}, ne={n'-P, ne-P, n'y-P}, que={que-P, que je-P,
   que l'-P, que nous-P}, il, dans, et, la, le, les, pas, je, ce, s',
   l' ...). Suite 779 green; mypy clean.
6. **Phase 2 Stage B (keypress assignment) IMPLEMENTED (2026-10-01,
   uncommitted)**: `assignKeypresses` in src/expressionrules.py (+2 tests;
   suite 781; mypy clean). Per family: every legal base chord (1751 via
   affixbinding.enumerateKeypresses), variants take base+selector in
   descending-frequency order (SELECTORS = none/*/#/*#), stage-1 on the
   top-30 sample with the 5% occurrence-weighted gate, stage-2 on all
   touched expressions for 5 finalists. Families evaluate ISOLATED
   (composing alongside earlier families would strand hostless particle
   n-grams like "et de" and order-distort; cross-family truth = Stage C).
   Segment now carries its token span; trailing/leading pool FRAGMENTS
   (a prefix run ending the expression — "n' y", "il n' y" — a suffix run
   starting it) are artifacts, excluded from both gate masses. Driver
   output: ALL 15 families have legal bases — de={de:(5,), d':(5,10)},
   ne={n':(2,), ne:(2,10), n'y:(2,15)}, que/les/pas share base (2,),
   il=(7,), l'/je=(4,), ce/de=(5,) … Duplicate bases across families are
   EXPECTED at Stage B exit (cross-family union trap) — Stage C's CP-SAT
   joint repair reassigns them; full collision audit vs the 190k live
   outlines follows there.
7. **Phase 2 Stage C (joint repair + audit) IMPLEMENTED (2026-10-01,
   uncommitted)**: `repairKeypresses` (CP-SAT in the featuregroupingsat
   tradition — one variable per family over its Stage B candidate bases,
   pairwise add_allowed_assignments forbidding intersecting effective
   keypress sets, objective = total score with rank tie-break, Stage B
   winners as hints) + `auditExpressionRules` (first JOINT composition of
   the whole pool: totals, Q7 shadows scoped to CHANGED compositions,
   cross-expression collisions). Stage B extended: per-family ranked
   shadow-clean candidate bases (REPAIR_CANDIDATES=20; Q7 hard no — this
   pushed Stage B to multi-key bases, 1-key bases shadowed live words).
   Driver feedback loop (3 rounds): cross-family collisions ban the
   involved bases and re-solve; SINGLE-family collisions are selector
   collapse on a marked host (the host's own */# swallows the variant's
   selector — "il a" vs "il n' a" under every base) → drop the weaker
   variant instead (its contexts compose through other families: il+n').
   Final: 15 families, 0 shadows, 0 collisions, 342 exception segments,
   saving 1.633e9 of 1.314e10 pool longform strokes (12.4%). Bases:
   de=(5,9,18) d'=+*; ne=(2,8,17) ne=+* n'y=+#; que=(2,9,17) with
   que je=+* que l'=+# que nous=+*#; dans et à il la le les pas l' je ce
   s'; il lost both absorbed variants (il n', il y) to selector collapse.
   Suite 781; mypy clean (ortools snake_case API).
8. ~~Uncommitted (ask user): Stage C changes~~ committed (766c0bf Stage C,
   dc243c6 disjointness, cb6f6a7 Q3, 96f63a9 Phase 3 report).
9. **Q3 circumfix experiments DONE (2026-10-01, commit dc243c6); user
   DECIDED Option C (decomposition + disjoint keys) — decision registered
   in the plan's Decisions block and the questions file's Q3 row.**
   Data on the ne…pas contexts (110M mass):
   - Option A (decomposition, no coordination): 31% full / 57% degraded /
     12% zero — degraded by κ STACKING: ne and pas keypresses shared
     phoneme keys, so on a 1-stroke host ("n' est pas") the second merge
     keyOverlaps into an exception.
   - Option C (decomposition + syllabic-key disjointness for the 31
     co-occurring family pairs, Stage B candidate width 20→200): 78% full
     / 8.5% degraded / 13.6% zero (the zeros are pure-particle fragments
     like the "ne pas" n-gram — pool artifacts, not writable hosts); pool
     total 12.4%→13.2% saved, exceptions 343→279. IMPLEMENTED and
     committed. Key subtlety: disjointness must ignore reserved keys —
     */# selectors are overlap-transparent in the composer, and naive
     key-level disjointness is infeasible (every multi-variant family
     carries 10/15).
   - Option B (a dedicated one-keypress circumfix rule) would target only
     the residual 8.5% (~9M mass) at the cost of a new learnable unit +
     budget slot + non-contiguous expressions in the algebra. Not
     implemented; looks outranked by C on the data.
   - Residual: 1 low-frequency collision ("ce n' est pas le" vs
     "ce qui n' est pas", ~1.5M each) — another marked-host selector
     collapse, mis-attributed by the drop heuristic (two differing
     families). Phase 3 polish.
10. **Phase 3 (report) DONE (2026-10-01, commit 96f63a9)**: the driver
    attributes the joint composition per rule (strokes saved = span
    merged / span-1 standalone, exception mass + top exception
    expressions, 3 worked examples with longform->composed RTFCRE,
    keySimilarity label — negative for the disjoint chords, the priced
    cost of the stacking fix) and emits `scratch/expr-rules.tsv` (29
    rules, affix-rules.tsv columns + composedWith),
    `expr-composability.tsv` (25 co-firing pairs >=1M with worked
    examples — "n' est pas: mR-/ie/pa -> RiejsR"), `expr-rules-final.json`
    + `expr-savings.tsv` (machine dumps). Suite 781 green.
11. **Budget sweep + pool fix + forced briefs (2026-10-02, uncommitted)**:
    - User raised the budget allowance to 30, priority to most frequent
      (the greedy's marginal frequency-weighted saving IS that priority).
      EXPR_RULE_BUDGET constant currently 30. **Sweep on the corrected
      pool (budget: saving, exceptions): 10: 13.3%/181, 15: 14.0%/272
      (PEAK), 20: 13.9%/351, 25: 13.6%/438, 30: 13.5%/452 — past 15 the
      disjointness crowding degrades the strong families. Recommendation
      delivered to the user: keep 15; NOT yet confirmed.**
    - **Pool coverage hole fixed** (scratch/build_expr_candidates.py):
      bare-fragment units c'/qu'/j'/m'/t' (unlike n'/l'/d'/s') are not
      theory orthos, so every expression containing them was silently
      dropped from the driver pool (101 rows: c'est 79M, qu'il 68M, j'ai,
      s'il...). resolveToken now falls back to the full form (ce/que/je).
      Pool 1050 → 1151; "c'est" now covered (2→1 strokes, c'-prefix into
      est).
    - **Forced briefs (user decision 2026-10-02)**: tao entries too
      infrequent to win a frequency slot, and later word additions, get
      invented brief strokes from their OWN budget
      (FORCED_BRIEF_BUDGET=40). `deriveBriefStroke` in
      src/expressionrules.py: derivation ladder union → skeleton → vowels
      → free chords (enumerateKeypresses), legality with reserved-key
      transparency, no shadowing (ctx.finalOutlines canonical index), no
      duplicate briefs (takenStrokes). Driver section creates briefs for
      uncovered tao entries sorted by -freq, audits jointly, writes
      scratch/expr-briefs.tsv and appends kind=brief rows to
      expr-rules.tsv. Run @15: 40 briefs, saving 2.009e9 → 2.348e9 (16.4%
      of pool), 0 shadows, 0 collisions. 5 new tests; suite 786 green;
      mypy clean.
    - **KNOWN FLAW, FIXED (2026-10-02, Next steps #12a)**: the forced-brief
      filter had taken top-frequency uncovered tao entries, mostly 1-STROKE
      words (26/40 rows saved 0 strokes). The `forced = ...` filter in
      scratch/select_expression_rules.py now requires
      `e.longformStrokes >= 2`. Rerun @15: 40 briefs, ALL with
      strokes_saved >= 1 (mostly 1; five entries save 2: toutes les,
      maintenant, aujourd'hui, société, avec les); derivations mnemonic-
      dominated (skeleton 21, union 6, vowels 1, free 12). Attaches alone:
      2.009e9/1.430e10 = 14.0%, exceptions 272; with briefs 2.709e9 =
      18.9% of pool, 0 shadows, 0 collisions. Briefs alone contribute
      7.0e8 (vs 3.4e8 pre-fix — double, same 40 slots). Log:
      scratch/briefs_run.log (not to commit).
12. NEXT:
    a. ~~Fix forced-brief eligibility~~ DONE (see item 11).
    b. Ask the user to confirm the selection budget (recommendation 15
       from the sweep) and the qu'-variant preference fix (qu' at 68M
       beats que nous 11M for family que's 4th selector slot; absorption
       currently ranks by accept-order not marginal).
    c. Residual collision polish ("ce n' est pas le" vs "ce qui n' est
       pas" — marked-host selector collapse, two differing families so the
       drop heuristic can't attribute it).
    d. Phase 4 (wiring into the theory build + Plover export) — the big
       remaining phase; docs owed before any merge (CLAUDE.md pipeline
       stage, docs/PIPELINE.md, docs/GLOSSARY.md vocabulary).

## 6. Verification bar

- Phase 1: full `pytest src/test/` green (763 = 740 + 23 new expression
  tests); `mypy src/expressions.py` adds zero errors (the ~127 pre-existing
  elsewhere are baseline); all of the plan's canonical examples tested.
- Phase 2 Stage A: suite 777 green (763 + 14); mypy clean on
  src/expressionrules.py; driver runs the real pool end-to-end (1151
  resolved expressions after the fragment fix, 383 candidates)
  deterministically.
- 2026-10-02 state: suite 786 green (740 base + 23 expressions + 14
  selection + 5 brief tests + 4 others); mypy clean on
  src/expressions.py, src/expressionrules.py; end-to-end driver @15:
  30 attach rules + 40 forced briefs, 0 shadows, 0 collisions, 16.4% of
  pool longform strokes saved (14.0% from attaches alone).
- Phase 0 merge: full `pytest src/test/` green; `git log --oneline` shows the
  merge commit; no scratch/ leftovers accidentally committed.
- Phase 0c: expr_candidates.tsv rows all resolve to Strokes; spot-check top-20
  frequencies against the Ngram Viewer (corpus id 30 — string ids are silently
  ignored and fall back to English; known endpoint quirk).

## 7. Pitfalls

- Disjointness between families must compare SYLLABIC keys only: every
  multi-variant family carries the */# selector keys 10/15, so naive
  key-level disjointness is infeasible for ANY pair of multi-variant
  families (found 2026-10-01; RESERVED_MARK_KEYS filtering in
  repairKeypresses).
- The repair's candidate width matters: with only 20 Stage B candidates
  per family all lists clustered on key 2 and even one disjoint pair was
  infeasible; repairCandidates=200 finds 13k+ disjoint combos.
- SimContext.isLegal rejects any stroke carrying keys 10/15 (outside the
  syllabic banks) — live strokes like a=((12,10),) are "illegal" under it;
  the expression code filters reserved keys before every legality call.
- A pool fragment ending in a prefix run (n-gram "n' y") noNeighbours —
  artifact, excluded from Stage B's gate masses via Segment.span.
- 1-stroke particles turn every merge failure into an exception (spanOne)
  — their exception rates drive base choice more than legality.
- Multi-word brief candidates must be checked for longform >= 2 strokes:
  the first forced-brief run burned 32/40 slots on 1-stroke words
  (0 saved).
- ExprRule is unhashable (mutable dataclass) — key stats dicts by
  (units, position) tuples.
- Driver recomputes everything (~3-4 min): theory load ~30 s, Stage B ~20 s,
  Stage C rounds ~30 s each; run with PYTHONUNBUFFERED=1 + log redirect.
- Ngram Viewer JSON endpoint ignores string corpus names (`fre`, `fre_2019` →
  silent English); numeric `30` = French. Batched comma-joined terms and
  percent-encoding are fine. Wildcard `X *` returns top-10 completions
  (EXPANSION rows).
- orgtre's FINAL lists silently drop fused apostrophe words (c'est, qu'il) —
  always rebuild from the `*_1a_no_pos.csv` intermediates
  (`scratch/rebuild_ngrams.py`).
- Word-unit rule: elision particles count as words (c'est = 2 units,
  il n'y a pas = 5); bare fragments (l') = 1 unit. Encoded in
  `scratch/rebuild_ngrams.py:wordUnits` — reuse, don't reinvent.
- After ANY lexicon or layout change: `rm -f Dictionary.pickle
  PhoneticTheory.pickle` (CLAUDE.md pitfall; DisambiguatedTheory.pickle is
  fingerprint-checked, no rm needed).
- Main checkout is on another branch in a different worktree — never check out
  `affix-abbreviation-rules` files by hand; use `git show` if reading is needed
  before the merge.
- long2+-minute pipeline steps: run with `PYTHONUNBUFFERED=1`, redirect to a
  log, `run_in_background` (memory habit).

## 8. Stop and ask the user when…

- The Phase 0 merge has real conflicts in src/affix*.py (resolution choices).
- Q3 (circumfix semantics) experiments produce a recommendation — user said
  "keep open", so present options with data before fixing it.
- Any push to origin, or any merge into main.
- The expression-rule budget number (~10–20 range) must be fixed.
- Shadowing pressure gets extreme (a huge-frequency expression with no free
  stroke) — user chose hard-no; revisiting that is their call.

## 9. Doc updates owed before merge

None yet — the branch is docs+scratch. Before any future merge to main of the
abbreviation ENGINE (Phase 4 era): CLAUDE.md (new pipeline stage + commands),
docs/PIPELINE.md (rebuild order), docs/GLOSSARY.md (brief / attach rule /
rule family vocabulary), and `python dictionary.py` orchestration docs.
