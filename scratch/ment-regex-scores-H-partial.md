# -ment regex scope scores (real simulator, keys (20, 21, 25), setting H, partial overlap True)

2724 carriers whose last syllable is `ment`. `k2 words` = words given the 2-stroke form;
`gain>0 k2` = of those, how many really gain (rest fall back). Exceptions = collision fallbacks.

| scope | k2 words | kept as k2 | fallbacks (words) | fallbacks (freq) | benefit | hard exc | score, fallback free | score, fallback 150 each |
|---|---|---|---|---|---|---|---|---|
| BASELINE enumerated list (100 syllables) | 2623 | 2518 | 105 | 481 | 8525 | 3 | 8213 | -7537 |
| no k=2 form (ment alone) | 0 | 0 | 0 | 0 | 4787 | 1 | 4787 | 4787 |
| user A: (C+[eiuéû]+)? | 2562 | 2456 | 104 | 426 | 8544 | 9 | 8224 | -7376 |
| user B: (C+[eiu]+)? | 2481 | 2403 | 78 | 85 | 8723 | 3 | 8412 | -3288 |
| C+[eiuéû]  (single vowel) | 2322 | 2224 | 98 | 411 | 8434 | 3 | 8122 | -6578 |
| C+[eiu]    (single vowel) | 2243 | 2171 | 72 | 71 | 8609 | 3 | 8298 | -2502 |
| C*[eiuéû]+ (onset optional) | 2564 | 2458 | 104 | 426 | 8544 | 9 | 8224 | -7376 |
| C+[eiuéûa]+ | 2589 | 2468 | 121 | 446 | 8606 | 3 | 8294 | -9856 |
| C+[eiuéûaé]+ + oie/ie | 2626 | 2481 | 145 | 515 | 8524 | 3 | 8212 | -13538 |
| C+ + any vowel letters | 2652 | 2482 | 170 | 963 | 8516 | 3 | 8204 | -17296 |
| anything (upper bound) | 2724 | 2525 | 199 | 1032 | 8494 | 3 | 8182 | -21668 |

Most frequent excluded words (named by the pattern, fall back to plain `ment`) per scope:
- BASELINE enumerated list (100 syllables): seulement, vêtements, bâtiment, éléments, élément, sacrément, largement, ciment
- no k=2 form (ment alone): -
- user A: (C+[eiuéû]+)?: seulement, rarement, éléments, élément, compliments, compliment, sacrément, largement
- user B: (C+[eiu]+)?: rarement, largement, jument, ciment, argument, parlement, bêtement, arguments
- C+[eiuéû]  (single vowel): seulement, éléments, élément, compliments, compliment, sacrément, largement, jument
- C+[eiu]    (single vowel): largement, jument, ciment, argument, parlement, bêtement, arguments, aliments
- C*[eiuéû]+ (onset optional): seulement, rarement, éléments, élément, compliments, compliment, sacrément, largement
- C+[eiuéûa]+: seulement, rarement, éléments, élément, compliments, compliment, sacrément, largement
- C+[eiuéûaé]+ + oie/ie: seulement, vêtements, rarement, éléments, élément, compliments, compliment, sacrément
- C+ + any vowel letters: moment, seulement, vêtements, moments, rarement, éléments, élément, compliments
- anything (upper bound): moment, seulement, vêtements, moments, bâtiment, serment, rarement, éléments
