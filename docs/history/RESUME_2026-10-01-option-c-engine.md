# RESUME 2026-10-01 — option C DONE (scopes + fusions in the engine) and the 30 rules made usable as an OPTIONAL dictionary

Supersedes `RESUME_2026-09-30-scope-decisions-to-engine.md` ("Next steps"). Branch `affix-abbreviation-rules`. Canonical description now:
`docs/AFFIX_RULES.md` (code map, how a rule is built, decisions, commands, pitfalls) and the "Affix ..." glossary entries.

## State
- Engine: `src/affixscopes.py` (30 decided anchors + 4 approved fusions + `fusionVerdict`), `src/affixes.py` (`isScoped`, `growScopedForms`,
  scoped anchors skip the generic lattice), `src/affixrules.py` (all scoped forms taken, `resolveFallbacks`, `ruleExclusions`, fusion verdicts in
  `resolveVariantRivals`), `util/affix_scan.py` (setting `D` = alpha 2, fallback price 5, form cost 100; `fallbacks` TSV column).
- Tests: 733 pass (`src/test/affixscopes_test.py` new); mypy 127 errors = pre-existing count.
- D sweep 2026-10-01 (1,388 s): 30 rules, total score 111,966, every rule a decided anchor or approved fusion; `scratch/affix-sweep-partial/D/`.
- User decisions of 2026-10-01 on fusions (table in `docs/AFFIX_RULES.md`): fused as anchor only: `en`+`em/an/am/han`, `ner`+`nner/née/nnée`,
  `tion`+`ssion/sion`; `der|dé|dée` fused with `gaR|m@` extended from `dez` to `dez|der|dé`; no fusion for `é`, `au`+`o`, `ger`, `cher`, `ver`,
  `pa`, `ment`. Declined: `ssion`+`pRe` form, `Ri` extended to the `ver` spelling.
- Scratch tools (tracked): `scratch/combined_scopes.py` (combined simulation of the 30 scopes, `--only`, `--diag`), `scratch/fusion_check.py`,
  `scratch/fusion_growth.py`, `scratch/fusion_growth_all.sh`; outputs `scratch/combined-scopes-2026-10-01.md`, `scratch/fusion-check-2026-10-01.md`,
  `scratch/fusion-growth-all-2026-10-01.out`.

## Usable output (2026-10-01, after the engine commit 64d3558)
User design: the stable theory is never changed; affix abbreviations are an optional layer added after it, long forms stay as fallback,
one abbreviation per word (largest saving). Implemented: `src/affixabbrev.py`, `util/export_affix_dictionary.py` (last step of `dictionary.py`),
committed input `affix_rules.json` (written by the sweep as `affix-rules.json`), outputs `plover_stenalgo_affix_dictionary.json` +
`affix_abbreviations.tsv`. Result: 59,358 abbreviations / 65,646 carriers (51,119 save 1 stroke, 8,239 save 2), 0 outline overlap with the main
dictionary, deterministic (same md5 twice), main dictionary unchanged. 740 tests.

## NEXT PHASE (user, 2026-10-01)
Plan how to integrate the affix findings and the production pipeline into the main algorithm WITHOUT an agent in the loop: review every intermediate step done on the fly
(scope proposals, combined check, fusion checks, adoption of the rule list) and systematise it. Start with `PLAN_2026-10-01-affix-pipeline-integration.md` (inventory, proposed
disposition, six decisions to elicit from the user). Nothing there is decided yet.

## Open / next
1. Not merged into main; ask the user before merging. Docs are done (AFFIX_RULES, GLOSSARY, PIPELINE pointer, CLAUDE.md, TODO `R2` entry removed; the
   `ra`+`Re` entry stays).
2. Possible next steps: trainer lessons/hints from `affix_abbreviations.tsv` (rule examples, exponent badge idea); a Plover usage note (second dictionary, higher priority); review the 1,381 words that lost a shared outline.
3. Unscoped low-ranked anchors still use the generic lattice; check the report for roots outside the table when the lexicon changes.
4. Re-run order after a lexicon/layout/`affixscopes.py` change: Part A (`--refresh --part a --partial-overlap`), then Part B `--settings D` (see docs/AFFIX_RULES.md).
