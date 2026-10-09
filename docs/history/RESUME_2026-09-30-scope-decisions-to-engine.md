> **DONE 2026-10-01.** Steps 1-5 below were carried out: combined check, engine support (option C), fusion decisions, the optional abbreviation dictionary. Current state: `RESUME_2026-10-01-option-c-engine.md` and `docs/AFFIX_RULES.md`; next phase: `PLAN_2026-10-01-affix-pipeline-integration.md`.

# RESUME 2026-09-30 (late) — all 30 affix-rule growth scopes decided; next: combined check, then the engine

Written for a fresh Sonnet session with no memory of the conversation. Everything below is on disk.
Supersedes the front matter (sections 1-9) of `RESUME_2026-09-30-ment-regex-scope.md`; that file's
per-rank log (sections "DECISIONS 2026-09-30 …", every bullet) is the DETAIL record and stays authoritative
for numbers and scripts.

## 1. Mission

The affix scan (`util/affix_scan.py --sweep`) proposes 30 rules (a key that replaces an affix syllable, optionally
fused with the neighbouring syllable = a "growth form"). Its growth scopes are enumerated syllable lists
(`·[be|ble|…]ment`): unlearnable. The user went through ALL 30 ranks and replaced each enumerated list by a short
scope: a pattern on the neighbour syllable's sound (X-SAMPA), a few literals, or no growth. "Done" for this phase =
the 30 decisions below are verified TOGETHER (one combined simulation), then wired into the engine
(`src/affixes.py`, `src/affixrules.py`), with a sweep + md5 comparison per `CLAUDE.md`. The engine does not accept
patterns yet ("option C", about a day of work, needs the user's go-ahead).

## 2. Where things are

- Repo `/home/jfsp/stenalgo`, branch `affix-abbreviation-rules` (base `main`; remote branch created by the push of
  2026-09-30). Interpreter `env/bin/python` (bare `python` is not on PATH). ~7 GB RAM: one heavy job at a time;
  long runs with `PYTHONUNBUFFERED=1`; wait on a PID (never `pgrep -f` in a loop).
- Other worktree `/home/jfsp/stenalgo-fix` (branch `lesson-generator`): not ours. A prunable detached worktree under /tmp is junk.
- Commits on this branch since the previous resume: `5699ab1` merge of main (R2 -> R° lexicon fix `2a6bad2`,
  `util/fixReSchwa.py`), `b340fe1` (affix pool + H sweep rerun, `--settings` option), `671902a` (re/ré notes), and the
  preclear commit (see `git log`). Main also has `2a6bad2` pushed.
- Code changed on this branch (tests: 723 pass): `src/affixes.py` (`NO_GROWTH_PREFIX_ORTHOS`, `isNoGrowthAnchor`: no growth
  for the `re`/`reh` prefix anchor, used in `growAffixesLattice`), `src/test/affixes_test.py` (+2 tests), `util/affix_scan.py`
  (`--settings H` runs only the named weight settings; comparison.md untouched then).
- Not tracked (files over 5 MB, regenerable): `scratch/affix-pool.pickle`, `affix-records.pickle`, `affix-families.pickle`,
  `*-before/` snapshots. Regenerate pool+records: `PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python -m util.affix_scan --refresh --part a --partial-overlap` (27 s).
  Never run `git clean -x`.
- Inputs used by all scope scripts: the pool pickle, the records pickle (via `util.affix_scan.loadRecords`),
  `scratch/affix-H-partial-by-anchor.json` (STALE, see pitfalls), the sweep table `scratch/rules-table-H-nogrowth.md`.

## 3. State

DONE and verified by running:
- Lexicon fix (164 `re`+consonant rows `R2` -> `R°`), rebuild 426 s, 717 tests on main; merged here.
- H sweep (flag on, no growth for `re-`), 1,405 s: 30 rules; md5s in `scratch/scope-baseline-md5-2026-09-30.txt`
  (`affix-rules.tsv` 584638c13e6638d2e573c24993ad17df). Table with full expansions: `scratch/rules-table-H-nogrowth.md`
  (generator `scratch/rules_table.py`).
- The 30 scope decisions: **`scratch/scope-decisions-2026-09-30.md`** (one table, read it first). Summary: no growth for
  ranks 2 (`re`), 4, 8, 9 and nothing to decide for 12, 14, 18, 20, 21, 22, 28, 30; patterns for 1, 3, 6, 10, 24, 25, 27, 29
  (and 17 partly, 23, 26); literals for 5, 7, 11, 13, 15, 16, 19.
- Scoring workflow (reusable for any re-check): `scratch/phon_scope.py RANK ROOT KEYS [GROWTH_SPELLING]` (table of anchor
  alone / list / patterns + best single neighbours), then a per-rank `scratch/*_lit.py` / `*_greedy.py` for sets.

NOT done:
- A COMBINED simulation of all decided scopes (every scorer evaluated one rule ALONE; the sweep scores a rule after the
  earlier ones, so cross-rule collisions are missing: e.g. `é` shows 70 exception words in the sweep table, 9 alone).
- Option C (engine support), the `re`+`ré` question is closed: they stay separate rules (user), `r-` skipped.
- Rank 1's regex was decided on SPELLING (`C{1,2}[eui]+`); all later ones on SOUND. Keep this in mind for the engine.

## 4. Decisions and constraints (the user's)

- Fallback price 5 per fallback word (words the scope names but that fall back to the anchor). Form cost about 100 per
  form (NOT the H sweep's 300). Meaning-carrying prefixes stay anchor-alone (`re-`, and the user chose anchor-alone for
  `de/des/dé/déh`, `é`, `-ter`). One key + a scope condition per rule; never split a rule into several keys.
- Preferences seen: short regex over enumerated lists; a few literal syllables when one word family carries the gain
  (excusez, regardez, aujourd'hui are near one-word cases, kept); exclusions only when worth it (kept `\{bv}` for `-té`).
- Rejected (reasons in the per-rank log): `re`+`ré` phonology-class merge; k=3 forms for `-tion`, `-té`, `-ser`; `ai` growth
  for rank 15; `de` neighbour `fl`/`ve` variants; bare-`y` and `p§` for rank 17; `ti` (tirer) for rank 26; `tRu` (trouvé) for 19.
- `ra`+`Re` lexicon oddity (rayâmes, `ra` pronounced `Re`): TODO.md entry; not fixed.

## 5. Next steps

1. Sanity: `cd /home/jfsp/stenalgo && env/bin/python -m pytest src/test/ -q` -> expect `723 passed`.
2. Write `scratch/combined_scopes.py` (does not exist): load pool/records/engine like `scratch/phon_scope.py` (its header
   up to `vowels = sorted` can be `exec`ed after setting `sys.argv`), then for ALL 30 rules at once take the sweep's rule keys
   from `scratch/affix-sweep-partial/H/affix-rules.tsv` (column `keys`, one row per rank, table ranks), build each rule's
   carriers with the decided scope (1/2/3 syllables per carrier; suffix = start-(k-1), prefix = span k), and call
   `src.affixes.simulate` with all bindings together (see how `src/affixrules.py` `selectRules`/`chooseRuleKeypress` pass
   several rules), retry failed multi-syllable carriers as k=1 like the scorers do. Report per rule: words, benefit, fallbacks,
   exceptions, ALONE vs COMBINED, flag any rule whose objective(5) drops by > 100. Acceptance: the script reproduces the single-rule
   numbers when run with one rule (e.g. rank 3 `en`: 227 two-stroke words, benefit 6,035 alone).
3. Show the user the combined result BEFORE touching `src/`; if some rules collide, propose which scope to relax (user decides).
4. After the user approves, option C (ask first): scope spec per rule (data file or Python table), matching in the candidate
   builder (`Candidate.slots`, `src/affixes.py`) and in `affixrules.py` (exception counting, report form column), tests, one
   `--settings H` sweep with `--partial-overlap`; compare with `scratch/scope-baseline-md5-2026-09-30.txt` and explain every difference.
5. Docs owed before merge (section 9), then ask the user about merging.

## 6. Verification bar

- `env/bin/python -m pytest src/test/` all green (723 on this branch; `CLAUDE.md` still says 717 for main).
- `mypy src/`: ~127 pre-existing errors; diff the count against a clean checkout (memory `mypy_preexisting_errors`).
- Any engine change: H sweep `PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python -m util.affix_scan --part b --reuse-pool --sweep --partial-overlap --settings H`
  (about 25 min; 1,300 s of it is the variant-rival step) and md5 comparison with the baseline file above.

## 7. Pitfalls

- `scratch/affix-H-partial-by-anchor.json` is from the OLD sweep: its ranks differ from the sweep table (JSON 6 = `in-`, 7 = `-tion`;
  table 6 = `-tion`, 7 = `in-`) and its keys are stale for table ranks 2, 7, 8, 12. `phon_scope.py` takes the keys on the command line;
  always pass the keys from `affix-rules.tsv` and use the JSON rank (the script asserts the root name).
- The scorers charge the form cost ONCE in total (`Scorer.objective`): subtract about 100 from any growth row when comparing with the anchor alone.
  `tion_scope.py`, `in_scope.py`, `te_k3.py`, `ser_scope*.py` charge per form (their rows are not comparable with phon_scope rows).
- Each scorer evaluates ONE rule against the lexicon alone (see the combined check above). Neighbours are keyed by sound in phon_scope
  (`C = "ptkbdgfsSvzZmnNlRjw"`, everything else is a vowel incl. nasals `@ 5 § 1` and schwa `°`); for growth only on one spelling pass it as the 4th argument.
- Simulation fallbacks: a multi-syllable carrier that gains nothing reverts to k=1; the sweep hides this, the scorers count it.
- Push can fail with `Permission denied (publickey)` when the ssh agent has no key; ask the user to run `! ssh-add` or `! git push`.
- Files over 5 MB are left untracked on purpose (git history size); commit with `git add -A` then `git reset` the big ones (see the preclear commit).
- The sweep takes ~25 minutes; do not poll with `pgrep -f`; wait on the PID.

## 8. Stop and ask the user when

- starting option C (engine change), changing any decided scope, the fallback price (5) or the form cost (100);
- a combined-simulation collision forces a scope change; a rule whose keys moved needs a decision;
- committing to main, merging this branch into main, or touching permanent docs; fixing the `ra`+`Re` lexicon oddity (user does lexicon fixes on main).

## 9. Doc updates owed before merge

`docs/PIPELINE.md` and `docs/GLOSSARY.md`: define "growth form", "scope", "fallback", "no-growth anchor"; the affix rules report format (scope column);
`docs/ARCHITECTURE.md` if the affix engine is described there; `CLAUDE.md` test count; remove the `R2` and keep the `ra`+`Re` entry in `TODO.md`.
