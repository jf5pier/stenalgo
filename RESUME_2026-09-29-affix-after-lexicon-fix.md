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

## Step 1 (on `main`): data fix
Resyllabify the 5 wrong `-ption` lemmas (`absorption(s)`, `réabsorption`, `résorption(s)`):
`p_s_j_§` -> `p|s_j_§` in `resources/LexiqueMixte.tsv` (see TODO.md, commit 3de3273; source is
Lexique383 syllable columns, so fix at the S1 origin, `lexique.py`, not by hand-editing the TSV).
Then `rm -f *.pickle` and rebuild per `docs/PIPELINE.md`; check md5 changes are limited to those
lemmas. Also check `ction` (`ksj§`, 5 carriers) and `-th` for the same artefact.

## Step 2 (back on this branch)
1. `git merge main` (or rebase) to pick up the fixed lexicon.
2. Rerun the affix scan (`util/affix_scan.py`, L/M/H sweep) and the reference diff; confirm the
   stray `psj§ ption` anchor is gone and `tion`'s carriers grew.
3. Decide whether the remaining cluster cases (`ksj§ ction`, `tj§ tion` = question/suggestion)
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
