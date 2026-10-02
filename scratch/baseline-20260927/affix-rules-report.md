# Affix rules (Phase 3 + 4 result, DESIGN_2026-09-27-affix-rule-selection.md)

Constants: RULE_BUDGET=30, MAX_RULE_FORMS=4, EXCEPTION_ALPHA=1.0, EXCLUSION_COST=5.0, FORM_COST=10.0, SWAP_CANDIDATES=20, SWAP_PASSES=3.

Note: bare verb-infinitive-ending candidates (isVerbEndingFragment) were left UNFILTERED in this run, per the user's 2026-09-27 decision to let them compete on score through Phase 3/4 instead of being cut upstream.

## Savings curve (cumulative total after each acceptance, 1..40)

8176, 14079, 18544, 22863, 26960, 30347, 33863, 36900, 39295, 41640, 43820, 45921, 47897, 49846, 51823, 53848, 55632, 57341, 59116, 60766, 62360, 63875, 65408, 66642, 67845, 69089, 70238, 71428, 72663, 73765

## 1. suffix `ment` -- keys (20, 25) = `-tm`

forms: `ment`(k=1), `·[be|ble|bre|ca|che|chi|cie|claffe|cle|cre|cré|cu|cé|de|di|die|dre|du|dé|dû|ffle|ffre|fie|fle|ge|gi|gle|gne|gre|gré|gu|gue|ille|le|li|lle|lu|lé|lû|ma|me|mmé|mé|ne|ni|nie|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|rre|rré|ré|se|ssuie|ssé|sé|ta|te|tie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|é]-{s°,ti}ment`(k=2), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|xa|za|ça]blement`(k=3), `·[ai|bai|chai|chaî|chè|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|miè|mmai|mè|mê|nai|niai|niè|nnai|nnê|plai|plè|prê|què|rai|re|rrai|rè|sai|scè|sei|siè|ssai|ssiè|strai|sè|tai|te|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3)
- score 8176.3, strokeFreqSaved 8226.6, keySimilarity 0.39 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 0.2)
- top exceptions: richement, blèsement
    seulement: s@/mt@a/m@ -> s@tm
    tellement: tie/mt@a/m@ -> tietm
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/aktm
    sûrement: s@i/R@a/m@ -> s@itm
    complètement: kai/pmtie/t@a/m@ -> kaitm
    doucement: pv@e/s@a/m@ -> pv@e/s@atm

## 2. suffix `·°ment` -- keys (19, 20) = `-dt`

forms: `·°ment`(k=2), `·[ai|bai|chai|chaî|chè|cie|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|me|miè|mmai|mè|mê|nai|ne|niai|niè|nnai|nne|nnê|plai|plè|prê|què|rai|re|rei|rie|rrai|rè|sai|scè|se|sei|siè|ssai|ssiè|strai|sè|tai|te|tie|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|xa|za|ça]blement`(k=3), `·[bi|bli|bri|chi|ci|cri|di|dri|fi|gi|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|pli|qui|ri|rri|sci|si|ssi|thi|ti|tri|tti|vi|vri|xi|y|ï]lement`(k=3)
- score 6880.9, strokeFreqSaved 7040.5, keySimilarity 0.06 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 33 (freq 119.5)
- top exceptions: simplement, renseignements, renseignement, hautement, classement, remplacement, ravissement, rendement, rangement, claquement
    seulement: s@/mt@a/m@ -> s@dt
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/akdt
    complètement: kai/pmtie/t@a/m@ -> kaidt
    doucement: pv@e/s@a/m@ -> pv@edt
    appartement: a/paR/t@a/m@ -> a/padtR

## 3. prefix `re` -- keys (19,) = `-d`

forms: `re`(k=1), `re[char|gar|mar|par|tar]·`(k=2), `re[bro|chau|co|do|fau|lo|mo|no|po|pro|vau|vo]·`(k=2), `re[bou|cou|dou|fou|grou|joue|loo|loue|mou|nou|pou|tou|trou|vou]·`(k=2)
- score 5902.7, strokeFreqSaved 6151.0, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 176 (freq 218.3)
- top exceptions: regardes, rejoindre, reprendre, regardent, record, repousse, recours, revendre, records, repaire
    revoir: R@a/vwaR -> vwadR
    regardez: R@a/ksaR/pve/-k -> pved/-k
    reviens: R@a/vRwaie/-k -> vRwaied/-k
    regarder: R@a/ksaR/pve/-l -> pved/-l
    retour: R@a/t@eR -> t@edR
    retard: R@a/taR -> tadR

## 4. suffix `tion` -- keys (19, 20, 22) = `-dtn`

forms: `tion`(k=1), `·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tion`(k=2), `·[sten|ten|tten|ven]tion`(k=2), `·[bi|ci|ddi|di|gni|li|mi|ni|ri|si|sti|ti|tri]tion`(k=2)
- score 4465.1, strokeFreqSaved 4495.1, keySimilarity 0.07 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    attention: a/t@/sRwai -> atm
    attention: a/t@/sRwai -> atm
    situation: si/t@a/sRwai -> si/t@atm
    solution: sae/mt@i/sRwai -> sae/mt@itm
    position: pae/twi/sRwai -> paetm
    opération: ae/pe/Ra/sRwai -> ae/petm

## 5. prefix `de` -- keys (17, 18) = `-sk`

forms: `de`(k=1), `de[ba|man|ve|vi|vien|vri]·`(k=2)
- score 4318.7, strokeFreqSaved 4328.7, keySimilarity -0.26 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    demain: pv@a/maie -> maiesk
    demande: pv@a/m@d -> m@skd
    devrais: pv@a/vRie/-k -> vRiesk/-k
    demandé: pv@a/m@/pve -> pvesk
    devrait: pv@a/vRie -> vRiesk
    demander: pv@a/m@/pve/-l -> pvesk/-l

## 6. prefix `a` -- keys (18, 19) = `-kd`

forms: `a`(k=1), `a[che|ge|me|pe|ve]·`(k=2), `a[mu|pu]·`(k=2), `a[ba|bâ|ca|cha|droi|ma|na|pâ|ra|sa|ta|va|voi]·`(k=2)
- score 4097.2, strokeFreqSaved 4154.2, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 50 (freq 27.0)
- top exceptions: amende, avère, avide, aborde, avides, aride, amandes, amande, amendes, agrippe
    avais: a/vie/-d -> viekd/-d
    avais: a/vie/-k -> viekd/-k
    avons: a/vai -> vaikd
    amis: a/mi/-s -> mikd/-s
    avons: a/vai -> vaikd
    avis: a/vi -> vikd

## 7. prefix `en` -- keys (18, 22) = `-kn`

forms: `en`(k=1), `en[a|ca|cloî|dia|fa|fla|foi|ga|gra|joi|la|ra|sa|ta|toi|tra|va]·`(k=2), `en[che|ge|gre|le|re|se]·`(k=2), `en[cen|chan|clen|gen|glan|gran|jam|san|vian]-{t}·`(k=2)
- score 3515.7, strokeFreqSaved 3588.1, keySimilarity -0.39 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 85 (freq 37.4)
- top exceptions: entraîne, enferme, enflamme, entraînes, entracte, entraînent, endorme, enfermes, endorment, enchaîne
    enfin: @/kpaie -> kpaiekn
    entendu: @/t@/pv@i -> t@kn/pv@i
    envie: @/vi -> vikn
    endroit: @/pvRwa -> pvRwakn
    entends: @/t@/-k -> t@kn/-k
    entendre: @/t@dR -> t@kdRn

## 8. suffix `ter` -- keys (19, 20, 25) = `-dtm`

forms: `ter`(k=1), `·[crê|nne|pê|rrê|trai]ter`(k=2), `·[bi|ci|cy|di|fi|gi|li|mi|pi|ri|sci|si|ssi|vi|xci]ter`(k=2), `·[an|cen|chan|den|emp|gen|glan|illan|jan|len|man|men|mmen|nen|pen|plan|quen|ren|rien|san|sen|ten|tien|tten|van|ven]ter`(k=2)
- score 3387.0, strokeFreqSaved 3973.6, keySimilarity 0.54
- word exceptions 97 (freq 556.6)
- top exceptions: arrêter, arrêtez, arrêté, éviter, habiter, arrêtée, habitez, arrêtés, contenter, habité
    rester: Ries/te/-l -> Riestm/-l
    acheter: a/pm@a/te/-l -> a/pm@atm/-l
    restez: Ries/te/-k -> Riestm/-k
    écoutez: e/k@e/te/-k -> e/k@etm/-k

## 9. suffix `té` -- keys (19, 22) = `-dn`

forms: `té`(k=1), `·[a|ba|bi|ca|cia|da|dua|dé|ga|gi|gra|ma|na|nna|qui|ra|ri|ria|sa|sua|ta|ti|tia|tra|tua|va|vi|via|xua]-{mi}lité`(k=3), `·rité`(k=2), `·[cu|da|ga|jo|la|lia|no|o|pa|rio|shé|ta|to|té]rité`(k=3)
- score 3266.3, strokeFreqSaved 3308.3, keySimilarity 0.01 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 5 (freq 7.0)
- top exceptions: égalité, liftée, égalités, liftées, lifté
    vérité: ve/Ri/te -> vedn
    sécurité: se/k@i/Ri/te -> sedn
    santé: s@/te -> s@dn
    liberté: mti/svieR/te -> mti/sviedRn
    société: sae/sRwe/te -> sae/sRwedn
    beauté: svae/te -> svaedn

## 10. suffix `der` -- keys (18, 19, 25) = `-kdm`

forms: `der`(k=1), `·[an|ban|chan|en|gen|lan|man|men|mman|pen|san|scen]dé`(k=2), `·[bar|blar|car|char|gar|gnar|lar|llar|mar|mmar|nar|par|sar|tar|ttar|var|zar]dez`(k=2), `·[ci|gui|li|mi|pi|qui|si|xy]dé`(k=2)
- score 2395.2, strokeFreqSaved 2577.4, keySimilarity 0.55
- word exceptions 32 (freq 152.2)
- top exceptions: décidé, décider, décidez, décidée, décidai, élucider, décidés, bondé, élucidé, bondée
    regardez: R@a/ksaR/pve/-k -> R@akdm/-k
    demandé: pv@a/m@/pve -> pv@akdm
    demander: pv@a/m@/pve/-l -> pv@akdm/-l
    regarder: R@a/ksaR/pve/-l -> R@akdm/-l
    garder: ksaR/pve/-l -> ksakdRm/-l

## 11. suffix `ver` -- keys (20, 22) = `-tn`

forms: `ver`(k=1), `·[chi|di|li|qui|ri|rri|ssi|ti|vi]vé`(k=2), `·[che|le]ver`(k=2), `·[ner|nner|ser]vé`(k=2)
- score 2344.2, strokeFreqSaved 2384.5, keySimilarity 0.01 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 8 (freq 10.4)
- top exceptions: préserver, préservé, préservée, préservez, préservées, préservés, oliver, olivers
    trouvé: tR@e/ve -> tR@edtn
    trouver: tR@e/ve/-l -> tR@edtn/-l
    arrivé: a/Ri/v*e -> *adtn
    arriver: a/Ri/ve/-l -> adtn/-l
    sauver: sae/ve/-l -> saedtn/-l
    retrouver: R@a/tR@e/ve/-l -> R@a/tR@edtn/-l

## 12. prefix `sa` -- keys (24,) = `-Z`

forms: `sa`(k=1), `sa[bor|bou|cré|la|le|li|lo|pris|ta|ti|to|va]-{bo,kRis}·`(k=2)
- score 2180.2, strokeFreqSaved 2204.0, keySimilarity -0.16 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 9 (freq 3.8)
- top exceptions: sacoche, salés, sacoches, salez, salés, salés, saboule, saboulent, saboules
    savoir: sa/vwaR -> vwaRZ
    savez: sa/ve -> veZ
    salut: sa/mt@i -> mt@iZ
    savais: sa/vie/-k -> vieZ/-k
    salut: sa/mt@i -> mt@iZ
    savait: sa/vie -> vieZ

## 13. suffix `ser` -- keys (19, 20, 23) = `-dtl`

forms: `ser`(k=1), `·[a|ba|bi|bo|ca|cia|co|cra|cu|da|dua|dé|ga|gi|gé|ma|mé|na|nna|phi|qui|ra|ri|ria|sua|ta|te|ti|tia|tra|tua|va|vi|via|xua]liser`(k=3), `·[bu|clu|du|ffu|fu|mu|xcu]-{k}sez`(k=2), `·[chi|ci|di|gui|li|lli|ly|mi|ni|nni|phi|ri|thi|ti|tri|vi|xci|y|ï]ser`(k=2)
- score 2100.8, strokeFreqSaved 2264.6, keySimilarity 0.10 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 76 (freq 128.9)
- top exceptions: amuser, causer, amusez, causé, amusé, analyser, amusés, amusée, analysé, causée
    excusez: ie/ks@i/twe/-k -> iedtl/-k
    utiliser: @i/ti/mti/twe/-l -> @idtl/-l
    épouser: e/p@e/twe/-l -> e/p@edtl/-l
    excuser: ie/ks@i/twe/-l -> iedtl/-l
    baiser: svie/twe/-l -> sviedtl/-l

## 14. prefix `par` -- keys (16, 19) = `-jd`

forms: `par`(k=1)
- score 2025.6, strokeFreqSaved 2025.6, keySimilarity -0.20 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 0.0)
- top exceptions: pardingue, pardingues
    partir: paR/tiR -> tijdR
    pardon: paR/pvai -> pvaijd
    parti: paR/t*i -> t*ijd
    parfois: paR/kpwa -> kpwajd
    partout: paR/t@e -> t@ejd
    parlez: paR/mte/-k -> mtejd/-k

## 15. suffix `·[au|blo|bo|ccro|chau|cho|cro|do|dro|fau|ffo|fo|fro|geo|glo|gno|go|illo|jo|lio|llo|lo|mmo|mo|nau|no|o|pho|pio|plô|ppro|pro|reau|rio|ro|sio|so|ssau|ssio|sso|tau|tio|to|tro|trô|vau|vio|vo|xo|xplo|ço]-{k,p}lé` -- keys (20, 24, 25) = `-tZm`

forms: `·[au|blo|bo|ccro|chau|cho|cro|do|dro|fau|ffo|fo|fro|geo|glo|gno|go|illo|jo|lio|llo|lo|mmo|mo|nau|no|o|pho|pio|plô|ppro|pro|reau|rio|ro|sio|so|ssau|ssio|sso|tau|tio|to|tro|trô|vau|vio|vo|xo|xplo|ço]-{k,p}lé`(k=2), `·[lé|mmé|mé|pre|ré|té]phoné`(k=3)
- score 2022.8, strokeFreqSaved 2074.4, keySimilarity 0.06 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 32 (freq 21.5)
- top exceptions: impressionné, impressionner, impressionnée, impressionnés, remémorer, commémorer, auréolé, détériorer, colorée, détériorée
    désolé: pve/twae/mte -> pvetZm
    désolée: pve/twae/mte/-j -> pvetZm/-j
    pardonnez: paR/pvae/mRe/-k -> patRZm/-k
    abandonner: a/sv@/pvae/mRe/-l -> a/sv@tZm/-l
    approchez: a/pRae/pme/-k -> atZm/-k
    exploser: ie/kspmtae/twe/-l -> ietZm/-l

## 16. suffix `·ir` -- keys (18, 20, 23) = `-ktl`

forms: `·ir`(k=1), `·[be|bé|ché|cqué|flé|fraî|mai|pai|qué|vê]chir`(k=2), `·[blou|bou|cou|dou|glou]vrir`(k=2), `·[an|gran|len|men|plen|ran|san|sen|ssen]-{p}tir`(k=2)
- score 1976.8, strokeFreqSaved 2017.8, keySimilarity 0.04 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 8 (freq 6.0)
- top exceptions: rouvrir, rougir, roussir, rouvrirent, rougirent, roussirent, calmir, calmirent
    partir: paR/tiR -> paktRl
    sortir: seR/tiR -> sektRl
    mourir: m@e/RiR -> m@ektl
    dormir: pveR/miR -> pvektRl
    servir: sieR/viR -> siektRl
    sentir: s@/tiR -> s@ktl

## 17. prefix `pou` -- keys (2, 16, 18) = `k-jk`

forms: `pou`(k=1)
- score 1976.6, strokeFreqSaved 1976.6, keySimilarity 0.17 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 0.0)
- top exceptions: poudingue, poudingues
    pouvez: p@e/ve -> kvejk
    pourrait: p@e/Rie -> kRiejk
    pourrais: p@e/Rie/-k -> kRiejk/-k
    pouvoir: p@e/vwaR -> kvwajkR
    pouvais: p@e/vie/-k -> kviejk/-k
    pouvait: p@e/vie -> kviejk

## 18. suffix `·[bu|ccu|chu|cu|dru|du|ffu|fu|gu|ju|llu|lu|mu|nhu|nu|pu|ssu|su|tu|u|xcu]sez` -- keys (9, 20) = `w-t`

forms: `·[bu|ccu|chu|cu|dru|du|ffu|fu|gu|ju|llu|lu|mu|nhu|nu|pu|ssu|su|tu|u|xcu]sez`(k=2)
- score 1829.6, strokeFreqSaved 1829.6, keySimilarity -0.02 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    excusez: ie/ks@i/twe/-k -> wiet/-k
    occuper: ae/k@i/pe/-l -> waet/-l
    discuter: pvis/k@i/te/-l -> pvwist/-l
    amuser: a/m@i/twe/-l -> wat/-l
    excuser: ie/ks@i/twe/-l -> wiet/-l
    occupé: ae/k@i/pe -> waet

## 19. prefix `ré` -- keys (22,) = `-n`

forms: `ré`(k=1), `réa[bo|che|gi|jus|li|mé|ni|per|ra]·`(k=3), `ré[cré|crée|e|flé|fé|gé|pre|pé|vei|vé|é]·`(k=2), `ré[com|con|pon]·`(k=2)
- score 1783.9, strokeFreqSaved 1911.8, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 81 (freq 97.9)
- top exceptions: réalité, réclame, récite, régale, répondit, récré, réforme, réclament, régal, révise
    réponds: Re/pai/-k -> pain/-k
    réveille: Re/v*iej -> v*iejn
    répondre: Re/paidR -> paidRn
    réunion: Re/@i/mRwai -> @in/mRwai
    réfléchir: Re/kpmte/pmiR -> pmiRn

## 20. prefix `pro` -- keys (16,) = `-j` (shares with in)

forms: `pro`(k=1), `pro[co|mo|no|po|ro|so|to|vo]·`(k=2), `pro[con|fon|lon|non]·`(k=2)
- score 1775.4, strokeFreqSaved 1800.5, keySimilarity -0.10 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 6 (freq 5.1)
- top exceptions: proverbe, proverbes, prolapsus, provider, professe, professes
    problème: pRae/svmtiem -> svmtiejm
    problèmes: pRae/svmtiem/-s -> svmtiejm/-s
    propos: pRae/pae -> paej
    prochaine: pRae/pmien -> pmiejn
    promis: pRae/mi -> mij
    promets: pRae/mie/-k -> miej/-k

## 21. prefix `im` -- keys (5, 19) = `v-d`

forms: `im`(k=1), `im[bai|bi|bri|bu|man|pa|pal|par|pay|pe|pen|per|pi|plan|pli|po|pon|por|pos|pra|pre|pri|pro|prou|pru|pré|pu|pui|pé]-{pyl}·`(k=2)
- score 1708.5, strokeFreqSaved 1725.5, keySimilarity -0.13 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 2.1)
- top exceptions: imper, impers
    importe: aie/petR -> pedtR
    important: aie/peR/t@ -> t@d
    impossible: aie/pae/sijl -> sijdl
    impression: aie/pRe/sRwai -> sRwaid
    importance: aie/peR/t@s -> t@sd
    importante: aie/peR/t@t -> t@dt

## 22. suffix `·[ce|cque|de|ge|gre|ille|je|le|lle|me|mme|pe|ppe|que|re|se|sse|te|ve]-{S}ler` -- keys (16, 18, 22) = `-jkn`

forms: `·[ce|cque|de|ge|gre|ille|je|le|lle|me|mme|pe|ppe|que|re|se|sse|te|ve]-{S}ler`(k=2)
- score 1683.3, strokeFreqSaved 1688.3, keySimilarity 0.29 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    appeler: a/p@a/mte/-l -> ajkn/-l
    appelé: a/p@a/mte -> ajkn
    appelez: a/p@a/mte/-k -> ajkn/-k
    emmener: @/m@a/mRe/-l -> @jkn/-l
    rappeler: Ra/p@a/mte/-l -> Rajkn/-l
    emmenez: @/m@a/mRe/-k -> @jkn/-k

## 23. suffix `er` -- keys (20, 22, 23) = `-tnl`

forms: `er`(k=1), `·[bli|blii|boy|clé|cré|doy|dri|droy|flou|flu|geoy|gri|loy|loyi|moy|noy|pli|plii|ppli|ppuy|ppuyi|pri|prii|rroy|ré|ssuy|ssuyi|stru|toy|tri|trii|troy|ttoy|ttoyi|voy|voyi]-{n8ij,vRij}é`(k=2)
- score 1649.5, strokeFreqSaved 1669.5, keySimilarity 0.15 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    oublié: @e/svmtij/e -> @edtl
    oublier: @e/svmtij/e/-l -> @edtl/-l
    envoyé: @/vwaj/e -> @dtl
    envoyer: @/vwaj/e/-l -> @dtl/-l
    oubliez: @e/svmtij/e/-k -> @edtl/-k
    envoyez: @/vwaj/e/-k -> @dtl/-k

## 24. suffix `·[bai|be|chaî|clai|de|e|fe|ga|ge|gre|la|le|lhoue|nai|nna|pe|ple|ppre|pre|pê|re|roue|rrai|rrê|sei|ssa|sse|ta|tai|te|trai|za]ter` -- keys (16, 18, 20) = `-jkt`

forms: `·[bai|be|chaî|clai|de|e|fe|ga|ge|gre|la|le|lhoue|nai|nna|pe|ple|ppre|pre|pê|re|roue|rrai|rrê|sei|ssa|sse|ta|tai|te|trai|za]ter`(k=2)
- score 1606.4, strokeFreqSaved 1606.4, keySimilarity 0.30 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    arrêter: a/Rie/te/-l -> ajkt/-l
    arrêtez: a/Rie/te/-k -> ajkt/-k
    essayer: ie/sie/Rwe/-l -> iejkt/-l
    arrêté: a/Rie/te -> ajkt
    essayez: ie/sie/Rwe/-k -> iejkt/-k
    dépêchez: pve/pie/pme/-k -> pvejkt/-k

## 25. suffix `teur` -- keys (20, 25) = `-tm`

forms: `teur`(k=1), `·[a|ba|bra|ca|cia|da|dia|ga|gna|gra|la|lia|lla|ma|mma|na|nna|pa|pha|pla|qua|ra|ria|rra|sa|sla|ta|tia|tra|va|voi|xa|xploi]teur`(k=2), `·[flec|jec|lec|llec|pec|rec|tec|vec]teur`(k=2), `·[bri|ci|di|fi|gi|i|li|lli|mi|ni|pi|pli|qui|ri|sci|ssi|ti|vi]nateur`(k=3)
- score 1533.3, strokeFreqSaved 1569.4, keySimilarity 0.32 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 12 (freq 6.1)
- top exceptions: compteur, conteur, compteurs, conteurs, conciliateur, préteur, conciliateur, conciliateurs, convecteur, conciliateurs
    docteur: pvek/t@R -> pvektm
    inspecteur: aies/piek/t@R -> aiestm
    directeur: pvi/Riek/t@R -> pvitm
    ordinateur: eR/pvi/mRa/t@R -> etRm
    secteur: sek/t@R -> sektm
    menteur: m@/t@R -> m@tm

## 26. suffix `cher` -- keys (16, 24, 25) = `-jZm`

forms: `cher`(k=1), `·[bau|bo|co|lo|ppro|pro|vau|vo]-{kR}chez`(k=2), `·[bré|lé|pê|raî|ssé]cher`(k=2)
- score 1287.4, strokeFreqSaved 1379.4, keySimilarity 0.59
- word exceptions 10 (freq 66.9)
- top exceptions: empêcher, empêché, empêchée, empêchés, ébréché, ébréchée, empêchées, ébrécher, ébréchées, ébréchés
    chercher: pmieR/pme/-l -> pmiejRZm/-l
    marcher: maR/pme/-l -> majRZm/-l
    coucher: k@e/pme/-l -> k@ejZm/-l
    touché: t@e/pm*e -> t*@ejZm
    toucher: t@e/pme/-l -> t@ejZm/-l

## 27. prefix `se` -- keys (4, 5) = `pv-`

forms: `se`(k=1)
- score 1244.5, strokeFreqSaved 1244.5, keySimilarity -0.33 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 0.0)
- top exceptions: sedan, sedans
    semaine: s@a/mien -> pvmien
    serai: s@a/Re/-t -> pvRe/-t
    semaines: s@a/mien/-s -> pvmien/-s
    serais: s@a/Rie/-k -> pvRie/-k
    seras: s@a/Ra/-d -> pvRa/-d
    secret: s@a/kRie -> kpvRie

## 28. prefix `in` -- keys (16,) = `-j` (shares with pro)

forms: `in`(k=1), `infor[ma|me|mu|po|tu]·`(k=3), `in[co|coh|do|so|to|vio|vo]·`(k=2), `in[can|chan|fran|sen|tan|tem|ten|tran|ven]·`(k=2)
- score 1234.9, strokeFreqSaved 1265.2, keySimilarity 0.00 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 1 (freq 0.3)
- top exceptions: indue
    inquiète: aie/kRwiet -> kRwiedt
    informations: aie/kpeR/ma/sRwai/-s -> sRwaid/-s
    invite: aie/vit -> vidt
    invité: aie/vi/te -> vid/te
    invités: aie/vi/te/-s -> vid/te/-s
    information: aie/kpeR/ma/sRwai -> sRwaid

## 29. prefix `ai` -- keys (3,) = `s-`

forms: `ai`(k=1)
- score 1234.0, strokeFreqSaved 1234.0, keySimilarity -0.50 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 2 (freq 0.0)
- top exceptions: aiguise, aigris
    aider: ie/pve/-l -> spve/-l
    aimerais: ie/m@a/Rie/-k -> sm@a/Rie/-k
    aimer: ie/me/-l -> sme/-l
    aimé: ie/me -> sme
    aidez: ie/pve/-k -> spve/-k
    aimez: ie/me/-k -> sme/-k

## 30. suffix `ture` -- keys (19, 25) = `-dm`

forms: `ture`(k=1), `·[a|ba|bla|ca|che|cri|cul|da|dra|fac|fai|fec|fi|ga|ge|gia|gna|la|ma|me|mma|ni|nia|pos|pul|punc|ra|rri|sla|ta|tec|ti|tra|van|ven|ver|vol]ture`(k=2), `·[chi|di|gi|gis|gri|gé|i|llé|lo|pé|ri|sci|sin|ti|to|trou|tté|ves|é]-{ky}rature`(k=3)
- score 1202.8, strokeFreqSaved 1227.8, keySimilarity 0.35 -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)
- word exceptions 0 (freq 0.0)
    voiture: vwa/t@iR -> vwadtn
    nourriture: mR@e/Ri/t@iR -> mR@edtn
    voitures: vwa/t@iR/-s -> vwadtn/-s
    couverture: k@e/vieR/t@iR -> k@edtn
    peinture: paie/t@iR -> paiedtn
    aventure: a/v@/t@iR -> adtn

## Sibling pairs (candidateSim >= FAMILY_LINK_SIM, not a grow lineage, out of scope for v1)

- ter ~ té (sim 1.00)
- im ~ in (sim 1.00)
- ment ~ ·°ment (sim 0.80)
- ter ~ teur (sim 0.76)
- re ~ ré (sim 0.75)
- teur ~ ture (sim 0.67)
- ver ~ er (sim 0.67)
- der ~ ver (sim 0.67)
- ter ~ ver (sim 0.67)
- ter ~ ser (sim 0.67)
- ver ~ ser (sim 0.67)
- ter ~ der (sim 0.67)
- der ~ ser (sim 0.67)
- der ~ er (sim 0.67)
- ser ~ er (sim 0.67)
- ter ~ er (sim 0.67)
