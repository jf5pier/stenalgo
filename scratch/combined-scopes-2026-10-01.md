# Combined simulation of the 30 decided scopes (H, flag on, form cost 100, fallback 5)

ALONE = rule simulated by itself; COMBINED = all rules in one `simulate` call. d_obj = combined - alone; flagged when objective drops by more than 100.

| rank | root | keys | scope words (2-stroke) | benefit alone / comb | exc words alone / comb | exc freq alone / comb | fallbacks alone / comb | objective alone | objective comb | d_obj | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `ment` | (20, 21, 25) | 2471 (2393/2393) | 8729 / 8729 | 1 / 1 | 0.0 / 0.0 | 78 / 78 | 8239 | 8239 | +0 |  |
| 2 | `re|reh` | (9, 18) | 0 (0/0) | 6200 / 6200 | 40 / 40 | 48.8 / 48.8 | 0 / 0 | 6102 | 6102 | +0 |  |
| 3 | `en` | (2, 16, 18) | 227 (197/196) | 6035 / 5498 | 35 / 97 | 2.5 / 539.4 | 30 / 31 | 5780 | 4164 | -1616 | **DROP** |
| 4 | `de|des|dé|déh` | (11, 16, 18) | 0 (0/0) | 5029 / 4966 | 226 / 274 | 102.2 / 165.4 | 0 / 0 | 4824 | 4635 | -189 | **DROP** |
| 5 | `de` | (16, 19) | 47 (47/47) | 4792 / 4792 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 4692 | 4692 | +0 |  |
| 6 | `tion` | (9, 20, 25) | 1712 (1698/1698) | 5361 / 5361 | 2 / 2 | 10.9 / 10.9 | 14 / 14 | 5169 | 5169 | +0 |  |
| 7 | `ain|hin|im|in` | (9, 19) | 118 (118/118) | 4833 / 4833 | 2 / 2 | 2.7 / 2.7 | 0 / 0 | 4727 | 4727 | +0 |  |
| 8 | `é` | (2, 5) | 0 (0/0) | 5449 / 5244 | 9 / 22 | 2.8 / 207.4 | 0 / 0 | 5443 | 4830 | -614 | **DROP** |
| 9 | `ter` | (16, 20, 22) | 0 (0/0) | 4569 / 4569 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 4569 | 4569 | +0 |  |
| 10 | `té` | (19, 20, 25) | 1515 (1423/1423) | 4223 / 4223 | 29 / 29 | 5.4 / 5.4 | 92 / 92 | 3652 | 3652 | +0 |  |
| 11 | `au` | (2, 5, 8) | 290 (288/288) | 3673 / 3672 | 1 / 10 | 0.3 / 1.9 | 2 / 2 | 3563 | 3558 | -5 |  |
| 12 | `pa` | (2, 5, 18) | 0 (0/0) | 3155 / 3144 | 15 / 34 | 18.3 / 29.2 | 0 / 0 | 3118 | 3086 | -33 |  |
| 13 | `cer|cé|cée|cés|scer|se|ser|sse` | (16, 17, 19) | 4 (4/4) | 4732 / 4730 | 0 / 8 | 0.0 / 2.2 | 0 / 0 | 4632 | 4625 | -7 |  |
| 14 | `par` | (8, 19) | 0 (0/0) | 3071 / 3071 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 3071 | 3071 | +0 |  |
| 15 | `ai|aî|e|ei|hai|he|hê|é` | (5, 18, 19) | 124 (115/110) | 4803 / 4801 | 0 / 1 | 0.0 / 0.0 | 9 / 14 | 4658 | 4631 | -27 |  |
| 16 | `der` | (16, 19, 25) | 9 (7/7) | 2523 / 2523 | 0 / 0 | 0.0 / 0.0 | 2 / 2 | 2413 | 2413 | +0 |  |
| 17 | `ra|rai|raie|re|rhé|ré|réh` | (3, 4, 16) | 712 (695/695) | 3367 / 3367 | 17 / 17 | 7.0 / 7.0 | 17 / 17 | 3168 | 3168 | +0 |  |
| 18 | `sa|sah` | (5, 24) | 0 (0/0) | 2649 / 2649 | 14 / 14 | 0.2 / 0.2 | 0 / 0 | 2649 | 2649 | +0 |  |
| 19 | `ver` | (19, 20, 22) | 3 (2/2) | 2509 / 2509 | 0 / 0 | 0.0 / 0.0 | 1 / 1 | 2404 | 2404 | +0 |  |
| 20 | `pro|proh|prô` | (4, 5, 8) | 0 (0/0) | 2455 / 2434 | 4 / 7 | 0.0 / 21.1 | 0 / 0 | 2455 | 2392 | -63 |  |
| 21 | `ce|sce|se` | (3, 6) | 0 (0/0) | 2383 / 2383 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 2383 | 2383 | +0 |  |
| 22 | `pou|pu` | (4, 7, 18) | 0 (0/0) | 2215 / 2215 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 2215 | 2215 | +0 |  |
| 23 | `ser|sée|zer|zé` | (16, 19, 20) | 536 (530/530) | 2354 / 2354 | 0 / 0 | 0.0 / 0.0 | 6 / 6 | 2124 | 2124 | +0 |  |
| 24 | `de|dea|di|die|dis|dy|dî` | (3, 16, 19) | 280 (278/278) | 2296 / 2291 | 0 / 4 | 0.0 / 4.6 | 2 / 2 | 2186 | 2172 | -14 |  |
| 25 | `e|hi|hy|i|y|î` | (16, 17, 19) | 811 (792/768) | 3199 / 2889 | 12 / 47 | 5.0 / 254.0 | 19 / 43 | 2994 | 2066 | -928 | **DROP** |
| 26 | `rae|rai|raie|re|rer|rez|rrer|r` | (16, 20, 21) | 107 (102/102) | 2397 / 2397 | 1 / 1 | 0.0 / 0.0 | 5 / 5 | 2272 | 2272 | +0 |  |
| 27 | `o` | (16, 18, 19) | 400 (387/384) | 2584 / 2583 | 4 / 4 | 0.1 / 0.1 | 13 / 16 | 2419 | 2403 | -16 |  |
| 28 | `ger` | (16, 24) | 0 (0/0) | 1910 / 1910 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 1910 | 1910 | +0 |  |
| 29 | `ner` | (18, 19, 20) | 120 (112/112) | 1779 / 1779 | 0 / 0 | 0.0 / 0.0 | 8 / 8 | 1639 | 1639 | +0 |  |
| 30 | `cher` | (9, 24, 25) | 0 (0/0) | 1789 / 1789 | 0 / 0 | 0.0 / 0.0 | 0 / 0 | 1789 | 1789 | +0 |  |

Sum of objectives: alone 107260, combined 103749 (-3511). Benefit credited once per word and position: 109479 (sum of per-rule combined benefits 109904).

Top exceptions and fallbacks (combined):

- 1 `ment`: exceptions ['blèsement']; fallbacks ['rarement', 'largement', 'jument', 'ciment']
- 2 `re|reh`: exceptions ['remords', 'relax', 'requin', 'relax', 'requins', 'relis']; fallbacks []
- 3 `en`: exceptions ['ensemble', 'envie', 'ensemble', 'envie', 'encourager', 'engueuler']; fallbacks ['enfants', 'enfant', 'entends', 'entend']
- 4 `de|des|dé|déh`: exceptions ['décide', 'débrouiller', 'dégoûte', 'décides', 'député', 'décrit']; fallbacks []
- 5 `de`: exceptions []; fallbacks []
- 6 `tion`: exceptions ['caution', 'cautions']; fallbacks ['station', 'nation', 'addition', 'nations']
- 7 `ain|hin|im|in`: exceptions ['indemne', 'indemnes']; fallbacks []
- 8 `é`: exceptions ['équipe', 'époque', 'équipes', 'évoque', 'époques', 'épi']; fallbacks []
- 9 `ter`: exceptions []; fallbacks []
- 10 `té`: exceptions ['limité', 'limitée', 'agilité', 'limitées', 'limités', 'milité']; fallbacks ['comité', 'cité', 'hésitez', 'hérité']
- 11 `au`: exceptions ['aubaine', 'audit', 'autisme', 'audits', 'aubaines', 'audit']; fallbacks ['auto', 'autos']
- 12 `pa`: exceptions ['panique', 'papy', 'paddy', 'pager', 'paré', 'parés']; fallbacks []
- 13 `cer|cé|cée|cés|scer|`: exceptions ['percée', 'versé', 'versée', 'nocer', 'percé', 'vécés']; fallbacks []
- 14 `par`: exceptions []; fallbacks []
- 15 `ai|aî|e|ei|hai|he|hê`: exceptions ['aidâtes']; fallbacks ['essaie', 'essaies', 'essaierai', 'essaient']
- 16 `der`: exceptions []; fallbacks ['gardez', 'mandez']
- 17 `ra|rai|raie|re|rhé|r`: exceptions ['régner', 'régnez', 'régné', 'récria', 'récriai', 'récrié']; fallbacks ['réagi', 'réagit', 'réagis', 'réfugie']
- 18 `sa|sah`: exceptions ['sableuse', 'saroual', 'sableuses', 'sarouals', 'sabelles', 'saboule']; fallbacks []
- 19 `ver`: exceptions []; fallbacks ['rivé']
- 20 `pro|proh|prô`: exceptions ['profite', 'profites', 'profitent', 'prodrome', 'prodromes', 'procréerai']; fallbacks []
- 21 `ce|sce|se`: exceptions []; fallbacks []
- 22 `pou|pu`: exceptions []; fallbacks []
- 23 `ser|sée|zer|zé`: exceptions []; fallbacks ['usez', 'balisée', 'baliser', 'balisé']
- 24 `de|dea|di|die|dis|dy`: exceptions ['diverses', 'diverses', 'diverse', 'digresse']; fallbacks ['dixie', 'divis']
- 25 `e|hi|hy|i|y|î`: exceptions ['ira', 'hiver', 'iras', 'issue', 'hyper', 'issues']; fallbacks ['innocent', 'innocents', 'innocence', 'innocent']
- 26 `rae|rai|raie|re|rer|`: exceptions ['aurai']; fallbacks ['gérer', 'blairer', 'parer', 'galérer']
- 27 `o`: exceptions ['oblongue', 'oblong', 'oblongues', 'oblongs']; fallbacks ['omis', 'offrit', 'obi', 'officie']
- 28 `ger`: exceptions []; fallbacks []
- 29 `ner`: exceptions []; fallbacks ['mené', 'dîné', 'miné', 'fouiné']
- 30 `cher`: exceptions []; fallbacks []
