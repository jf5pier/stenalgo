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

## Interactive Triage (Pass 4) — 2026-09-23
Inventory run: leaner option (2 Sonnet agents) chosen by user.

### README round
- t-r1 | README 38–62 strain criteria | **Both**: 3–4 line summary in README, full text in docs/ARCHITECTURE.md design rationale.
- t-r2 | README 76–187 phoneme order tables | **ARCHITECTURE, labeled** as a worked example from one Keyboard Layout Optimization (S4) run, not current output.
- t-r3 | README 189–214 keymap diagrams | user: **keep the first layer in README**, labeled "optimized single-key phoneme keymap"; **copy both layers to ARCHITECTURE**.
- t-r4 | README 229–237 verbs/prefixes/suffixes | user: **prefixes** are in ROADMAP — keep there, plus a stub in ARCHITECTURE. **Suffixes are solved** (feature strokes, i.e. the discriminating feature strokes of S6): state so and describe it in ARCHITECTURE.

### ROADMAP round
- t-m1 | ROADMAP history (30–383, done Phases 0/1/2/4) | **Delete**; git keeps it. New ROADMAP is forward-looking only.
- t-m2 | "what's left to do" (240–279: MARKING_OVERRIDES regeneration, -er/-ers nouns, satoptimizer cleanup, one orchestrated entrypoint, …) | **TODO.md**.
- t-m3 | Design decisions 1–6 | #1 reserved-key budget, #2 */# scope, #6 dual-target/Javelin → ARCHITECTURE design rationale; #4 fusion bug deferred, #5 prefix goal → ROADMAP; **#3 (conjugation as phoneme keys) kept in ARCHITECTURE as a one-line "rejected approach" note** (why elicitation replaced it).
- t-m4 | prior-art survey (594–637) | **new docs/PRIOR_ART.md**, linked from README doc map and ARCHITECTURE.
- t-m5 | ROADMAP remainder | open questions 1/3/8/9 stay in ROADMAP, resolved 2/4/5/6/7 deleted; "Ongoing" (untested cpsatsolver ambiguity math) → TODO.md; "Verification approach" → CLAUDE.md (near pytest/rebuild).

### todo.md round
- t-t1 | todo.md 194–213 lexicon data bugs (verified still present 2026-09-23: `baux` lemme "bail,bau", `baud` phon=bo) + ghost lemmas | **B36–B38** in TODO.md "Suspected bugs"; not fixed in this refactor.
- t-t2 | "p"/"f_p"/"m_p" fusion bug (239–275, legacy greedyoptimizer selector) | **Delete the entry**; the selector's fate is decided in Dead-Code Removal (Pass 5).
- t-t3 | todo.md history sections (146–238 except the data bugs, 276–384) | **Delete all**; TODO.md = suspected bugs + queued follow-ups + live items.
- t-t4 | todo.md B1–B35 + queued follow-ups (5–144) | keep as-is (inventory default).

### CLAUDE.md / recompute round
- t-c1 | CLAUDE.md pipeline summary (42–58) | **Compact list + link**: 8 one-line stages (name, entry point, output) + Pitfalls paragraph + link to PIPELINE.md (~15 lines).
- t-c2 | CLAUDE.md Core Data Model + Key Constants | **Both places**: short versions stay in CLAUDE.md; ARCHITECTURE gets the fuller data model and constant rationale.
- t-c3 | LEXICON_RECOMPUTE_PIPELINE.md | **Merge into PIPELINE.md** as a "Recomputing after a fix" section (évaser example, "safe to skip" Grouping Phase note, 7-step theory-1-collision checklist); then git rm. **No docs/RECOMPUTE.md** (overrides the plan).
- t-c4 | GLOSSARY.md:398 "(CLAUDE.md says 21)" | stale note (CLAUDE.md says 22) — drop in Doc Rewrite (Pass 6). (Main-thread fact, no question needed.)
- t-c5 | steno-trainer/README.md | keep unchanged (inventory: current, self-contained).

### Plan/design docs round (inventory/B.md)
- main-thread checks: `selectSharedDiscriminators` (src/featureextractor.py:266) is coverage-first with complexity tie-break and is live via `buildDiscriminatorSelection` (S2 paradigm-completion gating, util/completeVerbParadigms.py:281/:383; ambiguitychecker diagnostic :1403). `_isFeasibleAddition` / `checkComposedChords` are reached only from ambiguitychecker `__main__` (:1407) and tests.
- t-b1 | Bundle B (ATOMIC_KEYPRESS_REWIRE_PLAN, SHARED_DISCRIMINATOR_REWIRE_PLAN, DESIGN_alternate_press_sets, NOTES_2026-09-17_…, PLAN_2026-09-18_…) | **git rm all five + 3 extracts**: (1) parler-walkthrough rationale (why elicitation beat solver-picks-features), one paragraph → ARCHITECTURE; (2) "selection is coverage-first, complexity tie-break" one line → PIPELINE Synthetic Lexicon Building (S2); (3) 17.6% (8,413/47,827 groups) self-homograph scale figure → docs/specs/discriminating-features.md.
- t-b2 | design-phase bugs | **B39/B40 now** in TODO.md, marked "diagnostic path only": B39 `_isFeasibleAddition` (src/ambiguitychecker.py:608) misses new-vs-new composed-chord collisions; B40 `checkComposedChords` (:676) uses only `feasibleComboPhonemes[0]` (:712), half of a 2-phoneme combo.
- -er/-ers wishlist: single surviving copy = TODO.md (per t-m2).

### RESUME files round (inventory/C.md)
- main-thread checks: `régnions` and `régnons` both `ReN§` in the lexicon (no yod on -ions) and both still in questionnaire.json/elicitation_answers.json; `entêtai`/`entêtez` both `@tEte` (genuine homophones, no action).
- t-x1 | RESUME files | **git rm the 13 root RESUME_*.md; keep `scratch/reform1990/`** (RESUME_2026-09-16.md + STATUS.md) as the research trail behind resources/reform1990.tsv — final placement decided with Bundle D. The 9 `.py` comment references (inventory/C.md correction) are repointed/dropped in Doc Rewrite (Pass 6), proposed to the user first.
- t-x2 | trainer-features open items | (a) 182 ungendered nouns → **B41**; (b) definition search exact-spelling only, (c) hyphenated compounds drilled as two chords → **TODO.md** trainer follow-ups; (d) marker strokes as a Plover macro plugin → **ROADMAP**.
- t-x3 | single-copy facts, all kept: `régnions` false homophone (ReN§, no yod; possibly broader -ions/-iez after [N]) → **B42**; firmware button rewire for keys 2/10 → **ROADMAP** open question; `plover_stenalgo/` ↔ github.com/jf5pier/stenalgo-plover hand-sync → **ARCHITECTURE** one line; buckets 2/3 pooling never re-confirmed → **star-hash-marking.md "Known gaps"** one line.

### Data files and scratch round (inventory/D.md)
- t-d1 | pers-default comparison leftovers | **Delete all 5**: git rm elicitation_answers_pers1default.json, pers3default_repair_log.txt, pers_1PreferedOver_pers_3KeyAssignation; delete gitignored elicitation_questionnaire_pers3default.html, resolved_press_sets_pers3default.json. `util/build_pers3_default_answers.py` → Dead-Code Removal (Pass 5) candidate.
- t-d2 | scratch/ | **Keep scratch/reform1990/ and scratch/combined_regret.py** (proof script for the 10× / ~0.5 % gap headline); delete the other 4 regret scripts, scratch/sameLemmeHomophoneResolution.txt, scratch/callgraph. User addition: **"regret" needs a definition and its relevance explained** → Doc Rewrite (Pass 6): GLOSSARY entry "Regret (gap)" (cost of the chosen mark minus the per-pair optimum min(fA, fB), summed as gap%; why it drives R4–R6), star-hash-marking.md §2 states regret = gap explicitly, and combined_regret.py's docstring says what it reproduces and links spec §2. Open detail for Pass 6: combined_regret.py is untracked — `git add` it if it's meant to survive.
- t-d3 | morphalou/ | download URL + expected path (morphalou/5/Morphalou3.1_CSV.csv) in **PIPELINE Synthetic Lexicon Building (S2)** + one line in the **README quickstart**.
- t-d4 | ARCHITECTURE artifact table | **tracked files + key gitignored caches** (pickles, resolved_press_sets.json, questionnaire.json, theory*.tsv) with rebuild commands; diagnostics (ambiguity_report.tsv, feature_keypress_feasibility.tsv) as a footnote.
- inventory defaults accepted without a question (all "keep, already documented"): conjugation_disambiguation_order.txt, elicitation_answers.json, excluded_words.txt, keypress_groups.json, plover_stenalgo_dictionary.json, realization_report.json, requirements.txt, starboard3h.json, images/, gitignored caches.

Interactive Triage (Pass 4) complete 2026-09-23.

## Dead-Code Removal (Pass 5) approvals (2026-09-23)
- p5-1 | legacy SAT/CP-SAT discriminator solvers (satoptimizer.py, cpsatoptimizer.py, satoptimizer_test.py 22 tests, dictionary.py:47 commented import) | **Remove**.
- p5-2 | legacy greedy discriminator assignment (assignDiscriminatorKeypresses, _buildStrokePool, greedyoptimizer_test.py 16 tests; FEATURE_PRIORITY only if Phase 0 goes) | **Remove**. GRAMCAT_PRIORITY stays.
- p5-3 | Phase 0 ambiguity-report diagnostic (ambiguitychecker __main__, buildAtomicFeatureToWords, findFeatureKeypresses, checkComposedChords, _isFeasibleAddition, _appendCodaAddition, findCollidingNewAdditions, _selectCanonicalIndex, classifyTheory, classifyStrokeCluster; 17 tests; FEATURE_PRIORITY; drop B39/B40) | **Remove** (after confirming no rebuild-chain caller). detectCrossCategoryClash is live — stays.
- p5-4 | greedy feature grouping (runFeatureGrouping, greedyColorMarkers, coOccurrencePairs, wouldCollideIfMergedPairs, _findSharedKeypressPair, FeatureGroupingResult, __main__) | **Remove** (after confirming CP-SAT scans K independently; preferences hard-coded in build_keypress_groups.py). Loaders/verifiers stay.
- p5-5 | featuregroupingsat Preferring API (minKeypressesSatPreferring, _bestAssignmentPreferring, __main__ use; 5 tests) | **Remove**. aloneKeys/mustDifferGroups/mustShareKey stay.
- p5-6 | grammar.py scorer twins (analysePhonemSyllabicAmbiguity_serial, analysePhonemeLexicalAmbiguity_serial, analyseMultiphonemeLexicalAmbiguity plain) | **Remove**.
- p5-7 | lexique.py helpers, Dictionary write-only fields, dictionary.py __main__ comments, keyboard.py __main__ | **Keep** (not selected).
- p5-8 | util/build_pers3_default_answers.py | **Delete** (git rm; hazardous to rerun).
- p5-9 | ~41 one-shot util/fix*/validate*/inventory*/split*/copy* scripts | **Keep as-is**; PIPELINE lists them as one-shot.
- p5-10 | execution | **main thread**, one commit per group, pytest after each, full md5 rebuild at end.
