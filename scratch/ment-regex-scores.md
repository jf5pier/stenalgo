# -ment regex scope scores (real simulator, keys (20, 21, 25))

2724 carriers whose last syllable is `ment`. `k2 words` = words given the 2-stroke form;
`gain>0 k2` = of those, how many really gain (rest fall back). Exceptions = collision fallbacks.

| scope | k2 words | gain>0 k2 | covered | benefit | exc words | exc freq | score | d score vs list |
|---|---|---|---|---|---|---|---|---|
| BASELINE enumerated list (100 syllables) | 2623 | 2552 | 2646 | 7817 | 71 | 417.2 | 7390 | +0 |
| no k=2 form (ment alone) | 0 | 0 | 2717 | 4758 | 7 | 28.6 | 4729 | -2661 |
| user A: (C+[eiuéû]+)? | 2562 | 2482 | 2637 | 7745 | 71 | 414.8 | 7321 | -70 |
| user B: (C+[eiu]+)? | 2481 | 2444 | 2676 | 8400 | 42 | 64.4 | 8325 | +935 |
| C+[eiuéû]  (single vowel) | 2322 | 2246 | 2641 | 7660 | 69 | 400.8 | 7249 | -141 |
| C+[eiu]    (single vowel) | 2243 | 2210 | 2684 | 8319 | 34 | 46.5 | 8262 | +872 |
| C*[eiuéû]+ (onset optional) | 2564 | 2484 | 2637 | 7745 | 71 | 414.8 | 7321 | -70 |
| C+[eiuéûa]+ | 2589 | 2494 | 2622 | 7787 | 79 | 416.0 | 7361 | -29 |
| C+[eiuéûaé]+ + oie/ie | 2626 | 2525 | 2616 | 7785 | 82 | 417.8 | 7357 | -33 |
| C+ + any vowel letters | 2652 | 2526 | 2591 | 7329 | 99 | 431.9 | 6887 | -503 |
| anything (upper bound) | 2724 | 2569 | 2569 | 7266 | 103 | 438.3 | 6818 | -572 |

Top exceptions per scope:
- BASELINE enumerated list (100 syllables): seulement, bâtiment, serment, éléments, élément, sacrément
- no k=2 form (ment alone): serment, tourments, serments, tourment, sarment, blèsement
- user A: (C+[eiuéû]+)?: seulement, serment, rarement, éléments, élément, compliments
- user B: (C+[eiu]+)?: serment, rarement, bêtement, tourments, serments, tourment
- C+[eiuéû]  (single vowel): seulement, serment, éléments, élément, compliments, compliment
- C+[eiu]    (single vowel): serment, bêtement, tourments, serments, tourment, sagement
- C*[eiuéû]+ (onset optional): seulement, serment, rarement, éléments, élément, compliments
- C+[eiuéûa]+: seulement, serment, rarement, éléments, élément, compliments
- C+[eiuéûaé]+ + oie/ie: seulement, serment, rarement, éléments, élément, compliments
- C+ + any vowel letters: seulement, serment, rarement, éléments, élément, compliments
- anything (upper bound): seulement, bâtiment, rarement, éléments, élément, compliments
