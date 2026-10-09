> **Status 2026-10-01: HISTORICAL.** Kept for its reasoning. The current description is `docs/AFFIX_RULES.md`; the state is `RESUME_2026-10-01-option-c-engine.md`; the next phase (pipeline integration) is `PLAN_2026-10-01-affix-pipeline-integration.md`.

> **Superseded 2026-09-29 (evening) by `RESUME_2026-09-29-affix-partial-overlap-flag.md`** — Steps 1-2 below are done; read that file first.

# Resume: affix rules, after the `-ption` lexicon fix (written 2026-09-29)

Branch `affix-abbreviation-rules` (last commit = "Single-generator affix rewrite + OQLF/TAO
reference comparison"). Work paused here to fix lexicon data on `main`, then return.

## Where things stand
- Single-generator rewrite done and tested (711 tests). Read, in order:
  `FINDINGS_2026-09-28-affix-single-generator.md` (§6-7 = reference diff + open questions),
  `PLAN_2026-09-28-affix-single-generator-rewrite.md`.
- References (local copies + standing practice) in `resources/reference/README.md`. After every
  selection change rerun `env/bin/python scratch/affix_reference_diff.py > scratch/affix-reference-diff.md`
  (reads `scratch/affix-candidates.tsv` and `scratch/affix-sweep/{L,M,H}/affix-rules.tsv`; the
  big pickles/logs in `scratch/` are untracked and regenerable via `python -m util.affix_scan`).
- Nothing about the theory/Plover output changed by this branch.

## Step 1 (on `main`): data fix -- DONE 2026-09-29 (`-ption` 9f871e7, `-ction` 27668cf; pushed)
Resyllabify the 5 wrong `-ption` lemmas (`absorption(s)`, `réabsorption`, `résorption(s)`):
`p_s_j_§` -> `p|s_j_§` in `resources/LexiqueMixte.tsv` (see TODO.md, commit 525414f; source is
Lexique383 syllable columns, so fix at the S1 origin, `lexique.py`, not by hand-editing the TSV).
Then `rm -f *.pickle` and rebuild per `docs/PIPELINE.md`; check md5 changes are limited to those
lemmas. The 5 `-ction` lemmas with an x were fixed too (`fix_x_k_s`, 27668cf); `-xion`/`-xtion` deliberately left. `-th` still unchecked.

## Step 2 (back on this branch)
Integration of `main` into this branch is deliberately deferred (user: not ready). Until then the
branch still has the OLD lexicon (stray `psj§ ption` and `ksj§ ction` anchors). Decide how to get
the fixed lexicon here before rerunning anything.
1. Rerun the affix scan (`util/affix_scan.py`, L/M/H sweep) and the reference diff; confirm the
   stray `psj§ ption` anchor is gone and `tion`'s carriers grew.
2. Decide whether the remaining cluster cases (`ksj§` -xion/-xtion ~23 words, `tj§` -stion = question/digestion; `ksj§ ction` was a data bug, fixed)
   justify the generator change below.

## Idea, not started: cluster-onset fusion
Extend `buildVariantMerges` (`src/affixes.py`, U3a, runs before `inheritAndStat` and growth) to
group by (position, nucleus+coda) instead of (position, whole phono), letting onsets differ
(`sj§|psj§|ksj§|tj§`), with the same 2% new-conflict test in both places (pre-merge and the
authoritative post-inheritance test in `buildCandidates`). `resolveVariantRivals` in
`affixrules.py` already settles merged-vs-parts through `mergeParts`, no change expected there.
Open: same-onset-consonant-added only, or also consonant-changed (`tj§` vs `sj§`, teaches a
different sound)? Needs full rebuild + md5 comparison.

## Open questions from FINDINGS §7 (user decisions pending)
1. L/M/H weight setting (not comparable on credited saving alone).
2. Pseudo-affixes (`der`, `er`, `nir`, `voir`, `in`, `ve`): proposal = test an attestedShare
   weight or reserve slots for OQLF-attested affixes (-able, -age, -iste, -ique, trans-...).
3. Multi-syllable affixes (anti-, inter-, multi-, semi-, -eur, -able, -cation, -vité/-cité) are
   structurally ineligible as roots (only grown nodes): proposal = curated multi-syllable
   anchor list seeded from OQLF + TAO.
4. Still unanswered: is the affix key added to an existing stroke or a stroke of its own?
   (check `src/affixbinding.py` and the binding report).

## Untracked files deliberately not committed
`birds.md`, `RESUME_2026-09-25-spelling-variant-removal.md`, `steno-trainer/user*.json`,
`scratch/` pickles and logs.

## Update 2026-09-29 (evening): speedup done, cluster-onset fusion measured
- Sweep speedup committed (e31e6a7, 5068501): full sweep 669 s instead of ~5,200 s, rule tables
  byte-identical. See `PLAN_2026-09-29-affix-scan-speedup.md`. Stray `psj§ ption` / `ksj§ ction`
  anchors are gone; `tion` 2,355 -> 2,365 carriers.
- Cluster-onset fusion scope (`scratch/cluster_fusion_scope.py`, `scratch/same_ortho_scope.py`):
  * Strict "consonant added to the onset" (sj§ + psj§/ksj§): 10 suffix pairs, total freq 167
    (`xion` 14.8 vs `tion` 3,447 = 0.4%; the rest, llon/illon/breux, are not real variants);
    prefixes 10 pairs / 166, and they would wrongly fuse distinct affixes (cre/re, pres/res).
    NOT worth a generator change.
  * Same SPELLING, different onset (voicing / sound alternations): 30 pairs, total freq 1,912:
    -ser z/s 718, -tion sj/tj 434 (question, gestion), -sion zj/sj 130, -ller j/l 116, -sé 99,
    -son 91, -sible 46 ... A spelling-keyed merge (group by position+ortho+nucleus/coda, onsets
    differ) is simple and human-checkable ("the spelling decides the key"), but it needs a
    merged-node identity (phono label like `sj§|tj§`) and a 2% conflict test as today.
    Modest gain (~1.9k freq vs top rules at 3-9k): decision pending.
