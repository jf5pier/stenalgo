# RESUME 2026-09-25 — Spelling-variant removal (COMPLETE, uncommitted)

Everything done and verified 2026-09-25. Companion memory:
`spelling_variant_removal.md`. Only remaining: the user decides on the
commit (main; push separately). Optional follow-ups: ngram extract-additions,
R2/doublet machinery removal (TODO.md notes them).

## Final AFTER-metrics vs baseline (`scratch/before-variant-removal-md5s.txt`)
- reform doublet (R2): 28 → **0** (goal). crossLemma: 0 → 0.
  sameLemmeGramCat: 104 → 104 (6 unreachable, unchanged).
- ambiguity: clusters 6,707 → 6,551; overflow 8.32% → 8.31%.
- Rows: Mixte 136,456 → 136,202; Synthetic 46,020 → 46,022
  (prune −192, S2 convergence +verb-form rows); phonetic theory 78,647 →
  78,622; disambiguated 186,740 → 186,298; Plover 168,005 → 167,621 entries.
- Full pipeline `python dictionary.py` OK (671.9 s, scratch/variant-full-
  rebuild2.log); S2 converged in 2 rounds (no loop). pytest 628 green;
  mypy: pre-existing errors only.
- Docs updated: CLAUDE.md (diagnostics block, S1 row count, pitfalls),
  docs/PIPELINE.md (rebuild table steps 1/1b/2 trigger list, S1 call graph,
  dataset counts, S3.2.1 choke-point description, recompute checklist),
  TODO.md (item marked DONE with follow-ups).
- Changed tracked files: lexique.py, dictionary.py, src/spellingvariants.py,
  util/prune_spelling_variants.py, resources/reform1990.tsv,
  resources/spellingVariants.tsv (new), resources/LexiqueGoogleNgram.tsv
  (new), resources/LexiqueMixte.tsv, resources/LexiqueSynthetic.tsv, the
  rebuilt outputs (theory/JSONs/trainer data), CLAUDE.md, TODO.md,
  docs/PIPELINE.md, .gitignore, src/test/spellingvariants_test.py.
  scratch/ tooling: apply_review_decisions.py, reprint_batches.py,
  validate_drops.py, verify_variant_removal.py, review-batches.txt,
  review-decisions.txt.

### The kept-verb ortho exemption (found via an S2 convergence loop)
The first full rebuild looped forever: completeVerbParadigms regenerated
`boite` (subjonctif of kept verb boiter) and `fritte` (of fritter) every
round because those spellings are dropOrthos (noun variants of boîte/frite)
and hook C made the appended rows invisible. The context-free ortho-drop
had also eaten a NATIVE Mixte verb row (boiter 16→15 rows). A first fix
(blanket "VER rows with kept lemme are exempt") was too broad: it broke the
restore for verb paradigms whose REWRITTEN form is the dropped side
(absous→absout, asseoir→assoir, boursouffler, interpeler, persiffler,
rassoir, sursoir, trompéter all leaked into Mixte run 2). A second fix
(native-VER exemption keyed on pre==post) still leaked NATIVE
same-paradigm variants (absout under lemme absoudre). FINAL rule (628
tests green): `isDroppedOrthoRow(ortho, lemme, gramCat, rewritten)` —
1. lemme dropped → drop; 2. spelling produced by the rewrite chain
(pre != post) → drop unconditionally (drives the restore to the canonical);
3. native VER row → drop IFF the lemme carries the set's canonical
(absoudre carries absous → drops; boiter doesn't carry boîte → exempt);
4. otherwise (NOM/ADJ native) → drop. Carriers are corpus-derived:
SpellingVariantDrops gained `dropOrthoCanonicals` (loader) and
`canonicalCarriers` + `withCanonicalCarriers()` (runtime, from a pre-pass:
lexique.py outputMixedLexique over self.words; dictionary.py readCorpus
over its sources; the pruner over LexiqueMixte.tsv). Without carriers the
exemption defaults to permissive (keep). LexiqueSynthetic.tsv reverted to
HEAD and pruned clean (46,209 → 46,017: 192 by lemme, 0 by ortho).

## DONE this session (all tests green: 625 passed; mypy: 7 pre-existing errors only)

1. **Review gate CLEARED** (the 209 review rows, ruled in 14 batches of 15):
   - Final TSV state: **374 active / 48 veto / 0 review**.
   - Rulings recorded in `scratch/review-decisions.txt` (row numbers refer to
     `scratch/review-batches.txt` order). Applied by
     `scratch/apply_review_decisions.py`; reprints via
     `scratch/reprint_batches.py N M`.
   - User's standing rules: "as suggested" = left column becomes canonical,
     right column dropped; veto rows keep both; **reform pairs: the rectified
     spelling is canonical** (display swap `*` in batches; recorded per-row).
   - Notable overrides: beluga (not béluga), carre+drop care, dessouler,
     oignon + oignonière (old side! reconcile-back), drop-bale, drop-mary,
     drop-parr, griffton set → canonical griffon (both misspellings dropped),
     gale/galle → veto (keep both), gangréneux/gangréneuse → veto (masc/fem
     forms), **saoul family → reformed soul/souler/soulard/soulerie**.
2. **reform1990.tsv extended** for the saoul family (single-char edits only,
   the loader enforces this): soûlard→soulard, soûler→souler,
   soûlerie→soulerie (circonflexe); saoul→soul, saoulard→soulard,
   saouler→souler, saoulerie→soulerie, dessaouler→dessouler
   (autres_rectifications). Existing: soûl→soul, dessoûler→dessouler.
3. **Hooks implemented** (the three from the plan + two extra necessities):
   - `src/spellingvariants.py`: `SpellingVariantDrops` gained `canonicals` +
     `reconcileLemme(raw, normalized)` (normalized kept → normalized; dropped
     but raw is canonical → raw, suppressing the reform normalization;
     otherwise None → drop row).
   - lexique.py `read_corpus`: lemme via `variantDrops.reconcileLemme`;
     None → skip row. Module-level `variantDrops` next to `ignoredList`.
   - lexique.py `outputMixedLexique`: `reconcileOutputOrtho(word.ortho,
     orthoOut, …)` after the WHOLE rewrite chain; None → skip row; fallback →
     restore `word.ortho`/`writeOrthoSyll()` snapshot.
   - lexique.py `breakdownSyllables`: guard `item in self.words_by_ortho`
     (dropped words caused KeyError 'abatage').
   - dictionary.py `readCorpus`: skip dropped lemme OR ortho (choke point).
   - lexique.py rewrite table: values now `tuple[OrthoRewriteRule, …]`
     (multi-rule keys for doublet spellings) and deletion rules are keyed
     under newSpelling too when guarded (`newSpelling[position] != oldChar`)
     — needed so `saoulera`→`soulera` is reachable via lemme `souler`.
4. **5 carrier conflicts fixed** in the TSV (canonical rode on a dropped
   lemme): imprésario, média, phylloxéra, sottie, vélum — carrying lemme
   cleared from dropLemmes (kept in dropOrthos). Detector:
   `scratch/validate_drops.py` (0 conflicts now).
5. **S1 rebuilt and VERIFIED** (`scratch/variant-s1-rebuild.log`):
   LexiqueMixte.tsv 136,457 → 136,202 rows. All spot-checks green
   (`scratch/verify_variant_removal.py`): no dropped spelling leaks; oignon/
   événement/beluga/carre/dessouler/soul-family/sottie/imprésario/vélum
   present; bale/mary/abatage/appas/trimbaler/zyeuter/maffia gone; vetoes
   (tâche/tache, sur/sûr, gale/galle, colon/côlon, fût/fut) untouched.
   saoul paradigm unified under lemme souler (32 rows verb, 8 soul ADJ/NOM,
   6 soulard, 3 soulerie).
6. **Synthetic pruned** (after the exemption fix): 46,209 → 46,017 rows
   (192 by lemme, 0 by ortho). Pickles deleted. After the S1 rerun:
   `python dictionary.py` full rebuild (log ~10 min per past timings).

## NEXT after the rebuild finishes

1. AFTER-metrics vs baseline `scratch/before-variant-removal-md5s.txt`
   (Mixte 136,457/Synthetic 46,210/theory md5s; Plover 168,005 entries):
   - `python -m util.build_disambiguated_theory` report: reformDoublet 28 →
     **0** expected; crossLemma stays 0; sameLemmeGramCat 104 drops by the
     variant share.
   - `python -m src.ambiguitychecker` (baseline clusters 6,707 / overflow
     8.32%); `scratch/b44_probe.py`, `scratch/b44_residuals.py` (baseline 6
     unreachable spellings).
   - `pytest src/test/` green.
2. `python -m util.ngram_data extract-additions` (calibrate --threshold on
   the distribution first) → `resources/LexiqueGoogleNgramAdditions.tsv`.
3. Docs: CLAUDE.md diagnostics block (ngram_data, build_spelling_variants,
   prune_spelling_variants); docs/PIPELINE.md (S1 filtering + reconcile-back
   rule, rebuild checklist, reform1990 saoul rows); TODO.md:290-300 resolved
   + follow-ups ("R2/doublet machinery removal", "neologism patch").
   Update memory `spelling_variant_removal.md`.
4. Commit on main (user commits directly; push only on request). THEN the
   user may `purge` the ngram shards.

## GOTCHAS learned this session

- `pgrep -f 'python lexique.py'` self-matches wait-loop shells — match the
  real python with `ps aux | grep lexique | grep -v grep`.
- `import lexique` RUNS the whole S1 (module-level pipeline at the bottom).
- S1 takes ~25 min wall; full dictionary.py ~10 min.
- The reform ortho-rewrite table enforces SINGLE-character edits
  (computeSingleEditRule); saoul→soul is a deletion and passes.
- Deletion rules keyed under newSpelling are unsafe for doubled-letter
  pairs (grolle→grole would re-delete); the new guarded condition avoids it.
- Sets whose canonical is only produced by the ortho rewrite must NOT drop
  the carrying lemme (the 5 carrier fixes; CARRIER check in
  scratch/validate_drops.py).
- Canonical on the OLD side of a lemme-normalizing pair (oignon) needs
  reconcileLemme, not just reconcileOutputOrtho.
- Prior session gotchas (v3 shards, recentIdx, setId ordering, grep -P for
  accents, proper-noun contamination, isException never merged) still apply.
