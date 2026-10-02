# Weight sweep comparison (U6)

Credited saving = cumulative word-once-credited total from the selection curve (before the swap pass), in stroke-frequency units.

| setting | EXCEPTION_ALPHA | EXCLUSION_COST | FORM_COST | saving @20 | saving @30 | forms | exclusions | word exceptions | attestedShare<0.5 | max exception rate | max overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L | 1.0 | 5.0 | 10.0 | 50140 | 61383 | 90 | 20 | 722 | 16 | 4.9% | 0.00 |
| M | 1.0 | 50.0 | 100.0 | 55846 | 68670 | 79 | 15 | 950 | 15 | 4.9% | 0.00 |
| H | 2.0 | 150.0 | 300.0 | 77723 | 97884 | 60 | 5 | 1598 | 12 | 4.9% | 0.09 |

## Rules selected in any setting, by rank

| rule | L | M | H |
|---|---|---|---|
| suffix `ment` | — | — | 1 |
| suffix `man|mand|mant|ment|ments|mmant|mment` | 1 | 1 | — |
| suffix `ccion|cion|cyon|sion|ssion|tion|tions` | 2 | 2 | — |
| prefix `re` | — | — | 2 |
| prefix `en` | — | — | 3 |
| prefix `de` | 3 | 3 | 4 |
| prefix `au` | — | 4 | 11 |
| prefix `in` | 4 | 5 | — |
| prefix `ain|hin|im|in` | — | — | 5 |
| suffix `der` | 5 | 6 | 14 |
| suffix `tion` | — | — | 6 |
| prefix `pro|proh|prô` | 6 | 11 | 19 |
| prefix `ce|sce|se` | 7 | 9 | 20 |
| prefix `dé` | — | — | 7 |
| prefix `par` | — | 7 | 13 |
| suffix `ter` | — | — | 8 |
| prefix `im` | 8 | 13 | — |
| suffix `sser` | — | 8 | — |
| prefix `é` | — | — | 9 |
| suffix `er` | 9 | 17 | — |
| prefix `i` | — | 10 | — |
| suffix `nir` | 10 | 18 | — |
| suffix `té` | — | — | 10 |
| prefix `ai` | 11 | 19 | — |
| prefix `per` | 12 | — | — |
| suffix `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` | — | — | 12 |
| prefix `o` | — | 12 | 25 |
| suffix `teur` | 13 | 22 | — |
| prefix `ex` | 14 | 28 | — |
| prefix `pré` | — | 14 | — |
| suffix `voir` | 15 | 25 | — |
| prefix `pa|pei|pâ` | — | — | 15 |
| suffix `cher` | — | 15 | 30 |
| prefix `vou` | 16 | 24 | — |
| prefix `ra` | — | 16 | 29 |
| prefix `ai|aî|e|ei|hai|he|hê|é` | — | — | 16 |
| suffix `ture` | 17 | — | — |
| suffix `ver` | — | — | 17 |
| prefix `sa|sah` | — | — | 18 |
| prefix `ou` | 18 | — | — |
| prefix `ve` | 19 | 26 | — |
| prefix `di` | — | 20 | — |
| prefix `cou` | 20 | — | — |
| prefix `po` | — | 21 | — |
| prefix `ra|rai|raie|re|rhé|ré|réh` | — | — | 21 |
| prefix `pen` | 21 | — | — |
| suffix `ser|sée|zer|zé` | — | — | 22 |
| prefix `sou` | 22 | — | — |
| prefix `de|dea|di|die|dis|dy|dî` | — | — | 23 |
| suffix `mi` | 23 | — | — |
| prefix `mi` | — | 23 | — |
| suffix `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` | — | — | 24 |
| prefix `fi` | 24 | — | — |
| prefix `trou` | 25 | — | — |
| suffix `tant` | 26 | — | — |
| suffix `ger` | — | — | 26 |
| suffix `nner` | — | 27 | — |
| suffix `ner` | — | — | 27 |
| prefix `si` | 27 | — | — |
| prefix `e|hi|hy|i|y|î` | — | — | 28 |
| prefix `vi` | 28 | — | — |
| suffix `per` | 29 | — | — |
| prefix `em` | — | 29 | — |
| suffix `cer` | — | 30 | — |
| prefix `té` | 30 | — | — |

## Rules selected in every setting whose forms differ between settings

- prefix `pro|proh|prô`
    - L: pro|proh|prô, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·, profe[ne|sse|ssio|sso|tte|ttri]·, pro[chi|di|fi|i|li|phy|pi|vi]·
    - M: pro|proh|prô, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·
    - H: pro|proh|prô
- prefix `ce|sce|se`
    - L: ce|sce|se, se[con|cou|coue|crè|cré|cun|gue|mai|mes|mon|na|pen|rei|ri|rin|ven]·
    - M: ce|sce|se
    - H: ce|sce|se

## Pseudo-affix rules (attestedShare < 0.5) per setting

- L: `in`, `der`, `er`, `nir`, `per`, `ex`, `voir`, `ou`, `ve`, `pen`, `mi`, `fi`, `tant`, `si`, `vi`, `per`
- M: `au`, `in`, `der`, `i`, `o`, `ra`, `er`, `nir`, `di`, `po`, `mi`, `voir`, `ve`, `nner`, `ex`
- H: `ain|hin|im|in`, `é`, `au`, `der`, `pa|pei|pâ`, `ai|aî|e|ei|hai|he|hê|é`, `ra|rai|raie|re|rhé|ré|réh`, `ser|sée|zer|zé`, `de|dea|di|die|dis|dy|dî`, `o`, `e|hi|hy|i|y|î`, `ra`
