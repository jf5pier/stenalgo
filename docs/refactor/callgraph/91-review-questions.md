# Review questions for Glossary Review (Pass 1d)

Questions for the user, produced by the merge step of Pipeline Call Graph and Glossary
(Pass 1). Each is answerable by picking one option. The provisional pick already used in
`docs/PIPELINE.md` and `docs/GLOSSARY.md` is marked **(provisional)**; the glossary entries
that depend on the answer carry "⚠ provisional — pending user decision (id)".

---

## (a) Terminology conflicts

### a1. "Cluster" — three meanings
Used as: (1) same-`lemmeGramCat` homophones, in ATOMIC_KEYPRESS_REWIRE_PLAN.md:40 (root
GLOSSARY.md already says "use Homophone Group"); (2) all words on one theory-1 stroke,
`StrokeClusterReport` src/ambiguitychecker.py:46; (3) words of different `lemmeGramCat` on one
final stroke, `rankHomophoneCluster` :261 and Lemma-Homophone Marking (S4).
- A. **(provisional)** Homophone Group for (1), Theory-1 collision for (2), Lemma-homophone cluster for (3); never bare "cluster". Reason: keeps "cluster" only where the code already uses it for Lemma-Homophone Marking (S4).
- B. Homophone Group for (1), Stroke cluster for (2), Lemma-homophone cluster for (3).
- C. Homophone Group for (1), Theory-1 collision for (2), Lemma-homophone group for (3) (drop "cluster" entirely).

### a2. "Reading" vs "Feature Combination"
"Reading" is used by the plan (ATOMIC_KEYPRESS_REWIRE_PLAN.md:46), the `readings` field of
`resolved_press_sets.json`, `type Reading` in util/export_practice_words.py:70 and every stage
file. "Feature Combination" is the code type (`FeatureCombination` src/elicitation.py:27) and
the root GLOSSARY.md's preferred term.
- A. **(provisional)** Reading. Reason: plain word, already in the on-disk format and trainer; "feature" is the legacy word for a marker.
- B. Feature Combination (keep the root GLOSSARY.md decision).
- C. Reading in prose, keep `FeatureCombination` as the code type name only.

### a3. "Keypress" — physical type vs abstract unit
`Keypress: TypeAlias = tuple[int, ...]` (src/keyboard.py:26) is a physical per-finger key
combination; Marker Grouping (Phase G) docstrings (phaseg.py:10) and the plan
(ATOMIC_KEYPRESS_REWIRE_PLAN.md:49) use "keypress" for the abstract unit a set of markers maps to.
- A. **(provisional)** "Keypress Group" for the abstract unit; "Keypress" only for the keyboard.py type. Reason: matches `markersByKeypress` output and `KeypressGroupPhysicalAssignment`.
- B. "Marker group" for the abstract unit (says what it groups); keep "Keypress" for keyboard.py.
- C. Keep "keypress" for both, disambiguated by context.

### a4. "Signature"
Root GLOSSARY.md defines it as the old name of a press-set (with a stale "union across
readings" definition); `GroupSignature` (src/phasegsat.py:37) is a group's shape used to
deduplicate CP-SAT problems.
- A. **(provisional)** Press-set for what is pressed, "group shape" for `GroupSignature`; avoid "signature" in prose. Reason: removes both the stale and the clashing meaning.
- B. Press-set for what is pressed; keep "group signature" for the shape.

### a5. "Chord" vs "Stroke" vs "key-set"
"Chord" means a physical stroke (keyboard.py:21, Marker Stroke Realization (Phase P)
docstrings, "illegal chord" in the Phonetic Theory Building (S2) stage file), an abstract
keypress (plan :49) and a trainer record (`Chord`, export_practice_sentences.py:50).
- A. **(provisional)** "Stroke" for keys pressed together, "key-set" for part of a stroke (candidate key-set), "illegal stroke", "drill item" for the trainer record; avoid "chord". Reason: Stroke is the code type.
- B. Allow "chord" as a synonym of stroke in prose, but never for the abstract unit or the trainer record.
- C. "Chord" for any physical key combination (stroke or part of one), "stroke" only for the `Stroke` type.

### a6. "Marker" vs atom / atomic feature / feature / discriminator
The same grammatical value (`pers_2`, `nbr_p`, `f`) is called marker (plan :44, stage files),
atom (`atomsA` in the answers), atomic feature (`atomicFeatures` word.py:406), feature (legacy
`WordFeature`) and discriminator (legacy function names).
- A. **(provisional)** Marker everywhere; the others are "avoid". Reason: the plan's term, and it names the stages.
- B. Marker in prose, but accept "atom" as the on-disk/UI field name (`atomsA`) without renaming.

### a7. "Mark" vs "marker"
Same-Lemma Disambiguation (S3) uses **markers** (grammatical values, realized as coda keys);
Lemma-Homophone Marking (S4) adds **marks** (`*`/`#`). The words are one letter apart.
- A. **(provisional)** Keep "marker" (grammatical value, Same-Lemma Disambiguation (S3)) and "mark" (`*`/`#`, Lemma-Homophone Marking (S4)), each with an "avoid" note for the other meaning. Reason: both are already in stage names.
- B. Rename the Lemma-Homophone Marking (S4) term to "star/hash mark" in prose (and "star/hash code").
- C. Rename the Same-Lemma Disambiguation (S3) term to "grammatical marker" in prose.

### a8. The strokes appended after the base strokes
Called "extra stroke", "trailing stroke", "coda extra stroke", "Phase P stroke" and "marker
stroke" for the coda-bank stroke of Marker Stroke Realization (Phase P); "bare `*#` strokes" for
Lemma-Homophone Marking (S4); "alternates" for self-homograph extra entries.
- A. **(provisional)** "Marker stroke" (the coda stroke of Marker Stroke Realization (Phase P)), "bare mark stroke" (Lemma-Homophone Marking (S4)), "alternate stroke" (self-homograph entry); "extra stroke" only as the umbrella. Reason: each name says which mechanism produced it.
- B. "Extra stroke" for the coda stroke of Marker Stroke Realization (Phase P), "bare mark stroke" and "alternate stroke" for the others.
- C. "Coda marker stroke" for that stroke (explicit about the bank), others as in A.

### a9. R4: "frequency-ratio rule" vs "10x ratio exemption"
The code (`RATIO_EXEMPTION_THRESHOLD`, docstring :200) and ROADMAP.md:175 call it an
exemption, but the rarer word is still marked; only the category rule is skipped. Two exporter
docstrings took "exemption" literally (doc drift 47).
- A. **(provisional)** "Frequency-ratio rule" in prose; the constant name is left alone. Reason: describes the outcome correctly.
- B. "Frequency-ratio rule" in prose and rename the constant later (e.g. `FREQUENCY_RATIO_THRESHOLD`) in Dead-Code Removal (Pass 5) or later.
- C. Keep "ratio exemption", clarified as "exempt from the category rule".

### a10. Numbering of the marking rules
The `decideStarHashMark` docstring numbers R1 homograph … R6 category priority (R7 unnumbered);
comments at :392/:431 and RESUME_2026-09-20-starhash-priority.md use ratio = Rule 1, homograph
= Rule 2, doublet = Rule 3.
- A. **(provisional)** R1-R7 in code order (as in PIPELINE.md), and always cite the rule's name next to its number. Reason: matches execution order.
- B. Drop numbers, cite rules by name only.
- C. Adopt the RESUME numbering.

### a11. "In-scope collision" vs "same-lemmeGramCat collision"
`_isInScopeCollision` (ambiguitychecker.py:968) and the Same-Lemma Disambiguation (S3) stage
file say "in-scope"; the regression invariant, CLAUDE.md and the report use "same-`lemmeGramCat`".
- A. **(provisional)** "Same-lemmeGramCat collision"; "in-scope" only as the function name. Reason: says what the scope is.
- B. "In-scope collision" (shorter), defined once.
- C. "Same-paradigm collision" (ties in with option b1-B).

### a12. Code names that say "lemma" but mean lemma + category
`LemmaHomophoneGroupKey` (elicitation.py:24) keys a same-`lemmeGramCat` group;
`groupWordsByLemme` (word.py:414) groups by `lemmeGramCat` while `groupWordsByBareLemme` groups
by bare lemme.
- A. Document only (glossary notes, as now); no renames.
- B. Queue renames (`HomophoneGroupKey`, `groupWordsByLemmeGramCat`) for a later code pass.

---

## (b) Stage and phase naming refinements

### b1. Same-Lemma Disambiguation (S3)
It works on the same `lemmeGramCat` (lemma + grammatical category), not the same bare lemma
(`_isInScopeCollision`, `groupWordsByLemme`).
- A. Keep "Same-Lemma Disambiguation (S3)" and define "lemma" as lemma + category in this pipeline.
- B. "Same-Paradigm Disambiguation (S3)".
- C. "Inflection Disambiguation (S3)" (it separates the inflected forms of one paradigm).

### b2. Lemma-Homophone Marking (S4)
Its filter is "≥2 distinct `lemmeGramCat`" (ambiguitychecker.py:402), so it also marks
same-lemma cross-category clashes (appel NOM / appelle VER; 34-40 in the realization report).
- A. Keep the name and add the scope note (as now).
- B. "Cross-Paradigm Homophone Marking (S4)".
- C. "Star-Hash Marking (S4)" (names the mechanism, not the scope).

### b3. Sub-steps of Marker Elicitation (Phase E)
In a rebuild `python -m src.elicitation` asks nothing; it generates questionnaire items and
resolves the stored answers. The human part (page, answering, copying answers) is separate.
- A. Split into named sub-steps: "Questionnaire Generation", "Answer Collection" (human loop), "Press-Set Resolution".
- B. Keep one phase name; describe the human loop only in the rebuild instructions (as now).
- C. Split into two phases: "Marker Elicitation (Phase E)" for the human loop and "Press-Set Resolution (Phase R)" for the rebuild step.

### b4. The two call sites of Marker Stroke Realization (Phase P)
PIPELINE.md says "inline path" (inside `buildFinalTheory`, feeds theory 2 and exports) and
"report build" (`util/build_phase_p_realization.py`), whose output it calls the "realization report".
- A. **(provisional)** "inline path" / "report build" / "realization report".
- B. "live realization" / "realization report build" / "realization report".
- C. Name the report after its only consumer: "marker legend report".

### b5. The statistics sub-step of Phonetic Theory Building (S2)
Syllable inventory (S2.3) feeds theory 1; Phoneme order search (S2.4) and Ambiguity statistics
(S2.5) only feed the uncalled solver and the fallback keymap.
- A. Give Phoneme order search (S2.4) and Ambiguity statistics (S2.5) a sub-stage name, "Layout Statistics (S2a)", paired with Keyboard Layout Optimization (S2b).
- B. Keep them as ordinary calls of Phonetic Theory Building (S2), flagged "off the live path" (as now).
- C. Treat them as dead code candidates for Dead-Code Removal (Pass 5) and do not name them.

### b6. Synthetic Paradigm Completion (S1b)
A manual side branch of Lexicon Building (S1): verb completion, NOM/ADJ gap generation,
dual-form fillers, one in-place repair.
- A. Keep "Synthetic Paradigm Completion (S1b)".
- B. "Paradigm Gap Filling (S1b)".
- C. Make it its own stage, "Synthetic Lexicon Building (S1b)", at the same level as Lexicon Building (S1).

### b7. Keyboard Layout Optimization (S2b)
Not run; its past output is `starboard3h.json`.
- A. Keep it in PIPELINE.md as a short design-rationale subsection (as now).
- B. Move the rationale to a separate design doc and leave a one-line pointer.

### b8. Theory Export (S5)
Two very different consumers: Plover (dictionary, key table, plugin) and the steno-trainer.
- A. Keep one stage, "Theory Export (S5)", with two branches (as now).
- B. Split into "Plover Export (S5)" and "Trainer Export (S6)".

### b9. Code scheme
Stages use `S1`-`S5`, sub-stages `S1b`/`S2b`, and the three phases of Same-Lemma
Disambiguation (S3) use letters (`Phase E/G/P`), with call ids like `S3.P.5.2`.
- A. Keep the mixed scheme (as now).
- B. Unify phases as `S3E`, `S3G`, `S3P` (drop "Phase").
- C. Renumber phases `S3.1`, `S3.2`, `S3.3`.
