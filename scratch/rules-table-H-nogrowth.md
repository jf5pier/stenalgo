# The 30 affix rules, H setting, partial-overlap flag on, no growth for `re-`

Source: `scratch/affix-sweep-partial/H/affix-rules.tsv` (sweep of 2026-09-30 on the lexicon after the `R2` -> `R°` fix; merged into the branch at 5699ab1, no-growth for `re|reh` in `src/affixes.py`). Regenerate with `env/bin/python scratch/rules_table.py`.

Notation: `/` separates alternatives, `[a/b]` = any one of them, `·` = where the anchor sits, `k=n` = syllables on the stroke, `⟨…⟩` and `-{…}` are engine notation. Words = carrier words of the rule; saved = stroke-frequency saved; exceptions = words (frequency).

| # | pos | anchor | keys | forms (full expansion) | words | saved | exceptions |
|---|---|---|---|---|---|---|---|
| 1 | suffix | `ment` | 20,21,25 | ment(k=1); ·[be/ble/boie/bre/ca/ce/che/chi/chisse/ci/cie/claffe/cle/cre/cré/cu/cé/de/di/die/doie/dre/droie/du/dé/dû/ffle/ffre/fie/fle/ge/gi/gle/gne/gre/gré/gu/gue/ille/la/le/li/lle/loie/lu/lé/lû/ma/me/mmé/moie/mé/ne/ni/nie/nne/nné/noie/nu/nue/né/nû/pe/pie/ple/pli/ppe/pre/que/ra/re/rre/rré/ré/sce/se/sse/ssoie/ssé/sé/ta/te/ti/tie/toie/tre/trie/tru/tte/té/ve/voue/vre/vé/xcré/xe/xtre/zaie/é]ment(k=2) | 2724 | 8887 | 1 (0.0) |
| 2 | prefix | `re/reh` | 9,18 | re/reh(k=1) | 6275 | 6200 | 40 (48.8) |
| 3 | prefix | `en` | 2,16,18 | en(k=1); en[cen/chan/clen/fan/gen/gran/jam/san/ten]·(k=2) | 4244 | 6036 | 33 (2.5) |
| 4 | prefix | `de/des/dé/déh` | 11,16,18 | de/des/dé/déh(k=1); dé[bi/bri/brie/chi/ci/cli/cri/di/fi/fri/gi/gri/gui/i/li/mi/my/ni/pi/pli/pri/qui/ri/shy/si/ssi/tri/vi]·(k=2) | 10383 | 5389 | 310 (198.7) |
| 5 | prefix | `de` | 16,19 | de(k=1); de[ba/man/meu/moi/re/van/ve/vi/vien/vri]·(k=2) | 261 | 4915 | 0 (0.0) |
| 6 | suffix | `tion` | 9,20,25 | tion(k=1); ·[a/ba/bra/ca/cia/cra/da/dia/fla/ga/gna/gra/la/lia/lla/ma/mma/na/pa/pla/qua/ra/ria/rra/sa/sla/ssa/ta/tia/tra/tta/va/via/xa/xpia]tions(k=2); ·[bi/bli/bri/chi/ci/di/fi/gi/gri/i/ki/li/lli/mi/mmi/ni/pi/pli/ppli/qui/ri/ry/si/spi/sti/thi/ti/tri/vi/xci/xi/xpli]tations(k=3); ·[sten/ten/tten/ven]tion(k=2) | 2165 | 5504 | 2 (10.9) |
| 7 | prefix | `ain/hin/im/in` | 9,19 | ain/hin/im/in(k=1); in[bé/ce/clé/cré/dé/flé/fré/fé/gré/gé/pe/plé/pre/pré/pé/quié/sai/sé/te/tré/té/vé]·(k=2); im[cor/for/por]·(k=2); inté[ce/chi/ci/cro/cu/di/du/fec/fen/fi/for/fri/gra/gre/gri/li/llec/lli/lo/lé/ma/men/mi/ni/nia/nie/nieu/nio/nom/nou/né/o/pa/pen/pi/ra/re/ri/ria/rieu/rio/ré/sa/si/ssa/ssio/te/tec/ter/ti/té/vi/voy]·(k=3) | 4821 | 5614 | 45 (80.2) |
| 8 | prefix | `é` | 2,5 | é(k=1); é[chi/cri/di/gri/li/ly/mi/pi/qui/ri/ry/thi/thy/ti/tri/ty/vi]·(k=2) | 6111 | 5499 | 70 (384.5) |
| 9 | suffix | `ter` | 16,20,22 | ter(k=1); ·[crê/nne/pê/rrê/trai]ter(k=2) | 3162 | 4573 | 5 (0.1) |
| 10 | suffix | `té` | 19,20,25 | té(k=1); ·[bi/bri/ci/cli/cri/di/fi/gi/gni/gri/i/li/lli/mi/mmi/ni/nni/pi/pli/qui/ri/rri/ry/sci/si/ssi/ti/xci/xi/ï]-{v}té(k=2) | 2889 | 4151 | 20 (27.6) |
| 11 | prefix | `au` | 2,5,8 | au(k=1); au[ber/bu/bé/cu/da/di/dien/dio/gu/gus/jour/lo/mô/pa/re/ri/ré/ssi/tar/then/to/toch/tom/top/tore/tos/tre/tri/ver/xe/xi]·(k=2) | 564 | 3747 | 2 (0.3) |
| 12 | prefix | `pa` | 2,5,18 | pa(k=1) | 1677 | 3171 | 13 (2.0) |
| 13 | suffix | `cer/cé/cée/cés/scer/se/ser/sser/ssez/ssée/sé` | 16,17,19 | cer/cé/cée/cés/scer/se/ser/sser/ssez/ssée/sé(k=1); ·[cen/den/en/ffen/gan/lan/man/men/mmen/nan/nnan/pen/quen/ren/rren/sen/ten/van/xpan]cé(k=2) | 2019 | 4500 | 25 (520.3) |
| 14 | prefix | `par` | 8,19 | par(k=1) | 552 | 3071 | 0 (0.0) |
| 15 | prefix | `ai/aî/e/ei/hai/he/hê/é` | 5,18,19 | ai/aî/e/ei/hai/he/hê/é(k=1); ai[che/de/gle/gre/le/me/nne/rre]·(k=2); e[ssa/ssai/ssaie/xce/xcré/xpre/xte/xtrê]·(k=2) | 1973 | 4253 | 24 (298.1) |
| 16 | suffix | `der` | 16,19,25 | der(k=1); ·[an/ba/bar/bau/blar/bon/ca/car/cca/ccor/chan/char/ci/con/cé/en/fau/ffau/gar/gnar/gon/gour/gra/gui/illa/la/lan/lar/li/llar/man/mar/mer/mi/mman/mmar/mmo/na/nar/nau/non/o/par/pen/pi/qui/ra/rau/san/sar/scen/si/ssou/ssua/ssé/sua/sé/va/vau/xtra/zar]-{bOR}dez(k=2) | 1058 | 3523 | 39 (10.5) |
| 17 | prefix | `ra/rai/raie/re/rhé/ré/réh` | 3,4,16 | ra/rai/raie/re/rhé/ré/réh(k=1); ré[clu/cu/du/fu/gu/mu/pu/su/u]·(k=2); réa[bi/bli/bo/ccou/che/dap/ffec/ffi/ffir/gi/jus/li/mor/mé/ni/per/pi/ppa/ppe/ppre/ppren/ppro/ra/re/rran/ssem/ssi/ssor/ssu/tta]·(k=3) | 3743 | 3348 | 57 (29.2) |
| 18 | prefix | `sa/sah` | 5,24 | sa/sah(k=1) | 1017 | 2650 | 14 (0.2) |
| 19 | suffix | `ver` | 19,20,22 | ver(k=1); ·[che/chi/cur/di/li/ner/nno/pprou/qui/ra/ri/rri/ser/ssi/ti/tra/trou/vi/xca]-{l°}vé(k=2) | 452 | 3083 | 2 (0.2) |
| 20 | prefix | `pro/proh/prô` | 4,5,8 | pro/proh/prô(k=1) | 1353 | 2455 | 4 (0.0) |
| 21 | prefix | `ce/sce/se` | 3,6 | ce/sce/se(k=1) | 274 | 2383 | 0 (0.0) |
| 22 | prefix | `pou/pu` | 4,7,18 | pou/pu(k=1) | 278 | 2215 | 0 (0.0) |
| 23 | suffix | `ser/sée/zer/zé` | 16,19,20 | ser/sée/zer/zé(k=1); ·[a/ba/bap/bi/bo/bé/ca/char/cia/co/cra/cré/cu/cé/da/do/dua/dé/for/ga/gi/gli/gné/go/gé/la/li/lia/lo/ma/mi/mmu/mo/mor/mé/na/ni/nna/no/né/or/pa/per/phi/phé/po/pro/qui/ra/ri/ria/rio/rro/sec/so/ssoi/ssu/sua/ta/ter/teu/ti/tia/to/tou/tra/tro/tu/tua/ty/té/va/ve/vi/via/vo/vé/xper/xtua/xua/ï]liser(k=3); ·[bu/clu/cu/du/ffu/fu/mu/xcu]sez⟨ser/sée/zer/zé⟩(k=2) | 1939 | 2763 | 79 (50.8) |
| 24 | prefix | `de/dea/di/die/dis/dy/dî` | 3,16,19 | de/dea/di/die/dis/dy/dî(k=1); di[ffi/gi/gni/li/mi/ri/sci/ssi/ssy/thy/vi/xie]·⟨de/dea/di/die/dis/dy/dî⟩(k=2) | 1201 | 2306 | 0 (0.0) |
| 25 | prefix | `e/hi/hy/i/y/î` | 16,17,19 | e/hi/hy/i/y/î(k=1); i[ber/bis/bo/bé/ca/ce/cko/co/den/deu/dio/do/dra/drau/dro/drop/dros/dé/gié/gni/gno/gro/gua/ke/la/lle/lli/llo/llu/llus/llé/lo/lé/ma/mer/mi/mma/mmen/mmer/mmi/mmo/mmon/mmor/mmu/mmé/mé/na/nac/nad/nal/nap/nar/nau/ne/nemp/nen/nep/ner/nes/nex/nha/nhar/nhi/nhos/nhu/ni/nin/nno/nnom/no/non/nor/nou/nu/né/o/pa/pe/per/pere/pho/po/pos/ppo/pé/ra/ri/ro/ron/rra/rrai/rre/rrem/rres/rri/rro/rrup/rré/ru/sa/sla/slan/so/sra/ta/thy/ti/ver/voi/vro]·(k=2) | 2506 | 3262 | 23 (483.7) |
| 26 | suffix | `rae/rai/raie/re/rer/rez/rrer/rrhée/rrée/rée` | 16,20,21 | rae/rai/raie/re/rer/rez/rrer/rrhée/rrée/rée(k=1); ·[bé/cé/dé/fé/gé/lle/lé/mmé/mé/né/pie/pé/re/scé/ssié/sé/te/té/vé]rer(k=2) | 1633 | 2363 | 53 (51.0) |
| 27 | prefix | `o` | 16,18,19 | o(k=1); o[bi/bli/dy/ffi/ffri/gi/li/mi/ni/pi/ppi/ppri/ri/sci/ssi/vi]·(k=2) | 1201 | 2255 | 0 (0.0) |
| 28 | suffix | `ger` | 16,24 | ger(k=1) | 1028 | 1910 | 0 (0.0) |
| 29 | suffix | `ner` | 18,19,20 | ner(k=1); ·[ber/bi/bor/boui/ca/car/chaî/chi/ci/co/dam/di/fa/fi/fré/ga/gai/gi/gor/gre/gri/gé/jeu/jour/li/me/mi/mo/pa/pho/pi/pli/poui/qui/ri/ré/scer/sci/ser/si/ssi/sti/ta/ter/ti/traî/tri/tti/tu/ver/vi]-{tRe,tuR}né(k=2) | 1226 | 2488 | 38 (3.2) |
| 30 | suffix | `cher` | 9,24,25 | cher(k=1) | 831 | 1789 | 0 (0.0) |
