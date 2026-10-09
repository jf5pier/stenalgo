# Lexicon completion: continuation after the 2026-10-09 glide session

Resume point after a context clear. Read this first, then `docs/LEXICON_COMPLETION_HANDOFF.md` (the earlier handoff: the nine
questions, the tools table, the measured numbers; its answered questions are marked below) and `TODO.md` ("Glide encodings of the
`i`/`y` + vowel and `-ions`/`-iez` forms"). Plan of record: `/home/jfsp/.claude/plans/have-a-look-at-whimsical-gray.md`.

**Update 2026-10-09 (evening): the synth_rule work.**
- Verdict #1 `reference-bar` (`21dde669cb`) is recorded `accept`, param `0.5` (user: the references are right wherever the bar refuses; the sub-question "Wiktionary first or the union of Wiktionary and GLÀFF" is still open, about 1,400 rows).
- New rule `glide-future-stem` (`f9f81b950d`, recorded `accept`): the future and conditional of `-ier`/`-uer`/`-ouer` verbs (not `-guer`/`-quer`, never after a vowel, so `-éier`/`-ouier` are untouched) vocalize the glide before the schwa of the ending (`afilj°Ra` -> `afiliRa`, `aks@t8°Ra` -> `aks@tyRa`, `alw°Ra` -> `aluRa`; `cluster+i+j°R` loses the glide and its `=` unit). Code: `hasGlideFutureStem`, `vocalizeGlideBeforeFutureR` and the `glideFutureStem` flag in `src/verbparadigm.py`, the `Mechanisms.glideFutureStem` field in `util/completeVerbParadigms.py`, the registry entry in `src/synthrules.py`, tests in `src/test/glidefuture_test.py`. Dry run: bar-accepted slots 84,713 -> 87,305, refused 4,603 -> 2,011. pytest 1,513 pass + the 1 known failure, mypy clean.
- Step 5.1 DONE (regeneration in a copy of the tree, `check_synthetic_regeneration`): no error, converged in 2 rounds, two runs byte-identical (md5 `69c02c7308a5664eee6e08289b0d0f7c`). Synthetic would go from 50,345 to 149,548 rows (75,805 only-regenerated, 741 only-committed, 7,891 column differences, not examined). `affiliera`, `accentuera`, `allouera` are generated; the 9 wrong `relouer` futures are gone; `créerions`, `clouas`, `déshabillâtes` are NOT rebuilt (probably wait for `slot-map`). The committed `LexiqueSynthetic.tsv` is NOT replaced.
- Still to do: verdicts #2-#5 (`slot-map`, `participle-from-infinitive` strict, `homograph-tag` strict, `lost-nasal`; all recommended accept) and the missing `infinitive-participle-present` row, then regenerate again and see how many of the 741 come back; 6 Mixte rows still have the glide before `R` (`graciera`, `réconcilier-` x3, `épierais`, `épierait`: correction rows to add); about 2,000 bar refusals remain (`razzier` `dz`, `substituer`, `bayer`, several-edit rows, not looked at).

**Update 2026-10-09 (late):** open decisions 1-3 are settled (section 4, "Answers") and the correction rows are implemented: 30 rows in `resources/mixteManualCorrections.tsv` (28 stray-`i` rows incl. `industrialisé`/`-ée`, + 2 `riant`), loaded with `mixteCorrections.tsv` by `loadAllMixteCorrections`; Mixte md5 now `d73812fb92ece0c19a5382f36799f813`; pytest 1,497 pass + the 1 known failure, mypy clean. Next: step 5.3.

**Nothing is committed.** The working tree also carries the earlier uncommitted work of the handoff (decision store, audit tools,
synth rules, lexicon files).

## 1. What this session did

The session went through question 1 of the handoff (the five `synth_rule` decisions) with examples, which led to a ruling on the
glide encodings of the `-ier`/`-yer`/`-iller` verbs, and then implemented it in S1 (the Mixte build).

State of the repo:

| Item | State |
|---|---|
| `resources/LexiqueMixte.tsv` | rebuilt by `python lexique.py`, md5 `d73812fb92ece0c19a5382f36799f813` (was `e176db7d…` before the 30 correction rows, `34560521…` before the glide rules) |
| `resources/LexiqueSynthetic.tsv` | **not regenerated**: the committed file is unchanged |
| pickles (`Dictionary`, `PhoneticTheory`) | **stale**: `rm -f *.pickle` before any rebuild |
| tests | `pytest src/test/`: 1,495 pass, 1 known failure (`plover_plugin_test::test_export_refuses_data_built_against_another_stock_dictionary`, stale expressions file); `mypy` clean |
| decisions | 2 new accepted `mixte_rule` rows in `resources/lexiconDecisions.tsv` (see 2); the 5 `synth_rule` and all other rows are still `pending` |

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
