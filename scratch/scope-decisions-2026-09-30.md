# Growth scopes decided for the 30 affix rules (H sweep, flag on, no growth for `re-`), 2026-09-30

Rank = row of `scratch/rules-table-H-nogrowth.md`. Form cost assumed about 100 per form (user), fallback price 5 per word. "Anchor" = the k=1 form on the rule's own keys; a growth
form fuses the anchor with the neighbour syllable (before a suffix, after a prefix) when the neighbour matches the scope. Scopes are matched on the neighbour's SOUND (X-SAMPA, C = a consonant
phoneme, V = a vowel) except rank 1 (spelling). Details, numbers and scripts per rank: `RESUME_2026-09-30-ment-regex-scope.md`.

| # | anchor | keys | growth scope (user's decision) |
|---|---|---|---|
| 1 | `-ment` | 20,21,25 | syllable before: `C{1,2}[eui]+` (spelling), fallback price 5 |
| 2 | `re/reh` | 9,18 | none (anchor alone; meaning-carrying prefix) |
| 3 | `en` | 2,16,18 | next syllable `C{1,2}@` (consonant(s) + nasal vowel): entendre, engendrer, enfantine |
| 4 | `de/des/dé/déh` | 11,16,18 | none |
| 5 | `de` (schwa) | 16,19 | next syllable `man` or `ve` (demander, devenir) |
| 6 | `-tion` | 9,20,25 | syllable before: `C*[ai]` (-ation, -ition); no 3-syllable form, no ten/ven |
| 7 | `ain/hin/im/in` | 9,19 | `in` + `té` (intérêt) |
| 8 | `é` | 2,5 | none |
| 9 | `-ter` | 16,20,22 | none |
| 10 | `-té` | 19,20,25 | syllable before: `C\{bv}{1,2}i` (-ité without b, v) |
| 11 | `au` | 2,5,8 | next syllable `jour`, `to`, `tre` or `di` (aujourd'hui, auto-, autre-, audition) |
| 12 | `pa` | 2,5,18 | none (no growth form) |
| 13 | `-cer/-cé/-sé…` | 16,17,19 | `cé` forms: syllable before `m@` (commencé) |
| 14 | `par` | 8,19 | none (no growth form) |
| 15 | `ai/aî/e/ei/hai/he/hê/é` | 5,18,19 | spelling `e`: next syllable `ksky`, `kspli`, `sE` or `n°` (excuser, expliquer, essayer, ennemi); no `ai` growth |
| 16 | `-der` | 16,19,25 | `dez` forms: syllable before `gaR` or `m@` (regardez, demandez) |
| 17 | `ra/rai/raie/re/rhé/ré/réh` | 3,4,16 | spelling `ré`: next syllable `a`, `fle`, `vE` or `C{1,2}y` (réalité, réfléchir, réveiller, réduire) |
| 18 | `sa/sah` | 5,24 | none (no growth form) |
| 19 | `-ver` | 19,20,22 | `vé` forms: syllable before `Ri` (arrivé, dérivé) |
| 20 | `pro/proh/prô` | 4,5,8 | none (no growth form) |
| 21 | `ce/sce/se` | 3,6 | none (no growth form) |
| 22 | `pou/pu` | 4,7,18 | none (no growth form) |
| 23 | `ser/sée/zer/zé` | 16,19,20 | two k=2 forms: syllable before `li` (-liser, -lisé) and, for `sez`, `Cy` before it (excusez, refusez) |
| 24 | `de/dea/di/die/dis/dy/dî` | 3,16,19 | spelling `di`: next syllable `C{1,2}i` |
| 25 | `e/hi/hy/i/y/î` | 16,17,19 | spelling `i`: next syllable `[mn][aeiouy]` (imagine, inutile, innocent) |
| 26 | `rae/rai/raie/re/rer/rez/rrer/rrhée/rrée/rée` | 16,20,21 | `rer` forms: syllable before `p[aeiouy]`, `C*e` or `sy` |
| 27 | `o` | 16,18,19 | next syllable `C{1,2}i` or `kV` |
| 28 | `ger` | 16,24 | none (no growth form) |
| 29 | `-ner` | 18,19,20 | `né` forms: syllable before `C{1,2}[i°]` |
| 30 | `cher` | 9,24,25 | none (no growth form) |

Open before wiring into the engine (option C): (a) one COMBINED simulation of all the scopes (every scorer so far evaluated each rule alone; the sweep scores a rule after the earlier ones,
so cross-rule collisions are not in my numbers); (b) engine support for phonology/spelling scopes, literals and exclusions; (c) rules whose keys moved (2: (9,18), 7: (9,19)); (d) the lexicon
oddity `ra`+`Re` (TODO.md).
