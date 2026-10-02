# Affix rules (Phase 3 + 4 result, DESIGN_2026-09-27-affix-rule-selection.md; single-generator pool, PLAN_2026-09-28)

Constants: RULE_BUDGET=30, MAX_RULE_FORMS=6, EXCEPTION_ALPHA=2.0, EXCLUSION_COST=5.0, FORM_COST=100.0, SWAP_CANDIDATES=20, SWAP_PASSES=3, RULE_OVERLAP_MAX=0.5, MAX_EXCEPTION_RATE=0.05, GROWTH_MIN_EXPAND=5.0, GROWTH_MAX_DEPTH=4, MAX_SLOT_EXCLUSIONS=3, GROWTH_MAX_EXCEPTION_SHARE=0.05.

Note: bare verb-infinitive-ending candidates (isVerbEndingFragment) are left UNFILTERED, per the user's 2026-09-27 decision to let them compete on score.

Selected rules with attestedShare < 0.5 (the old stem-attestation filter would have rejected most of their carriers; candidate pseudo-affixes like `ma-`): **10** -- `é`, `ain|hin|im|in`, `ai|aî|e|ei|hai|he|hê|é`, `au`, `der|dé|dée`, `ra|rai|raie|re|rhé|ré|réh`, `pa`, `e|hi|hy|i|y|î`, `o`, `de|dea|di|die|dis|dy|dî`

## Savings curve (cumulative total after each acceptance, 1..40)

8503, 15688, 21790, 27333, 32777, 37345, 42038, 46670, 51343, 56070, 60735, 64308, 67840, 71140, 74396, 77417, 80600, 83249, 85658, 88825, 91294, 93677, 96132, 98410, 100625, 102820, 104950, 108021, 109931, 111720

## 1. suffix `ment` -- keys (16, 20, 25) = `-jtm`

forms: `ment`(k=1), `·[C{1,2}[eui]+]ment`(k=2)
- score 8503.2, strokeFreqSaved 8763.2, keySimilarity 0.44 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.76; exception rate 0.0%; top categories: ADV 60%, NOM 39%, ADJ 0%
- word exceptions 1 (freq 0.0); scope fallbacks 32
- top exceptions: blèsement
    moment: mae/m@ -> maejtm
    seulement: s@/mt@a/m@ -> s@jtm
    tellement: tie/mt@a/m@ -> tiejtm
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/ajktm
    sûrement: s@i/R@a/m@ -> s@ijtm
    complètement: kai/pmtie/t@a/m@ -> kai/pmtiejtm

## 2. prefix `am|an|ant|em|en|ench|enh|ham|han|hen` -- keys (3, 6, 18) = `sm-k`

forms: `am|an|ant|em|en|ench|enh|ham|han|hen`(k=1), `am|an|ant|em|en|ench|enh|ham|han|hen[en:C{1,2}@]·`(k=2)
- score 7185.1, strokeFreqSaved 7578.5, keySimilarity -0.44 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.54; exception rate 0.7%; top categories: VER 48%, NOM 33%, ADV 10%
- fused spelling variants: am, an, ant, em, en, ench, enh, ham, han, hen (new conflict freq 3.0)
- word exceptions 50 (freq 61.7); scope fallbacks 34
- top exceptions: engagé, engager, engagée, engrais, envol, engagés, engagez, engagé, engagé, entassés
    enfants: @/kp@/-s -> kspm@k/-s
    enfant: @/kp@ -> kspm@k
    enfin: @/kpaie -> kspmaiek
    entendu: @/t@/pv@i -> spvm@ik
    ensemble: @/s@jl -> sm@jkl
    envie: @/vi -> svmik

## 3. prefix `re|reh` -- keys (9, 18) = `w-k`

forms: `re|reh`(k=1)
- score 6102.2, strokeFreqSaved 6199.8, keySimilarity -0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.82; exception rate 0.6%; top categories: VER 75%, NOM 22%, ADJ 3%
- fused spelling variants: re, reh (new conflict freq 0.0)
- word exceptions 40 (freq 48.8); scope fallbacks 0
- top exceptions: remords, relax, requin, relax, requins, relis, rené, recoins, relique, reliques
    revoir: R@a/vwaR -> vwakR
    regardez: R@a/ksaR/pve/-k -> kswakR/pve/-k
    reviens: R@a/vRwaie/-k -> vRwaiek/-k
    regarder: R@a/ksaR/pve/-l -> kswakR/pve/-l
    retour: R@a/t@eR -> tw@ekR
    retard: R@a/taR -> twakR

## 4. suffix `ccion|cion|cyon|sion|ssion|tion|tions` -- keys (16, 17, 20) = `-jst`

forms: `ccion|cion|cyon|sion|ssion|tion|tions`(k=1), `·[tion:C*[ai]]ccion|cion|cyon|sion|ssion|tion|tions`(k=2)
- score 5542.8, strokeFreqSaved 5915.0, keySimilarity 0.66
- attestedShare 0.84; exception rate 0.2%; top categories: NOM 96%, ONO 4%, ADJ 0%
- fused spelling variants: ccion, cion, cyon, sion, ssion, tion, tions (new conflict freq 0.1)
- word exceptions 4 (freq 101.1); scope fallbacks 14
- top exceptions: impression, caution, impressions, cautions
    attention: a/t@/sRwai -> a/t@jst
    attention: a/t@/sRwai -> a/t@jst
    situation: si/t@a/sRwai -> si/t@ajst
    mission: mi/sRwai -> mijst
    félicitations: kpe/mti/si/ta/sRwai/-s -> kpe/mti/sijst/-s

## 5. prefix `é` -- keys (2, 5) = `kv-`

forms: `é`(k=1)
- score 5443.4, strokeFreqSaved 5449.0, keySimilarity -1.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.37; exception rate 0.1%; top categories: VER 46%, NOM 39%, ADJ 11%
- word exceptions 9 (freq 2.8); scope fallbacks 0
- top exceptions: épi, équité, épis, édit, édits, évitée, équidés, évitées, équités
    écoute: e/k@et -> kv@et
    étaient: e/tie/-st -> kvtie/-st
    école: e/kel -> kvel
    état: e/ta -> kvta
    écrit: e/kRi -> kvRi
    équipe: e/kijk -> kvijk

## 6. prefix `ain|hin|im|in` -- keys (7, 14, 16) = `tej`

forms: `ain|hin|im|in`(k=1), `ain|hin|im|in[in+té]·`(k=2)
- score 4727.3, strokeFreqSaved 4832.7, keySimilarity -0.19 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.49; exception rate 0.1%; top categories: NOM 33%, VER 33%, ADJ 29%
- fused spelling variants: ain, hin, im, in (new conflict freq 0.0)
- word exceptions 4 (freq 2.7); scope fallbacks 0
- top exceptions: indemne, indemnes, insights, intrait
    importe: aie/petR -> ptejtR
    ainsi: aie/si -> stiej
    important: aie/peR/t@ -> ptejR/t@
    impossible: aie/pae/sijl -> ptaej/sijl
    inquiète: aie/kRwiet -> ktRwiejt
    intérieur: aie/te/Rw@R -> tRw@ejR

## 7. prefix `de` -- keys (2, 6, 19) = `km-d`

forms: `de`(k=1), `de[man|ve]·`(k=2)
- score 4692.3, strokeFreqSaved 4792.3, keySimilarity 0.22 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.80; exception rate 0.0%; top categories: VER 65%, ADV 20%, NOM 9%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    demain: pv@a/maie -> kmaied
    demande: pv@a/m@d -> km@d
    devrais: pv@a/vRie/-k -> kvmRied/-k
    demandé: pv@a/m@/pve -> kpvmed
    devrait: pv@a/vRie -> kvmRied
    devant: pv@a/v@ -> kvm@d

## 8. prefix `ai|aî|e|ei|hai|he|hê|é` -- keys (5, 18, 19) = `v-kd`

forms: `ai|aî|e|ei|hai|he|hê|é`(k=1), `ai|aî|e|ei|hai|he|hê|é[e:ksky|kspli|sE|n°]·`(k=2)
- score 4673.2, strokeFreqSaved 4803.2, keySimilarity -0.44 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.35; exception rate 0.0%; top categories: VER 73%, NOM 17%, ADJ 9%
- fused spelling variants: ai, aî, e, ei, hai, he, hê, é (new conflict freq 0.1)
- word exceptions 0 (freq 0.0); scope fallbacks 6
    aider: ie/pve/-l -> pvekd/-l
    excusez: ie/ks@i/twe/-k -> vtwekd/-k
    aimerais: ie/m@a/Rie/-k -> vm@akd/Rie/-k
    essaie: ie/sie -> sviekd
    essayer: ie/sie/Rwe/-l -> vRwekd/-l
    essayé: ie/siej/e -> sviejkd/e

## 9. prefix `de|des|dé|déh` -- keys (5, 9, 18) = `vw-k`

forms: `de|des|dé|déh`(k=1)
- score 4665.5, strokeFreqSaved 4975.9, keySimilarity -0.50 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.63; exception rate 1.3%; top categories: VER 58%, NOM 28%, ADJ 13%
- fused spelling variants: de, des, dé, déh (new conflict freq 3.5)
- word exceptions 130 (freq 155.2); scope fallbacks 0
- top exceptions: début, débarque, dépit, déçu, débuts, dévoiler, dépanner, débarquent, dédie, déçue
    désolé: pve/twae/mte -> vtwaek/mte
    désolé: pve/twae/mte -> vtwaek/mte
    désolée: pve/twae/mte/-j -> vtwaek/mte/-j
    décidé: pve/si/pve -> svwik/pve
    désolée: pve/twae/mte/-j -> vtwaek/mte/-j

## 10. suffix `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` -- keys (16, 17, 19) = `-jsd`

forms: `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé`(k=1), `·[cé:m@]cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé`(k=2)
- score 4632.0, strokeFreqSaved 4732.0, keySimilarity 0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.66; exception rate 0.0%; top categories: VER 85%, ADV 9%, ADJ 3%
- fused spelling variants: cer, cé, cée, cés, scer, se, ser, sser, ssez, ssée, sé (new conflict freq 89.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    assez: a/se -> ajsd
    passer: pa/se/-l -> pajsd/-l
    passé: pa/se -> pajsd
    laissez: mtie/se/-k -> mtiejsd/-k
    laisser: mtie/se/-l -> mtiejsd/-l
    pensé: p@/s*e -> p*@jsd

## 11. suffix `ter` -- keys (16, 20, 22) = `-jtn`

forms: `ter`(k=1)
- score 4568.5, strokeFreqSaved 4568.5, keySimilarity 0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.92; exception rate 0.0%; top categories: VER 100%, NOM 0%, ADJ 0%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    rester: Ries/te/-l -> Riejstn/-l
    arrêter: a/Rie/te/-l -> a/Riejtn/-l
    arrêtez: a/Rie/te/-k -> a/Riejtn/-k
    acheter: a/pm@a/te/-l -> a/pm@ajtn/-l
    restez: Ries/te/-k -> Riejstn/-k
    écoutez: e/k@e/te/-k -> e/k@ejtn/-k

## 12. prefix `au` -- keys (7, 8, 19) = `tR-d`

forms: `au`(k=1), `au[jour|to|tre|di]·`(k=2)
- score 3572.7, strokeFreqSaved 3673.4, keySimilarity 0.24 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.39; exception rate 0.2%; top categories: AUX 28%, ADV 23%, VER 22%
- word exceptions 1 (freq 0.3); scope fallbacks 0
- top exceptions: autisme
    aujourd'hui: ae/vt@eR/pv@ai -> pvtR@aid
    aurais: ae/Rie/-d -> tRied/-d
    aurait: ae/Rie -> tRied
    aucune: ae/k@in -> ktR@idn
    aura: ae/Ra -> tRad
    aucun: ae/k@aie -> ktR@aied

## 13. suffix `té` -- keys (19, 20, 25) = `-dtm`

forms: `té`(k=1), `·[C\{bv}{1,2}i]té`(k=2)
- score 3546.3, strokeFreqSaved 4047.2, keySimilarity 0.46 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.69; exception rate 0.4%; top categories: NOM 83%, VER 9%, ADJ 8%
- word exceptions 11 (freq 10.5); scope fallbacks 76
- top exceptions: gravité, limité, agilité, limités, lité, caté, agilités, lités, litée, litées
    côté: kae/te -> kaedtm
    vérité: ve/Ri/te -> vedtm
    sécurité: se/k@i/Ri/te -> se/k@idtm
    santé: s@/te -> s@dtm
    liberté: mti/svieR/te -> mti/sviedtRm
    société: sae/sRwe/te -> sae/sRwedtm

## 14. suffix `der|dé|dée` -- keys (18, 19, 25) = `-kdm`

forms: `der|dé|dée`(k=1), `·[dez|der|dé:gaR|m@]der|dé|dée`(k=2)
- score 3531.7, strokeFreqSaved 3638.5, keySimilarity 0.62
- attestedShare 0.31; exception rate 0.6%; top categories: VER 82%, NOM 17%, ADJ 2%
- fused spelling variants: der, dé, dée (new conflict freq 52.2)
- word exceptions 8 (freq 3.4); scope fallbacks 0
- top exceptions: codé, codée, codé, codées, codés, codée, coder, codés
    aider: ie/pve/-l -> iekdm/-l
    idée: i/pve -> ikdm
    regardez: R@a/ksaR/pve/-k -> R@akdm/-k
    demandé: pv@a/m@/pve -> pv@akdm
    demander: pv@a/m@/pve/-l -> pv@akdm/-l
    regarder: R@a/ksaR/pve/-l -> R@akdm/-l

## 15. suffix `ner|nez|nner|nnée|née|nées` -- keys (16, 17, 25) = `-jsm`

forms: `ner|nez|nner|nnée|née|nées`(k=1), `·[né:C{1,2}[i°]]ner|nez|nner|nnée|née|nées`(k=2)
- score 3256.2, strokeFreqSaved 3371.3, keySimilarity 0.04 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.57; exception rate 0.0%; top categories: VER 77%, NOM 23%, ADJ 0%
- fused spelling variants: ner, nez, nner, nnée, née, nées (new conflict freq 52.2)
- word exceptions 1 (freq 0.0); scope fallbacks 3
- top exceptions: tannées
    donné: pvae/mRe -> pvaejsm
    donner: pvae/mRe/-l -> pvaejsm/-l
    années: a/mRe/-s -> ajsm/-s
    journée: vt@eR/mRe -> vt@ejsRm
    année: a/mRe -> ajsm
    donnez: pvae/mRe/-k -> pvaejsm/-k

## 16. prefix `ra|rai|raie|re|rhé|ré|réh` -- keys (3, 4, 16) = `sp-j`

forms: `ra|rai|raie|re|rhé|ré|réh`(k=1), `ra|rai|raie|re|rhé|ré|réh[ré:a|fle|vE|C{1,2}y]·`(k=2)
- score 3183.4, strokeFreqSaved 3367.3, keySimilarity -0.27 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.49; exception rate 0.5%; top categories: VER 59%, NOM 32%, ADJ 7%
- fused spelling variants: ra, rai, raie, re, rhé, ré, réh (new conflict freq 0.3)
- word exceptions 17 (freq 7.0); scope fallbacks 14
- top exceptions: régner, régnez, régné, récria, récriai, récrié, récriée, récriées, récriés, récriaient
    réponse: Re/pais -> spaijs
    réussi: Re/@i/si -> sp@ij/si
    réponds: Re/pai/-k -> spaij/-k
    réveille: Re/v*iej -> spv*iej
    répondre: Re/paidR -> spaijdR
    réalité: Re/a/mti/te -> spmtij/te

## 17. prefix `pa` -- keys (2, 5, 18) = `kv-k`

forms: `pa`(k=1)
- score 3167.3, strokeFreqSaved 3171.3, keySimilarity -0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.27; exception rate 0.8%; top categories: NOM 49%, VER 38%, ADJ 12%
- word exceptions 13 (freq 2.0); scope fallbacks 0
- top exceptions: pager, pagaie, pagaie, patine, pagaies, papisme, pagaient, pagaies, pagé, paginer
    passer: pa/se/-l -> ksve/-l
    passé: pa/se -> ksve
    papa: pa/pa -> kpva
    parents: pa/R@/-s -> kvR@/-s
    patron: pa/tRai -> kvtRai
    passé: pa/se -> ksve

## 18. prefix `par` -- keys (8, 19) = `R-d`

forms: `par`(k=1)
- score 3071.0, strokeFreqSaved 3071.0, keySimilarity 0.30 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.66; exception rate 0.0%; top categories: VER 60%, NOM 15%, ADV 12%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    partir: paR/tiR -> tRidR
    parlé: paR/mte -> mtRed
    pardon: paR/pvai -> pvRaid
    partie: paR/ti -> tRid
    parti: paR/t*i -> tR*id
    parfois: paR/kpwa -> kpRwad

## 19. prefix `e|hi|hy|i|y|î` -- keys (16, 19) = `-jd`

forms: `e|hi|hy|i|y|î`(k=1), `e|hi|hy|i|y|î[i:[mn][aeiouy]]·`(k=2)
- score 3020.6, strokeFreqSaved 3200.0, keySimilarity -0.57 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.22; exception rate 0.3%; top categories: NOM 41%, VER 32%, ADJ 24%
- fused spelling variants: e, hi, hy, i, y, î (new conflict freq 0.2)
- word exceptions 7 (freq 4.7); scope fallbacks 14
- top exceptions: hissez, hisser, hissé, hissai, hissées, hissés, hissée
    idée: i/pve -> pvejd
    ira: i/Ra -> Rajd
    imagine: i/ma/vtin -> vtijdn
    ignore: i/waeR -> waejdR
    irai: i/Re/-t -> Rejd/-t
    inutile: i/mR@i/til -> tijdl

## 20. prefix `sa|sah` -- keys (5, 24) = `v-Z`

forms: `sa|sah`(k=1)
- score 2649.0, strokeFreqSaved 2649.5, keySimilarity -0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.82; exception rate 1.4%; top categories: VER 55%, NOM 32%, ONO 8%
- fused spelling variants: sa, sah (new conflict freq 0.0)
- word exceptions 14 (freq 0.2); scope fallbacks 0
- top exceptions: sableuse, saroual, sableuses, sarouals, sabelles, saboule, saboulent, saboules, samizdats, sanieuses
    savoir: sa/vwaR -> vwaRZ
    savez: sa/ve -> veZ
    salut: sa/mt@i -> vmt@iZ
    savais: sa/vie/-k -> vieZ/-k
    salut: sa/mt@i -> vmt@iZ
    savait: sa/vie -> vieZ

## 21. prefix `o` -- keys (16, 17, 19) = `-jsd`

forms: `o`(k=1), `o[C{1,2}i|kV]·`(k=2)
- score 2469.1, strokeFreqSaved 2584.1, keySimilarity 0.05 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.24; exception rate 0.0%; top categories: VER 39%, NOM 34%, ADJ 20%
- word exceptions 0 (freq 0.0); scope fallbacks 3
    ok: ae/k- -> k-jsd
    occupe: ae/k@ijk -> k@ijskd
    ok: ae/k- -> k-jsd
    occuper: ae/k@i/pe/-l -> pejsd/-l
    occasion: ae/ka/tRwai -> tRwaijsd
    offrir: ae/kpRiR -> kpRijsdR

## 22. prefix `pro|proh|prô` -- keys (4, 5, 8) = `pvR-`

forms: `pro|proh|prô`(k=1)
- score 2455.1, strokeFreqSaved 2455.1, keySimilarity 0.70
- attestedShare 0.68; exception rate 0.3%; top categories: NOM 56%, VER 28%, ADJ 12%
- fused spelling variants: pro, proh, prô (new conflict freq 0.0)
- word exceptions 4 (freq 0.0); scope fallbacks 0
- top exceptions: prodrome, prodromes, procréerai, procréerez
    problème: pRae/svmtiem -> spvmtRiem
    problèmes: pRae/svmtiem/-s -> spvmtRiem/-s
    propos: pRae/pae -> pvRae
    prochaine: pRae/pmien -> pvmRien
    promis: pRae/mi -> pvmRi
    probablement: pRae/sva/svmt@a/m@ -> spvRa/svmt@a/m@

## 23. suffix `ver` -- keys (16, 17, 18) = `-jsk`

forms: `ver`(k=1), `·[vé:Ri]ver`(k=2)
- score 2408.5, strokeFreqSaved 2508.5, keySimilarity 0.46 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.82; exception rate 0.0%; top categories: VER 100%, NOM 0%, ADJ 0%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    trouvé: tR@e/ve -> tR@ejsk
    trouver: tR@e/ve/-l -> tR@ejsk/-l
    arrivé: a/Ri/v*e -> *ajsk
    arriver: a/Ri/ve/-l -> a/Rijsk/-l
    sauver: sae/ve/-l -> saejsk/-l
    retrouver: R@a/tR@e/ve/-l -> R@a/tR@ejsk/-l

## 24. prefix `ce|sce|se` -- keys (3, 6) = `sm-`

forms: `ce|sce|se`(k=1)
- score 2382.7, strokeFreqSaved 2382.7, keySimilarity 0.50 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.64; exception rate 0.0%; top categories: VER 35%, NOM 28%, PRO:dem 16%
- fused spelling variants: ce, sce, se (new conflict freq 0.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    serait: s@a/Rie -> smRie
    celui: s@a/mt@ai -> smt@ai
    semaine: s@a/mien -> smien
    serai: s@a/Re/-t -> smRe/-t
    ceci: s@a/si -> smi
    semaines: s@a/mien/-s -> smien/-s

## 25. suffix `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` -- keys (16, 19, 21) = `-jdR`

forms: `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée`(k=1), `·[rer:p[aeiouy]|C*e|sy]rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée`(k=2)
- score 2277.8, strokeFreqSaved 2387.8, keySimilarity 0.59
- attestedShare 0.64; exception rate 0.1%; top categories: VER 93%, NOM 7%, AUX 0%
- fused spelling variants: rae, rai, raie, re, rer, rez, rrer, rrhée, rrée, rée (new conflict freq 17.9)
- word exceptions 1 (freq 0.0); scope fallbacks 2
- top exceptions: aurai
    tirer: ti/Re/-l -> tijdR/-l
    soirée: swa/Re -> swajdR
    tiré: ti/Re -> tijdR
    pleurer: pmt@ie/Re/-l -> pmt@iejdR/-l
    préparer: pRe/pa/Re/-l -> pRejdR/-l
    tirez: ti/Re/-k -> tijdR/-k

## 26. prefix `pou|pu` -- keys (4, 7, 18) = `pt-k`

forms: `pou|pu`(k=1)
- score 2215.0, strokeFreqSaved 2215.0, keySimilarity 0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.89; exception rate 0.0%; top categories: VER 86%, NOM 13%, ADJ 1%
- fused spelling variants: pou, pu (new conflict freq 0.2)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    pouvez: p@e/ve -> pvtek
    pourrait: p@e/Rie -> ptRiek
    pourrais: p@e/Rie/-k -> ptRiek/-k
    pouvoir: p@e/vwaR -> pvtwakR
    pouvais: p@e/vie/-k -> pvtiek/-k
    pouvait: p@e/vie -> pvtiek

## 27. prefix `de|dea|di|die|dis|dy|dî` -- keys (3, 16, 19) = `s-jd`

forms: `de|dea|di|die|dis|dy|dî`(k=1), `de|dea|di|die|dis|dy|dî[di:C{1,2}i]·`(k=2)
- score 2195.6, strokeFreqSaved 2295.6, keySimilarity 0.16 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.33; exception rate 0.0%; top categories: VER 49%, NOM 29%, ADJ 20%
- fused spelling variants: de, dea, di, die, dis, dy, dî (new conflict freq 0.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    dirait: pvi/Rie -> sRiejd
    difficile: pvi/kpi/sil -> sijdl
    disais: pvi/twie/-k -> stwiejd/-k
    disait: pvi/twie -> stwiejd
    dîner: pvi/mRe -> smRejd
    dirai: pvi/Re/-t -> sRejd/-t

## 28. suffix `ser|sée|zer|zé` -- keys (18, 22, 23) = `-knl`

forms: `ser|sée|zer|zé`(k=1), `·[sez:C*y]ser|sée|zer|zé`(k=2), `·[li]ser|sée|zer|zé`(k=2)
- score 2129.4, strokeFreqSaved 2354.4, keySimilarity 0.62
- attestedShare 0.70; exception rate 0.0%; top categories: VER 94%, NOM 6%, ADJ 0%
- fused spelling variants: ser, sée, zer, zé (new conflict freq 5.8)
- word exceptions 0 (freq 0.0); scope fallbacks 5
    excusez: ie/ks@i/twe/-k -> ieknl/-k
    poser: pae/twe/-l -> paeknl/-l
    utiliser: @i/ti/mti/twe/-l -> @i/tiknl/-l
    épouser: e/p@e/twe/-l -> e/p@eknl/-l
    amuser: a/m@i/twe/-l -> a/m@iknl/-l
    excuser: ie/ks@i/twe/-l -> ie/ks@iknl/-l

## 29. suffix `ger` -- keys (16, 24) = `-jZ`

forms: `ger`(k=1)
- score 1910.1, strokeFreqSaved 1910.1, keySimilarity 0.50 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- attestedShare 0.94; exception rate 0.0%; top categories: VER 88%, NOM 10%, ADJ 2%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    manger: m@/vte/-l -> m@jZ/-l
    changer: pm@/vte/-l -> pm@jZ/-l
    changé: pm@/vte -> pm@jZ
    danger: pv@/vte -> pv@jZ
    protéger: pRae/te/vte/-l -> pRae/tejZ/-l
    mangé: m@/vte -> m@jZ

## 30. suffix `cher` -- keys (9, 24, 25) = `w-Zm`

forms: `cher`(k=1)
- score 1789.2, strokeFreqSaved 1789.2, keySimilarity 0.50
- attestedShare 0.79; exception rate 0.0%; top categories: VER 96%, NOM 4%, ADJ 0%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    chercher: pmieR/pme/-l -> pmwieRZm/-l
    marcher: maR/pme/-l -> mwaRZm/-l
    coucher: k@e/pme/-l -> kw@eZm/-l
    cacher: ka/pme/-l -> kwaZm/-l
    empêcher: @/pe/pme/-l -> @/pweZm/-l
    touché: t@e/pm*e -> tw*@eZm

## Sibling pairs (candidateSim >= FAMILY_LINK_SIM, out of scope for v1)

- ter ~ té (sim 1.00)
- au ~ o (sim 1.00)
- re|reh ~ ra|rai|raie|re|rhé|ré|réh (sim 0.75)
- de ~ de|des|dé|déh (sim 0.75)
- ver ~ ger (sim 0.67)
- ter ~ ver (sim 0.67)
- pa ~ par (sim 0.67)
- ter ~ ger (sim 0.67)

## Variant rivals (merged spelling-variant anchors vs their parts, U3b)

- `ae|ai|aî|e|ei|he|hé|oe|é|éh` (parts é, e, hé, ai; new conflict freq 5.5): **apart**
- `tai|taie|taient|tais|tait|tet|têt` (parts tait, tais, taient, tet; new conflict freq 0.0): **outOfReach**
- `a|ah|ha|hah|hâ|â` (parts a, ha, â, hâ, ah; new conflict freq 7.6); merged score None vs main 0: **apart**
    merged forms: a|ah|ha|hah|hâ|â, a[bi|bri|by|bî|ccli|ci|cqui|cri|cry|ddi|di|ffi|ffli|ffri|fi|fri|gi|gri|gui|li|lli|mi|my|myg|nhy|ni|nni|nnih|ny|pi|ppli|ppri|qui|ri|rri|ssi|ssy|sy|ti|tti|ttri|ty|vi|xi|zi|zy|ï]·, a[ban|fflan|ffran|gran|lam|lan|len|lham|man|men|ppren|ran|ren|rran|scen|ssem|ssen|tten|van|ven]·, a[a|ba|bba|boie|bra|bâ|ca|cca|ccla|cha|da|djoi|dra|droi|ffa|ga|ggra|gla|gra|la|lla|ma|mha|na|nna|pa|pha|pla|ppa|ppâ|qua|ra|ria|rra|sia|ssa|ssoi|ta|tha|tra|tta|ttra|va|via|voi|wa|ya]·, a[bai|be|bê|chè|cquie|dre|ffai|grai|gre|gue|le|llai|lle|llè|lè|mai|me|mè|nne|pai|ppe|pprê|rai|rrai|rrê|se|ssai|sse|ssè|tte|ttei|vè]·, aé[a|an|cia|cie|cé|di|en|fle|ga|go|lec|lio|llu|lu|ma|mo|na|ni|no|nu|nua|o|ou|qua|qui|ra|ri|rin|ro|ros|rri|ssi|ta|ti|ty|tyl]·; main forms: a, a[ban|fflan|ffran|gran|lam|lan|len|lham|man|men|ppren|rran|scen|ssem|ssen|tten|van|ven]·, a[bri|by|bî|ccli|ci|cqui|cri|cry|ddi|di|ffi|ffli|ffri|fi|fri|gi|gri|gui|li|lli|mi|my|myg|nhy|ni|nni|nnih|ny|pi|ppli|ppri|qui|rri|ssi|ssy|sy|tti|ttri|ty|vi|xi|zi|zy]·, a[bai|be|bê|chè|cquie|dre|ffai|grai|gre|gue|le|llai|lle|llè|mai|me|mè|nne|pai|ppe|pprê|rai|rrai|rrê|se|ssai|sse|ssè|tte|ttei|vè]·, a[ba|bba|boie|bra|bâ|ca|cca|ccla|cha|da|djoi|dra|droi|ffa|ga|ggra|gla|gra|la|ma|mha|na|nna|pa|pha|pla|ppa|ppâ|pâ|qua|ra|ria|rra|sia|ssa|ssoi|ta|tha|tra|tta|ttra|va|via|voi|ya]·, aé[a|an|cia|cie|cé|di|en|fle|ga|go|lec|lio|llu|lu|ma|mo|na|ni|no|nu|nua|o|ou|qua|qui|ra|ri|rin|ro|ros|rri|ssi|ta|ti|ty|tyl]·
- `le|leh|ler|lers|ller|llé|llée|lée` (parts ler, ller, llée, lée, llé; new conflict freq 14.6); merged score None vs main 0: **apart**
    merged forms: le|leh|ler|lers|ller|llé|llée|lée, ·[ce|de|ge|me|mme|pe|ppe|que|rre|se|sse|te|ve]ler⟨le|leh|ler|lers|ller|llé|llée|lée⟩, ·[bo|co|do|ffo|fo|geo|gno|go|jo|mo|no|o|pau|po|ro|so|sso|to|trô|vo]lé; main forms: ler, ·[ce|de|ge|me|mme|pe|ppe|que|rre|se|sse|te|ve]ler, ·[bo|co|do|ffo|fo|geo|gno|go|jo|no|o|pau|po|so|sso|to|trô|vo]lé
- `am|an|ant|em|en|ench|enh|ham|han|hen` (parts en, em, an, am, han; new conflict freq 3.0): **fused**
- `ve|ver|wé` (parts ver; new conflict freq 0.1): **apart**
- `au|aul|ho|hos|o|oi` (parts o, ho; new conflict freq -0.0): **outOfReach**
- `bai|be` (parts be; new conflict freq 0.0): **outOfReach**
- `re|reh` (parts re; new conflict freq 0.0): **fused**
- `mai|maî|me|mei|mes|mè|mê` (parts me, mai, mê; new conflict freq 0.0): **outOfReach**
- `bom|bon` (parts bon, bom; new conflict freq 0.2): **outOfReach**
- `ma|mah|mâ` (parts ma, mâ, mah; new conflict freq 0.5); merged score None vs main 0: **apart**
    merged forms: ma|mah|mâ, ma[a|ca|ccha|cha|chi|chia|chin|cho|cin|ckin|cra|cro|cros|cu|cum|cé|da|de|dri|dré|es|fio|ga|gen|ghré|gi|gis|gna|gni|gno|gné|gou|illo|jes|jo|jor|la|lai|lan|len|lha|lheu|lho|li|lin|llar|llé|lo|lé|ma|me|mmec|mmi|mmo|na|nha|ni|nia|nie|nié|nne|nni|no|noeu|nou|nu|nue|nus|nué|né|o|ppe|que|qui|ra|rau|raî|ri|ria|rie|rin|rio|ro|rou|rro|ry|ré|so|ssa|ssi|ta|te|ter|thu|thé|ti|toi|tra|tri|tu|té|xi|yo|za|zur|ço|ï]·, made[ar|bi|bri|ca|can|cha|chou|ché|cli|co|con|cou|cre|cu|da|di|dic|do|droi|fac|fi|gan|gra|jua|la|li|lle|ma|mi|mo|moi|mou|mé|na|ni|nne|o|plas|po|pu|qui|ra|re|reau|reu|ri|ria|ro|sa|si|ten|ti|to|tos|tra|tri|vau|vra|vri|vé|é]-{fEs}·; main forms: ma, ma[ca|ccha|cha|chi|chia|chin|cin|ckin|cra|cro|cros|cu|cum|cé|da|de|dri|dré|es|fio|ga|gen|ghré|gi|gis|gna|gni|gno|gné|gou|illo|jes|jo|jor|la|lai|lan|len|lha|lheu|lho|li|lin|llar|llé|lo|lé|ma|me|mmec|mmi|mmo|na|nha|ni|nia|nie|nié|nne|nni|no|noeu|nou|nu|nue|nus|nué|né|o|ppe|que|qui|ra|rau|raî|ri|ria|rie|rin|rio|ro|rou|rro|ry|ré|so|ssa|ssi|ta|te|ter|thu|thé|ti|toi|tra|tri|tu|té|xi|yo|za|zur|ço|ï]·, made[ar|bi|bri|ca|can|cha|chou|ché|cli|co|con|cre|cu|da|di|dic|do|droi|fac|fi|gan|gra|jua|la|li|lle|ma|mi|mo|moi|mou|na|ni|nne|o|plas|po|pu|qui|re|reau|reu|ri|ria|ro|sa|si|ten|ti|to|tos|tra|tri|vau|vra|vri|vé|é]-{fEs}·
- `van|vant|vent` (parts vant, vent; new conflict freq 0.0): **outOfReach**
- `ar|har` (parts ar, har; new conflict freq 0.1): **outOfReach**
- `llon|lon` (parts lon, llon; new conflict freq 0.6): **outOfReach**
- `ce|sce|se` (parts se, ce; new conflict freq 0.0): **fused**
- `rette|rrette|rète|rête` (parts rette; new conflict freq 0.0): **outOfReach**
- `fan|fang|fant|fends|fens|ffant|phant` (parts ffant; new conflict freq 0.0): **outOfReach**
- `main|men|min` (parts main, min; new conflict freq 0.0): **outOfReach**
- `ra|rai|re|rei|rè|rê` (parts rai, rê, re; new conflict freq 0.0): **outOfReach**
- `son|zon` (parts son, zon; new conflict freq 0.0): **outOfReach**
- `sa|sah` (parts sa; new conflict freq 0.0): **fused**
- `voir|voire` (parts voir; new conflict freq 0.0): **outOfReach**
- `vou|voue|voû|woo` (parts vou; new conflict freq 0.0): **outOfReach**
- `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` (parts sser, cer, ser, sé, cé, cée, ssée; new conflict freq 89.0): **fused**
- `ssé|sée` (parts ssé; new conflict freq 0.0): **outOfReach**
- `mau|mo|moh` (parts mo, mau; new conflict freq 0.1): **outOfReach**
- `man|mand|mant|ment|ments|mmant|mment` (parts ment, mment, mant, mand, man; new conflict freq 1.4): **apart**
- `pro|proh|prô` (parts pro; new conflict freq 0.0): **fused**
- `bien|byen` (parts bien; new conflict freq 0.0): **outOfReach**
- `tture|tur|ture` (parts ture; new conflict freq 0.0): **outOfReach**
- `tir|tire|ttir|tyr|tyre` (parts tir; new conflict freq 4.1): **outOfReach**
- `tra|trah|trâ` (parts tra; new conflict freq 0.0): **outOfReach**
- `vail|vaille|vailles` (parts vail; new conflict freq 0.0): **outOfReach**
- `nhir|nir|nnir` (parts nir, nnir; new conflict freq 0.0): **outOfReach**
- `ai|aî|e|ei|hai|he|hê|é` (parts e, ai, é, he; new conflict freq 0.1): **fused**
- `der|dé|dée` (parts der, dée, dé; new conflict freq 52.2): **fused**
- `mi|mie|mis|mmies|mmis|mmy|my` (parts mi, mie, mis; new conflict freq 0.9): **outOfReach**
- `au|aux|hau|haut|ho|hô|o|oh|ô` (parts au, o, ho, hô, hau; new conflict freq 34.4): **apart**
- `d'hui|duit` (parts duit; new conflict freq 0.0): **outOfReach**
- `fa|fe|fei|fâ|pha` (parts fa, fâ, pha; new conflict freq 0.2): **outOfReach**
- `pou|pu` (parts pou; new conflict freq 0.2): **fused**
- `pa|pei|pâ` (parts pa, pâ; new conflict freq 0.2): **apart**
- `cher|chée|scher|sher` (parts cher, chée; new conflict freq 14.4): **apart**
- `trou|troue` (parts trou; new conflict freq 0.0): **outOfReach**
- `e|hi|hy|i|y|î` (parts i, hi, hy; new conflict freq 0.2): **fused**
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
- `ain|hin|im|in` (parts in, im; new conflict freq 0.0): **fused**
- `cau|cho|coa|coh|cô|ko|quo` (parts cô, cau, quo, cho, coh, ko; new conflict freq 0.4): **outOfReach**
- `nnu|nue|nut` (parts nue, nnu; new conflict freq 0.0): **outOfReach**
- `moo|mou|mu` (parts mou; new conflict freq 0.0): **outOfReach**
- `rir|rire|rrir` (parts rir, rrir; new conflict freq 0.0): **outOfReach**
- `dau|dho|do` (parts do, dau; new conflict freq 0.3): **outOfReach**
- `ner|nez|nner|nnée|née|nées` (parts ner, nner, née, nnée; new conflict freq 52.2): **fused**
- `nné|né` (parts né, nné; new conflict freq 1.2): **outOfReach**
- `ser|sée|zer|zé` (parts ser, sée, zer; new conflict freq 5.8): **fused**
- `ter|teur|tter|tteur|ttheure` (parts teur, tteur, ter; new conflict freq 0.3): **outOfReach**
- `son|sson|çon` (parts çon, sson, son; new conflict freq 0.0): **outOfReach**
- `vi|vie|vis|vit` (parts vis, vi; new conflict freq 0.0): **outOfReach**
- `tau|taud|taut|teau|tho|to|tos|tot|tto|tô|tôt` (parts tôt, teau, to, tto; new conflict freq 4.7): **outOfReach**
- `mam|man|mem|men` (parts man, men, mem; new conflict freq 3.8): **outOfReach**
- `ger|gée` (parts ger, gée; new conflict freq 10.9): **apart**
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
- `de|des|dé|déh` (parts dé, de, déh; new conflict freq 3.5): **fused**
- `er|ée|ë` (parts er; new conflict freq 0.4): **outOfReach**
- `de|dea|di|die|dis|dy|dî` (parts di, dy; new conflict freq 0.0): **fused**
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
- `ccion|cion|cyon|sion|ssion|tion|tions` (parts tion, ssion, sion; new conflict freq 0.1): **fused**
- `ca|cah|cha|câ|ka|kha|khâ|qua` (parts ca, qua, ka, câ, cah; new conflict freq 2.1); merged score None vs main 0: **apart**
    merged forms: ca|cah|cha|câ|ka|kha|khâ|qua, ca[ba|bi|blo|bo|bri|bu|bé|ca|cah|cha|che|cho|chè|co|da|das|de|den|do|dri|far|fe|fou|fé|gi|ille|illou|jo|la|lach|lai|lan|le|lem|len|li|lié|lli|llo|lo|lom|lu|lyp|lé|ma|mar|me|mem|mi|mio|mo|mou|mé|més|na|nar|nas|ne|ni|nna|nne|nni|no|nu|o|ou|pa|pe|po|pri|pu|pé|que|què|ra|rac|ram|ran|re|ri|rio|ris|ro|rou|rre|rrié|rro|rrou|rré|ryo|sa|se|ser|so|ssa|sse|ssi|sso|ssou|sé|ta|tal|tan|tas|ter|thar|tho|thé|to|tor|tri|té|va|val|ver|vi|ya]-{pi,zi}·, capi·; main forms: ca, ca[ba|bi|bo|bri|bé|ca|cah|cha|che|cho|chè|co|da|das|de|den|do|far|fe|fou|fé|gi|ille|illou|jo|la|lai|lan|le|lem|len|li|lli|llo|lo|lom|lu|lyp|lé|ma|mar|me|mem|mi|mio|mo|mou|mé|més|na|nar|nas|ne|ni|nna|nne|nni|no|nu|ou|pa|pe|po|pri|pu|pé|que|què|ra|rac|ram|re|ri|rio|ro|rou|rre|rrié|rro|rrou|rré|ryo|ré|sa|se|ser|si|so|ssa|sse|ssi|sso|ssou|sé|ta|tal|tas|ter|thar|tho|thé|to|té|va|val|ver|vi]-{pi}·, capi·
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
- `ra|rha|râ` (parts ra, râ; new conflict freq 0.4); merged score 1377 vs main 1773: **apart**
    merged forms: ra|rha|râ, ra[be|che|ge|ille|me|pe|ppe|re|te|ve]·⟨ra|rha|râ⟩; main forms: ra, ra[be|che|ge|ille|me|pe|ppe|re|te|ve]·
- `be|bee|bi|bih|by` (parts bi; new conflict freq 0.0): **outOfReach**
- `sar|sard|zar|zard|zarre|zarts|zzard` (parts sard, zar; new conflict freq 0.2): **outOfReach**
- `por|pore|port|ports|pport` (parts port; new conflict freq 0.0): **outOfReach**
- `nial|niale` (parts nial; new conflict freq 0.0): **outOfReach**
- `paud|peau|po|poc|pos|pot|ppeau|ppo|ppôt|pôt` (parts peau, po, pot; new conflict freq 3.0): **outOfReach**
- `comp|kon` (parts comp; new conflict freq 0.0): **outOfReach**
- `thier|tier|tiers|tiez|tié|ttier` (parts tier, tié, tiez, ttier; new conflict freq 0.1): **outOfReach**
- `tea|tee|thi|thy|ti|ty` (parts ti, ty, thy; new conflict freq 2.7): **outOfReach**
- `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` (parts rer, rée, rrer, rai, rrhée, rez; new conflict freq 17.9): **fused**
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
- `ra|rai|raie|re|rhé|ré|réh` (parts ré, re, rhé; new conflict freq 0.3): **fused**
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

- ter ~ té: 0.09

## Overlap skips during selection (0)

- none
