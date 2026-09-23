# Triage decisions log (append-only)

Format: `block-id | source file:lines | decision | destination | note`

## Scoping decisions (2026-09-22, before Pass 0)
- New docs under `docs/`; root keeps README.md, CLAUDE.md, TODO.md, ROADMAP.md, LICENSE.
- Dead code: remove with per-item approval.
- Triage also covers stale data files and untracked `scratch/`.
- Triage via multiple-choice rounds.
- Stages/phases/passes get descriptive names, code in parentheses, cited by name.
- `steno-trainer/user.json`, `user_fr.json`: personal Plover dictionaries, not committed in the snapshot (triage later).

## Glossary Review (Pass 1d) — terminology (docs/refactor/callgraph/91-review-questions.md)
- a1 | Cluster | **Drop "cluster" entirely**: Homophone Group (same lemmeGramCat), Theory-1 collision (one theory-1 stroke), Lemma-homophone group (*/# scope). Code names like rankHomophoneCluster stay, noted in glossary.
- a2 | Reading vs Feature Combination | **Feature Combination** (keep root GLOSSARY decision); "Reading" = avoid (on-disk `readings` field / trainer `Reading` type noted as code names).
- a3 | Keypress | **Keypress Group** for the abstract unit; "Keypress" only for the keyboard.py type.
- a5 | Chord | **Stroke; avoid "chord"**. "key-set" for part of a stroke, "illegal stroke", "drill item" for trainer record.
- a6 | marker/atom/feature/discriminator | **User: "stay with feature and atomic feature in the code"** → Feature / Atomic feature are the canonical terms (not "marker"). Follow-up on phase names asked in next round.
- a7 | mark vs marker | **"star/hash mark"** (and "star/hash code") in prose for */#.
- a8 | appended strokes | **User: "Extra stroke, feature discriminating stroke, */# marker strokes"** → umbrella "extra stroke"; Phase P coda stroke = "feature discriminating stroke"; escalated bare */# strokes = "*/# marker stroke". (alternate stroke: confirm)
- a9 | R4 naming | **"Frequency-ratio rule"** in prose; constant unchanged.
- phase names | **Discriminating-Feature Elicitation (Phase E), Discriminating-Feature Grouping (Phase G), Discriminating-Feature Stroke Realization (Phase P)** (replaces "Marker …").
- a8 follow-up | **Alternate is not an extra stroke**: "extra stroke" = feature discriminating stroke + */# marker stroke only; "alternate entry" = separate concept (a second dictionary entry).
- a10 | rule ids | **R1–R7 in code order, always cited with the rule name**, e.g. "frequency-ratio rule (R4)".
- a11 | collision naming | **Same-lemmeGramCat collision**; "in-scope" only as function name.
- b1 | S3 name | **Same-Lemma and Grammatical-Category Disambiguation (S3)** (user wording, spelling normalized).
- b2 | S4 name | **Different-Lemma or Grammatical-Category Disambiguation (S4)** (user wording, spelling normalized). The mechanism inside it = star/hash marks.
- b3 | Phase E | **Named sub-steps**: Questionnaire Generation, Answer Collection (human loop), Press-Set Resolution.
- b4 | Phase P two call sites | user asked for more details before deciding.
- b4 | Phase P call sites | **"inline path" / "report build" / "realization report"** (user saw the drift explanation: trainer legend reads the tracked report, Plover recomputes inline).
- a12 | lemma-named code | **Queue renames in TODO** (LemmaHomophoneGroupKey → e.g. HomophoneGroupKey, groupWordsByLemme → groupWordsByLemmeGramCat); no code change now.
- b5 | layout statistics | **NOT dead code.** optimizeBiphonemeOrder + analyseAmbiguities feed cpsatsolver.optimizeKeyboard (verified: cpsatsolver.py:14/:48 syllabicPartAmbiguity, :363 pairwiseBiphonemeOrderScore). Keyboard layout regeneration (starboard3h.json) is a real, rarely-run, costly pipeline step. Document it as such; excluded from Dead-Code Removal (Pass 5). Note/TODO: solver call commented out at dictionary.py:494 — no command regenerates starboard3h.json today.
- a4 | signature/press-set | user asked: "keypress set" instead of press-set? "Homophone group feature set"? → follow-up round.
- a4a | press-set | **Discriminating feature set** (preferred); "press-set" = legacy/avoid term (pressSet / resolved_press_sets.json keep their code names).
- a4b | GroupSignature | **Homophone group set of feature sets** (user wording, typo fixed); "signature" = avoid in prose.
- b6 | synthetic lexicon | **Own stage** ("Synthetic Lexicon Building"), not a sub-stage of Lexicon Building.
- b8 | export | **One stage, two branches** (Plover, trainer).
- stage list | **8 flat stages**: Lexicon Building (S1) → LexiqueMixte.tsv; Synthetic Lexicon Building (S2) → LexiqueSynthetic.tsv (manual); Dictionary Loading (S3) → Words, syllables, stats; Keyboard Layout Optimization (S4) → starboard3h.json (rare, costly); Phonetic Theory Building (S5) → theory 1; Same-Lemma and Grammatical-Category Disambiguation (S6) [3 phases]; Different-Lemma or Grammatical-Category Disambiguation (S7) → theory 2 (star/hash marks); Theory Export (S8) → Plover + trainer.
- b9 | phase codes | **User: "Use meaningful names like Elicitation Phase, etc"** → no letter codes in prose. Phases: Discriminating-Feature Elicitation (Elicitation Phase), Discriminating-Feature Grouping (Grouping Phase), Discriminating-Feature Stroke Realization (Realization Phase). Call ids: S6.Elicitation.n / S6.Grouping.n / S6.Realization.n. Glossary maps the legacy "Phase E/G/P" (file names phase_g_*, phase_p_*, commit history) to these.
- b7 | superseded by stage list (Keyboard Layout Optimization is a full stage).
- Suspected bugs: file all of 90-findings.md into todo.md (user said suspected bugs "can be added to the Todo.md"); no per-bug interrogation.
- b9 confirmed by user: meaningful phase names (Elicitation / Grouping / Realization Phase); **file names may change too.**
- file renames | src/phaseg.py → src/featuregrouping.py; src/phasegsat.py → src/featuregroupingsat.py; src/test/phaseg_test.py → src/test/featuregrouping_test.py; src/test/phasegsat_test.py → src/test/featuregroupingsat_test.py; util/build_phase_g_assignment.py → util/build_keypress_groups.py; util/build_phase_p_realization.py → util/build_realization_report.py; phase_g_keypress_assignment.json → keypress_groups.json; phase_p_keypress_realization.json → realization_report.json.
- code scope | **Files + identifiers + comments**: runPhaseG → runFeatureGrouping, PhaseGResult → FeatureGroupingResult, "Phase E/G/P" in comments/docstrings reworded to the new names. Behaviour-neutral, verified by rebuild check.
- md scope | user: "Update all md files" to the new terminology.
- spec name (2026-09-23) | `docs/specs/same-lemma-markers.md` → **`docs/specs/discriminating-features.md`** (user: "ok for the rename").

## Spec Extraction (Pass 2) — 2026-09-23
- specs | written `docs/specs/star-hash-marking.md` and `docs/specs/discriminating-features.md` in the main thread (no agent). Code = source of truth; prose mismatches found were all already superseded (append-after-Realization-stroke → merged mark 2026-09-22; ROADMAP "no stroke to the most frequent lemma" → rule stack; plan's FEATURE_PRIORITY canonical choice / K=5 → answers decide / K=7; RESUME's design-order Rule 1/2/3 numbering → R1–R7). No new code bugs; precedence-order enforcement gap already B12.
- p2-q1 | stale .py docstrings | **Fix now** (comment-only): `util/build_keypress_groups.py` K=6 note dated + K=7; `src/ambiguitychecker.py` "Rule 1/2/3" → rule names with R1–R7 ids. pytest 593 passed.
- `conjugation_disambiguation_order.txt` stays at the repo root (plan default; linked from the spec, not copied).
