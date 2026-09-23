# Lexicon recompute pipeline

Written 2026-09-20 to survive a `/clear`. Read this before making any change to
`resources/Lexique383.tsv`, `resources/LexiqueInfraCorrespondance.tsv`,
`resources/LexiqueMixte.tsv`, or `resources/LexiqueSynthetic.tsv` — the recompute
chain has several manual, order-dependent steps with no single source of truth for
"did I recompute everything," and two of them fail silently rather than erroring.

Motivating incident: fixing `évaser`'s word-final-z syllabification bug in
`LexiqueSynthetic.tsv` changed which words collide at theory-1 (`évases` now
correctly collides with `évase`/`évasent`). Rebuilding `Dictionary.pickle`/
`FirstTheory.pickle`/`theory2.tsv` alone was not enough — `resolved_press_sets.json`
stayed stale, so `évases` silently came out unmarked (indistinguishable from
"canonical") instead of getting the `pers_2` feature the elicited rules said it should.
Caught only because the outcome looked wrong against the stated pers_3-default design
rule; nothing errored.

## The full chain

| Step | Command | Reads | Writes | Auto-run by `dictionary.py`? |
|---|---|---|---|---|
| Lexicon merge | `python lexique.py` | `Lexique383.tsv`, `LexiqueInfraCorrespondance.tsv` | `LexiqueMixte.tsv` | No |
| Paradigm completion | `util/completeVerbParadigms.py` (+ friends) | `Lexique383.tsv`, Verbiste templates | `LexiqueSynthetic.tsv` | No |
| Theory 1 | `python dictionary.py` | `LexiqueMixte.tsv`, `LexiqueSynthetic.tsv` | `Dictionary.pickle`, `FirstTheory.pickle` | — (this *is* the step) |
| Discriminating-Feature Elicitation (Elicitation Phase), re-derivation | `python -m src.elicitation` | `elicitation_answers.json` + theory-1 | `resolved_press_sets.json`, `questionnaire.json` | **No** |
| Discriminating-Feature Grouping (Grouping Phase) | `python -m util.build_keypress_groups` | `resolved_press_sets.json` | `keypress_groups.json` | No |
| Discriminating-Feature Stroke Realization (Realization Phase), report build | `python -m util.build_realization_report` | theory-1 + Grouping Phase + Elicitation Phase outputs | `realization_report.json` (tracked realization report) | No |
| Theory 2 (Realization Phase + star/hash marks, wired 2026-09-20) | `python dictionary.py` (`__main__`) | theory-1 + Grouping Phase + Elicitation Phase outputs | `theory2.tsv` | — (this *is* the step; runs the Realization Phase inline (the inline path) via `Dictionary.buildFinalTheory`) |

## Two silent-failure traps

1. **The pickle cache.** `dictionary.py`'s `__main__` only rebuilds
   `Dictionary.pickle`/`FirstTheory.pickle` if they don't already exist — otherwise it
   silently loads the stale cache and does nothing with your lexicon edit, no error or
   warning. **Always `rm -f Dictionary.pickle FirstTheory.pickle` before rerunning**
   after any lexicon change.
2. **`realization_report.json` is a separately-tracked artifact**, distinct
   from `theory2.tsv`. Since the 2026-09-20 wiring, `dictionary.py` computes the
   Realization Phase internally (the inline path) to build `theory2.tsv`, but it does not write
   `realization_report.json` — that file is only refreshed by explicitly
   running `python -m util.build_realization_report`. If you only run `dictionary.py`,
   `theory2.tsv` is correct but the realization report goes stale (and with it the
   trainer keyboard legend, which `util/export_keyboard_layout.py` reads from it).

## What's usually safe to skip

The Grouping Phase groups the fixed vocabulary of ~194 atomic features (`pers_2`, `subjonctif`,
...), not specific words — a lexicon fix essentially never requires rerunning it, since
it doesn't add or remove atomic features. Confirmed directly for the `évaser` case
(both needed features already existed in `keypress_groups.json`) rather than
assumed. Skip it unless a fix somehow introduces a genuinely new feature requirement to
a previously-unseen opposition — vanishingly unlikely for an ordinary phonology/
syllabification correction.

## Checklist for any fix that changes theory-1 collisions

1. Apply the fix (typically a scoped `util/fix*.py` dry-run + `--apply` script, patching
   the exact source file(s) plus `LexiqueMixte.tsv` directly rather than re-running
   `lexique.py` wholesale, to avoid unrelated full-file regen diffs).
2. `rm -f Dictionary.pickle FirstTheory.pickle`
3. `python dictionary.py` (rebuilds theory 1; writes `theory2.tsv` using whatever Elicitation,
   Grouping and Realization Phase outputs currently exist — may be stale at this point, that's expected)
4. `python -m src.elicitation` (re-derives `resolved_press_sets.json` against the fixed
   theory 1)
5. `python -m util.build_realization_report` (refreshes the tracked
   `realization_report.json` realization report)
6. `python dictionary.py` again (rebuilds `theory2.tsv` against the now-fresh Elicitation
   Phase data — pickles already exist from step 3, so this run is fast)
7. Verify: `pytest src/test/`, plus a targeted collision check for the specific
   word(s)/lemma(s) the fix touched (see recent session transcripts for the pattern —
   group `theory2`/`buildFinalTheory` output by final stroke, flag any group with >= 2
   distinct `ortho` and >= 2 distinct `lemmeGramCat`, excluding `reform1990.tsv`
   spelling-doublet pairs).

## Open follow-up

`ROADMAP.md`'s "What's left to do" tracks consolidating this whole chain into one
script/entrypoint so this class of mistake stops being possible — see that file.
