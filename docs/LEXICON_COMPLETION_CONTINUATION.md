# Lexicon completion: continuation after the 2026-10-10 sessions

Resume point after a context clear. Read this first, then `docs/LEXICON_COMPLETION_HANDOFF.md` (the earlier handoff: the nine
questions, the tools table, the measured numbers; its answered questions are marked below) and `TODO.md` ("Glide encodings of the
`i`/`y` + vowel and `-ions`/`-iez` forms"). Plan of record: `/home/jfsp/.claude/plans/have-a-look-at-whimsical-gray.md`.

**Update 2026-10-10 (late night): the 528 only-committed rows worked down to zero decisions pending; the full rebuild passes again (supersedes the "Not done" of the update below).**
- Method: `git show f02125f~1:resources/LexiqueSynthetic.tsv` (the pre-regeneration file, 50,345 rows) against the regenerated one, keyed on (ortho, lemme, cgram, genre, nombre); causes read from `synthetic_skip_reasons.tsv` / `synthetic_bar_rejections.tsv`; every form checked against Wiktionary and GLÀFF (`util._verbreferences`, `util._pronunciation.compare`).
- Generator fixes (`src/verbparadigm.py`): (1) `isInfinitiveOutlier` reads `|` and `_` as the same character and `_spliceFiniteWord` keeps the infinitive's own boundary at the cut (`_endingWithOwnBoundary`): the hiatus `-ir` verbs (`ébahir`, `trahir`, `bleuir`, `obéir`, `éblouir`, `envahir`, `désobéir`) and `aérer`, `bridger`, `relouer`, `dégréer`, `tabouer` generate (+215 rows; the donor tables stay strict); (2) a slot that the glide-shaped `#ij` table lacks (`brillâtes`, `vacillâmes`) takes the plain template's ending (+90 rows).
- Mixte rules and corrections: rule `schwaOfE` (`src/mixterules.py`, group `9122e600e4`, accepted): a verb's `2` on the plain letter `e` is the stem schwa `°` (62 rows, 25 lemmas, `flageller` excepted, `eu` untouched; 41 exact / 8 up to `o`/`O` / 12 without reference against the references); 15 `manual-dropped-schwa` rows in `resources/mixteManualCorrections.tsv` (`rejeter`: 13 forms and the infinitive, `épousseter` infinitive: Lexique383 drops the stem schwa; `rejeter` had become a donor whose `rejeté` still dropped it, which lost 174 `-eter` rows until all 13 were fixed). `celer` stays `sele` in the infinitive and uses the `sel-` form in every conjugated form (user).
- Hand-derived rows: `resources/syntheticManualRows.tsv` grew from 21 to 218 rows (the `-oyer`/`-ayer` conditional 1p, the unit-shape outliers `manager` `immiscer` `acquiescer` `excéder` `celer`, `persiflé`, 18 present-tense `Ej` rows on the split shape `E_j` / `a_y`). Each was kept only if it agrees with a reference exactly or up to the mid vowel; `excéder` futures use `E` after the `ks` (references list `excèder-`).
- Ignored by design (`resources/excludedSlots.tsv`): `bitter` and `stripper` (every slot) and 50 NOM/ADJ slots of the old file (truncated or invented spellings, loanword plurals; reason `old_synthetic_row_not_promoted_2026-10-10`). The census reads that file; the generator does not.
- Result: Mixte md5 `76603f66fa744269b2665137faa9570e`, Synthetic 185,405 rows md5 `9360eeec3963c6a753dba7970c5c7051`; full `python dictionary.py` clean (`rc=0`, 1,793 s, 0 unresolved oppositions, 0 press-set conflicts, 0 final-stroke collisions, K=7 over 80,366 groups); pytest 1,533 pass + the 1 known failure (`plover_plugin_test`), mypy clean.
- New flag: `python dictionary.py --optimize-keyboard` adds S4 (`util.optimize_keyboard`, seeded from `starboard3h.json`, writes `starboard3h_optimized.json` only, never the committed layout) after the converged Synthetic file; off by default. The orchestrator still does not time S1, S4 or the expression-layer exports.
- Still open (details in `TODO.md`): `crayon` and the 229 non-verb `ay` rows, the 12 Mixte verb rows on the fused `Ej`/`ay` shape (the other 25 use `E_j`/`a_y`), the `ill`/`ll` lexicon, the E/e `phon`/`syll_cv` disagreements, the 3 folded en-/em- rows, the duplicate synthetic `ionienne`/`ioniennes`, `huguenotes` (`yg°nOt`, excluded from the census, not generated), the lemma errors (`liserer`, `écher`, `rapiécer`, `retraire`), the `reference-bar` sub-question, the handoff's undecided mixte groups and policy questions, a generator rule for the `-oyer` conditional 1p, the expression layer rebuild (`export_expression_data`, `export_plover_plugin`, `sync_plover_mirror`) and a second identical run for the md5 comparison.

**Update 2026-10-10 (night): the full rebuild passes, the repo's Synthetic file is replaced (supersedes the "Still to do" below).**
- Mixte gained case G of `splitGlides` (the fused `Ej` of the letters `ay` before `-ons`/`-ez`/`-ions`/`-iez`: `abstrayons` `E|j_§`, `abstrayions` `E_j|j_§` with `phon` `...Ejj§`; 20 verb rows; the first full run had 13 cross-lemma and 88 same-lemma collisions, many of them `-ayions`/`-ayons` twins with one `phon`) and a tag-correction step (`resources/mixteTagCorrections.tsv`, `applyTagCorrections` in `src/mixtecorrections.py`, called by `lexique.py` after the phonology corrections; its one row sets `ioniennes` f to number `p`). Mixte md5 `a5d34bef27481d560ca9a5f37f02e74d`.
- Elicitation: 15 oppositions were unanswered after the new rows (`-ions`/`-erions`/`-ons`, `sourire`-type subjunctive vs participle / passé simple, `dis`/`dits`, `ionienne`/`ioniennes`, `margotons`/`margottons`); the user approved guesses by analogy, written into `elicitation_answers.json` (225 answers, keyed by the pair of atom sets, not by words). The rule found while answering: within a mood the keys are unioned, so a pair answer only needs to separate its two sides (subjonctif 1s/3s `subjonctif`, 2s adds `pers_2`, 3p adds `nbr_p`; passé simple 3s unmarked, 1s `pers_1`, 2s `pers_2`).
- Result of `python dictionary.py` (clean, `rc=0`, 1,608 s, S2 to S10 including the trainer files): 0 unresolved oppositions, 0 press-set conflicts, 0 cross-lemma / 0 same-lemma residual / 0 reform-doublet final-stroke collisions, keypress groups K=7 (group 0 is now `conditionnel`, `infinitif`), `LexiqueSynthetic.tsv` 184,404 rows (md5 `513c02996230d70d27ae11b5773d0dc0`). pytest 1,526 pass + the 1 known failure (`plover_plugin_test`, stale expressions file: `export_expression_data` then `export_plover_plugin` are not in `dictionary.py`), mypy clean.
- Not done: the 528 only-committed rows, the 3 folded en-/em- rows and the E/e rows (the previous update's list), the `balayé`/`balaya` fused `Ej` before other vowels, the duplicate synthetic `ionienne` (lemma `ionien`) and `ioniennes` (lemma `ionienne`) beside the Mixte rows, a second identical run for the md5 comparison with the baseline (none was taken: the layer changed on purpose), the expression layer rebuild (`export_expression_data`, `export_plover_plugin`, `sync_plover_mirror`).

**Update 2026-10-10: verdicts recorded, Synthetic regenerated in a temp copy, S2 about 2.3x faster (supersedes the "still to do" of the evening update).**
- All `synth_rule` verdicts are recorded `accept` in `resources/lexiconDecisions.tsv` (user): `slot-map` (+25,815 rows, 753 verbs), `participle-from-infinitive` param `unvalidated` (strict +2,106 rows and 72 rows with no reference: ragée, hennie, claquetée, transparue), `lost-nasal` (+21), `homograph-tag` strict (+1,934, no new spelling), and the new row `1aa3c5d45d` `infinitive-participle-present` (+3,183: 2,174 present participles, 79 of them sharing a spelling with an ADJ/NOM/VER row, plus the full paradigms of 24 verbs known only by their present participle). Seven rules active with `reference-bar` and `glide-future-stem`.
- Regeneration (`python -m util.check_synthetic_regeneration`, temp copy; the repo's `LexiqueSynthetic.tsv` is still the old file): 184,404 rows, 4 rounds, two runs byte-identical (md5 `a6e16bec58b7499a2e3e03d5946b6f51`), 100,710 only-regenerated, **528** only-committed (741 before; 471 VER: `acquiescer`, `aérer`, `aboierions`...), `check_lexicon_features`: units 21 (committed file 33), duplicateIdentity 10,522 (same as committed), sounded 332 (committed 80, Mixte 132).
- A defect found and fixed: the Word constructor folds the n/m unit of en-/em- verbs (`fix_e_n_en`) but the lexicons store it; `writeSynthetic` now puts it back (`reinsertLostNasalUnit`; 57 raw rows, 3 folded rows remain: `enamouré`, `enamourés`, `enivrements`). The other 317 `sounded` rows are `E`/`e` disagreements between `phon` and `syll_cv` that Mixte already has in its en-/em- verbs (e.g. `embouteiller`) and that the generator copies into every conjugated form (the low-priority E/e item of the 2026-10-09 rulings).
- Speed (S2 loop about 14 min to about 6 min; details in `docs/PIPELINE.md`, Synthetic Lexicon Building (S2)): S2.1 skips the discriminator passes (118 s to 86 s per call), the ambiguity statistics are computed on demand, light theory rebuilds between rounds, `VerbReferences.pickle` cache, S2.2 parses once and skips unchanged rounds, prune/sort only after a writing appender, per-step timers, `S2_PROFILE_DIR`, `S2_SNAPSHOT_DIR`. Proven identical on `phonetic_theory.tsv`, `PhoneticTheory.pickle`, `disambiguated_theory.tsv`, `DisambiguatedTheory.pickle` (new vs old code, same lexicons). The Plover export and the elicitation chain were not re-run (the collision gate of `build_disambiguated_theory` fails on stale keypress groups in both trees).
- Why 4 rounds, and what was measured and dropped: see PIPELINE.md. Frozen donor tables (Mixte alone) converge in 3 rounds but lose 327 real forms (318 are in Wiktionary/GLÀFF): not adopted, the flag was removed. About 84% of the later-round rows are lemma-local, the rest depend on donors that other verbs' generated rows supply.
- Still to do: replace the repo's `LexiqueSynthetic.tsv` (run `python -m util.build_synthetic_lexicon` in place, then the full rebuild, phases 4-5 below, with elicitation for the new rows), look at the 528 only-committed rows, the 3 folded rows, the E/e rows. Possible further saving of about 60 s: build `Word`s directly instead of the theory in S2.1 (output must stay byte-identical: the theory lists words in stroke order).

**Update 2026-10-09 (evening): the synth_rule work.**
- Verdict #1 `reference-bar` (`21dde669cb`) is recorded `accept`, param `0.5` (user: the references are right wherever the bar refuses; the sub-question "Wiktionary first or the union of Wiktionary and GLÀFF" is still open, about 1,400 rows).
- New rule `glide-future-stem` (`f9f81b950d`, recorded `accept`): the future and conditional of `-ier`/`-uer`/`-ouer` verbs (not `-guer`/`-quer`, never after a vowel, so `-éier`/`-ouier` are untouched) vocalize the glide before the schwa of the ending (`afilj°Ra` -> `afiliRa`, `aks@t8°Ra` -> `aks@tyRa`, `alw°Ra` -> `aluRa`; `cluster+i+j°R` loses the glide and its `=` unit). Code: `hasGlideFutureStem`, `vocalizeGlideBeforeFutureR` and the `glideFutureStem` flag in `src/verbparadigm.py`, the `Mechanisms.glideFutureStem` field in `util/completeVerbParadigms.py`, the registry entry in `src/synthrules.py`, tests in `src/test/glidefuture_test.py`. Dry run: bar-accepted slots 84,713 -> 87,305, refused 4,603 -> 2,011. pytest 1,513 pass + the 1 known failure, mypy clean.
- Step 5.1 DONE (regeneration in a copy of the tree, `check_synthetic_regeneration`): no error, converged in 2 rounds, two runs byte-identical (md5 `69c02c7308a5664eee6e08289b0d0f7c`). Synthetic would go from 50,345 to 149,548 rows (75,805 only-regenerated, 741 only-committed, 7,891 column differences, not examined). `affiliera`, `accentuera`, `allouera` are generated; the 9 wrong `relouer` futures are gone; `créerions`, `clouas`, `déshabillâtes` are NOT rebuilt (probably wait for `slot-map`). The committed `LexiqueSynthetic.tsv` is NOT replaced.
- Still to do: verdicts #2-#5 (`slot-map`, `participle-from-infinitive` strict, `homograph-tag` strict, `lost-nasal`; all recommended accept) and the missing `infinitive-participle-present` row, then regenerate again and see how many of the 741 come back; 6 Mixte rows still have the glide before `R` (`graciera`, `réconcilier-` x3, `épierais`, `épierait`: correction rows to add); about 2,000 bar refusals remain (`razzier` `dz`, `substituer`, `bayer`, several-edit rows, not looked at).

**Update 2026-10-09 (late):** open decisions 1-3 are settled (section 4, "Answers") and the correction rows are implemented: 30 rows in `resources/mixteManualCorrections.tsv` (28 stray-`i` rows incl. `industrialisé`/`-ée`, + 2 `riant`), loaded with `mixteCorrections.tsv` by `loadAllMixteCorrections`; Mixte md5 now `d73812fb92ece0c19a5382f36799f813`; pytest 1,497 pass + the 1 known failure, mypy clean. Next: step 5.3.

**Git state (2026-10-09 night).** The work is committed on branch `lexique-completion` (pushed to `origin`) in 5 commits (decisions + audit tools,
verb-form references, Mixte S1, Synthetic S2, docs) on top of `main`, which has the two unrelated commits (star/hash ranking, lessons) and the
commit-id docs. The author of the 24 early commits was rewritten (every commit id changed): see `docs/HISTORY_AUTHOR_REWRITE_PLAN.md` (DONE),
`docs/history/COMMIT_MAP_2026-10-09.tsv` (old -> new ids) and `docs/history/OLD_BRANCH_COMMIT_REFERENCES.md` (ids cited by the other branches).
**Still uncommitted in the working tree (leave them for now):** `resources/LexiqueSynthetic.tsv` (modified, not regenerated; commit it only
after the regeneration with verdicts #2-#5), the generated outputs of an older rebuild (`plover_stenalgo_*dictionary.json`, `affix_abbreviations.tsv`,
`keypress_groups.json`, `realization_report.json`, `elicitation_answers.json` K=7, `steno-trainer/public/data/*.json`: to regenerate and commit
together after the full rebuild, phases 4-5 below), a few untracked doc files and ~35 scratch files (never commit). Identity: every commit as
`jf5pier <jf.stpierre@gmail.com>` (the global git config is another identity; pass `-c user.name=jf5pier -c user.email=jf.stpierre@gmail.com`).
The agent may not force-push or `reset --hard` (the action classifier refuses); the user runs those with `!`.

## 1. What this session did

The session went through question 1 of the handoff (the five `synth_rule` decisions) with examples, which led to a ruling on the
glide encodings of the `-ier`/`-yer`/`-iller` verbs, and then implemented it in S1 (the Mixte build).

State of the repo:

| Item | State |
|---|---|
| `resources/LexiqueMixte.tsv` | rebuilt by `python lexique.py`, md5 `d73812fb92ece0c19a5382f36799f813` (was `e176db7d…` before the 30 correction rows, `34560521…` before the glide rules) |
| `resources/LexiqueSynthetic.tsv` | **not regenerated in the repo** (the working-tree file is the old, hand-edited one and is not committed); the regeneration was run in a temp copy, see the evening update |
| pickles (`Dictionary`, `PhoneticTheory`) | **stale**: `rm -f *.pickle` before any rebuild |
| tests | `pytest src/test/`: 1,513 pass, 1 known failure (`plover_plugin_test::test_export_refuses_data_built_against_another_stock_dictionary`, stale expressions file); `mypy` clean |
| decisions | in `resources/lexiconDecisions.tsv`: 2 accepted `mixte_rule` rows (see 2), `reference-bar` and `glide-future-stem` accepted; the other 4 `synth_rule` rows (`slot-map`, `participle-from-infinitive`, `homograph-tag`, `lost-nasal`), the missing `infinitive-participle-present` row and all other rows are still `pending` / absent |

### New code

- `src/orthounits.py`: the marker units of `orthosyll_cv`: `#` (silent sound) and `=` (**repeated letter**, see 3), `spellingOf`,
  `stripMarks`.
- `src/mixterules.py`: two registered systematic rules (run by `lexique.py` `outputMixedLexique` through `activeRules`, only when their
  decision is `accept`):
  - `splitGlides`, group `e3e2ed7746`: cases A, B, C, E, F below (verb rows only; 481 rows changed);
  - `dropStrayGlide`, group `e1cded21a8`: `ij` on the letter `i` followed by a silent unit on a letter starting with `e` -> `i`
    (5 rows: `dévierait`, `sciera`, `recopierait`, `mésallieras`, `mésallies`; precision 1.00 against the references).
- `lexique.py`: `OrthoRewriteRule.followingChar` and the accent-blind guard in `orthoRewriteOccurrence` (a deletion rule fires only when
  the letter after the deleted one is the old spelling's). It fixes `asseyiez` (Lexique383) wrongly rewritten to `assyiez` by the
  `asseoir -> assoir` rule (18 rows: 11 `assey-`, 7 `rassey-`). The other 30 deletion contexts of `reform1990.tsv` (151 rows) are unaffected.
- Readers taught the `=` unit: `Word.graphemsToSyllables(withSilent=False)` (`src/word.py`), the five spelling checks of
  `src/verbparadigm.py` (now `spellingOf`), `graphemesOf` in `src/diffsignature.py`, `check_units` in `util/check_lexicon_features.py`.
- Tests: `src/test/mixterules_test.py` (new), `src/test/lexique_orthorewrite_test.py` (the guard, two new tests), one `word_test` case.
- `TODO.md`: the entry "Glide encodings of the `i`/`y` ..." records the rulings.

## 2. Rulings taken (all by the user, 2026-10-09)

Glide encodings, verbs only (non-verbs later):

| Case | Target | `phon` |
|---|---|---|
| A. `-Ciions`/`-Ciiez`, two letters `i`+`i` | `s_ij_#\|§` -> `s_i\|j_§` (`criions`) | unchanged |
| B. `-yions`/`-yiez` | `8_ij_#\|§` -> `8_ij\|j_§` (`essuyions`, `appuyiez`) | gains a `j` |
| C. `-illions`/`-illiez`, `-oyiez` | `i\|j_#_§` -> `i_j\|j_§` (`brillions`, `aillions`, `croyiez`) | gains a `j` |
| F. letters `lli` | `R_E\|j_§` -> `R_E_j\|j_§`, letters `lli\|=_ons` (`appareillions`, `surveillions`) | gains a `j` |
| E. one letter carrying vowel + glide | `k_R_ij\|a` -> `k_R_i\|j_a`, letters `c_r_i\|=_a` (`cria`, `plié`, `accablions`, `devrions`, `appuyais`) | unchanged |

- `-illons`/`-illez` and `-ons`/`-ez` with a single glide stay single (`brillons` `b_R_i\|j_§`).
- The conditionals/futures (`-rions`/`-riez`) are **included** in E (an earlier hold-back was a mistake; `phon` is untouched, so the
  `Rij§` / `Rj§` question stays open as a pronunciation question, not an encoding one).
- The `=` unit (letter side only): "the previous grapheme repeated in the onset of the next unit". Chosen because `&` is special in
  sed/awk replacement strings; `=` occurs nowhere in the lexicons.
- Stray `j` before a mute `e` is corrected at Mixte generation (rule `e1cded21a8`).
- `assyiez` and the `assy-` family were a bug: the spelling is `asseyiez` (fixed, see New code).
- Consonant + glide shares the syllable of the following vowel (`S_j_§`, `s_j_o|n_a`), as Mixte already does for the 59 existing rows.
- The `i` after `8` stays a separate unit (`nuit` = `n_8_i_#`).

## 3. The `=` unit and the unit-pairing convention

`syll_cv` and `orthosyll_cv` pair unit for unit. The only enforcement is `util/check_lexicon_features.py` (hand-run) and the readers
that splice or anchor by unit: `src/verbparadigm.py` (donor tables skip a misaligned row; `_padSilentUnits` raises), `src/diffsignature.py`
(`AlignmentError`), `src/affixes.py`/`src/affixproposals.py` (skip when syllable counts differ). The theory, strokes and disambiguation read
only `syll_cv`. A letter that carries two sounds across a syllable break needs the `=` unit on the letter side.

Not yet checked: that the Synthetic generator copes with Mixte donors that contain `=` (see 5, first item).

## 4. Decisions (1-3 settled and implemented, see "Answers" below; 4 open)

1. **The 26 stray-`i` rows** (Mixte has an extra `i`, the references do not): `contorsionner` x9, `espionner` x4, `excursionnant`,
   `remercier` x5, `marchiez`, `rallions`, `travaillerions`, `autopsiais`, `dématérialiser` x2, `industrialiser`. Agreed targets (j joins the
   following vowel's syllable; `ij` -> `j`, except `industrialiser` `ij` -> `i`):

   | Word(s) | Target `syll_cv` | Target `phon` |
   |---|---|---|
   | `contorsionna` | `k_§\|t_O_R\|s_j_o\|n_a` | `k§tORsjona` |
   | `contorsionnait` / `-ant` | `…s_j_o\|n_E` / `…s_j_o\|n_@` | `k§tORsjonE` / `k§tORsjon@` |
   | `contorsionne` / `-ent` | `…s_j_o_n_#` | `k§tORsjon` |
   | `contorsionné` / `-ée`, `-ées`, `-és` | `…s_j_o\|n_e` / `…s_j_o\|n_e_#` | `k§tORsjone` |
   | `espionnais`, `espionnait` / `espionnant` / `espionnent` | `E_s\|p_j_o\|n_E` / `…n_@` / `E_s\|p_j_o_n_#` | `EspjonE` / `Espjon@` / `Espjon` |
   | `excursionnant` | `E\|ks_k_y_R\|s_j_o\|n_@` | `EkskyRsjon@` |
   | `remerciai` / `remerciais`, `remerciait` | `R_°\|m_E_R\|s_j_e` / `…s_j_E` | `R°mERsje` / `R°mERsjE` |
   | `remerciant` / `remerciâmes` | `…s_j_@` / `…s_j_a_m_#` | `R°mERsj@` / `R°mERsjam` |
   | `marchiez` | `m_a_R\|S_j_e` | `maRSje` |
   | `rallions` | `R_a\|l_j_§` | `Ralj§` |
   | `travaillerions` | `t_R_a\|v_a\|j_°\|R_j_§` | `tRavaj°Rj§` |
   | `autopsiais` | `o\|t_O_p\|s_j_E` | `otOpsjE` |
   | `dématérialiser`, `dématérialisé` | `d_e\|m_a\|t_e\|R_j_a\|l_i\|z_e` | `demateRjalize` |
   | `industrialiser` | `5\|d_y_s\|t_R_i\|a\|l_i\|z_e` | `5dystRialize` |
   | `ressuyée` (not a stray `i`) | `R_E\|s_8_i\|j_e_#` | `REs8ije` |

   Their letters stay as Lexique383 has them (no `=`), except `ressuyée` (`r_e\|ss_u_y\|=_é_e`). Only one of these rows is in the mined
   decision store (`mésallies`, `6824b54615`, pending; now moot). **Mechanism not chosen**: correction rows in `mixteCorrections.tsv`
   (built by `util.build_mixte_corrections` from accepted decisions + the `lexicon_decision_examples.json` sidecar, which is gitignored and
   rewritten by the audit: awkward for hand-found rows), or lemma-keyed rules in `lexique.py` like the reform rewrites. `riant` (`Rj@` ->
   `Rij@`) is one more row of the same kind.
2. **Closed `o` policy.** Mixte follows Lexique383: `O` in a closed syllable (965 vs 102 before consonant + mute `e`, 2,410 vs 116 other
   closed), `o` in an open one (8,642 vs 1,055). 542 stem groups in 537 verb lemmas mix `o`/`O` between forms (`abandonne` / `abandonna`).
   The user believes `espionne` should be `E_s|p_j_o_n_#`. Choose: closed `o` for the 26 rows only, or an intra-lemma consistency policy
   (question 3 of the handoff).
3. **Schwa before a doubled consonant.** The user wants `E` (Quebec) or `e` (parts of France/Belgium), never `°`, for `(C)eCC-` (`ess-`,
   `ett-`, `eff-`...). Mixte: `E` 5,501 rows, `e` 766, `°` 228 (39 lemmas, mostly the `re-`/`de-` + `ss` prefixes: `dessous`, `dessus`,
   `ressac`, `ressaisir`, `ressembler`, `ressuyer`). Choose: `ressuyée` only, or the 228 rows.
4. **The handoff's other questions are still open**, in particular question 1: record the verdicts of the five `synth_rule` decisions
   (`reference-bar` `21dde669cb` +84,778 rows, `slot-map` `2c77b27d21` +26,444, `participle-from-infinitive` `08b1b8cedd` strict +2,113,
   `homograph-tag` `9b22fcd182` strict +2,909, `lost-nasal` `0cc34490fa` +41, plus `infinitive-participle-present` which has no row yet) and
   the sub-question "Wiktionary first, or the union of Wiktionary and GLÀFF" (`ReferenceBar.referencesOf`, `util/completeVerbParadigms.py`).
   The user has seen worked examples (the bar refuses `expiiez` `Ekspjje` because the `i` is missing: now fixed by case E at the source) but
   has **not recorded a verdict**.
   Questions 2, 4-9 of the handoff are untouched. Question 3 (policy: mid vowels and glides are conventions) is now partly answered by the
   glide rulings above and bears on decisions 2 and 3.

Variant policy, answered in discussion and worth recording in the spec: neither Wiktionary nor GLÀFF gives a regional label to the pipeline;
a reference is a set of variants and only vetoes (a candidate passes if exact or equivalent to any variant, `compare` in
`util/_pronunciation.py`); the stored pronunciation is a project convention.

### Answers of 2026-10-09 (user), to decisions 1-3

- Closed `o` (2): **dropped**, no `O` -> `o` anywhere. In the section 4 target table read every `o` as Lexique383's `O` (`contorsionne` `…s_j_O_n_#`, `espionne` `E_s|p_j_O_n_#`, phon `…sjOn…`): only the stray `i` is corrected.
- `8_i` (ressuyée): **kept**; `8` stays a nucleus phoneme.
- Schwa before a doubled consonant (3): the `ress-`/`dess-` reform is **dropped** (the prefix schwa `°` is right, `ressuyée` keeps `R_°|s_8_i|j_e_#`; remove it from the 26-row target table). Only root-internal cases (14 Mixte rows, ~130 Synthetic `-eler`/`-eter` rows) remain, as a low-priority TODO.
- Mechanism: with both policies dropped only the 26 rows + `riant` remain, so correction rows (`mixteCorrections.tsv`) are the natural choice; confirm when implementing.

## 5. Next steps, in order

1. DONE (see the evening update above; rerun after verdicts #2-#5). **Regenerate Synthetic in a temp tree** (the real test of the `=` rows): `rm -f *.pickle` in the tree, then
   `python -m util.check_synthetic_regeneration` (~12 min; it writes `synthetic_regen_report.tsv`, which is also a repo file: run it in a
   copy of the tree, as the earlier sessions did). Check: no `ValueError`/`AlignmentError`, the donor tables still serve the `-ier` verbs,
   and `expier`'s `expiions`/`expiiez` now come out right (`Ekspij§`, `Ekspije`) instead of being refused by the bar.
2. DONE: decisions 1-3 settled, the 30 correction rows implemented, Mixte rebuilt, `check_lexicon_features` re-run (Mixte `units` 35, `sounded` 132, unchanged: none of the corrected words was in them).
3. Record the `synth_rule` verdicts (`python -m util.review_lexicon_decisions --kind synth_rule`) and add the missing
   `infinitive-participle-present` row (see handoff "Next steps" 2).
4. Phases 4-5 of the plan (handoff "Next steps" 7): elicitation, keypress groups, a full clean `python dictionary.py`, the md5 comparison,
   a second identical run, then commit with approval. The Wiktionary TSV is CC BY-SA: commit its NOTICE with it.
5. Later, with the non-verbs: `crayon` `k_R_Ej|@` -> `k_R_E|j_@` (letters `c_r_a|y_on`), the 229 `ay` rows, the `ill`/`ll` words, NOM/ADJ gaps.
6. Docs still to refresh at the end: `docs/SYNTHETIC_LEXICON_STATUS.md`, `docs/PIPELINE.md` (S1: the two Mixte rules and the `=` unit; S2
   rules, decisions, new tools), `docs/GLOSSARY.md` (`=`, "repeat unit").

## 6. Facts and pitfalls worth keeping

- `import lexique` runs the whole Mixte build and rewrites `resources/LexiqueMixte.tsv` (the tests that import it do too); the output is
  deterministic (md5 above), so this is harmless but surprising.
- Rules run before correction rows in `outputMixedLexique`; a correction row replaces `phon`, `syll_cv` and `orthosyll_cv` wholesale, so it
  overrides whatever a rule did to the same row.
- `util.check_lexicon_features` has no spelling check; the `units` check now also rejects a misplaced `=`. Its Mixte `units` count fell from
  53 to 35 (the `assey-` family now pairs).
- The fused `ij` unit is in 487 Mixte verb rows (before the rule) and 294 Synthetic rows; the 66 conditional/future rows among them are split too (an earlier hold-back was reversed).
- Measurement material of this session (prototype script `glide_rule.py`, before/after Mixte copies, pytest logs) is in the session
  scratchpad `/tmp/claude-1000/-home-jfsp-Steno-stenalgo/7a7766d2-5de6-43c6-85d0-f42a08eedc8a/scratchpad/proto/`: temporary; the rule itself
  is in `src/mixterules.py`.
- Shell: never wait for a background job with `pgrep -f` (CLAUDE.md "Process rules").
