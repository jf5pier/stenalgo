# Affix rules (selection and keypress binding)

Constants: RULE_BUDGET=30, EXCEPTION_ALPHA=2.0, EXCLUSION_COST=5.0, FORM_COST=100.0, SWAP_CANDIDATES=20, SWAP_PASSES=3, RULE_OVERLAP_MAX=0.5, MAX_EXCEPTION_RATE=0.05. Growth forms and fusions come from `affix_decisions.json`.

Pending decisions: **0** (none)


Selected rules with attestedShare < 0.5 (candidate pseudo-affixes like `ma-`): **13** -- `a|ah|ha|hâ|â`, `co+col+com+con+cor`, `é`, `ain|hin|im|in`, `ai|aî|e|ei|hai|he|hê|é`, `au`, `der|dé|dée`, `ra|rai|raie|re|rhé|ré|réh`, `pa`, `ma|mah|mâ`, `e|hi|hy|i|y|î`, `o`, `de|dea|di|die|dis|dy|dî`

## Savings curve (cumulative total after each acceptance, 1..40)

17432, 25935, 32557, 39882, 45984, 51527, 56970, 61539, 66231, 70863, 75536, 80263, 85234, 88807, 92339, 95639, 98895, 101916, 105099, 108164, 110814, 113222, 116389, 118859, 121241, 123696, 125974, 128189, 130385, 132514

## 1. prefix `a|ah|ha|hâ|â` -- keys (9, 16) = `w-j`

forms: `a|ah|ha|hâ|â`(k=1), `a|ah|ha|hâ|â[R@|RE|Re]·`(k=2)
- score 17432.3, strokeFreqSaved 17983.3, keySimilarity -0.90 -- NOT phonetically motivated
- attestedShare 0.26; exception rate 1.5%; top categories: VER 52%, NOM 32%, ADJ 6%
- fused spelling variants: a, ah, ha, hâ, â (new conflict freq 7.6)
- word exceptions 160 (freq 188.0); scope fallbacks 15
- top exceptions: attaque, attaque, allée, âgée, âgé, attaques, arabes, attaquent, arabe, arabe
    arrête: a/Riet -> Rwiejt
    amour: a/m@eR -> mw@ejR
    avais: a/vie/-d -> vwiej/-d
    assez: a/se -> swej
    avais: a/vie/-k -> vwiej/-k
    ami: a/mi -> mwij

## 2. suffix `ment` -- keys (16, 20, 25) = `-jtm`

forms: `ment`(k=1), `·[C{1,2}[eui]+]ment`(k=2)
- score 8503.2, strokeFreqSaved 8763.2, keySimilarity 0.44 -- NOT phonetically motivated
- attestedShare 0.76; exception rate 0.0%; top categories: ADV 60%, NOM 39%, ADJ 0%
- word exceptions 1 (freq 0.0); scope fallbacks 32
- top exceptions: blèsement
    moment: mae/m@ -> maejtm
    seulement: s@/mt@a/m@ -> s@jtm
    tellement: tie/mt@a/m@ -> tiejtm
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/ajktm
    sûrement: s@i/R@a/m@ -> s@ijtm
    complètement: kai/pmtie/t@a/m@ -> kai/pmtiejtm

## 3. prefix `am|an|ant|em|en|ench|enh|ham|han|hen` -- keys (4, 6, 16) = `pm-j`

forms: `am|an|ant|em|en|ench|enh|ham|han|hen`(k=1), `am|an|ant|em|en|ench|enh|ham|han|hen[en:C{1,2}@]·`(k=2)
- score 7324.3, strokeFreqSaved 7617.2, keySimilarity 0.02 -- NOT phonetically motivated
- attestedShare 0.54; exception rate 0.9%; top categories: VER 48%, NOM 33%, ADV 10%
- fused spelling variants: am, an, ant, em, en, ench, enh, ham, han, hen (new conflict freq 3.0)
- word exceptions 64 (freq 18.9); scope fallbacks 31
- top exceptions: emplacement, emplit, amplement, empli, entassés, enchaîne, emplacements, ampli, entasser, envient
    enfants: @/kp@/-s -> kpm@j/-s
    enfant: @/kp@ -> kpm@j
    enfin: @/kpaie -> kpmaiej
    entendu: @/t@/pv@i -> pvm@ij
    ensemble: @/s@jl -> spm@jl
    envie: @/vi -> pvmij

## 4. prefix `co+col+com+con+cor` -- keys (9, 19) = `w-d`

forms: `co+col+com+con+cor`(k=1), `co+col+com+con+cor[m@]·`(k=2)
- score 6621.9, strokeFreqSaved 8180.7, keySimilarity -0.08 -- NOT phonetically motivated
- attestedShare 0.42; exception rate 3.3%; top categories: VER 48%, NOM 37%, ADJ 8%
- word exceptions 203 (freq 674.4); scope fallbacks 22
- top exceptions: connais, connaît, connard, connard, connards, connu, coté, coté, coffrer, connue
    combien: kai/svRwaie -> svRwaied
    comprends: kai/pR@/-k -> pRw@d/-k
    compris: kai/pRi -> pRwid
    confiance: kai/kpRw@s -> kpRw@sd
    commence: kae/m@s -> mw@sd

## 5. prefix `re|reh` -- keys (9, 18) = `w-k`

forms: `re|reh`(k=1)
- score 6102.2, strokeFreqSaved 6199.8, keySimilarity -0.33 -- NOT phonetically motivated
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

## 6. suffix `ccion|cion|cyon|sion|ssion|tion|tions` -- keys (16, 17, 20) = `-jst`

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

## 7. prefix `é` -- keys (2, 5) = `kv-`

forms: `é`(k=1)
- score 5443.4, strokeFreqSaved 5449.0, keySimilarity -1.00 -- NOT phonetically motivated
- attestedShare 0.37; exception rate 0.1%; top categories: VER 46%, NOM 39%, ADJ 11%
- word exceptions 9 (freq 2.8); scope fallbacks 0
- top exceptions: épi, équité, épis, édit, édits, évitée, équidés, évitées, équités
    écoute: e/k@et -> kv@et
    étaient: e/tie/-st -> kvtie/-st
    école: e/kel -> kvel
    état: e/ta -> kvta
    écrit: e/kRi -> kvRi
    équipe: e/kijk -> kvijk

## 8. prefix `de|des|dé|déh` -- keys (3, 9, 18) = `sw-k`

forms: `de|des|dé|déh`(k=1)
- score 4970.9, strokeFreqSaved 5077.7, keySimilarity -0.50 -- NOT phonetically motivated
- attestedShare 0.63; exception rate 1.1%; top categories: VER 58%, NOM 28%, ADJ 13%
- fused spelling variants: de, des, dé, déh (new conflict freq 3.5)
- word exceptions 116 (freq 53.4); scope fallbacks 0
- top exceptions: dégâts, débat, débarque, dévoiler, débats, débarquent, déballer, dévoilé, débarques, débat
    désolé: pve/twae/mte -> stwaek/mte
    désolé: pve/twae/mte -> stwaek/mte
    début: pve/sv@i -> svw@ik
    désolée: pve/twae/mte/-j -> stwaek/mte/-j
    décidé: pve/si/pve -> swik/pve
    désolée: pve/twae/mte/-j -> stwaek/mte/-j

## 9. prefix `ain|hin|im|in` -- keys (7, 8, 9) = `tRw-`

forms: `ain|hin|im|in`(k=1), `ain|hin|im|in[in+té]·`(k=2)
- score 4727.4, strokeFreqSaved 4832.7, keySimilarity -0.62 -- NOT phonetically motivated
- attestedShare 0.49; exception rate 0.1%; top categories: NOM 33%, VER 33%, ADJ 29%
- fused spelling variants: ain, hin, im, in (new conflict freq 0.0)
- word exceptions 3 (freq 2.7); scope fallbacks 0
- top exceptions: indemne, indemnes, intiment
    importe: aie/petR -> ptRwetR
    ainsi: aie/si -> stRwi
    important: aie/peR/t@ -> ptRweR/t@
    impossible: aie/pae/sijl -> ptRwae/sijl
    inquiète: aie/kRwiet -> ktRwiet
    intérieur: aie/te/Rw@R -> tRw@R

## 10. prefix `de` -- keys (2, 6, 19) = `km-d`

forms: `de`(k=1), `de[man|ve]·`(k=2)
- score 4692.3, strokeFreqSaved 4792.3, keySimilarity 0.22 -- NOT phonetically motivated
- attestedShare 0.80; exception rate 0.0%; top categories: VER 65%, ADV 20%, NOM 9%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    demain: pv@a/maie -> kmaied
    demande: pv@a/m@d -> km@d
    devrais: pv@a/vRie/-k -> kvmRied/-k
    demandé: pv@a/m@/pve -> kpvmed
    devrait: pv@a/vRie -> kvmRied
    devant: pv@a/v@ -> kvm@d

## 11. prefix `ai|aî|e|ei|hai|he|hê|é` -- keys (5, 18, 19) = `v-kd`

forms: `ai|aî|e|ei|hai|he|hê|é`(k=1), `ai|aî|e|ei|hai|he|hê|é[e:ksky|kspli|sE|n°]·`(k=2)
- score 4673.2, strokeFreqSaved 4803.2, keySimilarity -0.44 -- NOT phonetically motivated
- attestedShare 0.35; exception rate 0.0%; top categories: VER 73%, NOM 17%, ADJ 9%
- fused spelling variants: ai, aî, e, ei, hai, he, hê, é (new conflict freq 0.1)
- word exceptions 0 (freq 0.0); scope fallbacks 6
    aider: ie/pve/-l -> pvekd/-l
    excusez: ie/ks@i/twe/-k -> vtwekd/-k
    aimerais: ie/m@a/Rie/-k -> vm@akd/Rie/-k
    essaie: ie/sie -> sviekd
    essayer: ie/sie/Rwe/-l -> vRwekd/-l
    essayé: ie/siej/e -> sviejkd/e

## 12. suffix `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` -- keys (16, 17, 19) = `-jsd`

forms: `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé`(k=1), `·[cé:m@]cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé`(k=2)
- score 4632.0, strokeFreqSaved 4732.0, keySimilarity 0.33 -- NOT phonetically motivated
- attestedShare 0.66; exception rate 0.0%; top categories: VER 85%, ADV 9%, ADJ 3%
- fused spelling variants: cer, cé, cée, cés, scer, se, ser, sser, ssez, ssée, sé (new conflict freq 89.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    assez: a/se -> ajsd
    passer: pa/se/-l -> pajsd/-l
    passé: pa/se -> pajsd
    laissez: mtie/se/-k -> mtiejsd/-k
    laisser: mtie/se/-l -> mtiejsd/-l
    pensé: p@/se -> p@jsd

## 13. suffix `ter` -- keys (16, 20, 22) = `-jtn`

forms: `ter`(k=1)
- score 4568.5, strokeFreqSaved 4568.5, keySimilarity 0.33 -- NOT phonetically motivated
- attestedShare 0.92; exception rate 0.0%; top categories: VER 100%, NOM 0%, ADJ 0%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    rester: Ries/te/-l -> Riejstn/-l
    arrêter: a/Rie/te/-l -> a/Riejtn/-l
    arrêtez: a/Rie/te/-k -> a/Riejtn/-k
    acheter: a/pm@a/te/-l -> a/pm@ajtn/-l
    restez: Ries/te/-k -> Riejstn/-k
    écoutez: e/k@e/te/-k -> e/k@ejtn/-k

## 14. prefix `au` -- keys (7, 8, 19) = `tR-d`

forms: `au`(k=1), `au[jour|to|tre|di]·`(k=2)
- score 3572.7, strokeFreqSaved 3673.4, keySimilarity 0.24 -- NOT phonetically motivated
- attestedShare 0.39; exception rate 0.2%; top categories: AUX 28%, ADV 23%, VER 22%
- word exceptions 1 (freq 0.3); scope fallbacks 0
- top exceptions: autisme
    aujourd'hui: ae/vt@eR/pv@ai -> pvtR@aid
    aurais: ae/Rie/-d -> tRied/-d
    aurait: ae/Rie -> tRied
    aucune: ae/k@in -> ktR@idn
    aura: ae/Ra -> tRad
    aucun: ae/k@aie -> ktR@aied

## 15. suffix `té` -- keys (19, 20, 25) = `-dtm`

forms: `té`(k=1), `·[C\{bv}{1,2}i]té`(k=2)
- score 3546.3, strokeFreqSaved 4047.2, keySimilarity 0.46 -- NOT phonetically motivated
- attestedShare 0.69; exception rate 0.4%; top categories: NOM 83%, VER 9%, ADJ 8%
- word exceptions 11 (freq 10.5); scope fallbacks 76
- top exceptions: gravité, limité, agilité, limités, lité, caté, agilités, lités, litée, litées
    côté: kae/te -> kaedtm
    vérité: ve/Ri/te -> vedtm
    sécurité: se/k@i/Ri/te -> se/k@idtm
    santé: s@/te -> s@dtm
    liberté: mti/svieR/te -> mti/sviedtRm
    société: sae/sRwe/te -> sae/sRwedtm

## 16. suffix `der|dé|dée` -- keys (18, 19, 25) = `-kdm`

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

## 17. suffix `ner|nez|nner|nnée|née|nées` -- keys (16, 17, 25) = `-jsm`

forms: `ner|nez|nner|nnée|née|nées`(k=1), `·[né:C{1,2}[i°]]ner|nez|nner|nnée|née|nées`(k=2)
- score 3256.2, strokeFreqSaved 3371.3, keySimilarity 0.04 -- NOT phonetically motivated
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

## 18. prefix `ra|rai|raie|re|rhé|ré|réh` -- keys (3, 4, 16) = `sp-j`

forms: `ra|rai|raie|re|rhé|ré|réh`(k=1), `ra|rai|raie|re|rhé|ré|réh[ré:a|fle|vE|C{1,2}y]·`(k=2)
- score 3183.4, strokeFreqSaved 3367.3, keySimilarity -0.27 -- NOT phonetically motivated
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

## 19. prefix `pa` -- keys (2, 5, 18) = `kv-k`

forms: `pa`(k=1)
- score 3167.3, strokeFreqSaved 3171.3, keySimilarity -0.33 -- NOT phonetically motivated
- attestedShare 0.27; exception rate 0.8%; top categories: NOM 49%, VER 38%, ADJ 12%
- word exceptions 13 (freq 2.0); scope fallbacks 0
- top exceptions: pager, pagaie, pagaie, patine, pagaies, papisme, pagaient, pagaies, pagé, paginer
    passer: pa/se/-l -> ksve/-l
    passé: pa/se -> ksve
    papa: pa/pa -> kpva
    parents: pa/R@/-s -> kvR@/-s
    patron: pa/tRai -> kvtRai
    passé: pa/se -> ksve

## 20. prefix `ma|mah|mâ` -- keys (17, 18, 19) = `-skd`

forms: `ma|mah|mâ`(k=1), `ma|mah|mâ[ni]·`(k=2), `ma|mah|mâ[Ni]·`(k=2), `ma|mah|mâ[l2|la]·`(k=2)
- score 3065.5, strokeFreqSaved 3403.9, keySimilarity -0.46 -- NOT phonetically motivated
- attestedShare 0.44; exception rate 1.2%; top categories: NOM 70%, ADJ 18%, VER 11%
- fused spelling variants: ma, mah, mâ (new conflict freq 0.5)
- word exceptions 23 (freq 11.7); scope fallbacks 3
- top exceptions: marais, marions, maraud, machisme, manage, manioc, maraude, matisse, mati, manient
    matin: ma/taie -> taieskd
    mari: ma/Ri -> Riskd
    madame: ma/pvam -> pvaskdm
    mariage: ma/RwaZ -> RwaskdZ
    malade: ma/mtad -> mtaskd
    magnifique: ma/wi/kpik -> kpiskd

## 21. prefix `e|hi|hy|i|y|î` -- keys (16, 19) = `-jd`

forms: `e|hi|hy|i|y|î`(k=1), `e|hi|hy|i|y|î[i:[mn][aeiouy]]·`(k=2)
- score 3020.6, strokeFreqSaved 3200.0, keySimilarity -0.57 -- NOT phonetically motivated
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

## 22. prefix `sa|sah` -- keys (5, 24) = `v-Z`

forms: `sa|sah`(k=1)
- score 2649.0, strokeFreqSaved 2649.5, keySimilarity -0.33 -- NOT phonetically motivated
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

## 23. prefix `o` -- keys (16, 17, 19) = `-jsd`

forms: `o`(k=1), `o[C{1,2}i|kV]·`(k=2)
- score 2469.1, strokeFreqSaved 2584.1, keySimilarity 0.05 -- NOT phonetically motivated
- attestedShare 0.24; exception rate 0.0%; top categories: VER 39%, NOM 34%, ADJ 20%
- word exceptions 0 (freq 0.0); scope fallbacks 3
    ok: ae/k- -> k-jsd
    occupe: ae/k@ijk -> k@ijskd
    ok: ae/k- -> k-jsd
    occuper: ae/k@i/pe/-l -> pejsd/-l
    occasion: ae/ka/tRwai -> tRwaijsd
    offrir: ae/kpRiR -> kpRijsdR

## 24. prefix `pro|proh|prô` -- keys (4, 5, 8) = `pvR-`

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

## 25. suffix `ver` -- keys (16, 17, 18) = `-jsk`

forms: `ver`(k=1), `·[vé:Ri]ver`(k=2)
- score 2408.5, strokeFreqSaved 2508.5, keySimilarity 0.46 -- NOT phonetically motivated
- attestedShare 0.82; exception rate 0.0%; top categories: VER 100%, NOM 0%, ADJ 0%
- word exceptions 0 (freq 0.0); scope fallbacks 0
    trouvé: tR@e/ve -> tR@ejsk
    trouver: tR@e/ve/-l -> tR@ejsk/-l
    arrivé: a/Ri/ve -> ajsk
    arriver: a/Ri/ve/-l -> a/Rijsk/-l
    sauver: sae/ve/-l -> saejsk/-l
    retrouver: R@a/tR@e/ve/-l -> R@a/tR@ejsk/-l

## 26. prefix `ce|sce|se` -- keys (3, 6) = `sm-`

forms: `ce|sce|se`(k=1)
- score 2382.7, strokeFreqSaved 2382.7, keySimilarity 0.50 -- NOT phonetically motivated
- attestedShare 0.64; exception rate 0.0%; top categories: VER 35%, NOM 28%, PRO:dem 16%
- fused spelling variants: ce, sce, se (new conflict freq 0.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    serait: s@a/Rie -> smRie
    celui: s@a/mt@ai -> smt@ai
    semaine: s@a/mien -> smien
    serai: s@a/Re/-t -> smRe/-t
    ceci: s@a/si -> smi
    semaines: s@a/mien/-s -> smien/-s

## 27. suffix `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` -- keys (16, 19, 21) = `-jdR`

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

## 28. prefix `pou|pu` -- keys (4, 7, 18) = `pt-k`

forms: `pou|pu`(k=1)
- score 2215.0, strokeFreqSaved 2215.0, keySimilarity 0.33 -- NOT phonetically motivated
- attestedShare 0.89; exception rate 0.0%; top categories: VER 86%, NOM 13%, ADJ 1%
- fused spelling variants: pou, pu (new conflict freq 0.2)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    pouvez: p@e/ve -> pvtek
    pourrait: p@e/Rie -> ptRiek
    pourrais: p@e/Rie/-k -> ptRiek/-k
    pouvoir: p@e/vwaR -> pvtwakR
    pouvais: p@e/vie/-k -> pvtiek/-k
    pouvait: p@e/vie -> pvtiek

## 29. prefix `de|dea|di|die|dis|dy|dî` -- keys (3, 16, 19) = `s-jd`

forms: `de|dea|di|die|dis|dy|dî`(k=1), `de|dea|di|die|dis|dy|dî[di:C{1,2}i]·`(k=2)
- score 2195.6, strokeFreqSaved 2295.6, keySimilarity 0.16 -- NOT phonetically motivated
- attestedShare 0.33; exception rate 0.0%; top categories: VER 49%, NOM 29%, ADJ 20%
- fused spelling variants: de, dea, di, die, dis, dy, dî (new conflict freq 0.0)
- word exceptions 0 (freq 0.0); scope fallbacks 0
    dirait: pvi/Rie -> sRiejd
    difficile: pvi/kpi/sil -> sijdl
    disais: pvi/twie/-k -> stwiejd/-k
    disait: pvi/twie -> stwiejd
    dîner: pvi/mRe -> smRejd
    dirai: pvi/Re/-t -> sRejd/-t

## 30. suffix `ser|sée|zer|zé` -- keys (18, 22, 23) = `-knl`

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

## Variant merges (verdicts of `affix_decisions.json`)

- `ae|ai|aî|e|ei|he|hé|oe|é|éh` /e/ (parts é, e, hé, ai; new conflict freq 5.5): **apart**
- `a|ah|ha|hah|hâ|â` /a/ (parts a, ha, â, hâ, ah; new conflict freq 7.6): **apart**
- `le|leh|ler|lers|ller|llé|llée|lée` /le/ (parts ler, ller, llée, lée, llé; new conflict freq 14.6): **apart** (undecided)
- `am|an|ant|em|en|ench|enh|ham|han|hen` /@/ (parts en, em, an, am, han; new conflict freq 3.0): **fused**
- `ve|ver|wé` /ve/ (parts ver; new conflict freq 0.1): **apart**
- `au|aul|ho|hos|o|oi` /O/ (parts o, ho; new conflict freq -0.0): **apart** (undecided)
- `bai|be` /b°/ (parts be; new conflict freq 0.0): **apart** (undecided)
- `re|reh` /R°/ (parts re; new conflict freq 0.0): **fused**
- `mai|maî|me|mei|mes|mè|mê` /mE/ (parts me, mai, mê; new conflict freq 0.0): **apart** (undecided)
- `bom|bon` /b§/ (parts bon, bom; new conflict freq 0.2): **apart** (undecided)
- `ma|mah|mâ` /ma/ (parts ma, mâ, mah; new conflict freq 0.5): **fused**
- `van|vant|vent` /v@/ (parts vant, vent; new conflict freq 0.0): **apart** (undecided)
- `ar|har` /aR/ (parts ar, har; new conflict freq 0.1): **apart** (undecided)
- `llon|lon` /l§/ (parts lon, llon; new conflict freq 0.6): **apart** (undecided)
- `ce|sce|se` /s°/ (parts se, ce; new conflict freq 0.0): **fused**
- `rette|rrette|rète|rête` /REt/ (parts rette; new conflict freq 0.0): **apart** (undecided)
- `fan|fang|fant|fends|fens|ffant|phant` /f@/ (parts ffant; new conflict freq 0.0): **apart** (undecided)
- `main|men|min` /m5/ (parts main, min; new conflict freq 0.0): **apart** (undecided)
- `ra|rai|re|rei|rè|rê` /RE/ (parts rai, rê, re; new conflict freq 0.0): **apart** (undecided)
- `son|zon` /z§/ (parts son, zon; new conflict freq 0.0): **apart** (undecided)
- `sa|sah` /sa/ (parts sa; new conflict freq 0.0): **fused**
- `voir|voire` /vwaR/ (parts voir; new conflict freq 0.0): **apart** (undecided)
- `vou|voue|voû|woo` /vu/ (parts vou; new conflict freq 0.0): **apart** (undecided)
- `cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé` /se/ (parts sser, cer, ser, sé, cé, cée, ssée; new conflict freq 89.0): **fused**
- `ssé|sée` /se/ (parts ssé; new conflict freq 0.0): **apart** (undecided)
- `mau|mo|moh` /mo/ (parts mo, mau; new conflict freq 0.1): **apart** (undecided)
- `man|mand|mant|ment|ments|mmant|mment` /m@/ (parts ment, mment, mant, mand, man; new conflict freq 1.4): **apart**
- `pro|proh|prô` /pRo/ (parts pro; new conflict freq 0.0): **fused**
- `bien|byen` /bj5/ (parts bien; new conflict freq 0.0): **apart** (undecided)
- `tture|tur|ture` /tyR/ (parts ture; new conflict freq 0.0): **apart** (undecided)
- `tir|tire|ttir|tyr|tyre` /tiR/ (parts tir; new conflict freq 4.1): **apart** (undecided)
- `tra|trah|trâ` /tRa/ (parts tra; new conflict freq 0.0): **apart** (undecided)
- `vail|vaille|vailles` /vaj/ (parts vail; new conflict freq 0.0): **apart** (undecided)
- `nhir|nir|nnir` /niR/ (parts nir, nnir; new conflict freq 0.0): **apart** (undecided)
- `ai|aî|e|ei|hai|he|hê|é` /E/ (parts e, ai, é, he; new conflict freq 0.1): **fused**
- `der|dé|dée` /de/ (parts der, dée, dé; new conflict freq 52.2): **fused**
- `mi|mie|mis|mmies|mmis|mmy|my` /mi/ (parts mi, mie, mis; new conflict freq 0.9): **apart** (undecided)
- `au|aux|hau|haut|ho|hô|o|oh|ô` /o/ (parts au, o, ho, hô, hau; new conflict freq 34.4): **apart**
- `d'hui|duit` /d8i/ (parts duit; new conflict freq 0.0): **apart** (undecided)
- `fa|fe|fei|fâ|pha` /fa/ (parts fa, fâ, pha; new conflict freq 0.2): **apart** (undecided)
- `pou|pu` /pu/ (parts pou; new conflict freq 0.2): **fused**
- `pa|pei|pâ` /pa/ (parts pa, pâ; new conflict freq 0.2): **apart**
- `cher|chée|scher|sher` /Se/ (parts cher, chée; new conflict freq 14.4): **apart**
- `trou|troue` /tRu/ (parts trou; new conflict freq 0.0): **apart** (undecided)
- `e|hi|hy|i|y|î` /i/ (parts i, hi, hy; new conflict freq 0.2): **fused**
- `pam|pan|pem|pen` /p@/ (parts pen, pan, pam; new conflict freq 1.3): **apart** (undecided)
- `dan|dans|dant|dent` /d@/ (parts dant, dent; new conflict freq 0.2): **apart** (undecided)
- `his|hys|is|isth` /is/ (parts his, is; new conflict freq 0.0): **apart** (undecided)
- `toir|toire|ttoir` /twaR/ (parts toire, toir, ttoir; new conflict freq 0.0): **apart** (undecided)
- `tion|tions` /tj§/ (parts tion, tions; new conflict freq 0.0): **apart** (undecided)
- `fee|fi|fie|phi|phy` /fi/ (parts fi, phy, phi; new conflict freq 0.0): **apart** (undecided)
- `ni|nie|nies|nil|nis|nit|nni|nnie|nnies|nny` /ni/ (parts nie, ni; new conflict freq 0.9): **apart** (undecided)
- `lom|lon|long|lum` /l§/ (parts lon, lom; new conflict freq 0.0): **apart** (undecided)
- `tan|tang|tant|temps|tent|than|ttan|ttant|ttent` /t@/ (parts tant, tan, tent, ttant; new conflict freq 0.0): **apart** (undecided)
- `pu|pue` /py/ (parts pu; new conflict freq 0.0): **apart** (undecided)
- `tain|teint|thain|tin|tinct|tins|tteint|ttin` /t5/ (parts tin, tain; new conflict freq 1.3): **apart** (undecided)
- `ci|cie|cil|cis|cit|cy|si|sie|sil|sis|ssi|ssie|ssis|sy|tie` /si/ (parts ci, tie, cis, ssis, sie, cie; new conflict freq 0.4): **apart** (undecided)
- `llu|lu|lue|lus|lut` /ly/ (parts lu; new conflict freq 0.0): **apart** (undecided)
- `pau|peau|po` /po/ (parts po, pau, peau; new conflict freq 0.1): **apart** (undecided)
- `lice|lis|lisse|llis|lysse` /lis/ (parts lice, lis; new conflict freq 0.0): **apart** (undecided)
- `fain|ffin|fin|fins|phin` /f5/ (parts fin, ffin; new conflict freq 0.0): **apart** (undecided)
- `la|lai|le|les|lè` /lE/ (parts lai, le; new conflict freq 0.2): **apart** (undecided)
- `pa|pas|pat|ppa|ppât` /pa/ (parts pa, pas, ppa; new conflict freq 1.2): **apart** (undecided)
- `du|due|dus` /dy/ (parts du; new conflict freq 1.9): **apart** (undecided)
- `ree|ri|rie|ries|rii|ris|rit|rri|rrie|rril|rris|rry|ry|rye` /Ri/ (parts ri, rie, ry, rri; new conflict freq 1.3): **apart** (undecided)
- `ain|hin|im|in` /5/ (parts in, im; new conflict freq 0.0): **fused**
- `cau|cho|coa|coh|cô|ko|quo` /ko/ (parts cô, cau, quo, cho, coh, ko; new conflict freq 0.4): **apart** (undecided)
- `nnu|nue|nut` /ny/ (parts nue, nnu; new conflict freq 0.0): **apart** (undecided)
- `moo|mou|mu` /mu/ (parts mou; new conflict freq 0.0): **apart** (undecided)
- `rir|rire|rrir` /RiR/ (parts rir, rrir; new conflict freq 0.0): **apart** (undecided)
- `dau|dho|do` /do/ (parts do, dau; new conflict freq 0.3): **apart** (undecided)
- `ner|nez|nner|nnée|née|nées` /ne/ (parts ner, nner, née, nnée; new conflict freq 52.2): **fused**
- `nné|né` /ne/ (parts né, nné; new conflict freq 1.2): **apart** (undecided)
- `ser|sée|zer|zé` /ze/ (parts ser, sée, zer; new conflict freq 5.8): **fused**
- `ter|teur|tter|tteur|ttheure` /t9R/ (parts teur, tteur, ter; new conflict freq 0.3): **apart** (undecided)
- `son|sson|çon` /s§/ (parts çon, sson, son; new conflict freq 0.0): **apart** (undecided)
- `vi|vie|vis|vit` /vi/ (parts vis, vi; new conflict freq 0.0): **apart** (undecided)
- `tau|taud|taut|teau|tho|to|tos|tot|tto|tô|tôt` /to/ (parts tôt, teau, to, tto; new conflict freq 4.7): **apart** (undecided)
- `mam|man|mem|men` /m@/ (parts man, men, mem; new conflict freq 3.8): **apart** (undecided)
- `ger|gée` /Ze/ (parts ger, gée; new conflict freq 10.9): **apart**
- `faire|fer|fert|ffaire|fère|phère` /fER/ (parts fer, faire, phère, fère; new conflict freq 0.0): **apart** (undecided)
- `cune|qu'une` /kyn/ (parts cune; new conflict freq 0.0): **apart** (undecided)
- `pa|pai|paie|pe|pei|poe|pé` /pe/ (parts pé, pe; new conflict freq 0.0): **apart** (undecided)
- `i|id|ye|ys|ï|ïs` /i/ (parts i; new conflict freq 0.1): **apart** (undecided)
- `boo|bou|bow|bu` /bu/ (parts bou; new conflict freq 0.0): **apart** (undecided)
- `laud|leau|llo|llos|llot|llô|lo|lop|los|lot|low` /lo/ (parts lot, lo, llo; new conflict freq 5.5): **apart** (undecided)
- `sou|soû|su` /su/ (parts sou, soû; new conflict freq 0.2): **apart** (undecided)
- `ppris|pris|prit|prix` /pRi/ (parts pris; new conflict freq 0.0): **apart** (undecided)
- `mee|mi|my` /mi/ (parts mi, my; new conflict freq 0.0): **apart** (undecided)
- `col|cole|colle|cool` /kOl/ (parts cole; new conflict freq 0.0): **apart** (undecided)
- `cible|scible|sible|ssible` /sibl/ (parts ssible, sible, scible; new conflict freq 0.0): **apart** (undecided)
- `de|des|dé|déh` /de/ (parts dé, de, déh; new conflict freq 3.5): **fused**
- `er|ée|ë` /e/ (parts er; new conflict freq 0.4): **apart** (undecided)
- `de|dea|di|die|dis|dy|dî` /di/ (parts di, dy; new conflict freq 0.0): **fused**
- `ve|vei|vé|véh|vê` /ve/ (parts vé, ve, vei; new conflict freq 0.0): **apart** (undecided)
- `su|sue|sû` /sy/ (parts su; new conflict freq 0.0): **apart** (undecided)
- `ra|rah|ras|rat|rra|rrah|rras|rrat` /Ra/ (parts ra, rat, ras; new conflict freq 1.0): **apart** (undecided)
- `maine|men|mène|mènes` /mEn/ (parts men, mène; new conflict freq 1.0): **apart** (undecided)
- `bie|bien` /bj5/ (parts bien; new conflict freq 0.0): **apart** (undecided)
- `ta|tai|tay|te|tei|the|thê|tê` /tE/ (parts te; new conflict freq 1.6): **apart** (undecided)
- `eins|ins` /5s/ (parts ins; new conflict freq 0.0): **apart** (undecided)
- `de|deh|deu` /d2/ (parts deu; new conflict freq 0.0): **apart** (undecided)
- `tom|ton` /t§/ (parts tom, ton; new conflict freq 0.0): **apart** (undecided)
- `tee|thie|tie|ties|til|tis|tit|tti|ttis|ty` /ti/ (parts tie, thie, ty, tis, ttis; new conflict freq 1.9): **apart** (undecided)
- `tendre|ttendre` /t@dR/ (parts tendre; new conflict freq 0.0): **apart** (undecided)
- `plai|ple|plé` /ple/ (parts plé; new conflict freq 0.0): **apart** (undecided)
- `sir|zir` /ziR/ (parts sir; new conflict freq 0.0): **apart** (undecided)
- `d'a|da|dah|dam` /da/ (parts da; new conflict freq 0.0): **apart** (undecided)
- `bor|bord|bore` /bOR/ (parts bord; new conflict freq 0.0): **apart** (undecided)
- `ba|bai|be|bee|beh|bé|béh|bê` /be/ (parts bé, bê, be; new conflict freq 0.0): **apart** (undecided)
- `fai|fe` /f°/ (parts fe, fai; new conflict freq 0.0): **apart** (undecided)
- `nou|noue` /nu/ (parts nou; new conflict freq 0.0): **apart** (undecided)
- `veau|vo|vot|vôt` /vo/ (parts veau, vo; new conflict freq 0.0): **apart** (undecided)
- `mu|mue|mû` /my/ (parts mu, mû; new conflict freq 0.0): **apart** (undecided)
- `sic|sique|zique` /zik/ (parts sique; new conflict freq 0.0): **apart** (undecided)
- `ram|ran|rem|ren` /R@/ (parts ren, rem, ran, ram; new conflict freq 3.1): **apart** (undecided)
- `trer|tré|ttré` /tRe/ (parts trer, tré; new conflict freq 15.1): **apart** (undecided)
- `ci|cy|sci|scie|sea|si|sy` /si/ (parts si, ci, cy, sy; new conflict freq 0.7): **apart** (undecided)
- `nnon|nom|non` /n§/ (parts non, nom; new conflict freq 0.0): **apart** (undecided)
- `vien|vient` /vj5/ (parts vien; new conflict freq 0.0): **apart** (undecided)
- `jo|raud|raut|raux|reau|ro|rop|ros|rot|rrau|rreau|rro|rrot` /Ro/ (parts ro, reau, rreau, rot, raud; new conflict freq 5.5): **apart** (undecided)
- `seoir|soir|soire|sseoir|ssoir|ssoire|çoir|çoire` /swaR/ (parts soir, ssoire, ssoir; new conflict freq 0.0): **apart** (undecided)
- `mir|mire` /miR/ (parts mir; new conflict freq 0.0): **apart** (undecided)
- `ccion|cion|cyon|sion|ssion|tion|tions` /sj§/ (parts tion, ssion, sion; new conflict freq 0.1): **fused**
- `ca|cah|cha|câ|ka|kha|khâ|qua` /ka/ (parts ca, qua, ka, câ, cah; new conflict freq 2.1): **apart** (undecided)
- `bu|bû` /by/ (parts bu, bû; new conflict freq 0.0): **apart** (undecided)
- `cer|ser` /sER/ (parts ser, cer; new conflict freq 0.0): **apart** (undecided)
- `eu|heu|oe` /2/ (parts eu, oe; new conflict freq 0.0): **apart** (undecided)
- `reux|rreux|rrheux` /R2/ (parts reux; new conflict freq 0.0): **apart** (undecided)
- `tae|te|the|thé|té|tê` /te/ (parts té, thé, te; new conflict freq 0.0): **apart** (undecided)
- `mai|maî|me|mé|méh` /me/ (parts mé, me; new conflict freq 0.9): **apart** (undecided)
- `pair|paire|peire|per|ppert|père` /pER/ (parts père; new conflict freq 4.0): **apart** (undecided)
- `hoo|hou|houh|ou` /u/ (parts ou, hou; new conflict freq 0.1): **apart** (undecided)
- `cil|cile|cille|sile|ssile` /sil/ (parts cile; new conflict freq 0.0): **apart** (undecided)
- `taine|taines|ten|tenne|thène|tène` /tEn/ (parts taine; new conflict freq 3.8): **apart** (undecided)
- `pa|pai|paie|paî|pe|pei|pè|pé|pê` /pE/ (parts pe, pei; new conflict freq 1.3): **apart** (undecided)
- `illé|yé` /je/ (parts illé; new conflict freq 0.0): **apart** (undecided)
- `tou|tout|tu` /tu/ (parts tout, tou; new conflict freq 0.0): **apart** (undecided)
- `ce|cei|cè|cé|sai|say|sce|se|sei|sep|sè|sé` /sE/ (parts sai, ce, se; new conflict freq 2.6): **apart** (undecided)
- `gneur|gneurs` /N9R/ (parts gneur; new conflict freq 0.0): **apart** (undecided)
- `lade|llade` /lad/ (parts lade; new conflict freq 4.5): **apart** (undecided)
- `mier|mié|mmier` /mje/ (parts mier; new conflict freq 0.0): **apart** (undecided)
- `ex|exh|hex` /Egz/ (parts ex, exh; new conflict freq 0.0): **apart** (undecided)
- `pri|prie|pry` /pRi/ (parts pri; new conflict freq 0.0): **apart** (undecided)
- `cham|chan|sham|shan` /S@/ (parts chan, cham; new conflict freq 0.0): **apart** (undecided)
- `nier|nié|nnier` /nje/ (parts nier, nnier; new conflict freq 0.2): **apart** (undecided)
- `vais|vet|vêt` /vE/ (parts vet; new conflict freq 0.0): **apart** (undecided)
- `ta|tas|tat|tha|tta|tà` /ta/ (parts tat, ta, tta; new conflict freq 0.2): **apart** (undecided)
- `mom|mon|mont` /m§/ (parts mon, mont; new conflict freq 0.0): **apart** (undecided)
- `pprendre|prendre` /pR@dR/ (parts prendre; new conflict freq 0.0): **apart** (undecided)
- `gen|jam|jan` /Z@/ (parts gen, jam; new conflict freq 0.0): **apart** (undecided)
- `prae|prai|pre|pré|préh|prê` /pRe/ (parts pré; new conflict freq 0.0): **apart** (undecided)
- `illeur|illeurs|lleur|yeur` /j9R/ (parts lleur, illeur; new conflict freq 0.0): **apart** (undecided)
- `cri|crie|crit` /kRi/ (parts crit; new conflict freq 0.0): **apart** (undecided)
- `ner|neur|nheur|nneur` /n9R/ (parts nneur, neur, ner; new conflict freq 0.0): **apart** (undecided)
- `tal|thal|ttal` /tal/ (parts tal; new conflict freq 0.1): **apart** (undecided)
- `tar|tard|tare|tarrhe|thare|ttard` /taR/ (parts tard, tar; new conflict freq 0.2): **apart** (undecided)
- `vi|wi` /vi/ (parts vi; new conflict freq 0.0): **apart** (undecided)
- `sage|zage` /zaZ/ (parts sage; new conflict freq 0.0): **apart** (undecided)
- `fau|fo|pho` /fo/ (parts pho, fau, fo; new conflict freq 1.9): **apart** (undecided)
- `sau|saul|so|sot` /so/ (parts so, sau; new conflict freq 0.7): **apart** (undecided)
- `lar|lard|lare|llar|llard` /laR/ (parts lard, lar; new conflict freq 0.1): **apart** (undecided)
- `gé|géh|je|jé` /Ze/ (parts gé, jé; new conflict freq 0.1): **apart** (undecided)
- `ral|rral|rrhal` /Ral/ (parts ral; new conflict freq 0.3): **apart** (undecided)
- `ra|rha|râ` /Ra/ (parts ra, râ; new conflict freq 0.4): **apart** (undecided)
- `be|bee|bi|bih|by` /bi/ (parts bi; new conflict freq 0.0): **apart** (undecided)
- `sar|sard|zar|zard|zarre|zarts|zzard` /zaR/ (parts sard, zar; new conflict freq 0.2): **apart** (undecided)
- `por|pore|port|ports|pport` /pOR/ (parts port; new conflict freq 0.0): **apart** (undecided)
- `nial|niale` /njal/ (parts nial; new conflict freq 0.0): **apart** (undecided)
- `paud|peau|po|poc|pos|pot|ppeau|ppo|ppôt|pôt` /po/ (parts peau, po, pot; new conflict freq 3.0): **apart** (undecided)
- `comp|kon` /k§/ (parts comp; new conflict freq 0.0): **apart** (undecided)
- `thier|tier|tiers|tiez|tié|ttier` /tje/ (parts tier, tié, tiez, ttier; new conflict freq 0.1): **apart** (undecided)
- `tea|tee|thi|thy|ti|ty` /ti/ (parts ti, ty, thy; new conflict freq 2.7): **apart** (undecided)
- `rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée` /Re/ (parts rer, rée, rrer, rai, rrhée, rez; new conflict freq 17.9): **fused**
- `rré|ré` /Re/ (parts ré, rré; new conflict freq 0.0): **apart** (undecided)
- `cae|ce|coe|cé|sai|scé|se|sé` /se/ (parts sé, cé, se, ce, sai, scé; new conflict freq 0.2): **apart** (undecided)
- `cin|cinct|sain|seing|sin|ssaim|ssain|ssaint|ssin` /s5/ (parts cin, ssin; new conflict freq 0.0): **apart** (undecided)
- `ssu|ssue|ssus|su|sue|çu` /sy/ (parts çu, ssu; new conflict freq 5.2): **apart** (undecided)
- `bu|bue|bus|but` /by/ (parts bu; new conflict freq 0.9): **apart** (undecided)
- `coo|cou|coû|cu|kou|ku` /ku/ (parts cou; new conflict freq 0.2): **apart** (undecided)
- `ran|rand|rant|rend|reng|rent|rents|rrant|rrent` /R@/ (parts rant, rent, ran; new conflict freq 6.9): **apart** (undecided)
- `get|jet` /ZE/ (parts jet; new conflict freq 0.0): **apart** (undecided)
- `tail|tel|telle|ttelle|tèle` /tEl/ (parts tel, telle, tèle; new conflict freq 0.0): **apart** (undecided)
- `ba|bah|bap|bâ` /ba/ (parts ba, bâ, bap; new conflict freq 3.7): **apart** (undecided)
- `lance|lence|llence` /l@s/ (parts lence, lance; new conflict freq 0.0): **apart** (undecided)
- `dai|de|dé` /dE/ (parts de, dé; new conflict freq 0.0): **apart** (undecided)
- `rière|rrière` /RjER/ (parts rrière; new conflict freq 0.0): **apart** (undecided)
- `dou|du` /du/ (parts dou; new conflict freq 0.0): **apart** (undecided)
- `tram|tran|trem|tren` /tR@/ (parts tran, trem; new conflict freq 0.0): **apart** (undecided)
- `nel|nelle|nnel|nnelle` /nEl/ (parts nel, nnel, nelle; new conflict freq 0.0): **apart** (undecided)
- `geô|jau|jo` /Zo/ (parts jo, jau; new conflict freq 0.0): **apart** (undecided)
- `li|lie|lies|lis|lit|lli|llie|llye|ly` /li/ (parts li, lie, lis; new conflict freq 0.5): **apart** (undecided)
- `reur|rreur` /R9R/ (parts rreur, reur; new conflict freq 0.0): **apart** (undecided)
- `ac|acc|ak` /ak/ (parts ac; new conflict freq 0.0): **apart** (undecided)
- `sage|ssage|çage` /saZ/ (parts ssage, çage; new conflict freq 0.0): **apart** (undecided)
- `te|té` /t°/ (parts te; new conflict freq 0.0): **apart** (undecided)
- `fait|faix|fet|ffet` /fE/ (parts fait; new conflict freq 0.0): **apart** (undecided)
- `che|ché|sché|shé` /Se/ (parts ché; new conflict freq 0.3): **apart** (undecided)
- `dau|daud|deau|deaux|do|dot|dow` /do/ (parts deau, do; new conflict freq 0.2): **apart** (undecided)
- `dale|del|delle|dèle` /dEl/ (parts dèle, delle; new conflict freq 1.0): **apart** (undecided)
- `per|pper|ppé|ppée|pée` /pe/ (parts per, pper, pée, ppé; new conflict freq 10.1): **apart** (undecided)
- `reil|reille` /REj/ (parts reille; new conflict freq 0.0): **apart** (undecided)
- `soi|soie|swah` /swa/ (parts soi; new conflict freq 0.0): **apart** (undecided)
- `mer|mmer|mmé|mmée|mées` /me/ (parts mer, mmer, mmé; new conflict freq 10.9): **apart** (undecided)
- `cha|chah|char|châ|scha|sha` /Sa/ (parts cha, châ; new conflict freq 1.4): **apart** (undecided)
- `ga|gha|gua|gâ` /ga/ (parts ga, gâ; new conflict freq 0.0): **apart** (undecided)
- `gner|gnier|gnée` /Ne/ (parts gner, gnée; new conflict freq 1.0): **apart** (undecided)
- `geant|gent` /Z@/ (parts gent, geant; new conflict freq 0.0): **apart** (undecided)
- `bou|bout` /bu/ (parts bou; new conflict freq 0.0): **apart** (undecided)
- `mal|mâle` /mal/ (parts mal; new conflict freq 0.0): **apart** (undecided)
- `ccer|ceur|seur|soeur|sser|sseur` /s9R/ (parts sseur, seur, ceur; new conflict freq 0.0): **apart** (undecided)
- `ab|ap|hap` /ap/ (parts ab; new conflict freq 0.0): **apart** (undecided)
- `ca|cas|cat|cca|ka|kha|kka|qu'à|qua|quat` /ka/ (parts cat, ca, ka; new conflict freq 0.3): **apart** (undecided)
- `cker|cquer|cquée|ker|ké|quer|quée` /ke/ (parts quer; new conflict freq 1.4): **apart** (undecided)
- `sam|sang|sem|sen` /s@/ (parts sen, sem, sam; new conflict freq 0.0): **apart** (undecided)
- `cen|san` /s@/ (parts cen, san; new conflict freq 0.0): **apart** (undecided)
- `chi|ki|ky|qui` /ki/ (parts qui, ki; new conflict freq 0.0): **apart** (undecided)
- `lion|llion` /lj§/ (parts llion; new conflict freq 0.0): **apart** (undecided)
- `lage|llage` /laZ/ (parts llage, lage; new conflict freq 0.0): **apart** (undecided)
- `sit|site|sitent|sites` /zit/ (parts site, sitent; new conflict freq 1.1): **apart** (undecided)
- `dis|dys` /dis/ (parts dis, dys; new conflict freq 0.0): **apart** (undecided)
- `val|vale|valent|valle` /val/ (parts val; new conflict freq 0.2): **apart** (undecided)
- `cui|qui` /k8i/ (parts cui; new conflict freq 0.0): **apart** (undecided)
- `sine|zin|zine` /zin/ (parts sine, zine; new conflict freq 0.0): **apart** (undecided)
- `cein|cin|cym|sain|scin|sim|sin|sym|syn` /s5/ (parts sym, sim, cin, sin, syn, scin; new conflict freq 0.0): **apart** (undecided)
- `d'em|dan|den` /d@/ (parts dan, den; new conflict freq 0.0): **apart** (undecided)
- `nuer|nué` /n8e/ (parts nuer; new conflict freq 0.8): **apart** (undecided)
- `cer|cerre|cert|cère|saire|scère|sert|ssaire|sserre|ssert` /sER/ (parts ssaire; new conflict freq 0.0): **apart** (undecided)
- `nan|nant|nent|nnant` /n@/ (parts nant, nnant, nent; new conflict freq 0.0): **apart** (undecided)
- `ra|rai|raie|re|rhé|ré|réh` /Re/ (parts ré, re, rhé; new conflict freq 0.3): **fused**
- `vau|vo|vos` /vo/ (parts vo, vau; new conflict freq 0.0): **apart** (undecided)
- `fic|fique|phique` /fik/ (parts fique, phique; new conflict freq 0.0): **apart** (undecided)
- `vai|ve|vei|vé|vê` /vE/ (parts ve, vai, vê, vei; new conflict freq 2.0): **apart** (undecided)
- `ter|ther` /tER/ (parts ter, ther; new conflict freq 0.0): **apart** (undecided)
- `bau|bo|boh` /bo/ (parts bo, bau; new conflict freq 0.0): **apart** (undecided)
- `pea|pee|pi|py` /pi/ (parts pi, py; new conflict freq 0.5): **apart** (undecided)
- `lea|li|lie|ly` /li/ (parts li, ly; new conflict freq 1.8): **apart** (undecided)
- `moe|moi` /mwa/ (parts moi; new conflict freq 0.0): **apart** (undecided)
- `sel|selle|selles|zel|zelle` /zEl/ (parts selle; new conflict freq 0.1): **apart** (undecided)
- `vir|vire` /viR/ (parts vir; new conflict freq 0.0): **apart** (undecided)
- `nal|nales|nnal|nnale|nnales` /nal/ (parts nal; new conflict freq 0.8): **apart** (undecided)
- `rol|role|rolle` /ROl/ (parts role; new conflict freq 0.0): **apart** (undecided)
- `rage|rrage` /RaZ/ (parts rage, rrage; new conflict freq 0.0): **apart** (undecided)
- `cours|court` /kuR/ (parts cours; new conflict freq 0.0): **apart** (undecided)
- `laire|ler|llaire|lère` /lER/ (parts laire, llaire; new conflict freq 0.0): **apart** (undecided)
- `va|vah|wa` /va/ (parts va; new conflict freq 0.0): **apart** (undecided)
- `cance|kaans|quance|quence` /k@s/ (parts quence; new conflict freq 0.0): **apart** (undecided)
- `par|pard|pare|pars|part` /paR/ (parts pard; new conflict freq 0.0): **apart** (undecided)
- `ceau|sault|saut|sceau|seau|so|ssaut|sseau|sso|ssot` /so/ (parts sseau, ceau, so; new conflict freq 0.1): **apart** (undecided)
- `la|lla|lâ` /la/ (parts la, lâ; new conflict freq 0.0): **apart** (undecided)
- `ckel|quel|quelle` /kEl/ (parts quel, quelle; new conflict freq 0.0): **apart** (undecided)
- `tim|time` /tim/ (parts time; new conflict freq 0.0): **apart** (undecided)
- `cis|cys|sis|sys` /sis/ (parts sys, sis; new conflict freq 0.0): **apart** (undecided)
- `ler|leur|lheur|ller|lleur` /l9R/ (parts leur, lleur; new conflict freq 0.0): **apart** (undecided)
- `vance|vence` /v@s/ (parts vance; new conflict freq 0.0): **apart** (undecided)
- `vaire|ver|vers|vert|vère|wehr` /vER/ (parts vers, vert, vaire; new conflict freq 0.0): **apart** (undecided)
- `san|sant|sent|zan|zant` /z@/ (parts sant, san; new conflict freq 0.0): **apart** (undecided)
- `pied|pier|pié` /pje/ (parts pier; new conflict freq 1.3): **apart** (undecided)
- `thyle|til|tile|tille|tyle` /til/ (parts tile, til; new conflict freq 0.5): **apart** (undecided)
- `rie|rier|riez|rrier|rrié` /Rje/ (parts rier, rrier, riez; new conflict freq 0.0): **apart** (undecided)
- `lloir|loir|loire` /lwaR/ (parts loir; new conflict freq 0.0): **apart** (undecided)
- `rai|raie|raient|rais|rait|ret|rey|rrais|rret|rrêt|rè|rêt` /RE/ (parts rais, ret, rait, raie, raient; new conflict freq 1.6): **apart** (undecided)
- `pon|pons|pont|ppon` /p§/ (parts pon; new conflict freq 0.0): **apart** (undecided)
- `lope|loppe` /lOp/ (parts lope; new conflict freq 0.0): **apart** (undecided)
- `ma|mac|mas|mat|mma|mmas` /ma/ (parts ma, mat, mas; new conflict freq 0.0): **apart** (undecided)
- `hu|u|uh` /y/ (parts u, hu; new conflict freq 0.0): **apart** (undecided)
- `pain|paing|peint|pin|ppin` /p5/ (parts pin; new conflict freq 0.0): **apart** (undecided)
- `chau|cho|chô|sho|show` /So/ (parts chau, cho, chô; new conflict freq 0.0): **apart** (undecided)
- `ssure|ssures|sure|çure` /syR/ (parts ssure, sure; new conflict freq 0.0): **apart** (undecided)
- `gou|goû` /gu/ (parts gou; new conflict freq 0.1): **apart** (undecided)
- `bite|bitent|bites|byte` /bit/ (parts bite, bites, bitent; new conflict freq 0.0): **apart** (undecided)
- `mage|mmage` /maZ/ (parts mmage, mage; new conflict freq 0.0): **apart** (undecided)
- `ta|tah|tei|tha|tâ` /ta/ (parts ta, tâ, tha; new conflict freq 5.4): **apart** (undecided)
- `xi|xie|xis|xy|xys` /ksi/ (parts xie; new conflict freq 0.0): **apart** (undecided)
- `ge|je` /Z°/ (parts je, ge; new conflict freq -0.0): **apart** (undecided)
- `fae|fai|fe|foe|fé|fée|féé|fê|phoe|phé` /fe/ (parts fé, phé, fe; new conflict freq 0.3): **apart** (undecided)
- `si|sie|sil|sis|sy|zi|zy|zzi|zzy` /zi/ (parts sie, zi, si; new conflict freq 1.5): **apart** (undecided)
- `tance|tence|tense|ttance|ttence` /t@s/ (parts tance, tence; new conflict freq 0.0): **apart** (undecided)
- `ba|bac|bah|bas|bat|bbat` /ba/ (parts bat, ba; new conflict freq 0.0): **apart** (undecided)
- `re|rea|rhi|rhy|ri|rie` /Ri/ (parts ri, rhi, re; new conflict freq 0.0): **apart** (undecided)
- `cul|cule` /kyl/ (parts cule; new conflict freq 0.0): **apart** (undecided)
- `ron|rond|rons|ront|rron` /R§/ (parts ron, rron, rons, ront; new conflict freq 0.0): **apart** (undecided)
- `niaire|nière|nnière` /njER/ (parts nière, nnière; new conflict freq 0.0): **apart** (undecided)
- `sion|ziom` /zj§/ (parts sion; new conflict freq 0.0): **apart** (undecided)
- `pla|plai|plâ` /pla/ (parts pla, plâ; new conflict freq 0.0): **apart** (undecided)
- `net|neth|nette|nettes|nnette|nnête|nète` /nEt/ (parts nnette, nette; new conflict freq 0.0): **apart** (undecided)
- `car|kar|quar` /kaR/ (parts car, quar; new conflict freq 0.0): **apart** (undecided)
- `da|dah|das|dat|date|ddha` /da/ (parts dat, da; new conflict freq 0.1): **apart** (undecided)
- `illeux|lleux|ïeu|ïeux` /j2/ (parts lleux, illeux; new conflict freq 0.0): **apart** (undecided)
- `dain|din` /d5/ (parts din; new conflict freq 0.0): **apart** (undecided)
- `cquette|ket|kette|quette|quête` /kEt/ (parts quette; new conflict freq 0.0): **apart** (undecided)
- `an|and|ans|ant|empt|ent` /@/ (parts ant, ent, an; new conflict freq 0.2): **apart** (undecided)
- `poi|poê` /pwa/ (parts poi; new conflict freq 0.0): **apart** (undecided)
- `toi|toua` /twa/ (parts toi; new conflict freq 0.0): **apart** (undecided)
- `laite|leth|lette|llaite|llaitent|llaites|llette|lète` /lEt/ (parts lette; new conflict freq 0.0): **apart** (undecided)
- `gar|gard|gare|garre|guar` /gaR/ (parts gard; new conflict freq 0.0): **apart** (undecided)
- `ddie|ddy|dee|dhi|di|die|dis|dit|dits|dy` /di/ (parts di, die, dit, dis; new conflict freq 2.2): **apart** (undecided)
- `sain|sein|sin|zain|zin` /z5/ (parts sin; new conflict freq 0.0): **apart** (undecided)
- `des|dés` /des/ (parts des, dés; new conflict freq 0.0): **apart** (undecided)
- `rance|rence|rrance|rrence` /R@s/ (parts rence, rance; new conflict freq 0.0): **apart** (undecided)
- `ccu|cu|cul|cus|ku` /ky/ (parts cu; new conflict freq 0.2): **apart** (undecided)
- `tice|tis|tiss|tisse|tys` /tis/ (parts tice, tis; new conflict freq 0.0): **apart** (undecided)
- `pais|pect|pet` /pE/ (parts pect; new conflict freq 0.0): **apart** (undecided)
- `blai|ble|blê` /blE/ (parts ble; new conflict freq 0.0): **apart** (undecided)
- `rain|rein|rin|rrain|rrin` /R5/ (parts rrain, rin, rain; new conflict freq 0.1): **apart** (undecided)
- `bra|brah` /bRa/ (parts bra; new conflict freq 0.0): **apart** (undecided)
- `cam|can|kan|quan` /k@/ (parts cam, can, quan; new conflict freq -0.0): **apart** (undecided)
- `pan|pang|pant|pens|pent|ppant` /p@/ (parts pant, pan; new conflict freq 0.2): **apart** (undecided)
- `spe|spé` /spe/ (parts spé; new conflict freq 0.0): **apart** (undecided)
- `rad|rade|rrade` /Rad/ (parts rade; new conflict freq 0.0): **apart** (undecided)
- `der|deur` /d9R/ (parts deur, der; new conflict freq 0.2): **apart** (undecided)
- `cens|cent|san|sant|scent|sent|ssan|ssant|çant` /s@/ (parts ssant, cent, çant, sant, scent; new conflict freq 0.7): **apart** (undecided)
- `maître|mettre|mmettre|mètre` /mEtR/ (parts mettre, mètre; new conflict freq 0.0): **apart** (undecided)
- `lan|land|lant|lent|llan|llant|llent` /l@/ (parts lant, lan, lent, llant; new conflict freq 0.0): **apart** (undecided)
- `mael|mal` /mal/ (parts mal; new conflict freq 0.0): **apart** (undecided)
- `gree|gré|grée` /gRe/ (parts gré; new conflict freq 0.0): **apart** (undecided)
- `rif|riff|riph` /Rif/ (parts rif; new conflict freq 0.1): **apart** (undecided)
- `thera|tra|tras|trat` /tRa/ (parts tra; new conflict freq 0.2): **apart** (undecided)
- `ffieh|ffier|fier|phier|phié` /fje/ (parts fier, phier; new conflict freq 0.3): **apart** (undecided)
- `ni|nie|nih|ny` /ni/ (parts ni; new conflict freq 0.0): **apart** (undecided)
- `cet|cès|set|ssai|ssaient|ssais|ssait|sset|çais` /sE/ (parts cès, cet; new conflict freq 0.0): **apart** (undecided)
- `sance|sence` /z@s/ (parts sance; new conflict freq 0.0): **apart** (undecided)
- `traî|tre|trei|tré` /tRe/ (parts tré; new conflict freq 0.0): **apart** (undecided)
- `ciance|cience|science|tience|tiens` /sj@s/ (parts science; new conflict freq 0.0): **apart** (undecided)
- `nae|ne|nei|né` /ne/ (parts né; new conflict freq 0.1): **apart** (undecided)
- `fra|phra` /fRa/ (parts fra, phra; new conflict freq 0.0): **apart** (undecided)
- `hoi|houa|oi|oua|wa` /wa/ (parts oi, wa, oua; new conflict freq 0.0): **apart** (undecided)
- `seau|so|zo` /zo/ (parts seau, zo, so; new conflict freq 0.1): **apart** (undecided)
- `sième|xième|zième` /zjEm/ (parts zième; new conflict freq 0.0): **apart** (undecided)
- `mau|maux|meau|mmeau|mo|moan|mot` /mo/ (parts mo, meau; new conflict freq 0.1): **apart** (undecided)
- `nic|nich|nik|nique|nnique` /nik/ (parts nique; new conflict freq 1.2): **apart** (undecided)
- `illie|illis|illy|lli|llis|lly` /ji/ (parts illis; new conflict freq 0.0): **apart** (undecided)
- `prai|pre|pré|prê` /pRE/ (parts pre, prê; new conflict freq -0.0): **apart** (undecided)
- `illais|illet|llais|llet` /jE/ (parts llet, illet; new conflict freq 0.0): **apart** (undecided)
- `gler|glée` /gle/ (parts gler; new conflict freq 0.0): **apart** (undecided)
- `bai|be|bei|bê` /bE/ (parts bai, bê, be; new conflict freq 1.4): **apart** (undecided)
- `gee|gi|gie|gis|ji` /Zi/ (parts gie; new conflict freq 0.0): **apart** (undecided)
- `foo|fou` /fu/ (parts fou; new conflict freq 0.0): **apart** (undecided)
- `pace|pas|passe` /pas/ (parts pace; new conflict freq 0.0): **apart** (undecided)
- `nar|nard|nnard` /naR/ (parts nard, nar; new conflict freq 0.0): **apart** (undecided)
- `sable|ssable|çable` /sabl/ (parts sable, ssable, çable; new conflict freq 0.0): **apart** (undecided)
- `al|hal` /al/ (parts al, hal; new conflict freq 0.7): **apart** (undecided)
- `rit|rite|ritent|rites|rrite|rritent|rrites|ryte` /Rit/ (parts rite; new conflict freq 0.0): **apart** (undecided)
- `chette|chète` /SEt/ (parts chette; new conflict freq 0.0): **apart** (undecided)
- `mon|mont` /m§/ (parts mon; new conflict freq 0.0): **apart** (undecided)
- `dieu|dieux` /dj2/ (parts dieu, dieux; new conflict freq 0.0): **apart** (undecided)
- `tage|ttage` /taZ/ (parts tage, ttage; new conflict freq 0.0): **apart** (undecided)
- `mais|may|met|mets|mmet` /mE/ (parts met; new conflict freq 0.0): **apart** (undecided)
- `thume|tume` /tym/ (parts tume; new conflict freq 0.0): **apart** (undecided)
- `hur|ur` /yR/ (parts ur, hur; new conflict freq 0.0): **apart** (undecided)
- `geance|gence` /Z@s/ (parts gence, geance; new conflict freq 0.0): **apart** (undecided)
- `am|ame|ham` /am/ (parts am; new conflict freq 0.0): **apart** (undecided)
- `nai|naî|ne|nei|né` /nE/ (parts nai; new conflict freq 0.0): **apart** (undecided)
- `cence|scence|sence|sens|sense|ssance|ssence` /s@s/ (parts ssance, cence, scence; new conflict freq 0.0): **apart** (undecided)
- `tesse|tès` /tEs/ (parts tesse; new conflict freq 0.0): **apart** (undecided)
- `vam|van|ven` /v@/ (parts ven, vam, van; new conflict freq 0.1): **apart** (undecided)
- `gir|gire` /ZiR/ (parts gir; new conflict freq 0.0): **apart** (undecided)
- `fer|feur|ffeur|pher` /f9R/ (parts ffeur, feur, fer; new conflict freq 0.0): **apart** (undecided)
- `cket|ckey|cquet|cquêt|kay|quais|quet` /kE/ (parts quet; new conflict freq 0.0): **apart** (undecided)
- `ob|op` /Op/ (parts ob, op; new conflict freq 0.0): **apart** (undecided)
- `mise|miz` /miz/ (parts mise; new conflict freq 0.0): **apart** (undecided)
- `tail|taille` /taj/ (parts tail, taille; new conflict freq 0.0): **apart** (undecided)
- `thri|tri|trie|try` /tRi/ (parts tri; new conflict freq 0.0): **apart** (undecided)
- `fram|fran` /fR@/ (parts fran; new conflict freq 0.0): **apart** (undecided)
- `taire|ter|terre|ther|thère|ttaire|tter|tère|tèrent` /tER/ (parts taire, tère, ter, tèrent; new conflict freq 0.1): **apart** (undecided)
- `thique|tic|tik|tique|ttique|tyque` /tik/ (parts tique, thique, tic; new conflict freq 1.8): **apart** (undecided)
- `cal|cale|chal|kal` /kal/ (parts cal; new conflict freq 0.0): **apart** (undecided)
- `du|dû` /dy/ (parts du; new conflict freq 0.0): **apart** (undecided)
- `sau|so` /sO/ (parts so; new conflict freq 0.0): **apart** (undecided)
- `lise|lyse` /liz/ (parts lise, lyse; new conflict freq 0.0): **apart** (undecided)
- `lain|lin|llin` /l5/ (parts lin, lain; new conflict freq 0.0): **apart** (undecided)
- `cien|ssien|tien` /sj5/ (parts cien, tien, ssien; new conflict freq 0.0): **apart** (undecided)
- `lai|laie|lais|legs|let|lley` /lE/ (parts let, lais; new conflict freq 2.8): **apart** (undecided)
- `eu|eux` /2/ (parts eux; new conflict freq 0.0): **apart** (undecided)
- `table|ttable` /tabl/ (parts table, ttable; new conflict freq 0.0): **apart** (undecided)
- `cri|crii|cry` /kRij/ (parts cri; new conflict freq 0.0): **apart** (undecided)
- `gai|ggae|gger|guer` /ge/ (parts guer; new conflict freq 0.1): **apart** (undecided)
- `ver|veur|weur` /v9R/ (parts veur; new conflict freq 0.0): **apart** (undecided)
- `cain|kin|quain|quin` /k5/ (parts cain, quin; new conflict freq 0.2): **apart** (undecided)
- `thon|ton|tons|tton` /t§/ (parts ton, tons; new conflict freq 0.7): **apart** (undecided)
- `pui|puî` /p8i/ (parts pui; new conflict freq 0.0): **apart** (undecided)
- `champ|chan|chand|chant` /S@/ (parts chant; new conflict freq 0.2): **apart** (undecided)
- `hor|or` /OR/ (parts or, hor; new conflict freq 0.0): **apart** (undecided)
- `throm|trom|tron` /tR§/ (parts trom, tron; new conflict freq 0.0): **apart** (undecided)
- `breu|breux` /bR2/ (parts breux; new conflict freq 0.4): **apart** (undecided)
- `gei|ja|jea` /Za/ (parts ja; new conflict freq 0.0): **apart** (undecided)
- `lou|loup|loux` /lu/ (parts lou; new conflict freq 0.0): **apart** (undecided)
- `mer|meur|meure|mmer|mmeur` /m9R/ (parts meur; new conflict freq 0.0): **apart** (undecided)
- `fan|fen|phan` /f@/ (parts fan, fen; new conflict freq 0.3): **apart** (undecided)
- `tome|tôme` /tom/ (parts tome; new conflict freq 0.0): **apart** (undecided)
- `ciant|cient|scient|tiant|tient` /sj@/ (parts scient; new conflict freq 0.0): **apart** (undecided)
- `pir|pire` /piR/ (parts pir; new conflict freq 0.0): **apart** (undecided)
- `llote|lote|lotte` /lOt/ (parts lote, lotte; new conflict freq 0.0): **apart** (undecided)
- `tiaire|tière|ttière` /tjER/ (parts tière; new conflict freq 0.0): **apart** (undecided)
- `vit|vite|vitent|vites` /vit/ (parts vite, vites, vitent; new conflict freq 0.0): **apart** (undecided)
- `tau|thau|tho|to|tô` /to/ (parts to, tau, tho; new conflict freq 0.3): **apart** (undecided)
- `lam|lan|len` /l@/ (parts lan, len, lam; new conflict freq 0.0): **apart** (undecided)
- `plai|ple|plei` /plE/ (parts plai; new conflict freq 0.0): **apart** (undecided)
- `bau|baud|beau|bo|bot` /bo/ (parts bo, bot, beau; new conflict freq 0.1): **apart** (undecided)
- `chré|cre|cré|crée|crê` /kRe/ (parts cré; new conflict freq 0.2): **apart** (undecided)
- `thyste|tiste|ttiste` /tist/ (parts tiste, ttiste; new conflict freq 0.0): **apart** (undecided)
- `la|lacs|lah|las|lat|lla|llah|llat|là` /la/ (parts lat, la, las, lla; new conflict freq 1.3): **apart** (undecided)
- `nage|nnage` /naZ/ (parts nage, nnage; new conflict freq 0.0): **apart** (undecided)
- `gal|gale` /gal/ (parts gal, gale; new conflict freq 0.0): **apart** (undecided)
- `chi|chie|chis|chy|shi` /Si/ (parts chie, chi; new conflict freq 0.0): **apart** (undecided)
- `ness|nesse|nnesse` /nEs/ (parts nesse; new conflict freq 0.0): **apart** (undecided)
- `raître|rèthre|rètre` /REtR/ (parts raître; new conflict freq 0.0): **apart** (undecided)
- `dier|diée` /dje/ (parts dier; new conflict freq 0.0): **apart** (undecided)
- `naie|nais|nay|net|ney|nnaie|nnais|nnay|nnet|nêt` /nE/ (parts net, nais, nnet, nnais; new conflict freq 0.0): **apart** (undecided)
- `mar|mard|marre|mart|mmard` /maR/ (parts mar, mard; new conflict freq 0.0): **apart** (undecided)
- `gage|guage` /gaZ/ (parts gage; new conflict freq 0.0): **apart** (undecided)
- `na|nas|nat|naüm|nha|nna|nnah|nnat` /na/ (parts na, nat; new conflict freq 0.1): **apart** (undecided)
- `cu|ku` /ky/ (parts cu; new conflict freq 0.0): **apart** (undecided)
- `llois|loi|lois` /lwa/ (parts loi; new conflict freq 0.0): **apart** (undecided)
- `paim|pein|pen|pim|pin` /p5/ (parts pein, pin, pen; new conflict freq 0.0): **apart** (undecided)
- `frau|fro|frô` /fRo/ (parts fro; new conflict freq 0.0): **apart** (undecided)
- `pri|prii` /pRij/ (parts pri; new conflict freq 0.0): **apart** (undecided)
- `tra|trai|traî|tre|trei` /tRE/ (parts trai, traî, tre, trei; new conflict freq 0.0): **apart** (undecided)
- `cide|side` /sid/ (parts cide; new conflict freq 0.0): **apart** (undecided)
- `thrine|trine|ttrine` /tRin/ (parts trine; new conflict freq 0.0): **apart** (undecided)
- `tress|tresse` /tREs/ (parts tresse; new conflict freq 0.0): **apart** (undecided)
- `riel|rielle|rriel` /RjEl/ (parts riel; new conflict freq 0.0): **apart** (undecided)
- `nable|nnable` /nabl/ (parts nable, nnable; new conflict freq 0.0): **apart** (undecided)
- `tease|tise|ttise` /tiz/ (parts tise; new conflict freq 0.0): **apart** (undecided)
- `fforme|forme` /fORm/ (parts forme; new conflict freq 0.0): **apart** (undecided)
- `roir|roire|rroir` /RwaR/ (parts roir; new conflict freq 0.0): **apart** (undecided)
- `liste|lliste|lyste` /list/ (parts liste, lliste; new conflict freq 0.0): **apart** (undecided)
- `lace|las|lasse|llace` /las/ (parts lasse; new conflict freq 0.0): **apart** (undecided)
- `rrus|rus` /Rys/ (parts rus; new conflict freq 0.0): **apart** (undecided)
- `el|elle|elles|ël` /El/ (parts el, elle; new conflict freq 0.0): **apart** (undecided)
- `naire|naires|ner|nnaire|nner|nnerre|nère` /nER/ (parts naire, nnaire, ner; new conflict freq 0.7): **apart** (undecided)
- `au|aut|o|os|ot` /o/ (parts o, au; new conflict freq 0.2): **apart** (undecided)
- `cette|scète|set|ssette` /sEt/ (parts ssette, cette; new conflict freq 1.2): **apart** (undecided)
- `therie|tri|trie|trit|try` /tRi/ (parts trie; new conflict freq 0.1): **apart** (undecided)
- `cine|scine|sin|sine|ssine` /sin/ (parts cine, ssine; new conflict freq 0.0): **apart** (undecided)
- `ffort|fort|phore` /fOR/ (parts fort, phore; new conflict freq 0.0): **apart** (undecided)
- `bru|brû` /bRy/ (parts brû, bru; new conflict freq -0.0): **apart** (undecided)
- `rable|rrable` /Rabl/ (parts rable; new conflict freq 0.0): **apart** (undecided)
- `mis|mys` /mis/ (parts mys, mis; new conflict freq 0.0): **apart** (undecided)
- `tante|tente|ttante|ttente` /t@t/ (parts tante; new conflict freq 0.0): **apart** (undecided)
- `ciaire|cière|ssière|tiaire` /sjER/ (parts ssière, ciaire, cière; new conflict freq 0.6): **apart** (undecided)
- `traie|trait|ttrait` /tRE/ (parts trait; new conflict freq 0.0): **apart** (undecided)
- `mable|mmable` /mabl/ (parts mable, mmable; new conflict freq 0.0): **apart** (undecided)
- `chi|chie|chih|chy|schi|shi` /Si/ (parts chi; new conflict freq 1.5): **apart** (undecided)
- `nnois|noi|nois|noît` /nwa/ (parts nois; new conflict freq 0.1): **apart** (undecided)
- `gique|jik` /Zik/ (parts gique; new conflict freq 0.0): **apart** (undecided)
- `tam|tan|tem|ten` /t@/ (parts ten, tem, tan, tam; new conflict freq 0.0): **apart** (undecided)
- `nau|naud|neau|nneau|nnot|no|nod|not` /no/ (parts no, nneau, neau, not; new conflict freq 2.5): **apart** (undecided)
- `gnol|gnole|gnoles` /NOl/ (parts gnol, gnole; new conflict freq 0.0): **apart** (undecided)
- `sure|zur` /zyR/ (parts sure; new conflict freq 0.0): **apart** (undecided)
- `cir|cire|ssir|ssire` /siR/ (parts ssir, cir; new conflict freq 0.0): **apart** (undecided)
- `battre|bâtre` /batR/ (parts battre; new conflict freq 0.0): **apart** (undecided)
- `tiv|tive` /tiv/ (parts tive; new conflict freq 0.0): **apart** (undecided)
- `vain|vin` /v5/ (parts vin; new conflict freq 0.0): **apart** (undecided)
- `cieux|ssieu|ssieux|tieux` /sj2/ (parts cieux, tieux; new conflict freq 0.1): **apart** (undecided)
- `rau|rho|ro|rô` /Ro/ (parts ro, rô, rho; new conflict freq 1.0): **apart** (undecided)
- `geux|jeu` /Z2/ (parts geux; new conflict freq 0.0): **apart** (undecided)
- `pi|pie|pis|pit|ppie|ppy|py` /pi/ (parts pie, pi; new conflict freq 1.5): **apart** (undecided)
- `fai|faî|fe|fei|fê` /fE/ (parts fê, fe, fai; new conflict freq 0.3): **apart** (undecided)
- `pas|passe` /pas/ (parts pas; new conflict freq 0.0): **apart** (undecided)
- `cir|seer|sir` /siR/ (parts cir; new conflict freq 0.0): **apart** (undecided)
- `ra|ray` /REj/ (parts ray; new conflict freq 0.0): **apart** (undecided)
- `bbi|bbies|bby|bee|bi|bie|bis|bit|by` /bi/ (parts bi, by, bit, bie; new conflict freq 0.9): **apart** (undecided)
- `thu|tu|tue` /ty/ (parts tu; new conflict freq 0.0): **apart** (undecided)
- `car|card|carre|cart|cquard|kare|kkar|quard` /kaR/ (parts card, cart; new conflict freq 1.1): **apart** (undecided)
- `air|aire|ère` /ER/ (parts ère, aire; new conflict freq 0.0): **apart** (undecided)
- `mite|mitent|mites` /mit/ (parts mite, mitent, mites; new conflict freq 0.4): **apart** (undecided)
- `scam|scan` /sk@/ (parts scan; new conflict freq 0.0): **apart** (undecided)
- `dal|dale` /dal/ (parts dale, dal; new conflict freq 0.0): **apart** (undecided)
- `free|fri|phry` /fRi/ (parts fri; new conflict freq 0.0): **apart** (undecided)
- `gaud|gaux|gho|go|got|goth|guo` /go/ (parts go, got; new conflict freq 0.2): **apart** (undecided)
- `illance|llance|ïence` /j@s/ (parts llance; new conflict freq 0.0): **apart** (undecided)
- `mance|mence|mmense` /m@s/ (parts mence, mance; new conflict freq 0.0): **apart** (undecided)
- `rel|relle|relles` /REl/ (parts rel, relle; new conflict freq 0.0): **apart** (undecided)
- `sa|sat|za` /za/ (parts za, sa; new conflict freq 0.1): **apart** (undecided)
- `ance|ence` /@s/ (parts ance, ence; new conflict freq 0.0): **apart** (undecided)
- `page|ppage` /paZ/ (parts page; new conflict freq 0.0): **apart** (undecided)
- `nau|no` /no/ (parts no, nau; new conflict freq 0.0): **apart** (undecided)
- `teak|teck|thèque|tèque` /tEk/ (parts thèque, tèque; new conflict freq 0.2): **apart** (undecided)
- `thien|tien` /tj5/ (parts tien; new conflict freq 0.0): **apart** (undecided)
- `bil|bile|byle|bylle` /bil/ (parts bile; new conflict freq 0.0): **apart** (undecided)
- `clea|cli|klee` /kli/ (parts cli; new conflict freq 0.0): **apart** (undecided)
- `gaie|gaî|gei|gué|guê` /ge/ (parts gué; new conflict freq 0.0): **apart** (undecided)
- `pal|pale|ppal` /pal/ (parts pal; new conflict freq 0.0): **apart** (undecided)
- `cal|cale|ccal|qual` /kal/ (parts cal, cale; new conflict freq 1.7): **apart** (undecided)
- `chry|cri|crie|cry` /kRi/ (parts cri; new conflict freq 0.0): **apart** (undecided)
- `la|lai|laie|le|lé` /le/ (parts lé, le; new conflict freq 0.4): **apart** (undecided)
- `ette|ète` /Et/ (parts ette; new conflict freq 0.0): **apart** (undecided)
- `tomne|ton|tone|tonne` /tOn/ (parts tone; new conflict freq 0.0): **apart** (undecided)
- `bbon|bon|bond` /b§/ (parts bon, bond; new conflict freq 0.0): **apart** (undecided)
- `feuil|feuille` /f9j/ (parts feuille; new conflict freq 0.1): **apart** (undecided)
- `pli|plie|plies|plis` /pli/ (parts pli; new conflict freq 0.0): **apart** (undecided)
- `cra|crai|crâ|kra` /kRa/ (parts cra, crâ; new conflict freq 0.0): **apart** (undecided)
- `xuel|xuelle` /ks8El/ (parts xuel; new conflict freq 0.3): **apart** (undecided)
- `dance|danse|dence` /d@s/ (parts dence, dance; new conflict freq 0.0): **apart** (undecided)
- `trique|ttrique` /tRik/ (parts trique; new conflict freq 0.0): **apart** (undecided)
- `ffice|fice` /fis/ (parts fice; new conflict freq 0.0): **apart** (undecided)
- `sier|sié|zier` /zje/ (parts sier; new conflict freq 0.6): **apart** (undecided)
- `al|ale` /al/ (parts al; new conflict freq 0.3): **apart** (undecided)
- `pette|pettes|ppette|pète|pètes|pête` /pEt/ (parts pette; new conflict freq 0.4): **apart** (undecided)
- `bri|brie` /bRi/ (parts bri; new conflict freq 0.0): **apart** (undecided)
- `cru|crû` /kRy/ (parts cru; new conflict freq 0.0): **apart** (undecided)
- `lin|line|lline` /lin/ (parts lline, line; new conflict freq 0.0): **apart** (undecided)
- `tif|tife|tiff` /tif/ (parts tif; new conflict freq 0.0): **apart** (undecided)
- `ste|stea|sti|sty` /sti/ (parts sty, sti; new conflict freq 0.0): **apart** (undecided)
- `cond|gon|gong` /g§/ (parts gon; new conflict freq 0.0): **apart** (undecided)
- `rone|ronne` /ROn/ (parts rone; new conflict freq 0.0): **apart** (undecided)
- `rhom|rom|ron` /R§/ (parts ron; new conflict freq 0.0): **apart** (undecided)
- `ppu|pu` /py/ (parts pu; new conflict freq 0.0): **apart** (undecided)
- `cchi|cquis|cquit|kee|ki|kie|kies|ky|qui|quie|quis` /ki/ (parts quis, ki; new conflict freq 0.7): **apart** (undecided)
- `bel|belle` /bEl/ (parts belle, bel; new conflict freq 0.1): **apart** (undecided)
- `tec|tech` /tEk/ (parts tech; new conflict freq 0.0): **apart** (undecided)
- `chia|ria|riat` /Rja/ (parts riat, ria; new conflict freq 0.0): **apart** (undecided)
- `rou|roue` /Ru/ (parts rou; new conflict freq 0.0): **apart** (undecided)
- `illir|llir` /jiR/ (parts illir; new conflict freq 0.0): **apart** (undecided)
- `illant|llan|llant|yant` /j@/ (parts llant, illant; new conflict freq 0.0): **apart** (undecided)
- `mid|mide|myde` /mid/ (parts mide; new conflict freq 0.0): **apart** (undecided)
- `ddhique|dic|dique` /dik/ (parts dique; new conflict freq 0.0): **apart** (undecided)
- `log|logue` /lOg/ (parts logue; new conflict freq 0.0): **apart** (undecided)
- `bbler|bler` /ble/ (parts bler; new conflict freq 0.0): **apart** (undecided)
- `blé|blée` /ble/ (parts blé; new conflict freq 0.3): **apart** (undecided)
- `ball|bol|bole` /bOl/ (parts bole; new conflict freq 0.0): **apart** (undecided)
- `et|eth|het` /Et/ (parts eth; new conflict freq 0.0): **apart** (undecided)
- `lau|lo|loa` /lo/ (parts lo, lau; new conflict freq 0.0): **apart** (undecided)
- `ir|ïr|ïre` /iR/ (parts ir; new conflict freq 0.0): **apart** (undecided)
- `chla|cla|kla` /kla/ (parts cla; new conflict freq 0.0): **apart** (undecided)
- `cique|sique|ssik|ssique` /sik/ (parts ssique, cique; new conflict freq 0.0): **apart** (undecided)
- `ghol|gol|gole` /gOl/ (parts gol; new conflict freq 0.0): **apart** (undecided)
- `verse|verses` /vERs/ (parts verse; new conflict freq 0.0): **apart** (undecided)
- `nade|nnade` /nad/ (parts nade, nnade; new conflict freq 0.0): **apart** (undecided)
- `fil|phile|phylle` /fil/ (parts phile; new conflict freq 0.0): **apart** (undecided)
- `dir|dire` /diR/ (parts dir, dire; new conflict freq 0.0): **apart** (undecided)
- `ga|gas|gat|gha|gât` /ga/ (parts ga, gat; new conflict freq 0.0): **apart** (undecided)
- `lien|llien` /lj5/ (parts lien; new conflict freq 0.0): **apart** (undecided)
- `gil|gile` /Zil/ (parts gile; new conflict freq 0.3): **apart** (undecided)
- `mat|mate` /mat/ (parts mate; new conflict freq 0.0): **apart** (undecided)
- `meu|meux|mmeux` /m2/ (parts meux; new conflict freq 0.0): **apart** (undecided)
- `grafe|graphe` /gRaf/ (parts graphe; new conflict freq 0.0): **apart** (undecided)
- `ffee|ffi|fi|fis|fit|fix|phi|phie` /fi/ (parts phie; new conflict freq 0.0): **apart** (undecided)
- `croi|croî` /kRwa/ (parts croi; new conflict freq 0.0): **apart** (undecided)
- `cable|ccable|quable` /kabl/ (parts quable, cable; new conflict freq 0.0): **apart** (undecided)
- `cace|cas|casse|quace` /kas/ (parts casse; new conflict freq 0.0): **apart** (undecided)
- `cel|celle|celles|cèle|sel|ssel|sselle` /sEl/ (parts celle; new conflict freq 0.0): **apart** (undecided)
- `rhu|ru|rue` /Ry/ (parts ru; new conflict freq 0.0): **apart** (undecided)
- `lluer|llué|luer` /l8e/ (parts luer; new conflict freq 0.0): **apart** (undecided)
- `boi|boî` /bwa/ (parts boi; new conflict freq 0.0): **apart** (undecided)
- `ou|u` /u/ (parts ou; new conflict freq 0.0): **apart** (undecided)
- `coi|coua|cua|qua|quoi` /kwa/ (parts coi, qua; new conflict freq 0.0): **apart** (undecided)
- `thine|tine|ttine` /tin/ (parts tine; new conflict freq 0.0): **apart** (undecided)
- `baire|ber|bert|bère` /bER/ (parts bert, bère; new conflict freq 0.0): **apart** (undecided)
- `ciel|tiel` /sjEl/ (parts tiel, ciel; new conflict freq 0.0): **apart** (undecided)
- `illette|llette|llettes` /jEt/ (parts llette, illette; new conflict freq 0.0): **apart** (undecided)
- `laine|leine|len|llen|llène|lène` /lEn/ (parts lène; new conflict freq 0.2): **apart** (undecided)
- `bam|ban` /b@/ (parts ban, bam; new conflict freq 0.0): **apart** (undecided)
- `psi|psy` /psi/ (parts psy; new conflict freq 0.0): **apart** (undecided)
- `illage|illiage|llage|yage` /jaZ/ (parts llage, illage; new conflict freq 0.0): **apart** (undecided)
- `ccro|chro|cro|croc` /kRo/ (parts cro; new conflict freq 0.0): **apart** (undecided)
- `mette|mmette|mète` /mEt/ (parts mette; new conflict freq 0.0): **apart** (undecided)
- `le|leus|leux|lle|lleux` /l2/ (parts leux, lleux; new conflict freq 0.0): **apart** (undecided)
- `lir|lire|llir|llyre` /liR/ (parts lir, lire; new conflict freq 0.0): **apart** (undecided)
- `lic|lique|llique` /lik/ (parts lique, llique; new conflict freq 0.8): **apart** (undecided)
- `ssus|sus` /sys/ (parts sus; new conflict freq 0.0): **apart** (undecided)
- `dro|drô` /dRo/ (parts dro; new conflict freq 0.0): **apart** (undecided)
- `riste|rriste|ryste` /Rist/ (parts riste; new conflict freq 0.0): **apart** (undecided)
- `tache|ttache|tâche` /taS/ (parts tache; new conflict freq 0.0): **apart** (undecided)
- `lite|litent|lites|lithe|llite|lyte` /lit/ (parts lite, lithe, litent; new conflict freq 0.0): **apart** (undecided)
- `caire|cker|ker|kère|quaire|querre|quère` /kER/ (parts ker, caire; new conflict freq 0.0): **apart** (undecided)
- `brou|brouh` /bRu/ (parts brou; new conflict freq 0.0): **apart** (undecided)
- `illard|llard|llart|yard` /jaR/ (parts illard, llard; new conflict freq 0.0): **apart** (undecided)
- `illon|ion|llion|llon|llons|yon` /j§/ (parts llon, illon; new conflict freq 0.0): **apart** (undecided)
- `rion|rions|ryon` /Rj§/ (parts rions; new conflict freq 0.0): **apart** (undecided)
- `pom|pon` /p§/ (parts pom, pon; new conflict freq 0.0): **apart** (undecided)
- `man|mane` /man/ (parts man, mane; new conflict freq 0.0): **apart** (undecided)
- `main|men|min` /m5/ (parts main; new conflict freq 0.0): **apart** (undecided)
- `niste|nniste` /nist/ (parts niste, nniste; new conflict freq 0.0): **apart** (undecided)
- `ceux|seux|sseux` /s2/ (parts sseux; new conflict freq 0.0): **apart** (undecided)
- `tral|trales` /tRal/ (parts tral; new conflict freq 0.1): **apart** (undecided)
- `far|phar` /faR/ (parts far; new conflict freq 0.0): **apart** (undecided)
- `llure|lure` /lyR/ (parts lure; new conflict freq 0.0): **apart** (undecided)
- `nhomme|nome|num` /nOm/ (parts num, nome; new conflict freq 0.0): **apart** (undecided)
- `trau|tro|trô` /tRo/ (parts tro; new conflict freq 0.0): **apart** (undecided)
- `con|cond` /k§/ (parts con; new conflict freq 0.0): **apart** (undecided)
- `as|asth|az|hase` /as/ (parts as; new conflict freq 0.0): **apart** (undecided)
- `tadt|tate|tâtes` /tat/ (parts tate, tâtes; new conflict freq 0.0): **apart** (undecided)
- `choir|choire` /SwaR/ (parts choir; new conflict freq 0.0): **apart** (undecided)
- `rail|raille|railles|raï|rraille` /Raj/ (parts rail; new conflict freq 0.0): **apart** (undecided)
- `chaie|chet` /SE/ (parts chet; new conflict freq 0.0): **apart** (undecided)
- `dia|diat` /dja/ (parts dia; new conflict freq 0.0): **apart** (undecided)
- `gnard|gnare` /NaR/ (parts gnard; new conflict freq 0.0): **apart** (undecided)
- `plom|plon` /pl§/ (parts plon, plom; new conflict freq -0.0): **apart** (undecided)
- `crai|cre|crè|cré|crê` /kRE/ (parts crê; new conflict freq 0.0): **apart** (undecided)
- `pie|pied|pié` /pje/ (parts pié; new conflict freq 0.2): **apart** (undecided)
- `gai|gaî|ghe|gue|guê` /gE/ (parts gue; new conflict freq 0.6): **apart** (undecided)
- `bain|bbin|bin` /b5/ (parts bin, bain; new conflict freq 0.0): **apart** (undecided)
- `gli|gly` /gli/ (parts gli, gly; new conflict freq 0.0): **apart** (undecided)
- `taie|taient|tais|tait|tet|têt` /tE/ (parts tait, tais, taient, tet; new conflict freq 0.0): **apart** (undecided)
- `ge|gei|gey|gè|gê|je` /ZE/ (parts gei; new conflict freq 0.0): **apart** (undecided)
- `tern|terne|ternes` /tERn/ (parts terne; new conflict freq 0.0): **apart** (undecided)
- `sad|sade|ssade|çade` /sad/ (parts ssade; new conflict freq 0.0): **apart** (undecided)
- `rick|rique|rrhique|rrick|rrique` /Rik/ (parts rique; new conflict freq 0.0): **apart** (undecided)
- `tri|trii` /tRij/ (parts tri; new conflict freq 0.0): **apart** (undecided)
- `cit|cite|citent|cites|cyte|scite|scitent|scites|site|ssit|ssite|ssitent|ssites` /sit/ (parts cite, citent, cites; new conflict freq 0.0): **apart** (undecided)
- `tex|thex` /tEks/ (parts tex; new conflict freq 0.0): **apart** (undecided)
- `cas|casse|kas` /kas/ (parts cas; new conflict freq 0.0): **apart** (undecided)
- `pic|pik|pique|ppique` /pik/ (parts pique; new conflict freq 0.0): **apart** (undecided)
- `geon|jon|jonc` /Z§/ (parts geon; new conflict freq 0.0): **apart** (undecided)
- `rine|rrine` /Rin/ (parts rine; new conflict freq 0.0): **apart** (undecided)
- `gnan|gnant` /N@/ (parts gnant; new conflict freq 0.0): **apart** (undecided)
- `illot|llaud|llo|llot|yot|ïaut` /jo/ (parts illot; new conflict freq 0.0): **apart** (undecided)
- `vet|vete|vette|vète` /vEt/ (parts vette; new conflict freq 0.0): **apart** (undecided)
- `ger|gger|ggeur|gueur` /g9R/ (parts gueur, gger; new conflict freq 0.0): **apart** (undecided)
- `vier|viers|viller|vié` /vje/ (parts vier; new conflict freq 0.0): **apart** (undecided)
- `chro|craw|cro` /kRo/ (parts cro, chro; new conflict freq 0.0): **apart** (undecided)
- `soir|soire` /zwaR/ (parts soir; new conflict freq 0.0): **apart** (undecided)
- `cive|sive|ssive` /siv/ (parts sive; new conflict freq 0.0): **apart** (undecided)
- `raine|ren|renne|rennes|rraine|rène` /REn/ (parts rène; new conflict freq 0.1): **apart** (undecided)
- `dar|dard|ddar` /daR/ (parts dard; new conflict freq 0.0): **apart** (undecided)
- `pate|pathe|patte` /pat/ (parts pathe; new conflict freq 0.0): **apart** (undecided)
- `nance|nances|nence|nnance` /n@s/ (parts nance, nence; new conflict freq 0.0): **apart** (undecided)
- `bré|brée` /bRe/ (parts bré; new conflict freq 0.0): **apart** (undecided)
- `bour|bourg|bours` /buR/ (parts bour; new conflict freq 0.0): **apart** (undecided)
- `nim|nime|nyme` /nim/ (parts nyme; new conflict freq 0.0): **apart** (undecided)
- `gom|gon` /g§/ (parts gon; new conflict freq 0.0): **apart** (undecided)
- `vie|viei` /vjE/ (parts viei; new conflict freq 0.0): **apart** (undecided)
- `frai|fraî|fré|phré` /fRe/ (parts fré; new conflict freq 0.0): **apart** (undecided)
- `cure|qûre` /kyR/ (parts cure; new conflict freq 0.0): **apart** (undecided)
- `gaie|gais|gay|guais|guet` /gE/ (parts guet; new conflict freq 0.0): **apart** (undecided)
- `nin|nnain|nnin` /n5/ (parts nin; new conflict freq 0.0): **apart** (undecided)
- `bric|brique` /bRik/ (parts brique; new conflict freq 0.0): **apart** (undecided)
- `grim|grin` /gR5/ (parts grim, grin; new conflict freq 0.0): **apart** (undecided)
- `taise|thès|thèse|tès|tèse` /tEz/ (parts thèse; new conflict freq 0.0): **apart** (undecided)
- `lable|llable` /labl/ (parts lable; new conflict freq 0.0): **apart** (undecided)
- `caud|cco|cho|cko|co|cquot|kgo|ko|qu'au|quo` /ko/ (parts co, ko; new conflict freq 0.1): **apart** (undecided)
- `rrure|rure` /RyR/ (parts rrure, rure; new conflict freq 0.0): **apart** (undecided)
- `resse|rès` /REs/ (parts resse; new conflict freq 0.0): **apart** (undecided)
- `ffin|ffine|fine|phine` /fin/ (parts phine; new conflict freq 0.0): **apart** (undecided)
- `iste|ïste` /ist/ (parts ïste, iste; new conflict freq 0.0): **apart** (undecided)
- `hon|om|on|un` /§/ (parts on, om; new conflict freq 0.0): **apart** (undecided)
- `teux|theux|tteux` /t2/ (parts teux, tteux; new conflict freq 0.0): **apart** (undecided)
- `cha|chas|chat|sha|shad` /Sa/ (parts chat; new conflict freq 0.0): **apart** (undecided)
- `rien|rrien|ryen` /Rj5/ (parts rien; new conflict freq 0.0): **apart** (undecided)
- `foi|foua` /fwa/ (parts foi; new conflict freq 0.0): **apart** (undecided)
- `chlée|cler` /kle/ (parts cler; new conflict freq 0.0): **apart** (undecided)
- `mel|melle|mmel` /mEl/ (parts melle, mel; new conflict freq 0.0): **apart** (undecided)
- `spea|spee|spi` /spi/ (parts spi; new conflict freq 0.0): **apart** (undecided)
- `enne|ène` /En/ (parts enne, ène; new conflict freq 0.0): **apart** (undecided)
- `hos|os` /Os/ (parts hos, os; new conflict freq 0.0): **apart** (undecided)
- `cker|ckeur|coeur|ker|kkeur|queur` /k9R/ (parts queur, ker, cker; new conflict freq 0.4): **apart** (undecided)
- `ban|bant|ben` /b@/ (parts ban, bant; new conflict freq 0.0): **apart** (undecided)
- `ccage|ckage|quage` /kaZ/ (parts quage; new conflict freq 0.0): **apart** (undecided)
- `ger|jer` /ZER/ (parts ger; new conflict freq 0.0): **apart** (undecided)
- `chris|christ|cris` /kRis/ (parts cris; new conflict freq 0.0): **apart** (undecided)
- `ril|rile|ryl` /Ril/ (parts ril; new conflict freq 0.0): **apart** (undecided)
- `bro|brow` /bRo/ (parts bro; new conflict freq 0.0): **apart** (undecided)
- `xion|xtion` /ksj§/ (parts xion; new conflict freq 0.0): **apart** (undecided)
- `ffler|fler|flée` /fle/ (parts fler; new conflict freq 0.0): **apart** (undecided)
- `fflé|flé` /fle/ (parts flé; new conflict freq 0.0): **apart** (undecided)
- `per|peur|pper|ppeur` /p9R/ (parts peur, per, ppeur, pper; new conflict freq 0.0): **apart** (undecided)
- `thisme|thysme|tisme|ttisme` /tizm/ (parts tisme; new conflict freq 0.0): **apart** (undecided)
- `mick|mics|mique` /mik/ (parts mique; new conflict freq 0.7): **apart** (undecided)
- `can|cant|kan|quant|quent` /k@/ (parts quant, quent, can, cant; new conflict freq 0.0): **apart** (undecided)
- `puce|pus` /pys/ (parts pus; new conflict freq 0.0): **apart** (undecided)
- `spa|spah` /spa/ (parts spa; new conflict freq 0.0): **apart** (undecided)
- `rice|ris|risse|rrice` /Ris/ (parts ris; new conflict freq 0.0): **apart** (undecided)
- `nnoir|noir|noire` /nwaR/ (parts noir; new conflict freq 0.0): **apart** (undecided)
- `maire|mer|mere|mmaire|mmère|mère` /mER/ (parts maire, mère; new conflict freq 0.0): **apart** (undecided)
- `chère|sher` /SER/ (parts chère; new conflict freq 0.0): **apart** (undecided)
- `gi|gy|gî|ji` /Zi/ (parts gi, gy; new conflict freq 0.0): **apart** (undecided)
- `cif|scif|sif|ssif` /sif/ (parts ssif, sif, cif; new conflict freq 0.0): **apart** (undecided)
- `cail|caille|quaille` /kaj/ (parts caille; new conflict freq 0.0): **apart** (undecided)
- `ping|pping` /piG/ (parts ping; new conflict freq 0.0): **apart** (undecided)
- `ste|sté` /ste/ (parts sté; new conflict freq 0.0): **apart** (undecided)
- `ine|ïne` /in/ (parts ïne, ine; new conflict freq 0.0): **apart** (undecided)
- `jou|joue` /Zu/ (parts jou; new conflict freq 0.0): **apart** (undecided)
- `som|son` /s§/ (parts son; new conflict freq 0.0): **apart** (undecided)
- `omme|um` /Om/ (parts um; new conflict freq 0.0): **apart** (undecided)
- `val|vol|vole` /vOl/ (parts val; new conflict freq 0.0): **apart** (undecided)
- `loo|lou|loue` /lu/ (parts lou; new conflict freq 0.0): **apart** (undecided)
- `chlo|clau|clo|clô` /klo/ (parts clo, chlo; new conflict freq 0.0): **apart** (undecided)
- `sière|zière` /zjER/ (parts sière; new conflict freq 0.0): **apart** (undecided)
- `cheur|sheur` /S9R/ (parts cheur; new conflict freq 0.0): **apart** (undecided)
- `ffian|fiant` /fj@/ (parts fiant; new conflict freq 0.0): **apart** (undecided)
- `illère|ière|llière|llère|yère` /jER/ (parts illère, ière; new conflict freq 0.0): **apart** (undecided)
- `dace|das|dasse` /das/ (parts dasse; new conflict freq 0.0): **apart** (undecided)
- `gan|gand|gant|ggan|ghan|guent` /g@/ (parts gant, gan; new conflict freq 0.0): **apart** (undecided)
- `pli|plii` /plij/ (parts pli; new conflict freq 0.0): **apart** (undecided)
- `tesque|ttesque` /tEsk/ (parts tesque; new conflict freq 0.0): **apart** (undecided)
- `mur|mure` /myR/ (parts mure; new conflict freq 0.0): **apart** (undecided)
- `a|at|â` /a/ (parts a; new conflict freq 0.0): **apart** (undecided)
- `ffrer|ffré|frer|fré|phré` /fRe/ (parts ffrer; new conflict freq 0.2): **apart** (undecided)
- `fage|ffage|phage` /faZ/ (parts ffage, phage; new conflict freq 0.0): **apart** (undecided)
- `lisme|llisme` /lizm/ (parts lisme; new conflict freq 0.0): **apart** (undecided)
- `nisme|nnisme` /nizm/ (parts nisme, nnisme; new conflict freq 0.0): **apart** (undecided)
- `geur|jeur` /Z9R/ (parts geur; new conflict freq 0.0): **apart** (undecided)
- `neu|neux|nneux` /n2/ (parts neux, nneux; new conflict freq 0.0): **apart** (undecided)
- `dol|dole` /dOl/ (parts dole; new conflict freq 0.0): **apart** (undecided)
- `cquier|kier|quier` /kje/ (parts quier; new conflict freq 0.0): **apart** (undecided)
- `glau|glo` /glo/ (parts glo; new conflict freq 0.0): **apart** (undecided)
- `drai|dre|drey` /dRE/ (parts dre; new conflict freq 0.0): **apart** (undecided)
- `cade|ccade|quade` /kad/ (parts cade; new conflict freq 0.0): **apart** (undecided)
- `geois|joie` /Zwa/ (parts geois; new conflict freq 0.0): **apart** (undecided)
- `ning|nning` /niG/ (parts ning; new conflict freq 0.0): **apart** (undecided)
- `mas|masse` /mas/ (parts mas; new conflict freq 0.0): **apart** (undecided)
- `flé|phlé` /fle/ (parts flé; new conflict freq 0.0): **apart** (undecided)
- `ser|seur|zer|zeur` /z9R/ (parts seur, ser; new conflict freq 0.0): **apart** (undecided)
- `bla|blâ` /bla/ (parts bla; new conflict freq 0.0): **apart** (undecided)
- `rat|rate|ratte` /Rat/ (parts rate; new conflict freq 0.0): **apart** (undecided)
- `if|ïf` /if/ (parts if; new conflict freq 0.0): **apart** (undecided)
- `char|chard|chards|chart` /SaR/ (parts chard; new conflict freq 0.0): **apart** (undecided)
- `dair|daire|der|dère` /dER/ (parts daire, dère; new conflict freq 0.0): **apart** (undecided)
- `fo|pho` /fO/ (parts fo, pho; new conflict freq 0.0): **apart** (undecided)
- `va|vas|vat|vats` /va/ (parts va; new conflict freq 0.1): **apart** (undecided)
- `ia|illat|lla|llat|ya|yat|ïa` /ja/ (parts ya, lla; new conflict freq 0.3): **apart** (undecided)
- `fla|flah|flâ` /fla/ (parts fla, flâ; new conflict freq 0.0): **apart** (undecided)
- `nase|naze` /naz/ (parts nase; new conflict freq 0.0): **apart** (undecided)
- `lim|lin|lym|lyn` /l5/ (parts lin, lym; new conflict freq 0.0): **apart** (undecided)
- `grou|gru` /gRu/ (parts grou; new conflict freq 0.0): **apart** (undecided)
- `ves|wes` /vEs/ (parts ves; new conflict freq 0.0): **apart** (undecided)
- `rhomme|rum` /ROm/ (parts rum; new conflict freq 0.0): **apart** (undecided)
- `rium|ryum` /RjOm/ (parts rium; new conflict freq 0.0): **apart** (undecided)
- `pe|peu` /p2/ (parts pe, peu; new conflict freq 0.0): **apart** (undecided)
- `chiste|chyste|sciste` /Sist/ (parts chiste; new conflict freq 0.0): **apart** (undecided)
- `ciste|siste|ssiste` /sist/ (parts ciste, ssiste; new conflict freq 0.0): **apart** (undecided)
- `ec|ek|hec` /Ek/ (parts ec; new conflict freq 0.0): **apart** (undecided)
- `dic|dik` /dik/ (parts dic; new conflict freq 0.1): **apart** (undecided)
- `daient|dais|dait|det` /dE/ (parts dais, det; new conflict freq 0.0): **apart** (undecided)
- `sol|sole|ssole` /sOl/ (parts sol; new conflict freq 0.0): **apart** (undecided)
- `beur|beurre` /b9R/ (parts beur; new conflict freq 0.0): **apart** (undecided)
- `naise|nnaise|nèse` /nEz/ (parts nèse; new conflict freq 0.0): **apart** (undecided)
- `rou|rrou|rroux` /Ru/ (parts rou; new conflict freq 0.0): **apart** (undecided)
- `gau|go` /go/ (parts go, gau; new conflict freq 0.0): **apart** (undecided)
- `git|gite|gitent|gites` /Zit/ (parts gite; new conflict freq 0.0): **apart** (undecided)
- `ting|tting` /tiG/ (parts ting; new conflict freq 0.0): **apart** (undecided)
- `diaire|dière` /djER/ (parts dière; new conflict freq 0.0): **apart** (undecided)
- `tille|ttille` /tij/ (parts tille; new conflict freq 0.0): **apart** (undecided)
- `er|eur` /9R/ (parts eur; new conflict freq 0.0): **apart** (undecided)
- `trage|ttrage` /tRaZ/ (parts trage; new conflict freq 0.0): **apart** (undecided)
- `cot|cote|cott|cotte` /kOt/ (parts cotte; new conflict freq 0.0): **apart** (undecided)
- `ique|ïk|ïque` /ik/ (parts ïque, ique; new conflict freq 0.0): **apart** (undecided)
- `chou|schoo|shoo` /Su/ (parts chou; new conflict freq 0.0): **apart** (undecided)
- `ote|otte` /Ot/ (parts ote; new conflict freq 0.0): **apart** (undecided)
- `hyp|ip` /ip/ (parts hyp; new conflict freq 0.0): **apart** (undecided)
- `ger|gère` /ZER/ (parts gère; new conflict freq 0.0): **apart** (undecided)
- `cène|scène|sen` /sEn/ (parts cène; new conflict freq 0.0): **apart** (undecided)
- `lluche|luche` /lyS/ (parts luche; new conflict freq 0.0): **apart** (undecided)
- `drer|dré|drée` /dRe/ (parts drer, dré; new conflict freq 0.2): **apart** (undecided)
- `io|yo` /jo/ (parts io; new conflict freq 0.0): **apart** (undecided)
- `bais|bet` /bE/ (parts bet; new conflict freq 0.0): **apart** (undecided)
- `bar|bard|bare|bart` /baR/ (parts bard, bar; new conflict freq 0.0): **apart** (undecided)
- `plan|plant` /pl@/ (parts plan; new conflict freq 0.0): **apart** (undecided)
- `thus|tuce|tus` /tys/ (parts tus; new conflict freq 0.0): **apart** (undecided)
- `gas|gaz` /gas/ (parts gas; new conflict freq 0.2): **apart** (undecided)
- `pice|pis` /pis/ (parts pice; new conflict freq 0.0): **apart** (undecided)
- `dine|dines` /din/ (parts dine; new conflict freq 0.0): **apart** (undecided)
- `train|trim|trin` /tR5/ (parts trin; new conflict freq 0.0): **apart** (undecided)
- `gran|grand|grant` /gR@/ (parts grant; new conflict freq 0.0): **apart** (undecided)
- `roi|roie|rois|roît|rroi|rroie|rrois` /Rwa/ (parts rois; new conflict freq 0.0): **apart** (undecided)
- `tho|to` /tO/ (parts to; new conflict freq 0.0): **apart** (undecided)
- `bal|bale|ball|balle` /bal/ (parts bal; new conflict freq 0.0): **apart** (undecided)
- `nate|nates|nathe|nnate` /nat/ (parts nate; new conflict freq 0.0): **apart** (undecided)
- `dou|doub|doue|doux` /du/ (parts dou; new conflict freq 0.0): **apart** (undecided)
- `bul|bule` /byl/ (parts bule; new conflict freq 0.0): **apart** (undecided)
- `me|meu` /m2/ (parts meu; new conflict freq 0.0): **apart** (undecided)
- `hia|hya|ya` /ja/ (parts ya; new conflict freq 0.0): **apart** (undecided)
- `air|aire|er|her` /ER/ (parts her, er; new conflict freq 0.0): **apart** (undecided)
- `cause|chose|cose|khoze|kose` /koz/ (parts cose; new conflict freq 0.0): **apart** (undecided)
- `ffrage|frage` /fRaZ/ (parts ffrage; new conflict freq 0.0): **apart** (undecided)
- `gu|gus|guë` /gy/ (parts gu; new conflict freq 0.0): **apart** (undecided)
- `zi|zy` /zi/ (parts zi, zy; new conflict freq 0.0): **apart** (undecided)
- `flam|flan` /fl@/ (parts flam, flan; new conflict freq 0.0): **apart** (undecided)
- `d'homme|dom|dome|dum` /dOm/ (parts dum; new conflict freq 0.0): **apart** (undecided)
- `lor|lord|lore` /lOR/ (parts lore; new conflict freq 0.0): **apart** (undecided)
- `isme|ïsme` /izm/ (parts ïsme, isme; new conflict freq 0.0): **apart** (undecided)
- `hié|yé` /je/ (parts hié; new conflict freq 0.0): **apart** (undecided)
- `be|beu` /b2/ (parts be; new conflict freq 0.0): **apart** (undecided)
- `boos|bous` /bus/ (parts bous; new conflict freq 0.0): **apart** (undecided)
- `llose|lose` /loz/ (parts lose; new conflict freq 0.0): **apart** (undecided)
- `thore|tor|tore|tors` /tOR/ (parts tor; new conflict freq 0.0): **apart** (undecided)
- `clou|cloue|clow` /klu/ (parts clou; new conflict freq 0.0): **apart** (undecided)
- `daine|den|dène` /dEn/ (parts den; new conflict freq 0.0): **apart** (undecided)
- `chisme|scisme` /Sizm/ (parts chisme; new conflict freq 0.0): **apart** (undecided)
- `ccio|cho` /tSo/ (parts cho; new conflict freq 0.0): **apart** (undecided)
- `set|sette|zette` /zEt/ (parts sette; new conflict freq 0.0): **apart** (undecided)
- `seux|zeux` /z2/ (parts seux; new conflict freq 0.0): **apart** (undecided)
- `geat|ja|jah|jat` /Za/ (parts ja; new conflict freq 0.0): **apart** (undecided)
- `bette|bète|bête` /bEt/ (parts bette; new conflict freq 0.0): **apart** (undecided)
- `ar|ard` /aR/ (parts ard; new conflict freq 0.0): **apart** (undecided)
- `cya|scia|scie|sia` /sja/ (parts cya; new conflict freq 0.0): **apart** (undecided)
- `ce|cher|tcher` /tSe/ (parts ce, tcher; new conflict freq 0.0): **apart** (undecided)
- `ide|ides|yde|ïd|ïde` /id/ (parts ïde, ïd; new conflict freq 0.0): **apart** (undecided)
- `tein|tim|tym` /t5/ (parts tein, tim; new conflict freq 0.0): **apart** (undecided)
- `pit|pite|pitent|pites` /pit/ (parts pite, pitent, pites; new conflict freq 0.0): **apart** (undecided)
- `cisme|sisme|ssisme` /sizm/ (parts cisme; new conflict freq 0.0): **apart** (undecided)
- `hui|huî` /8i/ (parts hui; new conflict freq 0.0): **apart** (undecided)
- `piste|ppiste` /pist/ (parts piste; new conflict freq 0.0): **apart** (undecided)
- `tit|tite|ttite` /tit/ (parts tite; new conflict freq 0.0): **apart** (undecided)
- `cai|ché|ke|kei|khé|ké|que|qué` /ke/ (parts ké; new conflict freq 0.0): **apart** (undecided)
- `quim|quin` /k5/ (parts quin; new conflict freq 0.0): **apart** (undecided)
- `rhin|rhyn|rim|rin` /R5/ (parts rin; new conflict freq 0.0): **apart** (undecided)
- `ddhiste|diste` /dist/ (parts diste; new conflict freq 0.0): **apart** (undecided)
- `ien|yen|yin|ïen` /j5/ (parts ïen, ien; new conflict freq 0.0): **apart** (undecided)
- `chu|schu` /Sy/ (parts chu; new conflict freq 0.0): **apart** (undecided)
- `chage|shage` /SaZ/ (parts chage; new conflict freq 0.0): **apart** (undecided)
- `ad|ade` /ad/ (parts ade; new conflict freq 0.0): **apart** (undecided)
- `ponc|punc` /p§k/ (parts ponc; new conflict freq 0.0): **apart** (undecided)
- `ciable|tiable` /sjabl/ (parts ciable; new conflict freq 0.0): **apart** (undecided)
- `thrite|trite` /tRit/ (parts trite; new conflict freq 0.0): **apart** (undecided)
- `tiche|tish|ttish` /tiS/ (parts tiche; new conflict freq 0.0): **apart** (undecided)
- `gam|gan` /g@/ (parts gan, gam; new conflict freq 0.0): **apart** (undecided)
- `ling|lling` /liG/ (parts ling; new conflict freq 0.0): **apart** (undecided)
- `nome|nôme` /nom/ (parts nome; new conflict freq 0.0): **apart** (undecided)
- `ride|rides|rride` /Rid/ (parts ride; new conflict freq 0.0): **apart** (undecided)
- `tane|thane|ttan` /tan/ (parts tane, thane; new conflict freq 0.0): **apart** (undecided)
- `meu|mu` /m9/ (parts meu; new conflict freq 0.0): **apart** (undecided)
- `mac|mak|maque` /mak/ (parts mac; new conflict freq 0.0): **apart** (undecided)
- `rienne|ryenne` /RjEn/ (parts rienne; new conflict freq 0.0): **apart** (undecided)
- `bleu|bleux` /bl2/ (parts bleu; new conflict freq 0.0): **apart** (undecided)
- `liaire|lière|lliaire|llière` /ljER/ (parts lière; new conflict freq 0.0): **apart** (undecided)
- `hour|our` /uR/ (parts our; new conflict freq 0.0): **apart** (undecided)
- `door|dor|dore` /dOR/ (parts dor; new conflict freq 0.0): **apart** (undecided)
- `bleu|blu` /bl9/ (parts bleu; new conflict freq 0.0): **apart** (undecided)
- `resque|rresque` /REsk/ (parts resque; new conflict freq 0.0): **apart** (undecided)
- `can|cane` /kan/ (parts cane; new conflict freq 0.0): **apart** (undecided)
- `tam|tame|thame|tâmes` /tam/ (parts tâmes; new conflict freq 0.0): **apart** (undecided)
- `sien|zien` /zj5/ (parts sien; new conflict freq 0.0): **apart** (undecided)
- `ccus|cus` /kys/ (parts cus; new conflict freq 0.0): **apart** (undecided)
- `gre|gré|grée|grê` /gRe/ (parts gré; new conflict freq 0.0): **apart** (undecided)
- `geau|geaud|geot|jo` /Zo/ (parts jo; new conflict freq 0.0): **apart** (undecided)
- `sar|sard|ssar|ssard|ssart|çard` /saR/ (parts ssard; new conflict freq 0.0): **apart** (undecided)
- `val|wal` /val/ (parts val; new conflict freq 0.0): **apart** (undecided)
- `paul|pole` /pOl/ (parts pole; new conflict freq 0.0): **apart** (undecided)
- `toche|tosh` /tOS/ (parts toche; new conflict freq 0.0): **apart** (undecided)
- `tom|tum` /tOm/ (parts tum; new conflict freq 0.0): **apart** (undecided)
- `bic|bique` /bik/ (parts bique; new conflict freq 0.0): **apart** (undecided)
- `fal|fale|phal|phale` /fal/ (parts phale; new conflict freq 0.0): **apart** (undecided)
- `pac|pack` /pak/ (parts pac; new conflict freq 0.0): **apart** (undecided)
- `thol|tol|tole|toll` /tOl/ (parts tole; new conflict freq 0.0): **apart** (undecided)
- `grai|gre|grè|grê` /gRE/ (parts grai; new conflict freq 0.0): **apart** (undecided)
- `gus|gusse` /gys/ (parts gus; new conflict freq 0.0): **apart** (undecided)
- `mo|moh|moo` /mO/ (parts mo; new conflict freq 0.0): **apart** (undecided)
- `lloc|lloque|loch|lock|locks|loque` /lOk/ (parts loque; new conflict freq 0.0): **apart** (undecided)
- `ol|ole` /Ol/ (parts ole; new conflict freq 0.0): **apart** (undecided)
- `cryp|kryp` /kRip/ (parts cryp; new conflict freq 0.0): **apart** (undecided)
- `gette|gète|jette` /ZEt/ (parts gette; new conflict freq 0.0): **apart** (undecided)
- `flai|fle` /flE/ (parts fle; new conflict freq 0.0): **apart** (undecided)
- `rose|rrhose` /Roz/ (parts rose; new conflict freq 0.0): **apart** (undecided)
- `lium|llium` /ljOm/ (parts lium, llium; new conflict freq 0.0): **apart** (undecided)
- `fai|fe|feu` /f2/ (parts feu; new conflict freq 0.0): **apart** (undecided)
- `gneu|gneux|nieux` /N2/ (parts gneux; new conflict freq 0.0): **apart** (undecided)
- `tal|thal` /tal/ (parts tal; new conflict freq 0.0): **apart** (undecided)
- `treur|ttreur` /tR9R/ (parts treur; new conflict freq 0.0): **apart** (undecided)
- `fiste|phiste` /fist/ (parts phiste; new conflict freq 0.0): **apart** (undecided)
- `fane|phane` /fan/ (parts phane; new conflict freq 0.0): **apart** (undecided)
- `rho|rhu|ro` /RO/ (parts ro; new conflict freq 0.0): **apart** (undecided)
- `labe|llabe` /lab/ (parts llabe; new conflict freq 0.0): **apart** (undecided)
- `croo|crou|croû|cru|crui|krou` /kRu/ (parts crou; new conflict freq 0.0): **apart** (undecided)
- `ddite|dit|dite|ditent|dites|dith|dyte` /dit/ (parts dite, dites, ditent; new conflict freq 0.0): **apart** (undecided)
- `llus|lus` /lys/ (parts lus; new conflict freq 0.0): **apart** (undecided)
- `nim|nym` /n5/ (parts nym, nim; new conflict freq 0.0): **apart** (undecided)
- `fein|fin` /f5/ (parts fin; new conflict freq 0.0): **apart** (undecided)
- `dienne|diène` /djEn/ (parts dienne; new conflict freq 0.0): **apart** (undecided)
- `miau|myo` /mjo/ (parts myo; new conflict freq 0.0): **apart** (undecided)
- `tose|tôse` /toz/ (parts tose; new conflict freq 0.0): **apart** (undecided)
- `sal|sales|zal` /zal/ (parts sal; new conflict freq 0.0): **apart** (undecided)
- `late|llat` /lat/ (parts late; new conflict freq 0.0): **apart** (undecided)
- `pic|pick` /pik/ (parts pic; new conflict freq 0.0): **apart** (undecided)
- `guim|guin` /g5/ (parts guin; new conflict freq 0.0): **apart** (undecided)
- `flu|flû` /fly/ (parts flu; new conflict freq 0.0): **apart** (undecided)
- `bage|bages` /baZ/ (parts bage; new conflict freq 0.0): **apart** (undecided)
- `pien|piens` /pj5/ (parts pien; new conflict freq 0.0): **apart** (undecided)
- `bran|brant` /bR@/ (parts brant; new conflict freq 0.0): **apart** (undecided)
- `fiable|phiable` /fjabl/ (parts fiable; new conflict freq 0.0): **apart** (undecided)
- `beu|bu` /b9/ (parts beu; new conflict freq 0.0): **apart** (undecided)
- `cur|kur` /kyR/ (parts cur; new conflict freq 0.0): **apart** (undecided)
- `gam|game` /gam/ (parts game; new conflict freq 0.0): **apart** (undecided)
- `amb|emb` /@b/ (parts amb, emb; new conflict freq 0.0): **apart** (undecided)
- `llâtre|lâtre` /latR/ (parts lâtre; new conflict freq 0.0): **apart** (undecided)
- `nia|nnia` /nja/ (parts nia; new conflict freq 0.0): **apart** (undecided)
- `ben|bim` /b5/ (parts ben; new conflict freq 0.0): **apart** (undecided)
- `goi|goua|gua` /gwa/ (parts gua, goua; new conflict freq 0.0): **apart** (undecided)
- `ddhisme|disme|dysme` /dizm/ (parts disme; new conflict freq 0.0): **apart** (undecided)
- `chro|cro` /kRO/ (parts cro; new conflict freq 0.0): **apart** (undecided)
- `stri|strie` /stRi/ (parts stri; new conflict freq 0.0): **apart** (undecided)
- `ssim|ssime|zim` /sim/ (parts ssime; new conflict freq 0.0): **apart** (undecided)
- `cienne|sienne|ssienne|tienne` /sjEn/ (parts cienne; new conflict freq 0.0): **apart** (undecided)
- `lesque|llesque` /lEsk/ (parts lesque; new conflict freq 0.0): **apart** (undecided)
- `fisme|phisme` /fizm/ (parts phisme; new conflict freq 0.0): **apart** (undecided)
- `nol|nole` /nOl/ (parts nol; new conflict freq 0.0): **apart** (undecided)
- `cau|cho|coh|ko|quo` /kO/ (parts cho, ko; new conflict freq 0.0): **apart** (undecided)
- `pli|plie` /pli/ (parts pli; new conflict freq 0.0): **apart** (undecided)
- `lloche|loche` /lOS/ (parts loche; new conflict freq 0.0): **apart** (undecided)
- `llum|lom|lome|lum` /lOm/ (parts lum; new conflict freq 0.0): **apart** (undecided)
- `trisme|ttrisme` /tRizm/ (parts trisme; new conflict freq 0.0): **apart** (undecided)
- `ienne|yenne` /jEn/ (parts ienne; new conflict freq 0.0): **apart** (undecided)
- `bbeux|beu|beux` /b2/ (parts beux; new conflict freq 0.0): **apart** (undecided)
- `bbleur|bleur` /bl9R/ (parts bleur; new conflict freq 0.0): **apart** (undecided)
- `hin|in` /in/ (parts in; new conflict freq 0.0): **apart** (undecided)
- `thisme|tisme` /tism/ (parts tisme; new conflict freq 0.0): **apart** (undecided)
- `nisme|nnisme` /nism/ (parts nisme; new conflict freq 0.0): **apart** (undecided)
- `el|hel` /El/ (parts hel; new conflict freq 0.0): **apart** (undecided)
- `neuse|nneuse` /n2z/ (parts neuse; new conflict freq 0.0): **apart** (undecided)
- `a|ah|ha|hâ|â` /a/ (parts a, ah, ha, hâ, â; new conflict freq 7.6): **fused**

## Decided merges that are no longer in the pool (lexicon change?)

- none

## Overlaps among selected rules (must all be < 0.5)

- ter ~ té: 0.09

## Overlap skips during selection (0)

- none
