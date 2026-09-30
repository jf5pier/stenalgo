# OQLF cross-check of the family-unification merges (2026-09-27)

Cross-checks every `unifyFamilies` merge in the post-A7 run
(`scratch/affix-bindings-report.md`, `scratch/affix-merges.tsv`: 71 accepted merges) against the
[OQLF prefix/suffix table](https://www.oqlf.gouv.qc.ca/prix-concours/creativite-lexicale/contenu-pedagogique/tableau-prefixes-suffixes.aspx)
(`PLAN_2026-09-26-affix-abbreviations.md` §11) -- does each merged family's member list correspond
to one (or a few related) named, meaningful affix(es), or is it phonological coincidence riding
on `unifyFamilies`'s aggregate salient-phoneme cosine?

36 of the 71 accepted merges combine families whose `familyId` already had a `+` in it (i.e. at
least one side was itself already a merge); those chained results are listed below by their
current (post-chain) member list.

Verdict legend: **good** = the union backs one/a few coherent named affixes (including A7-style
consonant-variant spelling groups, e.g. `-ité` after different stem-final consonants); **mixed**
= a real affix polluted by unrelated riders; **none** = no member corresponds to a named affix at
all (pure phonological syllable pooling).

| family | members | verdict | note |
|---|---|---|---|
| S001+S010 | ment, °ment, Etement, 2sement, ablement, Ellement, Erement, alement, Enement, iquement | **good** | all `-ment` (manner) |
| S004+S022 | tion, ssion, sion, isation, itation, ication, ination, osition | **good** | all `-ion` (action/result) |
| S005+S075+S080 | ation, ission, cial, cien, icien, tiel, tien, lien, ciel, @tiel | **mixed** | `-ation`/`-ission` (`-ion`) OK; `-cien/-icien` is really `-ien` (origin/practitioner); `cial/ciel/tiel/tien` are a *different* adjective suffix (`-el`/`-al`-ish); `lien` is the word "lien", not a suffix |
| P006+P062+P119+P125 | com, con, ca, cu, cam, cons | **mixed** | `com-`/`con-` = real `co-` (together); `ca`/`cu` are bare stem syllables |
| S007+S030+S118 | ner, nant, onner, nner, née, oser, onnier, né, no, net | **none** | verb-conjugation fragments (`-ner`/`-nant`), not a semantic suffix |
| S016+S044+S096 | ger, gie, age, gé, tage, rage, gent, onnage, vage, mage | **mixed** | `-age` (action/result) present; `ger/gé/gent` are `-ger` verb endings, unrelated |
| P014+P067+P052 | se, es, su, sé, ce, sen, esa, eso, cen, cé | **none** | common word-initial syllables, no OQLF prefix |
| S006+S064+S128 | ler, lé, lot, let, ller, lon, lo, lant, lent, lin | **none** | `-ler` verb-ending fragments |
| S019+S101+S119+S043 | teur, toire, ateur, taire, atoire, loir, isateur, mètre, mettre, itaire | **mixed** | `-teur`/`-ateur`/`-isateur` = real `-eur` (performer); `mètre`/`mettre` are unrelated words riding along |
| S015+S082 | ci, cile, cin, ssin, cide, tie, cine, cis | **none** | fragments, no single named affix |
| P031+P103+P035 | main, man, mé, men, mo, mor, me | **mixed** | `mé-` is real (badly); `main/man/mo/mor/me` are bare syllables |
| S033+S085+S048 | rie, °rie, ri, sir, ro, soir, ir, reau, ssir | **mixed** | `-erie` (state/activity/place) real; `sir/soir/reau` unrelated |
| P026+P085+P111+P131 | ja, je, jo, gé, ge, ju | **none** | no OQLF prefix |
| P025+P079 | trou, tra, trans, tran, trom, trahi, tri, bran | **mixed** | `trans-` real (across); `trou/trom/tri/bran` unrelated |
| P015+P072 | ma, mou, maa, mea, mous | **none** | no OQLF prefix |
| S026+S074 | tique, icain, fique, cain, nique, gique, lique, mique, sque, rique | **mixed** | `-tique/-fique/-nique/-gique/-lique/-mique/-rique` = coherent `-ique` (relating to) consonant family, A7-style, good; but `icain/cain` = `-ain` (origin, different meaning) and `sque` = `-esque` also ride along |
| S023+S124 | ture, tude, ature, iture, itude, tu | **good/minor** | `-ure` and `-tude` are both real "state/result" suffixes (traditionally distinct but semantically close); `tu` is a bare fragment |
| P040+P059 | be, bou, bou°, ban, bé | **none** | no OQLF prefix |
| P039+P056+P098+P132 | fa, fai, féi, fi, phoo, fo, fê, fau, fé, fen | **none** | no OQLF prefix |
| S038+S102+S109+S079 | ilité, alité, aliste, lette, icité, rette, tuel, tel, quette, nnette | **mixed (worst)** | `-ité`/`-iste` real and internally coherent (A7-style); but `-ette` (diminutive) and `-el`/`-uel` (relating-to) are unrelated suffixes pooled in -- same failure pattern as the original `-cier`/`-ion` report |
| S025+S065 | iser, sin, sé, sine, sant, sie, isan | **none** | fragments |
| P038+P082 | pa, pu | **none** | no OQLF prefix (tiny family, low stakes) |
| S053+S069+S081+S112 | tout, to, teau, tin, tain, tat, ta | **none** | fragments |
| S050+S068+S088 | Essant, ssant, ssance, rence, erence, rance, lence, science, issant, gence | **good** | `-ant`/`-ance`/`-ence` family, coherent (participle + abstract-noun) |
| S036+S056 | table, able, ssible, rable, tile, sable, onnable, dable, ORtable, erable | **good** | `-able`/`-ible` (able to be), A7-style consonant family; `tile` (`-ile`) is a minor rider |
| S039+S057 | lleur, rieur, sseur, reur, seur, geur, illir, ceur, queur | **good** | `-eur`/`-euse` (performer), A7-style consonant family; `illir` (`-llir` verb ending) is a minor rider |
| P051+P101 | vi, véi, va | **none** | no OQLF prefix |
| P048+P116 | cai, sai, pai, ac, cani | **none** | no OQLF prefix |
| S047+S122 | tal, ral, @tal, lat, tral, la | **good/minor** | `-al` (relating to; not in the short OQLF list but a very common, real French adjective suffix), A7-style consonant family; `la` is a bare fragment |
| S061+S104 | dre, duire, deur, rade, nade, daire | **none** | verb endings (`-uire`/`-dre`) mixed with noun endings (`-ade`/`-aire`), no common meaning |
| S084+S093 | du, dat, @du, nat | **mixed** | `-at` (state/function, e.g. syndicat) real but thin; `du`/`@du` unrelated |
| P088+P089 | la, cal, mal, al, loa | **mixed** | `mal-` is a real quasi-prefix (badly, parallels `mé-`); `la/cal/al/loa` unrelated |
| P102+P137 | ga, gué | **none** | no OQLF prefix (tiny family) |
| P118+P129+P123 | na, no, ni | **none** | no OQLF prefix |
| S116+S121 | ra, card, pard | **mixed** | `-ard` (performer/quality) real, A7-style (`card`/`pard`); `ra` alone unrelated |
| P124+P139 | bi, bu | **none** | no OQLF prefix (tiny family) |

## Summary

- **7 good**: `-ment`, `-ion`, `-ant/-ance/-ence`, `-able/-ible`, `-eur/-euse`, `-ure/-tude`,
  `-al` -- coherent, A7-style consonant-variant families or straightforward OQLF matches. Keep.
- **~13 mixed**: a real, named affix (`co-`, `mé-`, `mal-`, `-erie`, `-eur`, `-ique`, `-ité`,
  `-iste`, `-ard`, `-at`, `trans-`, `-age`, `-ien`) with one or more unrelated riders pooled in by
  `unifyFamilies`'s aggregate cosine similarity. **S038+S102+S109+S079** (`-ité`/`-iste` polluted
  by `-ette`/`-el`/`-uel`) is the worst instance and structurally identical to the original
  `-cier`/`-ion` report finding.
- **~16 none**: no member maps to any OQLF-named prefix at all. Pattern: almost all are
  **prefixes**, and specifically short (k=1-2) common word-initial syllables (`se-/es-/su-`,
  `ja-/je-/jo-`, `ma-/mou-`, `be-/bou-`, `fa-/fi-/fo-`, `pa-/pu-`, `vi-/va-`, `cai-/sai-/pai-`,
  `ga-/gué`, `na-/no-/ni-`, `bi-/bu-`). These aren't semantic prefixes being pooled -- they were
  never one to begin with (Plan A2d's "loose morphological filter" already flagged `a-`
  (avoir/voir) as the same failure mode). `unifyFamilies` doesn't introduce this problem, it just
  compounds already-loose individual families into bigger loose ones.

## Root cause and fix

`unifyFamilies`'s merge gate (`src/affixbinding.py`) checks the cosine of the two families'
**aggregate** salient-phoneme weight vectors (`MERGE_SIM_MIN = 0.75`) plus the union's overall
gain and `sim`. Nothing checks that each **individual member** is actually similar to a member of
the other side -- so a family with an internally strong shared phoneme profile can absorb an
outlier member whose only connection is a shared consonant/vowel that also happens to dominate the
aggregate profile. This is exactly the failure the resume already named for `-cier`/`-ion`.

First attempt (implemented, then reverted after validation): a hard per-member similarity floor
using A3's own `candidateSim` (string + phoneme Levenshtein) -- reject a merge unless every member
of each family is at least `FAMILY_LINK_SIM`-similar to some member of the other family. Validated
against real family data (`scratch/affix-families.pickle` from this session's rerun):

- It correctly rejects every pair in the two worst chains above (`S005`/`S075`/`S080` and
  `S038`/`S102`/`S109`/`S079`) -- every pairwise combination fails the floor, matching the manual
  "mixed"/"none" verdicts.
- But it ALSO rejects clearly good merges: `S001`+`S010` (`-ment`), `S004`+`S022` (`-tion`/
  `-isation`), `S036`+`S056` (`-able`/`-ible`), `S039`+`S057` (`-eur`), `S050`+`S068`
  (`-ant`/`-ance`/`-ence`) -- all failed the blanket floor too. Root cause: length-normalized
  Levenshtein punishes a short affix (`tion`, k=1) against a longer elaboration of the *same*
  affix (`isation`, k=2) even though `isation` literally ends in `tion` -- the exact case A3's own
  `_nested()` helper exists to rescue, but only within a 3-extra-letter cap (`NESTED_MAX_EXTRA_LETTERS`)
  too tight for `tion` -> `isation` (4 extra letters) or `ment` -> `ablement` (4 extra letters).

Per-member breakdown showed the fix's real strength: for `S039`+`S057`, only ONE member
(`illir`, a stray `-llir` verb ending) failed the floor -- everything else passed. A hard
family-level reject throws out the whole merge over one outlier; that's the wrong response.

**Shipped instead**: `orphanMembers(fa, fb)` (`src/affixbinding.py`) computes the same per-member
floor but as a **non-blocking diagnostic** -- every accepted (and rejected) merge in
`affix-merges.tsv` now has an `orphanMembers` column listing exactly which members have no
adequate match in the other family, for the user's manual review pass, instead of an automatic
gate that would silently reject good merges or need a much more sophisticated (unbounded nesting +
partial-prune) rule to do better. `pytest src/test/` = 672 pass (2 new tests in
`TestOrphanMembers`).
