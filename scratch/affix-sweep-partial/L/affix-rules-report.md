# Affix rules (Phase 3 + 4 result, DESIGN_2026-09-27-affix-rule-selection.md; single-generator pool, PLAN_2026-09-28)

Constants: RULE_BUDGET=30, MAX_RULE_FORMS=6, EXCEPTION_ALPHA=1.0, EXCLUSION_COST=5.0, FORM_COST=10.0, SWAP_CANDIDATES=20, SWAP_PASSES=3, RULE_OVERLAP_MAX=0.5, MAX_EXCEPTION_RATE=0.05, GROWTH_MIN_EXPAND=5.0, GROWTH_MAX_DEPTH=4, MAX_SLOT_EXCLUSIONS=3, GROWTH_MAX_EXCEPTION_SHARE=0.05.

Note: bare verb-infinitive-ending candidates (isVerbEndingFragment) are left UNFILTERED, per the user's 2026-09-27 decision to let them compete on score.

Selected rules with attestedShare < 0.5 (the old stem-attestation filter would have rejected most of their carriers; candidate pseudo-affixes like `ma-`): **13** -- `in`, `e`, `der`, `ré`, `de|dea|di|die|dis|dy|dî`, `er`, `nir`, `per`, `ex`, `voir`, `ou`, `ve`, `mi`

## Savings curve (cumulative total after each acceptance, 1..40)

8169, 13695, 18601, 22484, 26138, 29635, 32936, 35683, 38134, 40346, 42489, 44356, 46187, 47875, 49439, 51064, 52563, 53996, 55320, 56628, 58161, 59454, 60785, 62049, 63230, 64468, 65631, 66868, 68160, 69287

## 1. suffix `man|mand|mant|ment|ments|mmant|mment` -- keys (19, 20) = `-dt`

forms: `man|mand|mant|ment|ments|mmant|mment`(k=1), `·[a|ai|be|ble|boie|bre|ca|ce|cha|che|chi|chisse|ci|cie|claffe|cle|cre|cré|cu|cé|da|de|di|die|doie|dre|droie|du|dé|dû|ffle|ffre|fie|fle|for|ga|ge|gle|gne|gre|gré|gu|gue|ille|la|le|li|lla|lle|loie|lu|lé|lû|ma|me|moie|mé|ne|ni|nie|nna|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|ro|rre|rré|ré|sa|sce|scie|se|sias|ssa|sse|ssoie|ssuie|ssé|sul|sé|ta|te|ti|tie|toie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|zaie|é]ment`(k=2), `·[a|ac|bi|blo|bus|ca|chan|cho|ci|cinc|co|cri|cru|crè|da|des|dia|dio|droi|fai|fes|fflo|frou|gen|glan|glou|gno|ille|illo|jec|jus|li|llo|lo|ma|men|mo|nes|nnê|noî|par|pen|pi|plè|po|ppar|ppoin|qua|quin|què|rec|ren|roi|rrec|sen|so|ssau|sso|strai|ten|ti|tinc|tis|troi|tui|van|ver|vro|vê|xper|zo|ïs]-{pOR}tement`(k=3), `·[bi|bli|bri|chi|ci|cri|di|dri|ffi|fi|gi|gli|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|pli|qui|ri|rri|sci|si|ssi|sti|thi|ti|tri|tti|vi|vri|xi|y|ï]caments`(k=3), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|ppa|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|voua|xa|za|ça]blement`(k=3), `·[ai|bai|be|chai|chaî|chè|cie|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|me|miè|mmai|mè|mê|nai|ne|niai|niè|nnai|nne|nnê|piè|plai|plè|prê|què|rai|re|rei|rie|rrai|rè|sai|scè|se|sei|siè|ssai|ssiè|strai|sè|tai|te|tie|tiè|trai|traî|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]tement⟨·[a|ai|be|ble|boie|bre|ca|ce|cha|che|chi|chisse|ci|cie|claffe|cle|cre|cré|cu|cé|da|de|di|die|doie|dre|droie|du|dé|dû|ffle|ffre|fie|fle|for|ga|ge|gle|gne|gre|gré|gu|gue|ille|la|le|li|lla|lle|loie|lu|lé|lû|ma|me|moie|mé|ne|ni|nie|nna|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|ro|rre|rré|ré|sa|sce|scie|se|sias|ssa|sse|ssoie|ssuie|ssé|sul|sé|ta|te|ti|tie|toie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|zaie|é]ment⟩`(k=3)
- score 8168.6, strokeFreqSaved 9200.2, keySimilarity 0.09 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.59; exception rate 3.4%; top categories: ADV 59%, NOM 39%, ADJ 2%
- fused spelling variants: man, mand, mant, ment, ments, mmant, mment (new conflict freq 1.4)
- word exceptions 99 (freq 976.6)
- top exceptions: moment, appartement, apparemment, également, allemands, moments, évidemment, enterrement, amant, bâtiment
    seulement: s@/mt@a/m@ -> s@dt
    tellement: tie/mt@a/m@ -> tiedt
    exactement: iekdnl/ak/t@a/m@ -> iekdtnl
    sûrement: s@i/R@a/m@ -> s@idt
    complètement: kai/pmtie/t@a/m@ -> kaidt

## 2. suffix `ccion|cion|cyon|sion|ssion|tion|tions` -- keys (9, 20, 25) = `w-tm`

forms: `ccion|cion|cyon|sion|ssion|tion|tions`(k=1), `·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tions⟨ccion|cion|cyon|sion|ssion|tion|tions⟩`(k=2), `·[bi|ci|ddi|di|gni|li|lli|mi|mmi|ni|pi|ri|sci|si|sti|ti|tri]tion`(k=2), `·[bi|bli|bri|chi|ci|di|fi|gi|gri|i|ki|li|lli|mi|mmi|ni|pi|pli|ppli|qui|ri|ry|si|spi|sti|thi|ti|tri|vi|xci|xi|xpli]tations`(k=3), `·[cen|en|men|pen|sten|ten|tten|ven|xten]tion`(k=2), `·[blu|bu|cu|llu|lu|nu|ru|tu]tion⟨ccion|cion|cyon|sion|ssion|tion|tions⟩`(k=2)
- score 5526.9, strokeFreqSaved 6050.0, keySimilarity 0.07 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.69; exception rate 1.8%; top categories: NOM 96%, ONO 4%, ADJ 0%
- fused spelling variants: ccion, cion, cyon, sion, ssion, tion, tions (new conflict freq 0.1)
- word exceptions 42 (freq 473.2)
- top exceptions: attention, attention, condition, commission, conditions, caution, compassion, potion, addition, démission
    situation: si/t@a/sRwai -> si/tw@atm
    impression: aie/pRe/sRwai -> aie/pRwetm
    mission: mi/sRwai -> mwitm
    félicitations: kpe/mti/si/ta/sRwai/-s -> kpe/mtwitm/-s

## 3. prefix `de` -- keys (16, 19) = `-jd`

forms: `de`(k=1), `de[ba|man|meu|moi|re|van|ve|vi|vien|vri]·`(k=2)
- score 4905.4, strokeFreqSaved 4915.4, keySimilarity 0.27 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.78; exception rate 0.0%; top categories: VER 65%, ADV 20%, NOM 9%
- word exceptions 0 (freq 0.0)
    demain: pv@a/maie -> maiejd
    demande: pv@a/m@d -> m@jd
    devrais: pv@a/vRie/-k -> vRiejd/-k
    demandé: pv@a/m@/pve -> pvejd
    devrait: pv@a/vRie -> vRiejd
    devant: pv@a/v@ -> v@jd

## 4. prefix `in` -- keys (12, 16, 19) = `ajd`

forms: `in`(k=1), `in[ce|clé|cré|dé|flé|fré|fé|gré|gué|gé|quié|sai|sé|te|tré|té|vé]·`(k=2), `in[chi|ci|cli|cri|di|fi|fli|gui|qui|si|ti|tri|vi]·`(k=2), `inté[ce|chi|ci|cro|di|du|fec|fen|fi|for|fri|gra|gre|gri|li|llec|lli|lo|lé|ma|mi|mon|nia|nie|nieu|nio|nom|nou|o|pa|pen|pi|ra|re|ri|rieu|rio|ré|si|ssa|te|tec|ter|té]·`(k=3), `in[cer|fer|ter|ver]·`(k=2), `infor[ma|me|mu|po|tu]·`(k=3)
- score 3882.8, strokeFreqSaved 4127.2, keySimilarity 0.02 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.46; exception rate 3.9%; top categories: NOM 38%, VER 36%, ADJ 26%
- word exceptions 153 (freq 194.4)
- top exceptions: inquiétez, invité, inquiéter, inviter, invitée, invités, infinie, intégrité, infini, infini
    inquiète: aie/kRwiet -> kRwiejdt
    intérieur: aie/te/Rw@R -> Rw@jdR
    intéresse: aie/te/Ries -> Riejsd
    intérêt: aie/te/Rie -> Riejd
    intéressant: aie/te/Rie/s@ -> s@jd
    interdit: aie/tieR/pvi -> pvijd

## 5. prefix `e` -- keys (5, 18, 23) = `v-kl`

forms: `e`(k=1), `e[ssa|ssai|ssaie|xce|xcré|xpre|xte|xtrê]·`(k=2), `e[xclu|xcu|xsu]·`(k=2), `e[ffi|ffri|xci|xpi|xpie|xpli|xpri]·`(k=2), `e[cclé|ffé|xce|xcré|xcé|xplé|xpé|xtré|xté]·`(k=2), `extra[ce|con|cor|ga|lu|ma|or|po|rou|sen|si|sys|ta|te|ti|tri|trii|va|ver|véh]·`(k=3)
- score 3654.2, strokeFreqSaved 3740.6, keySimilarity 0.12 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.07; exception rate 4.7%; top categories: VER 62%, NOM 26%, ADJ 11%
- word exceptions 79 (freq 36.4)
- top exceptions: essaierai, excès, essaiera, errer, essaierais, expiré, essaierait, erré, expirer, expirez
    excusez: ie/ks@i/twe/-k -> vtwekl/-k
    essaie: ie/sie -> sviekl
    essayer: ie/sie/Rwe/-l -> vRwekl/-l
    essayé: ie/siej/e -> sviejkl/e
    excuse: ie/ks@inl -> ksv@iknl
    erreur: ie/R@R -> vR@kRl

## 6. suffix `der` -- keys (16, 19, 25) = `-jdm`

forms: `der`(k=1), `·[an|ba|bar|bau|blar|bon|ca|car|cca|ccor|chan|char|ci|con|cor|cé|en|fau|ffau|gar|gnar|gon|gour|gra|gui|illa|la|lan|lar|li|llar|man|mar|mer|mi|mman|mmar|mmo|na|nar|nau|non|o|par|pen|pi|qui|ra|rau|san|sar|scen|si|ssou|ssua|ssé|sua|sé|va|vau|xtra|zar]-{bOR}dez`(k=2)
- score 3497.4, strokeFreqSaved 3522.9, keySimilarity 0.47 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.22; exception rate 3.7%; top categories: VER 100%, NOM 0%
- word exceptions 39 (freq 10.5)
- top exceptions: décoder, élucider, bondé, rider, décodé, élucidé, codé, gambader, extrader, codées
    aider: ie/pve/-l -> iejdm/-l
    regardez: R@a/ksaR/pve/-k -> R@ajdm/-k
    demandé: pv@a/m@/pve -> pv@ajdm
    demander: pv@a/m@/pve/-l -> pv@ajdm/-l
    regarder: R@a/ksaR/pve/-l -> R@ajdm/-l
    garder: ksaR/pve/-l -> ksajdRm/-l

## 7. prefix `ré` -- keys (18, 23) = `-kl`

forms: `ré`(k=1), `ré[clu|cu|du|fu|gu|mu|pu|su|u]·`(k=2), `ré[a|ca|ce|cha|cla|ga|ma|pa|ta]·`(k=2), `ré[be|cré|crée|cé|e|flé|fré|fé|gé|pre|préh|pé|sé|tré|vei|vé|é]·`(k=2), `ré[com|con|pon]·`(k=2), `ré[e|fle|gre|vei]·`(k=2)
- score 3300.4, strokeFreqSaved 3579.5, keySimilarity 0.03 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.36; exception rate 4.0%; top categories: VER 60%, NOM 31%, ADJ 7%
- word exceptions 148 (freq 229.1)
- top exceptions: réussi, réparer, révéler, réussit, réparé, révélé, récit, réagi, régner, réagit
    réponse: Re/pais -> paiskl
    réponds: Re/pai/-k -> paikl/-k
    réveille: Re/v*iej -> v*iejkl
    répondre: Re/paidR -> paikdRl
    réalité: Re/a/mti/te -> mtikl/te

## 8. prefix `pro|proh|prô` -- keys (16, 17, 18) = `-jsk`

forms: `pro|proh|prô`(k=1), `pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·`(k=2), `proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·`(k=3), `pro[co|mo|no|po|ro|so|to|toh|vo]·`(k=2), `profe[ne|sse|ssio|sso|tte|ttri]·`(k=3), `pro[chi|di|fi|i|li|phy|pi|vi]·`(k=2)
- score 2747.5, strokeFreqSaved 2867.9, keySimilarity 0.20 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.73; exception rate 1.8%; top categories: NOM 56%, VER 28%, ADJ 12%
- fused spelling variants: pro, proh, prô (new conflict freq 0.0)
- word exceptions 25 (freq 70.4)
- top exceptions: projet, projets, promènerait, promèneraient, pronom, pronoms, propagerait, promènerai, promènerez, programmerai
    problème: pRae/svmtiem -> svmtiejskm
    problèmes: pRae/svmtiem/-s -> svmtiejskm/-s
    propos: pRae/pae -> paejsk
    prochaine: pRae/pmien -> pmiejskn
    promis: pRae/mi -> mijsk
    probablement: pRae/sva/svmt@a/m@ -> m@jsk

## 9. prefix `ce|sce|se` -- keys (3, 4, 18) = `sp-k`

forms: `ce|sce|se`(k=1), `se[con|cou|coue|crè|cré|cun|gue|mai|mes|mon|na|pen|rei|ri|rin|ven]·`(k=2)
- score 2451.0, strokeFreqSaved 2461.0, keySimilarity 0.65
- attestedShare 0.64; exception rate 0.0%; top categories: VER 35%, NOM 28%, PRO:dem 16%
- fused spelling variants: ce, sce, se (new conflict freq 0.0)
- word exceptions 0 (freq 0.0)
    serait: s@a/Rie -> spRiek
    celui: s@a/mt@ai -> spmt@aik
    semaine: s@a/mien -> spmiekn
    serai: s@a/Re/-t -> spRek/-t
    ceci: s@a/si -> spik
    semaines: s@a/mien/-s -> spmiekn/-s

## 10. prefix `pou` -- keys (4, 7, 18) = `pt-k`

forms: `pou`(k=1)
- score 2211.8, strokeFreqSaved 2211.8, keySimilarity 0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.89; exception rate 0.0%; top categories: VER 86%, NOM 13%, ADJ 1%
- word exceptions 0 (freq 0.0)
    pouvez: p@e/ve -> pvtek
    pourrait: p@e/Rie -> ptRiek
    pourrais: p@e/Rie/-k -> ptRiek/-k
    pouvoir: p@e/vwaR -> pvtwakR
    pouvais: p@e/vie/-k -> pvtiek/-k
    pouvait: p@e/vie -> pvtiek

## 11. prefix `im` -- keys (4, 19, 23) = `p-dl`

forms: `im`(k=1), `im[ba|bi|bro|bu|bé|man|mar|pa|pal|par|pay|pe|pen|per|pi|pla|plan|pli|plo|plé|po|pon|por|pos|pra|pre|pres|pri|pro|promp|prou|pru|pré|pu|pui|pul|pé]·`(k=2), `impre[ca|cca|ci|cu|di|men|ni|né|pa|ra|ri|ria|sa|sen|ssio|ti|tueu|tuo|vi|voy]·`(k=3)
- score 2143.4, strokeFreqSaved 2163.5, keySimilarity 0.32 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.58; exception rate 0.1%; top categories: ADJ 41%, VER 31%, NOM 27%
- word exceptions 1 (freq 0.1)
- top exceptions: implémenter
    importe: aie/petR -> pedtRl
    important: aie/peR/t@ -> pt@dl
    impossible: aie/pae/sijl -> spijdl
    impression: aie/pRe/sRwai -> spRwaidl
    importance: aie/peR/t@s -> pt@sdl
    importante: aie/peR/t@t -> pt@dtl

## 12. prefix `de|dea|di|die|dis|dy|dî` -- keys (4, 19) = `p-d`

forms: `de|dea|di|die|dis|dy|dî`(k=1), `di[a|cho|chro|dac|ffa|ffen|ffi|ffor|ffu|ges|gi|gne|gni|gé|jo|jonc|la|le|li|lu|mi|na|nan|nas|ne|no|o|plo|plô|rec|ri|scer|sci|sen|shar|sig|sle|slo|ssem|ssen|sser|ssi|sso|ssol|ssou|ssu|ssua|ssy|ssé|su|thy|va|ver|vi|vor|vul|xie|xiè]-{fe,m@}·`(k=2), `diffé·`(k=2), `direc[ce|ge|se|te]·`(k=3)
- score 1866.1, strokeFreqSaved 2350.6, keySimilarity 0.24 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.38; exception rate 4.9%; top categories: VER 49%, NOM 29%, ADJ 20%
- fused spelling variants: de, dea, di, die, dis, dy, dî (new conflict freq 0.0)
- word exceptions 59 (freq 434.5)
- top exceptions: dirait, dirai, dirais, dira, diras, direz, diront, divan, diraient, dirons
    difficile: pvi/kpi/sil -> spidl
    disais: pvi/twie/-k -> ptwied/-k
    disait: pvi/twie -> ptwied
    dîner: pvi/mRe -> pmRed

## 13. suffix `er` -- keys (9, 19, 20) = `w-dt`

forms: `er`(k=1), `·[bli|blii|boy|brou|cli|clou|clé|cré|cuy|doy|dri|droy|fli|flu|fri|geoy|gli|gri|gré|loy|loyi|moy|noy|nuy|nuyi|oy|phri|pli|plii|ppli|ppuy|ppuyi|pri|prii|qui|rroy|ré|ssuy|ssuyi|stru|toy|tri|trii|troy|ttoy|ttoyi|tu|voy|voyi]-{vRij}é`(k=2), `·[len|lé|nou|né|pa|phan|ppro|pu|ro|sa|ti|xpa]drier`(k=3)
- score 1831.7, strokeFreqSaved 1856.7, keySimilarity 0.08 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.39; exception rate 0.2%; top categories: VER 86%, NOM 14%, ADJ 1%
- word exceptions 1 (freq 0.0)
- top exceptions: republier
    oublié: @e/svmtij/e -> w@edt
    oublier: @e/svmtij/e/-l -> w@edt/-l
    envoyé: @/vwaj/e -> w@dt
    envoyer: @/vwaj/e/-l -> w@dt/-l
    oubliez: @e/svmtij/e/-k -> w@edt/-k
    envoyez: @/vwaj/e/-k -> w@dt/-k

## 14. suffix `nir` -- keys (13, 21, 22) = `iRn`

forms: `nir`(k=1), `·[bru|fi|jeu|mu|ste|u|ve|ver]-{t°}nir`(k=2), `·tenir`(k=2)
- score 1688.1, strokeFreqSaved 1713.1, keySimilarity 0.70
- attestedShare 0.19; exception rate 0.0%; top categories: VER 88%, NOM 12%
- word exceptions 0 (freq 0.0)
    venir: v@a/mRiR -> v@aiRn
    devenir: pv@a/v@a/mRiR -> pv@aiRn
    revenir: R@a/v@a/mRiR -> R@aiRn
    finir: kpi/mRiR -> kpiRn
    tenir: t@a/mRiR -> t@aiRn
    avenir: a/v@a/mRiR -> aiRn

## 15. prefix `fa` -- keys (2, 5, 16) = `kv-j`

forms: `fa`(k=1), `fa[bli|bri|bu|ci|cul|cé|de|go|hre|illi|lla|meu|mi|mu|mé|na|ne|ra|ran|rau|ri|rou|sci|se|ta|ve|vo|vé|xe|yo|zen|ço|ïen]-{ti}·`(k=2), `faci[le|li|na|ne]·`(k=3)
- score 1625.3, strokeFreqSaved 1663.6, keySimilarity 0.02 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.61; exception rate 2.8%; top categories: NOM 51%, VER 26%, ADJ 22%
- word exceptions 15 (freq 13.2)
- top exceptions: faculté, facultés, fascisme, faner, fanées, fanée, fanée, fanées, fanés, fané
    famille: kpa/mij -> kvmij
    façon: kpa/sai -> ksvaij
    facile: kpa/sil -> ksvijl
    fallait: kpa/mtie -> kvmtiej
    failli: kpa/Rwi -> kvRwij
    falloir: kpa/mtwaR -> kvmtwajR

## 16. prefix `ai` -- keys (8, 11, 23) = `R@l`

forms: `ai`(k=1), `ai[gle|gre|gri|gui|ma|man|me]-{d°}·`(k=2)
- score 1563.3, strokeFreqSaved 1578.3, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.93; exception rate 0.0%; top categories: VER 96%, ADJ 3%, NOM 1%
- word exceptions 0 (freq 0.0)
    aider: ie/pve/-l -> pvR@el/-l
    aimerais: ie/m@a/Rie/-k -> R@iel/-k
    aimer: ie/me/-l -> mR@el/-l
    aimé: ie/me -> mR@el
    aidez: ie/pve/-k -> pvR@el/-k
    aimez: ie/me/-k -> mR@el/-k

## 17. prefix `per` -- keys (2, 5) = `kv-` (shares with vou, ve)

forms: `per`(k=1), `per[ce|cep|che|chlo|co|dri|du|fi|fo|for|fu|go|gé|lim|ma|man|me|mi|mu|mé|ni|pen|pi|ple|pé|qui|si|sif|sis|so|spec|spi|su|sua|sé|ti|tui|ver]-{fEk,ky,tyR}·`(k=2), `personne[fi|li|lle]·`(k=4)
- score 1532.5, strokeFreqSaved 1585.7, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.29; exception rate 1.2%; top categories: VER 59%, NOM 27%, ADJ 13%
- word exceptions 10 (freq 18.2)
- top exceptions: perdez, percuté, percuter, percutée, perlés, percutez, percutés, percutées, percevrez, percoler
    perdu: pieR/pv@i -> kpv@i
    perdre: pieR/pvR- -> kpvR-
    personnes: pieR/sen/-s -> ksven/-s
    permettez: pieR/mie/te -> kvte
    permission: pieR/mi/sRwai -> ksvRwai
    personnel: pieR/sae/mRiel -> kvmRiel

## 18. suffix `teur` -- keys (9, 20, 23) = `w-tl`

forms: `teur`(k=1), `·[a|ba|bra|ca|cia|da|dia|ffla|ga|gna|gra|la|lia|lla|ma|mma|na|nia|nna|pa|pha|pla|qua|ra|ria|rra|sa|sla|ta|tia|tra|va|voi|xa|xploi]teur`(k=2), `·[flec|jec|lec|llec|pec|rec|tec|vec]teur`(k=2), `·[bri|ci|di|fi|gi|i|li|lli|mi|ni|pi|pli|qui|ri|sci|ssi|ti|vi]nateur`(k=3), `·[bi|ci|di|ffi|fi|mi|ni|ri|si|ti|tri|vi|xci]teur`(k=2), `·[a|lo|sé|ti|tri|é]tuteur`(k=3)
- score 1498.6, strokeFreqSaved 1615.7, keySimilarity 0.32 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.71; exception rate 3.2%; top categories: NOM 94%, ADJ 6%
- word exceptions 37 (freq 67.1)
- top exceptions: hauteur, auteur, auteurs, détecteur, compteur, détecteurs, auditeurs, hauteurs, orateur, dessinateur
    docteur: pvek/t@R -> pvwektl
    inspecteur: aies/piek/t@R -> waiestl
    directeur: pvi/Riek/t@R -> pvwitl
    acteur: ak/t@R -> waktl
    ordinateur: eR/pvi/mRa/t@R -> wetRl
    moteur: mae/t@R -> mwaetl

## 19. prefix `ex` -- keys (4, 14, 16) = `pej`

forms: `ex`(k=1), `exac[bi|bio|bé|cer|ci|cu|ga|gé|mi|né|pla|plai|pli|pé|qua|que|te|ten|ther|ti]·`(k=3), `ex[a|ac|al|as|au|e|em|emp|er|i|is|o|oph|or|os|u|é]·`(k=2)
- score 1433.8, strokeFreqSaved 1453.8, keySimilarity 0.01 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.29; exception rate 0.0%; top categories: VER 37%, NOM 31%, ADV 18%
- word exceptions 0 (freq 0.0)
    exactement: iekdnl/ak/t@a/m@ -> pm@ej
    exemple: iekdnl/@jkl -> p@ejkl
    existe: iekdnl/ist -> piejst
    exact: iekdnl/akt -> paejkt
    examen: iekdnl/a/maie -> pmaiej
    existence: iekdnl/is/t@s -> pt@ejs

## 20. suffix `voir` -- keys (16, 17, 21) = `-jsR`

forms: `voir`(k=1), `·[breu|ce|de|mou|ser|tre]voir`(k=2)
- score 1331.5, strokeFreqSaved 1341.5, keySimilarity 0.85
- attestedShare 0.22; exception rate 0.0%; top categories: VER 62%, NOM 38%
- word exceptions 0 (freq 0.0)
    savoir: sa/vwaR -> sajsR
    revoir: R@a/vwaR -> R@ajsR
    pouvoir: p@e/vwaR -> p@ejsR
    pouvoir: p@e/vwaR -> p@ejsR
    revoir: R@a/vwaR -> R@ajsR
    devoir: pv@a/vwaR -> pv@ajsR

## 21. prefix `em` -- keys (16, 18, 19) = `-jkd`

forms: `em`(k=1), `em[me|pe]·`(k=2), `em[ba|bla|boî|bra|ma|pa|pha|pla|plâ|poi]·`(k=2), `em[be|blé|bra|braie|bé|bê|mé|mê|pie|pié|pre|pê]·`(k=2), `em[be|bra|bê|mè|mê|pe|pei|pie|pre|prei|pê]·`(k=2), `embar·`(k=2)
- score 1323.7, strokeFreqSaved 1461.2, keySimilarity -0.07 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.57; exception rate 3.9%; top categories: VER 82%, NOM 16%, ADJ 3%
- word exceptions 65 (freq 87.4)
- top exceptions: empêcher, empêché, embêter, empêchez, embêté, empêchée, embêtez, embellir, embêtait, empêchés
    emmène: @/mien -> miejkdn
    emmener: @/m@a/mRe/-l -> mRejkd/-l
    embrasse: @/svRas -> svRajskd
    embrasser: @/svRa/se/-l -> sejkd/-l
    emmenez: @/m@a/mRe/-k -> mRejkd/-k

## 22. prefix `vou` -- keys (2, 5) = `kv-` (shares with per)

forms: `vou`(k=1)
- score 1308.1, strokeFreqSaved 1308.1, keySimilarity 0.50
- attestedShare 1.00; exception rate 0.0%; top categories: VER 100%, ADJ 0%, NOM 0%
- word exceptions 0 (freq 0.0)
    voulais: v@e/mtie/-k -> kvmtie/-k
    voudrais: v@e/pvRie/-k -> kpvRie/-k
    voulait: v@e/mtie -> kvmtie
    voulu: v@e/mt@i -> kvmt@i
    vouloir: v@e/mtwaR -> kvmtwaR
    voudrait: v@e/pvRie -> kpvRie

## 23. suffix `ture` -- keys (5, 20, 25) = `v-tm`

forms: `ture`(k=1), `·[a|ba|bla|ca|che|cia|cla|cri|cul|da|dra|fac|fai|fec|fi|frac|ga|ge|ggia|gia|gna|la|lec|ma|me|mma|ni|nia|plan|pos|pul|punc|ra|ri|rri|sla|ssa|ssi|struc|ta|tec|ti|tra|truc|van|ven|ver|vol]ture`(k=2), `·[chi|cros|cu|di|fras|gi|gis|gri|gé|i|llé|lo|ly|men|mo|o|ou|per|pro|pé|ri|sa|sci|sin|ti|to|trou|tté|vi]rature`(k=3)
- score 1293.0, strokeFreqSaved 1313.0, keySimilarity 0.37 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.81; exception rate 0.0%; top categories: NOM 99%, ADJ 1%
- word exceptions 0 (freq 0.0)
    voiture: vwa/t@iR -> vwatm
    nature: mRa/t@iR -> vmRatm
    nourriture: mR@e/Ri/t@iR -> vmR@etm
    voitures: vwa/t@iR/-s -> vwatm/-s
    couverture: k@e/vieR/t@iR -> kv@etm
    peinture: paie/t@iR -> pvaietm

## 24. prefix `ou` -- keys (2, 16, 17) = `k-js`

forms: `ou`(k=1), `ou[bli|blie|blii|gan|lé|ra|ro|ti|tra|tran|tre|ver|vri|ï]-{vRij}·`(k=2)
- score 1291.7, strokeFreqSaved 1306.7, keySimilarity 0.20 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.18; exception rate 0.0%; top categories: VER 82%, NOM 12%, ADJ 6%
- word exceptions 0 (freq 0.0)
    oublié: @e/svmtij/e -> ejkd
    oublie: @e/svmti -> svmtijkd
    oublier: @e/svmtij/e/-l -> ejkd/-l
    ouvrir: @e/vRiR -> vRijkdR
    ouvrez: @e/vRe -> vRejkd
    ouvert: @e/vieR -> viejkdR

## 25. prefix `ve` -- keys (2, 5) = `kv-` (shares with per)

forms: `ve`(k=1)
- score 1264.2, strokeFreqSaved 1264.2, keySimilarity 0.50
- attestedShare 0.35; exception rate 0.0%; top categories: VER 95%, NOM 3%, ADJ 3%
- word exceptions 0 (freq 0.0)
    venir: v@a/mRiR -> kvmRiR
    venez: v@a/mRe -> kvmRe
    venu: v@a/mR@i -> kvmR@i
    venue: v@a/mR@i/-j -> kvmR@i/-j
    venus: v@a/mR@i/-s -> kvmR@i/-s
    venait: v@a/mRie -> kvmRie

## 26. prefix `cou` -- keys (2, 17, 19) = `k-sd`

forms: `cou`(k=1), `cou[cha|che|doy|dri|illo|le|leu|li|ma|pa|ra|ro|rrié|rrou|si|ssi|te|tu|vai|ven|ver]-{p°,vRi}·`(k=2)
- score 1238.1, strokeFreqSaved 1283.4, keySimilarity 0.61
- attestedShare 0.51; exception rate 1.3%; top categories: NOM 52%, VER 38%, ADJ 10%
- word exceptions 7 (freq 25.3)
- top exceptions: courrier, courriers, coucherais, coucherait, couriez, coucheraient, courriez
    courant: k@e/R@ -> kR@sd
    coucher: k@e/pme/-l -> kpmesd/-l
    courage: k@e/RaZ -> kRasdZ
    couleur: k@e/mt@R -> kmt@sdR
    couteau: k@e/tae -> ktaesd
    courir: k@e/RiR -> kRisdR

## 27. prefix `sou` -- keys (11, 17, 18) = `@sk`

forms: `sou`(k=1), `sou[bre|ffle|ffre|le|pe|que|ve]-{t}·`(k=2), `sou[ba|bre|da|dai|doy|ffle|fflè|ffre|ffri|la|le|li|lè|me|mi|pe|pi|pè|que|ri|ta|te|ti|ven|vien|vla]-{t°,v°}·`(k=2)
- score 1237.3, strokeFreqSaved 1314.1, keySimilarity 0.27 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.69; exception rate 1.5%; top categories: VER 55%, NOM 26%, ADV 15%
- word exceptions 10 (freq 41.8)
- top exceptions: souris, souriez, souris, soufflerie, soufflerai, soumettez, souffririez, souter, souffreteux, soufflerez
    souviens: s@e/vRwaie/-k -> vRw@aiesk/-k
    souvent: s@e/v@ -> v@sk
    souvenez: s@e/v@a/mRe -> mR@esk
    souffrir: s@e/kpRiR -> kpR@iskR
    sourire: s@e/RiR -> R@iskR
    souvenirs: s@e/v@a/mRiR/-s -> mR@iskR/-s

## 28. suffix `mi` -- keys (13, 21, 25) = `iRm`

forms: `mi`(k=1), `·[dor|ga|la|na|nne|ri|ta|té]mi`(k=2)
- score 1180.4, strokeFreqSaved 1190.5, keySimilarity 0.75
- attestedShare 0.07; exception rate 2.5%; top categories: NOM 81%, ADJ 12%, PRE 6%
- word exceptions 2 (freq 0.0)
- top exceptions: emmi, hémi
    ami: a/mi -> aiRm
    amis: a/mi/-s -> aiRm/-s
    amie: a/mi/-j -> aiRm/-j
    parmi: paR/mi -> paiRm
    ennemi: ie/mR@a/mi -> ieRm
    amis: a/mi/-s -> aiRm/-s

## 29. prefix `es` -- keys (7, 11, 19) = `t@d`

forms: `es`(k=1), `es[bi|ca|cam|car|cha|cla|co|comp|cor|cri|cro|cu|gour|pa|pe|pi|pin|pio|piè|pla|pé|qui|quin|ta|tam|tan|thé|ti|to|tom|tou|tour|tra|tran|tro|tu|tur]·`(k=2), `escro[bi|blish|ce|dian|fi|ga|la|ma|me|mo|mou|nne|o|pi|po|que|ran|re|sio|te|ti|to|va]-{p°}·`(k=3)
- score 1162.6, strokeFreqSaved 1223.2, keySimilarity 0.03 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.62; exception rate 4.7%; top categories: NOM 61%, VER 36%, ADJ 4%
- word exceptions 34 (freq 35.6)
- top exceptions: espérais, espérait, espériez, espionnait, espionnais, espéraient, esclandre, escamoté, espérerais, estimant
    espère: ies/pieR -> pt@iedR
    esprit: ies/pRi -> ptR@id
    espèce: ies/pies -> pt@iesd
    espoir: ies/pwaR -> ptw@adR
    espace: ies/pas -> pt@asd

## 30. prefix `trou` -- keys (7, 16, 17) = `t-js`

forms: `trou`(k=1), `trou[ba|du|fi|illo|ve]·`(k=2)
- score 1126.9, strokeFreqSaved 1136.9, keySimilarity 0.40 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.92; exception rate 0.0%; top categories: VER 96%, NOM 3%, ADJ 2%
- word exceptions 0 (freq 0.0)
    trouvé: tR@e/ve -> vtejs
    trouver: tR@e/ve/-l -> vtejs/-l
    trouvez: tR@e/ve/-k -> vtejs/-k
    trouvée: tR@e/ve/-j -> vtejs/-j
    trouvera: tR@e/v@a/Ra -> tRajs
    trouverai: tR@e/v@a/Re/-t -> tRejs/-t

## Sibling pairs (candidateSim >= FAMILY_LINK_SIM, out of scope for v1)

- in ~ im (sim 1.00)
- e ~ ai (sim 1.00)
- teur ~ ture (sim 0.67)
- ou ~ cou (sim 0.67)
- cou ~ sou (sim 0.67)
- pou ~ cou (sim 0.67)
- vou ~ cou (sim 0.67)
- der ~ er (sim 0.67)
- pou ~ vou (sim 0.67)
- pou ~ ou (sim 0.67)
- pou ~ sou (sim 0.67)
- vou ~ ou (sim 0.67)
- vou ~ sou (sim 0.67)
- ou ~ sou (sim 0.67)

## Variant rivals (merged spelling-variant anchors vs their parts, U3b)

- `ae|ai|aî|e|ei|he|hé|oe|é|éh` (parts é, e, hé, ai; new conflict freq 5.5); merged score None vs main 0: **apart**
    merged forms: ae|ai|aî|e|ei|he|hé|oe|é|éh, é[cchy|chi|cri|crie|di|ffi|gri|gui|li|ly|mi|nni|pi|qui|ri|ry|si|thi|thy|ti|tri|ty|vi]·, é[ba|bah|bra|ca|cha|cla|cra|ffa|ga|gra|ja|la|loi|ma|na|pa|qua|ra|ta|tha|troi|va]·, é[blou|bou|brou|chou|choue|cou|crou|dou|gou|mou|pou|prou|ssou|tou]·, é[bran|chan|den|fflan|glan|lan|man|mmen|pan|pen|ssen|tam|tan|ten|tran|van|ven]·, é[bu|clu|cu|du|fflu|ffu|lu|mu|nu|plu|pu|ru|tu]·; main forms: é, é[chi|cri|crie|di|gri|li|ly|mi|pi|qui|ri|ry|thi|thy|ti|tri|ty|vi]·, é[ba|bah|ca|cha|cla|cra|ga|gra|ja|la|loi|ma|na|pa|qua|ra|ta|tha|troi|va]·, é[blou|bou|brou|chou|choue|cou|crou|dou|gou|mou|pou|prou|tou]·, é[bu|clu|cu|du|lu|mu|nu|plu|pu|ru|tu]·, é[bran|chan|den|glan|lan|man|pan|pen|tam|tan|ten|tran|van|ven]·
- `tai|taie|taient|tais|tait|tet|têt` (parts tait, tais, taient, tet; new conflict freq 0.0): **outOfReach**
- `a|ah|ha|hah|hâ|â` (parts a, ha, â, hâ, ah; new conflict freq 7.6); merged score None vs main 0: **apart**
    merged forms: a|ah|ha|hah|hâ|â, a[bi|bri|by|bî|ccli|ci|cqui|cri|cry|ddi|di|ffi|ffli|ffri|fi|fri|gi|gri|gui|li|lli|mi|my|myg|nhy|ni|nni|nnih|ny|pi|ppli|ppri|qui|ri|rri|ssi|ssy|sy|ti|tti|ttri|ty|vi|xi|zi|zy|ï]·, a[ban|fflan|ffran|gran|lam|lan|len|lham|man|men|ppren|ran|ren|rran|scen|ssem|ssen|tten|van|ven]·, a[che|ge|le|lle|me|ne|nne|pe|ppe|ppre|que|te|tte|ve|vre]·, a[a|ba|bba|boie|bra|bâ|ca|cca|ccla|cha|da|djoi|dra|droi|ffa|ga|ggra|gla|gra|la|lla|ma|mha|na|nna|pa|pha|pla|ppa|ppâ|qua|ra|ria|rra|sia|ssa|ssoi|ta|tha|tra|tta|ttra|va|via|voi|wa|ya]·, aé[a|an|cia|cie|cé|di|en|fle|go|lec|lio|llu|lu|ma|men|mo|na|ni|no|nu|nua|o|ou|qua|qui|ra|ri|rin|ro|ros|rri|ssi|ta|ti|ty|tyl]·; main forms: a, a[ban|fflan|ffran|gran|lam|lan|len|lham|man|men|ppren|rran|scen|ssem|ssen|tten|van|ven]·, a[bri|by|bî|ccli|ci|cqui|cri|cry|ddi|di|ffi|ffli|ffri|fi|fri|gi|gri|gui|li|lli|mi|my|myg|nhy|ni|nni|nnih|ny|pi|ppli|ppri|qui|rri|ssi|ssy|sy|tti|ttri|ty|vi|xi|zi|zy]·, a[che|ge|le|lle|me|nne|pe|ppe|ppre|que|te|tte|ve]·, a[ba|bba|boie|bra|bâ|ca|cca|ccla|cha|da|djoi|dra|droi|ffa|ga|ggra|gla|gra|la|ma|mha|na|nna|pa|pha|pla|ppa|ppâ|pâ|qua|ra|ria|rra|sia|ssa|ssoi|ta|tha|tra|tta|ttra|va|via|voi|ya]·, a[bai|be|bê|chè|cquie|dre|ffai|grai|gre|gue|le|llai|lle|llè|mai|me|mè|nne|pai|ppe|pprê|rai|rrai|rrê|se|ssai|sse|ssè|tte|ttei|vè]·
- `le|leh|ler|lers|ller|llé|llée|lée` (parts ler, ller, llée, lée, llé; new conflict freq 14.6); merged score None vs main 0: **apart**
    merged forms: le|leh|ler|lers|ller|llé|llée|lée, ·[ce|de|ge|me|mme|pe|ppe|que|rre|se|sse|te|ve]ler, ·[bo|co|do|ffo|fo|geo|gno|go|jo|mo|no|o|pau|po|ro|so|sso|to|trô|vo]lé, ·[bu|cu|du|gu|llu|lu|mu|nnu|pu|su|tu|vu]lez, ·[a|ba|ca|da|fa|ga|gna|nha|ra|ssa|ta|va|voi]ller, ·[a|am|an|cap|ccu|for|gra|i|ja|ni|nna|no|pi|ssi|ti|tri]puler; main forms: ler, ·[ce|de|ge|me|mme|pe|ppe|que|rre|se|sse|te|ve]ler, ·[bo|co|do|ffo|fo|geo|gno|go|jo|no|o|pau|po|so|sso|to|trô|vo]lé, ·[bu|cu|du|gu|llu|lu|mu|nnu|pu|su|tu|vu]lez, ·[a|ba|ca|da|fa|ga|gna|nha|pa|ra|ssa|ta|va|voi]ler, ·[a|am|an|cap|ccu|for|gra|i|ja|ni|nna|no|pi|ssi|ti|tri]puler
- `am|an|ant|em|en|ench|enh|ham|han|hen` (parts en, em, an, am, han; new conflict freq 3.0); merged score None vs main 0: **apart**
    merged forms: am|an|ant|em|en|ench|enh|ham|han|hen, en[bran|cen|chan|clen|fan|gen|gran|jam|man|plan|san|ten]·, em[che|ge|gre|le|me|pe|ple|re|se|tre|ve]·, em[a|ba|bla|boî|bra|ca|cloî|da|dia|fa|fla|foi|ga|goi|gra|joi|la|ma|pa|pha|pla|plâ|poi|ra|sa|ta|thra|tr'a|tra|vah]·, en[bi|bri|chi|cli|cy|di|dri|fi|foui|gli|gui|i|ky|li|mi|phi|phy|pi|pli|pri|qui|ri|ti|tih|vi|vie|zy]·, en[be|bra|bê|cai|ce|chaî|cie|dê|fe|grai|lai|lè|mè|mê|nei|pe|pre|prei|pè|pê|quê|ra|se|sei|te|tiè|tr'ai|trai|traî|tê|ve]·; main forms: en, en[cen|chan|clen|fan|gen|gran|jam|san|ten]·, en[che|ge|gre|le|re|se|te|tre|ve]·, en[a|ca|cloî|dia|fa|fla|foi|ga|gra|joi|la|ra|sa|ta|toi|tr'a|tra|va|vah]·, en[chi|cli|cy|di|fi|foui|i|li|qui|ri|ti|vi|vie|zy]·, en[cai|ce|chaî|dê|fe|grai|lai|lè|nei|quê|ra|se|sei|te|tiè|tr'ai|trai|traî|tê|ve]·
- `ve|ver|wé` (parts ver; new conflict freq 0.1); merged score None vs main 0: **apart**
    merged forms: ve|ver|wé, ·[che|chi|cur|di|li|ner|nno|pa|pprou|qui|ra|ri|rri|ser|ssi|ti|tra|trou|vi|xca]-{l°}vé, ·[che|le]ver; main forms: ver, ·[che|chi|cur|di|li|ner|nno|pa|pprou|qui|ra|ri|rri|ser|ssi|ti|tra|trou|vi|xca]-{l°}vé, ·[che|le]ver
- `au|aul|ho|hos|o|oi` (parts o, ho; new conflict freq -0.0): **outOfReach**
- `bai|be` (parts be; new conflict freq 0.0): **outOfReach**
- `mai|maî|me|mei|mes|mè|mê` (parts me, mai, mê; new conflict freq 0.0): **outOfReach**
- `bom|bon` (parts bon, bom; new conflict freq 0.2): **outOfReach**
- `ma|mah|mâ` (parts ma, mâ, mah; new conflict freq 0.5); merged score None vs main 0: **apart**
    merged forms: ma|mah|mâ, ma[a|ca|ccha|cha|chi|chia|chin|cho|cin|ckin|cra|cro|cros|cu|cum|cé|da|de|dri|dré|es|fio|ga|gen|ghré|gi|gis|gna|gni|gno|gné|gou|illo|jes|jo|jor|la|lai|lan|len|lha|lheu|lho|li|lin|llar|llé|lo|lé|ma|me|mmec|mmi|mmo|na|nha|ni|nia|nie|nié|nne|nni|no|noeu|nou|nu|nue|nus|nué|né|o|ppe|que|qui|ra|rau|raî|ri|ria|rie|rin|rio|ro|rou|rro|ry|ré|so|ssa|ssi|ta|te|ter|thu|thé|ti|toi|tra|tri|tu|té|xi|yo|za|zur|ço|ï]·, made[ar|bi|bri|ca|can|cha|chou|ché|cli|co|con|cou|cre|cu|da|di|dic|do|droi|fac|fi|gan|ge|gra|jua|la|li|lle|ma|mi|mo|moi|mou|mé|na|ni|nne|o|plas|po|pu|qui|ra|re|reau|reu|ri|ria|ro|sa|si|ten|ti|to|tos|tra|tri|vau|vra|vri|vé|é]-{fEs}·, malheureu[bi|ce|co|dé|la|le|li|mi|ne|né|se|tai|ti|tio|treu|tu]-{k°}·, mani[ché|cieu|cou|cu|fes|fi|gan|gno|jua|li|lle|lo|ma|mi|mo|na|ne|och|pu|to|vau|ve]·; main forms: ma, ma[ca|ccha|cha|chi|chia|chin|cin|ckin|cra|cro|cros|cu|cum|cé|da|de|dri|dré|es|fio|ga|gen|ghré|gi|gis|gna|gni|gno|gné|gou|illo|jes|jo|jor|la|lai|lan|len|lha|lheu|lho|li|lin|llar|llé|lo|lé|ma|me|mmec|mmi|mmo|na|nha|ni|nia|nie|nié|nne|nni|no|noeu|nou|nu|nue|nus|nué|né|o|ppe|que|qui|ra|rau|raî|ri|ria|rie|rin|rio|ro|rou|rro|ry|ré|so|ssa|ssi|ta|te|ter|thu|thé|ti|toi|tra|tri|tu|té|xi|yo|za|zur|ço|ï]·, made[ar|bi|bri|ca|can|cha|chou|ché|cli|co|con|cre|cu|da|di|dic|do|droi|fac|fi|gan|ge|gra|jua|la|li|lle|ma|mi|mo|moi|mou|na|ni|nne|o|plas|po|pu|qui|re|reau|reu|ri|ria|ro|sa|si|ten|ti|to|tos|tra|tri|vau|vra|vri|vé|é]-{fEs}·, malheureu[bi|ce|co|dé|la|le|li|mi|ne|né|se|tai|ti|tio|treu|tu]-{k°}·, mani[ché|cieu|cu|fes|fi|gan|gno|jua|li|lle|lo|ma|mi|mo|na|ne|och|pu|to|vau|ve]·
- `van|vant|vent` (parts vant, vent; new conflict freq 0.0): **outOfReach**
- `ar|har` (parts ar, har; new conflict freq 0.1): **outOfReach**
- `llon|lon` (parts lon, llon; new conflict freq 0.6): **outOfReach**
- `ce|sce|se` (parts se, ce; new conflict freq 0.0); merged score 2451 vs main 2016: **fused**
    merged forms: ce|sce|se, se[con|cou|coue|crè|cré|cun|gue|mai|mes|mon|na|pen|rei|ri|rin|ven]·; main forms: se, se[con|cou|coue|crè|cré|cun|gue|mai|mes|mon|rei|ri|rin|ven]·
- `rette|rrette|rète|rête` (parts rette; new conflict freq 0.0): **outOfReach**
- `fan|fang|fant|fends|fens|ffant|phant` (parts ffant; new conflict freq 0.0): **outOfReach**
- `main|men|min` (parts main, min; new conflict freq 0.0): **outOfReach**
- `ra|rai|re|rei|rè|rê` (parts rai, rê, re; new conflict freq 0.0): **outOfReach**
- `son|zon` (parts son, zon; new conflict freq 0.0): **outOfReach**
- `sa|sah` (parts sa; new conflict freq 0.0); merged score None vs main 0: **apart**
    merged forms: sa|sah, sa[a|ba|bba|bli|blo|bo|bor|bou|bre|bé|cca|ccha|ccu|cer|cra|cri|cris|cré|ddu|di|do|fa|ga|gi|la|lai|le|li|lo|lu|lue|lé|ma|me|miz|mo|mou|na|nhé|ni|ou|pa|per|pi|po|pris|ra|rra|rru|ssa|ta|te|ti|tia|to|tra|tu|tur|va|van|ve|vo|vou|voy|xi|xo]-{bo,kR°,tis}·, sa[cris|pris|tis]·, salo[ci|cé|do|fi|fie|fii|fra|li|lli|ma|men|ni|pe|pho|que|ra|reu|ri|ro|sso|ta|tai|ti|to|za]·; main forms: sa, sa[ba|bba|bli|blo|bo|bor|bou|bre|bé|cca|ccha|ccu|cer|cra|cri|cris|cré|ddu|di|do|fa|ga|gi|la|lai|le|li|lo|lu|lue|lé|ma|me|miz|mo|mou|na|nhé|ni|ou|pa|per|pi|po|pris|ra|rra|rru|ssa|ta|te|ti|tia|to|tra|tu|tur|va|van|ve|vo|vou|voy|xi|xo]-{bo,kR°,tis}·, sa[cris|pris|tis]·, salo[ci|cé|do|fi|fie|fii|fra|li|lli|ma|men|ni|pe|pho|que|ra|reu|ri|ro|sso|ta|tai|ti|to|za]·
- `voir|voire` (parts voir; new conflict freq 0.0): **outOfReach**
- `vou|voue|voû|woo` (parts vou; new conflict freq 0.0): **outOfReach**
- `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` (parts sser, cer, ser, sé, cé, cée, ssée; new conflict freq 89.0); merged score None vs main 0: **apart**
    merged forms: cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé, ·[cen|den|en|ffen|gan|lan|man|men|mmen|nan|nnan|pen|quen|ren|rren|sen|ten|van|xpan]cé, ·[a|ba|bra|ca|cha|cra|fa|ffa|ga|gla|gna|illa|la|lia|ma|na|pa|pia|pla|ra|roi|rra|ta|va]sser, ·[er|mmer|per|ver]ser, ·[bai|dre|fe|gre|lai|ppre|pre|re]sser, ·[ba|co|com|cu|do|flu|ni|se|te]mmencer; main forms: sser, ·[a|ba|bra|ca|cha|cra|ga|gna|illa|la|ma|na|pa|ra|roi|rra|ta|va]sser, ·[bai|dre|fe|gre|lai|ppre|pre|re]sser, ·[ba|ca|de|pe|te|tre]rrasser
- `ssé|sée` (parts ssé; new conflict freq 0.0): **outOfReach**
- `mau|mo|moh` (parts mo, mau; new conflict freq 0.1): **outOfReach**
- `man|mand|mant|ment|ments|mmant|mment` (parts ment, mment, mant, mand, man; new conflict freq 1.4); merged score 8169 vs main 8027: **fused**
    merged forms: man|mand|mant|ment|ments|mmant|mment, ·[a|ai|be|ble|boie|bre|ca|ce|cha|che|chi|chisse|ci|cie|claffe|cle|cre|cré|cu|cé|da|de|di|die|doie|dre|droie|du|dé|dû|ffle|ffre|fie|fle|for|ga|ge|gle|gne|gre|gré|gu|gue|ille|la|le|li|lla|lle|loie|lu|lé|lû|ma|me|moie|mé|ne|ni|nie|nna|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|ro|rre|rré|ré|sa|sce|scie|se|sias|ssa|sse|ssoie|ssuie|ssé|sul|sé|ta|te|ti|tie|toie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|zaie|é]ment, ·[a|ac|bi|blo|bus|ca|chan|cho|ci|cinc|co|cri|cru|crè|da|des|dia|dio|droi|fai|fes|fflo|frou|gen|glan|glou|gno|ille|illo|jec|jus|li|llo|lo|ma|men|mo|nes|nnê|noî|par|pen|pi|plè|po|ppar|ppoin|qua|quin|què|rec|ren|roi|rrec|sen|so|ssau|sso|strai|ten|ti|tinc|tis|troi|tui|van|ver|vro|vê|xper|zo|ïs]-{pOR}tement, ·[bi|bli|bri|chi|ci|cri|di|dri|ffi|fi|gi|gli|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|pli|qui|ri|rri|sci|si|ssi|sti|thi|ti|tri|tti|vi|vri|xi|y|ï]caments, ·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|ppa|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|voua|xa|za|ça]blement, ·[ai|bai|be|chai|chaî|chè|cie|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|me|miè|mmai|mè|mê|nai|ne|niai|niè|nnai|nne|nnê|piè|plai|plè|prê|què|rai|re|rei|rie|rrai|rè|sai|scè|se|sei|siè|ssai|ssiè|strai|sè|tai|te|tie|tiè|trai|traî|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]tement⟨·[a|ai|be|ble|boie|bre|ca|ce|cha|che|chi|chisse|ci|cie|claffe|cle|cre|cré|cu|cé|da|de|di|die|doie|dre|droie|du|dé|dû|ffle|ffre|fie|fle|for|ga|ge|gle|gne|gre|gré|gu|gue|ille|la|le|li|lla|lle|loie|lu|lé|lû|ma|me|moie|mé|ne|ni|nie|nna|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|ro|rre|rré|ré|sa|sce|scie|se|sias|ssa|sse|ssoie|ssuie|ssé|sul|sé|ta|te|ti|tie|toie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|zaie|é]ment⟩; main forms: ment, ·[be|ble|boie|bre|ca|ce|che|chi|chisse|ci|cie|claffe|cle|cre|cré|cu|cé|de|di|die|doie|dre|droie|du|dé|dû|ffle|ffre|fie|fle|ge|gi|gle|gne|gre|gré|gu|gue|ille|la|le|li|lle|loie|lu|lé|lû|ma|me|mmé|moie|mé|ne|ni|nie|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|rre|rré|ré|sce|se|sse|ssoie|ssuie|ssé|sé|ta|te|ti|tie|toie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|zaie|é]ment, ·[a|ac|bi|blo|bus|ca|chan|cho|ci|cinc|co|cri|cru|crè|da|des|dia|dio|droi|fai|fes|fflo|frou|gen|glan|glou|gno|ille|illo|jec|jus|li|llo|lo|ma|men|mo|nes|nnê|noî|par|pen|pi|plè|po|ppar|ppoin|qua|quin|què|rec|ren|roi|rrec|sen|so|ssau|sso|strai|ten|ti|tinc|tis|troi|tui|van|ver|vro|vê|xper|zo|ïs]-{pOR}tement, ·[bi|bli|bri|chi|ci|cri|di|dri|fi|gi|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|pli|qui|ri|rri|sci|si|ssi|sti|thi|ti|tri|tti|vi|vri|xi|y|ï]caments, ·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|voua|xa|za|ça]blement, ·[ai|bai|be|chai|chaî|chè|cie|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|me|miè|mmai|mè|mê|nai|ne|niai|niè|nnai|nne|nnê|piè|plai|plè|prê|què|rai|re|rei|rie|rrai|rè|sai|scè|se|sei|siè|ssai|ssiè|strai|sè|tai|te|tie|tiè|trai|traî|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]tement
- `pro|proh|prô` (parts pro; new conflict freq 0.0); merged score 2748 vs main 2744: **fused**
    merged forms: pro|proh|prô, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·, profe[ne|sse|ssio|sso|tte|ttri]·, pro[chi|di|fi|i|li|phy|pi|vi]·; main forms: pro, pro[blé|ce|cré|crée|cé|fé|gre|gé|lé|phé|pé|sce|sé|thé|té|vé|é]·, proba[bi|ble|gan|ge|go|me|mma|mme|na|ï]·, pro[co|mo|no|po|ro|so|to|toh|vo]·, profe[ne|sse|ssio|sso|tte|ttri]·, pro[chi|di|fi|li|phy|pi|vi]·
- `bien|byen` (parts bien; new conflict freq 0.0): **outOfReach**
- `tture|tur|ture` (parts ture; new conflict freq 0.0): **outOfReach**
- `tir|tire|ttir|tyr|tyre` (parts tir; new conflict freq 4.1): **outOfReach**
- `tra|trah|trâ` (parts tra; new conflict freq 0.0): **outOfReach**
- `vail|vaille|vailles` (parts vail; new conflict freq 0.0): **outOfReach**
- `nhir|nir|nnir` (parts nir, nnir; new conflict freq 0.0): **outOfReach**
- `ai|aî|e|ei|hai|he|hê|é` (parts e, ai, é, he; new conflict freq 0.1); merged score None vs main 3654: **apart**
    merged forms: ai|aî|e|ei|hai|he|hê|é, ai[che|de|gle|gre|le|me|nne|rre]·, e[ssa|ssai|ssaie|xce|xcré|xpre|xte|xtrê]·, e[xclu|xcu|xsu]·, e[ffi|ffri|gri|gui|nni|xci|xpi|xpie|xpli|xpri]·, e[cclé|dé|ffé|llé|xce|xcré|xcé|xplé|xpé|xtré|xté]·; main forms: e, e[ssa|ssai|ssaie|xce|xcré|xpre|xte|xtrê]·, e[xclu|xcu|xsu]·, e[ffi|ffri|xci|xpi|xpie|xpli|xpri]·, e[cclé|ffé|xce|xcré|xcé|xplé|xpé|xtré|xté]·, extra[ce|con|cor|ga|lu|ma|or|po|rou|sen|si|sys|ta|te|ti|tri|trii|va|ver|véh]·
- `der|dé|dée` (parts der, dée, dé; new conflict freq 52.2); merged score None vs main 3497: **apart**
    merged forms: der|dé|dée, ·[an|ba|bar|bau|blar|bon|bro|ca|car|cca|ccor|chan|char|chi|ci|con|cor|en|fau|ffau|fon|ga|gan|gar|gnar|gon|gour|gra|gui|illa|la|lan|lar|li|llar|lli|man|mar|mer|mi|mma|mman|mmar|mmo|na|nar|nau|ni|non|o|par|pen|pi|qui|ra|rau|san|sar|scen|si|ssou|ssua|sua|va|vau|vi|xtra|zar]-{bOR,se}dez, ·[cé|ssé|sé|xcé]der; main forms: der, ·[an|ba|bar|bau|blar|bon|ca|car|cca|ccor|chan|char|ci|con|cor|cé|en|fau|ffau|gar|gnar|gon|gour|gra|gui|illa|la|lan|lar|li|llar|man|mar|mer|mi|mman|mmar|mmo|na|nar|nau|non|o|par|pen|pi|qui|ra|rau|san|sar|scen|si|ssou|ssua|ssé|sua|sé|va|vau|xtra|zar]-{bOR}dez
- `mi|mie|mis|mmies|mmis|mmy|my` (parts mi, mie, mis; new conflict freq 0.9): **outOfReach**
- `au|aux|hau|haut|ho|hô|o|oh|ô` (parts au, o, ho, hô, hau; new conflict freq 34.4); merged score None vs main 0: **apart**
    merged forms: au|aux|hau|haut|ho|hô|o|oh|ô, au[a|ber|bi|bli|bu|bé|ca|cca|ccul|cé|da|di|dien|dieu|dio|do|don|ffen|ffi|ffri|ffus|gi|gu|gus|jour|li|llan|lo|lym|lé|ma|mar|me|mer|mi|mo|mé|mô|na|ni|nni|nnê|nnête|no|nu|né|pa|pi|pio|po|ppi|ppo|ppor|ppre|ppri|pu|pus|pé|ra|ran|re|rei|ri|rien|ros|rri|ryc|ré|sa|sci|se|ssa|ssi|ta|tai|tar|te|then|to|toch|tom|top|tore|tos|tre|tri|tu|va|ver|vi|vo|vu|xe|xi]-{ky,no}·, o[bu|cclu|ccu|cu|gu|nu|pu|tu|vu]·, opé[a|bio|bri|cen|che|ci|cia|cie|cieu|co|con|cra|cré|cu|cui|da|des|di|dé|fi|fo|gar|ge|ges|gi|gra|gui|gé|i|li|lle|llo|llos|lo|ma|mi|mo|mu|mé|ne|niâ|no|ny|o|pa|phi|pho|pi|plas|por|pro|pu|ra|ri|rio|ris|rou|ré|sa|se|si|sio|su|sub|sug|sur|ta|te|thé|ti|tio|to|tu|té|ve|vi|zon|é]-{ga,zi}·, hono·⟨au|aux|hau|haut|ho|hô|o|oh|ô⟩; main forms: au, au[ber|bu|bé|cu|da|di|dien|dio|gu|gus|jour|lo|mô|pa|re|ri|ré|ssi|tar|then|to|toch|tom|top|tore|tos|tre|tri|ver|xe|xi]·, auto[bio|cen|che|cieu|co|con|cra|cré|cu|cui|da|des|di|dé|fi|fo|ge|ges|gui|gé|li|ma|mi|mo|mu|mé|ne|no|o|pi|plas|por|pro|pu|ra|re|ri|rou|ré|sa|si|su|sub|sug|sur|ti|tio|to|vi|é]·, autori[bi|ci|cla|ffi|fi|fé|ges|gra|gu|my|nan|ni|pul|que|rec|ro|sa|sci|se|ser|sis|su|ta|ter|ti|tis|tra|trui|ttoy|vei]-{tRyk}·
- `d'hui|duit` (parts duit; new conflict freq 0.0): **outOfReach**
- `fa|fe|fei|fâ|pha` (parts fa, fâ, pha; new conflict freq 0.2): **outOfReach**
- `pou|pu` (parts pou; new conflict freq 0.2): **outOfReach**
- `pa|pei|pâ` (parts pa, pâ; new conflict freq 0.2); merged score None vs main 0: **apart**
    merged forms: pa|pei|pâ, pa[chin|chy|ci|cka|co|ddo|e|ga|gaie|gay|gi|illa|illar|ille|illè|kis|la|lan|laz|le|lef|les|li|limp|lin|lla|llia|lu|ly|lé|moi|na|ne|ni|no|non|nur|né|o|pa|pe|pi|po|pou|pri|py|pè|que|ra|rai|ram|ran|rap|ras|raî|re|rei|ren|res|ri|ro|roi|rrai|rri|ru|ré|sio|ssa|sse|ssi|ssio|ssé|ta|tau|tchou|te|ter|teu|tho|thé|ti|tie|tien|toi|tou|tri|tro|trou|tte|tu|va|vlo|voi]-{sjo,vi}·, para[be|bo|che|chu|chè|cé|de|di|do|ffi|gou|gua|llè|llé|lo|ly|lym|ma|mi|mé|no|nor|né|phar|plé|re|si|thy|to]·, pa[co|ddo|go|lo|no|o|po|ro|sio|ssio|tau|tho|tro]·, pacifi[ca|lo|ma|na|né|que]·; main forms: pa, pa[chin|chy|ci|cka|co|ddo|e|ga|gaie|gay|gi|illa|illar|ille|illè|kis|la|lan|laz|le|lef|les|li|limp|lin|lla|llia|lu|ly|lé|na|ne|ni|no|non|nur|né|o|pa|pe|pi|po|pou|pri|py|pè|que|ra|rai|ram|ran|rap|ras|raî|re|rei|ren|res|ri|ro|roi|rrai|rri|ru|ré|sio|ssa|sse|ssi|ssio|ssé|ta|tau|tchou|te|ter|tho|thé|ti|tie|tien|toi|tou|tri|tro|trou|tte|va|vlo|voi]-{sjo,vi}·, para[be|bo|che|chu|chè|cé|de|di|do|ffi|gou|gua|llè|llé|lo|ly|lym|ma|mi|mé|no|nor|né|phar|plé|re|si|thy|to]·, pa[co|ddo|go|lo|no|o|po|ro|sio|ssio|tau|tho|tro]·, pacifi[ca|lo|ma|na|né|que]·
- `cher|chée|scher|sher` (parts cher, chée; new conflict freq 14.4): **outOfReach**
- `trou|troue` (parts trou; new conflict freq 0.0): **outOfReach**
- `e|hi|hy|i|y|î` (parts i, hi, hy; new conflict freq 0.2); merged score None vs main 0: **apart**
    merged forms: e|hi|hy|i|y|î, i[ber|bis|bo|bé|ca|ce|cko|co|den|deu|dio|do|dra|drau|dro|drop|dros|dé|gié|gni|gno|gro|gua|ke|la|lle|lli|llo|llu|llus|llé|lo|lé|ma|mer|mi|mma|mmen|mmer|mmi|mmo|mmon|mmor|mmu|mmé|mé|na|nac|nad|nal|nap|nar|nau|ne|nemp|nen|nep|ner|nes|nex|nha|nhar|nhi|nhos|nhu|ni|nin|nner|nno|nnom|no|non|nor|nou|noub|nu|né|o|pa|pe|per|pere|pho|po|pos|ppo|pé|ra|ri|ro|ron|rra|rrai|rre|rrem|rres|rri|rro|rrup|rré|ru|sa|sla|slan|so|sra|ta|thy|ti|ver|voi|vro]·, ima[bi|cri|die|dy|ffi|gi|gli|gly|li|mi|ni|phy|pi|ppli|ppri|qui|ssi|thy|ti|tie|tri|vi|xpli|xpri|xy]·, immédia[bi|ci|gi|la|li|ller|ra|te|tio|tré]·, imagi[ca|cu|cé|fi|fie|gi|gio|le|li|ma|mi|na|nai|ne|nieu|pi|ro|sa|ta|ti|tu]·, immé[a|ba|bran|chan|con|cu|dia|ffa|ffi|flé|fra|ga|gi|gu|li|lé|mo|mor|mé|ni|nop|o|pa|pro|pui|ri|sis|so|tré|va|ver|vi|vo|vé]·; main forms: i, i[bo|bé|ca|ce|co|den|dio|do|dy|dé|gni|gno|gua|ke|lle|lli|llo|llu|llus|llé|lo|lé|ma|mi|mma|mmen|mmer|mmi|mmo|mmon|mmor|mmu|mmé|na|nac|nad|nal|nap|nar|nau|ne|nemp|nen|nep|ner|nes|nex|nha|nhar|nhi|nhos|nhu|ni|nin|nner|nno|nnom|no|non|nor|nou|noub|nu|né|pé|ra|ri|ro|rra|rrai|rre|rrem|rres|rri|rro|rrup|rré|sa|sla|slan|so|sra|ta|thy|ti|voi|vro]·, ima[bi|ci|die|ffi|gi|li|mi|ni|pi|ppli|ppri|ssi|ti|tie|tri|vi|xpli|xpri|xy]·, immédia[bi|gi|li|ra|te|tio]·, imagi[ca|cu|fi|fie|gi|gio|le|li|ma|mi|na|nai|ne|nieu|sa|ta|ti|tu]·, immé[a|ba|bran|chan|con|cu|dia|ffa|ffi|flé|fra|ga|gi|gu|li|lé|mo|mé|o|pa|pro|pui|ri|sis|so|tré|va|ver|vi|vo|vé]·
- `pam|pan|pem|pen` (parts pen, pan, pam; new conflict freq 1.3): **outOfReach**
- `dan|dans|dant|dent` (parts dant, dent; new conflict freq 0.2): **outOfReach**
- `his|hys|is|isth` (parts his, is; new conflict freq 0.0): **outOfReach**
- `toir|toire|ttoir` (parts toire, toir, ttoir; new conflict freq 0.0): **outOfReach**
- `tion|tions` (parts tion, tions; new conflict freq 0.0): **outOfReach**
- `fee|fi|fie|phi|phy` (parts fi, phy, phi; new conflict freq 0.0): **outOfReach**
- `ni|nie|nies|nil|nis|nit|nni|nnie|nnies|nny` (parts nie, ni; new conflict freq 0.9): **outOfReach**
- `lom|lon|long|lum` (parts lon, lom; new conflict freq 0.0): **outOfReach**
- `tan|tang|tant|temps|tent|than|ttan|ttant|ttent` (parts tant, tan, tent, ttant; new conflict freq 0.0): **outOfReach**
- `pu|pue` (parts pu; new conflict freq 0.0): **outOfReach**
- `tain|teint|thain|tin|tinct|tins|tteint|ttin` (parts tin, tain; new conflict freq 1.3): **outOfReach**
- `ci|cie|cil|cis|cit|cy|si|sie|sil|sis|ssi|ssie|ssis|sy|tie` (parts ci, tie, cis, ssis, sie, cie; new conflict freq 0.4): **outOfReach**
- `llu|lu|lue|lus|lut` (parts lu; new conflict freq 0.0): **outOfReach**
- `pau|peau|po` (parts po, pau, peau; new conflict freq 0.1): **outOfReach**
- `lice|lis|lisse|llis|lysse` (parts lice, lis; new conflict freq 0.0): **outOfReach**
- `fain|ffin|fin|fins|phin` (parts fin, ffin; new conflict freq 0.0): **outOfReach**
- `la|lai|le|les|lè` (parts lai, le; new conflict freq 0.2): **outOfReach**
- `pa|pas|pat|ppa|ppât` (parts pa, pas, ppa; new conflict freq 1.2): **outOfReach**
- `du|due|dus` (parts du; new conflict freq 1.9): **outOfReach**
- `ree|ri|rie|ries|rii|ris|rit|rri|rrie|rril|rris|rry|ry|rye` (parts ri, rie, ry, rri; new conflict freq 1.3): **outOfReach**
- `ain|hin|im|in` (parts in, im; new conflict freq 0.0); merged score None vs main 3883: **apart**
    merged forms: ain|hin|im|in, in[bé|ce|clé|cré|dé|flé|fré|fé|gré|gé|pe|plé|pre|pré|pé|quié|sai|sé|te|tré|té|vé]·, im[cor|for|por]·, inté[ce|chi|ci|cro|cu|di|du|fec|fen|fi|for|fri|gra|gre|gri|li|llec|lli|lo|lé|ma|men|mi|ni|nia|nie|nieu|nio|nom|nou|né|o|pa|pen|pi|ra|re|ri|ria|rieu|rio|ré|sa|si|ssa|ssio|te|tec|ter|ti|té|vi|voy]·, im[bro|co|coh|do|flo|fo|plo|po|pro|so|to|tro|vio|vo]·, in[bi|bri|chi|ci|cli|cri|di|fi|fli|gui|pi|pli|pri|qui|si|ti|tri|vi]·; main forms: in, in[ce|clé|cré|dé|flé|fré|fé|gré|gué|gé|quié|sai|sé|te|tré|té|vé]·, in[chi|ci|cli|cri|di|fi|fli|gui|qui|si|ti|tri|vi]·, inté[ce|chi|ci|cro|di|du|fec|fen|fi|for|fri|gra|gre|gri|li|llec|lli|lo|lé|ma|mi|mon|nia|nie|nieu|nio|nom|nou|o|pa|pen|pi|ra|re|ri|rieu|rio|ré|si|ssa|te|tec|ter|té]·, in[cer|fer|ter|ver]·, infor[ma|me|mu|po|tu]·
- `cau|cho|coa|coh|cô|ko|quo` (parts cô, cau, quo, cho, coh, ko; new conflict freq 0.4): **outOfReach**
- `nnu|nue|nut` (parts nue, nnu; new conflict freq 0.0): **outOfReach**
- `moo|mou|mu` (parts mou; new conflict freq 0.0): **outOfReach**
- `rir|rire|rrir` (parts rir, rrir; new conflict freq 0.0): **outOfReach**
- `dau|dho|do` (parts do, dau; new conflict freq 0.3): **outOfReach**
- `ner|nez|nner|nnée|née|nées` (parts ner, nner, née, nnée; new conflict freq 52.2); merged score None vs main 0: **apart**
    merged forms: ner|nez|nner|nnée|née|nées, ·[ba|ber|bi|blo|bo|bor|boui|ca|car|chaî|chi|cho|ci|dam|di|do|dro|e|fa|ffo|fi|fo|ga|geo|gi|gno|go|gor|gre|gri|gé|illo|jeu|jour|li|llo|lo|me|mi|mo|o|pa|pho|pi|pio|pli|po|qui|ri|ro|ré|scer|sci|ser|si|sio|so|ssi|ssio|sso|sti|ta|ter|thé|ti|tio|to|traî|tri|tro|tti|tu|ver|vi|xo|ço]-{ko,tRe,tuR}né, ·[a|be|bo|bou|che|com|cri|de|do|ga|li|llan|llo|lo|lu|ma|po|ra|ré|sci|se|ssa|ta|ter|xter]giner, ·[four|jour|tour]ner, ·[ban|be|bi|bor|bou|cep|che|di|fa|fec|ges|le|lec|li|llu|lo|lu|lé|mi|or|pe|pi|poi|por|pre|pu|ri|si|ti|ven|vi|xcur]-{pRi}donner; main forms: ner, ·[ber|bi|bor|boui|ca|car|chaî|chi|ci|co|dam|di|fa|fi|fré|ga|gai|gi|gor|gre|gri|gé|jeu|jour|li|me|mi|mo|pa|pho|pi|pli|poui|qui|ri|ré|scer|sci|ser|si|ssi|sti|ta|ter|ti|traî|tri|tti|tu|ver|vi]-{tRe,tuR}né, ·[a|be|bo|bou|che|com|cri|de|do|ga|go|in|la|li|llan|llo|lo|lu|lé|ma|po|por|ra|ri|ré|sci|se|ssa|ta|ter|xter|xy]giner, ·[four|jour|tour]ner
- `nné|né` (parts né, nné; new conflict freq 1.2): **outOfReach**
- `ser|sée|zer|zé` (parts ser, sée, zer; new conflict freq 5.8); merged score None vs main 0: **apart**
    merged forms: ser|sée|zer|zé, ·[a|ba|bap|bi|bo|bé|ca|char|cia|co|cra|cré|cu|cé|da|do|dua|dé|for|ga|gi|gli|gné|go|gé|la|li|lia|lo|ma|mi|mmu|mo|mor|mé|na|ni|nna|no|né|or|pa|per|phi|phé|po|pro|qui|ra|ri|ria|rio|rro|sec|so|ssoi|ssu|sua|ta|ter|teu|ti|tia|to|tou|tra|tro|tu|tua|ty|té|va|ve|vi|via|vo|vé|xper|xtua|xua|ï]liser, ·[bu|clu|cu|du|ffu|fu|mu|xcu]sez⟨ser|sée|zer|zé⟩, ·[cro|lo|pho|po|ppo|rro|xplo]ser, ·[lou|pou|quou|tou]ser⟨ser|sée|zer|zé⟩, ·[chi|ci|di|gui|li|lli|ly|mi|ni|nni|phi|ri|thi|ti|tri|vi|xci|y|ï]ser; main forms: ser, ·[a|ba|bap|bi|bo|bé|ca|char|cia|co|cra|cré|cu|cé|da|do|dua|dé|for|ga|gi|gli|gné|go|gé|la|li|lia|lo|ma|mi|mmu|mo|mor|mé|na|ni|nna|no|né|or|pa|per|phi|phé|po|pro|qui|ra|ri|ria|rio|rro|sec|so|ssoi|ssu|sua|ta|ter|teu|ti|tia|to|tou|tra|tro|tu|tua|ty|té|va|ve|vi|via|vo|vé|xper|xtua|xua|ï]liser, ·[bu|clu|cu|du|ffu|fu|mu|xcu]sez, ·[cro|lo|pho|po|ppo|rro|xplo]ser, ·[lou|pou|quou|tou]ser, ·[chi|ci|di|gui|li|lli|ly|mi|ni|nni|phi|ri|thi|ti|tri|vi|xci|y|ï]ser
- `ter|teur|tter|tteur|ttheure` (parts teur, tteur, ter; new conflict freq 0.3): **outOfReach**
- `son|sson|çon` (parts çon, sson, son; new conflict freq 0.0): **outOfReach**
- `vi|vie|vis|vit` (parts vis, vi; new conflict freq 0.0): **outOfReach**
- `tau|taud|taut|teau|tho|to|tos|tot|tto|tô|tôt` (parts tôt, teau, to, tto; new conflict freq 4.7): **outOfReach**
- `mam|man|mem|men` (parts man, men, mem; new conflict freq 3.8): **outOfReach**
- `ger|gée` (parts ger, gée; new conflict freq 10.9); merged score None vs main 0: **apart**
    merged forms: ger|gée, ·[a|bra|cca|fra|ga|la|ma|mma|na|pa|ra|rra|sa|ssa|ta|tra|va]ger, ·[chan|dan|gran|lan|llen|ran|rran|tran]ger, ·[bli|di|ffli|fi|fli|gli|i|mi|ri|rri|si|ti]gé⟨ger|gée⟩, ·[gré|llé|lé|té]ger, ·[lo|mo|po|ro|rro|tau]ger; main forms: ger, ·[a|bra|cca|fra|ga|la|ma|mma|na|pa|ra|rra|sa|ssa|ta|tra|va]ger, ·[chan|dan|gran|lan|llen|ran|rran|tran]ger, ·[bli|di|ffli|fi|fli|gli|i|mi|ri|rri|si|ti]gé, ·[gré|llé|lé|té]ger, ·[bro|lo|mo|ro|rro|tau]ger
- `faire|fer|fert|ffaire|fère|phère` (parts fer, faire, phère, fère; new conflict freq 0.0): **outOfReach**
- `cune|cunes|qu'une` (parts cune; new conflict freq 1.0): **outOfReach**
- `pa|pai|paie|pe|pei|poe|pé` (parts pé, pe; new conflict freq 0.0): **outOfReach**
- `i|id|ye|ys|ï|ïs` (parts i; new conflict freq 0.1): **outOfReach**
- `boo|bou|bow|bu` (parts bou; new conflict freq 0.0): **outOfReach**
- `laud|leau|llo|llos|llot|llô|lo|lop|los|lot|low` (parts lot, lo, llo; new conflict freq 5.5): **outOfReach**
- `sou|soû|su` (parts sou, soû; new conflict freq 0.2): **outOfReach**
- `ppris|pris|prit|prix` (parts pris; new conflict freq 0.0): **outOfReach**
- `mee|mi|my` (parts mi, my; new conflict freq 0.0): **outOfReach**
- `col|cole|colle|cool` (parts cole; new conflict freq 0.0): **outOfReach**
- `cible|scible|sible|ssible` (parts ssible, sible, scible; new conflict freq 0.0): **outOfReach**
- `de|des|dé|déh` (parts dé, de, déh; new conflict freq 3.5); merged score None vs main 0: **apart**
    merged forms: de|des|dé|déh, dé[bi|bri|brie|chi|ci|cli|cri|di|fi|fri|gi|gri|gui|i|li|mi|my|ni|pi|pli|pri|qui|ri|shy|si|ssi|tri|vi]·, dé[a|ba|bap|bla|boi|boî|bra|bâ|ca|ce|cla|coi|cra|doua|dra|fa|fla|ga|goi|gra|la|ma|mâ|na|pa|pha|pla|plâ|poi|pra|qua|ra|sa|sha|ta|tra|va|via|voi]·, dé[bou|brou|clou|cloue|cou|dou|fou|gou|goû|grou|joue|kou|mou|noue|pou|rou|trou|voue]·, dé[bau|blo|bo|chau|co|cro|do|flo|fo|fro|gau|go|gro|jau|lo|mo|no|o|piau|plo|po|pro|ro|so|to|trô|vo]-{z}·, dé[ce|ché|cré|cé|fai|fra|fraie|fraî|fé|gre|gré|gé|lé|mé|né|pa|plai|pre|pré|pé|ré|shé|ssai|ssé|sé|té|vê]·; main forms: dé, dé[bi|bri|brie|chi|ci|cli|cri|di|fi|fri|gi|gri|gui|i|li|mi|my|ni|pi|pli|pri|qui|ri|shy|si|tri|vi]·, dé[ba|bap|bla|boi|boî|bra|bâ|ca|ce|cla|coi|cra|doua|dra|fa|fla|ga|goi|gra|la|ma|mâ|na|pa|pha|pla|plâ|poi|pra|qua|ra|sa|sha|ta|tra|va|via|voi]·, dé[bou|brou|clou|cloue|cou|dou|fou|gou|goû|grou|joue|kou|mou|noue|pou|rou|trou|voue]·, dé[bau|blo|bo|chau|co|cro|do|flo|fo|fro|gau|go|gro|jau|lo|mo|no|o|piau|plo|po|pro|ro|so|to|trô|vo]-{z}·, dé[ce|ché|cré|cé|fai|fra|fraie|fraî|fé|gre|gré|gé|lé|mé|né|pa|plai|pre|pré|pé|ré|shé|sé|té|vê]·
- `er|ée|ë` (parts er; new conflict freq 0.4): **outOfReach**
- `de|dea|di|die|dis|dy|dî` (parts di, dy; new conflict freq 0.0); merged score 1866 vs main 1660: **fused**
    merged forms: de|dea|di|die|dis|dy|dî, di[a|cho|chro|dac|ffa|ffen|ffi|ffor|ffu|ges|gi|gne|gni|gé|jo|jonc|la|le|li|lu|mi|na|nan|nas|ne|no|o|plo|plô|rec|ri|scer|sci|sen|shar|sig|sle|slo|ssem|ssen|sser|ssi|sso|ssol|ssou|ssu|ssua|ssy|ssé|su|thy|va|ver|vi|vor|vul|xie|xiè]-{fe,m@}·, diffé·, direc[ce|ge|se|te]·; main forms: di, di[a|cho|chro|dac|ffa|ffi|ffor|ffu|ges|gi|gne|gni|gé|jo|la|le|li|lu|mi|na|nan|no|o|plo|plô|rec|ri|scer|sci|shar|slo|ssem|ssen|sser|ssi|sso|ssol|ssou|ssu|ssua|ssy|ssé|thy|va|ver|vi|vor|vul|xie|xiè]-{fe,m@}·, diffé·, direc[ce|de|ge|se|te]·, dissi[mi|mu|mé|pa|pe|pli]·
- `ve|vei|vé|véh|vê` (parts vé, ve, vei; new conflict freq 0.0): **outOfReach**
- `su|sue|sû` (parts su; new conflict freq 0.0): **outOfReach**
- `ra|rah|ras|rat|rra|rrah|rras|rrat` (parts ra, rat, ras; new conflict freq 1.0): **outOfReach**
- `maine|men|mène|mènes` (parts men, mène; new conflict freq 1.0): **outOfReach**
- `bie|bien` (parts bien; new conflict freq 0.0): **outOfReach**
- `ta|tai|tay|te|tei|the|thê|tê` (parts te; new conflict freq 1.6): **outOfReach**
- `eins|ins` (parts ins; new conflict freq 0.0): **outOfReach**
- `de|deh|deu` (parts deu; new conflict freq 0.0): **outOfReach**
- `tom|ton` (parts tom, ton; new conflict freq 0.0): **outOfReach**
- `tee|thie|tie|ties|til|tis|tit|tti|ttis|ty` (parts tie, thie, ty, tis, ttis; new conflict freq 1.9): **outOfReach**
- `tendre|ttendre` (parts tendre; new conflict freq 0.0): **outOfReach**
- `plai|ple|plé` (parts plé; new conflict freq 0.0): **outOfReach**
- `sir|zir` (parts sir; new conflict freq 0.0): **outOfReach**
- `d'a|da|dah|dam` (parts da; new conflict freq 0.0): **outOfReach**
- `bor|bord|bore` (parts bord; new conflict freq 0.0): **outOfReach**
- `ba|bai|be|bee|beh|bé|béh|bê` (parts bé, bê, be; new conflict freq 0.0): **outOfReach**
- `fai|fe` (parts fe, fai; new conflict freq 0.0): **outOfReach**
- `nou|noue` (parts nou; new conflict freq 0.0): **outOfReach**
- `veau|vo|vot|vôt` (parts veau, vo; new conflict freq 0.0): **outOfReach**
- `mu|mue|mû` (parts mu, mû; new conflict freq 0.0): **outOfReach**
- `sic|sique|zique` (parts sique; new conflict freq 0.0): **outOfReach**
- `ram|ran|rem|ren` (parts ren, rem, ran, ram; new conflict freq 3.1): **outOfReach**
- `trer|tré|ttré` (parts trer, tré; new conflict freq 15.1): **outOfReach**
- `ci|cy|sci|scie|sea|si|sy` (parts si, ci, cy, sy; new conflict freq 0.7): **outOfReach**
- `nnon|nom|non` (parts non, nom; new conflict freq 0.0): **outOfReach**
- `vien|vient` (parts vien; new conflict freq 0.0): **outOfReach**
- `jo|raud|raut|raux|reau|ro|rop|ros|rot|rrau|rreau|rro|rrot` (parts ro, reau, rreau, rot, raud; new conflict freq 5.5): **outOfReach**
- `seoir|soir|soire|sseoir|ssoir|ssoire|çoir|çoire` (parts soir, ssoire, ssoir; new conflict freq 0.0): **outOfReach**
- `mir|mire` (parts mir; new conflict freq 0.0): **outOfReach**
- `ccion|cion|cyon|sion|ssion|tion|tions` (parts tion, ssion, sion; new conflict freq 0.1); merged score 5527 vs main 5031: **fused**
    merged forms: ccion|cion|cyon|sion|ssion|tion|tions, ·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tions⟨ccion|cion|cyon|sion|ssion|tion|tions⟩, ·[bi|ci|ddi|di|gni|li|lli|mi|mmi|ni|pi|ri|sci|si|sti|ti|tri]tion, ·[bi|bli|bri|chi|ci|di|fi|gi|gri|i|ki|li|lli|mi|mmi|ni|pi|pli|ppli|qui|ri|ry|si|spi|sti|thi|ti|tri|vi|xci|xi|xpli]tations, ·[cen|en|men|pen|sten|ten|tten|ven|xten]tion, ·[blu|bu|cu|llu|lu|nu|ru|tu]tion⟨ccion|cion|cyon|sion|ssion|tion|tions⟩; main forms: tion, ·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tions, ·[bi|bli|bri|chi|ci|di|fi|gi|gri|i|ki|li|lli|mi|mmi|ni|pi|pli|ppli|qui|ri|ry|si|spi|sti|thi|ti|tri|vi|xci|xi|xpli]tations, ·[sten|ten|tten|ven]tion, ·[bi|ci|ddi|di|gni|li|lli|mi|ni|ri|si|sti|ti|tri]tion, ·[blu|bu|cu|llu|lu|nu|ru|tu]tion
- `ca|cah|cha|câ|ka|kha|khâ|qua` (parts ca, qua, ka, câ, cah; new conflict freq 2.1); merged score None vs main 0: **apart**
    merged forms: ca|cah|cha|câ|ka|kha|khâ|qua, ca[ba|bi|blo|bo|bri|bu|bé|ca|cah|cha|che|cho|chè|co|da|das|de|den|do|dri|far|fe|fou|fé|gi|ille|illou|jo|la|lach|lai|lan|le|lem|len|li|lié|lli|llo|lo|lom|lu|lyp|lé|ma|mar|me|mem|mi|mio|mo|mou|mé|més|na|nar|nas|ne|ni|nna|nne|nni|no|nu|o|ou|pa|pe|po|pri|pu|pé|que|què|ra|rac|ram|ran|re|ri|rio|ris|ro|rou|rre|rrié|rro|rrou|rré|ryo|sa|se|ser|so|ssa|sse|ssi|sso|ssou|sé|ta|tal|tan|tas|ter|thar|the|tho|thé|to|tor|tri|té|va|val|ver|vi|ya]-{pi,zi}·, ca[bi|dri|gi|li|lli|mi|ni|nni|pi|pri|ri|si|ssi|theri|ti|vi]·, capa[ba|bi|blan|blé|bo|bou|bra|bre|bé|ca|cho|ci|cieu|clys|co|cu|de|dri|du|fi|fie|for|four|go|gra|i|la|le|lep|li|lin|liè|lle|llo|lo|ly|lé|ma|mis|mé|na|ni|nia|né|o|pi|ple|pul|ra|re|ri|rou|ta|tchou|te|ti|to|tro|té|va|van|vé|è]-{go,mi,s°}·; main forms: ca, ca[ba|bi|bo|bri|bé|ca|cah|cha|che|cho|chè|co|da|das|de|den|do|far|fe|fou|fé|gi|ille|illou|jo|la|lai|lan|le|lem|len|li|lli|llo|lo|lom|lu|lyp|lé|ma|mar|me|mem|mi|mio|mo|mou|mé|més|na|nar|nas|ne|ni|nna|nne|nni|no|nu|ou|pa|pe|po|pri|pu|pé|que|què|ra|rac|ram|re|ri|rio|ro|rou|rre|rrié|rro|rrou|rré|ryo|sa|se|ser|si|so|ssa|sse|ssi|sso|ssou|sé|ta|tal|tas|ter|thar|the|tho|thé|to|té|va|val|ver|vi]-{pi}·, ca[bi|gi|li|lli|mi|ni|nni|pi|pri|ri|si|ssi|theri|vi|ï]·, capa[ba|bi|blan|blé|bo|bou|bra|bre|bé|ca|cho|ci|cieu|clys|co|cu|de|dri|du|for|four|go|gra|i|la|le|lep|li|lin|liè|lle|llo|lo|ly|lé|ma|mis|mé|na|ni|nia|né|o|pi|ple|pul|ra|re|ri|rou|ta|tchou|te|ti|to|tro|té|va|van|vé]-{go,mi,s°}·
- `bu|bû` (parts bu, bû; new conflict freq 0.0): **outOfReach**
- `cer|ser` (parts ser, cer; new conflict freq 0.0): **outOfReach**
- `eu|heu|oe` (parts eu, oe; new conflict freq 0.0): **outOfReach**
- `reux|rreux|rrheux` (parts reux; new conflict freq 0.0): **outOfReach**
- `tae|te|the|thé|té|tê` (parts té, thé, te; new conflict freq 0.0): **outOfReach**
- `mai|maî|me|mé|méh` (parts mé, me; new conflict freq 0.9): **outOfReach**
- `pair|paire|peire|per|ppert|père` (parts père; new conflict freq 4.0): **outOfReach**
- `hoo|hou|houh|ou` (parts ou, hou; new conflict freq 0.1): **outOfReach**
- `cil|cile|cille|sile|ssile` (parts cile; new conflict freq 0.0): **outOfReach**
- `taine|taines|ten|tenne|thène|tène` (parts taine; new conflict freq 1.9): **outOfReach**
- `pa|pai|paie|paî|pe|pei|pè|pé|pê` (parts pe, pei; new conflict freq 1.3): **outOfReach**
- `illé|yé` (parts illé; new conflict freq 0.0): **outOfReach**
- `tou|tout|tu` (parts tout, tou; new conflict freq 0.0): **outOfReach**
- `ce|cei|cè|cé|sai|say|sce|se|sei|sep|sè|sé` (parts sai, ce, se; new conflict freq 2.6): **outOfReach**
- `gneur|gneurs` (parts gneur; new conflict freq 0.0): **outOfReach**
- `lade|llade` (parts lade; new conflict freq 4.5): **outOfReach**
- `mier|mié|mmier` (parts mier; new conflict freq 0.0): **outOfReach**
- `ex|exh|hex` (parts ex, exh; new conflict freq 0.0): **outOfReach**
- `pri|prie|pry` (parts pri; new conflict freq 0.0): **outOfReach**
- `cham|chan|sham|shan` (parts chan, cham; new conflict freq 0.0): **outOfReach**
- `nier|nié|nnier` (parts nier, nnier; new conflict freq 0.2): **outOfReach**
- `vais|vet|vêt` (parts vet; new conflict freq 0.0): **outOfReach**
- `ta|tas|tat|tha|tta|tà` (parts tat, ta, tta; new conflict freq 0.2): **outOfReach**
- `mom|mon|mont` (parts mon, mont; new conflict freq 0.0): **outOfReach**
- `pprendre|prendre` (parts prendre; new conflict freq 0.0): **outOfReach**
- `gen|jam|jan` (parts gen, jam; new conflict freq 0.0): **outOfReach**
- `prae|prai|pre|pré|préh|prê` (parts pré; new conflict freq 0.0): **outOfReach**
- `illeur|illeurs|lleur|yeur` (parts lleur, illeur; new conflict freq 0.0): **outOfReach**
- `cri|crie|crit` (parts crit; new conflict freq 0.0): **outOfReach**
- `ner|neur|nheur|nneur` (parts nneur, neur, ner; new conflict freq 0.0): **outOfReach**
- `tal|thal|ttal` (parts tal; new conflict freq 0.1): **outOfReach**
- `tar|tard|tare|tarrhe|thare|ttard` (parts tard, tar; new conflict freq 0.2): **outOfReach**
- `vi|wi` (parts vi; new conflict freq 0.0): **outOfReach**
- `sage|zage` (parts sage; new conflict freq 0.0): **outOfReach**
- `fau|fo|pho` (parts pho, fau, fo; new conflict freq 1.9): **outOfReach**
- `sau|saul|so|sot` (parts so, sau; new conflict freq 0.7): **outOfReach**
- `lar|lard|lare|llar|llard` (parts lard, lar; new conflict freq 0.1): **outOfReach**
- `gé|géh|je|jé` (parts gé, jé; new conflict freq 0.1): **outOfReach**
- `ral|rral|rrhal` (parts ral; new conflict freq 0.3): **outOfReach**
- `ra|rha|râ` (parts ra, râ; new conflict freq 0.4); merged score None vs main 0: **apart**
    merged forms: ra|rha|râ, ra[be|che|ge|ille|me|pe|ppe|re|te|ve]·⟨ra|rha|râ⟩, ra[ccom|con|gon|llon]·, ra[bbi|bi|chi|ci|di|ffi|lli|llie|mi|ni|pi|ppli|ri|si|ssi|ti|vi]·⟨ra|rha|râ⟩, ra[ba|bâ|chia|da|dia|ga|gna|gra|ma|pa|pha|pia|pla|ssa|ta|tta|ttra|va]·, ra[len|men|ssem]·; main forms: ra, ra[be|che|ge|ille|me|pe|ppe|re|te|ve]·, ra[ccom|con|gon|llon]·, ra[ba|bâ|chia|da|dia|ga|gna|gra|ma|pa|pha|pia|pla|ssa|ta|tta|ttra|va]·, ra[bbi|bi|chi|ci|di|ffi|lli|llie|mi|ni|pi|ppli|ri|si|ssi|ti|vi]·, ra[len|men|ssem]·
- `be|bee|bi|bih|by` (parts bi; new conflict freq 0.0): **outOfReach**
- `sar|sard|zar|zard|zarre|zarts|zzard` (parts sard, zar; new conflict freq 0.2): **outOfReach**
- `por|pore|port|ports|pport` (parts port; new conflict freq 0.0): **outOfReach**
- `nial|niale` (parts nial; new conflict freq 0.0): **outOfReach**
- `paud|peau|po|poc|pos|pot|ppeau|ppo|ppôt|pôt` (parts peau, po, pot; new conflict freq 3.0): **outOfReach**
- `comp|kon` (parts comp; new conflict freq 0.0): **outOfReach**
- `thier|tier|tiers|tiez|tié|ttier` (parts tier, tié, tiez, ttier; new conflict freq 0.1): **outOfReach**
- `tea|tee|thi|thy|ti|ty` (parts ti, ty, thy; new conflict freq 2.7): **outOfReach**
- `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` (parts rer, rée, rrer, rai, rrhée, rez; new conflict freq 17.9); merged score None vs main 0: **apart**
    merged forms: rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée, ·[bé|cé|dé|fé|gé|lle|lé|mmé|mé|né|pie|pé|re|scé|ssié|sé|te|té|vé]rer, ·[ba|ca|cla|ffa|ga|ma|pa]rer, ·[bu|cu|du|gu|ju|lu|mu|pu|ssu|su|tu]rer, ·[mi|pi|si|ti|tti|vi|xpi]rer, ·[bo|co|do|fo|gno|go|jau|jo|lio|lo|mo|no|plo|po|rio|ro|tau|to|vo|xplo]rer; main forms: rer, ·[bé|cé|dé|fé|gé|lé|mmé|mé|né|pé|scé|ssié|sé|té|vé]rer, ·[cla|ffa|ga|pa]rer, ·[bu|cu|du|gu|ju|lu|mu|pu|ssu|su|tu]rer, ·[mi|pi|si|ti|tti|vi|xpi]rer, ·[bo|co|do|fo|gno|go|jo|lio|lo|mo|no|plo|po|rio|ro|tau|to|vo|xplo]rer
- `rré|ré` (parts ré, rré; new conflict freq 0.0): **outOfReach**
- `cae|ce|coe|cé|sai|scé|se|sé` (parts sé, cé, se, ce, sai, scé; new conflict freq 0.2): **outOfReach**
- `cin|cinct|sain|seing|sin|ssaim|ssain|ssaint|ssin` (parts cin, ssin; new conflict freq 0.0): **outOfReach**
- `ssu|ssue|ssus|su|sue|çu` (parts çu, ssu; new conflict freq 5.2): **outOfReach**
- `bu|bue|bus|but` (parts bu; new conflict freq 0.9): **outOfReach**
- `coo|cou|coû|cu|kou|ku` (parts cou; new conflict freq 0.2): **outOfReach**
- `ran|rand|rant|rend|reng|rent|rents|rrant|rrent` (parts rant, rent, ran; new conflict freq 6.9): **outOfReach**
- `get|jet` (parts jet; new conflict freq 0.0): **outOfReach**
- `tail|tel|telle|ttelle|tèle` (parts tel, telle, tèle; new conflict freq 0.0): **outOfReach**
- `ba|bah|bap|bâ` (parts ba, bâ, bap; new conflict freq 3.7): **outOfReach**
- `lance|lence|llence` (parts lence, lance; new conflict freq 0.0): **outOfReach**
- `dai|de|dé` (parts de, dé; new conflict freq 0.0): **outOfReach**
- `rière|rrière` (parts rrière; new conflict freq 0.0): **outOfReach**
- `dou|du` (parts dou; new conflict freq 0.0): **outOfReach**
- `tram|tran|trem|tren` (parts tran, trem; new conflict freq 0.0): **outOfReach**
- `nel|nelle|nnel|nnelle` (parts nel, nnel, nelle; new conflict freq 0.0): **outOfReach**
- `geô|jau|jo` (parts jo, jau; new conflict freq 0.0): **outOfReach**
- `li|lie|lies|lis|lit|lli|llie|llye|ly` (parts li, lie, lis; new conflict freq 0.5): **outOfReach**
- `reur|rreur` (parts rreur, reur; new conflict freq 0.0): **outOfReach**
- `ac|acc|ak` (parts ac; new conflict freq 0.0): **outOfReach**
- `sage|ssage|çage` (parts ssage, çage; new conflict freq 0.0): **outOfReach**
- `te|té` (parts te; new conflict freq 0.0): **outOfReach**
- `fait|faix|fet|ffet` (parts fait; new conflict freq 0.0): **outOfReach**
- `che|ché|sché|shé` (parts ché; new conflict freq 0.3): **outOfReach**
- `dau|daud|deau|deaux|do|dot|dow` (parts deau, do; new conflict freq 0.2): **outOfReach**
- `dale|del|delle|dèle` (parts dèle, delle; new conflict freq 1.0): **outOfReach**
- `per|pper|ppé|ppée|pée` (parts per, pper, pée, ppé; new conflict freq 10.1): **outOfReach**
- `reil|reille` (parts reille; new conflict freq 0.0): **outOfReach**
- `soi|soie|swah` (parts soi; new conflict freq 0.0): **outOfReach**
- `mer|mmer|mmé|mmée|mées` (parts mer, mmer, mmé; new conflict freq 10.9): **outOfReach**
- `cha|chah|char|châ|scha|sha` (parts cha, châ; new conflict freq 1.4): **outOfReach**
- `ga|gha|gua|gâ` (parts ga, gâ; new conflict freq 0.0): **outOfReach**
- `gner|gnier|gnée` (parts gner, gnée; new conflict freq 1.0): **outOfReach**
- `geant|gent` (parts gent, geant; new conflict freq 0.0): **outOfReach**
- `bou|bout` (parts bou; new conflict freq 0.0): **outOfReach**
- `mal|mâle` (parts mal; new conflict freq 0.0): **outOfReach**
- `ccer|ceur|seur|soeur|sser|sseur` (parts sseur, seur, ceur; new conflict freq 0.0): **outOfReach**
- `ab|ap|hap` (parts ab; new conflict freq 0.0): **outOfReach**
- `ca|cas|cat|cca|ka|kha|kka|qu'à|qua|quat` (parts cat, ca, ka; new conflict freq 0.3): **outOfReach**
- `cker|cquer|cquée|ker|ké|quer|quée` (parts quer; new conflict freq 1.4): **outOfReach**
- `sam|sang|sem|sen` (parts sen, sem, sam; new conflict freq 0.0): **outOfReach**
- `cen|san` (parts cen, san; new conflict freq 0.0): **outOfReach**
- `chi|ki|ky|qui` (parts qui, ki; new conflict freq 0.0): **outOfReach**
- `lion|llion` (parts llion; new conflict freq 0.0): **outOfReach**
- `lage|llage` (parts llage, lage; new conflict freq 0.0): **outOfReach**
- `sit|site|sitent|sites` (parts site, sitent; new conflict freq 1.1): **outOfReach**
- `dis|dys` (parts dis, dys; new conflict freq 0.0): **outOfReach**
- `val|vale|valent|valle` (parts val; new conflict freq 0.2): **outOfReach**
- `cui|qui` (parts cui; new conflict freq 0.0): **outOfReach**
- `sine|zin|zine` (parts sine, zine; new conflict freq 0.0): **outOfReach**
- `cein|cin|cym|sain|scin|sim|sin|sym|syn` (parts sym, sim, cin, sin, syn, scin; new conflict freq 0.0): **outOfReach**
- `d'em|dan|den` (parts dan, den; new conflict freq 0.0): **outOfReach**
- `nuer|nué` (parts nuer; new conflict freq 0.8): **outOfReach**
- `cer|cerre|cert|cère|saire|scère|sert|ssaire|sserre|ssert` (parts ssaire; new conflict freq 0.0): **outOfReach**
- `nan|nant|nent|nnant` (parts nant, nnant, nent; new conflict freq 0.0): **outOfReach**
- `ra|rai|raie|re|rhé|ré|réh` (parts ré, re, rhé; new conflict freq 0.3); merged score None vs main 3300: **apart**
    merged forms: ra|rai|raie|re|rhé|ré|réh, ré[clu|cu|du|fu|gu|mu|pu|su|u]·, réa[bi|bli|bo|ccou|che|dap|ffec|ffi|gi|jus|li|mor|mé|ni|per|pi|ppa|ppe|ppre|ppren|ppro|ra|re|rran|ssem|ssi|ssor|ssu|tta]·, ré[be|cré|crée|cé|e|flé|fré|fé|gé|pre|préh|pé|sé|tré|vei|vé|é]·, ré[com|con|pon]·, ré[a|ca|ce|cha|cla|ga|ma|pa|ta]·⟨ra|rai|raie|re|rhé|ré|réh⟩; main forms: ré, ré[clu|cu|du|fu|gu|mu|pu|su|u]·, ré[a|ca|ce|cha|cla|ga|ma|pa|ta]·, ré[be|cré|crée|cé|e|flé|fré|fé|gé|pre|préh|pé|sé|tré|vei|vé|é]·, ré[com|con|pon]·, ré[e|fle|gre|vei]·
- `vau|vo|vos` (parts vo, vau; new conflict freq 0.0): **outOfReach**
- `fic|fique|phique` (parts fique, phique; new conflict freq 0.0): **outOfReach**
- `vai|ve|vei|vé|vê` (parts ve, vai, vê, vei; new conflict freq 2.0): **outOfReach**
- `ter|ther` (parts ter, ther; new conflict freq 0.0): **outOfReach**
- `bau|bo|boh` (parts bo, bau; new conflict freq 0.0): **outOfReach**
- `pea|pee|pi|py` (parts pi, py; new conflict freq 0.5): **outOfReach**
- `lea|li|lie|ly` (parts li, ly; new conflict freq 1.8): **outOfReach**
- `moe|moi` (parts moi; new conflict freq 0.0): **outOfReach**
- `sel|selle|selles|zel|zelle` (parts selle; new conflict freq 0.1): **outOfReach**
- `vir|vire` (parts vir; new conflict freq 0.0): **outOfReach**
- `nal|nales|nnal|nnale|nnales` (parts nal; new conflict freq 0.8): **outOfReach**
- `rol|role|rolle` (parts role; new conflict freq 0.0): **outOfReach**
- `rage|rrage` (parts rage, rrage; new conflict freq 0.0): **outOfReach**
- `cours|court` (parts cours; new conflict freq 0.0): **outOfReach**
- `laire|ler|llaire|lère` (parts laire, llaire; new conflict freq 0.0): **outOfReach**
- `va|vah|wa` (parts va; new conflict freq 0.0): **outOfReach**
- `cance|kaans|quance|quence` (parts quence; new conflict freq 0.0): **outOfReach**
- `par|pard|pare|pars|part` (parts pard; new conflict freq 0.0): **outOfReach**
- `ceau|sault|saut|sceau|seau|so|ssaut|sseau|sso|ssot` (parts sseau, ceau, so; new conflict freq 0.1): **outOfReach**
- `la|lla|lâ` (parts la, lâ; new conflict freq 0.0): **outOfReach**
- `ckel|quel|quelle` (parts quel, quelle; new conflict freq 0.0): **outOfReach**
- `tim|time` (parts time; new conflict freq 0.0): **outOfReach**
- `cis|cys|sis|sys` (parts sys, sis; new conflict freq 0.0): **outOfReach**
- `ler|leur|lheur|ller|lleur` (parts leur, lleur; new conflict freq 0.0): **outOfReach**
- `vance|vence` (parts vance; new conflict freq 0.0): **outOfReach**
- `vaire|ver|vers|vert|vère|wehr` (parts vers, vert, vaire; new conflict freq 0.0): **outOfReach**
- `san|sant|sent|zan|zant` (parts sant, san; new conflict freq 0.0): **outOfReach**
- `pied|pier|pié` (parts pier; new conflict freq 1.3): **outOfReach**
- `thyle|til|tile|tille|tyle` (parts tile, til; new conflict freq 0.5): **outOfReach**
- `rie|rier|riez|rrier|rrié` (parts rier, rrier, riez; new conflict freq 0.0): **outOfReach**
- `lloir|loir|loire` (parts loir; new conflict freq 0.0): **outOfReach**
- `rai|raie|raient|rais|rait|ret|rey|rrais|rret|rrêt|rè|rêt` (parts rais, ret, rait, raie, raient; new conflict freq 1.6): **outOfReach**
- `pon|pons|pont|ppon` (parts pon; new conflict freq 0.0): **outOfReach**
- `lope|loppe` (parts lope; new conflict freq 0.0): **outOfReach**
- `ma|mac|mas|mat|mma|mmas` (parts ma, mat, mas; new conflict freq 0.0): **outOfReach**
- `hu|u|uh` (parts u, hu; new conflict freq 0.0): **outOfReach**
- `pain|paing|peint|pin|ppin` (parts pin; new conflict freq 0.0): **outOfReach**
- `chau|cho|chô|sho|show` (parts chau, cho, chô; new conflict freq 0.0): **outOfReach**
- `ssure|ssures|sure|çure` (parts ssure, sure; new conflict freq 0.0): **outOfReach**
- `gou|goû` (parts gou; new conflict freq 0.1): **outOfReach**
- `bite|bitent|bites|byte` (parts bite, bites, bitent; new conflict freq 0.0): **outOfReach**
- `mage|mmage` (parts mmage, mage; new conflict freq 0.0): **outOfReach**
- `ta|tah|tei|tha|tâ` (parts ta, tâ, tha; new conflict freq 5.4): **outOfReach**
- `xi|xie|xis|xy|xys` (parts xie; new conflict freq 0.0): **outOfReach**
- `ge|je` (parts je, ge; new conflict freq -0.0): **outOfReach**
- `fae|fai|fe|foe|fé|fée|féé|fê|phoe|phé` (parts fé, phé, fe; new conflict freq 0.3): **outOfReach**
- `si|sie|sil|sis|sy|zi|zy|zzi|zzy` (parts sie, zi, si; new conflict freq 1.5): **outOfReach**
- `tance|tence|tense|ttance|ttence` (parts tance, tence; new conflict freq 0.0): **outOfReach**
- `ba|bac|bah|bas|bat|bbat` (parts bat, ba; new conflict freq 0.0): **outOfReach**
- `re|rea|rhi|rhy|ri|rie` (parts ri, rhi, re; new conflict freq 0.0): **outOfReach**
- `cul|cule` (parts cule; new conflict freq 0.0): **outOfReach**
- `ron|rond|rons|ront|rron` (parts ron, rron, rons, ront; new conflict freq 0.0): **outOfReach**
- `niaire|nière|nnière` (parts nière, nnière; new conflict freq 0.0): **outOfReach**
- `sion|ziom` (parts sion; new conflict freq 0.0): **outOfReach**
- `pla|plai|plâ` (parts pla, plâ; new conflict freq 0.0): **outOfReach**
- `net|neth|nette|nettes|nnette|nnête|nète` (parts nnette, nette; new conflict freq 0.0): **outOfReach**
- `car|kar|quar` (parts car, quar; new conflict freq 0.0): **outOfReach**
- `da|dah|das|dat|date|ddha` (parts dat, da; new conflict freq 0.1): **outOfReach**
- `illeux|lleux|ïeu|ïeux` (parts lleux, illeux; new conflict freq 0.0): **outOfReach**
- `dain|din` (parts din; new conflict freq 0.0): **outOfReach**
- `cquette|ket|kette|quette|quête` (parts quette; new conflict freq 0.0): **outOfReach**
- `an|and|ans|ant|empt|ent` (parts ant, ent, an; new conflict freq 0.2): **outOfReach**
- `poi|poê` (parts poi; new conflict freq 0.0): **outOfReach**
- `toi|toua` (parts toi; new conflict freq 0.0): **outOfReach**
- `laite|leth|lette|llaite|llaitent|llaites|llette|lète` (parts lette; new conflict freq 0.0): **outOfReach**
- `gar|gard|gare|garre|guar` (parts gard; new conflict freq 0.0): **outOfReach**
- `ddie|ddy|dee|dhi|di|die|dis|dit|dits|dy` (parts di, die, dit, dis; new conflict freq 2.2): **outOfReach**
- `sain|sein|sin|zain|zin` (parts sin; new conflict freq 0.0): **outOfReach**
- `des|dés` (parts des, dés; new conflict freq 0.0): **outOfReach**
- `rance|rence|rrance|rrence` (parts rence, rance; new conflict freq 0.0): **outOfReach**
- `ccu|cu|cul|cus|ku` (parts cu; new conflict freq 0.2): **outOfReach**
- `tice|tis|tiss|tisse|tys` (parts tice, tis; new conflict freq 0.0): **outOfReach**
- `pais|pect|pet` (parts pect; new conflict freq 0.0): **outOfReach**
- `blai|ble|blê` (parts ble; new conflict freq 0.0): **outOfReach**
- `rain|rein|rin|rrain|rrin` (parts rrain, rin, rain; new conflict freq 0.1): **outOfReach**
- `bra|brah` (parts bra; new conflict freq 0.0): **outOfReach**
- `cam|can|kan|quan` (parts cam, can, quan; new conflict freq -0.0): **outOfReach**
- `pan|pang|pant|pens|pent|ppant` (parts pant, pan; new conflict freq 0.2): **outOfReach**
- `spe|spé` (parts spé; new conflict freq 0.0): **outOfReach**
- `rad|rade|rrade` (parts rade; new conflict freq 0.0): **outOfReach**
- `der|deur` (parts deur, der; new conflict freq 0.2): **outOfReach**
- `cens|cent|san|sant|scent|sent|ssan|ssant|çant` (parts ssant, cent, çant, sant, scent; new conflict freq 0.7): **outOfReach**
- `maître|mettre|mmettre|mètre` (parts mettre, mètre; new conflict freq 0.0): **outOfReach**
- `lan|land|lant|lent|llan|llant|llent` (parts lant, lan, lent, llant; new conflict freq 0.0): **outOfReach**
- `mael|mal` (parts mal; new conflict freq 0.0): **outOfReach**
- `gree|gré|grée` (parts gré; new conflict freq 0.0): **outOfReach**
- `rif|riff|riph` (parts rif; new conflict freq 0.1): **outOfReach**
- `thera|tra|tras|trat` (parts tra; new conflict freq 0.2): **outOfReach**
- `ffieh|ffier|fier|phier|phié` (parts fier, phier; new conflict freq 0.3): **outOfReach**
- `ni|nie|nih|ny` (parts ni; new conflict freq 0.0): **outOfReach**
- `cet|cès|set|ssai|ssaient|ssais|ssait|sset|çais` (parts cès, cet; new conflict freq 0.0): **outOfReach**
- `sance|sence` (parts sance; new conflict freq 0.0): **outOfReach**
- `traî|tre|trei|tré` (parts tré; new conflict freq 0.0): **outOfReach**
- `ciance|cience|science|tience|tiens` (parts science; new conflict freq 0.0): **outOfReach**
- `nae|ne|nei|né` (parts né; new conflict freq 0.1): **outOfReach**
- `fra|phra` (parts fra, phra; new conflict freq 0.0): **outOfReach**
- `hoi|houa|oi|oua|wa` (parts oi, wa, oua; new conflict freq 0.0): **outOfReach**
- `seau|so|zo` (parts seau, zo, so; new conflict freq 0.1): **outOfReach**
- `sième|xième|zième` (parts zième; new conflict freq 0.0): **outOfReach**
- `mau|maux|meau|mmeau|mo|moan|mot` (parts mo, meau; new conflict freq 0.1): **outOfReach**
- `nic|nich|nik|nique|nnique` (parts nique; new conflict freq 1.2): **outOfReach**
- `illie|illis|illy|lli|llis|lly` (parts illis; new conflict freq 0.0): **outOfReach**
- `prai|pre|pré|prê` (parts pre, prê; new conflict freq -0.0): **outOfReach**
- `illais|illet|llais|llet` (parts llet, illet; new conflict freq 0.0): **outOfReach**
- `gler|glée` (parts gler; new conflict freq 0.0): **outOfReach**
- `bai|be|bei|bê` (parts bai, bê, be; new conflict freq 1.4): **outOfReach**
- `gee|gi|gie|gis|ji` (parts gie; new conflict freq 0.0): **outOfReach**
- `foo|fou` (parts fou; new conflict freq 0.0): **outOfReach**
- `pace|pas|passe` (parts pace; new conflict freq 0.0): **outOfReach**
- `nar|nard|nnard` (parts nard, nar; new conflict freq 0.0): **outOfReach**
- `sable|ssable|çable` (parts sable, ssable, çable; new conflict freq 0.0): **outOfReach**
- `al|hal` (parts al, hal; new conflict freq 0.7): **outOfReach**
- `rit|rite|ritent|rites|rrite|rritent|rrites|ryte` (parts rite; new conflict freq 0.0): **outOfReach**
- `chette|chète` (parts chette; new conflict freq 0.0): **outOfReach**
- `mon|mont` (parts mon; new conflict freq 0.0): **outOfReach**
- `dieu|dieux` (parts dieu, dieux; new conflict freq 0.0): **outOfReach**
- `tage|ttage` (parts tage, ttage; new conflict freq 0.0): **outOfReach**
- `mais|may|met|mets|mmet` (parts met; new conflict freq 0.0): **outOfReach**
- `thume|tume` (parts tume; new conflict freq 0.0): **outOfReach**
- `hur|ur` (parts ur, hur; new conflict freq 0.0): **outOfReach**
- `geance|gence` (parts gence, geance; new conflict freq 0.0): **outOfReach**
- `am|ame|ham` (parts am; new conflict freq 0.0): **outOfReach**
- `nai|naî|ne|nei|né` (parts nai; new conflict freq 0.0): **outOfReach**
- `cence|scence|sence|sens|sense|ssance|ssence` (parts ssance, cence, scence; new conflict freq 0.0): **outOfReach**
- `tesse|tès` (parts tesse; new conflict freq 0.0): **outOfReach**
- `vam|van|ven` (parts ven, vam, van; new conflict freq 0.1): **outOfReach**
- `gir|gire` (parts gir; new conflict freq 0.0): **outOfReach**
- `fer|feur|ffeur|pher` (parts ffeur, feur, fer; new conflict freq 0.0): **outOfReach**
- `cket|ckey|cquet|cquêt|kay|quais|quet` (parts quet; new conflict freq 0.0): **outOfReach**
- `ob|op` (parts ob, op; new conflict freq 0.0): **outOfReach**
- `mise|miz` (parts mise; new conflict freq 0.0): **outOfReach**
- `tail|taille` (parts tail, taille; new conflict freq 0.0): **outOfReach**
- `thri|tri|trie|try` (parts tri; new conflict freq 0.0): **outOfReach**
- `fram|fran` (parts fran; new conflict freq 0.0): **outOfReach**
- `taire|ter|terre|ther|thère|ttaire|tter|tère|tèrent` (parts taire, tère, ter, tèrent; new conflict freq 0.1): **outOfReach**
- `thique|tic|tik|tique|ttique|tyque` (parts tique, thique, tic; new conflict freq 1.8): **outOfReach**
- `cal|cale|chal|kal` (parts cal; new conflict freq 0.0): **outOfReach**
- `du|dû` (parts du; new conflict freq 0.0): **outOfReach**
- `sau|so` (parts so; new conflict freq 0.0): **outOfReach**
- `lise|lyse` (parts lise, lyse; new conflict freq 0.0): **outOfReach**
- `lain|lin|llin` (parts lin, lain; new conflict freq 0.0): **outOfReach**
- `cien|ssien|tien` (parts cien, tien, ssien; new conflict freq 0.0): **outOfReach**
- `lai|laie|lais|legs|let|lley` (parts let, lais; new conflict freq 2.8): **outOfReach**
- `eu|eux` (parts eux; new conflict freq 0.0): **outOfReach**
- `table|ttable` (parts table, ttable; new conflict freq 0.0): **outOfReach**
- `cri|crii|cry` (parts cri; new conflict freq 0.0): **outOfReach**
- `ggae|gger|guer` (parts guer; new conflict freq 0.1): **outOfReach**
- `ver|veur|weur` (parts veur; new conflict freq 0.0): **outOfReach**
- `cain|kin|quain|quin` (parts cain, quin; new conflict freq 0.2): **outOfReach**
- `re|reh` (parts re; new conflict freq 0.0): **outOfReach**
- `thon|ton|tons|tton` (parts ton, tons; new conflict freq 0.7): **outOfReach**
- `pui|puî` (parts pui; new conflict freq 0.0): **outOfReach**
- `champ|chan|chand|chant` (parts chant; new conflict freq 0.2): **outOfReach**
- `hor|or` (parts or, hor; new conflict freq 0.0): **outOfReach**
- `throm|trom|tron` (parts trom, tron; new conflict freq 0.0): **outOfReach**
- `breu|breux` (parts breux; new conflict freq 0.4): **outOfReach**
- `gei|ja|jea` (parts ja; new conflict freq 0.0): **outOfReach**
- `lou|loup|loux` (parts lou; new conflict freq 0.0): **outOfReach**
- `mer|meur|meure|mmer|mmeur` (parts meur; new conflict freq 0.0): **outOfReach**
- `fan|fen|phan` (parts fan, fen; new conflict freq 0.3): **outOfReach**
- `tome|tôme` (parts tome; new conflict freq 0.0): **outOfReach**
- `ciant|cient|scient|tiant|tient` (parts scient; new conflict freq 0.0): **outOfReach**
- `pir|pire` (parts pir; new conflict freq 0.0): **outOfReach**
- `llote|lote|lotte` (parts lote, lotte; new conflict freq 0.0): **outOfReach**
- `tiaire|tière|ttière` (parts tière; new conflict freq 0.0): **outOfReach**
- `vit|vite|vitent|vites` (parts vite, vites, vitent; new conflict freq 0.0): **outOfReach**
- `tau|thau|tho|to|tô` (parts to, tau, tho; new conflict freq 0.3): **outOfReach**
- `lam|lan|len` (parts lan, len, lam; new conflict freq 0.0): **outOfReach**
- `plai|ple|plei` (parts plai; new conflict freq 0.0): **outOfReach**
- `bau|baud|beau|bo|bot` (parts bo, bot, beau; new conflict freq 0.1): **outOfReach**
- `chré|cre|cré|crée|crê` (parts cré; new conflict freq 0.2): **outOfReach**
- `thyste|tiste|ttiste` (parts tiste, ttiste; new conflict freq 0.0): **outOfReach**
- `la|lacs|lah|las|lat|lla|llah|llat|là` (parts lat, la, las, lla; new conflict freq 1.3): **outOfReach**
- `nage|nnage` (parts nage, nnage; new conflict freq 0.0): **outOfReach**
- `gal|gale` (parts gal, gale; new conflict freq 0.0): **outOfReach**
- `chi|chie|chis|chy|shi` (parts chie, chi; new conflict freq 0.0): **outOfReach**
- `ness|nesse|nnesse` (parts nesse; new conflict freq 0.0): **outOfReach**
- `raître|rèthre|rètre` (parts raître; new conflict freq 0.0): **outOfReach**
- `dier|diée` (parts dier; new conflict freq 0.0): **outOfReach**
- `naie|nais|nay|net|ney|nnaie|nnais|nnay|nnet|nêt` (parts net, nais, nnet, nnais; new conflict freq 0.0): **outOfReach**
- `mar|mard|marre|mart|mmard` (parts mar, mard; new conflict freq 0.0): **outOfReach**
- `gage|guage` (parts gage; new conflict freq 0.0): **outOfReach**
- `na|nas|nat|naüm|nha|nna|nnah|nnat` (parts na, nat; new conflict freq 0.1): **outOfReach**
- `cu|ku` (parts cu; new conflict freq 0.0): **outOfReach**
- `llois|loi|lois` (parts loi; new conflict freq 0.0): **outOfReach**
- `paim|pein|pen|pim|pin` (parts pein, pin, pen; new conflict freq 0.0): **outOfReach**
- `frau|fro|frô` (parts fro; new conflict freq 0.0): **outOfReach**
- `pri|prii` (parts pri; new conflict freq 0.0): **outOfReach**
- `tra|trai|traî|tre|trei` (parts trai, traî, tre, trei; new conflict freq 0.0): **outOfReach**
- `cide|side` (parts cide; new conflict freq 0.0): **outOfReach**
- `thrine|trine|ttrine` (parts trine; new conflict freq 0.0): **outOfReach**
- `tress|tresse` (parts tresse; new conflict freq 0.0): **outOfReach**
- `riel|rielle|rriel` (parts riel; new conflict freq 0.0): **outOfReach**
- `nable|nnable` (parts nable, nnable; new conflict freq 0.0): **outOfReach**
- `tease|tise|ttise` (parts tise; new conflict freq 0.0): **outOfReach**
- `fforme|forme` (parts forme; new conflict freq 0.0): **outOfReach**
- `roir|roire|rroir` (parts roir; new conflict freq 0.0): **outOfReach**
- `liste|lliste|lyste` (parts liste, lliste; new conflict freq 0.0): **outOfReach**
- `lace|las|lasse|llace` (parts lasse; new conflict freq 0.0): **outOfReach**
- `rrus|rus` (parts rus; new conflict freq 0.0): **outOfReach**
- `el|elle|elles|ël` (parts el, elle; new conflict freq 0.0): **outOfReach**
- `naire|naires|ner|nnaire|nner|nnerre|nère` (parts naire, nnaire, ner; new conflict freq 0.7): **outOfReach**
- `au|aut|o|os|ot` (parts o, au; new conflict freq 0.2): **outOfReach**
- `cette|scète|set|ssette` (parts ssette, cette; new conflict freq 1.2): **outOfReach**
- `therie|tri|trie|trit|try` (parts trie; new conflict freq 0.1): **outOfReach**
- `cine|scine|sin|sine|ssine` (parts cine, ssine; new conflict freq 0.0): **outOfReach**
- `ffort|fort|phore` (parts fort, phore; new conflict freq 0.0): **outOfReach**
- `bru|brû` (parts brû, bru; new conflict freq -0.0): **outOfReach**
- `rable|rrable` (parts rable; new conflict freq 0.0): **outOfReach**
- `mis|mys` (parts mys, mis; new conflict freq 0.0): **outOfReach**
- `tante|tente|ttante|ttente` (parts tante; new conflict freq 0.0): **outOfReach**
- `ciaire|cière|ssière|tiaire` (parts ssière, ciaire, cière; new conflict freq 0.6): **outOfReach**
- `traie|trait|ttrait` (parts trait; new conflict freq 0.0): **outOfReach**
- `mable|mmable` (parts mable, mmable; new conflict freq 0.0): **outOfReach**
- `chi|chie|chih|chy|schi|shi` (parts chi; new conflict freq 1.5): **outOfReach**
- `nnois|noi|nois|noît` (parts nois; new conflict freq 0.1): **outOfReach**
- `gique|jik` (parts gique; new conflict freq 0.0): **outOfReach**
- `tam|tan|tem|ten` (parts ten, tem, tan, tam; new conflict freq 0.0): **outOfReach**
- `nau|naud|neau|nneau|nnot|no|nod|not` (parts no, nneau, neau, not; new conflict freq 2.5): **outOfReach**
- `gnol|gnole|gnoles` (parts gnol, gnole; new conflict freq 0.0): **outOfReach**
- `sure|zur` (parts sure; new conflict freq 0.0): **outOfReach**
- `cir|cire|ssir|ssire` (parts ssir, cir; new conflict freq 0.0): **outOfReach**
- `battre|bâtre` (parts battre; new conflict freq 0.0): **outOfReach**
- `tiv|tive` (parts tive; new conflict freq 0.0): **outOfReach**
- `vain|vin` (parts vin; new conflict freq 0.0): **outOfReach**
- `cieux|ssieu|ssieux|tieux` (parts cieux, tieux; new conflict freq 0.1): **outOfReach**
- `rau|rho|ro|rô` (parts ro, rô, rho; new conflict freq 1.0): **outOfReach**
- `geux|jeu` (parts geux; new conflict freq 0.0): **outOfReach**
- `pi|pie|pis|pit|ppie|ppy|py` (parts pie, pi; new conflict freq 1.5): **outOfReach**
- `fai|faî|fe|fei|fê` (parts fê, fe, fai; new conflict freq 0.3): **outOfReach**
- `pas|passe` (parts pas; new conflict freq 0.0): **outOfReach**
- `cir|seer|sir` (parts cir; new conflict freq 0.0): **outOfReach**
- `ra|ray` (parts ray; new conflict freq 0.0): **outOfReach**
- `bbi|bbies|bby|bee|bi|bie|bis|bit|by` (parts bi, by, bit, bie; new conflict freq 0.9): **outOfReach**
- `thu|tu|tue` (parts tu; new conflict freq 0.0): **outOfReach**
- `car|card|carre|cart|cquard|kare|kkar|quard` (parts card, cart; new conflict freq 1.1): **outOfReach**
- `air|aire|ère` (parts ère, aire; new conflict freq 0.0): **outOfReach**
- `mite|mitent|mites` (parts mite, mitent, mites; new conflict freq 0.4): **outOfReach**
- `scam|scan` (parts scan; new conflict freq 0.0): **outOfReach**
- `dal|dale` (parts dale, dal; new conflict freq 0.0): **outOfReach**
- `free|fri|phry` (parts fri; new conflict freq 0.0): **outOfReach**
- `gaud|gaux|gho|go|got|goth|guo` (parts go, got; new conflict freq 0.2): **outOfReach**
- `illance|llance|ïence` (parts llance; new conflict freq 0.0): **outOfReach**
- `mance|mence|mmense` (parts mence, mance; new conflict freq 0.0): **outOfReach**
- `rel|relle|relles` (parts rel, relle; new conflict freq 0.0): **outOfReach**
- `sa|sat|za` (parts za, sa; new conflict freq 0.1): **outOfReach**
- `ance|ence` (parts ance, ence; new conflict freq 0.0): **outOfReach**
- `page|ppage` (parts page; new conflict freq 0.0): **outOfReach**
- `nau|no` (parts no, nau; new conflict freq 0.0): **outOfReach**
- `teak|teck|thèque|tèque` (parts thèque, tèque; new conflict freq 0.2): **outOfReach**
- `thien|tien` (parts tien; new conflict freq 0.0): **outOfReach**
- `bil|bile|byle|bylle` (parts bile; new conflict freq 0.0): **outOfReach**
- `clea|cli|klee` (parts cli; new conflict freq 0.0): **outOfReach**
- `gaie|gaî|gei|gué|guê` (parts gué; new conflict freq 0.0): **outOfReach**
- `pal|pale|ppal` (parts pal; new conflict freq 0.0): **outOfReach**
- `cal|cale|ccal|qual` (parts cal, cale; new conflict freq 1.7): **outOfReach**
- `chry|cri|crie|cry` (parts cri; new conflict freq 0.0): **outOfReach**
- `la|lai|laie|le|lé` (parts lé, le; new conflict freq 0.4): **outOfReach**
- `ette|ète` (parts ette; new conflict freq 0.0): **outOfReach**
- `tomne|ton|tone|tonne` (parts tone; new conflict freq 0.0): **outOfReach**
- `bbon|bon|bond` (parts bon, bond; new conflict freq 0.0): **outOfReach**
- `feuil|feuille` (parts feuille; new conflict freq 0.1): **outOfReach**
- `pli|plie|plies|plis` (parts pli; new conflict freq 0.0): **outOfReach**
- `cra|crai|crâ|kra` (parts cra, crâ; new conflict freq 0.0): **outOfReach**
- `xuel|xuelle` (parts xuel; new conflict freq 0.3): **outOfReach**
- `dance|danse|dence` (parts dence, dance; new conflict freq 0.0): **outOfReach**
- `trique|ttrique` (parts trique; new conflict freq 0.0): **outOfReach**
- `ffice|fice` (parts fice; new conflict freq 0.0): **outOfReach**
- `sier|sié|zier` (parts sier; new conflict freq 0.6): **outOfReach**
- `al|ale` (parts al; new conflict freq 0.3): **outOfReach**
- `pette|pettes|ppette|pète|pètes|pête` (parts pette; new conflict freq 0.4): **outOfReach**
- `bri|brie` (parts bri; new conflict freq 0.0): **outOfReach**
- `cru|crû` (parts cru; new conflict freq 0.0): **outOfReach**
- `lin|line|lline` (parts lline, line; new conflict freq 0.0): **outOfReach**
- `tif|tife|tiff` (parts tif; new conflict freq 0.0): **outOfReach**
- `ste|stea|sti|sty` (parts sty, sti; new conflict freq 0.0): **outOfReach**
- `cond|gon|gong` (parts gon; new conflict freq 0.0): **outOfReach**
- `rone|ronne` (parts rone; new conflict freq 0.0): **outOfReach**
- `rhom|rom|ron` (parts ron; new conflict freq 0.0): **outOfReach**
- `ppu|pu` (parts pu; new conflict freq 0.0): **outOfReach**
- `cchi|cquis|cquit|kee|ki|kie|kies|ky|qui|quie|quis` (parts quis, ki; new conflict freq 0.7): **outOfReach**
- `bel|belle` (parts belle, bel; new conflict freq 0.1): **outOfReach**
- `tec|tech` (parts tech; new conflict freq 0.0): **outOfReach**
- `chia|ria|riat` (parts riat, ria; new conflict freq 0.0): **outOfReach**
- `rou|roue` (parts rou; new conflict freq 0.0): **outOfReach**
- `illir|llir` (parts illir; new conflict freq 0.0): **outOfReach**
- `illant|llan|llant|yant` (parts llant, illant; new conflict freq 0.0): **outOfReach**
- `mid|mide|myde` (parts mide; new conflict freq 0.0): **outOfReach**
- `ddhique|dic|dique` (parts dique; new conflict freq 0.0): **outOfReach**
- `log|logue` (parts logue; new conflict freq 0.0): **outOfReach**
- `bbler|bler` (parts bler; new conflict freq 0.0): **outOfReach**
- `blé|blée` (parts blé; new conflict freq 0.3): **outOfReach**
- `ball|bol|bole` (parts bole; new conflict freq 0.0): **outOfReach**
- `et|eth|het` (parts eth; new conflict freq 0.0): **outOfReach**
- `lau|lo|loa` (parts lo, lau; new conflict freq 0.0): **outOfReach**
- `ir|ïr|ïre` (parts ir; new conflict freq 0.0): **outOfReach**
- `chla|cla|kla` (parts cla; new conflict freq 0.0): **outOfReach**
- `cique|sique|ssik|ssique` (parts ssique, cique; new conflict freq 0.0): **outOfReach**
- `ghol|gol|gole` (parts gol; new conflict freq 0.0): **outOfReach**
- `verse|verses` (parts verse; new conflict freq 0.0): **outOfReach**
- `nade|nnade` (parts nade, nnade; new conflict freq 0.0): **outOfReach**
- `fil|phile|phylle` (parts phile; new conflict freq 0.0): **outOfReach**
- `dir|dire` (parts dir, dire; new conflict freq 0.0): **outOfReach**
- `ga|gas|gat|gha|gât` (parts ga, gat; new conflict freq 0.0): **outOfReach**
- `lien|llien` (parts lien; new conflict freq 0.0): **outOfReach**
- `gil|gile` (parts gile; new conflict freq 0.3): **outOfReach**
- `mat|mate` (parts mate; new conflict freq 0.0): **outOfReach**
- `meu|meux|mmeux` (parts meux; new conflict freq 0.0): **outOfReach**
- `grafe|graphe` (parts graphe; new conflict freq 0.0): **outOfReach**
- `ffee|ffi|fi|fis|fit|fix|phi|phie` (parts phie; new conflict freq 0.0): **outOfReach**
- `croi|croî` (parts croi; new conflict freq 0.0): **outOfReach**
- `cable|ccable|quable` (parts quable, cable; new conflict freq 0.0): **outOfReach**
- `cace|cas|casse|quace` (parts casse; new conflict freq 0.0): **outOfReach**
- `cel|celle|celles|cèle|sel|ssel|sselle` (parts celle; new conflict freq 0.0): **outOfReach**
- `rhu|ru|rue` (parts ru; new conflict freq 0.0): **outOfReach**
- `lluer|llué|luer` (parts luer; new conflict freq 0.0): **outOfReach**
- `boi|boî` (parts boi; new conflict freq 0.0): **outOfReach**
- `ou|u` (parts ou; new conflict freq 0.0): **outOfReach**
- `coi|coua|cua|qua|quoi` (parts coi, qua; new conflict freq 0.0): **outOfReach**
- `thine|tine|ttine` (parts tine; new conflict freq 0.0): **outOfReach**
- `baire|ber|bert|bère` (parts bert, bère; new conflict freq 0.0): **outOfReach**
- `ciel|tiel` (parts tiel, ciel; new conflict freq 0.0): **outOfReach**
- `illette|llette|llettes` (parts llette, illette; new conflict freq 0.0): **outOfReach**
- `laine|leine|len|llen|llène|lène` (parts lène; new conflict freq 0.2): **outOfReach**
- `bam|ban` (parts ban, bam; new conflict freq 0.0): **outOfReach**
- `psi|psy` (parts psy; new conflict freq 0.0): **outOfReach**
- `illage|illiage|llage|yage` (parts llage, illage; new conflict freq 0.0): **outOfReach**
- `ccro|chro|cro|croc` (parts cro; new conflict freq 0.0): **outOfReach**
- `mette|mmette|mète` (parts mette; new conflict freq 0.0): **outOfReach**
- `le|leus|leux|lle|lleux` (parts leux, lleux; new conflict freq 0.0): **outOfReach**
- `lir|lire|llir|llyre` (parts lir, lire; new conflict freq 0.0): **outOfReach**
- `lic|lique|llique` (parts lique, llique; new conflict freq 0.8): **outOfReach**
- `ssus|sus` (parts sus; new conflict freq 0.0): **outOfReach**
- `dro|drô` (parts dro; new conflict freq 0.0): **outOfReach**
- `riste|rriste|ryste` (parts riste; new conflict freq 0.0): **outOfReach**
- `tache|ttache|tâche` (parts tache; new conflict freq 0.0): **outOfReach**
- `lite|litent|lites|lithe|llite|lyte` (parts lite, lithe, litent; new conflict freq 0.0): **outOfReach**
- `caire|cker|ker|kère|quaire|querre|quère` (parts ker, caire; new conflict freq 0.0): **outOfReach**
- `brou|brouh` (parts brou; new conflict freq 0.0): **outOfReach**
- `illard|llard|llart|yard` (parts illard, llard; new conflict freq 0.0): **outOfReach**
- `illon|ion|llion|llon|llons|yon` (parts llon, illon; new conflict freq 0.0): **outOfReach**
- `rion|rions|ryon` (parts rions; new conflict freq 0.0): **outOfReach**
- `pom|pon` (parts pom, pon; new conflict freq 0.0): **outOfReach**
- `man|mane` (parts man, mane; new conflict freq 0.0): **outOfReach**
- `main|men|min` (parts main; new conflict freq 0.0): **outOfReach**
- `niste|nniste` (parts niste, nniste; new conflict freq 0.0): **outOfReach**
- `ceux|seux|sseux` (parts sseux; new conflict freq 0.0): **outOfReach**
- `tral|trales` (parts tral; new conflict freq 0.1): **outOfReach**
- `far|phar` (parts far; new conflict freq 0.0): **outOfReach**
- `llure|lure` (parts lure; new conflict freq 0.0): **outOfReach**
- `nhomme|nome|num` (parts num, nome; new conflict freq 0.0): **outOfReach**
- `trau|tro|trô` (parts tro; new conflict freq 0.0): **outOfReach**
- `con|cond` (parts con; new conflict freq 0.0): **outOfReach**
- `as|asth|az|hase` (parts as; new conflict freq 0.0): **outOfReach**
- `tadt|tate|tâtes` (parts tate, tâtes; new conflict freq 0.0): **outOfReach**
- `choir|choire` (parts choir; new conflict freq 0.0): **outOfReach**
- `rail|raille|railles|raï|rraille` (parts rail; new conflict freq 0.0): **outOfReach**
- `chaie|chet` (parts chet; new conflict freq 0.0): **outOfReach**
- `dia|diat` (parts dia; new conflict freq 0.0): **outOfReach**
- `gnard|gnare` (parts gnard; new conflict freq 0.0): **outOfReach**
- `plom|plon` (parts plon, plom; new conflict freq -0.0): **outOfReach**
- `crai|cre|crè|cré|crê` (parts crê; new conflict freq 0.0): **outOfReach**
- `pie|pied|pié` (parts pié; new conflict freq 0.2): **outOfReach**
- `gai|gaî|ghe|gue|guê` (parts gue; new conflict freq 0.6): **outOfReach**
- `bain|bbin|bin` (parts bin, bain; new conflict freq 0.0): **outOfReach**
- `gli|gly` (parts gli, gly; new conflict freq 0.0): **outOfReach**
- `ge|gei|gey|gè|gê|je` (parts gei; new conflict freq 0.0): **outOfReach**
- `tern|terne|ternes` (parts terne; new conflict freq 0.0): **outOfReach**
- `sad|sade|ssade|çade` (parts ssade; new conflict freq 0.0): **outOfReach**
- `rick|rique|rrhique|rrick|rrique` (parts rique; new conflict freq 0.0): **outOfReach**
- `tri|trii` (parts tri; new conflict freq 0.0): **outOfReach**
- `cit|cite|citent|cites|cyte|scite|scitent|scites|site|ssit|ssite|ssitent|ssites` (parts cite, citent, cites; new conflict freq 0.0): **outOfReach**
- `tex|thex` (parts tex; new conflict freq 0.0): **outOfReach**
- `cas|casse|kas` (parts cas; new conflict freq 0.0): **outOfReach**
- `pic|pik|pique|ppique` (parts pique; new conflict freq 0.0): **outOfReach**
- `geon|jon|jonc` (parts geon; new conflict freq 0.0): **outOfReach**
- `rine|rrine` (parts rine; new conflict freq 0.0): **outOfReach**
- `gnan|gnant` (parts gnant; new conflict freq 0.0): **outOfReach**
- `illot|llaud|llo|llot|yot|ïaut` (parts illot; new conflict freq 0.0): **outOfReach**
- `vet|vete|vette|vète` (parts vette; new conflict freq 0.0): **outOfReach**
- `ger|gger|ggeur|gueur` (parts gueur, gger; new conflict freq 0.0): **outOfReach**
- `vier|viers|viller|vié` (parts vier; new conflict freq 0.0): **outOfReach**
- `chro|craw|cro` (parts cro, chro; new conflict freq 0.0): **outOfReach**
- `soir|soire` (parts soir; new conflict freq 0.0): **outOfReach**
- `cive|sive|ssive` (parts sive; new conflict freq 0.0): **outOfReach**
- `raine|ren|renne|rennes|rraine|rène` (parts rène; new conflict freq 0.1): **outOfReach**
- `dar|dard|ddar` (parts dard; new conflict freq 0.0): **outOfReach**
- `pate|pathe|patte` (parts pathe; new conflict freq 0.0): **outOfReach**
- `nance|nances|nence|nnance` (parts nance, nence; new conflict freq 0.0): **outOfReach**
- `bré|brée` (parts bré; new conflict freq 0.0): **outOfReach**
- `bour|bourg|bours` (parts bour; new conflict freq 0.0): **outOfReach**
- `nim|nime|nyme` (parts nyme; new conflict freq 0.0): **outOfReach**
- `gom|gon` (parts gon; new conflict freq 0.0): **outOfReach**
- `vie|viei` (parts viei; new conflict freq 0.0): **outOfReach**
- `frai|fraî|fré|phré` (parts fré; new conflict freq 0.0): **outOfReach**
- `cure|qûre` (parts cure; new conflict freq 0.0): **outOfReach**
- `gai|gaie|gais|gay|guais|guet` (parts guet; new conflict freq 0.0): **outOfReach**
- `nin|nnain|nnin` (parts nin; new conflict freq 0.0): **outOfReach**
- `bric|brique` (parts brique; new conflict freq 0.0): **outOfReach**
- `grim|grin` (parts grim, grin; new conflict freq 0.0): **outOfReach**
- `taise|thès|thèse|tès|tèse` (parts thèse; new conflict freq 0.0): **outOfReach**
- `lable|llable` (parts lable; new conflict freq 0.0): **outOfReach**
- `caud|cco|cho|cko|co|cquot|kgo|ko|qu'au|quo` (parts co, ko; new conflict freq 0.1): **outOfReach**
- `rrure|rure` (parts rrure, rure; new conflict freq 0.0): **outOfReach**
- `resse|rès` (parts resse; new conflict freq 0.0): **outOfReach**
- `ffin|ffine|fine|phine` (parts phine; new conflict freq 0.0): **outOfReach**
- `iste|ïste` (parts ïste, iste; new conflict freq 0.0): **outOfReach**
- `hon|om|on|un` (parts on, om; new conflict freq 0.0): **outOfReach**
- `teux|theux|tteux` (parts teux, tteux; new conflict freq 0.0): **outOfReach**
- `cha|chas|chat|sha|shad` (parts chat; new conflict freq 0.0): **outOfReach**
- `rien|rrien|ryen` (parts rien; new conflict freq 0.0): **outOfReach**
- `foi|foua` (parts foi; new conflict freq 0.0): **outOfReach**
- `chlée|cler` (parts cler; new conflict freq 0.0): **outOfReach**
- `mel|melle|mmel` (parts melle, mel; new conflict freq 0.0): **outOfReach**
- `spea|spee|spi` (parts spi; new conflict freq 0.0): **outOfReach**
- `enne|ène` (parts enne, ène; new conflict freq 0.0): **outOfReach**
- `hos|os` (parts hos, os; new conflict freq 0.0): **outOfReach**
- `cker|ckeur|coeur|ker|kkeur|queur` (parts queur, ker, cker; new conflict freq 0.4): **outOfReach**
- `ban|bant|ben` (parts ban, bant; new conflict freq 0.0): **outOfReach**
- `ccage|ckage|quage` (parts quage; new conflict freq 0.0): **outOfReach**
- `ger|jer` (parts ger; new conflict freq 0.0): **outOfReach**
- `chris|christ|cris` (parts cris; new conflict freq 0.0): **outOfReach**
- `ril|rile|ryl` (parts ril; new conflict freq 0.0): **outOfReach**
- `bro|brow` (parts bro; new conflict freq 0.0): **outOfReach**
- `xion|xtion` (parts xion; new conflict freq 0.0): **outOfReach**
- `ffler|fler|flée` (parts fler; new conflict freq 0.0): **outOfReach**
- `fflé|flé` (parts flé; new conflict freq 0.0): **outOfReach**
- `per|peur|pper|ppeur` (parts peur, per, ppeur, pper; new conflict freq 0.0): **outOfReach**
- `thisme|thysme|tisme|ttisme` (parts tisme; new conflict freq 0.0): **outOfReach**
- `mick|mics|mique` (parts mique; new conflict freq 0.7): **outOfReach**
- `can|cant|kan|quant|quent` (parts quant, quent, can, cant; new conflict freq 0.0): **outOfReach**
- `puce|pus` (parts pus; new conflict freq 0.0): **outOfReach**
- `spa|spah` (parts spa; new conflict freq 0.0): **outOfReach**
- `rice|ris|risse|rrice` (parts ris; new conflict freq 0.0): **outOfReach**
- `nnoir|noir|noire` (parts noir; new conflict freq 0.0): **outOfReach**
- `maire|mer|mere|mmaire|mmère|mère` (parts maire, mère; new conflict freq 0.0): **outOfReach**
- `chère|sher` (parts chère; new conflict freq 0.0): **outOfReach**
- `gi|gy|gî|ji` (parts gi, gy; new conflict freq 0.0): **outOfReach**
- `cif|scif|sif|ssif` (parts ssif, sif, cif; new conflict freq 0.0): **outOfReach**
- `cail|caille|quaille` (parts caille; new conflict freq 0.0): **outOfReach**
- `ping|pping` (parts ping; new conflict freq 0.0): **outOfReach**
- `ste|sté` (parts sté; new conflict freq 0.0): **outOfReach**
- `ine|ïne` (parts ïne, ine; new conflict freq 0.0): **outOfReach**
- `jou|joue` (parts jou; new conflict freq 0.0): **outOfReach**
- `som|son` (parts son; new conflict freq 0.0): **outOfReach**
- `omme|um` (parts um; new conflict freq 0.0): **outOfReach**
- `val|vol|vole` (parts val; new conflict freq 0.0): **outOfReach**
- `loo|lou|loue` (parts lou; new conflict freq 0.0): **outOfReach**
- `chlo|clau|clo|clô` (parts clo, chlo; new conflict freq 0.0): **outOfReach**
- `sière|zière` (parts sière; new conflict freq 0.0): **outOfReach**
- `cheur|sheur` (parts cheur; new conflict freq 0.0): **outOfReach**
- `ffian|fiant` (parts fiant; new conflict freq 0.0): **outOfReach**
- `illère|ière|llière|llère|yère` (parts illère, ière; new conflict freq 0.0): **outOfReach**
- `dace|das|dasse` (parts dasse; new conflict freq 0.0): **outOfReach**
- `gan|gand|gant|ggan|ghan|guent` (parts gant, gan; new conflict freq 0.0): **outOfReach**
- `pli|plii` (parts pli; new conflict freq 0.0): **outOfReach**
- `tesque|ttesque` (parts tesque; new conflict freq 0.0): **outOfReach**
- `mur|mure` (parts mure; new conflict freq 0.0): **outOfReach**
- `a|at|â` (parts a; new conflict freq 0.0): **outOfReach**
- `ffrer|ffré|frer|fré|phré` (parts ffrer; new conflict freq 0.2): **outOfReach**
- `fage|ffage|phage` (parts ffage, phage; new conflict freq 0.0): **outOfReach**
- `lisme|llisme` (parts lisme; new conflict freq 0.0): **outOfReach**
- `nisme|nnisme` (parts nisme, nnisme; new conflict freq 0.0): **outOfReach**
- `geur|jeur` (parts geur; new conflict freq 0.0): **outOfReach**
- `neu|neux|nneux` (parts neux, nneux; new conflict freq 0.0): **outOfReach**
- `dol|dole` (parts dole; new conflict freq 0.0): **outOfReach**
- `cquier|kier|quier` (parts quier; new conflict freq 0.0): **outOfReach**
- `glau|glo` (parts glo; new conflict freq 0.0): **outOfReach**
- `drai|dre|drey` (parts dre; new conflict freq 0.0): **outOfReach**
- `cade|ccade|quade` (parts cade; new conflict freq 0.0): **outOfReach**
- `geois|joie` (parts geois; new conflict freq 0.0): **outOfReach**
- `ning|nning` (parts ning; new conflict freq 0.0): **outOfReach**
- `mas|masse` (parts mas; new conflict freq 0.0): **outOfReach**
- `flé|phlé` (parts flé; new conflict freq 0.0): **outOfReach**
- `ser|seur|zer|zeur` (parts seur, ser; new conflict freq 0.0): **outOfReach**
- `bla|blâ` (parts bla; new conflict freq 0.0): **outOfReach**
- `rat|rate|ratte` (parts rate; new conflict freq 0.0): **outOfReach**
- `if|ïf` (parts if; new conflict freq 0.0): **outOfReach**
- `char|chard|chards|chart` (parts chard; new conflict freq 0.0): **outOfReach**
- `dair|daire|der|dère` (parts daire, dère; new conflict freq 0.0): **outOfReach**
- `fo|pho` (parts fo, pho; new conflict freq 0.0): **outOfReach**
- `va|vas|vat|vats` (parts va; new conflict freq 0.1): **outOfReach**
- `ia|illat|lla|llat|ya|yat|ïa` (parts ya, lla; new conflict freq 0.3): **outOfReach**
- `fla|flah|flâ` (parts fla, flâ; new conflict freq 0.0): **outOfReach**
- `nase|naze` (parts nase; new conflict freq 0.0): **outOfReach**
- `lim|lin|lym|lyn` (parts lin, lym; new conflict freq 0.0): **outOfReach**
- `grou|gru` (parts grou; new conflict freq 0.0): **outOfReach**
- `ves|wes` (parts ves; new conflict freq 0.0): **outOfReach**
- `rhomme|rum` (parts rum; new conflict freq 0.0): **outOfReach**
- `rium|ryum` (parts rium; new conflict freq 0.0): **outOfReach**
- `pe|peu` (parts pe, peu; new conflict freq 0.0): **outOfReach**
- `chiste|chyste|sciste` (parts chiste; new conflict freq 0.0): **outOfReach**
- `ciste|siste|ssiste` (parts ciste, ssiste; new conflict freq 0.0): **outOfReach**
- `ec|ek|hec` (parts ec; new conflict freq 0.0): **outOfReach**
- `dic|dik` (parts dic; new conflict freq 0.1): **outOfReach**
- `daient|dais|dait|det` (parts dais, det; new conflict freq 0.0): **outOfReach**
- `sol|sole|ssole` (parts sol; new conflict freq 0.0): **outOfReach**
- `beur|beurre` (parts beur; new conflict freq 0.0): **outOfReach**
- `naise|nnaise|nèse` (parts nèse; new conflict freq 0.0): **outOfReach**
- `rou|rrou|rroux` (parts rou; new conflict freq 0.0): **outOfReach**
- `gau|go` (parts go, gau; new conflict freq 0.0): **outOfReach**
- `git|gite|gitent|gites` (parts gite; new conflict freq 0.0): **outOfReach**
- `ting|tting` (parts ting; new conflict freq 0.0): **outOfReach**
- `diaire|dière` (parts dière; new conflict freq 0.0): **outOfReach**
- `tille|ttille` (parts tille; new conflict freq 0.0): **outOfReach**
- `er|eur` (parts eur; new conflict freq 0.0): **outOfReach**
- `trage|ttrage` (parts trage; new conflict freq 0.0): **outOfReach**
- `cot|cote|cott|cotte` (parts cotte; new conflict freq 0.0): **outOfReach**
- `ique|ïk|ïque` (parts ïque, ique; new conflict freq 0.0): **outOfReach**
- `chou|schoo|shoo` (parts chou; new conflict freq 0.0): **outOfReach**
- `ote|otte` (parts ote; new conflict freq 0.0): **outOfReach**
- `hyp|ip` (parts hyp; new conflict freq 0.0): **outOfReach**
- `ger|gère` (parts gère; new conflict freq 0.0): **outOfReach**
- `cène|scène|sen` (parts cène; new conflict freq 0.0): **outOfReach**
- `lluche|luche` (parts luche; new conflict freq 0.0): **outOfReach**
- `drer|dré|drée` (parts drer, dré; new conflict freq 0.2): **outOfReach**
- `io|yo` (parts io; new conflict freq 0.0): **outOfReach**
- `bais|bet` (parts bet; new conflict freq 0.0): **outOfReach**
- `bar|bard|bare|bart` (parts bard, bar; new conflict freq 0.0): **outOfReach**
- `plan|plant` (parts plan; new conflict freq 0.0): **outOfReach**
- `thus|tuce|tus` (parts tus; new conflict freq 0.0): **outOfReach**
- `gas|gaz` (parts gas; new conflict freq 0.2): **outOfReach**
- `pice|pis` (parts pice; new conflict freq 0.0): **outOfReach**
- `dine|dines` (parts dine; new conflict freq 0.0): **outOfReach**
- `train|trim|trin` (parts trin; new conflict freq 0.0): **outOfReach**
- `gran|grand|grant` (parts grant; new conflict freq 0.0): **outOfReach**
- `roi|roie|rois|roît|rroi|rroie|rrois` (parts rois; new conflict freq 0.0): **outOfReach**
- `tho|to` (parts to; new conflict freq 0.0): **outOfReach**
- `bal|bale|ball|balle` (parts bal; new conflict freq 0.0): **outOfReach**
- `nate|nates|nathe|nnate` (parts nate; new conflict freq 0.0): **outOfReach**
- `dou|doub|doue|doux` (parts dou; new conflict freq 0.0): **outOfReach**
- `bul|bule` (parts bule; new conflict freq 0.0): **outOfReach**
- `me|meu` (parts meu; new conflict freq 0.0): **outOfReach**
- `hia|hya|ya` (parts ya; new conflict freq 0.0): **outOfReach**
- `air|aire|er|her` (parts her, er; new conflict freq 0.0): **outOfReach**
- `cause|chose|cose|khoze|kose` (parts cose; new conflict freq 0.0): **outOfReach**
- `ffrage|frage` (parts ffrage; new conflict freq 0.0): **outOfReach**
- `gu|gus|guë` (parts gu; new conflict freq 0.0): **outOfReach**
- `zi|zy` (parts zi, zy; new conflict freq 0.0): **outOfReach**
- `flam|flan` (parts flam, flan; new conflict freq 0.0): **outOfReach**
- `d'homme|dom|dome|dum` (parts dum; new conflict freq 0.0): **outOfReach**
- `lor|lord|lore` (parts lore; new conflict freq 0.0): **outOfReach**
- `isme|ïsme` (parts ïsme, isme; new conflict freq 0.0): **outOfReach**
- `hié|yé` (parts hié; new conflict freq 0.0): **outOfReach**
- `be|beu` (parts be; new conflict freq 0.0): **outOfReach**
- `boos|bous` (parts bous; new conflict freq 0.0): **outOfReach**
- `llose|lose` (parts lose; new conflict freq 0.0): **outOfReach**
- `thore|tor|tore|tors` (parts tor; new conflict freq 0.0): **outOfReach**
- `clou|cloue|clow` (parts clou; new conflict freq 0.0): **outOfReach**
- `daine|den|dène` (parts den; new conflict freq 0.0): **outOfReach**
- `chisme|scisme` (parts chisme; new conflict freq 0.0): **outOfReach**
- `ccio|cho` (parts cho; new conflict freq 0.0): **outOfReach**
- `set|sette|zette` (parts sette; new conflict freq 0.0): **outOfReach**
- `seux|zeux` (parts seux; new conflict freq 0.0): **outOfReach**
- `geat|ja|jah|jat` (parts ja; new conflict freq 0.0): **outOfReach**
- `bette|bète|bête` (parts bette; new conflict freq 0.0): **outOfReach**
- `ar|ard` (parts ard; new conflict freq 0.0): **outOfReach**
- `cya|scia|scie|sia` (parts cya; new conflict freq 0.0): **outOfReach**
- `ce|cher|tcher` (parts ce, tcher; new conflict freq 0.0): **outOfReach**
- `ide|ides|yde|ïd|ïde` (parts ïde, ïd; new conflict freq 0.0): **outOfReach**
- `tein|tim|tym` (parts tein, tim; new conflict freq 0.0): **outOfReach**
- `pit|pite|pitent|pites` (parts pite, pitent, pites; new conflict freq 0.0): **outOfReach**
- `cisme|sisme|ssisme` (parts cisme; new conflict freq 0.0): **outOfReach**
- `hui|huî` (parts hui; new conflict freq 0.0): **outOfReach**
- `piste|ppiste` (parts piste; new conflict freq 0.0): **outOfReach**
- `tit|tite|ttite` (parts tite; new conflict freq 0.0): **outOfReach**
- `cai|ché|ke|kei|khé|ké|que|qué` (parts ké; new conflict freq 0.0): **outOfReach**
- `quim|quin` (parts quin; new conflict freq 0.0): **outOfReach**
- `rhin|rhyn|rim|rin` (parts rin; new conflict freq 0.0): **outOfReach**
- `ddhiste|diste` (parts diste; new conflict freq 0.0): **outOfReach**
- `ien|yen|yin|ïen` (parts ïen, ien; new conflict freq 0.0): **outOfReach**
- `chu|schu` (parts chu; new conflict freq 0.0): **outOfReach**
- `chage|shage` (parts chage; new conflict freq 0.0): **outOfReach**
- `ad|ade` (parts ade; new conflict freq 0.0): **outOfReach**
- `ponc|punc` (parts ponc; new conflict freq 0.0): **outOfReach**
- `ciable|tiable` (parts ciable; new conflict freq 0.0): **outOfReach**
- `thrite|trite` (parts trite; new conflict freq 0.0): **outOfReach**
- `tiche|tish|ttish` (parts tiche; new conflict freq 0.0): **outOfReach**
- `gam|gan` (parts gan, gam; new conflict freq 0.0): **outOfReach**
- `ling|lling` (parts ling; new conflict freq 0.0): **outOfReach**
- `nome|nôme` (parts nome; new conflict freq 0.0): **outOfReach**
- `ride|rides|rride` (parts ride; new conflict freq 0.0): **outOfReach**
- `tane|thane|ttan` (parts tane, thane; new conflict freq 0.0): **outOfReach**
- `meu|mu` (parts meu; new conflict freq 0.0): **outOfReach**
- `mac|mak|maque` (parts mac; new conflict freq 0.0): **outOfReach**
- `rienne|ryenne` (parts rienne; new conflict freq 0.0): **outOfReach**
- `bleu|bleux` (parts bleu; new conflict freq 0.0): **outOfReach**
- `liaire|lière|lliaire|llière` (parts lière; new conflict freq 0.0): **outOfReach**
- `hour|our` (parts our; new conflict freq 0.0): **outOfReach**
- `door|dor|dore` (parts dor; new conflict freq 0.0): **outOfReach**
- `bleu|blu` (parts bleu; new conflict freq 0.0): **outOfReach**
- `resque|rresque` (parts resque; new conflict freq 0.0): **outOfReach**
- `can|cane` (parts cane; new conflict freq 0.0): **outOfReach**
- `tam|tame|thame|tâmes` (parts tâmes; new conflict freq 0.0): **outOfReach**
- `sien|zien` (parts sien; new conflict freq 0.0): **outOfReach**
- `ccus|cus` (parts cus; new conflict freq 0.0): **outOfReach**
- `gre|gré|grée|grê` (parts gré; new conflict freq 0.0): **outOfReach**
- `geau|geaud|geot|jo` (parts jo; new conflict freq 0.0): **outOfReach**
- `sar|sard|ssar|ssard|ssart|çard` (parts ssard; new conflict freq 0.0): **outOfReach**
- `val|wal` (parts val; new conflict freq 0.0): **outOfReach**
- `paul|pole` (parts pole; new conflict freq 0.0): **outOfReach**
- `toche|tosh` (parts toche; new conflict freq 0.0): **outOfReach**
- `tom|tum` (parts tum; new conflict freq 0.0): **outOfReach**
- `bic|bique` (parts bique; new conflict freq 0.0): **outOfReach**
- `fal|fale|phal|phale` (parts phale; new conflict freq 0.0): **outOfReach**
- `pac|pack` (parts pac; new conflict freq 0.0): **outOfReach**
- `thol|tol|tole|toll` (parts tole; new conflict freq 0.0): **outOfReach**
- `grai|gre|grè|grê` (parts grai; new conflict freq 0.0): **outOfReach**
- `gus|gusse` (parts gus; new conflict freq 0.0): **outOfReach**
- `mo|moh|moo` (parts mo; new conflict freq 0.0): **outOfReach**
- `lloc|lloque|loch|lock|locks|loque` (parts loque; new conflict freq 0.0): **outOfReach**
- `ol|ole` (parts ole; new conflict freq 0.0): **outOfReach**
- `cryp|kryp` (parts cryp; new conflict freq 0.0): **outOfReach**
- `gette|gète|jette` (parts gette; new conflict freq 0.0): **outOfReach**
- `flai|fle` (parts fle; new conflict freq 0.0): **outOfReach**
- `rose|rrhose` (parts rose; new conflict freq 0.0): **outOfReach**
- `lium|llium` (parts lium, llium; new conflict freq 0.0): **outOfReach**
- `fai|fe|feu` (parts feu; new conflict freq 0.0): **outOfReach**
- `gneu|gneux|nieux` (parts gneux; new conflict freq 0.0): **outOfReach**
- `tal|thal` (parts tal; new conflict freq 0.0): **outOfReach**
- `treur|ttreur` (parts treur; new conflict freq 0.0): **outOfReach**
- `fiste|phiste` (parts phiste; new conflict freq 0.0): **outOfReach**
- `fane|phane` (parts phane; new conflict freq 0.0): **outOfReach**
- `rho|rhu|ro` (parts ro; new conflict freq 0.0): **outOfReach**
- `labe|llabe` (parts llabe; new conflict freq 0.0): **outOfReach**
- `croo|crou|croû|cru|crui|krou` (parts crou; new conflict freq 0.0): **outOfReach**
- `ddite|dit|dite|ditent|dites|dith|dyte` (parts dite, dites, ditent; new conflict freq 0.0): **outOfReach**
- `llus|lus` (parts lus; new conflict freq 0.0): **outOfReach**
- `nim|nym` (parts nym, nim; new conflict freq 0.0): **outOfReach**
- `fein|fin` (parts fin; new conflict freq 0.0): **outOfReach**
- `dienne|diène` (parts dienne; new conflict freq 0.0): **outOfReach**
- `miau|myo` (parts myo; new conflict freq 0.0): **outOfReach**
- `tose|tôse` (parts tose; new conflict freq 0.0): **outOfReach**
- `sal|sales|zal` (parts sal; new conflict freq 0.0): **outOfReach**
- `late|llat` (parts late; new conflict freq 0.0): **outOfReach**
- `pic|pick` (parts pic; new conflict freq 0.0): **outOfReach**
- `guim|guin` (parts guin; new conflict freq 0.0): **outOfReach**
- `flu|flû` (parts flu; new conflict freq 0.0): **outOfReach**
- `bage|bages` (parts bage; new conflict freq 0.0): **outOfReach**
- `pien|piens` (parts pien; new conflict freq 0.0): **outOfReach**
- `bran|brant` (parts brant; new conflict freq 0.0): **outOfReach**
- `fiable|phiable` (parts fiable; new conflict freq 0.0): **outOfReach**
- `beu|bu` (parts beu; new conflict freq 0.0): **outOfReach**
- `cur|kur` (parts cur; new conflict freq 0.0): **outOfReach**
- `gam|game` (parts game; new conflict freq 0.0): **outOfReach**
- `amb|emb` (parts amb, emb; new conflict freq 0.0): **outOfReach**
- `llâtre|lâtre` (parts lâtre; new conflict freq 0.0): **outOfReach**
- `nia|nnia` (parts nia; new conflict freq 0.0): **outOfReach**
- `ben|bim` (parts ben; new conflict freq 0.0): **outOfReach**
- `goi|goua|gua` (parts gua, goua; new conflict freq 0.0): **outOfReach**
- `ddhisme|disme|dysme` (parts disme; new conflict freq 0.0): **outOfReach**
- `chro|cro` (parts cro; new conflict freq 0.0): **outOfReach**
- `stri|strie` (parts stri; new conflict freq 0.0): **outOfReach**
- `ssim|ssime|zim` (parts ssime; new conflict freq 0.0): **outOfReach**
- `cienne|sienne|ssienne|tienne` (parts cienne; new conflict freq 0.0): **outOfReach**
- `lesque|llesque` (parts lesque; new conflict freq 0.0): **outOfReach**
- `fisme|phisme` (parts phisme; new conflict freq 0.0): **outOfReach**
- `nol|nole` (parts nol; new conflict freq 0.0): **outOfReach**
- `cau|cho|coh|ko|quo` (parts cho, ko; new conflict freq 0.0): **outOfReach**
- `pli|plie` (parts pli; new conflict freq 0.0): **outOfReach**
- `lloche|loche` (parts loche; new conflict freq 0.0): **outOfReach**
- `llum|lom|lome|lum` (parts lum; new conflict freq 0.0): **outOfReach**
- `trisme|ttrisme` (parts trisme; new conflict freq 0.0): **outOfReach**
- `ienne|yenne` (parts ienne; new conflict freq 0.0): **outOfReach**
- `bbeux|beu|beux` (parts beux; new conflict freq 0.0): **outOfReach**
- `bbleur|bleur` (parts bleur; new conflict freq 0.0): **outOfReach**
- `hin|in` (parts in; new conflict freq 0.0): **outOfReach**
- `thisme|tisme` (parts tisme; new conflict freq 0.0): **outOfReach**
- `nisme|nnisme` (parts nisme; new conflict freq 0.0): **outOfReach**
- `el|hel` (parts hel; new conflict freq 0.0): **outOfReach**
- `neuse|nneuse` (parts neuse; new conflict freq 0.0): **outOfReach**

## Overlaps among selected rules (must all be < 0.5)

- none >= 0.05

## Overlap skips during selection (0)

- none
