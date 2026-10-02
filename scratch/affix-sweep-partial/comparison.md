# Weight sweep comparison (U6)

Credited saving = cumulative word-once-credited total from the selection curve (before the swap pass), in stroke-frequency units.

| setting | EXCEPTION_ALPHA | EXCLUSION_COST | FORM_COST | saving @20 | saving @30 | forms | exclusions | word exceptions | attestedShare<0.5 | max exception rate | max overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L | 1.0 | 5.0 | 10.0 | 56628 | 69287 | 100 | 20 | 826 | 13 | 4.9% | 0.00 |
| M | 1.0 | 50.0 | 100.0 | 60412 | 74952 | 85 | 17 | 905 | 14 | 4.7% | 0.00 |
| H | 2.0 | 150.0 | 300.0 | 79941 | 100787 | 60 | 5 | 976 | 11 | 4.1% | 0.09 |

## Rules selected in any setting, by rank

| rule | L | M | H |
|---|---|---|---|
| suffix `ment` | — | — | 1 |
| suffix `man|mand|mant|ment|ments|mmant|mment` | 1 | 1 | — |
| prefix `re` | — | — | 2 |
| suffix `ccion|cion|cyon|sion|ssion|tion|tions` | 2 | 2 | — |
| prefix `de` | 3 | 3 | 5 |
| prefix `en` | — | — | 3 |
| prefix `au` | — | 4 | 11 |
| prefix `in` | 4 | 5 | — |
| prefix `de|des|dé|déh` | — | — | 4 |
| prefix `e` | 5 | 7 | — |
| suffix `der` | 6 | 6 | 16 |
| prefix `ain|hin|im|in` | — | — | 6 |
| suffix `tion` | — | — | 7 |
| prefix `ré` | 7 | 9 | — |
| prefix `pro|proh|prô` | 8 | 13 | 20 |
| prefix `par` | — | 8 | 14 |
| prefix `é` | — | — | 8 |
| prefix `ce|sce|se` | 9 | 12 | 21 |
| suffix `ter` | — | — | 9 |
| suffix `sser` | — | 10 | — |
| prefix `pou` | 10 | — | — |
| suffix `té` | — | — | 10 |
| prefix `i` | — | 11 | — |
| prefix `im` | 11 | 16 | — |
| prefix `pa` | — | — | 12 |
| prefix `de|dea|di|die|dis|dy|dî` | 12 | 22 | 24 |
| suffix `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` | — | — | 13 |
| suffix `er` | 13 | 21 | — |
| prefix `pou|pu` | — | 14 | 22 |
| suffix `nir` | 14 | 23 | — |
| prefix `ai|aî|e|ei|hai|he|hê|é` | — | — | 15 |
| prefix `fa` | 15 | 24 | — |
| prefix `o` | — | 15 | 27 |
| prefix `ai` | 16 | 26 | — |
| prefix `per` | 17 | — | — |
| prefix `ra|rai|raie|re|rhé|ré|réh` | — | — | 17 |
| prefix `ra` | — | 17 | — |
| suffix `teur` | 18 | 28 | — |
| prefix `sa|sah` | — | 19 | 18 |
| prefix `pré` | — | 18 | — |
| suffix `ver` | — | — | 19 |
| prefix `ex` | 19 | — | — |
| suffix `cher` | — | 20 | 30 |
| suffix `voir` | 20 | 30 | — |
| prefix `em` | 21 | — | — |
| prefix `vou` | 22 | 29 | — |
| suffix `ser|sée|zer|zé` | — | — | 23 |
| suffix `ture` | 23 | — | — |
| prefix `ou` | 24 | — | — |
| prefix `e|hi|hy|i|y|î` | — | — | 25 |
| prefix `ve` | 25 | — | — |
| prefix `po` | — | 25 | — |
| suffix `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` | — | — | 26 |
| prefix `cou` | 26 | — | — |
| prefix `mi` | — | 27 | — |
| prefix `sou` | 27 | — | — |
| suffix `ger` | — | — | 28 |
| suffix `mi` | 28 | — | — |
| suffix `ner` | — | — | 29 |
| prefix `es` | 29 | — | — |
| prefix `trou` | 30 | — | — |

## Rules selected in every setting whose forms differ between settings

- prefix `pro|proh|prô`
    - L: pro|proh|prô, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·, profe[ne|sse|ssio|sso|tte|ttri]·, pro[chi|di|fi|i|li|phy|pi|vi]·
    - M: pro|proh|prô, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·
    - H: pro|proh|prô
- prefix `ce|sce|se`
    - L: ce|sce|se, se[con|cou|coue|crè|cré|cun|gue|mai|mes|mon|na|pen|rei|ri|rin|ven]·
    - M: ce|sce|se
    - H: ce|sce|se
- prefix `de|dea|di|die|dis|dy|dî`
    - L: de|dea|di|die|dis|dy|dî, di[a|cho|chro|dac|ffa|ffen|ffi|ffor|ffu|ges|gi|gne|gni|gé|jo|jonc|la|le|li|lu|mi|na|nan|nas|ne|no|o|plo|plô|rec|ri|scer|sci|sen|shar|sig|sle|slo|ssem|ssen|sser|ssi|sso|ssol|ssou|ssu|ssua|ssy|ssé|su|thy|va|ver|vi|vor|vul|xie|xiè]-{fe,m@}·, diffé·, direc[ce|ge|se|te]·
    - M: de|dea|di|die|dis|dy|dî, di[a|cho|chro|dac|ffa|ffen|ffi|ffor|ffu|ges|gi|gne|gni|gé|jo|jonc|la|le|li|lu|mi|na|nan|nas|ne|no|o|plo|plô|rec|ri|scer|sci|sen|shar|sig|sle|slo|ssem|ssen|sser|ssi|sso|ssol|ssou|ssu|ssua|ssy|ssé|su|thy|va|ver|vi|vor|vul|xie|xiè]-{fe,m@}·, diffé·
    - H: de|dea|di|die|dis|dy|dî, di[ffi|gi|gni|li|mi|ri|sci|ssi|ssy|thy|vi|xie]·⟨de|dea|di|die|dis|dy|dî⟩

## Pseudo-affix rules (attestedShare < 0.5) per setting

- L: `in`, `e`, `der`, `ré`, `de|dea|di|die|dis|dy|dî`, `er`, `nir`, `per`, `ex`, `voir`, `ou`, `ve`, `mi`
- M: `au`, `in`, `der`, `e`, `ré`, `i`, `o`, `ra`, `er`, `de|dea|di|die|dis|dy|dî`, `nir`, `po`, `mi`, `voir`
- H: `ain|hin|im|in`, `é`, `au`, `pa`, `ai|aî|e|ei|hai|he|hê|é`, `der`, `ra|rai|raie|re|rhé|ré|réh`, `ser|sée|zer|zé`, `de|dea|di|die|dis|dy|dî`, `e|hi|hy|i|y|î`, `o`
