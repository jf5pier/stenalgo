# Commit notes: LexiqueSynthetic.tsv regeneration (2026-10-08)

Branch TODO: "make LexiqueSynthetic.tsv fully regenerable" (see `TODO.md`). Steps 0 and 3 are partly done and
steps 1 and 2 are analysed, with the fix-script migration left. **`resources/LexiqueSynthetic.tsv` itself is NOT
changed** (the regenerated file only lived in temp copies); adopting it is the one-time refresh of step 5, which needs your approval.

## What changed (all uncommitted)

| File | Change |
|---|---|
| `util/check_synthetic_regeneration.py` (new) | Hand-run diagnostic: copies the repo to a temp dir, empties the Synthetic file to its header, runs `build_synthetic_lexicon` twice, checks the two outputs are byte-identical, writes `synthetic_regen_report.tsv` (`only-committed / only-regenerated / column-diff`). `--runs N`, `--keep`. |
| `util/build_synthetic_lexicon.py` | `canonicalizeSynthetic` sorts the data lines after every appender (the output depended on set/dict order, i.e. on the string hash seed: two runs gave the same rows in different orders). Each appender is followed by `util.prune_spelling_variants --apply` (the generators ignore `spellingVariants.tsv`: `dissous`, a dropped form of `dissoudre`, was regenerated every round and the loop never converged). Converges in 2 rounds (was 5). |
| `util/completeVerbParadigms.py` | `confirmCandidates` keeps every generated candidate; the historical collision filter (introduced in `37fdc4e`, built to fix the `rechampir`/`regarnir` discriminator collision) is behind `--only-colliding`. New `allTemplatedVerbLemmas`: every VER lemma with a trusted Verbiste template is completed, not only those the feature-space detector flags (`--undersampled-only` keeps the old detection). A generated participle whose spelling is already attested for another slot is skipped. |
| `util/generateMissingNomAdjForms.py` | The generation loop is now `generateRows(...)`, callable and testable. `main()` learns the ending tables from `LexiqueMixte.tsv` alone and iterates `generateRows` to its own fixed point (a generated row can be the source slot of another missing slot). Falls back to `resources/morphalouNomAdjForms.tsv` when the Morphalou CSV is absent. |
| `src/nomAdjParadigm.py` | `writeMorphalouForms` / `loadMorphalouForms` (distillate I/O). `generateAuthoritativeForm`: when Morphalou confirms the spelling but the donor table is below the 100% bar, retry at `MORPHALOU_CONFIRMED_MIN_MATCH_RATE = 0.9` (new source label `morphalou_relaxed`); the result is accepted only if its spelling is one Morphalou lists. |
| `util/build_morphalou_forms.py` (new) | Distils `morphalou/Morphalou3.1_CSV.csv` into `resources/morphalouNomAdjForms.tsv`. |
| `resources/morphalouNomAdjForms.tsv` (new, 646 KB, 22,147 rows) | The NOM/ADJ spellings of the slots `LexiqueMixte.tsv` lacks (10,457 NOM, 11,690 ADJ). Built from Morphalou 3.1 (downloaded from ORTOLANG, `repository.ortolang.fr/api/content/morphalou/3/Morphalou3.1_formatCSV_toutEnUn.zip`, 38 MB zip). |
| `resources/morphalouNomAdjForms.NOTICE.md` (new) | Attribution: Morphalou 3.1, ATILF (CNRS and Université de Lorraine), CNRTL, licence **LGPL-LR** (confirmed by the archive's `licenceLGPLLR.txt` and its readme). The citation line is my wording; check it. |
| `TODO.md` | The NOM/ADJ cascade item is closed; the remaining differences are recorded. |

Not part of the commit: `synthetic_regen_report.tsv` (scratch report; add it to `.gitignore` or delete it), the downloaded `morphalou/` folder (already gitignored).
Not mine, already modified when the session started: `plover_stenalgo_dictionary.json`, the trainer JSONs, `lexique.py`, `LexiqueMixte.tsv`, the docs and test edits listed in the opening `git status`.

## Results of the from-scratch regeneration (committed: 50,345 rows)

Deterministic: two runs give the same md5 (`7812d625fc7e8177744858daee5c397f`), 61,981 rows (from scratch is now the default of `build_synthetic_lexicon`).

| | Original run (2026-10-08 morning) | Now |
|---|---|---|
| only in committed | 3,963 | 412 (355 VER, 29 NOM, 28 ADJ) |
| only in regenerated | 485 | 11,505 |
| same key, different content | ~290 | ~530 once compared as sets (the report's 1,524 counts row-order artifacts) |

What closed the gap:
1. The collision filter hid whole paradigms (`confédérer` had 3 forms in Mixte and the filter dropped its 28 generated ones). Its committed rows dated from before the adaptive discriminator selection (`ccd4d4b`).
2. Detection: the old detector flagged only lemmas whose discriminator features were a strict subset of their siblings'. You want full conjugations for every verb whether or not a discriminator needs them, hence `allTemplatedVerbLemmas`.
3. Morphalou: the committed NOM/ADJ rows had been validated against Morphalou, which is not in the repo. The distillate makes that a committed input; the 0.9 relaxation recovers the plurals the strict donor tables refused (681 of the 686 overlapping committed rows reproduce field for field).

## Findings that need your decision

- **~190 NOM/ADJ rows came from a cross-round cascade.** About 104 used a generated row as the source slot (kept), about 86 came from ending classes promoted by generated donors (removed: tables now come from Mixte alone). 138 of the 190 had a Morphalou-confirmed spelling.
- **Vowel quality (218 rows): DECIDED, adopt the regenerated value everywhere** (doubled `-eler` `°`->`E`, `-ayer` `e`->`E`, `-ier` subjunctives without the final glide, `baie` `e`; and, against `util/harmonyVowelTargets.tsv`, `autographie` `O`->`o`, `clone` `o`->`O`; `décaties` follows Mixte's `dekasi`). Do not hand-run `fixHarmonyVowels` / `fixMixedHarmonyVowels` on the Synthetic file afterwards. Details in `TODO.md`.
- **Generator bugs found by the comparison, fixed in `src/verbparadigm.py`:**
  - `spliceParticiplePhon` stripped every `#` of the donor's breakdown and `_padSilentUnits` re-added them at the end. That lost the leading `#_` of h-initial participles (`hanchées`: 66 rows) and moved internal silent units (`ahurie` `a|y|R_i_#_#` instead of Mixte's `a_#|y|R_i_#`; 83 rows now differ only by that). Only trailing `_#` is stripped now. Tests: `test_silent_initial_h_marker_survives_the_splice`.
  - `generateMissingParticiple` now refuses a participle whose breakdown does not spell its word (Lexique's `persifflé` donor gave `persif|flée`; also skips `croître` m.pl. `crus` and the dropped `dissous`). Test: `test_generate_missing_participle_rejects_a_misspelled_donor`.
- **Looked like bugs, are not:** the lost `n_` of `enorgueillies` / `enamouré` (`Word.fix_e_n_en` normalizes `@|n_` with `e|n_` to `@|` with `en|` at load; both forms load to the same Word) and the `R|j_§` of the `-aierions` conditionals (`Word.fix_ayer_conditionnel_onset_glide` splits `R_j_` after `_E_#` on purpose, as in the attested `paierions`; it only fires with the open `E`, which the committed closed-`e` rows lack). 27 keys differ in the TSV text but load to identical Words, so compare loaded Words, not TSV text.
- **Still wrong, not fixed** (≈10 orthosyll rows): committed `épagomène` / `turkmène` singular rows carry `è_n_es` and `paseos` has `é`; regenerated `benoîtes` has `oi`, `cashmeres` `è`, `manips` / `portraites` have an odd unit shape.
- **NOM/ADJ leftovers diagnosed** (details in `TODO.md`): `generateRows` no longer remembers the spelling it just generated (a homograph for another slot or category was blocked, 43 rows recovered, field-for-field identical to the committed ones, plus ~800 new homographic rows); the donor-agreement bar for slots without a Morphalou entry is now 0.95 (`DONOR_ONLY_MIN_MATCH_RATE`, label `donor_table_relaxed`; +872 rows, 30 identical to committed, 840 new, spot check clean except the odd lemma `essential` -> `essentiale`); the `-ène` adjectives and `bodys`/`caddys`/`catchs` remain without a candidate, 13 are tag gaps by design, 6 committed rows are corrupt truncated spellings.
- **Homograph tag rows** (`regrées` `sub:pre:2s` next to `ind:pre:2s`; ~176 keys): the strict finite ending tables (`MIN_FINITE_MATCH_RATE = 1.0`) skip them. Only the `infover` tag differs.
- **Leftover committed-only rows** (373 VER): `asseoir`, `rasseoir`, `enorgueillir` (hand-fix scripts) and tenses the finite tables skip for `-iller`, `-éer`, `-uer`, `-oyer` verbs.

## Verification state

- `mypy`: clean (186 files).
- `pytest src/test/`: 1,276 passed, 1 failed (the unrelated stale Plover expressions file). The failure (`plover_plugin_test.py::TestPackagedAssets::test_export_refuses_data_built_against_another_stock_dictionary`) is a stale `plover_stenalgo_expressions.stenalgo` against the already-modified `plover_stenalgo_dictionary.json`; run `python -m util.export_expression_data` to refresh it.
- Tests added for `canonicalizeSynthetic`, `resetToHeader`, the manual-rows appender, `allTemplatedVerbLemmas`, `confirmCandidates`, `generateRows`, the Morphalou distillate I/O and the relaxed path. Not covered by a unit test: the prune step wiring in `runAppendersOnce` (exercised by the diagnostic).
- Not done: step 5 (adopting the regenerated file, then a full `python dictionary.py` and md5 comparison of the pipeline outputs). The regenerated file has about 10,000 more rows than the committed one, so every downstream output will change.

## Remaining TODO, in order

1. Fix the ~10 orthosyll rows above (the vowel-quality sub-classes are decided); re-run `python -m util.check_synthetic_regeneration` (about 12 minutes).
2. Step 2: move the hand-run fixes into the pipeline as idempotent post-steps (`asseoir` manual rows into `resources/syntheticManualRows.tsv`, `fixRectifiedEConjugations`, the harmony and schwa fixes). Dry-runs of `fixParticipleSilentUnits`, `fixSplicedVerbBreakdowns`, `fixParticipleGenderPhon` on the regenerated file found nothing to correct, so the generators already include them.
3. Decide on the finite ending-table threshold and whether verb tables should learn from Mixte only (same question as the NOM/ADJ cascade).
4. ~~Step 3~~ done: `build_synthetic_lexicon` starts from the empty file by default (`--incremental` keeps the old behaviour). Step 2 partly done: the 21 `asseoir` hand rows are `resources/syntheticManualRows.tsv`, appended by S2.4 (`util/appendSyntheticManualRows.py`).
5. Step 4 done: ~20 new tests (`build_synthetic_lexicon_test`, `append_synthetic_manual_rows_test`, `complete_verb_paradigms_test`, `nomAdjParadigm_test`, `verbparadigm_test`), `CLAUDE.md`, `docs/PIPELINE.md`, README credit. Left: the test count in `CLAUDE.md` (1240) and the stale row counts in `docs/PIPELINE.md` S2.
6. Step 5: refresh of the committed Synthetic with your approval, full rebuild and md5 comparison.

## Suggested commit message

```
S2: regenerable Synthetic lexicon (deterministic order, full verb paradigms, Morphalou distillate)

- Sort the Synthetic file after every appender and prune dropped spelling variants each round,
  so two from-scratch runs are byte-identical and the loop converges in 2 rounds.
- Verb completion: keep every generated candidate (collision filter behind --only-colliding) and
  complete every templated verb lemma, not only the feature-space undersampled ones.
- NOM/ADJ: ending tables learned from Mixte alone, generation iterated to its fixed point,
  Morphalou-confirmed spellings accepted at a 0.9 donor agreement, 0.95 for slots Morphalou has no entry for.
- Add resources/morphalouNomAdjForms.tsv (distillate of Morphalou 3.1, LGPL-LR; see NOTICE.md) and
  util/build_morphalou_forms.py.
- Add util/check_synthetic_regeneration.py (regeneration diagnostic).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```
