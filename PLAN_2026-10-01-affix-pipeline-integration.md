# PLAN 2026-10-01 — integrating the affix abbreviation work into the main pipeline (to be planned with the user)

Status: INVENTORY AND PROPOSALS, nothing here is decided. Written for a fresh session. Branch `affix-abbreviation-rules` (pushed, not merged).
Read first: `docs/AFFIX_RULES.md` (what exists today), `RESUME_2026-10-01-option-c-engine.md` (state), this note (what is missing).

## 1. Goal

`python dictionary.py` must produce the optional affix abbreviation dictionary WITHOUT an agent in the loop. Today the engine and the
exporter are automatic, but the 30 rules, their scopes, their fusions and their keys came out of a long interactive session: scripts I ran on
the fly, tables I showed, choices the user made. Every one of those steps must be classified:
(a) systematised into the pipeline (a deterministic rule/threshold), (b) a committed human decision file (rare, like `starboard3h.json`),
(c) a diagnostic kept hand-run, or (d) thrown away. The user reviews this classification before any code is written.

## 2. Pipeline today (what is already automatic)

| Step | Command | Cost | Output | Automatic? |
|---|---|---|---|---|
| stable theory S1-S8 | `python dictionary.py` | ~200-430 s | pickles, theory files, exports | yes |
| records + pool (Part A) | `util.affix_scan --refresh --part a --partial-overlap` | ~30 s | `scratch/affix-pool.pickle`, `affix-records.pickle` | yes (but writes to scratch, caches records) |
| rule selection + keys (Part B) | `util.affix_scan --part b --reuse-pool --sweep --partial-overlap --settings D` | ~23 min | `scratch/affix-sweep-partial/D/affix-rules.{tsv,json,md}` | yes |
| adopt the rule list | `cp .../affix-rules.json affix_rules.json` | - | `affix_rules.json` | NO, by hand |
| abbreviations | `util.export_affix_dictionary` | ~25 s | `plover_stenalgo_affix_dictionary.json`, `affix_abbreviations.tsv` | yes (last step of `dictionary.py`, reads the committed rule list) |

## 3. Inventory of the ad-hoc steps and a proposed disposition

| # | What was done on the fly | Script / location | What the user decided | Proposed disposition |
|---|---|---|---|---|
| 1 | **Growth scope per anchor** (30 ranks): for each anchor I scored "anchor alone / enumerated list / regex on the neighbour's sound / best single neighbours / literals", showed a table with a recommendation, the user picked | `scratch/phon_scope.py`, `*_lit.py`, `*_greedy.py`, `affix_scope_table.py`, `rules_table.py`; decisions in `scratch/scope-decisions-2026-09-30.md` | regex over lists; literals only when one word family carries the gain; no growth for meaning-carrying prefixes (`re-`, `de/dé`, `é`) | (a)+(b): a **scope proposer** (`util/propose_affix_scopes.py`) generating candidates from a FIXED grammar (sound classes `C*V`, `C{1,2}V`, `[mn]V`, literals up to N, spelling regex), scoring them with the engine's own `growScopedForms`/`simulate`, keeping the best by objective with a complexity cap; the result is a committed data file (`affix_scopes.json`) with the evidence, replacing the hand-written `SCOPES` dict. Human edits stay possible. |
| 2 | **Prices**: fallback 5, form cost 100, alpha 2 | `SWEEP_SETTINGS` "D" in `util/affix_scan.py` | the user's numbers | (b): move to one committed policy file (`affix_policy.json`) read by the engine and the sweep; delete the L/M/H experiments or keep them as diagnostics |
| 3 | **No-growth decisions** (ranks 2, 4, 8, 9, 12, 14, 18, 20-22, 28, 30) | `SCOPES` entries `[]` | gain below the cost, or meaning-carrying prefix | (a)+(b): rule "keep a growth form only if objective gain net of form cost >= threshold"; an explicit no-growth list (with reason) in the policy file for the meaning-carrying prefixes |
| 4 | **Combined check of all scopes** (cross-rule collisions: `en`/`é`, `i`/`cer...`) | `scratch/combined_scopes.py` (`--only`, `--diag`) | none (it found the problem; the sweep re-picking keys fixed it) | (a): a validation gate after selection: run the combined simulation, report each rule whose objective drops > 100 versus alone, fail or warn above a threshold |
| 5 | **Fusion of spelling variants**: for each merge that contains a decided anchor, score "approved rule alone" vs "fused with approved growth, other spellings anchor-only", list the added words | `scratch/fusion_check.py` -> `scratch/fusion-check-2026-10-01.md` | per row: fuse as anchor only (`en`, `ner`, `tion`), fuse + extend a scope (`der`), no fusion (`é`, `au`+`o`, `ger`, `cher`, `ver`, `pa`, `ment`) | (a)/(b): **criterion not yet known** (see section 4); today `APPROVED_FUSIONS` + `fusionVerdict` in `src/affixscopes.py` hard-code the verdicts |
| 6 | **Growth check of the added spellings** (single neighbours; the approved pattern applied to each added spelling) | `scratch/fusion_growth.py`, `fusion_growth_all.sh` | none pays except `der`: extend `gaR|m@` to `dez|der|dé` | (a): same proposer as #1 applied to the added spellings, with the "extend an approved scope to a sibling spelling" candidate generated automatically |
| 7 | **Variant-rival resolution** (merged vs parts) | `resolveVariantRivals` + `fusionVerdict` override | the verdicts above | (a): once #5 is a rule, the override is the rule |
| 8 | **Adopting a sweep**: copy `affix-rules.json` to the repo root; check all 30 are decided anchors / approved fusions | by hand | - | (a): `util.affix_scan --adopt` (or a pipeline step) that verifies every selected rule is in the scope data and writes `affix_rules.json` only if so |
| 9 | **Check that no unapproved rule enters the top 30** (a decided rule drops out and an old-lattice rule takes its place) | read the report by eye | - | (a): assertion in the adopt step; decide the default for anchors outside the scope data (generic lattice vs no growth) |
| 10 | **Engine vs scratch scripts diverge** (stem-keeping rule: 227 vs 214 `en` words) | scratch scorers duplicated engine logic | - | (a): the proposer must call engine functions only; no duplicated scoring code |
| 11 | **Records cache** `scratch/affix-records.pickle` (never checked for staleness) | `util/affix_scan.loadRecords` | - | (a): derive records from the stable theory every run (7 s) or fingerprint-check like `DisambiguatedTheory.pickle` |
| 12 | **Pool non-determinism**: 12,138 / 12,141 / 12,149 nodes in three runs (unscoped lattice nodes; the 30 rules' carriers are identical) | observed 2026-10-01 | - | (a): find the ordering source (set iteration), make the pool deterministic, add a `PYTHONHASHSEED` test; an unattended pipeline needs byte-stable outputs |
| 13 | **`ra`+`Re` lexicon oddity, stray anchors** | `TODO.md` | lexicon fixes are done on main by the user | (c)/(d): keep in TODO |
| 14 | **Reading the abbreviation results** (counts, examples, the 1,381 outranked words) | ad-hoc python | - | (a)/(c): the exporter prints the counts; add a report file with the lost words and the strokes saved |

## 4. Decisions to elicit from the user (needed before coding)

1. **Fusion criterion.** The user's verdicts do not follow one numeric threshold: `é`+`e/hé/ai` gains +633 but was refused, `tion`+`ssion/sion` gains +344 and was accepted,
   `ner`+`nner/née/nnée` +1,578 / `en`+`em/an/am/han` +1,340 / `der`+`dé/dée` +494 accepted, `au`+`o`+`ho` +455 refused (two approved rules on one key), `ment`+... -940 refused.
   What is the rule? (candidates: gain threshold AND the added spellings are variants of the same morpheme / sound-alike inflections; never fuse two approved rules; never fuse a meaning-carrying prefix.)
2. **Where do the human decisions live and how are they reviewed?** Proposal: three committed files next to `starboard3h.json`: `affix_policy.json` (prices, no-growth list, fusion policy, caps), `affix_scopes.json` (the 34 anchor entries with provenance), `affix_rules.json` (selected rules and keys). The proposer and the adopt step write proposals; the user edits/approves; the pipeline only READS them.
3. **Frequency of the expensive step.** Selection (~23 min) is rare and costly like Keyboard Layout Optimization (S4): run on demand (`util.optimize_affix_rules`?), output committed; the cheap export (25 s) runs every time. A lexicon or layout change should make the pipeline WARN that `affix_rules.json` may be stale (fingerprint of the lexicon md5s and `starboard3h.json` stored in `affix_rules.json`) rather than rerun 23 min silently.
4. **Unscoped anchors** (outside the 34 entries): keep the generic enumerated-list lattice (rejected by the user as unlearnable but still in the code) or switch growth off for them? Proposal: off, and delete the lattice growth as dead code once nothing uses it.
5. **Pipeline placement.** After the Plover/trainer exports (today) vs a named stage in `docs/PIPELINE.md` ("Affix Abbreviation (S9)") with its own rebuild-table row, md5 baseline and "Recomputing after a fix" entry.
6. **Trainer.** Do the abbreviations ship in the steno-trainer (lessons by rule with the scope examples, exponent badge idea in memory `lessons_homophone_badge_idea`) as part of this integration or later?

## 5. Verification bar for the integration

- `pytest src/test/` green (740 now); every systematised step has unit tests on hand-built fixtures (as `affixabbrev_test.py`).
- The unattended run reproduces today's output: same 30 rules, same 59,358 abbreviations (md5 of `plover_stenalgo_affix_dictionary.json`
  `affix_abbreviations.tsv`), unless a decided change explains the difference.
- The main dictionary and every S1-S8 output keep their md5s (`CLAUDE.md` verification approach).
- A clean-checkout run of `python dictionary.py` followed by the affix steps needs no scratch file and no manual copy.
- A determinism check: two runs, different `PYTHONHASHSEED`, identical md5s.

## 6. Pointers

- Code: `src/affixscopes.py`, `src/affixes.py`, `src/affixrules.py`, `src/affixabbrev.py`, `util/affix_scan.py`, `util/export_affix_dictionary.py`; tests `src/test/affix*_test.py`.
- Decisions and numbers: `scratch/scope-decisions-2026-09-30.md`, `scratch/combined-scopes-2026-10-01.md`, `scratch/fusion-check-2026-10-01.md`, `scratch/fusion-growth-all-2026-10-01.out`, `RESUME_2026-09-30-ment-regex-scope.md` (per-rank log).
- User preferences: prices (fallback 5, form 100, alpha 2); regex on the neighbour's SOUND over lists; one key per rule, never split a rule; meaning-carrying prefixes stay anchor-alone; 20-30 rules total, simple human-checkable logic (memories `affix_scope_decisions`, `affix_rule_learnability`, `feedback_no_splitting_rules`, `feedback_prefix_meaning_no_growth`).
