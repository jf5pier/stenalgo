# Resume: self-homograph alternate strokes + elicitation spec (2026-09-22)

Continuation doc for a long session that started from `RESUME_2026-09-21-steno-trainer.md`
item 2 (the "calmez" → `-kt` over-marking bug) and grew into a full pipeline fix. That older
doc's items 1 and 2 are now **resolved** — this doc supersedes it for those; its items 3/4
(steno-trainer sentence mode, IPA toggle) are still open.

## What changed, in commit order (all on `main`)

1. `688c74d` — **Root fix**: same-spelling homograph readings (e.g. "calmez" = impératif or
   indicatif présent) no longer get their discriminator marks unioned together.
   `src/elicitation.py::resolveGroupPressSets`/`resolvePressByCombination` now keep each
   reading's press as a separate alternate; `src/phaseg.py`/`src/phasegsat.py`'s
   distinctness constraints exempt a spelling's own alternates from needing to differ from
   each other. Also fixed 3 real `elicitation_answers.json` mistakes this surfaced (see
   below) and added `conjugation_disambiguation_order.txt` (user-authored spec) +
   `util/check_conjugation_disambiguation_order.py` (report-only validator) — **0
   violations** currently.
2. `1d68593` — Added `preferredKeysByGroup` to `realizeKeypressGroupsAsExtraStroke`: a human
   mnemonic preference for PHYSICAL key choice (e.g. `pers_3` on `-t`), tried first, wins
   outright over cost if feasible.
3. `98e7526` — Wired the alternate-strokes fix into the REAL export path.
   `Dictionary.buildFinalTheory` now returns `dict[Word, list[Strokes]]` (index 0 primary,
   further entries a self-homograph's other readings) and shares `PREFERRED_KEYS_BY_MARKER`
   with the diagnostic script via `ambiguitychecker.resolvePreferredKeysByGroup`. Before this
   commit, the fix only showed up in `phase_p_keypress_realization.json`'s bookkeeping, not
   in the actual `plover_stenalgo_dictionary.json`/steno-trainer exports — that gap is closed.
4. `b1e02ed` — Made Phase G's CP-SAT search deterministic: `_newDeterministicSolver`
   (`num_search_workers=1`, fixed `random_seed`) + `_breakTiesAlphabetically` (a final,
   lowest-priority tie-break tier). Two consecutive real builds of
   `phase_g_keypress_assignment.json` are now byte-identical.

## Current keyboard state (K=7)

| Markers | Physical key |
|---|---|
| conditionnel, infinitif | (auto-assigned) |
| f | (auto-assigned) |
| future, passé, pers_3 | `-t` (preferred) |
| imparfait, subjonctif | (auto-assigned) |
| impératif, pers_1 | `-k` (preferred) |
| nbr_p, p | (auto-assigned) |
| pers_2 | `-d` (preferred) |

`calmez` now has two real, independently-correct dictionary entries: `kal/me/-k` (impératif)
and `kal/me/-d` (pers_2/indicatif) — either one alone is sufficient, matching the design goal.

## The 3 elicitation_answers.json fixes (all applied and reverified)

1. `q4` (`avoir`): dropped a redundant `pers_3` from a `subjonctif présent pers_3 nbr_p`
   reading's press — this single fix (the abstract shape recurs across ~all `-er` verbs)
   resolved 549 lexicon-wide violations of "subjonctif may be clarified by at most one
   pers_/nbr_ atom."
2. `q113` (`renvoyer`): `renvoyé` (masculine singular participle) was checked `m` when
   masculine should always be the free/∅ default — a one-off human mistake, not systemic.
3. 5 duplicate `id` values (`q98`/`q113`/`q141`/`q163`/`q184`, all colliding with a
   later-appended `renvoyer` batch) renumbered to `q200`–`q204` — cosmetic, no functional
   effect (lookups match by content, not id).

## Follow-up session (same day): reading labels + a Phase P matching bug — DONE, pushed

`RESUME_2026-09-21-steno-trainer.md` item 1 (the drill can't say which reading a chord is
for) is now **resolved**. Two commits, both pushed to `origin/main`:

5. `cc86d98` — **Phase P bug fix**: `src/ambiguitychecker.py::_resolveEntryWord` compared
   theory 1's RAW strokes against `resolved_press_sets.json`'s CANONICAL entry strokes, so
   any word whose raw stroke repeats a key (e.g. "nie" /nj/, `((6,8,8,9),)` vs `[[6,8,9]]`)
   never matched and fell back to `candidates[0]` — a different same-spelling Word ("nie"
   /ni/), which then carried the subjonctif mark while the real subjonctif Word went
   unmarked. Now canonicalizes before comparing (+ regression test). ~90 Plover dictionary
   entries moved their mark to the right Word (e.g. `renie` /ni/ `R@a/mRi/-l` → `R@a/mRi`,
   `renie` /nj/ gains `R@a/mRw-/-l`). Still 0 residual same-`lemmeGramCat` collisions; marker
   keys unchanged. Found because the labels work below reported 26 "misaligned" words.
6. `b9537de` — **Reading labels in steno-trainer**:
   - `src/elicitation.py::serializeResolvedPressSets` now writes a `readings` field per
     entry: per spelling, a list PARALLEL to its `pressSets` alternates, each the feature
     combinations that resolved to that press. Unused by Phase G/P (verified: the file is
     otherwise byte-identical in content).
   - `util/export_practice_words.py` emits one drill item per (word, stroke) with a French
     `label` (e.g. "impératif présent, 2e pl.", "subjonctif présent, 1re sg. / 3e sg.",
     "nom, m. sg. · adjectif"), keyed by (ortho, steno) instead of ortho alone — so
     self-homograph alternates and same-spelling/different-chord words ("est" verb vs noun)
     are all drilled. 10000 items / 8360 distinct spellings; 0 misaligned after the fix.
   - `util/_theoryio.py::loadFirstAndFinalTheory` returns both theories from one unpickle.
   - `Drill.elm` decodes `label`; `Main.elm`'s `viewDrill` shows it in italics under the
     word (`.target-label` in `style.css`). Compiles; **not yet eyeballed in a browser**.

7. `3b22e0f` — **`être` conflict fixed** (pushed): `elicitation_answers.json`
   `q32` (`sois` sub-pres-1s vs `soit` sub-pres-3s) — `sois` side's `checkedA` was
   `["subjonctif"]`, identical to `soit`'s, so E5 held back the whole `être_VER` group (no
   Phase P marks on any être form). User's call: `sois` needs `subjonctif` + `pers_1`. Dry
   run first (conflict 1 → 0, violations 0 → 0, only `être_VER` changed), then applied and
   full chain rerun: 0 groups held back, 0 violations, 0 residual same-`lemmeGramCat`
   collisions; Phase G grouping + Phase P keys unchanged (only Phase G usage-frequency
   numbers moved). Result: `swa` soit (ind), `swa/-l` soit (sub 3s), `swa/-k` sois (imp),
   `swa/-kl` sois (sub 1s), `swa/-dl` sois (sub 2s), `swa/-sl` soient; side effect `soi`
   `swa/*#` → `swa/*`, `soie` `swa/*#/*#` → `swa/#`. `q32`'s `"clean": false` flag was left
   as-is (meaning not investigated).

The drill is live at **https://jf5pier.github.io/stenalgo/** — GitHub Pages, redeployed by
`.github/workflows/deploy-steno-trainer.yml` on every push to `main` touching
`steno-trainer/**` (it compiles Elm itself; `main.js` is not tracked).

## Update (later 2026-09-22): items 1 and 3 below are DONE, item 2 still open

Superseded by `RESUME_2026-09-22-trainer-features.md` — labels live, sentence mode and the IPA
toggle shipped, plus further features and fixes. Item 2 (optional `q31`/`q49` review) is carried
over there. Kept for history.

## What's NOT done — next steps

1. Browser-check the new label line in the drill view (live site above).
2. Optional: review `elicitation_answers.json` `q31`/`q49` (`sois` impératif rows), also
   `"clean": false` — they resolve without conflict, so not blocking.
3. `RESUME_2026-09-21-steno-trainer.md` items 3 (short-sentence mode) and 4 (X-SAMPA/IPA
   toggle) — still not started; the new `label` field slots straight into sentence mode.

## Recompute chain, if you touch elicitation/lexicon data again

See the `[[lexicon_fix_recompute_order]]` memory (auto-memory system) for the full 5-step
chain — it's now longer than "dictionary.py → elicitation → dictionary.py": add
`util.build_phase_g_assignment` → `util.build_phase_p_realization` → the 3 export scripts.
Verify with `python -m util.check_conjugation_disambiguation_order` (expect 0 violations) and
by grepping the actual word in `plover_stenalgo_dictionary.json`, not just the intermediate
`phase_p_keypress_realization.json`.
