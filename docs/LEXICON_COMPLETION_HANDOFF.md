# Lexicon completion: handoff and open questions

> **Superseded as the resume point by `docs/LEXICON_COMPLETION_CONTINUATION.md` (2026-10-09, after the glide session).** This file keeps
> the nine questions, the measured numbers and the tools table; the continuation file says which parts are decided, implemented or still open
> (question 1: examined but no verdict recorded; question 3: partly answered by the glide rulings; the rest untouched). Its Mixte md5
> `34560521…` is now `e176db7d…`, and the test count is 1,496 (one known failure).

Resume point after a context clear (2026-10-09). Plan: `/home/jfsp/.claude/plans/have-a-look-at-whimsical-gray.md` (approved
2026-10-08). Spec of the decision machinery: `docs/specs/lexicon-decisions.md`. Status before this work:
`docs/SYNTHETIC_LEXICON_STATUS.md`.

Goals:
1. Mixte and Synthetic are complete for the Lexique383 lemmas.
2. Both are regenerable deterministically.
3. Both can feed the discriminator optimizer.

Mixte sets the phonetic and syllabic conventions. The references only check and choose: Wiktionary (committed TSV),
GLÀFF (external, `glaff/`) and Morphalou (external, `morphalou/`). Decisions are grouped so that one ruling covers many
slots.

Nothing is committed. **No decision has been taken**: every row of `resources/lexiconDecisions.tsv` is `pending`, so
every new mechanism is still off and the committed `LexiqueSynthetic.tsv` is unchanged. `LexiqueMixte.tsv` was rebuilt
by the current `lexique.py`, with a deterministic md5 `34560521…`; it differs from the pre-session working tree only by
the `interpeller` alignment fix.

## Where it stands

Measured on from-scratch regenerations in temp trees, VER only (282,462 expected slots for 6,289 lemmas):

| Configuration | Synthetic VER rows | VER slots still missing | of which no_template |
|---|---|---|---|
| Committed file | 42,381 | 165,321 | 30,537 |
| Current code, no rule accepted | 45,783 | 161,919 | 30,537 |
| Every synth rule forced | 165,145 | 42,866 | 30,537 |
| Every synth rule + every template group accepted | 188,832 | **19,179** (1,955 lemmas) | 3,936 |

- The last configuration has 98.3% of the rows with a reference exact or equivalent to Wiktionary/GLÀFF, and two runs
  are byte-identical (md5 `7e6c297d…`, 4 rounds, about 6–8 min alone).
- Remaining causes: `reference_differs` 6,287, `unattested_ending` 3,603, `no_infinitive` 3,444, `no_template` 3,936,
  `infinitive_outlier` 1,200, and smaller ones.
- NOM: 1,280 missing slots; ADJ: 4,640. These are untouched by this work, apart from the audit.
- Last check, bar-only regeneration after T3.9's second `robustSuffix` change (it prefers the majority suffix when
  longer): md5 `654c148c…`, which is no longer the earlier `9c91226c…`. 130,797 VER rows against 130,954, 98.2% exact or
  equivalent (unchanged), 2,272 `differs` against 2,337. The 157 fewer rows fit the new `infinitive_outlier`
  refusals, but they were not traced row by row. Synthetic `sounded` is 333: the same `em-`/`en-` `E`/`e` class as
  question 7.

## Questions for the user

Answer in `resources/lexiconDecisions.tsv` with `python -m util.review_lexicon_decisions [--kind K]`. The CLI sorts by
slots, has `y`/`n`/`s`/`p`(param)/`d`(split)/`q`, and saves after every answer. Policy questions get a plain answer.

1. **Accept the synth rules?** There are five `synth_rule` decisions, each with a `rec(opus)` note:
   - `reference-validated agreement bar` (`21dde669cb`): about +85k slots, param = floor 0.5;
   - `slot-map` (`2c77b27d21`): +26k, including a pseudo-infinitive derived from the other forms;
   - `participle-from-infinitive` (`08b1b8cedd`), param `strict`;
   - `homograph-tag` (`9b22fcd182`), param `strict`;
   - `lost-nasal` (`0cc34490fa`).

   Also `infinitive-participle-present` (T3.9), which has no decision row yet: add it like the others (see "Next steps").
   - **Sub-question: which references count.** Today a candidate passes if it matches the union of Wiktionary and GLÀFF.
     About 1,400 bar rows match only GLÀFF's 2013 variants (`boucliez` `buklje` against current Wiktionary `buklije`).
   - The alternative is current Wiktionary first, whenever it has the slot; `ReferenceBar.referencesOf` in
     `util/completeVerbParadigms.py` is the one place to change.
   - Recommendation: Wiktionary first, tied to question 3.
2. **Untemplated verbs.** There are 32 `template` decisions.
   - `-er → aim:er` (`e992e4e2e8`) covers 553 lemmas; 30 groups have members, 624 lemmas in all.
   - Once accepted, `python -m util.apply_template_decisions` writes them into `verbModelExceptions.tsv` (managed rows).
   - Twelve proposed lemmas have a non-trusted hand row and are never overridden; they need an individual ruling.
     - needs_review: accalmir, agonir, brouir, esbaudir, grinchir, rechampir, ébaudir, éperdre.
     - skip_artifact: amochir.
     - defective: chevir, avenir, ravoir.
   - Unresolved proposals: 24 ambiguous, 32 with no evidence, 15 with no candidate (inflected forms stored as lemmas:
     `appert`, `chaut`, `choses`, `découverte`) and 9 contradicted (`verb_template_proposals.tsv`).
3. **Policy: are mid vowels and glides conventions (Mixte wins)?** The audit found real differences from the references in
   2,209 Mixte VER slots:
   - 1,677 mid vowel: `E`/`e` in non-final syllables, `ei`/`ê`/`ai`, `2`/`9`;
   - 192 glide or hiatus: `aks@tye`/`aks@t8e`, `ij`/`i`;
   - 336 other.

   For NOM/ADJ (against Morphalou): 2,730 slots, of which 684 mid vowel and 735 glide (`8→y @ u`, 472, `actuel`).

   These vowels vary freely in unstressed syllables, and the references disagree among themselves. Recommendation:
   - add both classes to `CONVENTION_EDITS` (`src/diffsignature.py`, spec §3);
   - replace them with an **intra-lemma consistency check**: the same stem grapheme should have the same vowel in every
     form of a lemma, which is what a typist needs to predict a stroke.

   Otherwise, review about 60 heterogeneous groups.
4. **NOM/ADJ specifics.**
   - **`-isme`**, group `e23c2b0f53`, 369 slots, plus an L1 group of 92. Ours is `izm`, Morphalou `ism`. Recommendation:
     keep `izm` (reject).
   - **`2→° @ e`**, group `90cae078aa`, 99 slots, homogeneous (`premier` `pR2mje`, `amenuiser`). Recommendation: accept.
5. **The 99 other Mixte groups** have `rec(opus): accept|reject|split` notes. To review them:
   `python -m util.review_lexicon_decisions --kind mixte_rule`, then `--kind mixte_typo`.
   - Accept: `courir`/`-quérir` futures with `RR` (keeps `courrait` apart from `courait`), `dompter`, `sers`, `reperds`,
     `réconcilierai`, `interpela` schwa, `enchtiber`.
   - Your call: the anglicisms `manager`, `luncher`, `surfer`, `dealer`.
   - Reject: voicing assimilation (`absent` `aps`: keep Mixte), and every group whose reference is garbage.
   - **Should the audit drop its lemma+tag reference tier** (428 rows, the source of most of the garbage:
     `reconfigure` → `R°k§plik`, `puis` → `p2`)? Recommendation: yes.
6. **`arguer`:** `[aʁɡɥe]` or `[aʁɡe]`? It decides `b3efd1782d` and `64402d8bce`.
7. **Internal inconsistencies** (`python -m util.check_lexicon_features`, already in HEAD).
   - `phon` differs from the join of `syll_cv` in 132 Mixte rows and about 390 rows of the regenerated Synthetic.
     108 of the Mixte rows are `E`/`e` in the `em-`/`en-` + `ê`/`ei` words (`embêter`); 24 are loanwords
     (`capharnaüm`, `game`).
   - Unit counts differ in 53 Mixte rows (`souler` 18, `asseoir`/`rasseoir` 18, `quincaillier`, `joaillier`) and about
     30–50 Synthetic rows.
   - Strokes use `syll_cv`. Recommendation: `syll_cv` wins, through a systematic `mixte_rule` (task T2.5). Should
     `phon` be rebuilt from it?
8. **Likely lemma errors.**
   - `liserer` should be `lisérer`.
   - `écher` should be `èche`.
   - `rapiécer` needs an è-stem template.
   - `retraire`'s Verbiste template has no passé simple.

   Should these become rows of the proposed `resources/lemmaCorrections.tsv` (TODO.md:21-23), or be excluded?
9. **Confirm that Mixte wins:**
   - 1990 reform `balloter`/`greloter` single `t` (the references have `tt`);
   - `céderai` with `é` (the references have `cèderai`).

## Next steps (after the answers)

1. Record the verdicts (review CLI).
2. Add the missing `synth_rule` row for `infinitive-participle-present`: the same Python snippet pattern as the others,
   `minedDecision('synth_rule','-',SYNTH_RULES[name])`, whose id equals `ruleGroupId(name)`.
3. If question 3 is "conventions": extend `CONVENTION_EDITS` and add the intra-lemma consistency miner. Then rerun
   `python -m util.audit_mixte`; it keeps verdicts and `rec(opus)` notes and flags stale groups.
4. Apply the decisions:
   - `python -m util.build_mixte_corrections`, then `python lexique.py` (deterministic, 16 s);
   - `python -m util.apply_template_decisions`.
5. T2.5 (question 7): realign the inconsistent rows.
6. Remaining gaps:
   - `reference_differs` slots: review them as groups by mining `synthetic_bar_rejections.tsv` with the same signatures
     (`util/audit_mixte.py --lexicon synthetic` is the model);
   - `no_infinitive` lemmas whose only form is a `par:pre` homograph (`adoniser`, `attoucher`, `agneler`): manual rows
     in `resources/syntheticManualRows.tsv`;
   - NOM/ADJ gaps (T3.8).
7. Phase 4–5 of the plan:
   - `python -m src.elicitation --ask` and `util.build_keypress_groups` on the new lexicons;
   - then a full `python dictionary.py` from a clean state (`rm -f *.pickle`), the md5 comparison of the outputs (they
     will change; you judge), and a second identical run;
   - then commit, with your approval. The Wiktionary TSV is CC BY-SA: commit its NOTICE with it.
8. Docs: refresh `docs/SYNTHETIC_LEXICON_STATUS.md`, `docs/PIPELINE.md` (S1 corrections and rules hook; S2 rules,
   decisions and new tools), the CLAUDE.md command list and test count (now 1,470), and TODO.md.

## Tools added this session

All are tested and clean under bare `mypy`. `pytest`: 1,470 pass; the one failure is the known stale-expressions
`plover_plugin_test` failure.

| Tool | Role |
|---|---|
| `util/lexicon_completeness.py` | census of expected slots per lemma (`mixte` / `synthetic` / `excluded` / `missing:<cause>`), `--skip-reasons`; data `resources/excludedSlots.tsv` |
| `util/_verbreferences.py` | Wiktionary + GLÀFF index (`RefSet`, conflicts, `forRow`/`forOrtho`/`matchRow`); `--conflicts` (366 genuine conflicts) |
| `util/_morphalouphon.py` | Morphalou `PHONÉTIQUE` → lexicon alphabet, NOM/ADJ index, `--stats` (96.5% agreement) |
| `src/diffsignature.py` | edit scripts, anchoring on units, L1–L4 signatures, homogeneous and heterogeneous grouping |
| `src/lexicondecisions.py`, `resources/lexiconDecisions.tsv` | decision store: 604 pending (184 `mixte_rule`, 387 `mixte_typo`, 5 `synth_rule`, 32 `template`); sidecar `lexicon_decision_examples.json` (gitignored, rewritten by the audit) |
| `util/review_lexicon_decisions.py` | interactive review |
| `util/audit_mixte.py` | miner: Mixte (or `--lexicon synthetic`) against the references, VER + NOM/ADJ; report `mixte_audit_report.md` |
| `util/build_mixte_corrections.py`, `src/mixtecorrections.py`, `src/mixterules.py`, `resources/mixteCorrections.tsv` | replay of accepted Mixte groups inside `lexique.py` (`outputMixedLexique`) |
| `util/propose_verb_templates.py`, `util/apply_template_decisions.py` | templates for the untemplated verbs |
| `src/synthrules.py` + `util/completeVerbParadigms.py` | gated synth rules, `--force-rule NAME[=PARAM]` (also on `build_synthetic_lexicon`, `check_synthetic_regeneration`); outputs `synthetic_bar_rejections.tsv`, `synthetic_skip_reasons.tsv` |
| `util/check_lexicon_features.py` | integrity checks (units, sounded, infover, excluded, features) |

Fixes:
- `lexique.py` `applyOrthoRewrite`: a deletion inside a multi-letter unit kept the separator wrongly (`interpeller`).
- `util/_pronunciation.compare`: ties made deterministic.
- `src/verbparadigm.py` `robustSuffix`: one outlier donor such as `dealer` `dil9R` collapsed a template's infinitive
  suffix and broke every `aim:er` subjunctive once the templates were applied.
- `writeSynthetic` deduplicates its lines.
- GLÀFF `Vmn----` and `Vmpp---` are mapped to `inf` and `par:pre`.
- README and PIPELINE: GLÀFF install.

Measurement trees and logs are in the session scratchpad
(`/tmp/claude-1000/-home-jfsp-Steno-stenalgo/7f132685-…/scratchpad/`, temporary).
