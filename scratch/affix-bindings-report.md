# Affix abbreviation bindings (measurement and proposals only)

Constants: MAX_AFFIX_SYLL=3, MIN_STEM_LETTERS=3, MIN_CARRIER_LEMMAS=5, MIN_STEM_ROOTS=5, MEMBER_MIN_SHARE=0.05, MIN_CANDIDATE_FREQ=20.0, FAMILY_LINK_SIM=0.6, MAX_FAMILY_MEMBERS=12, MIN_FAMILY_STROKEFREQ=30.0, MAX_FAMILY_CANDIDATES=1500, SIM_MIN=0.5, GAIN_KEEP=0.8, OTHER_BANK_WEIGHT=0.5, NUCLEUS_VOWEL_WEIGHT=0.5, UNEXPLAINED_KEY_PENALTY=0.25, MAX_KEYPRESS_KEYS=3, SPLIT_MAX_LOSS=0.02, NESTED_SIM=0.8, MERGE_SIM_MIN=0.85, MERGE_KEEP=0.9, MERGE_MAX_MEMBERS=8, MERGE_SIM_DROP=0.9, MERGE_MEMBER_SIM_FLOOR=0.6, SAMPLE_CARRIERS=2000

Words carrying both a prefix and a suffix binding are simulated independently.

## S001 (suffix) -- ·°ment, ment

- merged keys [25] = `-m` for ·°ment, ment (sim 0.563, comfort 416.0)
- strokeFreqSaved 8288.8, freqBenefiting 5252.1 of 5296.6 (share by freq 0.992, by count 0.977), boundary risks 958
- fallbacks: {'markCostTooHigh': 58, 'keyOverlap': 1, 'illegalChord': 1}
- alternatives: merged [[25]] sim 0.563 saved 8288.8; merged [[11, 20, 25]] sim 0.563 saved 5714.4; merged [[11, 16, 25]] sim 0.563 saved 5714.3; merged [[11, 19, 25]] sim 0.563 saved 5706.9; merged [[11, 25]] sim 0.703 saved 5703.4

    vraiment: vRie/m@ -> vRiem
    seulement: s@/mt@a/m@ -> s@m
    tellement: tie/mt@a/m@ -> tie/mt@am
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/akm
    sûrement: s@i/R@a/m@ -> s@i/R@am
    complètement: kai/pmtie/t@a/m@ -> kai/pmtiem
    doucement: pv@e/s@a/m@ -> pv@em
    absolument: ajk/sae/mt@i/m@ -> ajk/sae/mt@im
    simplement: saie/pmt@a/m@ -> saiem
    appartement: a/paR/t@a/m@ -> a/paRm

## S002 (suffix) -- ter, té, trer, tant, tter, tier, ce

- merged keys [16, 20, 21] = `-jtR` for ter, té, tter, ce (sim 0.68, comfort 515.0)
- merged keys [8, 20, 21] = `R-tR` for trer (sim 0.68, comfort 515.0)
- merged keys [11, 20, 21] = `@tR` for tant (sim 0.68, comfort 515.0)
- merged keys [17, 20, 21] = `-stR` for tier (sim 0.68, comfort 515.0)
- strokeFreqSaved 6601.7, freqBenefiting 6601.7 of 7945.7 (share by freq 0.831, by count 0.907), boundary risks 9
- fallbacks: {'keyOverlap': 473}
- alternatives: merged [[16, 20, 21], [8, 20, 21], [11, 20, 21], [17, 20, 21]] sim 0.68 saved 6601.7; merged [[16, 17, 20], [16, 20, 21], [11, 16, 20], [16, 18, 20]] sim 0.63 saved 6948.1; merged [[16, 20, 24, 25], [20, 21, 24, 25], [11, 20, 24, 25], [17, 20, 24, 25]] sim 0.62 saved 7483.4; merged [[9, 16, 20, 21], [8, 9, 20, 21], [9, 11, 20, 21], [9, 17, 20, 21]] sim 0.525 saved 6155.1; merged [[16, 17, 20, 21], [8, 16, 20, 21], [11, 16, 20, 21], [16, 18, 20, 21]] sim 0.69 saved 5899.1

    rester: Ries/te/-l -> RiejstR/-l
    vérité: ve/Ri/te -> ve/RijtR
    instant: aies/t@ -> @aiestR
    arrêter: a/Rie/te/-l -> a/RiejtR/-l
    arrêtez: a/Rie/te/-k -> a/RiejtR/-k
    montrer: mai/tRe/-l -> mRaitR/-l
    acheter: a/pm@a/te/-l -> a/pm@ajtR/-l
    sécurité: se/k@i/Ri/te -> se/k@i/RijtR
    restez: Ries/te/-k -> RiejstR/-k
    écoutez: e/k@e/te/-k -> e/k@ejtR/-k

## P002 (prefix) -- re, ré, ren, rem, re, re

- merged keys [5, 8] = `vR-` for re, ré, ren, rem, re, re (sim 0.5, comfort 501.7)
- strokeFreqSaved 5108.8, freqBenefiting 5108.8 of 7705.8 (share by freq 0.663, by count 0.653), boundary risks 123
- fallbacks: {'keyOverlap': 2465, 'markCostTooHigh': 123, 'lostDistinction': 48}
- alternatives: merged [[6, 8]] sim 0.5 saved 5564.3; merged [[5, 8]] sim 0.5 saved 5108.8; merged [[7, 8]] sim 0.5 saved 5205.7

    regarde: R@a/ksadR -> ksvRadR
    regardez: R@a/ksaR/pve/-k -> ksvRaR/pve/-k
    regarder: R@a/ksaR/pve/-l -> ksvRaR/pve/-l
    retour: R@a/t@eR -> vtR@eR
    retard: R@a/taR -> vtRaR
    rencontrer: R@/kai/tRe/-l -> kvRai/tRe/-l
    rencontré: R@/kai/tRe -> kvRai/tRe
    retourne: R@a/t@eRn -> vtR@eRn
    retourner: R@a/t@eR/mRe/-l -> vtR@eR/mRe/-l
    réponds: Re/pai/-k -> pvRai/-k

## S003 (suffix) -- ser, sser, cer, ser, ·asser, ·@cer, cé, ssé, sé

- merged keys [17, 22, 23] = `-snl` for ser, sser, cer, ser, ·asser, ·@cer, cé, ssé, sé (sim 0.652, comfort 546.2)
- strokeFreqSaved 4897.3, freqBenefiting 4749.4 of 4820.8 (share by freq 0.985, by count 0.938), boundary risks 0
- fallbacks: {'markCostTooHigh': 137, 'keyOverlap': 118, 'illegalChord': 6}
- alternatives: merged [[17, 22, 23]] sim 0.652 saved 4897.3; merged [[7, 9, 17]] sim 0.554 saved 3377.6; merged [[14, 17]] sim 0.62 saved 2867.2; merged [[12, 14, 17]] sim 0.627 saved 2158.0; merged [[11, 14, 17]] sim 0.624 saved 1192.5

    laissez: mtie/se/-k -> mtiesnl/-k
    laisser: mtie/se/-l -> mtiesnl/-l
    excusez: ie/ks@i/twe/-k -> ie/ks@isnl/-k
    pensé: p@/s*e -> p*@snl
    pensez: p@/se/-k -> p@snl/-k
    penser: p@/se/-l -> p@snl/-l
    laissé: mtie/se -> mtiesnl
    commencé: kae/m@/se -> kae/m@snl
    commencer: kae/m@/se/-l -> kae/m@snl/-l
    danser: pv@/se/-l -> pv@snl/-l

## S004+S045 (suffix) -- tion, ·[ca|cia|crip|ma|mma|pec|rec|rrec|tec|tia|ven]tion, tion, ssion, sion, sion, llon, ption

- merged keys [16, 17, 18] = `-jsk` for tion, ·[ca|cia|crip|ma|mma|pec|rec|rrec|tec|tia|ven]tion, tion, ssion, sion, sion, llon, ption (sim 0.543, comfort 478.1)
- strokeFreqSaved 3730.8, freqBenefiting 3335.2 of 4205.0 (share by freq 0.793, by count 0.878), boundary risks 56
- fallbacks: {'keyOverlap': 212}
- alternatives: merged [[16, 17, 18]] sim 0.543 saved 3730.8; merged [[16, 17, 20]] sim 0.524 saved 4081.3; merged [[16, 17, 21]] sim 0.504 saved 3830.6; merged [[16, 17, 25]] sim 0.504 saved 4081.3

    attention: a/t@/sRwai -> a/t@jsk
    attention: a/t@/sRwai -> a/t@jsk
    situation: si/t@a/sRwai -> si/t@ajsk
    impression: aie/pRe/sRwai -> aie/pRejsk
    solution: sae/mt@i/sRwai -> sae/mt@ijsk
    occasion: ae/ka/tRwai -> ae/kajsk
    position: pae/twi/sRwai -> pae/twijsk
    décision: pve/si/tRwai -> pve/sijsk
    opération: ae/pe/Ra/sRwai -> ae/pe/Rajsk
    relation: R@a/mta/sRwai -> R@a/mtajsk

## P004 (prefix) -- pour, pou, po, por, pom

- merged keys [3, 4, 8] = `spR-` for pour, pou, po, por, pom (sim 0.626, comfort 490.4)
- strokeFreqSaved 3674.9, freqBenefiting 3674.9 of 4818.5 (share by freq 0.763, by count 0.497), boundary risks 0
- fallbacks: {'keyOverlap': 217, 'markCostTooHigh': 12}
- alternatives: merged [[3, 4, 8]] sim 0.626 saved 3674.9; merged [[4, 8, 16]] sim 0.626 saved 3703.7; merged [[4, 8, 19]] sim 0.626 saved 3763.0; merged [[4, 8, 20]] sim 0.626 saved 3724.8; merged [[4, 8, 23]] sim 0.626 saved 3720.3

    pourquoi: p@eR/kwa -> kspRwa
    pourquoi: p@eR/kwa -> kspRwa
    pouvez: p@e/ve -> spvRe
    police: pae/mtis -> spmtRis
    pouvoir: p@e/vwaR -> spvRwaR
    pouvais: p@e/vie/-k -> spvRie/-k
    pouvait: p@e/vie -> spvRie
    pourtant: p@eR/t@ -> sptR@
    pouvoir: p@e/vwaR -> spvRwaR
    pouvons: p@e/vai -> spvRai

## S005 (suffix) -- ·ation, ·ission, ction

- merged keys [16, 17] = `-js` for ·ation, ·ission, ction (sim 0.666, comfort 396.6)
- strokeFreqSaved 3178.6, freqBenefiting 1597.7 of 1660.2 (share by freq 0.962, by count 0.953), boundary risks 290
- fallbacks: {'keyOverlap': 72, 'markCostTooHigh': 1}
- alternatives: merged [[16, 17, 18]] sim 0.667 saved 3173.0; merged [[16, 17]] sim 0.666 saved 3178.6; merged [[11, 16, 17]] sim 0.583 saved 2640.8; merged [[5, 16, 17]] sim 0.583 saved 2728.8; merged [[16, 17, 19]] sim 0.583 saved 3180.0

    félicitations: kpe/mti/si/ta/sRwai/-s -> kpe/mti/sijs/-s
    opération: ae/pe/Ra/sRwai -> ae/pejs
    informations: aie/kpeR/ma/sRwai/-s -> aie/kpejsR/-s
    conversation: kai/vieR/sa/sRwai -> kai/viejsR
    permission: pieR/mi/sRwai -> piejsR
    imagination: i/ma/vti/mRa/sRwai -> i/ma/vtijs
    condition: kai/pvi/sRwai -> kaijs
    explication: ie/kspmti/ka/sRwai -> ie/kspmtijs
    information: aie/kpeR/ma/sRwai -> aie/kpejsR
    réputation: Re/p@i/ta/sRwai -> Re/p@ijs

## P003 (prefix) -- en, em, an

- merged keys [11] = `@` for en, em, an (sim 0.5, comfort 400.6)
- strokeFreqSaved 2499.1, freqBenefiting 2499.1 of 5439.1 (share by freq 0.459, by count 0.729), boundary risks 545
- fallbacks: {'markCostTooHigh': 59, 'keyOverlap': 731}
- alternatives: merged [[11]] sim 0.5 saved 2499.1

    enfin: @/kpaie -> kp@aie
    endroit: @/pvRwa -> pvRw@a
    envoie: @/vwa -> vw@a
    enfer: @/kpieR -> kp@ieR
    envoyé: @/vwaj/e -> vw@aj/e
    emmène: @/mien -> m@ien
    envoyer: @/vwaj/e/-l -> vw@aj/e/-l
    empêcher: @/pe/pme/-l -> p@e/pme/-l
    enlève: @/mtiejs -> mt@iejs
    enquête: @/kiet -> k@iet

## S006 (suffix) -- ler, lé, let, ller, lant, lent, fler

- merged keys [14, 16, 23] = `ejl` for ler, lé, let, ller, lant, lent, fler (sim 0.655, comfort 527.9)
- strokeFreqSaved 2255.8, freqBenefiting 2255.8 of 3297.7 (share by freq 0.684, by count 0.624), boundary risks 24
- fallbacks: {'keyOverlap': 701, 'markCostTooHigh': 108}
- alternatives: merged [[14, 16, 23]] sim 0.655 saved 2255.8; merged [[14, 17, 23]] sim 0.655 saved 2255.8; merged [[14, 18, 23]] sim 0.655 saved 2255.8; merged [[14, 19, 23]] sim 0.655 saved 2255.8

    parler: paR/mte/-l -> paejRl/-l
    parlé: paR/mte -> paejRl
    appeler: a/p@a/mte/-l -> a/p@aejl/-l
    appelé: a/p@a/mte -> a/p@aejl
    parlez: paR/mte/-k -> paejRl/-k
    appelez: a/p@a/mte/-k -> a/p@aejl/-k
    rappeler: Ra/p@a/mte/-l -> Ra/p@aejl/-l
    rappelez: Ra/p@a/mte/-k -> Ra/p@aejl/-k
    appelée: a/p@a/mte/-j -> a/p@aejl/-j
    brûler: svR@i/mte/-l -> svR@iejl/-l

## S014 (suffix) -- ·°nant, ·°nu

- merged keys [11, 22] = `@n` for ·°nant, ·°nu (sim 0.619, comfort 435.6)
- strokeFreqSaved 2152.9, freqBenefiting 1076.8 of 1178.1 (share by freq 0.914, by count 0.537), boundary risks 0
- fallbacks: {'keyOverlap': 25, 'markCostTooHigh': 13}
- alternatives: merged [[11, 22]] sim 0.619 saved 2152.9; merged [[22]] sim 0.5 saved 2328.4; merged [[11, 12, 22]] sim 0.744 saved 8.5; merged [[11, 13, 22]] sim 0.625 saved 5.2

    maintenant: maie/t@a/mR@ -> m@aien
    bienvenue: svRwaie/v@a/mR@i -> svRw@aien
    bienvenu: svRwaie/v@a/mR*@i -> svRw*@aien
    bienvenus: svRwaie/v@a/mR@i/-s -> svRw@aien/-s
    prévenue: pRie/v@a/mR@i/-j -> pR@ien/-j
    bienvenus: svRwaie/v@a/mR@i/-s -> svRw@aien/-s
    inconvenant: aie/kai/v@a/mR@ -> aie/k@ain
    bienvenu: svRwaie/v@a/mR*@i -> svRw*@aien
    bienvenues: svRwaie/v@a/mR*@i/-s -> svRw*@aien/-s
    prévenu: pRie/v@a/mR@i -> pR@ien

## P012 (prefix) -- sou, cou, nou, dou, ou, fou

- merged keys [2, 3, 17, 22] = `ks-sn` for sou, nou, ou (sim 0.536, comfort 667.7)
- merged keys [2, 3, 18, 22] = `ks-kn` for cou (sim 0.536, comfort 667.7)
- merged keys [2, 3, 19, 22] = `ks-dn` for dou (sim 0.536, comfort 667.7)
- merged keys [2, 3, 8, 22] = `ksR-n` for fou (sim 0.536, comfort 667.7)
- strokeFreqSaved 2144.3, freqBenefiting 2144.3 of 2250.3 (share by freq 0.953, by count 0.867), boundary risks 0
- fallbacks: {'keyOverlap': 85, 'illegalChord': 9}
- alternatives: merged [[2, 3, 17, 22], [2, 3, 18, 22], [2, 3, 19, 22], [2, 3, 8, 22]] sim 0.536 saved 2144.3

    souviens: s@e/vRwaie/-k -> ksvRwaiesn/-k
    nouveau: mR@e/vae -> ksvaesn
    souvent: s@e/v@ -> ksv@sn
    nouveau: mR@e/vae -> ksvaesn
    coucher: k@e/pme/-l -> kspmekn/-l
    nouvelles: mR@e/viel/-s -> ksviesnl/-s
    courage: k@e/RaZ -> ksRaknZ
    douleur: pv@e/mt@R -> ksmt@dRn
    couleur: k@e/mt@R -> ksmt@kRn
    ouvert: @e/vieR -> ksviesRn

## S016 (suffix) -- ci, cile, cide, tie, cine, cis

- merged keys [17, 19, 23] = `-sdl` for ci, cile, cide, tie, cine, cis (sim 0.69, comfort 508.5)
- strokeFreqSaved 1989.8, freqBenefiting 1989.8 of 2013.3 (share by freq 0.988, by count 0.988), boundary risks 9
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[17, 19, 23]] sim 0.69 saved 1989.8; merged [[17, 22, 23]] sim 0.682 saved 2013.3; merged [[17, 23]] sim 0.675 saved 2013.3; merged [[17, 19, 22]] sim 0.628 saved 1989.8; merged [[17, 19]] sim 0.621 saved 1989.7

    merci: mieR/si -> miesdRl
    merci: mieR/si -> miesdRl
    voici: vwa/si -> vwasdl
    difficile: pvi/kpi/sil -> pvi/kpisdl
    imbécile: aie/sve/sil -> aie/svesdl
    souci: s@e/si -> s@esdl
    suicide: s@ai/sid -> s@aisdl
    soucis: s@e/si/-s -> s@esdl/-s
    précis: pRe/si -> pResdl
    imbécile: aie/sve/sil -> aie/svesdl

## P016 (prefix) -- par, parti

- merged keys [8, 16, 18] = `R-jk` for par, parti (sim 0.59, comfort 550.7)
- strokeFreqSaved 1985.5, freqBenefiting 1978.1 of 2029.0 (share by freq 0.975, by count 0.889), boundary risks 21
- fallbacks: {'keyOverlap': 27, 'markCostTooHigh': 5}
- alternatives: merged [[8, 16, 18]] sim 0.59 saved 1985.5; merged [[4, 8, 16]] sim 0.688 saved 1275.5; merged [[4, 8, 17]] sim 0.688 saved 1275.5; merged [[4, 8, 19]] sim 0.688 saved 1275.5; merged [[4, 8, 18]] sim 0.688 saved 1275.3

    partir: paR/tiR -> tRijkR
    pardon: paR/pvai -> pvRaijk
    parti: paR/t*i -> tR*ijk
    parfois: paR/kpwa -> kpRwajk
    partout: paR/t@e -> tR@ejk
    parlez: paR/mte/-k -> mtRejk/-k
    partie: paR/ti/-j -> tRijk/-j
    partez: paR/te -> tRejk
    pardon: paR/pvai -> pvRaijk
    pardonne: paR/pven -> pvRejkn

## P007 (prefix) -- dé, dé

- merged keys [4, 5, 16] = `pv-j` for dé, dé (sim 0.5, comfort 521.8)
- strokeFreqSaved 1927.6, freqBenefiting 1927.6 of 3217.7 (share by freq 0.599, by count 0.579), boundary risks 58
- fallbacks: {'keyOverlap': 2516, 'lostDistinction': 22}
- alternatives: merged [[4, 5]] sim 0.667 saved 1974.8; merged [[4, 5, 6]] sim 0.5 saved 1627.6; merged [[4, 5, 17]] sim 0.5 saved 1771.5; merged [[4, 5, 8]] sim 0.5 saved 1650.9; merged [[4, 5, 16]] sim 0.5 saved 1927.6

    désolé: pve/twae/mte -> pvtwaej/mte
    désolé: pve/twae/mte -> pvtwaej/mte
    désolée: pve/twae/mte/-j -> pvtwaej/mte/-j
    déteste: pve/tiest -> pvtiejst
    dérange: pve/R@Z -> pvR@jZ
    dégage: pve/ksaZ -> kspvajZ
    découvert: pve/k@e/vieR -> kpv@ej/vieR
    démon: pve/mai -> pvmaij
    découvrir: pve/k@e/vRiR -> kpv@ej/vRiR
    détruit: pve/tR@ai -> pvtR@aij

## S010 (suffix) -- der, dant, dent, ·ider, dé, ·@der

- merged keys [14, 16, 19] = `ejd` for der, dé, ·@der (sim 0.771, comfort 508.0)
- merged keys [11, 14, 19] = `@ed` for dant, dent, ·ider (sim 0.771, comfort 508.0)
- strokeFreqSaved 1840.3, freqBenefiting 1828.8 of 2561.8 (share by freq 0.714, by count 0.542), boundary risks 0
- fallbacks: {'keyOverlap': 739}
- alternatives: merged [[14, 16, 19], [11, 14, 19]] sim 0.771 saved 1840.3; merged [[14, 16, 17, 19], [11, 14, 17, 19]] sim 0.607 saved 1840.3; merged [[14, 16, 18, 19], [11, 14, 18, 19]] sim 0.607 saved 1840.3; merged [[8, 14, 16, 19], [8, 11, 14, 19]] sim 0.607 saved 1811.0; merged [[5, 14, 16, 19], [5, 11, 14, 19]] sim 0.607 saved 1756.2

    regardez: R@a/ksaR/pve/-k -> R@a/ksaejdR/-k
    demandé: pv@a/m@/pve -> pv@a/m@ejd
    demander: pv@a/m@/pve/-l -> pv@a/m@ejd/-l
    regarder: R@a/ksaR/pve/-l -> R@a/ksaejdR/-l
    président: pRe/twi/pv@ -> pRe/tw@ied
    garder: ksaR/pve/-l -> ksaejdR/-l
    accident: ak/si/pv@ -> ak/s@ied
    décidé: pve/si/pve -> pve/siejd
    demandez: pv@a/m@/pve/-k -> pv@a/m@ejd/-k
    décider: pve/si/pve/-l -> pve/siejd/-l

## S011 (suffix) -- ·Etement, ·2sement, ·ablement, ·Ellement, ·Erement, ·alement, ·Enement, ·iquement, ·issement, ·ivement

- dedicated keys [11, 12, 25] = `@am` for ·Etement, ·2sement, ·ablement, ·Ellement, ·Erement, ·alement, ·Enement, ·iquement, ·issement, ·ivement, ·Onnement (sim 0.429, comfort 254.0)
- strokeFreqSaved 1736.7, freqBenefiting 868.4 of 868.4 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[11, 12, 25]] sim 0.429 saved 1736.7; dedicated [[11, 23, 25]] sim 0.427 saved 1736.7; dedicated [[3, 5, 6, 7, 8, 11, 12]] sim 0.417 saved 1736.7; dedicated [[20, 23, 25]] sim 0.409 saved 1736.7; dedicated [[3, 5, 6, 7, 9, 11, 12]] sim 0.406 saved 1736.7

    complètement: kai/pmtie/t@a/m@ -> kai/@am
    probablement: pRae/sva/svmt@a/m@ -> pRae/@am
    certainement: sieR/tie/mR@a/m@ -> sieR/@am
    parfaitement: paR/kpie/t@a/m@ -> paR/@am
    heureusement: @ie/R@ie/tw@a/m@ -> @ie/@am
    malheureusement: ma/mt@ie/R@ie/tw@a/m@ -> ma/mt@ie/@am
    naturellement: mRa/t@i/Rie/mt@a/m@ -> mRa/t@i/@am
    normalement: mReR/ma/mt@a/m@ -> mReR/@am
    personnellement: pieR/sae/mRie/mt@a/m@ -> pieR/sae/@am
    particulièrement: paR/ti/k@i/mtRwie/R@a/m@ -> paR/ti/k@i/@am

## P010 (prefix) -- sa, sau

- merged keys [3, 12, 16] = `saj` for sa (sim 0.5, comfort 480.0)
- merged keys [3, 8, 16] = `sR-j` for sau (sim 0.5, comfort 480.0)
- strokeFreqSaved 1734.9, freqBenefiting 1734.9 of 2565.1 (share by freq 0.676, by count 0.629), boundary risks 2
- fallbacks: {'keyOverlap': 138}
- alternatives: merged [[3, 12, 16], [3, 8, 16]] sim 0.5 saved 1734.9; merged [[3, 12, 17], [3, 8, 17]] sim 0.5 saved 1779.2; merged [[3, 12, 20], [3, 8, 20]] sim 0.5 saved 1807.7; merged [[3, 12, 19], [3, 8, 19]] sim 0.5 saved 1807.6; merged [[3, 4, 12], [3, 4, 8]] sim 0.5 saved 1765.7

    savez: sa/ve -> svaej
    salut: sa/mt@i -> smt@aij
    savais: sa/vie/-k -> svaiej/-k
    salut: sa/mt@i -> smt@aij
    sauver: sae/ve/-l -> svRej/-l
    savait: sa/vie -> svaiej
    sauvé: sae/ve -> svRej
    sauter: sae/te/-l -> stRej/-l
    saviez: sa/vRwe -> svRwaej
    sacré: sa/kRe -> ksRaej

## S018 (suffix) -- iller, ller, mier, nier, yer, lier, nnier, llant, illé, llé

- merged keys [6, 16, 22, 23] = `m-jnl` for iller, ller, mier, yer, nnier, illé, llé, ier (sim 0.66, comfort 640.2)
- merged keys [11, 16, 22, 23] = `@jnl` for nier, llant (sim 0.66, comfort 640.2)
- merged keys [16, 17, 22, 23] = `-jsnl` for lier (sim 0.66, comfort 640.2)
- strokeFreqSaved 1730.4, freqBenefiting 1730.4 of 1800.1 (share by freq 0.961, by count 0.872), boundary risks 0
- fallbacks: {'keyOverlap': 193, 'illegalChord': 6}
- alternatives: merged [[6, 16, 22, 23], [11, 16, 22, 23], [16, 17, 22, 23]] sim 0.66 saved 1730.4; merged [[6, 16, 23, 25], [11, 16, 23, 25], [16, 17, 23, 25]] sim 0.649 saved 1730.4; merged [[6, 16, 17, 22], [6, 11, 16, 22], [6, 16, 22, 23]] sim 0.649 saved 1705.1; merged [[6, 16, 23, 25], [6, 16, 22, 23], [6, 16, 17, 23]] sim 0.607 saved 1712.9; merged [[6, 16, 22], [11, 16, 22], [16, 22, 23]] sim 0.607 saved 1735.0

    travailler: tRa/va/Rwe/-l -> tRa/vmajnl/-l
    premier: pR@ie/mRwe -> pmR@iejnl
    dernier: pvieR/mRwe -> pv@iejRnl
    essayer: ie/sie/Rwe/-l -> ie/smiejnl/-l
    premier: pR@ie/mRwe -> pmR@iejnl
    essayez: ie/sie/Rwe/-k -> ie/smiejnl/-k
    travaillé: tRa/va/Rwe -> tRa/vmajnl
    derniers: pvieR/mRwe/-s -> pv@iejRnl/-s
    dernier: pvieR/mRwe -> pv@iejRnl
    réveiller: Re/vie/Rwe/-l -> Re/vmiejnl/-l

## S008+S073 (suffix) -- ·[le|lle|te|tte]ment, ·[ce|ci|cqui|cè|ga|na|qui|rein|se|so|zo]lement

- dedicated keys [20, 23, 25] = `-tlm` for ·[le|lle|te|tte]ment, ·[ce|ci|cqui|cè|ga|na|qui|rein|se|so|zo]lement (sim 0.374, comfort 343.0)
- strokeFreqSaved 1688.8, freqBenefiting 1548.4 of 1548.4 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[20, 23, 25]] sim 0.374 saved 1688.8; dedicated [[7, 23, 25]] sim 0.312 saved 1688.8; dedicated [[6, 20, 23]] sim 0.312 saved 1688.8; dedicated [[11, 20, 23]] sim 0.281 saved 1688.8; dedicated [[11, 20, 25]] sim 0.281 saved 1688.8

    seulement: s@/mt@a/m@ -> s@/-tlm
    tellement: tie/mt@a/m@ -> tie/-tlm
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/ak/-tlm
    complètement: kai/pmtie/t@a/m@ -> kai/pmtie/-tlm
    appartement: a/paR/t@a/m@ -> a/paR/-tlm
    justement: vt@is/t@a/m@ -> vt@is/-tlm
    vêtements: vie/t@a/m@/-s -> vie/-tlm/-s
    immédiatement: i/me/pvRwa/t@a/m@ -> i/me/pvRwa/-tlm
    finalement: kpi/mRa/mt@a/m@ -> kpi/-tlm
    parfaitement: paR/kpie/t@a/m@ -> paR/kpie/-tlm

## S017 (suffix) -- ger, gé, gent

- merged keys [14, 24] = `eZ` for ger, gé, gent (sim 0.827, comfort 428.3)
- strokeFreqSaved 1626.1, freqBenefiting 1626.1 of 1963.0 (share by freq 0.828, by count 0.689), boundary risks 32
- fallbacks: {'keyOverlap': 361, 'illegalChord': 2, 'markCostTooHigh': 8}
- alternatives: merged [[14, 24]] sim 0.827 saved 1626.1; merged [[14, 24, 25]] sim 0.661 saved 1629.0; merged [[9, 14, 24]] sim 0.661 saved 1617.5; merged [[14, 22, 24]] sim 0.661 saved 1629.0; merged [[14, 16, 24]] sim 0.661 saved 1629.0

    manger: m@/vte/-l -> m@eZ/-l
    changer: pm@/vte/-l -> pm@eZ/-l
    changé: pm@/vte -> pm@eZ
    danger: pv@/vte -> pv@eZ
    mangé: m@/vte -> m@eZ
    arranger: a/R@/vte/-l -> a/R@eZ/-l
    obligé: ae/svmti/vte -> ae/svmtieZ
    étranger: e/tR@/vte -> e/tR@eZ
    partager: paR/ta/vte/-l -> paR/taeZ/-l
    intelligent: aie/te/mti/vt@ -> aie/te/mtieZ

## S009 (suffix) -- ·ité, ·@ter, ·oté, ·°té

- merged keys [13, 20] = `it` for ·ité (sim 0.5, comfort 427.4)
- merged keys [11, 20] = `@t` for ·@ter (sim 0.5, comfort 427.4)
- merged keys [16, 20] = `-jt` for ·oté (sim 0.5, comfort 427.4)
- merged keys [17, 20] = `-st` for ·°té (sim 0.5, comfort 427.4)
- strokeFreqSaved 1554.3, freqBenefiting 809.4 of 1400.2 (share by freq 0.578, by count 0.686), boundary risks 297
- fallbacks: {'keyOverlap': 834, 'markCostTooHigh': 56}
- alternatives: merged [[11, 13, 20], [11, 16, 20], [11, 17, 20], [11, 18, 20]] sim 0.52 saved 1409.9; merged [[13, 20], [11, 20], [16, 20], [17, 20]] sim 0.5 saved 1554.3; merged [[13, 14, 20, 22], [11, 14, 20, 22], [14, 16, 20, 22], [14, 17, 20, 22]] sim 0.5 saved 849.6; merged [[13, 14, 20, 25], [11, 14, 20, 25], [14, 16, 20, 25], [14, 17, 20, 25]] sim 0.5 saved 849.6; merged [[13, 14, 19, 20], [11, 14, 19, 20], [14, 16, 19, 20], [14, 17, 19, 20]] sim 0.5 saved 849.0

    présenter: pRe/tw@/te/-l -> pR@et/-l
    réalité: Re/a/mti/te -> Re/ait
    identité: i/pv@/ti/te -> i/pv@it
    humanité: @i/ma/mRi/te -> @i/mait
    profiter: pRae/kpi/te/-l -> pRaiet/-l
    communauté: kae/m@i/mRae/te -> kae/m@ijt
    autorité: ae/tae/Ri/te -> ae/taiet
    plaisantez: pmtie/tw@/te/-k -> pmt@iet/-k
    autorités: ae/tae/Ri/te/-s -> ae/taiet/-s
    personnalité: pieR/sae/mRa/mti/te -> pieR/sae/mRait

## S015 (suffix) -- rer, ·erer, rant, ·yrer, ré, rrer, rent, ·orer

- merged keys [11, 16, 21] = `@jR` for rer, ré, rrer (sim 0.666, comfort 524.2)
- merged keys [11, 17, 21] = `@sR` for ·erer (sim 0.666, comfort 524.2)
- merged keys [11, 18, 21] = `@kR` for rant, ·yrer, rent, ·orer (sim 0.666, comfort 524.2)
- strokeFreqSaved 1535.1, freqBenefiting 1324.7 of 1886.3 (share by freq 0.702, by count 0.674), boundary risks 71
- fallbacks: {'keyOverlap': 1009, 'markCostTooHigh': 6}
- alternatives: merged [[11, 16, 21], [11, 17, 21], [11, 18, 21]] sim 0.666 saved 1535.1; merged [[11, 16, 19, 21], [11, 17, 19, 21], [11, 18, 19, 21]] sim 0.505 saved 1535.1; merged [[11, 16, 20, 21], [11, 17, 20, 21], [11, 18, 20, 21]] sim 0.505 saved 1534.8; merged [[6, 11, 16, 21], [6, 11, 17, 21], [6, 11, 18, 21]] sim 0.505 saved 1312.7; merged [[5, 11, 16, 21], [5, 11, 17, 21], [5, 11, 18, 21]] sim 0.505 saved 1393.0

    différent: pvi/kpe/R@ -> pvi/kp@ekR
    préparer: pRe/pa/Re/-l -> pRe/p@ajR/-l
    restaurant: Ries/tae/R@ -> Ries/t@aekR
    réparer: Re/pa/Re/-l -> Re/p@ajR/-l
    respirer: Ries/pi/Re/-l -> Ries/p@ijR/-l
    retirer: R@a/ti/Re/-l -> R@a/t@ijR/-l
    préparez: pRe/pa/Re/-k -> pRe/p@ajR/-k
    libérer: mti/sve/Re/-l -> mti/sv@ejR/-l
    préparé: pRe/pa/Re -> pRe/p@ajR
    désirez: pve/twi/Re/-k -> pve/tw@ijR/-k

## P022 (prefix) -- reaR·, reER·, reOl·, raOR·, reOR·, reuR·

- merged keys [8, 9, 11, 12] = `Rw@a` for reaR· (sim 0.694, comfort 500.5)
- merged keys [8, 11, 12, 23] = `R@al` for reER·, reOl· (sim 0.694, comfort 500.5)
- merged keys [2, 8, 11, 12] = `kR@a` for reOR·, reuR· (sim 0.694, comfort 500.5)
- merged keys [8, 11, 12, 14] = `R@ae` for raOR· (sim 0.694, comfort 500.5)
- strokeFreqSaved 1420.6, freqBenefiting 713.3 of 850.3 (share by freq 0.839, by count 0.504), boundary risks 0
- fallbacks: {'keyOverlap': 205, 'markCostTooHigh': 20}
- alternatives: merged [[8, 9, 11, 12], [8, 11, 12, 23], [2, 8, 11, 12], [8, 11, 12, 14]] sim 0.694 saved 1420.6; merged [[8, 9, 12, 23], [8, 12, 14, 23], [2, 8, 12, 23], [3, 8, 12, 23]] sim 0.595 saved 1386.7; merged [[8, 9, 12], [8, 12, 23], [2, 8, 12], [8, 12, 14]] sim 0.583 saved 1453.2; merged [[6, 7, 8, 9], [6, 7, 8, 23], [2, 6, 7, 8], [6, 7, 8, 14]] sim 0.512 saved 1313.2; merged [[8, 9, 23], [8, 14, 23], [2, 8, 23], [3, 8, 23]] sim 0.5 saved 1463.1

    regardez: R@a/ksaR/pve/-k -> pvRw@ae/-k
    regarder: R@a/ksaR/pve/-l -> pvRw@ae/-l
    remercie: R@a/mieR/si -> sR@ail
    remarqué: R@a/maR/ke -> kRw@ae
    regardé: R@a/ksaR/pve -> pvRw@ae
    revolver: Re/vel/vieR -> vR@aieRl
    repartir: R@a/paR/tiR -> tRw@aiR
    regardait: R@a/ksaR/pvie -> pvRw@aie
    regardais: R@a/ksaR/pvie/-k -> pvRw@aie/-k
    reparti: R@a/paR/ti -> tRw@ai

## P014 (prefix) -- se, sé, ce, sen, cen, cé

- merged keys [3, 11, 19] = `s@d` for se, sé, ce, sen, cen, cé (sim 0.519, comfort 555.4)
- strokeFreqSaved 1367.7, freqBenefiting 1367.7 of 2118.3 (share by freq 0.646, by count 0.678), boundary risks 2
- fallbacks: {'keyOverlap': 115, 'markCostTooHigh': 10, 'illegalChord': 2}
- alternatives: merged [[3, 11, 19]] sim 0.519 saved 1367.7; merged [[3, 11, 18]] sim 0.519 saved 1367.5; merged [[3, 11, 16]] sim 0.519 saved 1367.1; merged [[3, 11]] sim 0.686 saved 1366.3

    semaine: s@a/mien -> sm@iedn
    serai: s@a/Re/-t -> sR@ed/-t
    semaines: s@a/mien/-s -> sm@iedn/-s
    serais: s@a/Rie/-k -> sR@ied/-k
    seras: s@a/Ra/-d -> sR@ad/-d
    secret: s@a/kRie -> ksR@ied
    sentir: s@/tiR -> st@idR
    serez: s@a/Re/-d -> sR@ed/-d
    serais: s@a/Rie/-d -> sR@ied/-d
    senti: s@/ti -> st@id

## P026 (prefix) -- ja

- merged keys [5, 7, 12] = `vta` for ja (sim 0.833, comfort 505.1)
- strokeFreqSaved 1361.8, freqBenefiting 1361.8 of 1363.7 (share by freq 0.999, by count 0.178), boundary risks 0
- fallbacks: {'keyOverlap': 37}
- alternatives: merged [[5, 7, 12]] sim 0.833 saved 1361.8; merged [[5, 7]] sim 0.667 saved 1363.5; merged [[4, 5, 7]] sim 0.5 saved 1363.4; merged [[12, 24]] sim 0.5 saved 1361.8; merged [[3, 5, 7]] sim 0.5 saved 1363.5

    jamais: vta/mie -> vmtaie
    jaquette: vta/kiet -> kvtaiet
    jachère: vta/pmieR -> pvmtaieR
    jacob: vta/kej -> kvtaej
    jaquettes: vta/kiet/-s -> kvtaiet/-s
    jaquet: vta/kie# -> kvtaie#
    jachères: vta/pmieR/-s -> pvmtaieR/-s
    jacobs: vta/kej/-s -> kvtaej/-s

## P011 (prefix) -- pro, proe·, proi·, pro, poe·, proa·, proo·

- merged keys [4, 8, 9, 19] = `pRw-d` for pro (sim 0.666, comfort 677.1)
- merged keys [4, 8, 13, 19] = `pRid` for proi·, pro, poe·, proa· (sim 0.666, comfort 677.1)
- merged keys [4, 8, 14, 19] = `pRed` for proe· (sim 0.666, comfort 677.1)
- merged keys [2, 4, 8, 19] = `kpR-d` for proo· (sim 0.666, comfort 677.1)
- strokeFreqSaved 1181.9, freqBenefiting 1092.1 of 2048.0 (share by freq 0.533, by count 0.506), boundary risks 2
- fallbacks: {'keyOverlap': 417, 'markCostTooHigh': 6}
- alternatives: merged [[8, 9, 16, 18], [8, 13, 16, 18], [8, 14, 16, 18], [2, 8, 16, 18]] sim 0.569 saved 1802.3; merged [[4, 8, 9], [4, 8, 13], [4, 8, 14], [2, 4, 8]] sim 0.763 saved 1184.1; merged [[4, 8, 9, 19], [4, 8, 13, 19], [4, 8, 14, 19], [2, 4, 8, 19]] sim 0.666 saved 1181.9; merged [[4, 8, 9, 16], [4, 8, 13, 16], [4, 8, 14, 16], [2, 4, 8, 16]] sim 0.666 saved 1170.1; merged [[4, 8, 9, 20], [4, 8, 13, 20], [4, 8, 14, 20], [2, 4, 8, 20]] sim 0.666 saved 1164.7

    problème: pRae/svmtiem -> spvmtRwiedm
    problèmes: pRae/svmtiem/-s -> spvmtRwiedm/-s
    promis: pRae/mi -> pmRwid
    promets: pRae/mie/-k -> pmRwied/-k
    procès: pRae/sie -> spRwied
    projet: pRae/vtie -> pvtRwied
    projets: pRae/vtie/-s -> pvtRwied/-s
    profiter: pRae/kpi/te/-l -> ptRied/-l
    promesse: pRae/mies -> pmRwiesd
    promis: pRae/mi -> pmRwid

## S028 (suffix) -- ture, tude, ·ature, ·iture, ·itude

- merged keys [19, 20, 21] = `-dtR` for ture, tude, ·ature, ·iture, ·itude (sim 0.765, comfort 610.7)
- strokeFreqSaved 1159.6, freqBenefiting 1013.0 of 1095.9 (share by freq 0.924, by count 0.908), boundary risks 0
- fallbacks: {'keyOverlap': 22}
- alternatives: merged [[19, 20, 21]] sim 0.765 saved 1159.6; merged [[20, 21]] sim 0.697 saved 1159.3; merged [[8, 19, 20]] sim 0.607 saved 1021.2; merged [[7, 20, 21]] sim 0.601 saved 1034.0; merged [[11, 20, 21]] sim 0.601 saved 956.8

    voiture: vwa/t@iR -> vwadtR
    habitude: a/svi/t@id -> a/svidtR
    nourriture: mR@e/Ri/t@iR -> mR@edtR
    voitures: vwa/t@iR/-s -> vwadtR/-s
    peinture: paie/t@iR -> paiedtR
    aventure: a/v@/t@iR -> a/v@dtR
    attitude: a/ti/t@id -> a/tidtR
    créature: kRe/a/t@iR -> kRedtR
    solitude: sae/mti/t@id -> sae/mtidtR
    ceinture: saie/t@iR -> saiedtR

## P032 (prefix) -- main

- merged keys [6] = `m-` for main (sim 0.667, comfort 275.9)
- strokeFreqSaved 1150.5, freqBenefiting 1150.5 of 1152.5 (share by freq 0.998, by count 0.881), boundary risks 14
- fallbacks: {'markCostTooHigh': 1, 'keyOverlap': 4}
- alternatives: merged [[6]] sim 0.667 saved 1150.5; merged [[6, 13]] sim 0.5 saved 1143.5; merged [[6, 14]] sim 0.5 saved 1143.5; merged [[6, 8]] sim 0.5 saved 1143.7; merged [[6, 9]] sim 0.5 saved 1143.7

    maintenant: maie/t@a/mR@ -> mt@a/mR@
    maintenant: maie/t@a/mR@ -> mt@a/mR@
    maintenir: maie/t@a/mRiR -> mt@a/mRiR
    maintenez: maie/t@a/mRe -> mt@a/mRe
    maintient: maie/tRw*aie -> mtRw*aie
    maintiens: maie/tRwaie/-k -> mtRwaie/-k
    maintenu: maie/t@a/mR@i -> mt@a/mR@i
    maintenue: maie/t@a/mR@i/-j -> mt@a/mR@i/-j
    maintenons: maie/t@a/mRai -> mt@a/mRai
    maintiennent: maie/tRwien/-st -> mtRwien/-st

## P008 (prefix) -- per, ser, inER·, éER·, cer, fer, ter, enER·, ver

- merged keys [3, 4, 8, 17] = `spR-s` for per, ser, cer (sim 0.645, comfort 568.8)
- merged keys [4, 7, 8, 17] = `ptR-s` for inER·, fer, ter (sim 0.645, comfort 568.8)
- merged keys [4, 8, 14, 17] = `pRes` for éER·, enER· (sim 0.645, comfort 568.8)
- merged keys [4, 5, 8, 17] = `pvR-s` for ver (sim 0.645, comfort 568.8)
- strokeFreqSaved 1129.7, freqBenefiting 1047.6 of 2451.1 (share by freq 0.427, by count 0.461), boundary risks 0
- fallbacks: {'keyOverlap': 559}
- alternatives: merged [[3, 4, 8, 17], [4, 7, 8, 17], [4, 8, 14, 17], [4, 5, 8, 17]] sim 0.645 saved 1129.7; merged [[2, 3, 4, 8], [2, 4, 7, 8], [2, 4, 8, 14], [2, 4, 5, 8]] sim 0.623 saved 1314.7; merged [[3, 4, 7, 8], [4, 7, 8, 20], [4, 7, 8, 14], [4, 5, 7, 8]] sim 0.622 saved 1072.0; merged [[3, 4, 8, 20], [4, 7, 8, 20], [4, 8, 14, 20], [4, 5, 8, 20]] sim 0.611 saved 1285.5; merged [[3, 4, 8, 11], [4, 7, 8, 11], [4, 8, 11, 14], [4, 5, 8, 11]] sim 0.604 saved 1229.4

    terminé: tieR/mi/mRe -> pmtRis/mRe
    servir: sieR/viR -> spvRisR
    certain: sieR/taie -> sptRaies
    cerveau: sieR/vae -> spvRaes
    fermer: kpieR/me/-l -> pmtRes/-l
    permettez: pieR/mie/te -> spmRies/te
    énergie: e/mRieR/vti -> pvtRies
    servi: sieR/vi -> spvRis
    fermé: kpieR/me -> pmtRes
    certaine: sieR/t*ien -> sptR*iesn

## P029 (prefix) -- imOR·, dor, emOR·, for, or

- merged keys [4, 5, 8, 9] = `pvRw-` for imOR· (sim 0.577, comfort 509.8)
- merged keys [4, 5, 8, 19] = `pvR-d` for dor, or (sim 0.577, comfort 509.8)
- merged keys [4, 5, 8, 11] = `pvR@` for emOR· (sim 0.577, comfort 509.8)
- merged keys [2, 4, 5, 8] = `kpvR-` for for (sim 0.577, comfort 509.8)
- strokeFreqSaved 1105.9, freqBenefiting 739.5 of 849.5 (share by freq 0.87, by count 0.667), boundary risks 0
- fallbacks: {'markCostTooHigh': 4, 'keyOverlap': 176}
- alternatives: merged [[4, 5, 8, 9], [4, 5, 8, 19], [4, 5, 8, 11], [2, 4, 5, 8]] sim 0.577 saved 1105.9; merged [[8, 9, 17, 19], [2, 8, 17, 19], [8, 11, 17, 19], [3, 8, 17, 19]] sim 0.545 saved 1180.0; merged [[8, 9, 19], [2, 8, 19], [8, 11, 19], [3, 8, 19]] sim 0.525 saved 1180.0; merged [[2, 4, 8, 9], [2, 4, 8, 19], [2, 4, 8, 11], [2, 3, 4, 8]] sim 0.514 saved 1106.3; merged [[8, 9, 14, 19], [2, 8, 14, 19], [8, 11, 14, 19], [3, 8, 14, 19]] sim 0.643 saved 911.3

    important: aie/peR/t@ -> pvtRw@
    dormir: pveR/miR -> pvmRidR
    dormi: pveR/mi -> pvmRid
    importante: aie/peR/t@t -> pvtRw@t
    fortune: kpeR/t@in -> kpvtR@in
    emporter: @/peR/te/-l -> pvtR@e/-l
    endormir: @/pveR/miR -> pvmR@iR
    dormais: pveR/mie/-k -> pvmRied/-k
    importantes: aie/peR/t@t/-s -> pvtRw@t/-s
    endormi: @/pveR/mi -> pvmR@i

## S007 (suffix) -- ner, nant, nner, née, né, net, nais, nnant, nné

- merged keys [14, 22, 23] = `enl` for ner, nner, née, né, nné (sim 0.5, comfort 428.2)
- merged keys [11, 22, 23] = `@nl` for nant, net, nais, nnant (sim 0.5, comfort 428.2)
- strokeFreqSaved 1102.7, freqBenefiting 1102.7 of 3188.3 (share by freq 0.346, by count 0.457), boundary risks 164
- fallbacks: {'keyOverlap': 1570, 'markCostTooHigh': 10}
- alternatives: merged [[14, 22, 23], [11, 22, 23]] sim 0.5 saved 1102.7; merged [[14, 20, 22], [11, 20, 22]] sim 0.5 saved 1109.2; merged [[8, 14, 22], [8, 11, 22]] sim 0.5 saved 1063.6; merged [[9, 14, 22], [9, 11, 22]] sim 0.5 saved 1066.0; merged [[5, 14, 22], [5, 11, 22]] sim 0.5 saved 895.7

    terminé: tieR/mi/mRe -> tieR/mienl
    emmener: @/m@a/mRe/-l -> @/m@aenl/-l
    ramener: Ra/m@a/mRe/-l -> Ra/m@aenl/-l
    emmenez: @/m@a/mRe/-k -> @/m@aenl/-k
    imaginer: i/ma/vti/mRe/-l -> i/ma/vtienl/-l
    amener: a/m@a/mRe/-l -> a/m@aenl/-l
    ramené: Ra/m@a/mRe -> Ra/m@aenl
    imaginez: i/ma/vti/mRe/-k -> i/ma/vtienl/-k
    emmené: @/m@a/mRe -> @/m@aenl
    amenez: a/m@a/mRe/-k -> a/m@aenl/-k

## P025 (prefix) -- trou, tra, trom, trahi·, tri

- merged keys [7, 8, 13] = `tRi` for trou, tra, trom, trahi·, tri (sim 0.801, comfort 421.8)
- strokeFreqSaved 1090.6, freqBenefiting 1082.4 of 1357.5 (share by freq 0.797, by count 0.633), boundary risks 0
- fallbacks: {'keyOverlap': 134, 'markCostTooHigh': 12}
- alternatives: merged [[7, 8, 12]] sim 0.811 saved 1128.6; merged [[7, 8, 13]] sim 0.801 saved 1090.6; merged [[7, 8]] sim 0.793 saved 1318.4; merged [[3, 7, 8]] sim 0.694 saved 1304.6; merged [[4, 7, 8]] sim 0.694 saved 1155.5

    trouvé: tR@e/ve -> vtRie
    trouver: tR@e/ve/-l -> vtRie/-l
    trouvez: tR@e/ve/-k -> vtRie/-k
    trouvée: tR@e/ve/-j -> vtRie/-j
    trompé: tRai/pe -> ptRie
    trouvera: tR@e/v@a/Ra -> vtR@ai/Ra
    tromper: tRai/pe/-l -> ptRie/-l
    trouverai: tR@e/v@a/Re/-t -> vtR@ai/Re/-t
    trouveras: tR@e/v@a/Ra/-d -> vtR@ai/Ra/-d
    trouverez: tR@e/v@a/Re/-d -> vtR@ai/Re/-d

## P039+P054+P134 (prefix) -- fa, fai·, féi·, fi, fê, fé, fen

- merged keys [2, 4, 14] = `kpe` for fa, fai·, féi·, fi, fê, fé, fen (sim 0.622, comfort 445.0)
- strokeFreqSaved 1082.7, freqBenefiting 980.4 of 1257.8 (share by freq 0.779, by count 0.447), boundary risks 1
- fallbacks: {'keyOverlap': 232, 'markCostTooHigh': 2}
- alternatives: merged [[2, 4, 14]] sim 0.622 saved 1082.7; merged [[2, 4, 11]] sim 0.604 saved 1145.5; merged [[2, 4]] sim 0.604 saved 1187.5; merged [[2, 4, 12]] sim 0.722 saved 923.9; merged [[2, 4, 13]] sim 0.663 saved 128.2

    famille: kpa/mij -> kpmiej
    façon: kpa/sai -> kspaie
    facile: kpa/sil -> kspiel
    félicitations: kpe/mti/si/ta/sRwai/-s -> kspie/ta/sRwai/-s
    familles: kpa/mij/-s -> kpmiej/-s
    finie: kpi/mRi/-j -> kpmRie/-j
    façons: kpa/sai/-s -> kspaie/-s
    fascinant: kpa/si/mR@ -> kpmR@e
    fabrique: kpa/svRik -> kspvRiek
    féliciter: kpe/mti/si/te/-l -> kspie/te/-l

## S032 (suffix) -- tique, fique, nique, gique, lique, mique, sque, rique, trique, sique

- merged keys [18, 20, 22] = `-ktn` for tique, fique, nique, gique, lique, mique, sque, rique, trique, sique, dique (sim 0.627, comfort 489.5)
- strokeFreqSaved 1042.8, freqBenefiting 1042.8 of 1113.8 (share by freq 0.936, by count 0.94), boundary risks 0
- fallbacks: {'keyOverlap': 80, 'markCostTooHigh': 7, 'illegalChord': 4}
- alternatives: merged [[18, 20, 22]] sim 0.627 saved 1042.8; merged [[18, 20, 21]] sim 0.618 saved 968.7; merged [[18, 20, 24]] sim 0.612 saved 1041.1; merged [[18, 20, 23]] sim 0.606 saved 1041.1; merged [[18, 20, 25]] sim 0.605 saved 1042.8

    magnifique: ma/wi/kpik -> ma/wiktn
    lorsque: mteR/ks@a -> mtektRn
    politique: pae/mti/tik -> pae/mtiktn
    politique: pae/mti/tik -> pae/mtiktn
    fantastique: kp@/tas/tik -> kp@/tasktn
    boutique: sv@e/tik -> sv@ektn
    romantique: Rae/m@/tik -> Rae/m@ktn
    clinique: kmti/mRik -> kmtiktn
    physique: kpi/twik -> kpiktn
    scientifique: sRw@/ti/kpik -> sRw@/tiktn

## P028 (prefix) -- sor, sur, suOR·

- merged keys [3, 8, 9] = `sRw-` for sor, sur (sim 0.793, comfort 523.9)
- merged keys [3, 8, 14] = `sRe` for suOR· (sim 0.793, comfort 523.9)
- strokeFreqSaved 1035.0, freqBenefiting 1022.0 of 1235.2 (share by freq 0.827, by count 0.65), boundary risks 22
- fallbacks: {'keyOverlap': 259}
- alternatives: merged [[3, 8, 9], [3, 8, 14]] sim 0.793 saved 1035.0; merged [[3, 6, 8, 9], [3, 6, 8, 14]] sim 0.694 saved 1015.1; merged [[2, 3, 8, 9], [2, 3, 8, 14]] sim 0.694 saved 1010.7; merged [[2, 3, 8, 9], [3, 8, 9, 14]] sim 0.694 saved 1010.7; merged [[3, 8, 9, 12], [3, 8, 12, 14]] sim 0.694 saved 941.8

    sortir: seR/tiR -> stRwiR
    surtout: s@iR/t@e -> stRw@e
    sortez: seR/te -> stRwe
    sorti: seR/t*i -> stRw*i
    sortie: seR/ti/-j -> stRwi/-j
    surveiller: s@iR/vie/Rwe/-l -> svRwie/Rwe/-l
    surveille: s@iR/viej -> svRwiej
    survivre: s@iR/vijsR -> svRwijsR
    surface: s@iR/kpas -> kspRwas
    survécu: s@iR/ve/k@i -> svRwe/k@i

## S012 (suffix) -- ver, vé, vent, vant, vée

- merged keys [9, 14, 16, 17] = `wejs` for ver, vé, vée (sim 0.5, comfort 446.4)
- merged keys [9, 11, 16, 17] = `w@js` for vent, vant (sim 0.5, comfort 446.4)
- strokeFreqSaved 1007.0, freqBenefiting 1007.0 of 2554.8 (share by freq 0.394, by count 0.714), boundary risks 0
- fallbacks: {'keyOverlap': 177}
- alternatives: merged [[9, 14, 16, 17], [9, 11, 16, 17]] sim 0.5 saved 1007.0; merged [[14, 16, 17, 19], [11, 16, 17, 19]] sim 0.5 saved 1007.0; merged [[2, 14, 16, 17], [2, 11, 16, 17]] sim 0.5 saved 941.7; merged [[5, 14, 16, 17], [5, 11, 16, 17]] sim 0.5 saved 989.3; merged [[6, 14, 16, 17], [6, 11, 16, 17]] sim 0.5 saved 773.0

    arrivé: a/Ri/v*e -> a/Rw*iejs
    arriver: a/Ri/ve/-l -> a/Rwiejs/-l
    arrivé: a/Ri/v*e -> a/Rw*iejs
    enlever: @/mt@a/ve/-l -> @/mtw@aejs/-l
    arrivée: a/Ri/ve -> a/Rwiejs
    arrivée: a/Ri/ve/-j -> a/Rwiejs/-j
    arrivés: a/Ri/ve/-s -> a/Rwiejs/-s
    crever: kR@a/ve/-l -> kRw@aejs/-l
    enlevé: @/mt@a/ve -> @/mtw@aejs
    enlevez: @/mt@a/ve/-k -> @/mtw@aejs/-k

## S036 (suffix) -- ·°nir, nir

- merged keys [21, 22] = `-Rn` for ·°nir, nir (sim 0.723, comfort 512.9)
- strokeFreqSaved 933.2, freqBenefiting 751.8 of 836.0 (share by freq 0.899, by count 0.68), boundary risks 1
- fallbacks: {'keyOverlap': 67, 'markCostTooHigh': 16}
- alternatives: merged [[21, 22]] sim 0.723 saved 933.2; merged [[20, 21, 22]] sim 0.632 saved 933.2; merged [[19, 21, 22]] sim 0.632 saved 933.2; merged [[4, 21, 22]] sim 0.632 saved 790.1; merged [[21, 22, 23]] sim 0.632 saved 933.2

    devenir: pv@a/v@a/mRiR -> pv@a/v@aRn
    revenir: R@a/v@a/mRiR -> R@a/v@aRn
    maintenant: maie/t@a/mR@ -> maieRn/mR@
    avenir: a/v@a/mRiR -> a/v@aRn
    prévenir: pRie/v@a/mRiR -> pRieRn
    obtenir: ejk/t@a/mRiR -> ejk/t@aRn
    souvenez: s@e/v@a/mRe -> s@eRn/mRe
    souvenirs: s@e/v@a/mRiR/-s -> s@eRn/-s
    souvenir: s@e/v@a/mRiR -> s@eRn
    souvenir: s@e/v@a/mRiR -> s@eRn

## S030 (suffix) -- ·ailler, ·ajer, ·Eller, ·aner, ·aller

- merged keys [14, 16, 17, 22] = `ejsn` for ·ailler, ·aner (sim 0.577, comfort 621.1)
- merged keys [14, 16, 18, 22] = `ejkn` for ·ajer (sim 0.577, comfort 621.1)
- merged keys [14, 16, 19, 22] = `ejdn` for ·Eller (sim 0.577, comfort 621.1)
- merged keys [14, 16, 22, 23] = `ejnl` for ·aller (sim 0.577, comfort 621.1)
- strokeFreqSaved 903.1, freqBenefiting 493.4 of 628.6 (share by freq 0.785, by count 0.468), boundary risks 0
- fallbacks: {'keyOverlap': 495}
- alternatives: merged [[14, 16, 17, 22], [14, 16, 18, 22], [14, 16, 19, 22], [14, 16, 22, 23]] sim 0.577 saved 903.1; merged [[14, 16, 22, 23], [14, 16, 17, 23], [14, 16, 18, 23], [14, 16, 19, 23]] sim 0.573 saved 901.9; merged [[14, 16, 22], [14, 16, 17], [14, 16, 18], [14, 16, 23]] sim 0.525 saved 903.1; merged [[16, 17, 22, 23], [16, 18, 22, 23], [16, 19, 22, 23], [16, 20, 22, 23]] sim 0.5 saved 1045.7; merged [[13, 14, 16, 22], [13, 14, 16, 17], [13, 14, 16, 18], [13, 14, 16, 23]] sim 0.545 saved 613.8

    travailler: tRa/va/Rwe/-l -> tRaejsn/-l
    travaillé: tRa/va/Rwe -> tRaejsn
    surveiller: s@iR/vie/Rwe/-l -> s@iejdRn/-l
    travaillait: tRa/va/Rwie -> tRaejsn/Rwie
    travaillez: tRa/va/Rwe/-k -> tRaejsn/-k
    condamné: kai/pva/mRe -> kaiejsn
    renvoyer: R@/vwaj/e/-l -> R@ejkn/-l
    conseiller: kai/sie/Rwe -> kaiejdn
    travaillais: tRa/va/Rwie/-k -> tRaejsn/Rwie/-k
    renvoyé: R@/vwaj/e -> R@ejkn

## S040 (suffix) -- ·onnel, nal, nel, nnel, ·inel, ·inal, ·onal

- merged keys [9, 22, 23] = `w-nl` for ·onnel, nal, nel, nnel, ·inel, ·inal, ·onal (sim 0.636, comfort 571.6)
- strokeFreqSaved 887.9, freqBenefiting 602.8 of 649.6 (share by freq 0.928, by count 0.832), boundary risks 12
- fallbacks: {'keyOverlap': 85, 'markCostTooHigh': 4}
- alternatives: merged [[22, 23]] sim 0.727 saved 934.1; merged [[11, 22, 23]] sim 0.636 saved 797.6; merged [[20, 22, 23]] sim 0.636 saved 934.1; merged [[9, 22, 23]] sim 0.636 saved 887.9; merged [[5, 22, 23]] sim 0.636 saved 778.7

    colonel: kae/mtae/mRiel -> kae/mtwaenl
    journal: vt@eR/mRal -> vtw@eRnl
    tribunal: tRi/sv@i/mRal -> tRi/svw@inl
    personnel: pieR/sae/mRiel -> pwieRnl
    personnel: pieR/sae/mRiel -> pwieRnl
    criminel: kRi/mi/mRiel -> kRwinl
    personnelle: pieR/sae/mRiel/-j -> pwieRnl/-j
    éternel: e/tieR/mRiel -> e/twieRnl
    criminels: kRi/mi/mRiel/-s -> kRwinl/-s
    éternelle: e/tieR/mRiel/-j -> e/twieRnl/-j

## S019 (suffix) -- ·[ble|bre|ne|ni|nie|nne|si|ta|ti|tre]ment, ·[ffle|fle|gle|me|pre|que|se|tru|voue]ment

- dedicated keys [20, 22, 23] = `-tnl` for ·[ble|bre|ne|ni|nie|nne|si|ta|ti|tre]ment, ·[ffle|fle|gle|me|pre|que|se|tru|voue]ment (sim 0.292, comfort 252.0)
- strokeFreqSaved 856.2, freqBenefiting 856.2 of 856.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[20, 22, 23]] sim 0.292 saved 856.2; dedicated [[21, 22, 23]] sim 0.292 saved 856.2; dedicated [[3, 5, 6, 7, 8, 11, 12]] sim 0.277 saved 856.2; dedicated [[16, 22, 23]] sim 0.271 saved 856.2; dedicated [[2, 3, 6, 7, 8, 11, 12]] sim 0.259 saved 856.2

    probablement: pRae/sva/svmt@a/m@ -> pRae/sva/-tnl
    gouvernement: ks@e/vieR/mR@a/m@ -> ks@e/vieR/-tnl
    certainement: sieR/tie/mR@a/m@ -> sieR/tie/-tnl
    autrement: ae/tR@a/m@ -> ae/-tnl
    sentiments: s@/ti/m@/-s -> s@/-tnl/-s
    sentiment: s@/ti/m@ -> s@/-tnl
    bâtiment: sva/ti/m@ -> sva/-tnl
    uniquement: @i/mRi/k@a/m@ -> @i/mRi/-tnl
    entraînement: @/tRie/mR@a/m@ -> @/tRie/-tnl
    règlement: Rie/ksmt@a/m@ -> Rie/-tnl

## S031+S092 (suffix) -- ·iser, sin, sé, sine, sant, sie, ·isan

- merged keys [13, 22, 23] = `inl` for ·iser, sin, sé, sine, sant, sie, ·isan (sim 0.662, comfort 435.3)
- strokeFreqSaved 840.0, freqBenefiting 568.4 of 994.4 (share by freq 0.572, by count 0.71), boundary risks 94
- fallbacks: {'keyOverlap': 743, 'markCostTooHigh': 63}
- alternatives: merged [[14, 22, 23]] sim 0.655 saved 1071.4; merged [[11, 22, 23]] sim 0.572 saved 1163.8; merged [[13, 22, 23]] sim 0.662 saved 840.0

    magasin: ma/ksa/twaie -> ma/ksainl
    cousin: k@e/twaie -> k@ienl
    voisins: vwa/twaie/-s -> vwainl/-s
    réalisé: Re/a/mti/twe -> Re/ainl
    voisin: vwa/twaie -> vwainl
    poésie: pae/e/twi -> pae/ienl
    réaliser: Re/a/mti/twe/-l -> Re/ainl/-l
    organiser: eR/ksa/mRi/twe/-l -> eR/ksainl/-l
    jalousie: vta/mt@e/twi -> vta/mt@ienl
    cousins: k@e/twaie/-s -> k@ienl/-s

## S021 (suffix) -- ·[cra|llu|lu|mi|ra|rra|ten|tten|tua]tion

- dedicated keys [3, 6, 7, 8, 9, 11, 12, 13] = `smtRw@ai` for ·[cra|llu|lu|mi|ra|rra|ten|tten|tua]tion (sim 0.346, comfort 517.0)
- strokeFreqSaved 822.4, freqBenefiting 822.4 of 822.4 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[3, 6, 7, 8, 9, 11, 12, 13]] sim 0.346 saved 822.4; dedicated [[2, 6, 7, 8, 11, 12, 13]] sim 0.308 saved 822.4; dedicated [[6, 7, 8, 11, 12, 13]] sim 0.269 saved 822.4; dedicated [[3, 7, 8, 9, 11, 12, 13]] sim 0.269 saved 822.4; dedicated [[16, 17, 18]] sim 0.231 saved 822.4

    attention: a/t@/sRwai -> a/smtRw@ai
    attention: a/t@/sRwai -> a/smtRw@ai
    situation: si/t@a/sRwai -> si/smtRw@ai
    solution: sae/mt@i/sRwai -> sae/smtRw@ai
    opération: ae/pe/Ra/sRwai -> ae/pe/smtRw@ai
    intention: aie/t@/sRwai -> aie/smtRw@ai
    révolution: Re/vae/mt@i/sRwai -> Re/vae/smtRw@ai
    déclaration: pve/kmta/Ra/sRwai -> pve/kmta/smtRw@ai
    génération: vte/mRe/Ra/sRwai -> vte/mRe/smtRw@ai
    opérations: ae/pe/Ra/sRwai/-s -> ae/pe/smtRw@ai/-s

## S026+S064 (suffix) -- ·[ber|cié|cu|ffron|fron|li|lli|nau|ni|nni|ti|tié]té, ·[a|bi|cia|gi|na|nna|ri|ti|tia|va]lité

- dedicated keys [16, 17, 19] = `-jsd` for ·[ber|cié|cu|ffron|fron|li|lli|nau|ni|nni|ti|tié]té, ·[a|bi|cia|gi|na|nna|ri|ti|tia|va]lité (sim 0.273, comfort 234.0)
- strokeFreqSaved 820.4, freqBenefiting 649.1 of 649.1 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 17, 18]] sim 0.273 saved 820.4; dedicated [[16, 17, 19]] sim 0.273 saved 820.4; dedicated [[16, 17, 20]] sim 0.273 saved 820.4; dedicated [[16, 17, 21]] sim 0.273 saved 820.4; dedicated [[16, 17, 22]] sim 0.273 saved 820.4

    liberté: mti/svieR/te -> mti/-jsd
    société: sae/sRwe/te -> sae/-jsd
    réalité: Re/a/mti/te -> Re/-jsd
    identité: i/pv@/ti/te -> i/pv@/-jsd
    unité: @i/mRi/te -> @i/-jsd
    responsabilité: Ries/pai/sa/svi/mti/te -> Ries/pai/sa/-jsd
    humanité: @i/ma/mRi/te -> @i/ma/-jsd
    communauté: kae/m@i/mRae/te -> kae/m@i/-jsd
    qualité: ka/mti/te -> ka/-jsd
    éternité: e/tieR/mRi/te -> e/tieR/-jsd

## P006 (prefix) -- aE·, ao·, a@·, ae·, auo·, au·, au@·

- dedicated keys [11, 12] = `@a` for aE·, ao·, a@·, ae·, auo·, au·, au@· (sim 0.29, comfort 127.0)
- strokeFreqSaved 818.4, freqBenefiting 818.4 of 1708.2 (share by freq 0.479, by count 0.637), boundary risks 4
- fallbacks: {'markCostTooHigh': 621, 'lostDistinction': 6}
- alternatives: dedicated [[11, 12]] sim 0.29 saved 818.4; dedicated [[8, 11, 12]] sim 0.028 saved 735.5; dedicated [[5, 8, 12, 13, 14]] sim -0.093 saved 818.4; dedicated [[5, 8, 11, 12, 14]] sim -0.105 saved 818.4; dedicated [[7, 8, 11, 12, 14]] sim -0.105 saved 818.4

    avocat: a/vae/ka -> @a/ka
    agréable: a/ksRe/ajl -> @a/ajl
    américain: a/me/Ri/kaie -> @a/Ri/kaie
    abandonner: a/sv@/pvae/mRe/-l -> @a/pvae/mRe/-l
    américains: a/me/Ri/kaie/-s -> @a/Ri/kaie/-s
    abandonne: a/sv@/pven -> @a/pven
    adorable: a/pvae/Rajl -> @a/Rajl
    abandonné: a/sv@/pvae/mRe -> @a/pvae/mRe
    autorité: ae/tae/Ri/te -> @a/Ri/te
    américaine: a/me/Ri/kien -> @a/Ri/kien

## P040 (prefix) -- be, ban, bé

- merged keys [3, 5, 11] = `sv@` for be, ban, bé (sim 0.675, comfort 463.6)
- strokeFreqSaved 807.9, freqBenefiting 807.9 of 848.6 (share by freq 0.952, by count 0.609), boundary risks 0
- fallbacks: {'keyOverlap': 61}
- alternatives: merged [[3, 5, 11]] sim 0.675 saved 807.9; merged [[3, 5]] sim 0.667 saved 816.5; merged [[2, 3, 5]] sim 0.5 saved 803.2; merged [[3, 5, 17]] sim 0.5 saved 814.6; merged [[3, 5, 16]] sim 0.5 saved 814.7

    besoin: sv@a/twaie -> svtw@aie
    besoins: sv@a/twaie/-s -> svtw@aie/-s
    béton: sve/tai -> svt@ai
    bénie: sve/mRi/-j -> svmR@i/-j
    banquet: sv@/kie -> ksv@ie
    bétel: sve/tiel -> svt@iel
    banquette: sv@/kiet -> ksv@iet
    belette: sv@a/mtiet -> svmt@iet
    béquilles: sve/kij/-s -> ksv@ij/-s
    bécasse: sve/kas -> ksv@as

## P049 (prefix) -- res, respec

- merged keys [2, 3, 8, 9] = `ksRw-` for res (sim 0.773, comfort 525.4)
- merged keys [2, 3, 4, 8] = `kspR-` for respec (sim 0.773, comfort 525.4)
- strokeFreqSaved 748.7, freqBenefiting 702.4 of 710.9 (share by freq 0.988, by count 0.584), boundary risks 0
- fallbacks: {'keyOverlap': 52}
- alternatives: merged [[2, 3, 8, 9], [2, 3, 4, 8]] sim 0.773 saved 748.7; merged [[3, 4, 8, 9], [2, 3, 4, 8]] sim 0.773 saved 721.2; merged [[3, 8, 9, 18], [2, 3, 8, 18]] sim 0.751 saved 751.5; merged [[3, 8, 9], [2, 3, 8]] sim 0.728 saved 751.5; merged [[3, 5, 8, 9], [2, 3, 5, 8]] sim 0.637 saved 751.5

    rester: Ries/te/-l -> kstRwe/-l
    restez: Ries/te/-k -> kstRwe/-k
    resté: Ries/te -> kstRwe
    respire: Ries/piR -> kspRwiR
    restera: Ries/t@a/Ra -> kstRw@a/Ra
    restée: Ries/te/-j -> kstRwe/-j
    restait: Ries/tie -> kstRwie
    respecter: Ries/piek/te/-l -> ksptRe/-l
    restons: Ries/tai -> kstRwai
    resterai: Ries/t@a/Re/-t -> kstRw@a/Re/-t

## S044 (suffix) -- voir, rir, vir, vrir, rrir

- merged keys [13, 16, 21] = `ijR` for voir, rir, vir, vrir, rrir (sim 0.628, comfort 522.0)
- strokeFreqSaved 737.0, freqBenefiting 737.0 of 840.7 (share by freq 0.877, by count 0.764), boundary risks 1
- fallbacks: {'keyOverlap': 21}
- alternatives: merged [[5, 16, 21]] sim 0.682 saved 755.9; merged [[13, 16, 21]] sim 0.628 saved 737.0; merged [[12, 16, 21]] sim 0.608 saved 698.4; merged [[5, 9, 21]] sim 0.601 saved 755.9

    mourir: m@e/RiR -> m@iejR
    pouvoir: p@e/vwaR -> p@iejR
    pouvoir: p@e/vwaR -> p@iejR
    courir: k@e/RiR -> k@iejR
    recevoir: R@a/s@a/vwaR -> R@a/s@aijR
    découvrir: pve/k@e/vRiR -> pve/k@iejR
    pouvoirs: p@e/vwaR/-s -> p@iejR/-s
    nourrir: mR@e/RiR -> mR@iejR
    couvrir: k@e/vRiR -> k@iejR
    guérir: kse/RiR -> ksiejR

## S041 (suffix) -- rie, ·°rie, ri

- merged keys [13, 21, 23] = `iRl` for rie, ·°rie, ri (sim 0.596, comfort 483.7)
- strokeFreqSaved 736.3, freqBenefiting 629.6 of 733.3 (share by freq 0.859, by count 0.625), boundary risks 7
- fallbacks: {'keyOverlap': 250}
- alternatives: merged [[13, 20, 21]] sim 0.596 saved 722.9; merged [[13, 21, 23]] sim 0.596 saved 736.3; merged [[13, 19, 21]] sim 0.596 saved 722.9; merged [[9, 13, 21]] sim 0.596 saved 686.6

    chérie: pme/Ri/-j -> pmieRl/-j
    conneries: ke/mR@a/Ri/-s -> ke/mR@aiRl/-s
    chéri: pme/Ri -> pmieRl
    chérie: pme/Ri/-j -> pmieRl/-j
    chéri: pme/Ri -> pmieRl
    théorie: te/ae/Ri -> te/aieRl
    connerie: ke/mR@a/Ri -> ke/mR@aiRl
    saloperie: sa/mte/p@a/Ri -> sa/mtieRl
    galerie: ksa/mt@a/Ri -> ksa/mt@aiRl
    mairie: me/Ri -> mieRl

## S034+S057 (suffix) -- ·[bai|bou|li|lli|ly|su|xcu]sez, ·[a|ca|co|cu|na|nna|ra|ti]liser

- dedicated keys [16, 22, 23] = `-jnl` for ·[bai|bou|li|lli|ly|su|xcu]sez, ·[a|ca|co|cu|na|nna|ra|ti]liser (sim 0.281, comfort 270.0)
- strokeFreqSaved 735.1, freqBenefiting 530.3 of 530.6 (share by freq 0.999, by count 0.99), boundary risks 0
- fallbacks: {'markCostTooHigh': 5}
- alternatives: dedicated [[16, 22, 23]] sim 0.281 saved 735.1; dedicated [[17, 22, 23]] sim 0.281 saved 735.1; dedicated [[18, 22, 23]] sim 0.281 saved 735.1; dedicated [[16, 17, 18]] sim 0.251 saved 735.1; dedicated [[16, 17, 23]] sim 0.251 saved 735.1

    excusez: ie/ks@i/twe/-k -> ie/-jnl/-k
    utiliser: @i/ti/mti/twe/-l -> @i/-jnl/-l
    excuser: ie/ks@i/twe/-l -> ie/-jnl/-l
    utilisé: @i/ti/mti/twe -> @i/-jnl
    réalisé: Re/a/mti/twe -> Re/-jnl
    réaliser: Re/a/mti/twe/-l -> Re/-jnl/-l
    utilisez: @i/ti/mti/twe/-k -> @i/-jnl/-k
    localiser: mtae/ka/mti/twe/-l -> mtae/-jnl/-l
    analyser: a/mRa/mti/twe/-l -> a/-jnl/-l
    utilisée: @i/ti/mti/twe/-j -> @i/-jnl/-j

## P035 (prefix) -- man, mé, men, me

- merged keys [6, 9, 11] = `mw@` for man, mé, men, me (sim 0.599, comfort 495.9)
- strokeFreqSaved 708.6, freqBenefiting 708.6 of 1024.6 (share by freq 0.692, by count 0.569), boundary risks 0
- fallbacks: {'keyOverlap': 208}
- alternatives: merged [[3, 6, 11]] sim 0.599 saved 671.2; merged [[6, 9, 11]] sim 0.599 saved 708.6; merged [[6, 11, 16]] sim 0.599 saved 743.1

    manger: m@/vte/-l -> vmtw@e/-l
    mangé: m@/vte -> vmtw@e
    menti: m@/ti -> mtw@i
    mérite: me/Rit -> mRw@it
    manqué: m@/ke -> kmw@e
    mentir: m@/tiR -> mtw@iR
    mensonge: m@/saiZ -> smw@aiZ
    mensonges: m@/saiZ/-s -> smw@aiZ/-s
    mandat: m@/pva -> pvmw@a
    mangez: m@/vte/-k -> vmtw@e/-k

## P051 (prefix) -- es, esa·, eso·

- merged keys [3] = `s-` for es, esa·, eso· (sim 0.6, comfort 467.6)
- strokeFreqSaved 690.5, freqBenefiting 575.2 of 579.8 (share by freq 0.992, by count 0.848), boundary risks 19
- fallbacks: {'markCostTooHigh': 17, 'keyOverlap': 15}
- alternatives: merged [[3]] sim 0.6 saved 690.5; merged [[3, 12]] sim 0.638 saved 511.9; merged [[3, 13, 14]] sim 0.75 saved 129.4; merged [[3, 12, 14]] sim 0.65 saved 12.4

    espère: ies/pieR -> spieR
    espèce: ies/pies -> spies
    espoir: ies/pwaR -> spwaR
    estomac: ies/tae/ma -> sma
    escalier: ies/ka/mtRwe -> smtRwe
    espion: ies/pRwai -> spRwai
    espagnol: ies/pa/wel -> swel
    espèces: ies/pies/-s -> spies/-s
    escaliers: ies/ka/mtRwe/-s -> smtRwe/-s
    espagnol: ies/pa/wel -> swel

## P046 (prefix) -- tée·, rée·, fée·

- merged keys [7, 21] = `t-R` for tée·, rée·, fée· (sim 0.535, comfort 552.7)
- strokeFreqSaved 675.7, freqBenefiting 337.9 of 395.4 (share by freq 0.855, by count 0.656), boundary risks 13
- fallbacks: {'keyOverlap': 95, 'markCostTooHigh': 3}
- alternatives: merged [[7, 8]] sim 0.623 saved 606.0; merged [[7, 21]] sim 0.535 saved 675.7; merged [[7, 14, 21]] sim 0.702 saved 245.2; merged [[8, 14, 20]] sim 0.566 saved 203.9; merged [[7, 8, 14]] sim 0.789 saved 179.2

    téléphone: te/mte/kpen -> kpteRn
    réfléchi: Re/kpmte/pmi -> pmtiR
    télévision: te/mte/vi/tRwai -> vtiR/tRwai
    téléphoné: te/mte/kpae/mRe -> kptaeR/mRe
    réfléchis: Re/kpmte/pmi/-s -> pmtiR/-s
    télégramme: te/mte/ksRam -> kstRaRm
    téléphone: te/mte/kpen -> kpteRn
    fédéral: kpe/pve/Ral -> tRaRl
    téléphonique: te/mte/kpae/mRik -> kptaeR/mRik
    téléphones: te/mte/kpen/-s -> kpteRn/-s

## P038 (prefix) -- pa

- merged keys [4, 6] = `pm-` for pa (sim 0.5, comfort 366.5)
- strokeFreqSaved 675.1, freqBenefiting 675.1 of 876.7 (share by freq 0.77, by count 0.558), boundary risks 7
- fallbacks: {'keyOverlap': 119, 'markCostTooHigh': 15}
- alternatives: merged [[4, 6]] sim 0.5 saved 675.1; merged [[4, 5]] sim 0.5 saved 734.9; merged [[2, 4]] sim 0.5 saved 690.7; merged [[4, 9]] sim 0.5 saved 708.9

    parents: pa/R@/-s -> pmR@/-s
    patron: pa/tRai -> pmtRai
    parole: pa/Rel -> pmRel
    parie: pa/R*i -> pmR*i
    paquet: pa/kie -> kpmie
    paradis: pa/Ra/pvi -> pmRa/pvi
    paroles: pa/Rel/-s -> pmRel/-s
    patrie: pa/tRi -> pmtRi
    paris: pa/Ri/-s -> pmRi/-s
    patronne: pa/tRen -> pmtRen

## S024 (suffix) -- tir, tie, time, ti, tive

- merged keys [8, 20, 21, 25] = `R-tRm` for tir, tive (sim 0.62, comfort 676.9)
- merged keys [8, 16, 20, 25] = `R-jtm` for tie, ti (sim 0.62, comfort 676.9)
- merged keys [6, 8, 20, 25] = `mR-tm` for time (sim 0.62, comfort 676.9)
- strokeFreqSaved 660.3, freqBenefiting 660.3 of 1470.3 (share by freq 0.449, by count 0.707), boundary risks 0
- fallbacks: {'keyOverlap': 101}
- alternatives: merged [[8, 20, 21, 25], [8, 16, 20, 25], [6, 8, 20, 25]] sim 0.62 saved 660.3; merged [[6, 8, 20, 21], [6, 8, 16, 20], [6, 8, 20, 25]] sim 0.6 saved 597.1; merged [[13, 20, 21, 25], [13, 16, 20, 25], [6, 13, 20, 25]] sim 0.6 saved 520.6; merged [[5, 8, 20, 21], [5, 8, 16, 20], [5, 8, 20, 25]] sim 0.592 saved 516.4; merged [[8, 13, 20, 21], [8, 13, 16, 20], [8, 13, 20, 25]] sim 0.692 saved 480.9

    partie: paR/ti -> pRajtRm
    victime: vik/tim -> vmRiktm
    sentir: s@/tiR -> sR@tRm
    sortie: seR/ti -> sRejtRm
    parti: paR/t*i -> pR*ajtRm
    victimes: vik/tim/-s -> vmRiktm/-s
    mentir: m@/tiR -> mR@tRm
    détective: pve/tiek/tijs -> pve/tRiektRm
    tentative: t@/ta/tijs -> t@/tRatRm
    parties: paR/ti/-s -> pRajtRm/-s

## S025 (suffix) -- ·[chan|ci|jes|lon|nus|ri|rrê|ry|si|ssi]té

- dedicated keys [4, 5, 6, 7, 11, 13, 14, 17] = `pvmt@ies` for ·[chan|ci|jes|lon|nus|ri|rrê|ry|si|ssi]té (sim 0.327, comfort 517.0)
- strokeFreqSaved 657.6, freqBenefiting 657.6 of 657.6 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[4, 5, 6, 7, 11, 13, 14, 17]] sim 0.327 saved 657.6; dedicated [[5, 6, 7, 12, 13, 14, 17]] sim 0.269 saved 657.6; dedicated [[5, 7, 8, 13, 14, 17]] sim 0.25 saved 657.6; dedicated [[17, 20, 21]] sim 0.231 saved 657.6; dedicated [[17, 20, 22]] sim 0.231 saved 657.6

    vérité: ve/Ri/te -> ve/pvmt@ies
    sécurité: se/k@i/Ri/te -> se/k@i/pvmt@ies
    volonté: vae/mtai/te -> vae/pvmt@ies
    majesté: ma/vties/te -> ma/pvmt@ies
    université: @i/mRi/vieR/si/te -> @i/mRi/vieR/pvmt@ies
    enchanté: @/pm@/te -> @/pvmt@ies
    enchantée: @/pm@/te/-j -> @/pvmt@ies/-j
    autorité: ae/tae/Ri/te -> ae/tae/pvmt@ies
    électricité: e/mtiek/tRi/si/te -> e/mtiek/tRi/pvmt@ies
    autorités: ae/tae/Ri/te/-s -> ae/tae/pvmt@ies/-s

## S050 (suffix) -- ·ilité, ·alité, ·icité

- merged keys [17, 20, 23] = `-stl` for ·ilité, ·alité, ·icité (sim 0.634, comfort 570.7)
- strokeFreqSaved 656.6, freqBenefiting 219.0 of 223.6 (share by freq 0.979, by count 0.955), boundary risks 0
- fallbacks: {'keyOverlap': 22}
- alternatives: merged [[17, 20, 23]] sim 0.634 saved 656.6; merged [[20, 23]] sim 0.594 saved 670.4; merged [[20, 22, 23]] sim 0.515 saved 670.4; merged [[20, 21, 23]] sim 0.515 saved 623.7; merged [[18, 20, 23]] sim 0.515 saved 619.8

    responsabilité: Ries/pai/sa/svi/mti/te -> Ries/pai/sastl
    possibilité: pae/si/svi/mti/te -> pae/sistl
    électricité: e/mtiek/tRi/si/te -> e/mtiesktl
    personnalité: pieR/sae/mRa/mti/te -> pieR/saestl
    culpabilité: k@il/pa/svi/mti/te -> k@il/pastl
    responsabilités: Ries/pai/sa/svi/mti/te/-s -> Ries/pai/sastl/-s
    possibilités: pae/si/svi/mti/te/-s -> pae/sistl/-s
    spécialité: spe/sRwa/mti/te -> spestl
    hospitalité: es/pi/ta/mti/te -> es/pistl
    sensibilité: s@/si/svi/mti/te -> s@/sistl

## P030 (prefix) -- pré, pré@·, prée·, préa·

- merged keys [4, 12, 21] = `paR` for pré, pré@·, prée·, préa· (sim 0.58, comfort 527.9)
- strokeFreqSaved 655.0, freqBenefiting 517.5 of 1044.1 (share by freq 0.496, by count 0.389), boundary risks 0
- fallbacks: {'keyOverlap': 480}
- alternatives: merged [[8, 16, 18]] sim 0.574 saved 969.8; merged [[4, 12, 21]] sim 0.58 saved 655.0; merged [[2, 4, 8]] sim 0.67 saved 651.7; merged [[4, 8, 19]] sim 0.67 saved 650.1

    présent: pRe/tw@ -> ptw@aR
    présente: pRe/tw@t -> ptw@atR
    présenter: pRe/tw@/te/-l -> ptaeR/-l
    prévu: pRe/v@i -> pv@aiR
    présent: pRe/tw@ -> ptw@aR
    préparez: pRe/pa/Re/-k -> pRaeR/-k
    précis: pRe/si -> spaiR
    précieux: pRe/sRw@ie -> spRw@aieR
    présenté: pRe/tw@/te -> ptaeR
    préférez: pRe/kpe/Re/-k -> pRaeR/-k

## P020 (prefix) -- coni·, com°·, cona·, comp, cono·, conER·, conak·, conOR·, con5·, cone·

- merged keys [2, 3, 13, 21] = `ksiR` for coni·, comp, con5· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 8, 21] = `ksR-R` for com°· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 9, 21] = `ksw-R` for cona· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 4, 21] = `ksp-R` for cono· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 5, 21] = `ksv-R` for conER· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 6, 21] = `ksm-R` for conak· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 14, 21] = `kseR` for conOR· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 7, 21] = `kst-R` for cone· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 11, 21] = `ks@R` for con@· (sim 0.518, comfort 592.1)
- merged keys [2, 3, 17, 21] = `ks-sR` for cons (sim 0.518, comfort 592.1)
- strokeFreqSaved 652.6, freqBenefiting 396.5 of 966.9 (share by freq 0.41, by count 0.532), boundary risks 0
- fallbacks: {'keyOverlap': 465, 'markCostTooHigh': 32}
- alternatives: merged [[2, 3, 13, 21], [2, 3, 8, 21], [2, 3, 9, 21], [2, 3, 4, 21], [2, 3, 5, 21], [2, 3, 6, 21], [2, 3, 14, 21], [2, 3, 7, 21], [2, 3, 11, 21], [2, 3, 17, 21]] sim 0.518 saved 652.6; merged [[2, 13, 17, 21], [2, 8, 17, 21], [2, 9, 17, 21], [2, 3, 17, 21], [2, 4, 17, 21], [2, 5, 17, 21], [2, 14, 17, 21], [2, 6, 17, 21], [2, 11, 17, 21], [2, 7, 17, 21]] sim 0.512 saved 668.9; merged [[2, 13, 21], [2, 8, 21], [2, 9, 21], [2, 3, 21], [2, 4, 21], [2, 5, 21], [2, 14, 21], [2, 6, 21], [2, 11, 21], [2, 17, 21]] sim 0.505 saved 711.5; merged [[2, 12, 13], [2, 8, 12], [2, 9, 12], [2, 3, 12], [2, 4, 12], [2, 5, 12], [2, 12, 14], [2, 6, 12], [2, 11, 12], [2, 12, 17]] sim 0.501 saved 456.9; merged [[2, 12, 13, 17], [2, 8, 12, 17], [2, 9, 12, 17], [2, 3, 12, 17], [2, 4, 12, 17], [2, 5, 12, 17], [2, 12, 14, 17], [2, 6, 12, 17], [2, 11, 12, 17], [2, 7, 12, 17]] sim 0.507 saved 441.4

    continuer: kai/ti/mR@ae/-l -> ksmR@aieR/-l
    compter: kai/te/-l -> kstieR/-l
    construit: kais/tR@ai -> kstR@aisR
    comptez: kai/te/-k -> kstieR/-k
    concernant: kai/sieR/mR@ -> ksvmR@R
    confortable: kai/kpeR/tajl -> kstaejRl
    continué: kai/ti/mR@ae -> ksmR@aieR
    compté: kai/t*e -> kst*ieR
    considéré: kai/si/pve/Re -> kspvieR/Re
    comptable: kai/tajl -> kstaijRl

## S043 (suffix) -- ·yter, ·Ekteur, ·yler, ·Ekter, ·ykteur, ·ylter, ·yteur

- merged keys [16, 18, 20, 21] = `-jktR` for ·yter, ·yler, ·Ekter (sim 0.556, comfort 551.1)
- merged keys [17, 18, 20, 21] = `-sktR` for ·Ekteur (sim 0.556, comfort 551.1)
- merged keys [18, 19, 20, 21] = `-kdtR` for ·ykteur (sim 0.556, comfort 551.1)
- merged keys [18, 20, 21, 23] = `-ktRl` for ·ylter (sim 0.556, comfort 551.1)
- merged keys [18, 20, 21, 22] = `-ktRn` for ·yteur (sim 0.556, comfort 551.1)
- strokeFreqSaved 648.7, freqBenefiting 351.4 of 466.3 (share by freq 0.754, by count 0.859), boundary risks 0
- fallbacks: {'markCostTooHigh': 24, 'keyOverlap': 113}
- alternatives: merged [[16, 18, 20, 21], [17, 18, 20, 21], [18, 19, 20, 21], [18, 20, 21, 23], [18, 20, 21, 22]] sim 0.556 saved 648.7; merged [[16, 18, 20, 23], [17, 18, 20, 23], [18, 19, 20, 23], [18, 20, 21, 23], [18, 20, 22, 23]] sim 0.526 saved 661.6

    discuter: pvis/k@i/te/-l -> pvijsktR/-l
    respecter: Ries/piek/te/-l -> RiejsktR/-l
    discuté: pvis/k@i/te -> pvijsktR
    consulter: kai/s@il/te/-l -> kaiktRl/-l
    producteur: pRae/pv@ik/t@R -> pRaekdtR
    difficultés: pvi/kpi/k@il/te/-s -> pvi/kpiktRl/-s
    conducteur: kai/pv@ik/t@R -> kaikdtR
    exécuter: iekdnl/e/k@i/te/-l -> iekdnl/ejktR/-l
    instituteur: aies/ti/t@i/t@R -> aies/tiktRn
    exécuté: iekdnl/e/k@i/te -> iekdnl/ejktR

## P052 (prefix) -- ve, vé, ven

- merged keys [5, 9] = `vw-` for ve, vé, ven (sim 0.5, comfort 412.5)
- strokeFreqSaved 632.4, freqBenefiting 632.4 of 690.9 (share by freq 0.915, by count 0.38), boundary risks 0
- fallbacks: {'keyOverlap': 68, 'markCostTooHigh': 7}
- alternatives: merged [[5]] sim 0.667 saved 633.5; merged [[4, 5]] sim 0.5 saved 633.5; merged [[3, 5]] sim 0.5 saved 633.4; merged [[5, 9]] sim 0.5 saved 632.4; merged [[5, 12]] sim 0.5 saved 630.2

    venez: v@a/mRe -> vmRwe
    vérité: ve/Ri/te -> vRwi/te
    venue: v@a/mR@i/-j -> vmRw@i/-j
    venant: v@a/mR@ -> vmRw@
    venue: v@a/mR@i/-j -> vmRw@i/-j
    venue: v@a/mR*@i -> vmRw*@i
    vérités: ve/Ri/te/-s -> vRwi/te/-s
    vélos: ve/mtae/-s -> vmtwae/-s
    venues: v@a/mR*@i/-s -> vmRw*@i/-s
    ventouse: v@/t@enl -> vtw@enl

## S020 (suffix) -- ·iner, ·ifier, ·ijer, ·iller, ·aliser, ·iliser, ·iper, ·inier, ·alier, ·ilier

- dedicated keys [14, 16, 22] = `ejn` for ·iner, ·ifier, ·ijer, ·iller, ·aliser, ·iliser, ·iper, ·inier, ·alier, ·ilier (sim 0.494, comfort 319.0)
- strokeFreqSaved 631.3, freqBenefiting 595.1 of 855.2 (share by freq 0.696, by count 0.427), boundary risks 0
- fallbacks: {'noGain': 1857, 'markCostTooHigh': 313}
- alternatives: dedicated [[14, 16, 22]] sim 0.494 saved 631.3; dedicated [[13, 16, 22]] sim 0.491 saved 631.3; dedicated [[16, 22, 23]] sim 0.486 saved 631.3; dedicated [[2, 4, 6, 8, 9, 13, 14]] sim 0.442 saved 631.3; dedicated [[14, 22, 23]] sim 0.44 saved 631.3

    terminé: tieR/mi/mRe -> tieR/ejn
    imaginer: i/ma/vti/mRe/-l -> i/ma/ejn/-l
    imaginez: i/ma/vti/mRe/-k -> i/ma/ejn/-k
    meurtrier: m@R/tRij/e -> m@R/ejn
    terminée: tieR/mi/mRe/-j -> tieR/ejn/-j
    terminer: tieR/mi/mRe/-l -> tieR/ejn/-l
    identifier: i/pv@/ti/kpRwe/-l -> i/pv@/ejn/-l
    examiner: iekdnl/a/mi/mRe/-l -> iekdnl/a/ejn/-l
    participer: paR/ti/si/pe/-l -> paR/ti/ejn/-l
    assassiné: a/sa/si/mRe -> a/sa/ejn

## S056 (suffix) -- age, tage, rage, ·onnage, vage, mage, nage, nnage, llage, page

- merged keys [20, 22, 24] = `-tnZ` for age, tage, rage, ·onnage, vage, mage, nage, nnage, llage, page, lage, dage (sim 0.588, comfort 582.6)
- strokeFreqSaved 619.4, freqBenefiting 585.8 of 586.5 (share by freq 0.999, by count 0.99), boundary risks 0
- fallbacks: {'illegalChord': 3, 'markCostTooHigh': 3}
- alternatives: merged [[20, 22, 24]] sim 0.588 saved 619.4; merged [[21, 22, 24]] sim 0.578 saved 512.5; merged [[7, 22, 24]] sim 0.555 saved 541.9; merged [[8, 22, 24]] sim 0.55 saved 556.3; merged [[20, 21, 24]] sim 0.547 saved 512.5

    voyage: vwaj/aZ -> vwajtnZ
    courage: k@e/RaZ -> k@etnZ
    fromage: kpRae/maZ -> kpRaetnZ
    personnage: pieR/sae/mRaZ -> pietRnZ
    équipage: e/ki/paZ -> e/kitnZ
    avantage: a/v@/taZ -> a/v@tnZ
    sauvage: sae/vaZ -> saetnZ
    tournage: t@eR/mRaZ -> t@etRnZ
    chômage: pmae/maZ -> pmaetnZ
    héritage: e/Ri/taZ -> e/RitnZ

## S049 (suffix) -- mer, mé, mmer

- merged keys [23, 25] = `-lm` for mer, mé, mmer (sim 0.5, comfort 540.2)
- strokeFreqSaved 616.9, freqBenefiting 616.9 of 707.3 (share by freq 0.872, by count 0.98), boundary risks 0
- fallbacks: {'keyOverlap': 17}
- alternatives: merged [[23, 25]] sim 0.5 saved 616.9; merged [[24, 25]] sim 0.5 saved 613.6; merged [[11, 25]] sim 0.5 saved 630.9; merged [[6, 25]] sim 0.5 saved 611.3; merged [[5, 25]] sim 0.5 saved 686.4

    fermer: kpieR/me/-l -> kpieRlm/-l
    fermé: kpieR/me -> kpieRlm
    fermez: kpieR/me/-k -> kpieRlm/-k
    exprimer: ie/kspRi/me/-l -> ie/kspRilm/-l
    enfermé: @/kpieR/me -> @/kpieRlm
    fermée: kpieR/me/-j -> kpieRlm/-j
    enfermer: @/kpieR/me/-l -> @/kpieRlm/-l
    informer: aie/kpeR/me/-l -> aie/kpeRlm/-l
    allumer: a/mt@i/me/-l -> a/mt@ilm/-l
    transformer: tR@s/kpeR/me/-l -> tR@s/kpeRlm/-l

## S052 (suffix) -- vail, val, cal, al, gal, bal, val

- merged keys [16, 17, 23] = `-jsl` for vail, val, cal, al, gal, bal, val (sim 0.722, comfort 566.8)
- strokeFreqSaved 616.0, freqBenefiting 616.0 of 652.5 (share by freq 0.944, by count 0.861), boundary risks 0
- fallbacks: {'keyOverlap': 25}
- alternatives: merged [[16, 17, 23]] sim 0.722 saved 616.0; merged [[16, 17, 18]] sim 0.595 saved 616.1; merged [[5, 16, 23]] sim 0.572 saved 544.3; merged [[2, 16, 17]] sim 0.568 saved 612.0; merged [[14, 16, 17]] sim 0.54 saved 559.0

    travail: tRa/vaj -> tRajsl
    cheval: pm@a/val -> pm@ajsl
    musical: m@i/twi/kal -> m@i/twijsl
    idéal: i/pve/al -> i/pvejsl
    médical: me/pvi/kal -> me/pvijsl
    illégal: i/mte/ksal -> i/mtejsl
    médicale: me/pvi/kal/-j -> me/pvijsl/-j
    idéal: i/pve/al -> i/pvejsl
    carnaval: kaR/mRa/val -> kaR/mRajsl
    festival: kpies/ti/val -> kpies/tijsl

## S051 (suffix) -- rieur, sseur, reur, seur, geur, ceur, seur, queur, eur, cheur

- merged keys [16, 17, 21] = `-jsR` for rieur, sseur, reur, seur, geur, ceur, seur, queur, eur, cheur, gueur, peur (sim 0.713, comfort 524.8)
- strokeFreqSaved 607.6, freqBenefiting 607.6 of 657.6 (share by freq 0.924, by count 0.845), boundary risks 54
- fallbacks: {'markCostTooHigh': 10, 'keyOverlap': 93}
- alternatives: merged [[16, 17, 21]] sim 0.713 saved 607.6; merged [[3, 16, 21]] sim 0.63 saved 518.7; merged [[17, 21, 24]] sim 0.609 saved 629.7; merged [[17, 18, 21]] sim 0.603 saved 631.8; merged [[17, 21]] sim 0.588 saved 631.8

    professeur: pRe/kpie/s@R -> pRe/kpiejsR
    intérieur: aie/te/Rw@R -> aie/tejsR
    procureur: pRae/k@i/R@R -> pRae/k@ijsR
    extérieur: ie/kste/Rw@R -> ie/kstejsR
    empereur: @/p@a/R@R -> @/p@ajsR
    ascenseur: a/s@/s@R -> a/s@jsR
    chasseur: pma/s@R -> pmajsR
    douceur: pv@e/s@R -> pv@ejsR
    chasseurs: pma/s@R/-s -> pmajsR/-s
    supérieure: s@i/pe/Rw@R/-j -> s@i/pejsR/-j

## P071+P075 (prefix) -- tom, te, ten, té, to, thé, tem

- merged keys [7, 11] = `t@` for tom, te, ten, té, to, thé, tem (sim 0.69, comfort 398.8)
- strokeFreqSaved 606.9, freqBenefiting 606.9 of 766.4 (share by freq 0.792, by count 0.523), boundary risks 10
- fallbacks: {'keyOverlap': 117, 'markCostTooHigh': 6}
- alternatives: merged [[7, 11]] sim 0.69 saved 606.9; merged [[7, 9, 11]] sim 0.523 saved 531.9; merged [[2, 7, 11]] sim 0.523 saved 604.0; merged [[7, 11, 17]] sim 0.523 saved 591.0

    tomber: tai/sve/-l -> svt@e/-l
    tenez: t@a/mRe -> mtR@e
    tombé: tai/sve -> svt@e
    témoin: te/mwaie -> mtw@aie
    théâtre: te/atR -> t@atR
    tombée: tai/sve/-j -> svt@e/-j
    témoins: te/mwaie/-s -> mtw@aie/-s
    tempête: t@/piet -> pt@iet
    tendresse: t@/pvRies -> pvtR@ies
    tomates: tae/mat/-s -> mt@at/-s

## S029 (suffix) -- ·[ci|ga|me|mi|na|ré|sci|si|ssi|voi]né

- dedicated keys [16, 17, 22] = `-jsn` for ·[ci|ga|me|mi|na|ré|sci|si|ssi|voi]né (sim 0.308, comfort 270.0)
- strokeFreqSaved 605.9, freqBenefiting 605.9 of 605.9 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 17, 21]] sim 0.308 saved 605.9; dedicated [[16, 17, 22]] sim 0.308 saved 605.9; dedicated [[16, 17, 25]] sim 0.308 saved 605.9; dedicated [[8, 16, 17]] sim 0.269 saved 605.9; dedicated [[6, 16, 17]] sim 0.269 saved 605.9

    terminé: tieR/mi/mRe -> tieR/-jsn
    emmener: @/m@a/mRe/-l -> @/-jsn/-l
    ramener: Ra/m@a/mRe/-l -> Ra/-jsn/-l
    emmenez: @/m@a/mRe/-k -> @/-jsn/-k
    amener: a/m@a/mRe/-l -> a/-jsn/-l
    ramené: Ra/m@a/mRe -> Ra/-jsn
    emmené: @/m@a/mRe -> @/-jsn
    amenez: a/m@a/mRe/-k -> a/-jsn/-k
    terminée: tieR/mi/mRe/-j -> tieR/-jsn/-j
    terminer: tieR/mi/mRe/-l -> tieR/-jsn/-l

## S055 (suffix) -- toire, ·atoire, loir

- merged keys [7, 16, 21] = `t-jR` for toire, ·atoire, loir (sim 0.694, comfort 501.4)
- strokeFreqSaved 595.3, freqBenefiting 557.0 of 585.8 (share by freq 0.951, by count 0.761), boundary risks 9
- fallbacks: {'keyOverlap': 50}
- alternatives: merged [[16, 20, 21]] sim 0.816 saved 619.4; merged [[7, 16, 21]] sim 0.694 saved 595.3; merged [[9, 20, 21]] sim 0.674 saved 616.9; merged [[8, 16, 20]] sim 0.674 saved 591.6; merged [[12, 16, 21]] sim 0.643 saved 557.3

    histoire: is/twaR -> tijsR
    histoires: is/twaR/-s -> tijsR/-s
    vouloir: v@e/mtwaR -> vt@ejR
    victoire: vik/twaR -> vtijkR
    couloir: k@e/mtwaR -> kt@ejR
    territoire: tie/Ri/twaR -> tie/tRijR
    laboratoire: mta/svae/Ra/twaR -> mta/svtaejR
    interrogatoire: aie/tie/Rae/ksa/twaR -> aie/tie/tRaejR
    couloirs: k@e/mtwaR/-s -> kt@ejR/-s
    territoires: tie/Ri/twaR/-s -> tie/tRijR/-s

## S038 (suffix) -- quer, ·iqué, qué, quet, quant

- merged keys [11, 14, 16, 18] = `@ejk` for quer, qué (sim 0.782, comfort 580.7)
- merged keys [11, 13, 14, 18] = `@iek` for ·iqué, quant (sim 0.782, comfort 580.7)
- merged keys [2, 11, 14, 18] = `k@ek` for quet (sim 0.782, comfort 580.7)
- strokeFreqSaved 571.4, freqBenefiting 557.2 of 900.8 (share by freq 0.619, by count 0.448), boundary risks 2
- fallbacks: {'keyOverlap': 578}
- alternatives: merged [[11, 14, 16, 18], [11, 13, 14, 18], [2, 11, 14, 18]] sim 0.782 saved 571.4; merged [[14, 16, 18], [13, 14, 18], [2, 14, 18]] sim 0.779 saved 699.4; merged [[11, 14, 18], [11, 13, 18], [2, 11, 18]] sim 0.633 saved 590.9; merged [[14, 16, 18, 19], [13, 14, 18, 19], [2, 14, 18, 19]] sim 0.621 saved 699.4; merged [[14, 16, 17, 18], [13, 14, 16, 18], [2, 14, 16, 18]] sim 0.621 saved 637.4

    expliquer: ie/kspmti/ke/-l -> ie/kspmt@iejk/-l
    remarqué: R@a/maR/ke -> R@a/m@aejkR
    attaquer: a/ta/ke/-l -> a/t@aejk/-l
    attaqué: a/ta/ke -> a/t@aejk
    marqué: maR/ke -> m@aejkR
    expliquez: ie/kspmti/ke/-k -> ie/kspmt@iejk/-k
    expliqué: ie/kspmti/ke -> ie/kspmt@iejk
    impliqué: aie/pmti/ke -> aie/pmt@iejk
    risquer: Ris/ke/-l -> R@iejsk/-l
    remarquer: R@a/maR/ke/-l -> R@a/m@aejkR/-l

## S048 (suffix) -- table, able, rable, sable, ·onnable, dable, ·ORtable, ·erable, nnable, nable

- merged keys [16, 21, 23] = `-jRl` for table, able, rable, sable, ·onnable, dable, ·ORtable, ·erable, nnable, nable (sim 0.654, comfort 520.9)
- strokeFreqSaved 568.9, freqBenefiting 497.2 of 678.8 (share by freq 0.732, by count 0.801), boundary risks 0
- fallbacks: {'keyOverlap': 77, 'illegalChord': 1}
- alternatives: merged [[16, 20, 23]] sim 0.664 saved 615.2; merged [[16, 21, 23]] sim 0.654 saved 568.9; merged [[7, 16, 23]] sim 0.621 saved 567.2; merged [[16, 22, 23]] sim 0.621 saved 615.2; merged [[16, 17, 23]] sim 0.606 saved 605.0

    formidable: kpeR/mi/pvajl -> kpeR/mijRl
    responsable: Ries/pai/sajl -> Ries/paijRl
    agréable: a/ksRe/ajl -> a/ksRejRl
    véritable: ve/Ri/tajl -> ve/RijRl
    raisonnable: Rie/twae/mRajl -> RiejRl
    adorable: a/pvae/Rajl -> a/pvaejRl
    responsable: Ries/pai/sajl -> Ries/paijRl
    confortable: kai/kpeR/tajl -> kaijRl
    insupportable: aie/s@i/peR/tajl -> aie/s@ijRl
    misérable: mi/twe/Rajl -> mi/twejRl

## P015 (prefix) -- ma, maa·, mea·

- merged keys [6, 14, 19] = `med` for ma, maa·, mea· (sim 0.5, comfort 583.8)
- strokeFreqSaved 562.6, freqBenefiting 464.0 of 1925.0 (share by freq 0.241, by count 0.488), boundary risks 8
- fallbacks: {'keyOverlap': 236}
- alternatives: merged [[12, 14, 25]] sim 0.5 saved 827.7; merged [[6, 14, 19]] sim 0.5 saved 562.6; merged [[6, 14]] sim 0.665 saved 559.1; merged [[6, 14, 24]] sim 0.5 saved 558.8

    madame: ma/pvam -> pvmaedm
    maladie: ma/mta/pvi -> pvmied
    magie: ma/vti -> vmtied
    marie: ma/R*i -> mR*ied
    maria: ma/Rwa -> mRwaed
    maladies: ma/mta/pvi/-s -> pvmied/-s
    matinée: ma/ti/mRe -> mtied/mRe
    maris: ma/Ri/-s -> mRied/-s
    manager: ma/mRa/pvt@R -> pvmt@edR
    maladroit: ma/mta/pvRwa -> pvmRwaed

## S054 (suffix) -- veau, sseau, ceau, vo, beau

- merged keys [12, 16, 17] = `ajs` for veau, sseau, ceau, vo, beau (sim 0.5, comfort 478.9)
- strokeFreqSaved 559.4, freqBenefiting 559.4 of 642.5 (share by freq 0.871, by count 0.569), boundary risks 0
- fallbacks: {'keyOverlap': 31}
- alternatives: merged [[12, 16, 17]] sim 0.5 saved 559.4; merged [[4, 16, 17]] sim 0.5 saved 633.8; merged [[7, 16, 17]] sim 0.5 saved 624.3; merged [[16, 17, 19]] sim 0.5 saved 642.5

    nouveau: mR@e/vae -> mR@aejs
    nouveau: mR@e/vae -> mR@aejs
    vaisseau: vie/sae -> vaiejs
    cerveau: sieR/vae -> saiejsR
    morceau: meR/sae -> maejsR
    nouveaux: mR@e/vae/-s -> mR@aejs/-s
    morceaux: meR/sae/-s -> maejsR/-s
    vaisseaux: vie/sae/-s -> vaiejs/-s
    nouveaux: mR@e/vae/-s -> mR@aejs/-s
    berceau: svieR/sae -> svaiejsR

## S060 (suffix) -- reux, lleux, eux, geux, leux, teux

- merged keys [16, 21, 24] = `-jRZ` for reux, lleux, eux, geux, leux, teux (sim 0.594, comfort 596.3)
- strokeFreqSaved 551.9, freqBenefiting 551.9 of 600.4 (share by freq 0.919, by count 0.951), boundary risks 0
- fallbacks: {'keyOverlap': 7}
- alternatives: merged [[16, 21, 24]] sim 0.594 saved 551.9; merged [[16, 21, 23]] sim 0.593 saved 551.9; merged [[16, 20, 21]] sim 0.591 saved 551.9; merged [[16, 21]] sim 0.567 saved 544.7; merged [[20, 21, 24]] sim 0.54 saved 600.4

    heureux: @ie/R@ie -> @iejRZ
    dangereux: pv@/vt@a/R@ie -> pv@/vt@ajRZ
    amoureux: a/m@e/R@ie -> a/m@ejRZ
    merveilleux: mieR/vie/Rw@ie -> mieR/viejRZ
    malheureux: ma/mt@ie/R@ie -> ma/mt@iejRZ
    courageux: k@e/Ra/vt@ie -> k@e/RajRZ
    généreux: vte/mRe/R@ie -> vte/mRejRZ
    amoureux: a/m@e/R@ie -> a/m@ejRZ
    douloureux: pv@e/mt@e/R@ie -> pv@e/mt@ejRZ
    fabuleux: kpa/sv@i/mt@ie -> kpa/sv@ijRZ

## P056 (prefix) -- gar, car, bar

- merged keys [8, 9, 18, 19] = `Rw-kd` for gar (sim 0.589, comfort 566.7)
- merged keys [2, 8, 18, 19] = `kR-kd` for car (sim 0.589, comfort 566.7)
- merged keys [8, 16, 18, 19] = `R-jkd` for bar (sim 0.589, comfort 566.7)
- strokeFreqSaved 539.1, freqBenefiting 539.1 of 576.0 (share by freq 0.936, by count 0.858), boundary risks 0
- fallbacks: {'keyOverlap': 37}
- alternatives: merged [[8, 9, 18, 19], [2, 8, 18, 19], [8, 16, 18, 19]] sim 0.589 saved 539.1; merged [[2, 3, 8, 21], [2, 3, 18, 21], [2, 3, 16, 21]] sim 0.579 saved 295.5; merged [[2, 3, 8, 9], [2, 3, 8, 18], [2, 3, 8, 16]] sim 0.778 saved 268.4; merged [[2, 8, 9, 12], [2, 8, 12, 18], [2, 8, 12, 16]] sim 0.545 saved 224.5; merged [[8, 9, 12, 16], [2, 8, 12, 16], [3, 8, 12, 16]] sim 0.511 saved 221.7

    garçon: ksaR/sai -> sRwaikd
    garder: ksaR/pve/-l -> pvRwekd/-l
    garçons: ksaR/sai/-s -> sRwaikd/-s
    gardez: ksaR/pve/-k -> pvRwekd/-k
    gardé: ksaR/pve -> pvRwekd
    carton: kaR/tai -> ktRaikd
    barman: svaR/man -> mRajkdn
    garderai: ksaR/pv@a/Re/-t -> pvRw@akd/Re/-t
    cartons: kaR/tai/-s -> ktRaikd/-s
    gardons: ksaR/pvai -> pvRwaikd

## S061 (suffix) -- leur, ssaire, traire, laire, ·ylaire, raire, aire

- merged keys [17, 21, 23] = `-sRl` for leur, ssaire, traire, laire, ·ylaire, raire, aire (sim 0.724, comfort 528.5)
- strokeFreqSaved 522.4, freqBenefiting 508.3 of 534.7 (share by freq 0.951, by count 0.937), boundary risks 0
- fallbacks: {'keyOverlap': 21}
- alternatives: merged [[17, 21, 23]] sim 0.724 saved 522.4; merged [[20, 21, 23]] sim 0.704 saved 539.4; merged [[3, 21, 23]] sim 0.687 saved 458.6; merged [[7, 21, 23]] sim 0.676 saved 488.5; merged [[21, 23]] sim 0.649 saved 539.4

    douleur: pv@e/mt@R -> pv@esRl
    contraire: kai/tRieR -> kaisRl
    couleur: k@e/mt@R -> k@esRl
    nécessaire: mRe/se/sieR -> mRe/sesRl
    commissaire: kae/mi/sieR -> kae/misRl
    chaleur: pma/mt@R -> pmasRl
    couleurs: k@e/mt@R/-s -> k@esRl/-s
    populaire: pae/p@i/mtieR -> pae/p@isRl
    nucléaire: mR@i/kmte/ieR -> mR@i/kmtesRl
    douleurs: pv@e/mt@R/-s -> pv@esRl/-s

## S053 (suffix) -- di, die, dit, dier, din, dien, dir

- merged keys [8, 16, 17, 19] = `R-jsd` for di, die, dit (sim 0.703, comfort 608.8)
- merged keys [8, 14, 16, 19] = `Rejd` for dier, din, dien (sim 0.703, comfort 608.8)
- merged keys [8, 16, 19, 21] = `R-jdR` for dir (sim 0.703, comfort 608.8)
- strokeFreqSaved 519.0, freqBenefiting 519.0 of 650.6 (share by freq 0.798, by count 0.57), boundary risks 0
- fallbacks: {'keyOverlap': 174}
- alternatives: merged [[8, 16, 17, 19], [8, 14, 16, 19], [8, 16, 19, 21]] sim 0.703 saved 519.0; merged [[16, 17, 19], [14, 16, 19], [16, 19, 21]] sim 0.688 saved 616.5; merged [[8, 9, 16, 19], [8, 9, 14, 19], [8, 9, 19, 21]] sim 0.641 saved 518.8; merged [[8, 16, 19], [8, 14, 19], [8, 19, 21]] sim 0.58 saved 519.2; merged [[16, 19], [14, 19], [19, 21]] sim 0.565 saved 616.7

    jardin: vtaR/pvaie -> vtRaejdR
    maladie: ma/mta/pvi -> ma/mtRajsd
    samedi: sa/m@a/pvi -> sa/mR@ajsd
    lundi: mt@aie/pvi -> mtR@aiejsd
    étudier: e/t@i/pvRwe/-l -> e/tR@iejd/-l
    jeudi: vt@ie/pvi -> vtR@iejsd
    mardi: maR/pvi -> mRajsdR
    comédie: kae/me/pvi -> kae/mRejsd
    gardien: ksaR/pvRwaie -> ksRaejdR
    incendie: aie/s@/pvi -> aie/sR@jsd

## S065 (suffix) -- tal, ral, ·@tal, tral

- merged keys [20, 21, 23] = `-tRl` for tal, ral, ·@tal, tral (sim 0.788, comfort 481.8)
- strokeFreqSaved 506.8, freqBenefiting 479.7 of 479.7 (share by freq 1.0, by count 0.991), boundary risks 0
- fallbacks: {'keyOverlap': 3}
- alternatives: merged [[20, 21, 23]] sim 0.788 saved 506.8; merged [[12, 20, 23]] sim 0.705 saved 463.7; merged [[7, 21, 23]] sim 0.675 saved 465.4; merged [[12, 21, 23]] sim 0.657 saved 463.7; merged [[11, 20, 23]] sim 0.619 saved 436.0

    hôpital: ae/pi/tal -> ae/pitRl
    général: vte/mRe/Ral -> vte/mRetRl
    général: vte/mRe/Ral -> vte/mRetRl
    générale: vte/mRe/Ral/-j -> vte/mRetRl/-j
    central: s@/tR*al -> s*@tRl
    caporal: ka/pae/Ral -> ka/paetRl
    central: s@/tR*al -> s*@tRl
    centrale: s@/tRal/-j -> s@tRl/-j
    fédéral: kpe/pve/Ral -> kpe/pvetRl
    mentale: m@/tal/-j -> m@tRl/-j

## S039 (suffix) -- ·[choue|gi|lu|lû|mmé|mé|pe|ppe|re|rre|sé]ment

- dedicated keys [21, 24, 25] = `-RZm` for ·[choue|gi|lu|lû|mmé|mé|pe|ppe|re|rre|sé]ment (sim 0.308, comfort 307.0)
- strokeFreqSaved 483.3, freqBenefiting 483.3 of 483.3 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[21, 24, 25]] sim 0.308 saved 483.3; dedicated [[8, 24, 25]] sim 0.269 saved 483.3; dedicated [[4, 24, 25]] sim 0.269 saved 483.3; dedicated [[13, 24, 25]] sim 0.25 saved 483.3; dedicated [[6, 7, 9, 11, 13, 14]] sim 0.212 saved 483.3

    sûrement: s@i/R@a/m@ -> s@i/-RZm
    absolument: ajk/sae/mt@i/m@ -> ajk/sae/-RZm
    enterrement: @/tie/R@a/m@ -> @/tie/-RZm
    clairement: kmtie/R@a/m@ -> kmtie/-RZm
    entièrement: @/tRwie/R@a/m@ -> @/tRwie/-RZm
    particulièrement: paR/ti/k@i/mtRwie/R@a/m@ -> paR/ti/k@i/mtRwie/-RZm
    rarement: Ra/R@a/m@ -> Ra/-RZm
    sincèrement: saie/sie/R@a/m@ -> saie/sie/-RZm
    précisément: pRe/si/twe/m@ -> pRe/si/-RZm
    énormément: e/mReR/me/m@ -> e/mReR/-RZm

## P034 (prefix) -- dii·, dis, disy·, disa·, disi·

- merged keys [3, 12, 13, 19] = `said` for dii·, disa·, disi· (sim 0.605, comfort 577.9)
- merged keys [3, 8, 13, 19] = `sRid` for dis (sim 0.605, comfort 577.9)
- merged keys [3, 9, 13, 19] = `swid` for disy· (sim 0.605, comfort 577.9)
- strokeFreqSaved 475.9, freqBenefiting 361.1 of 714.2 (share by freq 0.506, by count 0.516), boundary risks 17
- fallbacks: {'keyOverlap': 313, 'markCostTooHigh': 10}
- alternatives: merged [[4, 5, 12, 17], [4, 5, 8, 17], [4, 5, 9, 17]] sim 0.585 saved 625.5; merged [[3, 12, 13, 19], [3, 8, 13, 19], [3, 9, 13, 19]] sim 0.605 saved 475.9; merged [[3, 4, 5, 12], [3, 4, 5, 8], [3, 4, 5, 9]] sim 0.718 saved 324.3; merged [[4, 5, 12, 13], [4, 5, 8, 13], [4, 5, 9, 13]] sim 0.564 saved 206.8

    disparu: pvis/pa/R@i -> spRaid/R@i
    discuter: pvis/k@i/te/-l -> stwied/-l
    discours: pvis/k@eR -> ksR@iedR
    disparaître: pvis/pa/RietR -> spRaid/RietR
    diriger: pvi/Ri/vte/-l -> svtaied/-l
    disposition: pvis/pae/twi/sRwai -> spRaied/twi/sRwai
    discuté: pvis/k@i/te -> stwied
    disparaît: pvis/pa/Rie -> spRaid/Rie
    disposer: pvis/pae/twe/-l -> spRaied/twe/-l
    disparaissent: pvis/pa/Ries/-st -> spRaid/Ries/-st

## P062 (prefix) -- ca

- merged keys [2] = `k-` for ca (sim 0.667, comfort 343.3)
- strokeFreqSaved 474.9, freqBenefiting 474.9 of 491.4 (share by freq 0.966, by count 0.774), boundary risks 22
- fallbacks: {'keyOverlap': 70, 'markCostTooHigh': 13}
- alternatives: merged [[2]] sim 0.667 saved 474.9; merged [[2, 3]] sim 0.5 saved 450.8; merged [[2, 11]] sim 0.5 saved 456.3; merged [[2, 5]] sim 0.5 saved 430.8; merged [[2, 7]] sim 0.5 saved 442.7

    capitaine: ka/pi/tien -> kpi/tien
    cacher: ka/pme/-l -> kpme/-l
    caché: ka/pme -> kpme
    canapé: ka/mRa/pe -> kmRa/pe
    canard: ka/mRaR -> kmRaR
    canon: ka/mRai -> kmRai
    cabane: ka/svan -> ksvan
    casino: ka/twi/mRae -> ktwi/mRae
    cachez: ka/pme/-k -> kpme/-k
    cachée: ka/pme/-j -> kpme/-j

## P050 (prefix) -- vi, véi·

- merged keys [3, 5, 14] = `sve` for vi, véi· (sim 0.5, comfort 505.3)
- strokeFreqSaved 465.5, freqBenefiting 384.4 of 552.3 (share by freq 0.696, by count 0.38), boundary risks 0
- fallbacks: {'keyOverlap': 142}
- alternatives: merged [[5]] sim 0.576 saved 689.9; merged [[3, 5, 14]] sim 0.5 saved 465.5; merged [[5, 14]] sim 0.644 saved 465.5; merged [[5, 14, 18]] sim 0.5 saved 465.5; merged [[5, 14, 19]] sim 0.5 saved 465.5

    visage: vi/twaZ -> svtwaeZ
    visite: vi/twit -> svtwiet
    véritable: ve/Ri/tajl -> svtaejl
    virus: vi/R@is -> svR@ies
    vérifie: ve/Ri/kpi -> kspvie
    véhicule: ve/i/k@il -> ksv@iel
    visages: vi/twaZ/-s -> svtwaeZ/-s
    visites: vi/twit/-s -> svtwiet/-s
    virage: vi/RaZ -> svRaeZ
    vitrine: vi/tRin -> svtRien

## S023 (suffix) -- cher, ché, chant

- merged keys [14, 19, 24, 25] = `edZm` for cher, ché (sim 0.5, comfort 609.1)
- merged keys [11, 19, 24, 25] = `@dZm` for chant (sim 0.5, comfort 609.1)
- strokeFreqSaved 449.0, freqBenefiting 449.0 of 1579.3 (share by freq 0.284, by count 0.453), boundary risks 0
- fallbacks: {'keyOverlap': 474}
- alternatives: merged [[14, 19, 24, 25], [11, 19, 24, 25]] sim 0.5 saved 449.0; merged [[14, 20, 24, 25], [11, 20, 24, 25]] sim 0.5 saved 448.8; merged [[9, 14, 24, 25], [9, 11, 24, 25]] sim 0.5 saved 449.0; merged [[5, 14, 24, 25], [5, 11, 24, 25]] sim 0.5 saved 413.7; merged [[8, 14, 24, 25], [8, 11, 24, 25]] sim 0.5 saved 342.6

    marcher: maR/pme/-l -> maedRZm/-l
    marché: maR/pme -> maedRZm
    marché: maR/pme -> maedRZm
    arracher: a/Ra/pme/-l -> a/RaedZm/-l
    attacher: a/ta/pme/-l -> a/taedZm/-l
    arraché: a/Ra/pme -> a/RaedZm
    attaché: a/ta/pme -> a/taedZm
    marchez: maR/pme/-k -> maedRZm/-k
    cracher: kRa/pme/-l -> kRaedZm/-l
    plancher: pmt@/pme -> pmt@edZm

## S042 (suffix) -- ·[bla|ddi|di|jonc|la|lla|na|ru|si|xpia]tion

- dedicated keys [2, 3, 4, 5, 7, 8, 9, 12, 13, 18] = `kspvtRwaik` for ·[bla|ddi|di|jonc|la|lla|na|ru|si|xpia]tion (sim 0.344, comfort 680.0)
- strokeFreqSaved 443.5, freqBenefiting 443.5 of 443.5 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 3, 4, 5, 7, 8, 9, 12, 13, 18]] sim 0.344 saved 443.5; dedicated [[16, 17, 18]] sim 0.312 saved 443.5; dedicated [[16, 18, 19]] sim 0.312 saved 443.5; dedicated [[16, 18, 21]] sim 0.312 saved 443.5; dedicated [[16, 18, 22]] sim 0.312 saved 443.5

    position: pae/twi/sRwai -> pae/kspvtRwaik
    relation: R@a/mta/sRwai -> R@a/kspvtRwaik
    imagination: i/ma/vti/mRa/sRwai -> i/ma/vti/kspvtRwaik
    condition: kai/pvi/sRwai -> kai/kspvtRwaik
    conditions: kai/pvi/sRwai/-s -> kai/kspvtRwaik/-s
    tradition: tRa/pvi/sRwai -> tRa/kspvtRwaik
    population: pae/p@i/mta/sRwai -> pae/p@i/kspvtRwaik
    disposition: pvis/pae/twi/sRwai -> pvis/pae/kspvtRwaik
    circulation: siR/k@i/mta/sRwai -> siR/k@i/kspvtRwaik
    destination: pves/ti/mRa/sRwai -> pves/ti/kspvtRwaik

## S069 (suffix) -- rence, ·erence, rance, lence, gence, geance, quence, lance, ance, llance

- merged keys [17, 21, 24] = `-sRZ` for rence, ·erence, rance, lence, gence, geance, quence, lance, ance, llance, ence (sim 0.661, comfort 626.5)
- strokeFreqSaved 441.9, freqBenefiting 407.4 of 415.3 (share by freq 0.981, by count 0.927), boundary risks 0
- fallbacks: {'illegalChord': 2, 'keyOverlap': 11}
- alternatives: merged [[17, 21, 23]] sim 0.671 saved 441.9; merged [[17, 21, 24]] sim 0.661 saved 441.9; merged [[17, 18, 21]] sim 0.632 saved 444.4; merged [[16, 17, 21]] sim 0.625 saved 434.3; merged [[17, 21]] sim 0.607 saved 444.4

    différence: pvi/kpe/R@s -> pvi/kpesRZ
    violence: vRwae/mt@s -> vRwaesRZ
    vengeance: v@/vt@s -> v@sRZ
    ambulance: @/sv@i/mt@s -> @/sv@isRZ
    assurance: a/s@i/R@s -> a/s@isRZ
    surveillance: s@iR/vie/Rw@s -> s@iR/viesRZ
    intelligence: aie/te/mti/vt@s -> aie/te/mtisRZ
    conférence: kai/kpe/R@s -> kaisRZ
    conséquences: kai/se/k@s/-s -> kai/sesRZ/-s
    influence: aie/kpmt@i/@s -> aie/kpmt@isRZ

## S037+S149 (suffix) -- ·onner, ·oser, ·onnier, no

- merged keys [12, 14, 22] = `aen` for ·onner, ·oser, ·onnier, no (sim 0.646, comfort 475.6)
- strokeFreqSaved 436.1, freqBenefiting 236.3 of 593.2 (share by freq 0.398, by count 0.33), boundary risks 0
- fallbacks: {'keyOverlap': 1187, 'markCostTooHigh': 17}
- alternatives: merged [[16, 22, 23]] sim 0.536 saved 1025.4; merged [[14, 16, 22]] sim 0.581 saved 708.0; merged [[14, 22, 23]] sim 0.593 saved 705.3; merged [[14, 22]] sim 0.526 saved 703.5; merged [[12, 14, 22]] sim 0.646 saved 436.1

    abandonner: a/sv@/pvae/mRe/-l -> a/sv@aen/-l
    abandonné: a/sv@/pvae/mRe -> a/sv@aen
    prisonniers: pRi/twae/mRwe/-s -> pRaien/-s
    prisonnier: pRi/twae/mRwe -> pRaien
    prisonnier: pRi/twae/mRwe -> pRaien
    casino: ka/twi/mRae -> ka/twaien
    disposer: pvis/pae/twe/-l -> pvaiesn/-l
    abandonnée: a/sv@/pvae/mRe/-j -> a/sv@aen/-j
    mentionné: m@/sRwae/mRe -> m@aen
    abandonnez: a/sv@/pvae/mRe/-k -> a/sv@aen/-k

## S066 (suffix) -- sir, soir, ir, ssir

- merged keys [9, 17, 21] = `w-sR` for sir, soir, ir, ssir (sim 0.565, comfort 625.4)
- strokeFreqSaved 415.4, freqBenefiting 415.4 of 470.3 (share by freq 0.883, by count 0.84), boundary risks 0
- fallbacks: {'keyOverlap': 8}
- alternatives: merged [[16, 17, 21]] sim 0.626 saved 470.1; merged [[9, 17, 21]] sim 0.565 saved 415.4; merged [[21, 22, 23]] sim 0.553 saved 470.1; merged [[17, 21]] sim 0.503 saved 470.1; merged [[13, 16, 21]] sim 0.543 saved 287.9

    plaisir: pmte/twiR -> pmtwesR
    bonsoir: svai/swaR -> svwaisR
    réussir: Re/@i/siR -> Re/w@isR
    obéir: ae/sve/iR -> ae/svwesR
    trahir: tRa/iR -> tRwasR
    saisir: se/twiR -> swesR
    plaisirs: pmte/twiR/-s -> pmtwesR/-s
    envahir: @/va/iR -> @/vwasR
    grossir: ksRae/siR -> ksRwaesR
    désobéir: pve/twae/sve/iR -> pve/twae/svwesR

## S074 (suffix) -- to, teau

- merged keys [20, 22] = `-tn` for to, teau (sim 0.5, comfort 468.8)
- strokeFreqSaved 414.3, freqBenefiting 414.3 of 414.3 (share by freq 1.0, by count 0.971), boundary risks 10
- fallbacks: {'keyOverlap': 3}
- alternatives: merged [[13, 20]] sim 0.5 saved 388.2; merged [[20, 22]] sim 0.5 saved 414.3; merged [[18, 20]] sim 0.5 saved 413.8

    photo: kpae/tae -> kpaetn
    photos: kpae/tae/-s -> kpaetn/-s
    couteau: k@e/tae -> k@etn
    château: pma/tae -> pmatn
    manteau: m@/tae -> m@tn
    plateau: pmta/tae -> pmtatn
    marteau: maR/tae -> matRn
    resto: Ries/tae -> Riestn
    couteaux: k@e/tae/-s -> k@etn/-s
    hosto: es/tae -> estn

## P064 (prefix) -- poi·, pri, poi

- merged keys [4, 16, 21] = `p-jR` for poi·, pri, poi (sim 0.56, comfort 636.5)
- strokeFreqSaved 408.5, freqBenefiting 313.9 of 345.0 (share by freq 0.91, by count 0.867), boundary risks 2
- fallbacks: {'keyOverlap': 22}
- alternatives: merged [[4, 8, 16]] sim 0.649 saved 404.3; merged [[4, 8]] sim 0.617 saved 416.0; merged [[4, 16, 21]] sim 0.56 saved 408.5; merged [[4, 21]] sim 0.528 saved 418.0; merged [[4, 6, 8]] sim 0.507 saved 403.9

    prison: pRi/twai -> ptwaijR
    politique: pae/mti/tik -> ptijkR
    poitrine: pwa/tRin -> ptRijRn
    politique: pae/mti/tik -> ptijkR
    poison: pwa/twai -> ptwaijR
    politiques: pae/mti/tik/-s -> ptijkR/-s
    positif: pae/twi/tisd -> ptijsdR
    privé: pRi/ve -> pvejR
    privée: pRi/ve/-j -> pvejR/-j
    prisons: pRi/twai/-s -> ptwaijR/-s

## S072 (suffix) -- velle, rel, el, riel, vel, belle, relle, elle

- merged keys [5, 21, 23] = `v-Rl` for velle, rel, el, riel, vel, belle, relle, elle (sim 0.628, comfort 565.4)
- strokeFreqSaved 407.2, freqBenefiting 407.2 of 422.5 (share by freq 0.964, by count 0.949), boundary risks 0
- fallbacks: {'keyOverlap': 8}
- alternatives: merged [[16, 17, 23]] sim 0.687 saved 411.7; merged [[5, 21, 23]] sim 0.628 saved 407.2; merged [[5, 16, 23]] sim 0.573 saved 411.7; merged [[16, 21, 23]] sim 0.571 saved 397.1; merged [[3, 5, 23]] sim 0.528 saved 401.8

    nouvelle: mR@e/viel -> vmR@eRl
    nouvelles: mR@e/viel/-s -> vmR@eRl/-s
    nouvel: mR@e/v*iel -> vmR*@eRl
    matériel: ma/te/Rwiel -> ma/vteRl
    naturel: mRa/t@i/Riel -> mRa/vt@iRl
    cruel: kR@i/iel -> kvR@iRl
    poubelle: p@e/sviel -> pv@eRl
    naturelle: mRa/t@i/Riel/-j -> mRa/vt@iRl/-j
    querelle: k@a/Riel -> kv@aRl
    cruelle: kR@i/iel/-j -> kvR@iRl/-j

## S076 (suffix) -- ·ager, ·ageux

- merged keys [24] = `-Z` for ·ager, ·ageux (sim 0.5, comfort 420.5)
- strokeFreqSaved 397.5, freqBenefiting 219.6 of 220.6 (share by freq 0.996, by count 0.997), boundary risks 46
- fallbacks: {'markCostTooHigh': 2}
- alternatives: merged [[24]] sim 0.5 saved 397.5; merged [[12, 16, 24]] sim 0.5 saved 201.9; merged [[12, 17, 24]] sim 0.5 saved 201.9; merged [[12, 18, 24]] sim 0.5 saved 201.9; merged [[12, 19, 24]] sim 0.5 saved 201.9

    partager: paR/ta/vte/-l -> paRZ/-l
    courageux: k@e/Ra/vt@ie -> k@eZ
    voyager: vwaj/a/vte/-l -> vwajZ/-l
    déménager: pve/me/mRa/vte/-l -> pve/meZ/-l
    déménagé: pve/me/mRa/vte -> pve/meZ
    courageuse: k@e/Ra/vt@ienl -> k@eZ/vt@ienl
    soulager: s@e/mta/vte/-l -> s@eZ/-l
    voyagé: vwaj/a/vte -> vwajZ
    partagé: paR/ta/vte -> paRZ
    emménager: @/me/mRa/vte/-l -> @/meZ/-l

## S098+S119 (suffix) -- ·Essant, ssant, ssance, science, ·issant

- merged keys [11, 17] = `@s` for ·Essant, ssant, ssance, science, ·issant (sim 0.705, comfort 385.2)
- strokeFreqSaved 396.3, freqBenefiting 307.5 of 396.1 (share by freq 0.776, by count 0.681), boundary risks 41
- fallbacks: {'keyOverlap': 117}
- alternatives: merged [[11, 16, 17]] sim 0.75 saved 396.3; merged [[11, 17]] sim 0.705 saved 396.3; merged [[16, 17]] sim 0.609 saved 490.8; merged [[11, 17, 19]] sim 0.564 saved 396.3; merged [[11, 17, 21]] sim 0.564 saved 392.7

    intéressant: aie/te/Rie/s@ -> aie/t@es
    conscience: kai/sRw@s -> k@ais
    naissance: mRie/s@s -> mR@ies
    connaissance: kae/mRie/s@s -> kae/mR@ies
    reconnaissance: R@a/kae/mRie/s@s -> R@a/kae/mR@ies
    intéressant: aie/te/Rie/s@ -> aie/t@es
    intéressante: aie/te/Rie/s@t -> aie/t@es/s@t
    reconnaissant: R@a/kae/mRie/s@ -> R@a/k@aes
    connaissances: kae/mRie/s@s/-s -> kae/mR@ies/-s
    reconnaissante: R@a/kae/mRie/s@t -> R@a/k@aes/s@t

## S087+S135 (suffix) -- dre, duire, deur, rade, nade, daire

- merged keys [8, 19, 22] = `R-dn` for dre, duire, deur, rade, nade, daire (sim 0.631, comfort 602.3)
- strokeFreqSaved 395.1, freqBenefiting 395.1 of 471.4 (share by freq 0.838, by count 0.784), boundary risks 0
- fallbacks: {'keyOverlap': 47, 'markCostTooHigh': 1}
- alternatives: merged [[8, 19, 22]] sim 0.631 saved 395.1; merged [[8, 11, 19]] sim 0.617 saved 361.8; merged [[8, 19]] sim 0.598 saved 395.1; merged [[16, 19, 21]] sim 0.683 saved 315.2; merged [[18, 19, 21]] sim 0.683 saved 315.2

    perdre: pieR/pvR- -> pRiedRn
    conduire: kai/pv@aiR -> kRaidn
    camarade: ka/ma/Rad -> ka/mRadn
    camarades: ka/ma/Rad/-s -> ka/mRadn/-s
    ambassadeur: @/sva/sa/pv@R -> @/sva/sRadn
    vendeur: v@/pv@R -> vR@dn
    profondeur: pRae/kpai/pv@R -> pRae/kpRaidn
    mordre: meR/pvR- -> mRedRn
    répondeur: Re/pai/pv@R -> Re/pRaidn
    limonade: mti/mae/mRad -> mti/mRaedn

## S046 (suffix) -- ·[a|ac|dic|jec|sa|ta|truc|tta|vic]tion

- dedicated keys [3, 5, 7, 8, 9, 12, 13, 14, 18] = `svtRwaiek` for ·[a|ac|dic|jec|sa|ta|truc|tta|vic]tion (sim 0.379, comfort 638.0)
- strokeFreqSaved 394.8, freqBenefiting 394.8 of 394.8 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[3, 5, 7, 8, 9, 12, 13, 14, 18]] sim 0.379 saved 394.8; dedicated [[3, 7, 8, 9, 11, 12, 13, 18]] sim 0.31 saved 394.8; dedicated [[4, 5, 7, 9, 12, 13, 18]] sim 0.293 saved 394.8; dedicated [[3, 4, 5, 8, 9, 12, 13, 18]] sim 0.293 saved 394.8; dedicated [[16, 17, 18]] sim 0.276 saved 394.8

    réaction: Re/ak/sRwai -> Re/svtRwaiek
    organisation: eR/ksa/mRi/twa/sRwai -> eR/ksa/mRi/svtRwaiek
    instructions: aies/tR@ik/sRwai/-s -> aies/svtRwaiek/-s
    invitation: aie/vi/ta/sRwai -> aie/vi/svtRwaiek
    destruction: pves/tR@ik/sRwai -> pves/svtRwaiek
    accusation: a/k@i/twa/sRwai -> a/k@i/svtRwaiek
    objection: ej/vtiek/sRwai -> ej/svtRwaiek
    construction: kais/tR@ik/sRwai -> kais/svtRwaiek
    bénédiction: sve/mRe/pvik/sRwai -> sve/mRe/svtRwaiek
    civilisation: si/vi/mti/twa/sRwai -> si/vi/mti/svtRwaiek

## S047 (suffix) -- ·[ce|cie|cu|dre|dé|li|llie|ple|plé|pplé|sce|se|sse|tie]ment

- dedicated keys [4, 5, 6, 7, 8, 11, 12, 13] = `pvmtR@ai` for ·[ce|cie|cu|dre|dé|li|llie|ple|plé|pplé|sce|se|sse|tie]ment (sim 0.28, comfort 487.0)
- strokeFreqSaved 394.6, freqBenefiting 394.6 of 394.6 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[4, 5, 6, 7, 8, 11, 12, 13]] sim 0.28 saved 394.6; dedicated [[16, 17, 18]] sim 0.24 saved 394.6; dedicated [[16, 18, 19]] sim 0.24 saved 394.6; dedicated [[16, 18, 21]] sim 0.24 saved 394.6; dedicated [[16, 18, 23]] sim 0.24 saved 394.6

    doucement: pv@e/s@a/m@ -> pv@e/pvmtR@ai
    simplement: saie/pmt@a/m@ -> saie/pvmtR@ai
    profondément: pRae/kpai/pve/m@ -> pRae/kpai/pvmtR@ai
    documents: pvae/k@i/m@/-s -> pvae/pvmtR@ai/-s
    document: pvae/k@i/m@ -> pvae/pvmtR@ai
    avertissement: a/vieR/ti/s@a/m@ -> a/vieR/ti/pvmtR@ai
    lancement: mt@/s@a/m@ -> mt@/pvmtR@ai
    applaudissements: a/pmtae/pvi/s@a/m@/-s -> a/pmtae/pvi/pvmtR@ai/-s
    commencement: kae/m@/s@a/m@ -> kae/m@/pvmtR@ai
    investissement: aie/vies/ti/s@a/m@ -> aie/vies/ti/pvmtR@ai

## P070 (prefix) -- géné

- merged keys [5, 7, 22] = `vt-n` for géné (sim 0.6, comfort 503.3)
- strokeFreqSaved 389.5, freqBenefiting 194.8 of 204.5 (share by freq 0.952, by count 0.826), boundary risks 0
- fallbacks: {'keyOverlap': 4}
- alternatives: merged [[5, 7, 22]] sim 0.6 saved 389.5; merged [[5, 7, 14]] sim 0.5 saved 377.5; merged [[14, 22, 24]] sim 0.5 saved 76.7; merged [[6, 8, 14]] sim 0.5 saved 19.5; merged [[6, 8, 24]] sim 0.6 saved 19.5

    général: vte/mRe/Ral -> vtRanl
    général: vte/mRe/Ral -> vtRanl
    génération: vte/mRe/Ra/sRwai -> vtRan/sRwai
    générale: vte/mRe/Ral/-j -> vtRanl/-j
    généralement: vte/mRe/Ra/mt@a/m@ -> vtRan/mt@a/m@
    générations: vte/mRe/Ra/sRwai/-s -> vtRan/sRwai/-s
    généraux: vte/mRe/Rae -> vtRaen
    généraux: vte/mRe/Rae -> vtRaen
    générale: vte/mRe/Ral/-j -> vtRanl/-j
    générales: vte/mRe/Ral/-js -> vtRanl/-js

## P009 (prefix) -- ai·, ai°·, ais·

- dedicated keys [3, 12, 13, 17] = `sais` for ai·, ai°·, ais· (sim 0.16, comfort 335.0)
- strokeFreqSaved 387.7, freqBenefiting 387.7 of 1367.5 (share by freq 0.284, by count 0.658), boundary risks 0
- fallbacks: {'markCostTooHigh': 231}
- alternatives: dedicated [[3, 12, 13, 17]] sim 0.16 saved 387.7; dedicated [[3, 5, 6, 11, 12, 13]] sim -0.019 saved 387.7; dedicated [[3, 6, 11, 12, 13, 17]] sim -0.019 saved 387.7; dedicated [[3, 8, 13, 17]] sim -0.258 saved 387.7; dedicated [[3, 5, 6, 7, 11, 12, 13]] sim -0.258 saved 387.7

    arrivera: a/Ri/v@a/Ra -> sais/v@a/Ra
    animaux: a/mRi/mae -> sais/mae
    animal: a/mRi/mal -> sais/mal
    ennemis: ie/mR@a/mi/-s -> sais/mi/-s
    arriverai: a/Ri/v@a/Re/-t -> sais/v@a/Re/-t
    arriverait: a/Ri/v@a/Rie -> sais/v@a/Rie
    arrivant: a/Ri/v@ -> sais/v@
    arriveras: a/Ri/v@a/Ra/-d -> sais/v@a/Ra/-d
    habituer: a/svi/t@ae/-l -> sais/t@ae/-l
    haricots: a/Ri/kae/-s -> sais/kae/-s

## S081 (suffix) -- lleur, illir, illeur, ière

- merged keys [16, 18, 21] = `-jkR` for lleur, illir, illeur, ière (sim 0.7, comfort 506.5)
- strokeFreqSaved 367.4, freqBenefiting 367.4 of 367.4 (share by freq 1.0, by count 1.0), boundary risks 2
- fallbacks: {}
- alternatives: merged [[11, 16, 21]] sim 0.892 saved 336.7; merged [[16, 17, 21]] sim 0.7 saved 367.4; merged [[16, 20, 21]] sim 0.7 saved 367.4; merged [[16, 18, 21]] sim 0.7 saved 367.4

    meilleur: mie/Rw@R -> miejkR
    meilleure: mie/Rw@R/-j -> miejkR/-j
    meilleur: mie/Rw@R -> miejkR
    meilleurs: mie/Rw@R/-s -> miejkR/-s
    meilleure: mie/Rw@R/-j -> miejkR/-j
    meilleures: mie/Rw@R/-js -> miejkR/-js
    meilleurs: mie/Rw@R/-s -> miejkR/-s
    accueillir: a/k@/RwiR -> a/k@jkR
    travailleurs: tRa/va/Rw@R/-s -> tRa/vajkR/-s
    cueillir: k@/RwiR -> k@jkR

## S080 (suffix) -- ssible, tile, sible, sible, tible

- merged keys [16, 20, 23] = `-jtl` for ssible, tile, sible, sible, tible (sim 0.639, comfort 582.5)
- strokeFreqSaved 362.6, freqBenefiting 362.6 of 374.9 (share by freq 0.967, by count 0.904), boundary risks 0
- fallbacks: {'keyOverlap': 16}
- alternatives: merged [[16, 17, 23]] sim 0.71 saved 346.5; merged [[16, 20, 23]] sim 0.639 saved 362.6; merged [[3, 16, 23]] sim 0.623 saved 322.1; merged [[17, 20, 23]] sim 0.588 saved 358.8; merged [[7, 16, 23]] sim 0.587 saved 350.3

    impossible: aie/pae/sijl -> aie/paejtl
    inutile: i/mR@i/til -> i/mR@ijtl
    impossible: aie/pae/sijl -> aie/paejtl
    sensible: s@/sijl -> s@jtl
    invisible: aie/vi/twijl -> aie/vijtl
    inutiles: i/mR@i/til/-s -> i/mR@ijtl/-s
    inutile: i/mR@i/til -> i/mR@ijtl
    hostile: es/til -> ejstl
    paisible: pe/twijl -> pejtl
    sensibles: s@/sijl/-s -> s@jtl/-s

## P067 (prefix) -- su, sus

- merged keys [3, 11] = `s@` for su, sus (sim 0.5, comfort 491.8)
- strokeFreqSaved 361.2, freqBenefiting 361.2 of 419.5 (share by freq 0.861, by count 0.371), boundary risks 3
- fallbacks: {'keyOverlap': 158}
- alternatives: merged [[3]] sim 0.667 saved 381.6; merged [[2, 3]] sim 0.5 saved 374.9; merged [[3, 12]] sim 0.5 saved 381.5; merged [[3, 11]] sim 0.5 saved 361.2; merged [[3, 9]] sim 0.5 saved 377.3

    super: s@i/pieR -> sp@ieR
    sujet: s@i/vtie -> svt@ie
    super: s@i/pieR -> sp@ieR
    sujets: s@i/vtie/-s -> svt@ie/-s
    sujet: s@i/vtie -> svt@ie
    sucré: s@i/kRe -> ksR@e
    supers: s@i/pieR/-s -> sp@ieR/-s
    sucrière: s@i/kRij/ieR -> ksR@ij/ieR
    sucrée: s@i/kRe/-j -> ksR@e/-j
    sucré: s@i/kRe -> ksR@e

## S063 (suffix) -- ·[du|fi|for|lli|ni|to|xi|xpli]mations

- dedicated keys [2, 3, 4, 6, 7, 8, 9, 12, 13] = `kspmtRwai` for ·[du|fi|for|lli|ni|to|xi|xpli]mations (sim 0.303, comfort 522.0)
- strokeFreqSaved 357.2, freqBenefiting 178.6 of 178.6 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 3, 4, 6, 7, 8, 9, 12, 13]] sim 0.303 saved 357.2; dedicated [[2, 3, 4, 5, 6, 7, 11, 13]] sim 0.276 saved 357.2; dedicated [[2, 3, 4, 6, 7, 13, 14, 21]] sim 0.276 saved 357.2; dedicated [[16, 17, 18]] sim 0.263 saved 357.2; dedicated [[16, 17, 19]] sim 0.263 saved 357.2

    informations: aie/kpeR/ma/sRwai/-s -> aie/kspmtRwai/-s
    explication: ie/kspmti/ka/sRwai -> ie/kspmtRwai
    information: aie/kpeR/ma/sRwai -> aie/kspmtRwai
    éducation: e/pv@i/ka/sRwai -> e/kspmtRwai
    communication: kae/m@i/mRi/ka/sRwai -> kae/m@i/kspmtRwai
    explications: ie/kspmti/ka/sRwai/-s -> ie/kspmtRwai/-s
    identification: i/pv@/ti/kpi/ka/sRwai -> i/pv@/ti/kspmtRwai
    signification: si/wi/kpi/ka/sRwai -> si/wi/kspmtRwai
    communications: kae/m@i/mRi/ka/sRwai/-s -> kae/m@i/kspmtRwai/-s
    vérification: ve/Ri/kpi/ka/sRwai -> ve/Ri/kspmtRwai

## S083 (suffix) -- ·athique, ·astique, ·ative, ·atie

- merged keys [17, 18, 20] = `-skt` for ·athique, ·astique, ·ative, ·atie (sim 0.609, comfort 551.8)
- strokeFreqSaved 356.7, freqBenefiting 178.4 of 182.8 (share by freq 0.976, by count 0.845), boundary risks 0
- fallbacks: {'keyOverlap': 32}
- alternatives: merged [[17, 18, 20]] sim 0.609 saved 356.7; merged [[13, 18, 20]] sim 0.563 saved 286.8; merged [[3, 18, 20]] sim 0.545 saved 319.2; merged [[5, 18, 20]] sim 0.514 saved 331.4; merged [[2, 17, 20]] sim 0.505 saved 240.4

    fantastique: kp@/tas/tik -> kp@skt
    tentative: t@/ta/tijs -> t@skt
    sympathique: saie/pa/tik -> saieskt
    démocratie: pve/mae/kRa/si -> pve/maeskt
    pharmacie: kpaR/ma/si -> kpasktR
    fantastique: kp@/tas/tik -> kp@skt
    dramatique: pvRa/ma/tik -> pvRaskt
    initiative: i/mRi/sRwa/tijs -> i/mRiskt
    automatique: ae/tae/ma/tik -> ae/taeskt
    démocratique: pve/mae/kRa/tik -> pve/maeskt

## P073 (prefix) -- mou, mous

- merged keys [6, 17] = `m-s` for mou, mous (sim 0.661, comfort 452.3)
- strokeFreqSaved 348.2, freqBenefiting 348.2 of 371.4 (share by freq 0.937, by count 0.632), boundary risks 0
- fallbacks: {'keyOverlap': 33, 'markCostTooHigh': 2}
- alternatives: merged [[3, 6]] sim 0.678 saved 348.9; merged [[6, 17]] sim 0.661 saved 348.2; merged [[3, 5, 6]] sim 0.517 saved 348.0

    mourir: m@e/RiR -> mRisR
    mourra: m@e/Ra -> mRas
    moustache: m@es/taZm -> mtasZm
    moutons: m@e/tai/-s -> mtais/-s
    mourras: m@e/Ra/-d -> mRas/-d
    mourrai: m@e/Re/-t -> mRes/-t
    mouton: m@e/tai -> mtais
    mourut: m@e/R@i -> mR@is
    mourrez: m@e/Re/-dt -> mRes/-dt
    mourrais: m@e/Rie/-kl -> mRies/-kl

## P066 (prefix) -- sii·, mii·, vii·, ii·

- merged keys [3, 5, 6, 17] = `svm-s` for sii·, ii· (sim 0.641, comfort 583.5)
- merged keys [3, 5, 6, 25] = `svm-m` for mii· (sim 0.641, comfort 583.5)
- merged keys [3, 5, 6, 8] = `svmR-` for vii· (sim 0.641, comfort 583.5)
- strokeFreqSaved 342.0, freqBenefiting 176.2 of 218.5 (share by freq 0.807, by count 0.449), boundary risks 1
- fallbacks: {'keyOverlap': 170, 'markCostTooHigh': 9}
- alternatives: merged [[3, 5, 6, 17], [3, 5, 6, 25], [3, 5, 6, 8]] sim 0.641 saved 342.0; merged [[3, 6, 17], [3, 6, 25], [3, 5, 6]] sim 0.529 saved 348.4; merged [[3, 5, 17, 25], [3, 5, 6, 25], [3, 5, 8, 25]] sim 0.521 saved 378.8; merged [[3, 6, 13, 17], [6, 13, 17, 25], [5, 6, 13, 17]] sim 0.564 saved 97.6; merged [[3, 5, 6, 13], [5, 6, 13, 25], [5, 6, 8, 13]] sim 0.531 saved 86.3

    signifie: si/wi/kpi -> kspvmis
    militaire: mi/mti/tieR -> svmtieRm
    visiter: vi/twi/te/-l -> svmtRe/-l
    militaires: mi/mti/tieR/-s -> svmtieRm/-s
    militaires: mi/mti/tieR/-s -> svmtieRm/-s
    imiter: i/mi/te/-l -> svmtes/-l
    visité: vi/twi/te -> svmtRe
    signifiait: si/wi/kpRwie -> kspvmRwies
    militaire: mi/mti/tieR -> svmtieRm
    signifient: si/wi/kpi/-st -> kspvmis/-st

## P045 (prefix) -- ui·, sui·, oui·, pui·

- dedicated keys [3, 4, 11, 13] = `sp@i` for ui·, sui·, oui·, pui· (sim 0.551, comfort 396.0)
- strokeFreqSaved 329.9, freqBenefiting 329.9 of 396.9 (share by freq 0.831, by count 0.779), boundary risks 0
- fallbacks: {'markCostTooHigh': 61}
- alternatives: dedicated [[3, 4, 11, 13]] sim 0.551 saved 329.9; dedicated [[3, 6, 11, 13]] sim 0.275 saved 329.9; dedicated [[3, 7, 11, 13]] sim 0.275 saved 329.9; dedicated [[4, 7, 11, 13]] sim 0.259 saved 329.9; dedicated [[7, 11, 13, 14]] sim 0.217 saved 329.9

    utiliser: @i/ti/mti/twe/-l -> sp@i/mti/twe/-l
    univers: @i/mRi/vieR -> sp@i/vieR
    utilise: @i/ti/mtinl -> sp@i/mtinl
    utilisé: @i/ti/mti/twe -> sp@i/mti/twe
    uniforme: @i/mRi/kpeRm -> sp@i/kpeRm
    suffisant: s@i/kpi/tw@ -> sp@i/tw@
    utilisez: @i/ti/mti/twe/-k -> sp@i/mti/twe/-k
    utilisent: @i/ti/mtinl/-st -> sp@i/mtinl/-st
    uniformes: @i/mRi/kpeRm/-s -> sp@i/kpeRm/-s
    supprimer: s@i/pRi/me/-l -> sp@i/me/-l

## S084 (suffix) -- ber, brer

- merged keys [14, 16, 17] = `ejs` for ber, brer (sim 0.64, comfort 418.2)
- strokeFreqSaved 327.9, freqBenefiting 327.9 of 361.9 (share by freq 0.906, by count 0.623), boundary risks 5
- fallbacks: {'keyOverlap': 108, 'markCostTooHigh': 1}
- alternatives: merged [[14, 16]] sim 0.8 saved 327.9; merged [[8, 16]] sim 0.66 saved 354.5; merged [[14, 16, 17]] sim 0.64 saved 327.9; merged [[9, 14, 16]] sim 0.64 saved 327.9; merged [[14, 16, 18]] sim 0.64 saved 327.9

    tomber: tai/sve/-l -> taiejs/-l
    tombé: tai/sve -> taiejs
    tombée: tai/sve/-j -> taiejs/-j
    tombés: tai/sve/-s -> taiejs/-s
    tombez: tai/sve/-k -> taiejs/-k
    perturbé: pieR/t@iR/sve -> pieR/t@iejsR
    retomber: R@a/tai/sve/-l -> R@a/taiejs/-l
    perturber: pieR/t@iR/sve/-l -> pieR/t@iejsR/-l
    sombrer: sai/svRe/-l -> saiejs/-l
    tombées: tai/sve/-js -> taiejs/-js

## P053 (prefix) -- hôi·, soi·

- dedicated keys [3, 8, 12, 13, 14] = `sRaie` for hôi·, soi· (sim 0.301, comfort 414.0)
- strokeFreqSaved 327.2, freqBenefiting 327.2 of 328.5 (share by freq 0.996, by count 0.92), boundary risks 0
- fallbacks: {'markCostTooHigh': 16}
- alternatives: dedicated [[3, 8, 12, 13, 14]] sim 0.301 saved 327.2; dedicated [[3, 4, 12, 13, 14]] sim 0.301 saved 327.2; dedicated [[3, 8, 13]] sim 0.068 saved 327.2; dedicated [[2, 3, 4, 12, 13, 14]] sim 0.068 saved 327.2; dedicated [[3, 6, 7, 12, 13, 14]] sim 0.068 saved 327.2

    hôpital: ae/pi/tal -> sRaie/tal
    obligé: ae/svmti/vte -> sRaie/vte
    origine: ae/Ri/vtin -> sRaie/vtin
    aussitôt: ae/si/tae -> sRaie/tae
    obligée: ae/svmti/vte/-j -> sRaie/vte/-j
    solitaire: sae/mti/tieR -> sRaie/tieR
    obligés: ae/svmti/vte/-s -> sRaie/vte/-s
    officiel: ae/kpi/sRwiel -> sRaie/sRwiel
    officielle: ae/kpi/sRwiel/-j -> sRaie/sRwiel/-j
    horizon: ae/Ri/twai -> sRaie/twai

## P037 (prefix) -- em°·, é@·, en@·, emE·

- dedicated keys [6, 7, 11, 12, 14] = `mt@ae` for em°·, é@·, en@·, emE· (sim -0.06, comfort 328.0)
- strokeFreqSaved 322.6, freqBenefiting 322.6 of 488.8 (share by freq 0.66, by count 0.718), boundary risks 0
- fallbacks: {'markCostTooHigh': 218}
- alternatives: dedicated [[11, 12]] sim 0.409 saved 322.6; dedicated [[6, 7, 11, 12, 14]] sim -0.06 saved 322.6; dedicated [[7, 8, 11, 12, 14]] sim -0.06 saved 322.6; dedicated [[4, 6, 11, 12]] sim -0.127 saved 322.5; dedicated [[7, 8, 11, 12]] sim -0.127 saved 322.6

    enlever: @/mt@a/ve/-l -> mt@ae/ve/-l
    emmenez: @/m@a/mRe/-k -> mt@ae/mRe/-k
    entreprise: @/tR@a/pRinl -> mt@ae/pRinl
    enlevé: @/mt@a/ve -> mt@ae/ve
    enlevez: @/mt@a/ve/-k -> mt@ae/ve/-k
    entretien: @/tR@a/tRwaie -> mt@ae/tRwaie
    entendue: @/t@/pv@i/-j -> mt@ae/pv@i/-j
    enlevée: @/mt@a/ve/-j -> mt@ae/ve/-j
    entretenir: @/tR@a/t@a/mRiR -> mt@ae/t@a/mRiR
    entrepôt: @/tR@a/pae -> mt@ae/pae

## S071 (suffix) -- ·ERser, ·ORter, ·ORmer, ·aRder, ·ERner

- merged keys [3, 17, 20, 21] = `s-stR` for ·ERser (sim 0.556, comfort 651.3)
- merged keys [17, 19, 20, 21] = `-sdtR` for ·aRder, ·ERner (sim 0.556, comfort 651.3)
- merged keys [7, 17, 20, 21] = `t-stR` for ·ORter (sim 0.556, comfort 651.3)
- merged keys [17, 20, 21, 25] = `-stRm` for ·ORmer (sim 0.556, comfort 651.3)
- strokeFreqSaved 319.7, freqBenefiting 173.3 of 237.7 (share by freq 0.729, by count 0.751), boundary risks 0
- fallbacks: {'keyOverlap': 146, 'markCostTooHigh': 5}
- alternatives: merged [[3, 14, 17, 21], [14, 17, 19, 21], [14, 17, 20, 21], [14, 17, 21, 25]] sim 0.603 saved 303.8; merged [[3, 17, 20, 21], [17, 19, 20, 21], [7, 17, 20, 21], [17, 20, 21, 25]] sim 0.556 saved 319.7; merged [[3, 17, 21, 25], [17, 19, 21, 25], [17, 20, 21, 25], [6, 17, 21, 25]] sim 0.538 saved 319.4; merged [[3, 17, 19, 21], [17, 19, 21, 22], [17, 19, 20, 21], [17, 19, 21, 25]] sim 0.532 saved 319.4; merged [[3, 14, 17, 21], [3, 14, 19, 21], [3, 14, 20, 21], [3, 14, 21, 25]] sim 0.523 saved 378.4

    traverser: tRa/vieR/se/-l -> stRastR/-l
    traversé: tRa/vieR/s*e -> stR*astR
    renversé: R@/vieR/se -> sR@stR
    renverser: R@/vieR/se/-l -> sR@stR/-l
    comporter: kai/peR/te/-l -> ktaistR/-l
    poignardé: pwa/waR/pve -> pwasdtR
    bouleversé: sv@e/mt@a/vieR/se -> sv@e/smt@astR
    bouleversée: sv@e/mt@a/vieR/se/-j -> sv@e/smt@astR/-j
    traversée: tRa/vieR/se -> stRastR
    concernant: kai/sieR/mR@ -> kaisdtR/mR@

## P084 (prefix) -- pu

- merged keys [4] = `p-` for pu (sim 0.667, comfort 431.9)
- strokeFreqSaved 315.2, freqBenefiting 315.2 of 317.0 (share by freq 0.995, by count 0.833), boundary risks 2
- fallbacks: {'markCostTooHigh': 1, 'keyOverlap': 3}
- alternatives: merged [[4]] sim 0.667 saved 315.2; merged [[4, 5]] sim 0.5 saved 313.8; merged [[4, 9]] sim 0.5 saved 312.7; merged [[4, 11]] sim 0.5 saved 316.2; merged [[2, 4]] sim 0.5 saved 316.2

    putain: p@i/taie -> ptaie
    putains: p@i/taie/-s -> ptaie/-s
    punie: p@i/mRi/-j -> pmRi/-j
    pucelle: p@i/siel -> spiel
    putois: p@i/twa -> ptwa
    pucelle: p@i/siel -> spiel
    pubiens: p@i/svRwaie/-s -> spvRwaie/-s
    pubis: p@i/svis -> spvis
    pubien: p@i/svRwaie -> spvRwaie
    punie: p@i/mRi/-j -> pmRi/-j

## P079 (prefix) -- mar, mer

- merged keys [8, 25] = `R-m` for mar, mer (sim 0.6, comfort 465.2)
- strokeFreqSaved 314.6, freqBenefiting 314.6 of 341.6 (share by freq 0.921, by count 0.881), boundary risks 11
- fallbacks: {'keyOverlap': 18, 'illegalChord': 3}
- alternatives: merged [[8, 12, 25]] sim 0.674 saved 272.9; merged [[8, 25]] sim 0.6 saved 314.6; merged [[8, 24, 25]] sim 0.5 saved 312.1; merged [[5, 8, 25]] sim 0.5 saved 252.2; merged [[2, 8, 25]] sim 0.5 saved 292.1

    marcher: maR/pme/-l -> pmRem/-l
    marché: maR/pme -> pmRem
    merveilleuse: mieR/vie/Rw@ienl -> vRiem/Rw@ienl
    marchera: maR/pm@a/Ra -> pmR@am/Ra
    marqué: maR/ke -> kRem
    merveille: mieR/viej -> vRiejm
    marchait: maR/pmie -> pmRiem
    merdé: mieR/pve -> pvRem
    marchand: maR/pm@ -> pmR@m
    marchez: maR/pme/-k -> pmRem/-k

## P048 (prefix) -- ay·, séy·, éy·, amy·

- dedicated keys [3, 6, 11, 13, 14] = `sm@ie` for ay·, séy·, éy·, amy· (sim 0.359, comfort 432.0)
- strokeFreqSaved 313.5, freqBenefiting 313.5 of 383.8 (share by freq 0.817, by count 0.725), boundary risks 0
- fallbacks: {'markCostTooHigh': 131}
- alternatives: dedicated [[3, 6, 11, 13, 14]] sim 0.359 saved 313.5; dedicated [[2, 3, 11, 13]] sim 0.265 saved 313.5; dedicated [[3, 6, 11, 13]] sim 0.265 saved 313.5; dedicated [[3, 6, 7, 11, 13, 14]] sim 0.169 saved 313.5; dedicated [[11, 12]] sim 0.096 saved 313.0

    sécurité: se/k@i/Ri/te -> sm@ie/Ri/te
    ambulance: @/sv@i/mt@s -> sm@ie/mt@s
    amusant: a/m@i/tw@ -> sm@ie/tw@
    assurance: a/s@i/R@s -> sm@ie/R@s
    éducation: e/pv@i/ka/sRwai -> sm@ie/ka/sRwai
    étudié: e/t@i/pvRwe -> sm@ie/pvRwe
    étudie: e/t@i/pvi -> sm@ie/pvi
    assurez: a/s@i/Re/-k -> sm@ie/Re/-k
    assurances: a/s@i/R@s/-s -> sm@ie/R@s/-s
    amusés: a/m@i/twe/-s -> sm@ie/twe/-s

## P081 (prefix) -- trans, tran, bran, trans

- merged keys [3, 7, 8, 20] = `stR-t` for trans, tran, trans (sim 0.804, comfort 656.6)
- merged keys [3, 7, 8, 16] = `stR-j` for bran (sim 0.804, comfort 656.6)
- strokeFreqSaved 311.0, freqBenefiting 311.0 of 340.4 (share by freq 0.914, by count 0.755), boundary risks 0
- fallbacks: {'keyOverlap': 121}
- alternatives: merged [[3, 7, 8, 20], [3, 7, 8, 16]] sim 0.804 saved 311.0; merged [[3, 7, 8, 17], [7, 8, 16, 17]] sim 0.719 saved 323.5; merged [[3, 7, 8, 11], [7, 8, 11, 16]] sim 0.716 saved 316.7; merged [[3, 7, 8, 20], [3, 8, 16, 20]] sim 0.653 saved 316.6; merged [[3, 7, 8, 16], [7, 8, 16, 21]] sim 0.648 saved 321.4

    tranquille: tR@/kil -> kstRitl
    tranquilles: tR@/kil/-s -> kstRitl/-s
    transport: tR@s/peR -> sptRetR
    transformer: tR@s/kpeR/me/-l -> ksptRetR/me/-l
    transfert: tR@s/kpieR -> ksptRietR
    transforme: tR@s/kpeRm -> ksptRetRm
    transformé: tR@s/kpeR/me -> ksptRetR/me
    transmission: tR@s/mi/sRwai -> smtRit/sRwai
    transporter: tR@s/peR/te/-l -> sptRetR/te/-l
    transports: tR@s/peR/-s -> sptRetR/-s

## P042 (prefix) -- ra, rao·

- merged keys [8, 9, 12, 18] = `Rwak` for ra (sim 0.646, comfort 579.1)
- merged keys [2, 8, 12, 18] = `kRak` for rao· (sim 0.646, comfort 579.1)
- strokeFreqSaved 310.8, freqBenefiting 305.7 of 777.2 (share by freq 0.393, by count 0.452), boundary risks 0
- fallbacks: {'keyOverlap': 428, 'markCostTooHigh': 13}
- alternatives: merged [[8, 9], [2, 8]] sim 0.646 saved 753.1; merged [[8, 9, 12], [2, 8, 12]] sim 0.807 saved 310.8; merged [[8, 9, 12, 18], [2, 8, 12, 18]] sim 0.646 saved 310.8; merged [[8, 9, 12, 19], [2, 8, 12, 19]] sim 0.646 saved 310.8; merged [[8, 9, 12, 16], [2, 8, 12, 16]] sim 0.646 saved 310.1

    ramène: Ra/mien -> mRwaiekn
    ravi: Ra/vi -> vRwaik
    raté: Ra/te -> tRwaek
    rater: Ra/te/-l -> tRwaek/-l
    ravie: Ra/vi/-j -> vRwaik/-j
    racines: Ra/sin/-s -> sRwaikn/-s
    ramènes: Ra/mien/-d -> mRwaiekn/-d
    raccroché: Ra/kRae/pme -> kpmRaek
    rapprocher: Ra/pRae/pme/-l -> kpmRaek/-l
    raccrocher: Ra/kRae/pme/-l -> kpmRaek/-l

## S067 (suffix) -- ·[bi|chi|cri|join|pa|pâ|thi|ti|tti|vai|ve|vei|voû|vè|vé|vê]nements

- dedicated keys [16, 18, 20] = `-jkt` for ·[bi|chi|cri|join|pa|pâ|thi|ti|tti|vai|ve|vei|voû|vè|vé|vê]nements (sim 0.303, comfort 214.0)
- strokeFreqSaved 306.4, freqBenefiting 153.2 of 153.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 18, 20]] sim 0.303 saved 306.4; dedicated [[16, 17, 18]] sim 0.303 saved 306.4; dedicated [[16, 18, 21]] sim 0.303 saved 306.4; dedicated [[16, 18, 24]] sim 0.303 saved 306.4; dedicated [[16, 18, 25]] sim 0.303 saved 306.4

    évènements: e/vie/mR@a/m@/-s -> e/-jkt/-s
    pratiquement: pRa/ti/k@a/m@ -> pRa/-jkt
    événement: e/vie/mR@a/m@ -> e/-jkt
    effectivement: e/kpiek/ti/v@a/m@ -> e/kpiek/-jkt
    définitivement: pve/kpi/mRi/ti/v@a/m@ -> pve/kpi/mRi/-jkt
    avertissement: a/vieR/ti/s@a/m@ -> a/vieR/-jkt
    attentivement: a/t@/ti/v@a/m@ -> a/t@/-jkt
    investissement: aie/vies/ti/s@a/m@ -> aie/vies/-jkt
    relativement: R@a/mta/ti/v@a/m@ -> R@a/mta/-jkt
    subitement: s@i/svi/t@a/m@ -> s@i/-jkt

## P072 (prefix) -- si, ci, cir

- merged keys [3, 14, 21] = `seR` for si, ci, cir (sim 0.5, comfort 544.2)
- strokeFreqSaved 305.5, freqBenefiting 305.5 of 380.4 (share by freq 0.803, by count 0.618), boundary risks 0
- fallbacks: {'keyOverlap': 100}
- alternatives: merged [[3, 21]] sim 0.653 saved 351.8; merged [[3, 14, 21]] sim 0.5 saved 305.5; merged [[3, 5, 21]] sim 0.5 saved 318.4; merged [[3, 20, 21]] sim 0.5 saved 353.5

    sinon: si/mRai -> smRaieR
    cimetière: si/m@a/tRwieR -> sm@aeR/tRwieR
    circonstances: siR/kais/t@s/-s -> ksaiesR/t@s/-s
    civile: si/vil/-j -> svieRl/-j
    citron: si/tRai -> stRaieR
    civils: si/vil/-s -> svieRl/-s
    circuit: siR/k@ai -> ks@aieR
    civil: si/vil -> svieRl
    civil: si/vil -> svieRl
    circulez: siR/k@i/mte/-k -> ks@ieR/mte/-k

## S091 (suffix) -- lot, lon, lo

- merged keys [13, 23] = `il` for lot, lon, lo (sim 0.5, comfort 449.8)
- strokeFreqSaved 305.1, freqBenefiting 305.1 of 330.1 (share by freq 0.924, by count 0.727), boundary risks 5
- fallbacks: {'keyOverlap': 34, 'markCostTooHigh': 2}
- alternatives: merged [[13, 23]] sim 0.5 saved 305.1; merged [[21, 23]] sim 0.5 saved 327.2; merged [[9, 23]] sim 0.5 saved 316.2; merged [[2, 23]] sim 0.5 saved 311.3; merged [[6, 23]] sim 0.5 saved 323.5

    boulot: sv@e/mtae -> sv@iel
    pantalon: p@/ta/mtai -> p@/tail
    violon: vRwae/mtai -> vRwaiel
    boulot: sv@e/mtae -> sv@iel
    pantalons: p@/ta/mtai/-s -> p@/tail/-s
    étalon: e/ta/mtai -> e/tail
    rigolo: Ri/ksae/mtae -> Ri/ksaiel
    matelot: ma/t@a/mtae -> ma/t@ail
    boulots: sv@e/mtae/-s -> sv@iel/-s
    rigolo: Ri/ksae/mtae -> Ri/ksaiel

## S095 (suffix) -- taine, tine, trine, trie, trice

- merged keys [20, 21, 22] = `-tRn` for taine, tine, trine, trie, trice (sim 0.79, comfort 476.1)
- strokeFreqSaved 302.8, freqBenefiting 302.8 of 307.0 (share by freq 0.986, by count 0.943), boundary risks 1
- fallbacks: {'keyOverlap': 7}
- alternatives: merged [[20, 21, 22]] sim 0.79 saved 302.8; merged [[8, 20, 22]] sim 0.748 saved 273.8; merged [[17, 20, 22]] sim 0.728 saved 293.6; merged [[3, 20, 22]] sim 0.717 saved 273.9; merged [[20, 22]] sim 0.706 saved 307.0

    capitaine: ka/pi/tien -> ka/pitRn
    poitrine: pwa/tRin -> pwatRn
    centaines: s@/tien/-s -> s@tRn/-s
    routine: R@e/tin -> R@etRn
    industrie: aie/pv@is/tRi -> aie/pv@istRn
    cicatrice: si/ka/tRis -> si/katRn
    quarantaine: ka/R@/tien -> ka/R@tRn
    fontaine: kpai/tien -> kpaitRn
    centaine: s@/tien -> s@tRn
    cicatrices: si/ka/tRis/-s -> si/katRn/-s

## S058 (suffix) -- ·[di|die|ge|glé|gne|gré|le|lé|ve|xcré]ment

- dedicated keys [2, 3, 4, 5, 6, 7, 13, 14] = `kspvmtie` for ·[di|die|ge|glé|gne|gré|le|lé|ve|xcré]ment (sim 0.3, comfort 449.0)
- strokeFreqSaved 302.7, freqBenefiting 302.7 of 302.7 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 3, 4, 5, 6, 7, 13, 14]] sim 0.3 saved 302.7; dedicated [[2, 3, 5, 6, 7, 11, 12, 14]] sim 0.283 saved 302.7; dedicated [[18, 19, 21]] sim 0.267 saved 302.7; dedicated [[18, 19, 23]] sim 0.267 saved 302.7; dedicated [[17, 18, 19]] sim 0.267 saved 302.7

    mouvement: m@e/v@a/m@ -> m@e/kspvmtie
    changement: pm@/vt@a/m@ -> pm@/kspvmtie
    jugement: vt@i/vt@a/m@ -> vt@i/kspvmtie
    renseignements: R@/sie/w@a/m@/-s -> R@/sie/kspvmtie/-s
    éléments: e/mte/m@/-s -> e/kspvmtie/-s
    effectivement: e/kpiek/ti/v@a/m@ -> e/kpiek/ti/kspvmtie
    mouvements: m@e/v@a/m@/-s -> m@e/kspvmtie/-s
    changements: pm@/vt@a/m@/-s -> pm@/kspvmtie/-s
    élément: e/mte/m@ -> e/kspvmtie
    engagement: @/ksa/vt@a/m@ -> @/ksa/kspvmtie

## P023 (prefix) -- a°·, ra°·, mae·, pa°·, ca°·, ma°·, ga°·, man°·

- dedicated keys [4, 6, 8, 11, 12] = `pmR@a` for a°·, ra°·, mae·, pa°·, ca°·, ma°·, ga°·, man°· (sim 0.561, comfort 341.0)
- strokeFreqSaved 302.3, freqBenefiting 302.3 of 826.1 (share by freq 0.366, by count 0.496), boundary risks 0
- fallbacks: {'markCostTooHigh': 253}
- alternatives: dedicated [[4, 6, 8, 11, 12]] sim 0.561 saved 302.3; dedicated [[4, 6, 11, 12]] sim 0.495 saved 288.0; dedicated [[4, 8, 11, 12]] sim 0.463 saved 301.7; dedicated [[8, 11, 12]] sim 0.428 saved 277.2; dedicated [[11, 12, 25]] sim 0.411 saved 302.3

    allemands: a/mt@a/m@/-s -> pmR@a/m@/-s
    matériel: ma/te/Rwiel -> pmR@a/Rwiel
    amenez: a/m@a/mRe/-k -> pmR@a/mRe/-k
    allemand: a/mt@a/m@ -> pmR@a/m@
    allemand: a/mt@a/m@ -> pmR@a/m@
    atelier: a/t@a/mtRwe -> pmR@a/mtRwe
    malédiction: ma/mte/pvik/sRwai -> pmR@a/pvik/sRwai
    ramenez: Ra/m@a/mRe/-k -> pmR@a/mRe/-k
    allemande: a/mt@a/m@d -> pmR@a/m@d
    matelas: ma/t@a/mta -> pmR@a/mta

## S090 (suffix) -- naire, ·inaire, ·onnaire, ·°naire, nnaire, neur

- merged keys [8, 22] = `R-n` for naire, ·inaire, ·onnaire, ·°naire, nnaire, neur (sim 0.542, comfort 496.2)
- strokeFreqSaved 302.2, freqBenefiting 184.1 of 223.1 (share by freq 0.826, by count 0.777), boundary risks 14
- fallbacks: {'keyOverlap': 59}
- alternatives: merged [[8, 11, 22]] sim 0.552 saved 257.6; merged [[8, 22]] sim 0.542 saved 302.2; merged [[19, 21, 22]] sim 0.633 saved 197.3; merged [[20, 21, 22]] sim 0.633 saved 197.3; merged [[21, 22]] sim 0.723 saved 197.3

    extraordinaire: ie/kstRa/eR/pvi/mRieR -> ie/kstRa/ReRn
    partenaire: paR/t@a/mRieR -> pRaRn
    gouverneur: ks@e/vieR/mR@R -> ks@e/vRieRn
    ordinaire: eR/pvi/mRieR -> eR/pvRin
    partenaires: paR/t@a/mRieR/-s -> pRaRn/-s
    fonctionnaire: kpaik/sRwae/mRieR -> kpRaikn
    ordinaires: eR/pvi/mRieR/-s -> eR/pvRin/-s
    révolutionnaire: Re/vae/mt@i/sRwae/mRieR -> Re/vae/mtR@in
    ordinaire: eR/pvi/mRieR -> eR/pvRin
    imaginaire: i/ma/vti/mRieR -> i/mRan

## S059 (suffix) -- ·[lo|pai|phra|po|ppo|pui|ri|voi|xplo]ser

- dedicated keys [2, 3, 4, 5, 6, 7, 9, 12, 14] = `kspvmtwae` for ·[lo|pai|phra|po|ppo|pui|ri|voi|xplo]ser (sim 0.317, comfort 496.0)
- strokeFreqSaved 300.5, freqBenefiting 300.5 of 300.5 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 17, 18]] sim 0.333 saved 300.5; dedicated [[2, 3, 4, 5, 6, 7, 9, 12, 14]] sim 0.317 saved 300.5; dedicated [[2, 3, 4, 6, 7, 9, 12, 14]] sim 0.283 saved 300.5; dedicated [[2, 3, 4, 6, 7, 8, 12, 13, 14]] sim 0.283 saved 300.5; dedicated [[16, 17, 19]] sim 0.267 saved 300.5

    reposer: R@a/pae/twe/-l -> R@a/kspvmtwae/-l
    exploser: ie/kspmtae/twe/-l -> ie/kspvmtwae/-l
    proposé: pRae/pae/twe -> pRae/kspvmtwae
    déposer: pve/pae/twe/-l -> pve/kspvmtwae/-l
    proposer: pRae/pae/twe/-l -> pRae/kspvmtwae/-l
    supposé: s@i/pae/twe -> s@i/kspvmtwae
    épuisé: e/p@ai/twe -> e/kspvmtwae
    explosé: ie/kspmtae/twe -> ie/kspvmtwae
    autorisé: ae/tae/Ri/twe -> ae/tae/kspvmtwae
    déposé: pve/pae/twe -> pve/kspvmtwae

## P091+P092 (prefix) -- la, cal, mal, al, loa·

- merged keys [6, 7, 18] = `mt-k` for la, cal, mal, al, loa· (sim 0.658, comfort 592.5)
- strokeFreqSaved 299.3, freqBenefiting 299.3 of 444.5 (share by freq 0.673, by count 0.485), boundary risks 11
- fallbacks: {'keyOverlap': 221, 'markCostTooHigh': 7}
- alternatives: merged [[6, 7, 12]] sim 0.726 saved 249.4; merged [[6, 7, 18]] sim 0.658 saved 299.3; merged [[2, 12, 23]] sim 0.509 saved 210.2; merged [[2, 6, 7]] sim 0.718 saved 116.7

    laquelle: mta/kiel -> kmtiekl
    malgré: mal/ksRe -> ksmtRek
    alcool: al/kel -> kmtekl
    laver: mta/ve/-l -> vmtek/-l
    lapin: mta/paie -> pmtaiek
    lapins: mta/paie/-s -> pmtaiek/-s
    lavé: mta/ve -> vmtek
    calcul: kal/k@il -> kmt@ikl
    calculs: kal/k@il/-s -> kmt@ikl/-s
    calculé: kal/k@i/mte -> kmt@ik/mte

## S085 (suffix) -- mi, mis, mie, ·emie

- merged keys [13, 25] = `im` for mi, mis, mie, ·emie (sim 0.801, comfort 492.4)
- strokeFreqSaved 295.7, freqBenefiting 284.9 of 336.2 (share by freq 0.847, by count 0.703), boundary risks 12
- fallbacks: {'keyOverlap': 49}
- alternatives: merged [[13, 25]] sim 0.801 saved 295.7; merged [[25]] sim 0.641 saved 359.1; merged [[13, 24, 25]] sim 0.641 saved 295.1; merged [[13, 23, 25]] sim 0.641 saved 295.1; merged [[9, 13, 25]] sim 0.641 saved 295.7

    parmi: paR/mi -> paiRm
    ennemi: ie/mR@a/mi -> ie/mR@aim
    ennemis: ie/mR@a/mi/-s -> ie/mR@aim/-s
    promis: pRae/mi -> pRaiem
    académie: a/ka/pve/mi -> a/kaim
    économie: e/kae/mRae/mi -> e/kae/mRaiem
    endormie: @/pveR/mi/-j -> @/pvieRm/-j
    promis: pRae/mi -> pRaiem
    économies: e/kae/mRae/mi/-s -> e/kae/mRaiem/-s
    fourmis: kp@eR/mi/-s -> kp@ieRm/-s

## S099 (suffix) -- tout

- merged keys [2, 20] = `k-t` for tout (sim 0.5, comfort 426.8)
- strokeFreqSaved 291.1, freqBenefiting 291.1 of 291.3 (share by freq 0.999, by count 0.75), boundary risks 0
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[14, 20]] sim 0.5 saved 291.1; merged [[2, 20]] sim 0.5 saved 291.1; merged [[5, 20]] sim 0.5 saved 291.3; merged [[18, 20]] sim 0.5 saved 291.3; merged [[20, 22]] sim 0.5 saved 291.3

    surtout: s@iR/t@e -> ks@itR
    partout: paR/t@e -> kpatR
    surtout: s@iR/t@e -> ks@itR
    surtouts: s@iR/t@e/-s -> ks@itR/-s
    antitout: @/ti/t@e -> @/ktit
    mangetout: m@/vt@a/t@e -> m@/kvt@at

## P021 (prefix) -- ine·, ini·, ins, in@·, inis·, inEs·, insi·

- dedicated keys [5, 11, 12, 13, 14] = `v@aie` for ine·, ini·, ins, in@·, inis·, inEs·, insi· (sim 0.175, comfort 322.0)
- strokeFreqSaved 279.6, freqBenefiting 279.6 of 1013.7 (share by freq 0.276, by count 0.575), boundary risks 0
- fallbacks: {'noGain': 72, 'markCostTooHigh': 255}
- alternatives: dedicated [[5, 11, 12, 13, 14]] sim 0.175 saved 279.6; dedicated [[3, 7, 13, 14]] sim 0.174 saved 279.6; dedicated [[3, 7, 11, 14]] sim 0.118 saved 279.6; dedicated [[3, 5, 7, 14]] sim -0.113 saved 279.6; dedicated [[2, 8, 9, 12, 13, 14]] sim -0.267 saved 279.6

    imbécile: aie/sve/sil -> v@aie/sil
    imbécile: aie/sve/sil -> v@aie/sil
    incendie: aie/s@/pvi -> v@aie/pvi
    incident: aie/si/pv@ -> v@aie/pv@
    intimité: aie/ti/mi/te -> v@aie/mi/te
    indispensable: aie/pvis/p@/sajl -> v@aie/p@/sajl
    imbéciles: aie/sve/sil/-s -> v@aie/sil/-s
    instituteur: aies/ti/t@i/t@R -> v@aie/t@i/t@R
    inspiration: aies/pi/Ra/sRwai -> v@aie/Ra/sRwai
    investir: aie/vies/tiR -> v@aie/tiR

## S062 (suffix) -- ·[ca|che|cré|cé|de|gu|pli|plie|rré|ré|ssé|sé]ment

- dedicated keys [2, 3, 4, 6, 11, 12, 13] = `kspm@ai` for ·[ca|che|cré|cé|de|gu|pli|plie|rré|ré|ssé|sé]ment (sim 0.283, comfort 471.0)
- strokeFreqSaved 277.8, freqBenefiting 277.8 of 277.8 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 3, 4, 6, 11, 12, 13]] sim 0.283 saved 277.8; dedicated [[2, 3, 4, 6, 7, 11, 13]] sim 0.283 saved 277.8; dedicated [[16, 18, 19]] sim 0.267 saved 277.8; dedicated [[18, 19, 21]] sim 0.267 saved 277.8; dedicated [[18, 19, 23]] sim 0.267 saved 277.8

    franchement: kpR@/pm@a/m@ -> kpR@/kspm@ai
    médicaments: me/pvi/ka/m@/-s -> me/pvi/kspm@ai/-s
    rapidement: Ra/pi/pv@a/m@ -> Ra/pi/kspm@ai
    forcément: kpeR/se/m@ -> kpeR/kspm@ai
    commandement: kae/m@/pv@a/m@ -> kae/m@/kspm@ai
    vachement: va/pm@a/m@ -> va/kspm@ai
    médicament: me/pvi/ka/m@ -> me/pvi/kspm@ai
    carrément: ka/Re/m@ -> ka/kspm@ai
    compliments: kai/pmti/m@/-s -> kai/kspm@ai/-s
    compliment: kai/pmti/m@ -> kai/kspm@ai

## S093 (suffix) -- liste, riste, niste, lisme, tisme, lyse, tiste, nisme, lise

- merged keys [13, 17, 20] = `ist` for liste, riste, niste, lisme, tisme, lyse, tiste, nisme, lise (sim 0.505, comfort 534.1)
- strokeFreqSaved 274.0, freqBenefiting 274.0 of 326.8 (share by freq 0.838, by count 0.798), boundary risks 38
- fallbacks: {'keyOverlap': 147}
- alternatives: merged [[17, 20, 23]] sim 0.567 saved 326.2; merged [[20, 22, 23]] sim 0.526 saved 326.3; merged [[13, 17, 20]] sim 0.505 saved 274.0; merged [[17, 20, 25]] sim 0.502 saved 326.6; merged [[17, 22, 23]] sim 0.502 saved 326.2

    journaliste: vt@eR/mRa/mtist -> vt@eR/mRaist
    analyse: a/mRa/mtinl -> a/mRaist
    dentiste: pv@/tist -> pv@ist
    spécialiste: spe/sRwa/mtist -> spe/sRwaist
    journalistes: vt@eR/mRa/mtist/-s -> vt@eR/mRaist/-s
    terroristes: tie/Rae/Rist/-s -> tie/Raiest/-s
    touristes: t@e/Rist/-s -> t@iest/-s
    analyses: a/mRa/mtinl/-s -> a/mRaist/-s
    traumatisme: tRae/ma/tinlm -> tRae/maist
    terroriste: tie/Rae/Rist -> tie/Raiest

## P059 (prefix) -- oy·, coy·

- dedicated keys [2, 11, 12, 13, 14] = `k@aie` for oy·, coy· (sim 0.577, comfort 322.0)
- strokeFreqSaved 268.6, freqBenefiting 268.6 of 268.6 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 11, 12, 13, 14]] sim 0.577 saved 268.6; dedicated [[2, 3, 11, 12, 13, 14]] sim 0.366 saved 268.6; dedicated [[2, 4, 11, 12, 13, 14]] sim 0.366 saved 268.6; dedicated [[2, 6, 11, 12, 13, 14]] sim 0.366 saved 268.6; dedicated [[11, 13, 18]] sim 0.289 saved 268.6

    occuper: ae/k@i/pe/-l -> k@aie/pe/-l
    occupé: ae/k@i/pe -> k@aie/pe
    communauté: kae/m@i/mRae/te -> k@aie/mRae/te
    occupée: ae/k@i/pe/-j -> k@aie/pe/-j
    occupez: ae/k@i/pe/-k -> k@aie/pe/-k
    communiquer: kae/m@i/mRi/ke/-l -> k@aie/mRi/ke/-l
    occuperai: ae/k@i/p@a/Re/-t -> k@aie/p@a/Re/-t
    occupera: ae/k@i/p@a/Ra -> k@aie/p@a/Ra
    occupés: ae/k@i/pe/-s -> k@aie/pe/-s
    occupait: ae/k@i/pie -> k@aie/pie

## S104 (suffix) -- fier, fiant

- merged keys [14, 16, 17, 19] = `ejsd` for fier (sim 0.8, comfort 482.7)
- merged keys [11, 16, 17, 19] = `@jsd` for fiant (sim 0.8, comfort 482.7)
- strokeFreqSaved 266.6, freqBenefiting 266.6 of 268.0 (share by freq 0.995, by count 0.939), boundary risks 0
- fallbacks: {'keyOverlap': 26}
- alternatives: merged [[14, 16, 17, 19], [11, 16, 17, 19]] sim 0.8 saved 266.6; merged [[11, 14, 16, 17], [11, 14, 16, 18]] sim 0.5 saved 261.6; merged [[2, 4, 14, 16], [2, 4, 11, 16]] sim 0.6 saved 198.4

    vérifier: ve/Ri/kpRwe/-l -> ve/Riejsd/-l
    vérifié: ve/Ri/kpRwe -> ve/Riejsd
    identifier: i/pv@/ti/kpRwe/-l -> i/pv@/tiejsd/-l
    vérifiez: ve/Ri/kpRwe/-k -> ve/Riejsd/-k
    confier: kai/kpRwe/-l -> kaiejsd/-l
    identifié: i/pv@/ti/kpRwe -> i/pv@/tiejsd
    confié: kai/kpRwe -> kaiejsd
    sacrifier: sa/kRi/kpRwe/-l -> sa/kRiejsd/-l
    justifier: vt@is/ti/kpRwe/-l -> vt@is/tiejsd/-l
    sacrifié: sa/kRi/kpRwe -> sa/kRiejsd

## P078 (prefix) -- ba, bâ, bas

- merged keys [3, 5, 9] = `svw-` for ba, bâ, bas (sim 0.525, comfort 469.8)
- strokeFreqSaved 261.4, freqBenefiting 261.4 of 341.9 (share by freq 0.764, by count 0.694), boundary risks 6
- fallbacks: {'keyOverlap': 137, 'markCostTooHigh': 5}
- alternatives: merged [[3, 5]] sim 0.683 saved 290.7; merged [[3, 5, 9]] sim 0.525 saved 261.4; merged [[3, 5, 8]] sim 0.525 saved 250.9; merged [[2, 3, 5]] sim 0.525 saved 263.2; merged [[3, 5, 17]] sim 0.525 saved 269.0

    bataille: sva/taj -> svtwaj
    baron: sva/Rai -> svRwai
    bâton: sva/tai -> svtwai
    basket: svas/kiet -> ksvwiet
    balancé: sva/mt@/se -> svmtw@/se
    balancer: sva/mt@/se/-l -> svmtw@/se/-l
    bâtard: sva/taR -> svtwaR
    balance: sva/mt@s -> svmtw@s
    balai: sva/mtie -> svmtwie
    balance: sva/mt@s -> svmtw@s

## S103 (suffix) -- tif, ·atif, ·itif

- merged keys [17, 19, 20] = `-sdt` for tif, ·atif, ·itif (sim 0.759, comfort 568.4)
- strokeFreqSaved 259.2, freqBenefiting 203.0 of 210.5 (share by freq 0.964, by count 0.94), boundary risks 8
- fallbacks: {'keyOverlap': 37}
- alternatives: merged [[17, 19, 20]] sim 0.759 saved 259.2; merged [[7, 17, 19]] sim 0.569 saved 175.9; merged [[2, 4, 20]] sim 0.569 saved 107.9; merged [[12, 13, 20]] sim 0.5 saved 53.2

    objectif: ej/vtiek/tisd -> ej/vtieskdt
    positif: pae/twi/tisd -> pae/twisdt
    négatif: mRe/ksa/tisd -> mRe/ksasdt
    négatif: mRe/ksa/tisd -> mRe/ksasdt
    affirmatif: a/kpiR/ma/tisd -> a/kpisdtR
    dispositif: pvis/pae/twi/tisd -> pvis/paesdt
    sportif: speR/tisd -> spesdtR
    définitif: pve/kpi/mRi/tisd -> pve/kpisdt
    attentif: a/t@/tisd -> a/t@sdt
    objectifs: ej/vtiek/tisd/-s -> ej/vtieskdt/-s

## P044 (prefix) -- ia·, ena·, éa·, ea·

- dedicated keys [2, 3, 6, 12] = `ksma` for ia·, ena·, éa·, ea· (sim -0.5, comfort 373.0)
- strokeFreqSaved 258.1, freqBenefiting 258.1 of 400.9 (share by freq 0.644, by count 0.581), boundary risks 0
- fallbacks: {'markCostTooHigh': 340}
- alternatives: dedicated [[11, 12]] sim 0.312 saved 258.1; dedicated [[2, 3, 11, 12]] sim -0.188 saved 258.1; dedicated [[2, 3, 6, 12]] sim -0.5 saved 258.1; dedicated [[2, 3, 7, 12]] sim -0.5 saved 258.1; dedicated [[2, 3, 7, 8, 12, 13, 14]] sim -0.562 saved 258.1

    imagine: i/ma/vtin -> ksma/vtin
    extraordinaire: ie/kstRa/eR/pvi/mRieR -> ksma/eR/pvi/mRieR
    imaginé: i/ma/vti/mRe -> ksma/vti/mRe
    italien: i/ta/mtRwaie -> ksma/mtRwaie
    italien: i/ta/mtRwaie -> ksma/mtRwaie
    italiens: i/ta/mtRwaie/-s -> ksma/mtRwaie/-s
    empoisonné: @/pwa/twae/mRe -> ksma/twae/mRe
    italienne: i/ta/mtRwien -> ksma/mtRwien
    égalité: e/ksa/mti/te -> ksma/mti/te
    extraterrestres: ie/kstRa/tie/RiestR/-s -> ksma/tie/RiestR/-s

## S109 (suffix) -- fois, nois

- merged keys [9, 17, 19] = `w-sd` for fois, nois (sim 0.53, comfort 536.1)
- strokeFreqSaved 238.5, freqBenefiting 238.5 of 238.5 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[16, 17, 19]] sim 0.73 saved 238.5; merged [[9, 17, 19]] sim 0.53 saved 238.5; merged [[12, 16]] sim 0.5 saved 41.5; merged [[12, 16, 22]] sim 0.57 saved 41.5; merged [[2, 4, 16]] sim 0.565 saved 35.2

    parfois: paR/kpwa -> pwasdR
    autrefois: ae/tR@a/kpwa -> ae/tRw@asd
    chinois: pmi/mRwa -> pmwisd
    chinois: pmi/mRwa -> pmwisd
    quelquefois: kiel/k@a/kpwa -> kiel/kw@asd
    toutefois: t@e/t@a/kpwa -> t@e/tw@asd
    sournois: s@eR/mRwa -> sw@esdR
    pékinois: pe/ki/mRwa -> pe/kwisd
    sournois: s@eR/mRwa -> sw@esdR
    berlinois: svieR/mti/mRwa -> svieR/mtwisd

## P086 (prefix) -- le, lé, lan

- merged keys [6, 7, 11] = `mt@` for le, lé, lan (sim 0.681, comfort 511.9)
- strokeFreqSaved 237.6, freqBenefiting 237.6 of 293.2 (share by freq 0.81, by count 0.474), boundary risks 0
- fallbacks: {'keyOverlap': 82}
- alternatives: merged [[6, 7, 11]] sim 0.681 saved 237.6; merged [[6, 7]] sim 0.667 saved 242.4; merged [[4, 6, 7]] sim 0.5 saved 238.9; merged [[6, 7, 9]] sim 0.5 saved 242.0; merged [[6, 7, 8]] sim 0.5 saved 238.9

    lequel: mt@a/kiel -> kmt@iel
    lever: mt@a/ve/-l -> vmt@e/-l
    leçon: mt@a/sai -> smt@ai
    levez: mt@a/ve/-k -> vmt@e/-k
    langage: mt@/ksaZ -> ksmt@aZ
    levé: mt@a/v*e -> vmt*@e
    leçons: mt@a/sai/-s -> smt@ai/-s
    légal: mte/ksal -> ksmt@al
    levée: mt@a/ve/-j -> vmt@e/-j
    lever: mt@a/ve -> vmt@e

## S111 (suffix) -- cien, ·icien, tien, lien, rien, ien

- merged keys [16, 17, 20] = `-jst` for cien, ·icien, tien, lien, rien, ien (sim 0.653, comfort 514.7)
- strokeFreqSaved 231.6, freqBenefiting 201.3 of 202.0 (share by freq 0.997, by count 0.978), boundary risks 0
- fallbacks: {'keyOverlap': 7}
- alternatives: merged [[16, 17, 20]] sim 0.653 saved 231.6; merged [[16, 17, 23]] sim 0.648 saved 231.6; merged [[16, 17, 21]] sim 0.599 saved 231.6; merged [[8, 16, 17]] sim 0.584 saved 190.7; merged [[16, 17]] sim 0.569 saved 231.6

    soutien: s@e/tRwaie -> s@ejst
    entretien: @/tR@a/tRwaie -> @/tR@ajst
    italien: i/ta/mtRwaie -> i/tajst
    magicien: ma/vti/sRwaie -> ma/vtijst
    italien: i/ta/mtRwaie -> i/tajst
    italiens: i/ta/mtRwaie/-s -> i/tajst/-s
    musiciens: m@i/twi/sRwaie/-s -> m@i/twijst/-s
    vaurien: vae/Rwaie -> vaejst
    chrétiens: kRe/tRwaie/-s -> kRejst/-s
    mécanicien: me/ka/mRi/sRwaie -> me/kajst

## S105 (suffix) -- ·icain, cain, quin

- merged keys [13, 18] = `ik` for ·icain, cain, quin (sim 0.639, comfort 362.5)
- strokeFreqSaved 228.8, freqBenefiting 143.6 of 174.2 (share by freq 0.824, by count 0.678), boundary risks 8
- fallbacks: {'keyOverlap': 37}
- alternatives: merged [[13, 18]] sim 0.639 saved 228.8; merged [[12, 13, 18]] sim 0.5 saved 208.6; merged [[13, 18, 19]] sim 0.5 saved 228.8; merged [[7, 13, 18]] sim 0.5 saved 224.3

    américain: a/me/Ri/kaie -> a/miek
    américains: a/me/Ri/kaie/-s -> a/miek/-s
    américaine: a/me/Ri/kien -> a/miek/kien
    américain: a/me/Ri/kaie -> a/miek
    américains: a/me/Ri/kaie/-s -> a/miek/-s
    mannequin: ma/mR@a/kaie -> ma/mR@aik
    bouquin: sv@e/kaie -> sv@iek
    bouquins: sv@e/kaie/-s -> sv@iek/-s
    américaine: a/me/Ri/kien -> a/miek/kien
    mannequins: ma/mR@a/kaie/-s -> ma/mR@aik/-s

## S112 (suffix) -- tin, tain

- merged keys [18, 20] = `-kt` for tin, tain (sim 0.5, comfort 494.6)
- strokeFreqSaved 226.9, freqBenefiting 226.9 of 226.9 (share by freq 1.0, by count 0.973), boundary risks 4
- fallbacks: {'keyOverlap': 4}
- alternatives: merged [[12, 20]] sim 0.5 saved 200.7; merged [[11, 20]] sim 0.5 saved 208.4; merged [[20, 22]] sim 0.5 saved 226.9; merged [[18, 20]] sim 0.5 saved 226.9

    certain: sieR/taie -> siektR
    destin: pves/taie -> pveskt
    crétin: kRe/taie -> kRekt
    crétin: kRe/taie -> kRekt
    crétins: kRe/taie/-s -> kRekt/-s
    lointain: mtwaie/taie -> mtwaiekt
    bulletin: sv@i/mt@a/taie -> sv@i/mt@akt
    festin: kpies/taie -> kpieskt
    baratin: sva/Ra/taie -> sva/Rakt
    pantin: p@/taie -> p@kt

## S070 (suffix) -- ·[bre|go|le|lle|me|ne|nne|o|pe]ries

- dedicated keys [16, 18, 19] = `-jkd` for ·[bre|go|le|lle|me|ne|nne|o|pe]ries (sim 0.261, comfort 234.0)
- strokeFreqSaved 224.1, freqBenefiting 224.1 of 224.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 18, 19]] sim 0.261 saved 224.1; dedicated [[16, 18, 21]] sim 0.261 saved 224.1; dedicated [[16, 18, 22]] sim 0.261 saved 224.1; dedicated [[16, 18, 23]] sim 0.261 saved 224.1; dedicated [[16, 18, 25]] sim 0.261 saved 224.1

    conneries: ke/mR@a/Ri/-s -> ke/-jkd/-s
    théorie: te/ae/Ri -> te/-jkd
    connerie: ke/mR@a/Ri -> ke/-jkd
    saloperie: sa/mte/p@a/Ri -> sa/mte/-jkd
    galerie: ksa/mt@a/Ri -> ksa/-jkd
    infirmerie: aie/kpiR/m@a/Ri -> aie/kpiR/-jkd
    cavalerie: ka/va/mt@a/Ri -> ka/va/-jkd
    sonnerie: se/mR@a/Ri -> se/-jkd
    saloperies: sa/mte/p@a/Ri/-s -> sa/mte/-jkd/-s
    catégorie: ka/te/ksae/Ri -> ka/te/-jkd

## S102 (suffix) -- mal, ma

- merged keys [13, 23, 25] = `ilm` for mal, ma (sim 0.655, comfort 542.7)
- strokeFreqSaved 223.3, freqBenefiting 223.3 of 273.2 (share by freq 0.817, by count 0.547), boundary risks 0
- fallbacks: {'keyOverlap': 39}
- alternatives: merged [[12, 23, 25]] sim 0.885 saved 252.5; merged [[23, 25]] sim 0.77 saved 273.2; merged [[13, 23, 25]] sim 0.655 saved 223.3; merged [[4, 23, 25]] sim 0.655 saved 265.4; merged [[11, 23, 25]] sim 0.655 saved 272.9

    normal: mReR/mal -> mRieRlm
    cinéma: si/mRe/ma -> si/mRielm
    normale: mReR/mal/-j -> mRieRlm/-j
    karma: kaR/ma -> kaiRlm
    normal: mReR/mal -> mRieRlm
    anormal: a/mReR/mal -> a/mRieRlm
    trauma: tRae/ma -> tRaielm
    normales: mReR/mal/-js -> mRieRlm/-js
    schéma: pme/ma -> pmielm
    plasma: pmtas/ma -> pmtaislm

## S113 (suffix) -- cin, ssin

- merged keys [7, 17] = `t-s` for cin, ssin (sim 0.5, comfort 437.2)
- strokeFreqSaved 221.0, freqBenefiting 221.0 of 222.3 (share by freq 0.994, by count 0.892), boundary risks 0
- fallbacks: {'keyOverlap': 4}
- alternatives: merged [[11, 17]] sim 0.5 saved 209.5; merged [[16, 17]] sim 0.5 saved 222.3; merged [[7, 17]] sim 0.5 saved 221.0; merged [[8, 17]] sim 0.5 saved 222.3

    médecin: mied/saie -> mtiesd
    assassin: a/sa/saie -> a/stas
    médecins: mied/saie/-s -> mtiesd/-s
    assassins: a/sa/saie/-s -> a/stas/-s
    poussin: p@e/saie -> pt@es
    vaccin: vak/saie -> vtask
    assassin: a/sa/saie -> a/stas
    coussin: k@e/saie -> kt@es
    coussins: k@e/saie/-s -> kt@es/-s
    poussins: p@e/saie/-s -> pt@es/-s

## P065 (prefix) -- die·, lie·, ie·

- dedicated keys [4, 5, 6, 7, 13, 14] = `pvmtie` for die·, lie·, ie· (sim 0.727, comfort 379.0)
- strokeFreqSaved 218.9, freqBenefiting 218.9 of 218.9 (share by freq 1.0, by count 0.993), boundary risks 0
- fallbacks: {'markCostTooHigh': 1}
- alternatives: dedicated [[4, 5, 6, 7, 13, 14]] sim 0.727 saved 218.9; dedicated [[4, 5, 6, 7, 13]] sim 0.591 saved 218.9; dedicated [[4, 5, 6, 7, 14]] sim 0.591 saved 218.9; dedicated [[2, 4, 5, 13, 14]] sim 0.477 saved 218.9; dedicated [[4, 5, 7, 13, 14]] sim 0.477 saved 218.9

    différent: pvi/kpe/R@ -> pvmtie/R@
    différente: pvi/kpe/R@t -> pvmtie/R@t
    différentes: pvi/kpe/R@t/-s -> pvmtie/R@t/-s
    différents: pvi/kpe/R@/-s -> pvmtie/R@/-s
    illégal: i/mte/ksal -> pvmtie/ksal
    littérature: mti/te/Ra/t@iR -> pvmtie/Ra/t@iR
    libération: mti/sve/Ra/sRwai -> pvmtie/Ra/sRwai
    libérez: mti/sve/Re/-k -> pvmtie/Re/-k
    idéale: i/pve/al/-j -> pvmtie/al/-j
    littéralement: mti/te/Ra/mt@a/m@ -> pvmtie/Ra/mt@a/m@

## S114 (suffix) -- mir, mar

- merged keys [8, 13, 25] = `Rim` for mir, mar (sim 0.682, comfort 640.7)
- strokeFreqSaved 215.6, freqBenefiting 215.6 of 217.0 (share by freq 0.994, by count 0.76), boundary risks 0
- fallbacks: {'keyOverlap': 6}
- alternatives: merged [[8, 13, 25]] sim 0.682 saved 215.6; merged [[8, 12, 25]] sim 0.618 saved 176.5; merged [[8, 25]] sim 0.6 saved 215.6; merged [[12, 13, 25]] sim 0.5 saved 177.8; merged [[8, 23, 25]] sim 0.5 saved 214.5

    dormir: pveR/miR -> pvRieRm
    cauchemar: kae/pm@a/maR -> kae/pmR@aim
    endormir: @/pveR/miR -> @/pvRieRm
    cauchemars: kae/pm@a/maR/-s -> kae/pmR@aim/-s
    calmar: kal/maR -> kRailm
    calamars: ka/mta/maR/-s -> ka/mtRaim/-s
    calmars: kal/maR/-s -> kRailm/-s
    calamar: ka/mta/maR -> ka/mtRaim
    dormirent: pveR/miR/-t -> pvRieRm/-t
    blêmir: svmte/miR -> svmtRiem

## S115 (suffix) -- du, ·@du

- merged keys [19] = `-d` for du, ·@du (sim 0.625, comfort 339.8)
- strokeFreqSaved 215.5, freqBenefiting 191.5 of 191.5 (share by freq 1.0, by count 0.986), boundary risks 8
- fallbacks: {'markCostTooHigh': 2}
- alternatives: merged [[19]] sim 0.625 saved 215.5; merged [[11, 16, 19]] sim 0.5 saved 86.8; merged [[11, 18, 19]] sim 0.5 saved 86.8; merged [[11, 19]] sim 0.656 saved 86.8; merged [[11, 19, 20]] sim 0.5 saved 86.8

    entendu: @/t@/pv@i -> @/t@d
    perdu: pieR/pv@i -> piedR
    malentendu: ma/mt@/t@/pv@i -> ma/mt@d
    perdue: pieR/pv@i/-j -> piedR/-j
    individu: aie/pvi/vi/pv@i -> aie/pvi/vid
    boudu: sv@e/pv@i -> sv@ed
    individus: aie/pvi/vi/pv@i/-s -> aie/pvi/vid/-s
    perdus: pieR/pv@i/-s -> piedR/-s
    tendu: t@/pv@i -> t@d
    tordu: teR/pv@i -> tedR

## S106 (suffix) -- cial, tiel, ciel, ·@tiel, tial, tial

- merged keys [12, 16, 23] = `ajl` for cial, tiel, ciel, ·@tiel, tial, tial (sim 0.592, comfort 571.6)
- strokeFreqSaved 210.3, freqBenefiting 191.4 of 224.7 (share by freq 0.852, by count 0.699), boundary risks 0
- fallbacks: {'keyOverlap': 59}
- alternatives: merged [[16, 17, 23]] sim 0.837 saved 237.4; merged [[12, 16, 23]] sim 0.592 saved 210.3; merged [[12, 16, 17]] sim 0.59 saved 208.2; merged [[12, 17, 23]] sim 0.59 saved 213.2; merged [[11, 16, 23]] sim 0.57 saved 201.8

    spécial: spe/sRwal -> spaejl
    spéciale: spe/sRwal/-j -> spaejl/-j
    essentiel: e/s@/sRwiel -> e/s@ajl
    officiel: ae/kpi/sRwiel -> ae/kpaijl
    commercial: kae/mieR/sRwal -> kae/maiejRl
    officielle: ae/kpi/sRwiel/-j -> ae/kpaijl/-j
    spéciales: spe/sRwal/-js -> spaejl/-js
    potentiel: pae/t@/sRwiel -> pae/t@ajl
    confidentiel: kai/kpi/pv@/sRwiel -> kai/kpaijl
    essentiel: e/s@/sRwiel -> e/s@ajl

## S116 (suffix) -- ro, reau

- merged keys [21] = `-R` for ro, reau (sim 0.667, comfort 303.5)
- strokeFreqSaved 210.0, freqBenefiting 210.0 of 214.1 (share by freq 0.981, by count 0.973), boundary risks 38
- fallbacks: {'markCostTooHigh': 2}
- alternatives: merged [[21]] sim 0.667 saved 210.0; merged [[13, 21]] sim 0.5 saved 209.7; merged [[7, 21]] sim 0.5 saved 190.3; merged [[20, 21]] sim 0.5 saved 214.1; merged [[12, 21]] sim 0.5 saved 190.1

    numéro: mR@i/me/Rae -> mR@i/meR
    numéros: mR@i/me/Rae/-s -> mR@i/meR/-s
    taureau: tae/Rae -> taeR
    maquereau: ma/k@a/Rae -> ma/k@aR
    hétéro: e/te/Rae -> e/teR
    taureaux: tae/Rae/-s -> taeR/-s
    amaro: a/ma/Rae -> a/maR
    hétéros: e/te/Rae/-s -> e/teR/-s
    hétéro: e/te/Rae -> e/teR
    maquereaux: ma/k@a/Rae/-s -> ma/k@aR/-s

## P068 (prefix) -- ré[a|com|con|pé|ser|vol]·

- dedicated keys [5, 7, 9, 13, 14, 21, 23] = `vtwieRl` for ré[a|com|con|pé|ser|vol]· (sim 0.326, comfort 521.0)
- strokeFreqSaved 208.2, freqBenefiting 208.2 of 208.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[5, 7, 9, 13, 14, 21, 23]] sim 0.326 saved 208.2; dedicated [[2, 5, 12, 13, 14, 23]] sim 0.326 saved 208.2; dedicated [[2, 7, 9, 12, 13, 14, 21]] sim 0.326 saved 208.2; dedicated [[4, 7, 9, 13, 14, 21]] sim 0.283 saved 208.2; dedicated [[2, 4, 5]] sim 0.261 saved 208.2

    répéter: Re/pe/te/-l -> vtwieRl/te/-l
    réalisé: Re/a/mti/twe -> vtwieRl/mti/twe
    récompense: Re/kai/p@s -> vtwieRl/p@s
    réservé: Re/twieR/ve -> vtwieRl/ve
    répétition: Re/pe/ti/sRwai -> vtwieRl/ti/sRwai
    réalise: Re/a/mtinl -> vtwieRl/mtinl
    réagir: Re/a/vtiR -> vtwieRl/vtiR
    répétez: Re/pe/te/-k -> vtwieRl/te/-k
    réagi: Re/a/vti -> vtwieRl/vti
    répété: Re/pe/te -> vtwieRl/te

## S110 (suffix) -- lette, rette, quette, nnette, ette

- merged keys [8, 20, 23] = `R-tl` for lette, rette, quette, nnette, ette (sim 0.653, comfort 623.5)
- strokeFreqSaved 206.4, freqBenefiting 206.4 of 236.9 (share by freq 0.871, by count 0.857), boundary risks 0
- fallbacks: {'keyOverlap': 26}
- alternatives: merged [[20, 21, 23]] sim 0.714 saved 236.0; merged [[8, 20, 23]] sim 0.653 saved 206.4; merged [[18, 20, 23]] sim 0.642 saved 236.6; merged [[20, 22, 23]] sim 0.626 saved 236.6; merged [[20, 23]] sim 0.592 saved 236.6

    toilettes: twa/mtiet/-s -> tRwatl/-s
    cigarette: si/ksa/Riet -> si/ksRatl
    cigarettes: si/ksa/Riet/-s -> si/ksRatl/-s
    toilette: twa/mtiet -> tRwatl
    casquette: kas/kiet -> kRastl
    omelette: ae/m@a/mtiet -> ae/mR@atl
    étiquette: e/ti/kiet -> e/tRitl
    squelette: ks@a/mtiet -> ksR@atl
    boulettes: sv@e/mtiet/-s -> svR@etl/-s
    poulette: p@e/mtiet -> pR@etl

## P069 (prefix) -- io·, imo·, kio·

- dedicated keys [2, 6, 12, 13, 14] = `kmaie` for io·, imo·, kio· (sim 0.334, comfort 432.0)
- strokeFreqSaved 205.8, freqBenefiting 205.8 of 205.9 (share by freq 0.999, by count 0.984), boundary risks 0
- fallbacks: {'markCostTooHigh': 4}
- alternatives: dedicated [[2, 6, 12, 13, 14]] sim 0.334 saved 205.8; dedicated [[12, 14, 18]] sim 0.278 saved 205.8; dedicated [[2, 6, 8, 12, 13, 14]] sim 0.112 saved 205.8; dedicated [[9, 12, 14]] sim 0.0 saved 205.8; dedicated [[4, 9, 12, 14]] sim -0.222 saved 205.8

    ignorais: i/wae/Rie/-k -> kmaie/Rie/-k
    innocent: i/mRae/s@ -> kmaie/s@
    kilomètres: ki/mtae/mietR/-s -> kmaie/mietR/-s
    innocents: i/mRae/s@/-s -> kmaie/s@/-s
    ignorez: i/wae/Re/-k -> kmaie/Re/-k
    innocent: i/mRae/s@ -> kmaie/s@
    innocente: i/mRae/s@t -> kmaie/s@t
    hypothèse: i/pae/tienl -> kmaie/tienl
    immobile: i/mae/svil -> kmaie/svil
    ignorance: i/wae/R@s -> kmaie/R@s

## S075 (suffix) -- ·[bi|cep|lec|llec|sa|ssa|tra|tu|tui|va]tion

- dedicated keys [3, 7, 8, 12, 13, 14, 16, 18] = `stRaiejk` for ·[bi|cep|lec|llec|sa|ssa|tra|tu|tui|va]tion (sim 0.433, comfort 679.0)
- strokeFreqSaved 205.7, freqBenefiting 205.7 of 205.7 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[3, 7, 8, 12, 13, 14, 16, 18]] sim 0.433 saved 205.7; dedicated [[16, 17, 18]] sim 0.4 saved 205.7; dedicated [[3, 5, 12, 13, 14, 16, 18]] sim 0.4 saved 205.7; dedicated [[3, 6, 7, 13, 14, 16, 18]] sim 0.4 saved 205.7; dedicated [[3, 7, 11, 13, 14, 16, 18]] sim 0.383 saved 205.7

    réception: Re/siejk/sRwai -> Re/stRaiejk
    collection: ke/mtiek/sRwai -> ke/stRaiejk
    administration: ad/mi/mRis/tRa/sRwai -> ad/mi/mRis/stRaiejk
    sensation: s@/sa/sRwai -> s@/stRaiejk
    élections: e/mtiek/sRwai/-s -> e/stRaiejk/-s
    intuition: aie/t@ai/sRwai -> aie/stRaiejk
    concentration: kai/s@/tRa/sRwai -> kai/s@/stRaiejk
    ambition: @/svi/sRwai -> @/stRaiejk
    démonstration: pve/mais/tRa/sRwai -> pve/mais/stRaiejk
    observation: aejk/sieR/va/sRwai -> aejk/sieR/stRaiejk

## S077 (suffix) -- ·[cri|di|li|ni|nni|ri|rri|ta|thi|ti]fier

- dedicated keys [2, 4, 6, 7, 8, 9, 13, 14] = `kpmtRwie` for ·[cri|di|li|ni|nni|ri|rri|ta|thi|ti]fier (sim 0.32, comfort 453.0)
- strokeFreqSaved 199.1, freqBenefiting 199.1 of 199.1 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 4, 6, 7, 8, 9, 13, 14]] sim 0.32 saved 199.1; dedicated [[16, 18, 20]] sim 0.24 saved 199.1; dedicated [[16, 17, 19]] sim 0.24 saved 199.1; dedicated [[16, 18, 19]] sim 0.24 saved 199.1; dedicated [[16, 18, 21]] sim 0.24 saved 199.1

    vérifier: ve/Ri/kpRwe/-l -> ve/kpmtRwie/-l
    vérifié: ve/Ri/kpRwe -> ve/kpmtRwie
    identifier: i/pv@/ti/kpRwe/-l -> i/pv@/kpmtRwie/-l
    vérifiez: ve/Ri/kpRwe/-k -> ve/kpmtRwie/-k
    identifié: i/pv@/ti/kpRwe -> i/pv@/kpmtRwie
    sacrifier: sa/kRi/kpRwe/-l -> sa/kpmtRwie/-l
    justifier: vt@is/ti/kpRwe/-l -> vt@is/kpmtRwie/-l
    sacrifié: sa/kRi/kpRwe -> sa/kpmtRwie
    planifié: pmta/mRi/kpRwe -> pmta/kpmtRwie
    modifier: mae/pvi/kpRwe/-l -> mae/kpmtRwie/-l

## P097 (prefix) -- voy

- merged keys [5, 8, 9] = `vRw-` for voy (sim 0.857, comfort 450.5)
- strokeFreqSaved 197.6, freqBenefiting 197.6 of 197.6 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[5, 8, 9]] sim 0.857 saved 197.6; merged [[5, 9, 16]] sim 0.714 saved 197.6; merged [[5, 9]] sim 0.571 saved 197.6; merged [[9, 16, 17]] sim 0.571 saved 197.6; merged [[8, 9, 25]] sim 0.5 saved 197.6

    voyage: vwaj/aZ -> vRwaZ
    voyais: vwaj/ie/-k -> vRwie/-k
    voyant: vwaj/@ -> vRw@
    voyages: vwaj/aZ/-s -> vRwaZ/-s
    voyage: vwaj/aZ -> vRwaZ
    voyagé: vwaj/a/vte -> vRwa/vte
    voyant: vwaj/@ -> vRw@
    voyant: vwaj/@ -> vRw@
    voyagent: vwaj/aZ/-st -> vRwaZ/-st
    voyante: vwaj/@t -> vRw@t

## P047 (prefix) -- cai·, sai·, pai·, pai·, cani·

- merged keys [2, 3, 13] = `ksi` for cai·, sai·, pai·, pai·, cani· (sim 0.529, comfort 487.2)
- strokeFreqSaved 196.5, freqBenefiting 103.6 of 392.3 (share by freq 0.264, by count 0.325), boundary risks 0
- fallbacks: {'keyOverlap': 223, 'markCostTooHigh': 12}
- alternatives: merged [[2, 4, 12]] sim 0.532 saved 443.8; merged [[2, 3, 12]] sim 0.506 saved 437.3; merged [[2, 3, 4]] sim 0.5 saved 545.2; merged [[2, 3, 13]] sim 0.529 saved 196.5; merged [[2, 4, 13]] sim 0.555 saved 172.1

    capitale: ka/pi/tal -> kstail
    paysans: pe/i/tw@/-s -> kstw@i/-s
    paysage: pe/i/twaZ -> kstwaiZ
    candidat: k@/pvi/pva -> kspvai
    qualités: ka/mti/te/-s -> kstie/-s
    candidats: k@/pvi/pva/-s -> kspvai/-s
    capital: ka/pi/t*al -> kst*ail
    capital: ka/pi/t*al -> kst*ail
    capitale: ka/pi/tal/-j -> kstail/-j
    caniveau: ka/mRi/vae -> ksvaie

## S078 (suffix) -- ·[le|sio|so|ssio|tio]nnel

- dedicated keys [3, 22, 23] = `s-nl` for ·[le|sio|so|ssio|tio]nnel (sim 0.35, comfort 254.0)
- strokeFreqSaved 195.3, freqBenefiting 195.3 of 195.3 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 22, 23]] sim 0.4 saved 195.3; dedicated [[17, 22, 23]] sim 0.4 saved 195.3; dedicated [[3, 22, 23]] sim 0.35 saved 195.3; dedicated [[6, 7, 8, 9, 12, 13, 14, 23]] sim 0.35 saved 195.3; dedicated [[3, 6, 8, 9, 12, 13, 14, 23]] sim 0.35 saved 195.3

    personnel: pieR/sae/mRiel -> pieR/s-nl
    personnel: pieR/sae/mRiel -> pieR/s-nl
    personnelle: pieR/sae/mRiel/-j -> pieR/s-nl/-j
    professionnel: pRae/kpie/sRwae/mRiel -> pRae/kpie/s-nl
    exceptionnel: ie/ksiejk/sRwae/mRiel -> ie/ksiejk/s-nl
    personnels: pieR/sae/mRiel/-s -> pieR/s-nl/-s
    personnelles: pieR/sae/mRiel/-js -> pieR/s-nl/-js
    professionnelle: pRae/kpie/sRwae/mRiel/-j -> pRae/kpie/s-nl/-j
    professionnel: pRae/kpie/sRwae/mRiel -> pRae/kpie/s-nl
    conditionnelle: kai/pvi/sRwae/mRiel/-j -> kai/pvi/s-nl/-j

## S120 (suffix) -- cat, ·icat, ka

- merged keys [18] = `-k` for cat, ·icat, ka (sim 0.614, comfort 353.3)
- strokeFreqSaved 195.0, freqBenefiting 166.4 of 167.0 (share by freq 0.997, by count 0.9), boundary risks 18
- fallbacks: {'markCostTooHigh': 4, 'keyOverlap': 2}
- alternatives: merged [[18]] sim 0.614 saved 195.0; merged [[9, 13, 18]] sim 0.5 saved 129.9; merged [[13, 16, 18]] sim 0.5 saved 129.9; merged [[13, 18]] sim 0.653 saved 129.9; merged [[13, 18, 20]] sim 0.5 saved 129.9

    avocat: a/vae/ka -> a/vaek
    vodka: ved/ka -> vekd
    avocats: a/vae/ka/-s -> a/vaek/-s
    certificat: sieR/ti/kpi/ka -> sieR/tik
    syndicat: saie/pvi/ka -> saiek
    délicat: pve/mti/ka -> pve/mtik
    syndicats: saie/pvi/ka/-s -> saiek/-s
    polka: pel/ka -> pekl
    harmonica: aR/mae/mRi/ka -> aR/maek
    délicats: pve/mti/ka/-s -> pve/mtik/-s

## P089 (prefix) -- tou, tour

- merged keys [7, 8, 9] = `tRw-` for tou, tour (sim 0.555, comfort 404.4)
- strokeFreqSaved 191.1, freqBenefiting 191.1 of 239.1 (share by freq 0.799, by count 0.436), boundary risks 1
- fallbacks: {'keyOverlap': 57}
- alternatives: merged [[7, 8]] sim 0.703 saved 191.1; merged [[7, 8, 9]] sim 0.555 saved 191.1; merged [[2, 7, 8]] sim 0.555 saved 191.1

    touché: t@e/pm*e -> pmtRw*e
    toucher: t@e/pme/-l -> pmtRwe/-l
    touchez: t@e/pme/-k -> pmtRwe/-k
    touchée: t@e/pme/-j -> pmtRwe/-j
    toucher: t@e/pme -> pmtRwe
    touchant: t@e/pm@ -> pmtRw@
    toubib: t@e/svij -> svtRwij
    touchera: t@e/pm@a/Ra -> pmtRw@a/Ra
    touchés: t@e/pme/-s -> pmtRwe/-s
    touchait: t@e/pmie -> pmtRwie

## S117 (suffix) -- tance, tence, tesse

- merged keys [3, 11, 20] = `s@t` for tance, tence, tesse (sim 0.688, comfort 580.4)
- strokeFreqSaved 190.3, freqBenefiting 190.3 of 213.6 (share by freq 0.891, by count 0.724), boundary risks 1
- fallbacks: {'keyOverlap': 24}
- alternatives: merged [[3, 11, 20]] sim 0.688 saved 190.3; merged [[3, 20]] sim 0.6 saved 192.4; merged [[2, 3, 20]] sim 0.5 saved 165.9; merged [[3, 5, 20]] sim 0.5 saved 158.4; merged [[3, 12, 20]] sim 0.5 saved 162.0

    importance: aie/peR/t@s -> aie/sp@etR
    distance: pvis/t@s -> spv@ist
    existence: iekdnl/is/t@s -> iekdnl/s@ist
    circonstances: siR/kais/t@s/-s -> siR/ks@aist/-s
    résistance: Re/twis/t@s -> Re/stw@ist
    tristesse: tRis/ties -> stR@ist
    distances: pvis/t@s/-s -> spv@ist/-s
    politesse: pae/mti/ties -> pae/smt@it
    compétences: kai/pe/t@s/-s -> kai/sp@et/-s
    délicatesse: pve/mti/ka/ties -> pve/mti/ks@at

## S107 (suffix) -- ·ifique, ·ogique, ·onique, ·orique, ·Ogique, logique

- merged keys [13, 18, 24] = `ikZ` for ·ifique, ·ogique, ·onique, ·orique, ·Ogique, logique (sim 0.546, comfort 621.7)
- strokeFreqSaved 189.6, freqBenefiting 94.8 of 121.8 (share by freq 0.778, by count 0.856), boundary risks 0
- fallbacks: {'keyOverlap': 36, 'illegalChord': 3}
- alternatives: merged [[13, 18, 24]] sim 0.546 saved 189.6; merged [[18, 22, 24]] sim 0.531 saved 223.2; merged [[18, 21, 24]] sim 0.52 saved 217.6; merged [[13, 18, 22]] sim 0.512 saved 193.1; merged [[13, 18, 21]] sim 0.501 saved 188.6

    scientifique: sRw@/ti/kpik -> sRw@ikZ
    scientifique: sRw@/ti/kpik -> sRw@ikZ
    psychologique: spi/kae/mtae/vtik -> spi/kaiekZ
    scientifiques: sRw@/ti/kpik/-s -> sRw@ikZ/-s
    téléphonique: te/mte/kpae/mRik -> te/mtiekZ
    biologique: svRwae/mtae/vtik -> svRwaiekZ
    spécifique: spe/si/kpik -> spiekZ
    scientifiques: sRw@/ti/kpik/-s -> sRw@ikZ/-s
    téléphoniques: te/mte/kpae/mRik/-s -> te/mtiekZ/-s
    biologiques: svRwae/mtae/vtik/-s -> svRwaiekZ/-s

## S086 (suffix) -- ·[bi|cla|le|lle|mi|mmi|prun|pé|vi|é]tés

- dedicated keys [2, 4, 6, 7, 8, 11, 12, 13, 14] = `kpmtR@aie` for ·[bi|cla|le|lle|mi|mmi|prun|pé|vi|é]tés (sim 0.315, comfort 542.0)
- strokeFreqSaved 177.0, freqBenefiting 177.0 of 177.0 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 4, 6, 7, 8, 11, 12, 13, 14]] sim 0.315 saved 177.0; dedicated [[16, 18, 20]] sim 0.296 saved 177.0; dedicated [[16, 17, 18]] sim 0.296 saved 177.0; dedicated [[16, 18, 21]] sim 0.296 saved 177.0; dedicated [[16, 18, 23]] sim 0.296 saved 177.0

    invités: aie/vi/te/-s -> aie/kpmtR@aie/-s
    propriété: pRae/pRij/e/te -> pRae/pRij/kpmtR@aie
    comité: kae/mi/te -> kae/kpmtR@aie
    activité: ak/ti/vi/te -> ak/ti/kpmtR@aie
    invité: aie/vi/te -> aie/kpmtR@aie
    saleté: sa/mt@a/te -> sa/kpmtR@aie
    intimité: aie/ti/mi/te -> aie/ti/kpmtR@aie
    activités: ak/ti/vi/te/-s -> ak/ti/kpmtR@aie/-s
    gravité: ksRa/vi/te -> ksRa/kpmtR@aie
    saletés: sa/mt@a/te/-s -> sa/kpmtR@aie/-s

## S088 (suffix) -- ·[ccu|cra|cu|di|ffu|fu|lé|ni|nni|quou|tai]sé

- dedicated keys [18, 22, 23] = `-knl` for ·[ccu|cra|cu|di|ffu|fu|lé|ni|nni|quou|tai]sé (sim 0.286, comfort 288.0)
- strokeFreqSaved 175.1, freqBenefiting 175.1 of 175.1 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[20, 22, 23]] sim 0.286 saved 175.1; dedicated [[18, 22, 23]] sim 0.286 saved 175.1; dedicated [[19, 22, 23]] sim 0.286 saved 175.1; dedicated [[21, 22, 23]] sim 0.286 saved 175.1; dedicated [[2, 22, 23]] sim 0.25 saved 175.1

    refusé: R@a/kp@i/twe -> R@a/-knl
    refuser: R@a/kp@i/twe/-l -> R@a/-knl/-l
    écraser: e/kRa/twe/-l -> e/-knl/-l
    organiser: eR/ksa/mRi/twe/-l -> eR/ksa/-knl/-l
    accusé: a/k@i/twe -> a/-knl
    écrasé: e/kRa/twe -> e/-knl
    organisé: eR/ksa/mRi/twe -> eR/ksa/-knl
    accuser: a/k@i/twe/-l -> a/-knl/-l
    refusez: R@a/kp@i/twe/-k -> R@a/-knl/-k
    diffuser: pvi/kp@i/twe/-l -> pvi/-knl/-l

## P036 (prefix) -- bon, mon, fon

- merged keys [3, 5, 25] = `sv-m` for bon, mon, fon (sim 0.575, comfort 452.2)
- strokeFreqSaved 175.0, freqBenefiting 175.0 of 1007.2 (share by freq 0.174, by count 0.242), boundary risks 0
- fallbacks: {'keyOverlap': 114, 'illegalChord': 3, 'markCostTooHigh': 5}
- alternatives: merged [[3, 5, 6]] sim 0.645 saved 183.3; merged [[3, 5, 25]] sim 0.575 saved 175.0; merged [[3, 5]] sim 0.506 saved 183.4

    monter: mai/te/-l -> svtem/-l
    monté: mai/t*e -> svt*em
    montez: mai/te/-k -> svtem/-k
    montage: mai/taZ -> svtaZm
    montée: mai/te/-j -> svtem/-j
    montant: mai/t@ -> svt@m
    montait: mai/tie -> svtiem
    montés: mai/te/-s -> svtem/-s
    montons: mai/tai -> svtaim
    montrait: mai/tRie -> svtRiem

## S089 (suffix) -- ·ogie, ·onie, ·orie, ·omie

- dedicated keys [5, 6, 7, 8, 12, 13, 14] = `vmtRaie` for ·ogie, ·onie, ·orie, ·omie (sim 0.5, comfort 548.0)
- strokeFreqSaved 174.2, freqBenefiting 174.2 of 174.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[5, 6, 7, 8, 12, 13, 14]] sim 0.5 saved 174.2; dedicated [[13, 22, 24]] sim 0.416 saved 174.2; dedicated [[13, 21, 24]] sim 0.407 saved 174.2; dedicated [[21, 22, 24]] sim 0.405 saved 174.2; dedicated [[13, 24, 25]] sim 0.387 saved 174.2

    théorie: te/ae/Ri -> te/vmtRaie
    cérémonie: se/Re/mae/mRi -> se/Re/vmtRaie
    technologie: tiek/mRae/mtae/vti -> tiek/mRae/vmtRaie
    économie: e/kae/mRae/mi -> e/kae/vmtRaie
    économies: e/kae/mRae/mi/-s -> e/kae/vmtRaie/-s
    harmonie: aR/mae/mRi -> aR/vmtRaie
    compromis: kai/pRae/mi -> kai/vmtRaie
    psychologie: spi/kae/mtae/vti -> spi/kae/vmtRaie
    catégorie: ka/te/ksae/Ri -> ka/te/vmtRaie
    théories: te/ae/Ri/-s -> te/vmtRaie/-s

## P080 (prefix) -- ré[ca|ci|cla|cré|crée|im|in|mi|vei|vé]·

- dedicated keys [2, 5, 6, 7, 12, 13, 14] = `kvmtaie` for ré[ca|ci|cla|cré|crée|im|in|mi|vei|vé]· (sim 0.457, comfort 594.0)
- strokeFreqSaved 170.4, freqBenefiting 170.4 of 170.4 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[2, 5, 6, 7, 12, 13, 14]] sim 0.457 saved 170.4; dedicated [[2, 3, 6, 7, 12, 13]] sim 0.391 saved 170.4; dedicated [[2, 6, 7, 8, 12, 14]] sim 0.391 saved 170.4; dedicated [[2, 5, 6, 7, 12, 14]] sim 0.391 saved 170.4; dedicated [[2, 5, 8, 13, 14]] sim 0.326 saved 170.4

    réveiller: Re/vie/Rwe/-l -> kvmtaie/Rwe/-l
    réveillé: Re/vie/Rwe -> kvmtaie/Rwe
    réveillée: Re/vie/Rwe/-j -> kvmtaie/Rwe/-j
    réveillez: Re/vie/Rwe/-k -> kvmtaie/Rwe/-k
    révéler: Re/ve/mte/-l -> kvmtaie/mte/-l
    révélé: Re/ve/mte -> kvmtaie/mte
    réveillera: Re/vie/Rw@a/Ra -> kvmtaie/Rw@a/Ra
    réciter: Re/si/te/-l -> kvmtaie/te/-l
    réclamer: Re/kmta/me/-l -> kvmtaie/me/-l
    récréation: Re/kRe/a/sRwai -> kvmtaie/a/sRwai

## S123 (suffix) -- phone

- merged keys [17, 19, 22] = `-sdn` for phone (sim 0.8, comfort 511.4)
- strokeFreqSaved 170.1, freqBenefiting 170.1 of 170.1 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[17, 19, 22]] sim 0.8 saved 170.1; merged [[2, 4, 22]] sim 0.6 saved 166.5; merged [[14, 17, 19]] sim 0.5 saved 1.4; merged [[14, 22]] sim 0.5 saved 1.4

    téléphone: te/mte/kpen -> te/mtesdn
    téléphones: te/mte/kpen/-s -> te/mtesdn/-s
    magnétophone: ma/we/tae/kpen -> ma/we/taesdn
    interphone: aie/tieR/kpen -> aie/tiesdRn
    saxophone: sa/ksae/kpen -> sa/ksaesdn
    mégaphone: me/ksa/kpen -> me/ksasdn
    microphone: mi/kRae/kpen -> mi/kRaesdn
    magnétophones: ma/we/tae/kpen/-s -> ma/we/taesdn/-s
    dictaphone: pvik/ta/kpen -> pvik/tasdn
    mégaphones: me/ksa/kpen/-s -> me/ksasdn/-s

## S079 (suffix) -- gner, gneur

- merged keys [14, 20, 22] = `etn` for gner, gneur (sim 0.606, comfort 500.4)
- strokeFreqSaved 167.7, freqBenefiting 167.7 of 387.8 (share by freq 0.432, by count 0.623), boundary risks 8
- fallbacks: {'keyOverlap': 82, 'markCostTooHigh': 2}
- alternatives: merged [[14, 20, 22]] sim 0.606 saved 167.7

    accompagner: a/kai/pa/we/-l -> a/kai/paetn/-l
    soigner: swa/we/-l -> swaetn/-l
    éloigner: e/mtwa/we/-l -> e/mtwaetn/-l
    témoigner: te/mwa/we/-l -> te/mwaetn/-l
    épargner: e/paR/we/-l -> e/paetRn/-l
    accompagné: a/kai/pa/we -> a/kai/paetn
    soigné: swa/we -> swaetn
    épargné: e/paR/we -> e/paetRn
    accompagnez: a/kai/pa/we/-k -> a/kai/paetn/-k
    éloigné: e/mtwa/we -> e/mtwaetn

## S126 (suffix) -- cule, ·icule

- merged keys [18, 23] = `-kl` for cule, ·icule (sim 0.752, comfort 498.9)
- strokeFreqSaved 166.7, freqBenefiting 135.3 of 135.3 (share by freq 1.0, by count 0.973), boundary risks 4
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[18, 23]] sim 0.752 saved 166.7; merged [[16, 18, 23]] sim 0.658 saved 166.7; merged [[18, 20, 23]] sim 0.658 saved 166.7; merged [[18, 21, 23]] sim 0.658 saved 158.7; merged [[18, 22, 23]] sim 0.658 saved 166.7

    ridicule: Ri/pvi/k@il -> Ri/pvikl
    véhicule: ve/i/k@il -> vekl
    ridicule: Ri/pvi/k@il -> Ri/pvikl
    crépuscule: kRe/p@is/k@il -> kRe/p@iskl
    pellicule: pe/mti/k@il -> pe/mtikl
    minuscule: mi/mR@is/k@il -> mi/mR@iskl
    véhicules: ve/i/k@il/-s -> vekl/-s
    ridicules: Ri/pvi/k@il/-s -> Ri/pvikl/-s
    matricule: ma/tRi/k@il -> ma/tRikl
    particules: paR/ti/k@il/-s -> pakRl/-s

## S124 (suffix) -- dat, nat

- merged keys [12, 19, 22] = `adn` for dat, nat (sim 0.833, comfort 529.7)
- strokeFreqSaved 165.9, freqBenefiting 165.9 of 168.4 (share by freq 0.985, by count 0.593), boundary risks 0
- fallbacks: {'keyOverlap': 22}
- alternatives: merged [[12, 19, 22]] sim 0.833 saved 165.9; merged [[12, 19]] sim 0.754 saved 165.9; merged [[19, 22]] sim 0.667 saved 167.4; merged [[6, 8, 19]] sim 0.627 saved 135.3; merged [[19]] sim 0.587 saved 167.4

    soldats: sel/pva/-s -> saednl/-s
    soldat: sel/pva -> saednl
    mandat: m@/pva -> m@adn
    candidat: k@/pvi/pva -> k@/pvaidn
    assassinat: a/sa/si/mRa -> a/sa/saidn
    orphelinat: eR/kp@a/mti/mRa -> eR/kp@a/mtaidn
    candidats: k@/pvi/pva/-s -> k@/pvaidn/-s
    internat: aie/tieR/mRa -> aie/taiedRn
    mandats: m@/pva/-s -> m@adn/-s
    assassinats: a/sa/si/mRa/-s -> a/sa/saidn/-s

## S121 (suffix) -- guer, gué

- merged keys [6, 18, 19] = `m-kd` for guer, gué (sim 0.5, comfort 435.6)
- strokeFreqSaved 157.7, freqBenefiting 157.7 of 189.8 (share by freq 0.831, by count 0.609), boundary risks 5
- fallbacks: {'keyOverlap': 108}
- alternatives: merged [[6, 18, 19]] sim 0.5 saved 157.7; merged [[11, 18, 19]] sim 0.5 saved 183.3; merged [[9, 18, 19]] sim 0.5 saved 189.4; merged [[16, 18, 19]] sim 0.5 saved 189.8; merged [[8, 18, 19]] sim 0.5 saved 156.7

    fatigué: kpa/ti/kse -> kpa/mtikd
    fatiguée: kpa/ti/kse/-j -> kpa/mtikd/-j
    fatigué: kpa/ti/kse -> kpa/mtikd
    fatiguée: kpa/ti/kse/-j -> kpa/mtikd/-j
    draguer: pvRa/kse/-l -> pvmRakd/-l
    distinguer: pvis/taie/kse/-l -> pvis/mtaiekd/-l
    fatigués: kpa/ti/kse/-s -> kpa/mtikd/-s
    naviguer: mRa/vi/kse/-l -> mRa/vmikd/-l
    fatiguer: kpa/ti/kse/-l -> kpa/mtikd/-l
    distingué: pvis/taie/kse -> pvis/mtaiekd

## S128 (suffix) -- gramme, graphie, graphe

- merged keys [18, 19, 21, 25] = `-kdRm` for gramme (sim 0.545, comfort 638.5)
- merged keys [13, 18, 19, 21] = `ikdR` for graphie (sim 0.545, comfort 638.5)
- merged keys [16, 18, 19, 21] = `-jkdR` for graphe (sim 0.545, comfort 638.5)
- strokeFreqSaved 156.6, freqBenefiting 131.4 of 132.8 (share by freq 0.989, by count 0.976), boundary risks 6
- fallbacks: {'keyOverlap': 6}
- alternatives: merged [[18, 19, 21, 25], [13, 18, 19, 21], [16, 18, 19, 21]] sim 0.545 saved 156.6

    programme: pRae/ksRam -> pRaekdRm
    photographe: kpae/tae/ksRasd -> kpae/taejkdR
    télégramme: te/mte/ksRam -> te/mtekdRm
    photographie: kpae/tae/ksRa/kpi -> kpae/taiekdR
    autographe: ae/tae/ksRasd -> ae/taejkdR
    programmes: pRae/ksRam/-s -> pRaekdRm/-s
    orthographe: eR/tae/ksRasd -> eR/taejkdR
    photographes: kpae/tae/ksRasd/-s -> kpae/taejkdR/-s
    paragraphe: pa/Ra/ksRasd -> pa/RajkdR
    biographie: svRwae/ksRa/kpi -> svRwaiekdR

## S094 (suffix) -- ·[ce|da|de|la|le|lle|ra|re|rre|sa|ssa|ta|va]mment

- dedicated keys [16, 17, 25] = `-jsm` for ·[ce|da|de|la|le|lle|ra|re|rre|sa|ssa|ta|va]mment (sim 0.25, comfort 288.0)
- strokeFreqSaved 154.9, freqBenefiting 154.9 of 154.9 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 17, 19]] sim 0.25 saved 154.9; dedicated [[16, 17, 20]] sim 0.25 saved 154.9; dedicated [[16, 17, 21]] sim 0.25 saved 154.9; dedicated [[16, 17, 23]] sim 0.25 saved 154.9; dedicated [[16, 17, 25]] sim 0.25 saved 154.9

    apparemment: a/pa/Ra/m@ -> a/pa/-jsm
    évidemment: e/vi/pva/m@ -> e/vi/-jsm
    récemment: Re/sa/m@ -> Re/-jsm
    suffisamment: s@i/kpi/twa/m@ -> s@i/kpi/-jsm
    précédemment: pRe/se/pva/m@ -> pRe/se/-jsm
    différemment: pvi/kpe/Ra/m@ -> pvi/kpe/-jsm
    constamment: kais/ta/m@ -> kais/-jsm
    violemment: vRwae/mta/m@ -> vRwae/-jsm
    prudemment: pR@i/pva/m@ -> pR@i/-jsm
    notamment: mRae/ta/m@ -> mRae/-jsm

## S096 (suffix) -- ·[ba|ca|ci|cré|cy|lon|man|men|mmen|ri|si|ven]taire

- dedicated keys [3, 5, 7, 12, 13, 14, 21] = `svtaieR` for ·[ba|ca|ci|cré|cy|lon|man|men|mmen|ri|si|ven]taire (sim 0.304, comfort 516.0)
- strokeFreqSaved 152.0, freqBenefiting 152.0 of 152.0 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[3, 5, 7, 12, 13, 14, 21]] sim 0.304 saved 152.0; dedicated [[16, 17, 18]] sim 0.286 saved 152.0; dedicated [[16, 17, 20]] sim 0.286 saved 152.0; dedicated [[16, 17, 21]] sim 0.286 saved 152.0; dedicated [[16, 17, 23]] sim 0.286 saved 152.0

    secrétaire: s@a/kRe/tieR -> s@a/svtaieR
    volontaire: vae/mtai/tieR -> vae/svtaieR
    célibataire: se/mti/sva/tieR -> se/mti/svtaieR
    commentaire: kae/m@/tieR -> kae/svtaieR
    commentaires: kae/m@/tieR/-s -> kae/svtaieR/-s
    volontaires: vae/mtai/tieR/-s -> vae/svtaieR/-s
    supplémentaires: s@i/pmte/m@/tieR/-s -> s@i/pmte/svtaieR/-s
    célibataire: se/mti/sva/tieR -> se/mti/svtaieR
    alimentaire: a/mti/m@/tieR -> a/mti/svtaieR
    supplémentaire: s@i/pmte/m@/tieR -> s@i/pmte/svtaieR

## P085 (prefix) -- dé[ca|chaî|cou|gou|goû|la|lai|pou|qua|tra]·

- dedicated keys [4, 6, 7, 8, 12, 13, 14] = `pmtRaie` for dé[ca|chaî|cou|gou|goû|la|lai|pou|qua|tra]· (sim 0.442, comfort 487.0)
- strokeFreqSaved 150.9, freqBenefiting 150.9 of 150.9 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[4, 6, 7, 8, 12, 13, 14]] sim 0.442 saved 150.9; dedicated [[4, 5, 6, 7, 13, 14]] sim 0.423 saved 150.9; dedicated [[2, 3, 4, 6, 11, 13, 14]] sim 0.365 saved 150.9; dedicated [[2, 3, 6, 7, 11, 13, 14]] sim 0.365 saved 150.9; dedicated [[2, 3, 7, 8, 11, 12, 14]] sim 0.365 saved 150.9

    découvert: pve/k@e/vieR -> pmtRaie/vieR
    découvrir: pve/k@e/vRiR -> pmtRaie/vRiR
    découverte: pve/k@e/vietR -> pmtRaie/vietR
    découper: pve/k@e/pe/-l -> pmtRaie/pe/-l
    découverte: pve/k@e/vietR/-j -> pmtRaie/vietR/-j
    découvertes: pve/k@e/vietR/-s -> pmtRaie/vietR/-s
    découpé: pve/k@e/pe -> pmtRaie/pe
    découvrira: pve/k@e/vRi/Ra -> pmtRaie/vRi/Ra
    découvrez: pve/k@e/vRe -> pmtRaie/vRe
    découverts: pve/k@e/vieR/-s -> pmtRaie/vieR/-s

## S097 (suffix) -- ·[mo|pio|sio|so|ssio|sso|tio|to|xo|ço]nné

- dedicated keys [16, 18, 22] = `-jkn` for ·[mo|pio|sio|so|ssio|sso|tio|to|xo|ço]nné (sim 0.333, comfort 276.0)
- strokeFreqSaved 150.0, freqBenefiting 150.0 of 150.1 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[16, 18, 20]] sim 0.333 saved 150.0; dedicated [[16, 17, 18]] sim 0.333 saved 150.0; dedicated [[16, 18, 22]] sim 0.333 saved 150.0; dedicated [[16, 18, 25]] sim 0.333 saved 150.0; dedicated [[3, 16, 18]] sim 0.292 saved 150.0

    empoisonné: @/pwa/twae/mRe -> @/pwa/-jkn
    impressionné: aie/pRe/sRwae/mRe -> aie/pRe/-jkn
    fonctionner: kpaik/sRwae/mRe/-l -> kpaik/-jkn/-l
    mentionné: m@/sRwae/mRe -> m@/-jkn
    impressionner: aie/pRe/sRwae/mRe/-l -> aie/pRe/-jkn/-l
    démissionné: pve/mi/sRwae/mRe -> pve/mi/-jkn
    démissionner: pve/mi/sRwae/mRe/-l -> pve/mi/-jkn/-l
    espionner: ies/pRwae/mRe/-l -> ies/-jkn/-l
    raisonner: Rie/twae/mRe/-l -> Rie/-jkn/-l
    empoisonner: @/pwa/twae/mRe/-l -> @/pwa/-jkn/-l

## P093 (prefix) -- pi, pis, pié

- merged keys [4, 8, 13, 16] = `pRij` for pi (sim 0.711, comfort 607.5)
- merged keys [3, 4, 13, 16] = `spij` for pis (sim 0.711, comfort 607.5)
- merged keys [4, 13, 14, 16] = `piej` for pié (sim 0.711, comfort 607.5)
- strokeFreqSaved 149.7, freqBenefiting 149.7 of 231.1 (share by freq 0.648, by count 0.644), boundary risks 2
- fallbacks: {'keyOverlap': 111}
- alternatives: merged [[3, 4, 8, 13], [3, 4, 13, 17], [3, 4, 13, 16]] sim 0.782 saved 170.6; merged [[4, 8, 13, 17], [3, 4, 13, 17], [4, 13, 16, 17]] sim 0.731 saved 170.3; merged [[4, 8, 13, 16], [3, 4, 13, 16], [4, 13, 14, 16]] sim 0.711 saved 149.7; merged [[3, 4, 8, 16], [3, 4, 16, 17], [3, 4, 14, 16]] sim 0.69 saved 167.8; merged [[4, 8, 13], [3, 4, 13], [4, 13, 16]] sim 0.679 saved 154.2

    pistolet: pis/tae/mtie -> sptaiej/mtie
    pilote: pi/mtet -> pmtRiejt
    pigé: pi/vte -> pvtRiej
    piqué: pi/ke -> kpRiej
    pilote: pi/mtet -> pmtRiejt
    pilotes: pi/mtet/-s -> pmtRiejt/-s
    pistolets: pis/tae/mtie/-s -> sptaiej/mtie/-s
    pilote: pi/mtet -> pmtRiejt
    picoler: pi/kae/mte/-l -> kpRaiej/mte/-l
    pigez: pi/vte/-k -> pvtRiej/-k

## P077 (prefix) -- i, hi

- merged keys [13] = `i` for i, hi (sim 0.5, comfort 351.2)
- strokeFreqSaved 146.8, freqBenefiting 146.8 of 346.8 (share by freq 0.423, by count 0.324), boundary risks 12
- fallbacks: {'markCostTooHigh': 8, 'keyOverlap': 88}
- alternatives: merged [[13]] sim 0.5 saved 146.8

    image: i/maZ -> maiZ
    images: i/maZ/-s -> maiZ/-s
    idéal: i/pve/al -> pvie/al
    idéal: i/pve/al -> pvie/al
    idéale: i/pve/al/-j -> pvie/al/-j
    idole: i/pvel -> pviel
    isolé: i/twae/mte -> twaie/mte
    hibou: i/sv@e -> sv@ie
    isolé: i/twae/mte -> twaie/mte
    idéaux: i/pve/ae -> pvie/ae

## P107 (prefix) -- fu

- merged keys [2, 4, 12] = `kpa` for fu (sim 0.5, comfort 440.2)
- strokeFreqSaved 145.5, freqBenefiting 145.5 of 152.9 (share by freq 0.952, by count 0.614), boundary risks 0
- fallbacks: {'keyOverlap': 49}
- alternatives: merged [[2, 4]] sim 0.667 saved 149.9; merged [[2, 4, 12]] sim 0.5 saved 145.5; merged [[2, 3, 4]] sim 0.5 saved 150.1; merged [[2, 4, 5]] sim 0.5 saved 150.1; merged [[2, 4, 16]] sim 0.5 saved 149.5

    fusil: kp@i/twi -> kptwai
    fumer: kp@i/me/-l -> kpmae/-l
    furieux: kp@i/Rw@ie -> kpRw@aie
    fusils: kp@i/twi/-s -> kptwai/-s
    furieuse: kp@i/Rw@ienl -> kpRw@aienl
    fumé: kp@i/m*e -> kpm*ae
    fumez: kp@i/me/-k -> kpmae/-k
    fumait: kp@i/mie -> kpmaie
    fusiller: kp@i/twi/Rwe/-l -> kptwai/Rwe/-l
    furie: kp@i/Ri -> kpRai

## S100 (suffix) -- ·[bu|do|ffé|fé|go|lu|sso|tou|tu]ré

- dedicated keys [17, 19, 21] = `-sdR` for ·[bu|do|ffé|fé|go|lu|sso|tou|tu]ré (sim 0.308, comfort 214.0)
- strokeFreqSaved 142.0, freqBenefiting 142.0 of 142.0 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: dedicated [[17, 19, 21]] sim 0.308 saved 142.0; dedicated [[16, 17, 19]] sim 0.308 saved 142.0; dedicated [[17, 19, 20]] sim 0.308 saved 142.0; dedicated [[17, 19, 23]] sim 0.308 saved 142.0; dedicated [[17, 18, 19]] sim 0.308 saved 142.0

    préféré: pRe/kpe/Re -> pRe/-sdR
    adoré: a/pvae/Re -> a/-sdR
    préférez: pRe/kpe/Re/-k -> pRe/-sdR/-k
    adorer: a/pvae/Re/-l -> a/-sdR/-l
    torturer: teR/t@i/Re/-l -> teR/-sdR/-l
    entouré: @/t@e/Re -> @/-sdR
    transféré: tR@s/kpe/Re -> tR@s/-sdR
    capturé: kajk/t@i/Re -> kajk/-sdR
    capturer: kajk/t@i/Re/-l -> kajk/-sdR/-l
    torturé: teR/t@i/Re -> teR/-sdR

## S130 (suffix) -- ent, ant

- merged keys [11] = `@` for ent, ant (sim 0.5, comfort 500.0)
- strokeFreqSaved 138.2, freqBenefiting 138.2 of 149.8 (share by freq 0.923, by count 0.76), boundary risks 8
- fallbacks: {'keyOverlap': 25}
- alternatives: merged [[11]] sim 0.5 saved 138.2

    client: kmtij/@ -> kmt@ij
    clients: kmtij/@/-s -> kmt@ij/-s
    effrayant: e/kpRiej/@ -> e/kpR@iej
    croyant: kRwaj/@ -> kRw@aj
    voyant: vwaj/@ -> vw@aj
    voyant: vwaj/@ -> vw@aj
    fainéants: kpe/mRe/@/-s -> kpe/mR@e/-s
    croyants: kRwaj/@/-s -> kRw@aj/-s
    fainéant: kpe/mRe/@ -> kpe/mR@e
    payant: piej/@ -> p@iej

## P105 (prefix) -- ga

- merged keys [2, 3, 8] = `ksR-` for ga (sim 0.5, comfort 496.9)
- strokeFreqSaved 135.0, freqBenefiting 135.0 of 164.0 (share by freq 0.823, by count 0.806), boundary risks 0
- fallbacks: {'keyOverlap': 20}
- alternatives: merged [[2, 3]] sim 0.667 saved 163.1; merged [[2, 3, 4]] sim 0.5 saved 163.2; merged [[2, 3, 8]] sim 0.5 saved 135.0; merged [[2, 3, 11]] sim 0.5 saved 163.0; merged [[2, 3, 7]] sim 0.5 saved 146.0

    gamin: ksa/maie -> ksmRaie
    gamins: ksa/maie/-s -> ksmRaie/-s
    gamin: ksa/maie -> ksmRaie
    gamine: ksa/min -> ksmRin
    gamine: ksa/min -> ksmRin
    gazon: ksa/twai -> kstRwai
    galop: ksa/mtae -> ksmtRae
    gamines: ksa/min/-s -> ksmRin/-s
    gazelle: ksa/twiel -> kstRwiel
    gamins: ksa/maie/-s -> ksmRaie/-s

## S133 (suffix) -- ·aliste

- merged keys [12, 20, 23] = `atl` for ·aliste (sim 0.562, comfort 601.7)
- strokeFreqSaved 132.8, freqBenefiting 66.4 of 72.2 (share by freq 0.92, by count 0.643), boundary risks 0
- fallbacks: {'keyOverlap': 46}
- alternatives: merged [[17, 20, 23]] sim 0.75 saved 144.1; merged [[12, 20, 23]] sim 0.562 saved 132.8; merged [[12, 17, 20]] sim 0.562 saved 132.6; merged [[13, 20, 23]] sim 0.562 saved 132.6; merged [[12, 17, 23]] sim 0.562 saved 132.6

    journaliste: vt@eR/mRa/mtist -> vt@aetRl
    spécialiste: spe/sRwa/mtist -> spaetl
    journalistes: vt@eR/mRa/mtist/-s -> vt@aetRl/-s
    spécialistes: spe/sRwa/mtist/-s -> spaetl/-s
    capitaliste: ka/pi/ta/mtist -> ka/paitl
    idéaliste: i/pve/a/mtist -> i/pvaetl
    surréaliste: s@iR/Re/a/mtist -> s@iR/Raetl
    idéaliste: i/pve/a/mtist -> i/pvaetl
    matérialiste: ma/te/Rwa/mtist -> ma/taetl
    capitalistes: ka/pi/ta/mtist/-s -> ka/paitl/-s

## P061 (prefix) -- co°·, co@·, cau°·, coe·

- merged keys [2, 11, 14] = `k@e` for co@·, cau°· (sim 0.564, comfort 506.4)
- merged keys [2, 8, 14] = `kRe` for co°· (sim 0.564, comfort 506.4)
- merged keys [2, 9, 14] = `kwe` for coe· (sim 0.564, comfort 506.4)
- strokeFreqSaved 131.1, freqBenefiting 65.5 of 246.4 (share by freq 0.266, by count 0.368), boundary risks 6
- fallbacks: {'keyOverlap': 103}
- alternatives: merged [[2, 8, 11, 12], [2, 11, 12, 14], [2, 9, 11, 12]] sim 0.61 saved 348.9; merged [[2, 8, 11, 14], [2, 9, 11, 14], [2, 3, 11, 14]] sim 0.604 saved 317.2; merged [[2, 8, 11], [2, 11, 14], [2, 9, 11]] sim 0.54 saved 335.3; merged [[2, 11], [2, 14], [2, 8]] sim 0.5 saved 237.6; merged [[2, 11, 14], [2, 8, 14], [2, 9, 14]] sim 0.564 saved 131.1

    cauchemar: kae/pm@a/maR -> km@aeR
    comédie: kae/me/pvi -> kpvwie
    cauchemars: kae/pm@a/maR/-s -> km@aeR/-s
    commérages: kae/me/RaZ/-s -> kRwaeZ/-s
    comédies: kae/me/pvi/-s -> kpvwie/-s
    cohérent: kae/e/R@ -> kRw@e
    commandons: kae/m@/pvai -> kpv@aie
    cohérente: kae/e/R@t -> kRw@et
    commandité: kae/m@/pvi/te -> kpv@ie/te
    cautériser: kae/te/Ri/twe/-l -> kRwie/twe/-l

## P088 (prefix) -- je, gé, ge

- merged keys [5, 7, 9] = `vtw-` for je, gé, ge (sim 0.5, comfort 455.0)
- strokeFreqSaved 129.9, freqBenefiting 129.9 of 285.5 (share by freq 0.455, by count 0.528), boundary risks 0
- fallbacks: {'keyOverlap': 51}
- alternatives: merged [[4, 5, 7]] sim 0.5 saved 130.4; merged [[5, 7, 9]] sim 0.5 saved 129.9; merged [[3, 5, 7]] sim 0.5 saved 130.4; merged [[5, 7, 12]] sim 0.5 saved 129.0

    genoux: vt@a/mR@e/-s -> vmtRw@e/-s
    génie: vte/mRi -> vmtRwi
    genou: vt@a/mR@e -> vmtRw@e
    géant: vte/@ -> vtw@
    géant: vte/@ -> vtw@
    géants: vte/@/-s -> vtw@/-s
    gémit: vte/mi/-t -> vmtwi/-t
    génies: vte/mRi/-s -> vmtRwi/-s
    géante: vte/@t -> vtw@t
    gémir: vte/miR -> vmtwiR

## S127 (suffix) -- gie

- merged keys [11, 24] = `@Z` for gie (sim 0.5, comfort 499.1)
- strokeFreqSaved 128.6, freqBenefiting 128.6 of 164.5 (share by freq 0.782, by count 0.899), boundary risks 0
- fallbacks: {'keyOverlap': 11, 'illegalChord': 4}
- alternatives: merged [[24]] sim 0.667 saved 159.9; merged [[11, 24]] sim 0.5 saved 128.6; merged [[9, 24]] sim 0.5 saved 159.9; merged [[22, 24]] sim 0.5 saved 159.9

    énergie: e/mRieR/vti -> e/mR@ieRZ
    technologie: tiek/mRae/mtae/vti -> tiek/mRae/mt@aeZ
    stratégie: stRa/te/vti -> stRa/t@eZ
    hémorragie: e/mae/Ra/vti -> e/mae/R@aZ
    psychologie: spi/kae/mtae/vti -> spi/kae/mt@aeZ
    biologie: svRwae/mtae/vti -> svRwae/mt@aeZ
    allergie: a/mtieR/vti -> a/mt@ieRZ
    technologies: tiek/mRae/mtae/vti/-s -> tiek/mRae/mt@aeZ/-s
    idéologie: i/pve/ae/mtae/vti -> i/pve/ae/mt@aeZ
    mythologie: mi/tae/mtae/vti -> mi/tae/mt@aeZ

## P096 (prefix) -- ta, tar

- merged keys [2, 7, 8] = `ktR-` for ta, tar (sim 0.543, comfort 461.4)
- strokeFreqSaved 127.5, freqBenefiting 127.5 of 200.9 (share by freq 0.634, by count 0.58), boundary risks 0
- fallbacks: {'keyOverlap': 167}
- alternatives: merged [[7, 8]] sim 0.696 saved 132.0; merged [[7, 21]] sim 0.652 saved 136.4; merged [[7]] sim 0.609 saved 140.3; merged [[6, 7, 8]] sim 0.543 saved 124.4; merged [[2, 7, 8]] sim 0.543 saved 127.5

    tapis: ta/pi -> kptRi
    taper: ta/pe/-l -> kptRe/-l
    tabac: ta/sva -> ksvtRa
    tarder: taR/pve/-l -> kpvtRe/-l
    tapé: ta/pe -> kptRe
    tabassé: ta/sva/se -> ksvtRa/se
    tapez: ta/pe/-k -> kptRe/-k
    taverne: ta/vieRn -> kvtRieRn
    tapin: ta/paie -> kptRaie
    tardé: taR/pve -> kpvtRe

## S131 (suffix) -- port, forme, fort

- merged keys [4, 21, 25] = `p-Rm` for port, forme, fort (sim 0.551, comfort 631.9)
- strokeFreqSaved 122.9, freqBenefiting 122.9 of 148.5 (share by freq 0.827, by count 0.893), boundary risks 0
- fallbacks: {'keyOverlap': 6}
- alternatives: merged [[16, 18, 21]] sim 0.559 saved 148.4; merged [[4, 21, 25]] sim 0.551 saved 122.9; merged [[14, 21, 25]] sim 0.545 saved 114.4; merged [[2, 4, 21]] sim 0.547 saved 109.7; merged [[17, 19, 21]] sim 0.534 saved 102.6

    aéroport: a/e/Rae/peR -> a/e/pRaeRm
    uniforme: @i/mRi/kpeRm -> @i/pmRiRm
    renforts: R@/kpeR/-s -> pR@Rm/-s
    transport: tR@s/peR -> ptR@sRm
    renfort: R@/kpeR -> pR@Rm
    transports: tR@s/peR/-s -> ptR@sRm/-s
    uniformes: @i/mRi/kpeRm/-s -> @i/pmRiRm/-s
    confort: kai/kpeR -> kpaiRm
    réconfort: Re/kai/kpeR -> Re/kpaiRm
    aéroports: a/e/Rae/peR/-s -> a/e/pRaeRm/-s

## S136 (suffix) -- dence, ·idence, dance

- merged keys [17, 19] = `-sd` for dence, ·idence, dance (sim 0.744, comfort 391.0)
- strokeFreqSaved 120.5, freqBenefiting 92.8 of 92.8 (share by freq 1.0, by count 1.0), boundary risks 11
- fallbacks: {}
- alternatives: merged [[17, 19]] sim 0.744 saved 120.5; merged [[17, 19, 21]] sim 0.651 saved 120.0; merged [[16, 17, 19]] sim 0.651 saved 120.5; merged [[5, 17, 19]] sim 0.651 saved 106.1; merged [[6, 17, 19]] sim 0.651 saved 120.5

    coïncidence: kae/aie/si/pv@s -> kae/aiesd
    évidence: e/vi/pv@s -> e/visd
    tendance: t@/pv@s -> t@sd
    résidence: Re/twi/pv@s -> Re/twisd
    indépendance: aie/pve/p@/pv@s -> aie/pve/p@sd
    correspondance: kae/Ries/pai/pv@s -> kae/Ries/paisd
    prudence: pR@i/pv@s -> pR@isd
    présidence: pRe/twi/pv@s -> pResd
    abondance: a/svai/pv@s -> a/svaisd
    confidence: kai/kpi/pv@s -> kaisd

## S132 (suffix) -- mètre, mettre, raître

- merged keys [20, 21, 25] = `-tRm` for mètre, mettre, raître (sim 0.846, comfort 560.4)
- strokeFreqSaved 120.1, freqBenefiting 120.1 of 146.4 (share by freq 0.82, by count 0.991), boundary risks 0
- fallbacks: {'keyOverlap': 1}
- alternatives: merged [[20, 21, 25]] sim 0.846 saved 120.1; merged [[20, 21]] sim 0.615 saved 120.1; merged [[21, 25]] sim 0.539 saved 120.1; merged [[20, 25]] sim 0.539 saved 146.4; merged [[9, 20, 21]] sim 0.538 saved 118.2

    disparaître: pvis/pa/RietR -> pvis/patRm
    kilomètres: ki/mtae/mietR/-s -> ki/mtaetRm/-s
    promettre: pRae/mietR -> pRaetRm
    transmettre: tR@s/mietR -> tR@stRm
    périmètre: pe/Ri/mietR -> pe/RitRm
    apparaître: a/pa/RietR -> a/patRm
    géomètre: vte/ae/mietR -> vte/aetRm
    soumettre: s@e/mietR -> s@etRm
    centimètres: s@/ti/mietR/-s -> s@/titRm/-s
    compromettre: kai/pRae/mietR -> kai/pRaetRm

## S137 (suffix) -- ssure

- merged keys [17, 21] = `-sR` for ssure (sim 0.8, comfort 596.4)
- strokeFreqSaved 119.5, freqBenefiting 119.5 of 119.5 (share by freq 1.0, by count 1.0), boundary risks 3
- fallbacks: {}
- alternatives: merged [[17, 21]] sim 0.8 saved 119.5; merged [[17, 19, 21]] sim 0.7 saved 119.5; merged [[8, 17, 21]] sim 0.7 saved 119.4; merged [[16, 17, 21]] sim 0.7 saved 119.5; merged [[17, 20, 21]] sim 0.7 saved 119.5

    chaussures: pmae/s@iR/-s -> pmaesR/-s
    blessure: svmte/s@iR -> svmtesR
    blessures: svmte/s@iR/-s -> svmtesR/-s
    chaussure: pmae/s@iR -> pmaesR
    éclaboussures: e/kmta/sv@e/s@iR/-s -> e/kmta/sv@esR/-s
    moisissure: mwa/twi/s@iR -> mwa/twisR
    éclaboussure: e/kmta/sv@e/s@iR -> e/kmta/sv@esR
    vomissures: vae/mi/s@iR/-s -> vae/misR/-s
    moisissures: mwa/twi/s@iR/-s -> mwa/twisR/-s
    vomissure: vae/mi/s@iR -> vae/misR

## S122 (suffix) -- ·ologie, ·ologique

- dedicated keys [5, 6, 7, 12, 13, 14, 18] = `vmtaiek` for ·ologie, ·ologique (sim 0.55, comfort 611.0)
- strokeFreqSaved 116.8, freqBenefiting 58.4 of 61.0 (share by freq 0.958, by count 0.956), boundary risks 0
- fallbacks: {'markCostTooHigh': 7}
- alternatives: dedicated [[5, 6, 7, 12, 13, 14, 18]] sim 0.55 saved 116.8; dedicated [[13, 18, 23]] sim 0.475 saved 116.8; dedicated [[13, 18, 24]] sim 0.475 saved 116.8; dedicated [[5, 6, 7, 8, 12, 13, 14, 18]] sim 0.475 saved 116.8; dedicated [[6, 7, 24]] sim 0.45 saved 116.8

    technologie: tiek/mRae/mtae/vti -> tiek/vmtaiek
    psychologique: spi/kae/mtae/vtik -> spi/vmtaiek
    psychologie: spi/kae/mtae/vti -> spi/vmtaiek
    technologies: tiek/mRae/mtae/vti/-s -> tiek/vmtaiek/-s
    idéologie: i/pve/ae/mtae/vti -> i/pve/vmtaiek
    théologie: te/ae/mtae/vti -> te/vmtaiek
    archéologie: aR/ke/ae/mtae/vti -> aR/ke/vmtaiek
    idéologique: i/pve/ae/mtae/vtik -> i/pve/vmtaiek
    psychologiques: spi/kae/mtae/vtik/-s -> spi/vmtaiek/-s
    technologique: tiek/mRae/mtae/vtik -> tiek/vmtaiek

## S118 (suffix) -- ffer, fait, ffeur, fer, fer

- merged keys [8, 14, 17, 19] = `Resd` for ffer, fait, fer, fer (sim 0.642, comfort 584.1)
- merged keys [8, 17, 19, 21] = `R-sdR` for ffeur (sim 0.642, comfort 584.1)
- strokeFreqSaved 113.7, freqBenefiting 113.7 of 201.4 (share by freq 0.565, by count 0.384), boundary risks 0
- fallbacks: {'keyOverlap': 130}
- alternatives: merged [[8, 14, 17, 19], [8, 17, 19, 21]] sim 0.642 saved 113.7; merged [[11, 14, 17, 19], [11, 17, 19, 21]] sim 0.604 saved 111.4; merged [[14, 17, 19], [17, 19, 21]] sim 0.566 saved 122.9; merged [[14, 16, 17, 19], [14, 17, 19, 21]] sim 0.63 saved 81.4; merged [[14, 17, 19, 21], [8, 17, 19, 21]] sim 0.717 saved 74.1

    chauffeur: pmae/kp@R -> pmRaesdR
    parfait: paR/kpie -> pRaesdR
    coiffeur: kwa/kp@R -> kRwasdR
    surfer: s@R/kpe/-l -> sR@esdR/-l
    chauffeurs: pmae/kp@R/-s -> pmRaesdR/-s
    coiffer: kwa/kpe/-l -> kRwaesd/-l
    parfait: paR/kpie -> pRaesdR
    parfaits: paR/kpie/-s -> pRaesdR/-s
    bluffer: svmt@/kpe/-l -> svmtR@esd/-l
    assoiffés: a/swa/kpe/-s -> a/sRwaesd/-s

## P074 (prefix) -- plu, pla, plan

- merged keys [4, 5, 12, 23] = `pval` for plu, pla (sim 0.5, comfort 619.8)
- merged keys [4, 5, 11, 23] = `pv@l` for plan (sim 0.5, comfort 619.8)
- strokeFreqSaved 112.8, freqBenefiting 112.8 of 370.3 (share by freq 0.305, by count 0.537), boundary risks 0
- fallbacks: {'keyOverlap': 62, 'illegalChord': 1}
- alternatives: merged [[4, 11, 12, 23], [4, 8, 11, 23]] sim 0.613 saved 112.3; merged [[4, 12, 23], [4, 11, 23]] sim 0.6 saved 108.7; merged [[4, 5, 12, 23], [4, 5, 11, 23]] sim 0.5 saved 112.8; merged [[4, 9, 12, 23], [4, 9, 11, 23]] sim 0.5 saved 112.8; merged [[4, 6, 12, 23], [4, 6, 11, 23]] sim 0.5 saved 49.7

    planète: pmta/mRiet -> pvmRaietl
    planté: pmt@/te -> pvt@el
    planter: pmt@/te/-l -> pvt@el/-l
    planètes: pmta/mRiet/-s -> pvmRaietl/-s
    plaqué: pmta/ke -> kpvael
    planqué: pmt@/ke -> kpv@el
    plantée: pmt@/te/-j -> pvt@el/-j
    plantés: pmt@/te/-s -> pvt@el/-s
    placés: pmta/se/-s -> spvael/-s
    placés: pmta/se/-s -> spvael/-s

## S140 (suffix) -- tuel, tel

- merged keys [20, 23] = `-tl` for tuel, tel (sim 0.715, comfort 477.9)
- strokeFreqSaved 111.2, freqBenefiting 111.2 of 111.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[20, 23]] sim 0.715 saved 111.2; merged [[20, 22, 23]] sim 0.626 saved 111.2; merged [[18, 20, 23]] sim 0.626 saved 94.5; merged [[12, 20, 23]] sim 0.626 saved 103.5; merged [[11, 20, 23]] sim 0.626 saved 103.2

    mortel: meR/tiel -> metRl
    inhabituel: i/mRa/svi/t@aiel -> i/mRa/svitl
    spirituel: spi/Ri/t@aiel -> spi/Ritl
    mortelle: meR/tiel/-j -> metRl/-j
    habituel: a/svi/t@aiel -> a/svitl
    habituelle: a/svi/t@aiel/-j -> a/svitl/-j
    spirituelle: spi/Ri/t@aiel/-j -> spi/Ritl/-j
    habituels: a/svi/t@aiel/-s -> a/svitl/-s
    mortels: meR/tiel/-s -> metRl/-s
    immortel: i/meR/tiel -> i/metRl

## P112 (prefix) -- aéro

- merged keys [8, 12] = `Ra` for aéro (sim 0.5, comfort 484.0)
- strokeFreqSaved 109.1, freqBenefiting 36.4 of 40.6 (share by freq 0.896, by count 0.364), boundary risks 0
- fallbacks: {'keyOverlap': 28}
- alternatives: merged [[8, 12]] sim 0.5 saved 109.1; merged [[8, 14]] sim 0.5 saved 6.7; merged [[8, 12, 14]] sim 0.7 saved 5.8; merged [[12, 14, 21]] sim 0.5 saved 5.8

    aéroport: a/e/Rae/peR -> pRaeR
    aéroports: a/e/Rae/peR/-s -> pRaeR/-s
    aérobic: a/e/Rae/svik -> svRaik
    aérodynamique: a/e/Rae/pvi/mRa/mik -> pvRai/mRa/mik
    aéroportée: a/e/Rae/peR/te/-j -> pRaeR/te/-j
    aérosol: a/e/Rae/sel -> sRael
    aérodynamique: a/e/Rae/pvi/mRa/mik -> pvRai/mRa/mik
    aérosols: a/e/Rae/sel/-s -> sRael/-s
    aéroporté: a/e/Rae/peR/te -> pRaeR/te
    aéroportées: a/e/Rae/peR/te/-js -> pRaeR/te/-js

## P083 (prefix) -- eni·, seni·

- merged keys [3, 8, 11, 13] = `sR@i` for eni· (sim 0.589, comfort 554.7)
- merged keys [3, 11, 13, 17] = `s@is` for seni· (sim 0.589, comfort 554.7)
- strokeFreqSaved 108.2, freqBenefiting 54.1 of 159.5 (share by freq 0.339, by count 0.383), boundary risks 2
- fallbacks: {'keyOverlap': 305}
- alternatives: merged [[3, 8, 11, 13], [3, 11, 13, 17]] sim 0.589 saved 108.2; merged [[8, 11, 13, 17], [3, 11, 13, 17]] sim 0.5 saved 114.1

    sentiras: s@/ti/Ra/-d -> sR@ais/-d
    antidote: @/ti/pvet -> spvR@iet
    sentirez: s@/ti/Re/-d -> sR@ies/-d
    handicapés: @/pvi/ka/pe/-s -> ksR@ai/pe/-s
    envisage: @/vi/twaZ -> stRw@aiZ
    handicap: @/pvi/kajk -> ksR@aijk
    envisagé: @/vi/twa/vte -> stRw@ai/vte
    emprisonné: @/pRi/twae/mRe -> stRw@aie/mRe
    sentirai: s@/ti/Re/-t -> sR@ies/-t
    emprisonner: @/pRi/twae/mRe/-l -> stRw@aie/mRe/-l

## P082 (prefix) -- exa·, ex, exi·

- dedicated keys [12, 13, 14, 18, 19, 22, 23] = `aiekdnl` for exa·, ex, exi· (sim 0.5, comfort 505.0)
- strokeFreqSaved 104.1, freqBenefiting 104.1 of 227.6 (share by freq 0.457, by count 0.713), boundary risks 0
- fallbacks: {'noGain': 56}
- alternatives: dedicated [[12, 13, 14, 18, 19, 22, 23]] sim 0.5 saved 104.1; dedicated [[13, 14, 18, 19, 22, 23]] sim 0.458 saved 104.1; dedicated [[7, 9, 13]] sim 0.369 saved 104.1; dedicated [[2, 3]] sim 0.359 saved 104.1

    examens: iekdnl/a/maie/-s -> aiekdnl/maie/-s
    examiner: iekdnl/a/mi/mRe/-l -> aiekdnl/mi/mRe/-l
    exagères: iekdnl/a/vtieR/-d -> aiekdnl/vtieR/-d
    exagère: iekdnl/a/vtieR -> aiekdnl/vtieR
    examiné: iekdnl/a/mi/mRe -> aiekdnl/mi/mRe
    examine: iekdnl/a/min -> aiekdnl/min
    exigé: iekdnl/i/vte -> aiekdnl/vte
    exagérez: iekdnl/a/vte/Re/-k -> aiekdnl/vte/Re/-k
    exiger: iekdnl/i/vte/-l -> aiekdnl/vte/-l
    exagérer: iekdnl/a/vte/Re/-l -> aiekdnl/vte/Re/-l

## S101 (suffix) -- ·oler, ·olet, ·olat

- merged keys [12, 23] = `al` for ·oler, ·olet, ·olat (sim 0.533, comfort 498.3)
- strokeFreqSaved 103.2, freqBenefiting 52.3 of 143.9 (share by freq 0.364, by count 0.495), boundary risks 8
- fallbacks: {'keyOverlap': 144, 'markCostTooHigh': 2}
- alternatives: merged [[12, 23]] sim 0.533 saved 103.2; merged [[12, 14, 23]] sim 0.717 saved 95.4; merged [[13, 14, 23]] sim 0.592 saved 5.1

    pistolet: pis/tae/mtie -> paisl
    pistolets: pis/tae/mtie/-s -> paisl/-s
    cambriolé: k@/svRij/ae/mte -> k@/svRaijl
    cambrioler: k@/svRij/ae/mte/-l -> k@/svRaijl/-l
    bricoler: svRi/kae/mte/-l -> svRail/-l
    survoler: s@iR/vae/mte/-l -> s@aiRl/-l
    bénévolat: sve/mRe/vae/mta -> sve/mRael
    déboussolé: pve/sv@e/sae/mte -> pve/sv@ael
    déboussolée: pve/sv@e/sae/mte/-j -> pve/sv@ael/-j
    batifoler: sva/ti/kpae/mte/-l -> sva/tail/-l

## P116 (prefix) -- transOR·

- merged keys [3, 8, 20] = `sR-t` for transOR· (sim 0.625, comfort 497.5)
- strokeFreqSaved 99.3, freqBenefiting 49.6 of 49.8 (share by freq 0.997, by count 0.899), boundary risks 0
- fallbacks: {'keyOverlap': 7}
- alternatives: merged [[3, 8, 20]] sim 0.625 saved 99.3; merged [[3, 8, 11]] sim 0.562 saved 91.3; merged [[3, 8]] sim 0.5 saved 99.3; merged [[3, 20, 21]] sim 0.5 saved 99.5

    transformer: tR@s/kpeR/me/-l -> smRet/-l
    transformé: tR@s/kpeR/me -> smRet
    transporter: tR@s/peR/te/-l -> stRet/-l
    transporté: tR@s/peR/te -> stRet
    transformée: tR@s/kpeR/me/-j -> smRet/-j
    transformés: tR@s/kpeR/me/-s -> smRet/-s
    transportez: tR@s/peR/te/-k -> stRet/-k
    transportait: tR@s/peR/tie -> stRiet
    transportant: tR@s/peR/t@ -> stR@t
    transformez: tR@s/kpeR/me/-k -> smRet/-k

## S129 (suffix) -- bler, blant, ble

- merged keys [14, 16, 17, 23] = `ejsl` for bler, ble (sim 0.872, comfort 545.7)
- merged keys [11, 14, 16, 23] = `@ejl` for blant (sim 0.872, comfort 545.7)
- strokeFreqSaved 98.8, freqBenefiting 98.8 of 151.1 (share by freq 0.654, by count 0.667), boundary risks 0
- fallbacks: {'keyOverlap': 40}
- alternatives: merged [[14, 16, 17, 23], [11, 14, 16, 23]] sim 0.872 saved 98.8; merged [[14, 16, 17, 23], [11, 16, 17, 23]] sim 0.7 saved 98.8; merged [[14, 16, 22, 23], [11, 16, 22, 23]] sim 0.7 saved 98.8; merged [[14, 16, 18, 23], [11, 16, 18, 23]] sim 0.7 saved 98.8; merged [[12, 14, 16, 23], [11, 12, 16, 23]] sim 0.7 saved 76.3

    semblez: s@/svmte/-k -> s@ejsl/-k
    ressembler: R@a/s@/svmte/-l -> R@a/s@ejsl/-l
    probable: pRae/sva/svmt@a -> pRae/svaejsl
    semblé: s@/svmte -> s@ejsl
    ressemblez: R@a/s@/svmte/-k -> R@a/s@ejsl/-k
    rassembler: Ra/s@/svmte/-l -> Ra/s@ejsl/-l
    trembler: tR@/svmte/-l -> tR@ejsl/-l
    sembler: s@/svmte/-l -> s@ejsl/-l
    rassemblez: Ra/s@/svmte/-k -> Ra/s@ejsl/-k
    combler: kai/svmte/-l -> kaiejsl/-l

## P118 (prefix) -- ac

- merged keys [2, 12] = `ka` for ac (sim 0.833, comfort 399.1)
- strokeFreqSaved 97.6, freqBenefiting 97.6 of 97.9 (share by freq 0.997, by count 0.962), boundary risks 19
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[2, 12]] sim 0.833 saved 97.6; merged [[2, 11, 12]] sim 0.667 saved 83.1; merged [[2, 12, 16]] sim 0.667 saved 92.9; merged [[2, 4, 12]] sim 0.667 saved 97.6; merged [[2, 5, 12]] sim 0.667 saved 97.6

    accès: ak/sie -> ksaie
    actrice: ak/tRis -> ktRais
    accent: ak/s@ -> ks@a
    accélère: ak/se/mtieR -> ksae/mtieR
    accéder: ak/se/pve/-l -> ksae/pve/-l
    active: ak/tijs -> ktaijs
    actif: ak/tisd -> ktaisd
    accents: ak/s@/-s -> ks@a/-s
    actifs: ak/tisd/-s -> ktaisd/-s
    accéléré: ak/se/mte/Re -> ksae/mte/Re

## S142 (suffix) -- nie, ni

- merged keys [22] = `-n` for nie, ni (sim 0.667, comfort 365.9)
- strokeFreqSaved 96.6, freqBenefiting 96.6 of 104.8 (share by freq 0.922, by count 0.962), boundary risks 74
- fallbacks: {'illegalChord': 4, 'markCostTooHigh': 4}
- alternatives: merged [[22]] sim 0.667 saved 96.6; merged [[11, 22]] sim 0.5 saved 93.5; merged [[22, 23]] sim 0.5 saved 96.6; merged [[20, 22]] sim 0.5 saved 96.4; merged [[8, 22]] sim 0.5 saved 84.5

    cérémonie: se/Re/mae/mRi -> se/Re/maen
    harmonie: aR/mae/mRi -> aR/maen
    ironie: i/Rae/mRi -> i/Raen
    colonie: kae/mtae/mRi -> kae/mtaen
    pneumonie: pmR@ie/mae/mRi -> pmR@ie/maen
    agonie: a/ksae/mRi -> a/ksaen
    infinie: aie/kpi/mRi/-j -> aie/kpin/-j
    infini: aie/kpi/mRi -> aie/kpin
    infini: aie/kpi/mRi -> aie/kpin
    colonies: kae/mtae/mRi/-s -> kae/mtaen/-s

## S143 (suffix) -- tat, ta

- merged keys [12, 20] = `at` for tat, ta (sim 0.833, comfort 531.1)
- strokeFreqSaved 91.5, freqBenefiting 91.5 of 101.5 (share by freq 0.902, by count 0.545), boundary risks 6
- fallbacks: {'keyOverlap': 29, 'markCostTooHigh': 1}
- alternatives: merged [[12, 20]] sim 0.833 saved 91.5; merged [[20]] sim 0.667 saved 100.5; merged [[12, 20, 21]] sim 0.667 saved 91.2; merged [[12, 20, 22]] sim 0.667 saved 91.7; merged [[12, 18, 20]] sim 0.667 saved 91.6

    résultats: Re/tw@il/ta/-s -> Re/tw@aitl/-s
    résultat: Re/tw@il/ta -> Re/tw@aitl
    attentat: a/t@/ta -> a/t@at
    pesetas: pe/twe/ta/-s -> pe/twaet/-s
    delta: pviel/ta -> pvaietl
    attentats: a/t@/ta/-s -> a/t@at/-s
    habitat: a/svi/ta -> a/svait
    vista: vis/ta -> vaist
    manta: m@/ta -> m@at
    huerta: wieR/ta -> waietR

## P117 (prefix) -- ad

- merged keys [4, 5, 12] = `pva` for ad (sim 0.833, comfort 465.8)
- strokeFreqSaved 88.9, freqBenefiting 88.9 of 99.0 (share by freq 0.898, by count 0.791), boundary risks 0
- fallbacks: {'keyOverlap': 19}
- alternatives: merged [[4, 5, 12]] sim 0.833 saved 88.9; merged [[4, 5]] sim 0.667 saved 89.1; merged [[4, 5, 7]] sim 0.5 saved 89.1; merged [[4, 5, 8]] sim 0.5 saved 89.1; merged [[12, 19]] sim 0.5 saved 91.3

    admettre: ad/mietR -> pvmaietR
    admire: ad/miR -> pvmaiR
    admets: ad/mie/-k -> pvmaie/-k
    admis: ad/mi -> pvmai
    admirer: ad/mi/Re/-l -> pvmai/Re/-l
    admettons: ad/mie/tai -> pvmaie/tai
    admirais: ad/mi/Rie/-k -> pvmai/Rie/-k
    admet: ad/mie -> pvmaie
    admission: ad/mi/sRwai -> pvmai/sRwai
    admirez: ad/mi/Re/-k -> pvmai/Re/-k

## S138 (suffix) -- ·ituer, tuer, tueux

- merged keys [11, 12, 20] = `@at` for ·ituer, tuer, tueux (sim 0.559, comfort 539.7)
- strokeFreqSaved 86.3, freqBenefiting 68.0 of 92.7 (share by freq 0.734, by count 0.376), boundary risks 0
- fallbacks: {'keyOverlap': 128}
- alternatives: merged [[11, 12, 20]] sim 0.559 saved 86.3; merged [[14, 20]] sim 0.539 saved 54.7; merged [[13, 20]] sim 0.5 saved 40.7; merged [[13, 14, 20]] sim 0.592 saved 5.2

    habituer: a/svi/t@ae/-l -> a/sv@ait/-l
    prostituée: pRes/ti/t@ae/-j -> pR@aest/-j
    habitué: a/svi/t@ae -> a/sv@ait
    prostituées: pRes/ti/t@ae/-js -> pR@aest/-js
    habituée: a/svi/t@ae/-j -> a/sv@ait/-j
    affectueux: a/kpiek/t@aie -> a/kp@aiekt
    respectueux: Ries/piek/t@aie -> Ries/p@aiekt
    effectué: ie/kpiek/t@ae -> ie/kp@aiekt
    vertueux: vieR/t@aie -> v@aietR
    effectuer: ie/kpiek/t@ae/-l -> ie/kp@aiekt/-l

## S145 (suffix) -- pa

- merged keys [16, 18] = `-jk` for pa (sim 0.667, comfort 448.2)
- strokeFreqSaved 86.2, freqBenefiting 86.2 of 86.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[16, 18]] sim 0.667 saved 86.2; merged [[11, 16, 18]] sim 0.5 saved 85.5; merged [[2, 16, 18]] sim 0.5 saved 86.2; merged [[16, 18, 20]] sim 0.5 saved 86.2; merged [[16, 18, 19]] sim 0.5 saved 86.2

    sympa: saie/pa -> saiejk
    sympas: saie/pa/-s -> saiejk/-s
    vespa: vies/pa -> viejsk
    prépa: pRe/pa -> pRejk
    pampa: p@/pa -> p@jk
    pampas: p@/pa/-s -> p@jk/-s
    sherpa: pmieR/pa -> pmiejkR
    sherpas: pmieR/pa/-s -> pmiejkR/-s
    kalpa: kal/pa -> kajkl
    vespas: vies/pa/-s -> viejsk/-s

## P110 (prefix) -- sue·, nue·

- merged keys [3, 14, 22] = `sen` for sue·, nue· (sim 0.52, comfort 656.1)
- strokeFreqSaved 82.6, freqBenefiting 41.3 of 70.5 (share by freq 0.586, by count 0.48), boundary risks 0
- fallbacks: {'keyOverlap': 39}
- alternatives: merged [[3, 14, 22]] sim 0.52 saved 82.6; merged [[3, 6, 8]] sim 0.5 saved 34.4

    supérieure: s@i/pe/Rw@R/-j -> sRw@eRn/-j
    supérieur: s@i/pe/Rw@R -> sRw@eRn
    supérieur: s@i/pe/Rw@R -> sRw@eRn
    supérieurs: s@i/pe/Rw@R/-s -> sRw@eRn/-s
    supérieurs: s@i/pe/Rw@R/-s -> sRw@eRn/-s
    supérieures: s@i/pe/Rw@R/-js -> sRw@eRn/-js
    supérieure: s@i/pe/Rw@R/-j -> sRw@eRn/-j
    suprématie: s@i/pRe/ma/si -> smaen/si
    suppléant: s@i/pmte/@ -> s@en
    numération: mR@i/me/Ra/sRwai -> sRaen/sRwai

## S146 (suffix) -- fice, phie

- merged keys [11, 17, 19] = `@sd` for fice, phie (sim 0.635, comfort 515.1)
- strokeFreqSaved 81.3, freqBenefiting 81.3 of 81.3 (share by freq 1.0, by count 1.0), boundary risks 2
- fallbacks: {}
- alternatives: merged [[17, 19]] sim 0.756 saved 81.3; merged [[9, 17, 19]] sim 0.635 saved 71.0; merged [[11, 17, 19]] sim 0.635 saved 81.3; merged [[17, 19, 21]] sim 0.635 saved 81.3; merged [[6, 17, 19]] sim 0.635 saved 71.5

    sacrifice: sa/kRi/kpis -> sa/kR@isd
    philosophie: kpi/mtae/twae/kpi -> kpi/mtae/tw@aesd
    photographie: kpae/tae/ksRa/kpi -> kpae/tae/ksR@asd
    sacrifices: sa/kRi/kpis/-s -> sa/kR@isd/-s
    artifice: aR/ti/kpis -> aR/t@isd
    bénéfices: sve/mRe/kpis/-s -> sve/mR@esd/-s
    bénéfice: sve/mRe/kpis -> sve/mR@esd
    édifice: e/pvi/kpis -> e/pv@isd
    biographie: svRwae/ksRa/kpi -> svRwae/ksR@asd
    géographie: vte/ae/ksRa/kpi -> vte/ae/ksR@asd

## P057 (prefix) -- éu·, enu·

- dedicated keys [2, 5, 11, 14] = `kv@e` for éu·, enu· (sim -0.0, comfort 396.0)
- strokeFreqSaved 80.9, freqBenefiting 80.9 of 280.4 (share by freq 0.289, by count 0.788), boundary risks 0
- fallbacks: {'markCostTooHigh': 69}
- alternatives: dedicated [[2, 5, 11, 14]] sim -0.0 saved 80.9; dedicated [[2, 7, 11, 14]] sim -0.0 saved 80.9; dedicated [[4, 7, 11, 14]] sim -0.0 saved 80.9; dedicated [[4, 5, 8, 11, 14]] sim -0.25 saved 80.9; dedicated [[2, 4, 8, 11, 14]] sim -0.25 saved 80.9

    écoutais: e/k@e/tie/-k -> kv@e/tie/-k
    écoutait: e/k@e/tie -> kv@e/tie
    encourager: @/k@e/Ra/vte/-l -> kv@e/Ra/vte/-l
    écoutera: e/k@e/t@a/Ra -> kv@e/t@a/Ra
    encourage: @/k@e/RaZ -> kv@e/RaZ
    éprouver: e/pR@e/ve/-l -> kv@e/ve/-l
    éprouvé: e/pR@e/ve -> kv@e/ve
    écoutons: e/k@e/tai -> kv@e/tai
    entourage: @/t@e/RaZ -> kv@e/RaZ
    écoutant: e/k@e/t@ -> kv@e/t@

## S147 (suffix) -- ra

- merged keys [12, 21] = `aR` for ra (sim 0.833, comfort 357.4)
- strokeFreqSaved 78.8, freqBenefiting 78.8 of 81.2 (share by freq 0.97, by count 0.5), boundary risks 4
- fallbacks: {'keyOverlap': 24}
- alternatives: merged [[12, 21]] sim 0.833 saved 78.8; merged [[21]] sim 0.667 saved 81.2; merged [[12, 13, 21]] sim 0.667 saved 78.7; merged [[11, 12, 21]] sim 0.667 saved 78.7; merged [[12, 20, 21]] sim 0.667 saved 78.8

    caméra: ka/me/Ra -> ka/maeR
    opéra: ae/pe/Ra -> ae/paeR
    caméras: ka/me/Ra/-s -> ka/maeR/-s
    choléra: kae/mte/Ra -> kae/mtaeR
    opéras: ae/pe/Ra/-s -> ae/paeR/-s
    torera: te/Re/Ra -> te/RaeR
    tempera: t@/pe/Ra -> t@/paeR
    purpura: p@iR/p@i/Ra -> p@iR/p@aiR
    naira: mRie/Ra -> mRaieR
    rémora: Re/me/Ra -> Re/maeR

## S148 (suffix) -- gnol, gnon

- merged keys [9, 14, 23] = `wel` for gnol, gnon (sim 0.585, comfort 481.8)
- strokeFreqSaved 77.1, freqBenefiting 77.1 of 79.7 (share by freq 0.968, by count 0.796), boundary risks 0
- fallbacks: {'keyOverlap': 10}
- alternatives: merged [[20, 22, 23]] sim 0.758 saved 79.7; merged [[9, 14, 23]] sim 0.585 saved 77.1; merged [[14, 20, 22]] sim 0.552 saved 77.7; merged [[9, 23]] sim 0.517 saved 79.1

    espagnol: ies/pa/wel -> ies/pwael
    espagnol: ies/pa/wel -> ies/pwael
    compagnon: kai/pa/wai -> kai/pwael
    compagnons: kai/pa/wai/-s -> kai/pwael/-s
    champignons: pm@/pi/wai/-s -> pm@/pwiel/-s
    espagnole: ies/pa/wel/-j -> ies/pwael/-j
    espagnols: ies/pa/wel/-s -> ies/pwael/-s
    espagnols: ies/pa/wel/-s -> ies/pwael/-s
    champignon: pm@/pi/wai -> pm@/pwiel
    collignon: kae/mti/wai -> kae/mtwiel

## S144 (suffix) -- chir, chi

- merged keys [8, 21, 24, 25] = `R-RZm` for chir (sim 0.775, comfort 728.2)
- merged keys [16, 21, 24, 25] = `-jRZm` for chi (sim 0.775, comfort 728.2)
- strokeFreqSaved 75.6, freqBenefiting 75.6 of 91.7 (share by freq 0.825, by count 0.831), boundary risks 0
- fallbacks: {'keyOverlap': 11}
- alternatives: merged [[8, 21, 24, 25], [16, 21, 24, 25]] sim 0.775 saved 75.6; merged [[8, 21, 24, 25], [8, 16, 24, 25]] sim 0.613 saved 72.7; merged [[13, 21, 24, 25], [13, 16, 24, 25]] sim 0.563 saved 86.8; merged [[4, 6, 8, 21], [4, 6, 16, 21]] sim 0.55 saved 1.4

    réfléchir: Re/kpmte/pmiR -> Re/kpmtReRZm
    réfléchis: Re/kpmte/pmi/-s -> Re/kpmtejRZm/-s
    blanchir: svmt@/pmiR -> svmtR@RZm
    réfléchi: Re/kpmte/pmi -> Re/kpmtejRZm
    chichis: pmi/pmi/-s -> pmijRZm/-s
    affranchis: a/kpR@/pmi/-s -> a/kpR@jRZm/-s
    mariachi: ma/Rwa/pmi -> ma/RwajRZm
    fléchir: kpmte/pmiR -> kpmtReRZm
    chichi: pmi/pmi -> pmijRZm
    affranchi: a/kpR@/pmi -> a/kpR@jRZm

## P087 (prefix) -- déOR·, déER·, éaR·, déaR·

- merged keys [8, 14, 19] = `Red` for déOR·, déER·, éaR·, déaR· (sim 0.627, comfort 472.3)
- strokeFreqSaved 75.5, freqBenefiting 38.5 of 144.6 (share by freq 0.266, by count 0.59), boundary risks 0
- fallbacks: {'keyOverlap': 222, 'markCostTooHigh': 16}
- alternatives: merged [[8, 14, 19]] sim 0.627 saved 75.5; merged [[8, 12, 14]] sim 0.514 saved 61.3

    déterminer: pve/tieR/mi/mRe/-l -> mRied/mRe/-l
    déterminé: pve/tieR/mi/mRe -> mRied/mRe
    élargir: e/mtaR/vtiR -> vtRiedR
    déguerpir: pve/ksieR/piR -> pRiedR
    détermine: pve/tieR/min -> mRiedn
    déterminée: pve/tieR/mi/mRe/-j -> mRied/mRe/-j
    déterminé: pve/tieR/mi/mRe -> mRied/mRe
    dévergondée: pve/vieR/ksai/pve/-j -> ksRaied/pve/-j
    détergent: pve/tieR/vt@ -> vtR@ed
    élargit: e/mtaR/vti/-t -> vtRied/-t

## P101 (prefix) -- phoo·, fo, fau

- merged keys [2, 4, 9] = `kpw-` for phoo·, fo, fau (sim 0.5, comfort 427.4)
- strokeFreqSaved 75.0, freqBenefiting 71.2 of 134.3 (share by freq 0.53, by count 0.34), boundary risks 0
- fallbacks: {'keyOverlap': 92, 'markCostTooHigh': 1}
- alternatives: merged [[2, 4, 8]] sim 0.5 saved 65.4; merged [[2, 4, 5]] sim 0.5 saved 68.6; merged [[2, 4, 9]] sim 0.5 saved 75.0; merged [[2, 4, 11]] sim 0.5 saved 73.1

    folie: kpae/mti -> kpmtwi
    forêts: kpae/Rie/-s -> kpRwie/-s
    folies: kpae/mti/-s -> kpmtwi/-s
    photogénique: kpae/tae/vte/mRik -> kpvtwe/mRik
    foraine: kpae/Rien -> kpRwien
    fautif: kpae/tisd -> kptwisd
    fautive: kpae/tijs -> kptwijs
    faubourgs: kpae/sv@eR/-s -> kspvw@eR/-s
    fauté: kpae/te -> kptwe
    forage: kpae/RaZ -> kpRwaZ

## P123 (prefix) -- communi

- merged keys [6, 8, 18] = `mR-k` for communi (sim 0.556, comfort 467.1)
- strokeFreqSaved 71.0, freqBenefiting 23.7 of 23.7 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[6, 8, 18]] sim 0.556 saved 71.0; merged [[6, 8, 13]] sim 0.5 saved 71.0

    communication: kae/m@i/mRi/ka/sRwai -> kmRak/sRwai
    communications: kae/m@i/mRi/ka/sRwai/-s -> kmRak/sRwai/-s
    communiqué: kae/m@i/mRi/ke -> kmRek
    communiqué: kae/m@i/mRi/ke -> kmRek
    communiqués: kae/m@i/mRi/ke/-s -> kmRek/-s
    communiquant: kae/m@i/mRi/k*@ -> kmR*@k
    communicables: kae/m@i/mRi/kajl/-s -> kmRajkl/-s
    communiquai: kae/m@i/mRi/ke/-t -> kmRek/-t
    communicable: kae/m@i/mRi/kajl -> kmRajkl
    communisant: kae/m@i/mRi/tw@ -> mtRw@k

## P121 (prefix) -- cu

- merged keys [2, 22] = `k-n` for cu (sim 0.5, comfort 546.9)
- strokeFreqSaved 67.6, freqBenefiting 67.6 of 78.8 (share by freq 0.858, by count 0.855), boundary risks 5
- fallbacks: {'keyOverlap': 9}
- alternatives: merged [[2]] sim 0.667 saved 77.9; merged [[2, 4]] sim 0.5 saved 77.1; merged [[2, 3]] sim 0.5 saved 72.2; merged [[2, 22]] sim 0.5 saved 67.6; merged [[2, 23]] sim 0.5 saved 68.6

    curieux: k@i/Rw@ie -> kRw@ien
    culotte: k@i/mtet -> kmtetn
    culot: k@i/mtae -> kmtaen
    culottes: k@i/mtet/-s -> kmtetn/-s
    curieux: k@i/Rw@ie -> kRw@ien
    cubain: k@i/svaie -> ksvaien
    cubains: k@i/svaie/-s -> ksvaien/-s
    culinaire: k@i/mti/mRieR -> kmtin/mRieR
    cubain: k@i/svaie -> ksvaien
    cubains: k@i/svaie/-s -> ksvaien/-s

## P120 (prefix) -- na

- merged keys [6, 8] = `mR-` for na (sim 0.667, comfort 456.3)
- strokeFreqSaved 66.9, freqBenefiting 66.9 of 80.7 (share by freq 0.829, by count 0.887), boundary risks 0
- fallbacks: {'keyOverlap': 13}
- alternatives: merged [[6, 8]] sim 0.667 saved 66.9; merged [[4, 6, 8]] sim 0.5 saved 65.9; merged [[3, 6, 8]] sim 0.5 saved 62.4; merged [[6, 8, 9]] sim 0.5 saved 65.0; merged [[6, 8, 11]] sim 0.5 saved 65.4

    nager: mRa/vte/-l -> vmtRe/-l
    navire: mRa/viR -> vmRiR
    navires: mRa/viR/-s -> vmRiR/-s
    natale: mRa/tal/-j -> mtRal/-j
    naïve: mRa/ijs -> mRijs
    natal: mRa/tal -> mtRal
    naval: mRa/val -> vmRal
    nabot: mRa/svae -> svmRae
    navale: mRa/val/-j -> vmRal/-j
    nagé: mRa/vte -> vmtRe

## S152 (suffix) -- card, pard

- merged keys [18, 21] = `-kR` for card, pard (sim 0.64, comfort 529.1)
- strokeFreqSaved 66.2, freqBenefiting 66.2 of 66.2 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[16, 18, 21]] sim 0.8 saved 66.2; merged [[18, 21]] sim 0.64 saved 66.2; merged [[18, 20, 21]] sim 0.54 saved 66.2; merged [[18, 19, 21]] sim 0.54 saved 66.2; merged [[18, 21, 23]] sim 0.54 saved 66.2

    placard: pmta/kaR -> pmtakR
    salopard: sa/mtae/paR -> sa/mtaekR
    rencard: R@/kaR -> R@kR
    salopards: sa/mtae/paR/-s -> sa/mtaekR/-s
    léopard: mte/ae/paR -> mte/aekR
    rancard: R@/k*aR -> R*@kR
    placards: pmta/kaR/-s -> pmtakR/-s
    brancard: svR@/kaR -> svR@kR
    rencards: R@/kaR/-s -> R@kR/-s
    gaspard: ksas/paR -> ksaskR

## S150 (suffix) -- ·isateur

- merged keys [13, 20, 21] = `itR` for ·isateur (sim 0.5, comfort 321.4)
- strokeFreqSaved 65.0, freqBenefiting 22.0 of 24.9 (share by freq 0.883, by count 0.691), boundary risks 6
- fallbacks: {'keyOverlap': 21}
- alternatives: merged [[11, 20, 21]] sim 0.5 saved 73.4; merged [[13, 20, 21]] sim 0.5 saved 65.0; merged [[12, 20, 21]] sim 0.5 saved 9.6

    réalisateur: Re/a/mti/twa/t@R -> Re/aitR
    réalisateurs: Re/a/mti/twa/t@R/-s -> Re/aitR/-s
    organisateur: eR/ksa/mRi/twa/t@R -> eR/ksaitR
    organisateurs: eR/ksa/mRi/twa/t@R/-s -> eR/ksaitR/-s
    réalisatrice: Re/a/mti/twa/tRis -> Re/aitR/tRis
    organisateur: eR/ksa/mRi/twa/t@R -> eR/ksaitR
    moralisateur: mae/Ra/mti/twa/t@R -> mae/RaitR
    localisateur: mtae/ka/mti/twa/t@R -> mtae/kaitR
    organisatrice: eR/ksa/mRi/twa/tRis -> eR/ksaitR/tRis
    vaporisateur: va/pae/Ri/twa/t@R -> va/paietR

## P122 (prefix) -- cri, cli

- merged keys [2, 21, 23] = `k-Rl` for cri, cli (sim 0.6, comfort 609.4)
- strokeFreqSaved 64.0, freqBenefiting 64.0 of 72.3 (share by freq 0.884, by count 0.556), boundary risks 0
- fallbacks: {'keyOverlap': 40}
- alternatives: merged [[2, 21, 23]] sim 0.6 saved 64.0; merged [[2, 21]] sim 0.517 saved 64.0; merged [[2, 8]] sim 0.633 saved 46.4; merged [[2, 8, 9]] sim 0.533 saved 46.4; merged [[2, 8, 11]] sim 0.533 saved 46.4

    clinique: kmti/mRik -> kmRikRl
    critique: kRi/tik -> ktikRl
    critiques: kRi/tik/-s -> ktikRl/-s
    critique: kRi/tik -> ktikRl
    climat: kmti/ma -> kmaRl
    critiquer: kRi/ti/ke/-l -> ktiRl/ke/-l
    clinique: kmti/mRik -> kmRikRl
    critique: kRi/tik -> ktikRl
    critiques: kRi/tik/-s -> ktikRl/-s
    critiques: kRi/tik/-d -> ktikRl/-d

## S154 (suffix) -- logue, logiste, logie, logiste

- merged keys [18, 19, 23] = `-kdl` for logue, logiste, logie, logiste (sim 0.626, comfort 587.8)
- strokeFreqSaved 60.2, freqBenefiting 54.8 of 54.8 (share by freq 1.0, by count 1.0), boundary risks 0
- fallbacks: {}
- alternatives: merged [[18, 19, 23]] sim 0.626 saved 60.2; merged [[2, 3, 23]] sim 0.512 saved 45.3

    dialogue: pvRwa/mtekd -> pvRwakdl
    psychologue: spi/kae/mtekd -> spi/kaekdl
    catalogue: ka/ta/mtekd -> ka/takdl
    dialogues: pvRwa/mtekd/-s -> pvRwakdl/-s
    monologue: mae/mRae/mtekd -> mae/mRaekdl
    gynécologue: vti/mRe/kae/mtekd -> vti/mRe/kaekdl
    prologue: pRae/mtekd -> pRaekdl
    neurologue: mR@ie/Rae/mtekd -> mR@ie/Raekdl
    archéologue: aR/ke/ae/mtekd -> aR/ke/aekdl
    anthropologue: @/tRae/pae/mtekd -> @/tRae/paekdl

## P124 (prefix) -- bri, ri

- merged keys [8, 9, 16] = `Rw-j` for bri (sim 0.621, comfort 566.0)
- merged keys [2, 8, 16] = `kR-j` for ri (sim 0.621, comfort 566.0)
- strokeFreqSaved 60.0, freqBenefiting 60.0 of 70.0 (share by freq 0.857, by count 0.751), boundary risks 0
- fallbacks: {'keyOverlap': 64}
- alternatives: merged [[8, 9, 13, 16], [2, 8, 13, 16]] sim 0.743 saved 48.6; merged [[8, 9, 16], [2, 8, 16]] sim 0.621 saved 60.0; merged [[8, 9, 16, 17], [2, 8, 16, 17]] sim 0.5 saved 54.6; merged [[6, 8, 9, 16], [2, 6, 8, 16]] sim 0.5 saved 58.6; merged [[8, 13, 16, 21], [9, 13, 16, 21]] sim 0.5 saved 56.8

    brigade: svRi/ksad -> ksRwajd
    briquet: svRi/kie -> kRwiej
    brigades: svRi/ksad/-s -> ksRwajd/-s
    river: Ri/ve/-l -> kvRej/-l
    rival: Ri/val -> kvRajl
    riposte: Ri/pest -> kpRejst
    bricole: svRi/kel -> kRwejl
    bricoles: svRi/kel/-s -> kRwejl/-s
    riposter: Ri/pes/te/-l -> kpRejs/te/-l
    rivaliser: Ri/va/mti/twe/-l -> kvRaj/mti/twe/-l

## S155 (suffix) -- tu

- merged keys [3, 20] = `s-t` for tu (sim 0.5, comfort 496.3)
- strokeFreqSaved 56.1, freqBenefiting 56.1 of 56.1 (share by freq 1.0, by count 0.889), boundary risks 1
- fallbacks: {'keyOverlap': 3}
- alternatives: merged [[12, 20]] sim 0.5 saved 51.7; merged [[3, 20]] sim 0.5 saved 56.1; merged [[6, 20]] sim 0.5 saved 56.1; merged [[18, 20]] sim 0.5 saved 56.1; merged [[20, 22]] sim 0.5 saved 56.1

    foutu: kp@e/t@i -> ksp@et
    vertu: vieR/t@i -> svietR
    foutue: kp@e/t@i/-j -> ksp@et/-j
    vertus: vieR/t@i/-s -> svietR/-s
    foutus: kp@e/t@i/-s -> ksp@et/-s
    foutues: kp@e/t@i/-js -> ksp@et/-js
    pointu: pwaie/t@i -> spwaiet
    pointus: pwaie/t@i/-s -> spwaiet/-s
    pointues: pwaie/t@i/-js -> spwaiet/-js
    tortue: teR/t@i/-j -> stetR/-j

## P127 (prefix) -- cam

- merged keys [2, 11, 13] = `k@i` for cam (sim 0.667, comfort 527.0)
- strokeFreqSaved 55.2, freqBenefiting 55.2 of 63.7 (share by freq 0.866, by count 0.325), boundary risks 0
- fallbacks: {'keyOverlap': 26, 'markCostTooHigh': 1}
- alternatives: merged [[2, 11]] sim 0.833 saved 55.3; merged [[2]] sim 0.667 saved 63.3; merged [[2, 6, 11]] sim 0.667 saved 55.6; merged [[2, 11, 13]] sim 0.667 saved 55.2; merged [[2, 11, 18]] sim 0.667 saved 55.6

    campagne: k@/patn -> kp@aitn
    camper: k@/pe/-l -> kp@ie/-l
    campagnes: k@/patn/-s -> kp@aitn/-s
    campé: k@/pe -> kp@ie
    campos: k@/pae/-s -> kp@aie/-s
    camber: k@/sve -> ksv@ie
    campez: k@/pe/-k -> kp@ie/-k
    campés: k@/pe/-s -> kp@ie/-s
    campée: k@/pe/-j -> kp@ie/-j
    campées: k@/pe/-js -> kp@ie/-js

## P131 (prefix) -- ni

- merged keys [6, 8, 13] = `mRi` for ni (sim 0.833, comfort 456.5)
- strokeFreqSaved 54.8, freqBenefiting 54.8 of 56.1 (share by freq 0.977, by count 0.453), boundary risks 0
- fallbacks: {'keyOverlap': 29}
- alternatives: merged [[6, 8, 13]] sim 0.833 saved 54.8; merged [[6, 8]] sim 0.667 saved 54.8; merged [[13, 22]] sim 0.5 saved 55.5; merged [[4, 6, 8]] sim 0.5 saved 54.8; merged [[3, 6, 8]] sim 0.5 saved 53.2

    niveau: mRi/vae -> vmRaie
    niveaux: mRi/vae/-s -> vmRaie/-s
    niqué: mRi/ke -> kmRie
    nibards: mRi/svaR/-s -> svmRaiR/-s
    nibard: mRi/svaR -> svmRaiR
    niveler: mRi/v@a/mte/-l -> vmR@ai/mte/-l
    nivelant: mRi/v@a/mt@ -> vmR@ai/mt@
    nivelé: mRi/v@a/mte -> vmR@ai/mte
    nivelée: mRi/v@a/mte/-j -> vmR@ai/mte/-j
    nivelées: mRi/v@a/mte/-js -> vmR@ai/mte/-js

## P111 (prefix) -- toi, ti

- merged keys [7, 13, 16] = `tij` for toi, ti (sim 0.687, comfort 464.7)
- strokeFreqSaved 54.5, freqBenefiting 54.5 of 127.0 (share by freq 0.429, by count 0.301), boundary risks 14
- fallbacks: {'keyOverlap': 95}
- alternatives: merged [[7, 9, 13]] sim 0.812 saved 54.5; merged [[7, 9]] sim 0.75 saved 57.7; merged [[7, 13, 16]] sim 0.687 saved 54.5; merged [[5, 7, 9]] sim 0.625 saved 57.7; merged [[7, 9, 11]] sim 0.625 saved 56.3

    tirez: ti/Re/-k -> tRiej/-k
    tirage: ti/RaZ -> tRaijZ
    tirelire: ti/R@a/mtiR -> tR@aij/mtiR
    tirade: ti/Rad -> tRaijd
    tirages: ti/RaZ/-s -> tRaijZ/-s
    timoré: ti/mae/Re -> mtaiej/Re
    tirades: ti/Rad/-s -> tRaijd/-s
    tiraillé: ti/Ra/Rwe -> tRaij/Rwe
    tirai: ti/Re/-t -> tRiej/-t
    timorés: ti/mae/Re/-s -> mtaiej/Re/-s

## P130 (prefix) -- éEk·

- merged keys [2, 5, 14] = `kve` for éEk· (sim 0.5, comfort 580.5)
- strokeFreqSaved 51.9, freqBenefiting 25.9 of 29.5 (share by freq 0.878, by count 0.763), boundary risks 0
- fallbacks: {'keyOverlap': 9}
- alternatives: merged [[2, 14]] sim 0.625 saved 51.9; merged [[2]] sim 0.5 saved 59.1; merged [[2, 6, 14]] sim 0.5 saved 51.7; merged [[2, 4, 14]] sim 0.5 saved 51.9; merged [[2, 5, 14]] sim 0.5 saved 51.9

    électrique: e/mtiek/tRik -> kvtRiek
    électriques: e/mtiek/tRik/-s -> kvtRiek/-s
    effectifs: e/kpiek/tisd/-s -> kvtiesd/-s
    électrons: e/mtiek/tRai/-s -> kvtRaie/-s
    effectif: e/kpiek/tisd -> kvtiesd
    électron: e/mtiek/tRai -> kvtRaie
    éjectable: e/vtiek/tajl -> kvtaejl
    éclectique: e/kmtiek/tik -> kvtiek
    effectif: e/kpiek/tisd -> kvtiesd
    effective: e/kpiek/tijs -> kvtiejs

## P138 (prefix) -- dra

- merged keys [8, 9, 19] = `Rw-d` for dra (sim 0.5, comfort 525.5)
- strokeFreqSaved 50.1, freqBenefiting 50.1 of 50.1 (share by freq 1.0, by count 0.889), boundary risks 0
- fallbacks: {'keyOverlap': 5}
- alternatives: merged [[6, 8, 19]] sim 0.5 saved 50.1; merged [[8, 9, 19]] sim 0.5 saved 50.1; merged [[8, 18, 19]] sim 0.5 saved 50.1; merged [[8, 11, 19]] sim 0.5 saved 49.6; merged [[5, 8, 19]] sim 0.5 saved 50.1

    drapeau: pvRa/pae -> pRwaed
    dragon: pvRa/ksai -> ksRwaid
    draguer: pvRa/kse/-l -> ksRwed/-l
    drapeaux: pvRa/pae/-s -> pRwaed/-s
    dragons: pvRa/ksai/-s -> ksRwaid/-s
    dragué: pvRa/kse -> ksRwed
    draguée: pvRa/kse/-j -> ksRwed/-j
    draguait: pvRa/ksie -> ksRwied
    draguais: pvRa/ksie/-k -> ksRwied/-k
    draguez: pvRa/kse/-k -> ksRwed/-k

## P139 (prefix) -- gué

- merged keys [2, 3, 6] = `ksm-` for gué (sim 0.5, comfort 437.6)
- strokeFreqSaved 46.6, freqBenefiting 46.6 of 46.7 (share by freq 0.999, by count 0.95), boundary risks 0
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[2, 3, 6]] sim 0.5 saved 46.6; merged [[2, 3, 9]] sim 0.5 saved 46.6

    guérir: kse/RiR -> ksmRiR
    guéri: kse/Ri -> ksmRi
    guérie: kse/Ri/-j -> ksmRi/-j
    guérit: kse/Ri/-t -> ksmRi/-t
    guérira: kse/Ri/Ra -> ksmRi/Ra
    guéris: kse/Ri/-k -> ksmRi/-k
    guérisse: kse/Ris/-R -> ksmRis/-R
    guérie: kse/Ri/-j -> ksmRi/-j
    guérissent: kse/Ris/-st -> ksmRis/-st
    guérirai: kse/Ri/Re/-t -> ksmRi/Re/-t

## P115 (prefix) -- li

- merged keys [13, 23] = `il` for li (sim 0.5, comfort 408.4)
- strokeFreqSaved 45.6, freqBenefiting 45.6 of 111.5 (share by freq 0.409, by count 0.467), boundary risks 2
- fallbacks: {'keyOverlap': 62, 'markCostTooHigh': 9, 'illegalChord': 1}
- alternatives: merged [[13, 23]] sim 0.5 saved 45.6; merged [[4, 6, 7]] sim 0.5 saved 44.6; merged [[6, 7, 11]] sim 0.5 saved 44.6; merged [[2, 6, 7]] sim 0.5 saved 41.6

    libéré: mti/sve/Re -> sviel/Re
    limonade: mti/mae/mRad -> maiel/mRad
    lirai: mti/Re/-t -> Riel/-t
    lisant: mti/tw@ -> tw@il
    limace: mti/mas -> maisl
    lilas: mti/mta -> mtail
    liras: mti/Ra/-d -> Rail/-d
    libérés: mti/sve/Re/-s -> sviel/Re/-s
    licorne: mti/keRn -> kieRnl
    libérée: mti/sve/Re/-j -> sviel/Re/-j

## P135 (prefix) -- super

- merged keys [4, 8, 17] = `pR-s` for super (sim 0.625, comfort 533.0)
- strokeFreqSaved 44.8, freqBenefiting 22.4 of 26.3 (share by freq 0.852, by count 0.482), boundary risks 7
- fallbacks: {'keyOverlap': 44}
- alternatives: merged [[3, 4, 8]] sim 0.75 saved 40.2; merged [[4, 8, 17]] sim 0.625 saved 44.8; merged [[4, 8]] sim 0.5 saved 44.8; merged [[3, 4]] sim 0.5 saved 41.4

    supermarché: s@i/pieR/maR/pme -> pmRasR/pme
    superstar: s@i/pieR/staR -> sptRasR
    superviseur: s@i/pieR/vi/tw@R -> pvRis/tw@R
    supermarchés: s@i/pieR/maR/pme/-s -> pmRasR/pme/-s
    superman: s@i/pieR/man -> pmRasn
    supervise: s@i/pieR/vinl -> pvRisnl
    superviser: s@i/pieR/vi/twe/-l -> pvRis/twe/-l
    supervision: s@i/pieR/vi/tRwai -> pvRis/tRwai
    supervisé: s@i/pieR/vi/twe -> pvRis/twe
    supermen: s@i/pieR/mien -> pmRiesn

## P132 (prefix) -- gra, gre

- merged keys [2, 3, 21] = `ks-R` for gra, gre (sim 0.6, comfort 534.2)
- strokeFreqSaved 44.5, freqBenefiting 44.5 of 55.4 (share by freq 0.803, by count 0.813), boundary risks 0
- fallbacks: {'keyOverlap': 21, 'markCostTooHigh': 4}
- alternatives: merged [[2, 3, 21]] sim 0.6 saved 44.5; merged [[8, 18, 19]] sim 0.6 saved 31.1; merged [[2, 3, 8]] sim 0.8 saved 27.1; merged [[8, 11, 12]] sim 0.5 saved 22.7

    grenier: ksR@a/mRwe -> ksmRweR
    gravité: ksRa/vi/te -> ksviR/te
    grenouille: ksR@a/mR@ej -> ksmR@ejR
    gravé: ksRa/ve -> ksveR
    grenouilles: ksR@a/mR@ej/-s -> ksmR@ejR/-s
    graver: ksRa/ve/-l -> ksveR/-l
    gratin: ksRa/taie -> kstaieR
    gredin: ksR@a/pvaie -> kspvaieR
    gravés: ksRa/ve/-s -> ksveR/-s
    gravée: ksRa/ve/-j -> ksveR/-j

## S153 (suffix) -- lat, la

- merged keys [23] = `-l` for lat, la (sim 0.667, comfort 356.1)
- strokeFreqSaved 44.4, freqBenefiting 44.4 of 61.0 (share by freq 0.728, by count 0.957), boundary risks 20
- fallbacks: {'keyOverlap': 2}
- alternatives: merged [[23]] sim 0.667 saved 44.4; merged [[11, 23]] sim 0.5 saved 38.8; merged [[13, 23]] sim 0.5 saved 40.2; merged [[22, 23]] sim 0.5 saved 44.4; merged [[3, 23]] sim 0.5 saved 38.6

    chocolat: pmae/kae/mta -> pmae/kael
    consulat: kai/s@i/mta -> kai/s@il
    chocolats: pmae/kae/mta/-s -> pmae/kael/-s
    chocolat: pmae/kae/mta -> pmae/kael
    mandala: m@/pva/mta -> m@/pval
    bamboula: sv@/sv@e/mta -> sv@/sv@el
    favela: kpa/ve/mta -> kpa/vel
    bénévolat: sve/mRe/vae/mta -> sve/mRe/vael
    marsala: maR/sa/mta -> maR/sal
    favélas: kpa/ve/mta/-s -> kpa/vel/-s

## S156 (suffix) -- go

- merged keys [14, 18, 19] = `ekd` for go (sim 0.5, comfort 484.1)
- strokeFreqSaved 44.0, freqBenefiting 44.0 of 45.9 (share by freq 0.958, by count 0.864), boundary risks 0
- fallbacks: {'keyOverlap': 6}
- alternatives: merged [[18, 19]] sim 0.667 saved 45.9; merged [[6, 18, 19]] sim 0.5 saved 37.4; merged [[14, 18, 19]] sim 0.5 saved 44.0; merged [[9, 18, 19]] sim 0.5 saved 45.9; merged [[11, 18, 19]] sim 0.5 saved 38.1

    frigo: kpRi/ksae -> kpRiekd
    tango: t@/ksae -> t@ekd
    amigo: a/mi/ksae -> a/miekd
    cargo: kaR/ksae -> kaekdR
    amigos: a/mi/ksae/-s -> a/miekd/-s
    tango: t@/ksae -> t@ekd
    pongo: pai/ksae -> paiekd
    cargos: kaR/ksae/-s -> kaekdR/-s
    largo: mtaR/ksae -> mtaekdR
    embargo: @/svaR/ksae -> @/svaekdR

## P137 (prefix) -- do

- merged keys [4, 5, 7] = `pvt-` for do (sim 0.5, comfort 440.1)
- strokeFreqSaved 43.2, freqBenefiting 43.2 of 50.4 (share by freq 0.858, by count 0.603), boundary risks 0
- fallbacks: {'keyOverlap': 29}
- alternatives: merged [[4, 5]] sim 0.667 saved 49.1; merged [[4, 5, 7]] sim 0.5 saved 43.2; merged [[4, 5, 8]] sim 0.5 saved 46.6; merged [[4, 5, 11]] sim 0.5 saved 49.1; merged [[4, 5, 12]] sim 0.5 saved 44.7

    domaine: pvae/mien -> pvmtien
    dominer: pvae/mi/mRe/-l -> pvmti/mRe/-l
    domine: pvae/min -> pvmtin
    domaines: pvae/mien/-s -> pvmtien/-s
    docile: pvae/sil -> spvtil
    dominé: pvae/mi/mRe -> pvmti/mRe
    dominée: pvae/mi/mRe/-j -> pvmti/mRe/-j
    donation: pvae/mRa/sRwai -> pvmtRa/sRwai
    dominos: pvae/mi/mRae/-s -> pvmti/mRae/-s
    dominent: pvae/min/-st -> pvmtin/-st

## P133 (prefix) -- ju

- merged keys [11, 13, 24] = `@iZ` for ju (sim 0.5, comfort 472.7)
- strokeFreqSaved 43.2, freqBenefiting 43.2 of 54.0 (share by freq 0.799, by count 0.346), boundary risks 0
- fallbacks: {'keyOverlap': 68}
- alternatives: merged [[11, 13, 24]] sim 0.5 saved 43.2; merged [[2, 5, 7]] sim 0.5 saved 9.6; merged [[3, 5, 7]] sim 0.5 saved 9.6; merged [[5, 7]] sim 0.667 saved 9.6; merged [[5, 7, 9]] sim 0.5 saved 9.6

    juger: vt@i/vte/-l -> vt@ieZ/-l
    jugé: vt@i/vte -> vt@ieZ
    jurez: vt@i/Re/-k -> R@ieZ/-k
    jugez: vt@i/vte/-k -> vt@ieZ/-k
    jugée: vt@i/vte/-j -> vt@ieZ/-j
    jugés: vt@i/vte/-s -> vt@ieZ/-s
    jugea: vt@i/vta -> vt@aiZ
    juché: vt@i/pme -> pm@ieZ
    jurai: vt@i/Re/-t -> R@ieZ/-t
    jugiez: vt@i/vtRwe -> vtRw@ieZ

## P126 (prefix) -- bi

- merged keys [13, 16] = `ij` for bi (sim 0.5, comfort 419.7)
- strokeFreqSaved 40.9, freqBenefiting 40.9 of 64.7 (share by freq 0.632, by count 0.736), boundary risks 10
- fallbacks: {'keyOverlap': 47}
- alternatives: merged [[3, 5]] sim 0.667 saved 33.9; merged [[13, 16]] sim 0.5 saved 40.9; merged [[3, 5, 17]] sim 0.5 saved 33.7; merged [[3, 5, 16]] sim 0.5 saved 33.9; merged [[3, 5, 8]] sim 0.5 saved 33.4

    bisou: svi/tw@e -> tw@iej
    bijou: svi/vt@e -> vt@iej
    bisous: svi/tw@e/-s -> tw@iej/-s
    bipé: svi/pe -> piej
    bicarbonate: svi/kaR/svae/mRat -> kaijR/svae/mRat
    biper: svi/pe/-l -> piej/-l
    bibelots: svi/sv@a/mtae/-s -> sv@aij/mtae/-s
    bicoque: svi/kek -> kiejk
    bisexuel: svi/se/ks@aiel -> siej/ks@aiel
    bisexuels: svi/se/ks@i/iel/-s -> siej/ks@i/iel/-s

## S158 (suffix) -- lu

- merged keys [22, 23] = `-nl` for lu (sim 0.5, comfort 415.1)
- strokeFreqSaved 40.9, freqBenefiting 40.9 of 40.9 (share by freq 1.0, by count 1.0), boundary risks 2
- fallbacks: {}
- alternatives: merged [[13, 23]] sim 0.5 saved 40.9; merged [[22, 23]] sim 0.5 saved 40.9; merged [[21, 23]] sim 0.5 saved 40.9; merged [[2, 23]] sim 0.5 saved 38.9

    absolu: ajk/sae/mt@i -> ajk/saenl
    absolue: ajk/sae/mt@i/-j -> ajk/saenl/-j
    voulu: v@e/mt@i -> v@enl
    résolue: Re/twae/mt@i/-j -> Re/twaenl/-j
    poilu: pwa/mt@i -> pwanl
    résolu: Re/twae/mt@i -> Re/twaenl
    chevelu: pm@a/v@a/mt@i -> pm@a/v@anl
    révolue: Re/vae/mt@i/-j -> Re/vaenl/-j
    farfelu: kpaR/kp@a/mt@i -> kpaR/kp@anl
    poilus: pwa/mt@i/-s -> pwanl/-s

## P031 (prefix) -- au, o

- merged keys [12, 14] = `ae` for au, o (sim 0.5, comfort 391.9)
- strokeFreqSaved 36.8, freqBenefiting 36.8 of 1155.3 (share by freq 0.032, by count 0.332), boundary risks 20
- fallbacks: {'keyOverlap': 152, 'markCostTooHigh': 7}
- alternatives: merged [[12, 14]] sim 0.5 saved 36.8

    orange: ae/R@Z -> R@aeZ
    obus: ae/sv@i -> sv@aie
    oranges: ae/R@Z/-s -> R@aeZ/-s
    orange: ae/R@Z -> R@aeZ
    olives: ae/mtijs/-s -> mtaiejs/-s
    olive: ae/mtijs -> mtaiejs
    oranger: ae/R@/vte -> R@ae/vte
    omission: ae/mi/sRwai -> maie/sRwai
    orangers: ae/R@/vte/-s -> R@ae/vte/-s
    audit: ae/pvit -> pvaiet

## S157 (suffix) -- con, chon

- merged keys [18, 24, 25] = `-kZm` for con, chon (sim 0.667, comfort 625.0)
- strokeFreqSaved 35.3, freqBenefiting 35.3 of 45.9 (share by freq 0.77, by count 0.964), boundary risks 0
- fallbacks: {'illegalChord': 2}
- alternatives: merged [[18, 24, 25]] sim 0.667 saved 35.3; merged [[4, 6, 18]] sim 0.516 saved 24.9; merged [[12, 13, 18]] sim 0.533 saved 10.9

    bouchon: sv@e/pmai -> sv@ekZm
    flacon: kpmta/kai -> kpmtakZm
    faucon: kpae/kai -> kpaekZm
    torchon: teR/pmai -> tekRZm
    cornichons: keR/mRi/pmai/-s -> keR/mRikZm/-s
    flocons: kpmtae/kai/-s -> kpmtaekZm/-s
    faucons: kpae/kai/-s -> kpaekZm/-s
    bouchons: sv@e/pmai/-s -> sv@ekZm/-s
    cornichon: keR/mRi/pmai -> keR/mRikZm
    capuchon: ka/p@i/pmai -> ka/p@ikZm

## P128 (prefix) -- gui, qui

- merged keys [2, 3, 11] = `ks@` for gui, qui (sim 0.5, comfort 467.6)
- strokeFreqSaved 35.2, freqBenefiting 35.2 of 61.6 (share by freq 0.571, by count 0.617), boundary risks 0
- fallbacks: {'keyOverlap': 18}
- alternatives: merged [[2, 3, 13]] sim 0.833 saved 36.4; merged [[2, 3]] sim 0.667 saved 38.7; merged [[2, 3, 11]] sim 0.5 saved 35.2; merged [[2, 3, 6]] sim 0.5 saved 37.2; merged [[2, 3, 9]] sim 0.5 saved 35.0

    guitare: ksi/taR -> kst@aR
    guider: ksi/pve/-l -> kspv@e/-l
    guidé: ksi/pve -> kspv@e
    guignol: ksi/wel -> ksw@el
    guidée: ksi/pve/-j -> kspv@e/-j
    guidon: ksi/pvai -> kspv@ai
    guidés: ksi/pve/-s -> kspv@e/-s
    guimauve: ksi/maejs -> ksm@aejs
    guignols: ksi/wel/-s -> ksw@el/-s
    guitares: ksi/taR/-s -> kst@aR/-s

## P125 (prefix) -- no

- merged keys [6, 8, 12] = `mRa` for no (sim 0.5, comfort 414.1)
- strokeFreqSaved 33.7, freqBenefiting 33.7 of 66.0 (share by freq 0.511, by count 0.391), boundary risks 0
- fallbacks: {'keyOverlap': 39}
- alternatives: merged [[6, 8]] sim 0.667 saved 35.4; merged [[6, 8, 12]] sim 0.5 saved 33.7; merged [[6, 8, 11]] sim 0.5 saved 35.3; merged [[4, 6, 8]] sim 0.5 saved 35.4; merged [[6, 8, 16]] sim 0.5 saved 34.1

    noté: mRae/te -> mtRae
    notez: mRae/te/-k -> mtRae/-k
    noter: mRae/te/-l -> mtRae/-l
    notaire: mRae/tieR -> mtRaieR
    novice: mRae/vis -> vmRais
    novice: mRae/vis -> vmRais
    novices: mRae/vis/-s -> vmRais/-s
    notice: mRae/tis -> mtRais
    notés: mRae/te/-s -> mtRae/-s
    notée: mRae/te/-j -> mtRae/-j

## P140 (prefix) -- lo

- merged keys [3, 6, 7] = `smt-` for lo (sim 0.5, comfort 489.1)
- strokeFreqSaved 31.0, freqBenefiting 31.0 of 44.4 (share by freq 0.697, by count 0.315), boundary risks 2
- fallbacks: {'keyOverlap': 61}
- alternatives: merged [[6, 7]] sim 0.667 saved 30.4; merged [[4, 6, 7]] sim 0.5 saved 30.4; merged [[3, 6, 7]] sim 0.5 saved 31.0; merged [[6, 7, 11]] sim 0.5 saved 30.9; merged [[6, 7, 9]] sim 0.5 saved 31.0

    locale: mtae/kal/-j -> ksmtal/-j
    local: mtae/kal -> ksmtal
    location: mtae/ka/sRwai -> ksmta/sRwai
    local: mtae/kal -> ksmtal
    locales: mtae/kal/-js -> ksmtal/-js
    locaux: mtae/k*ae -> ksmt*ae
    locaux: mtae/k*ae -> ksmt*ae
    loquet: mtae/kie -> ksmtie
    lopin: mtae/paie -> spmtaie
    locations: mtae/ka/sRwai/-s -> ksmta/sRwai/-s

## P141 (prefix) -- bu

- merged keys [3, 5] = `sv-` for bu (sim 0.667, comfort 339.9)
- strokeFreqSaved 30.2, freqBenefiting 30.2 of 30.4 (share by freq 0.993, by count 0.94), boundary risks 0
- fallbacks: {'keyOverlap': 3}
- alternatives: merged [[3, 5]] sim 0.667 saved 30.2; merged [[3, 5, 9]] sim 0.5 saved 30.1; merged [[3, 5, 11]] sim 0.5 saved 29.0; merged [[2, 3, 5]] sim 0.5 saved 30.0; merged [[3, 5, 8]] sim 0.5 saved 30.2

    buter: sv@i/te/-l -> svte/-l
    buté: sv@i/te -> svte
    butin: sv@i/taie -> svtaie
    butez: sv@i/te/-k -> svte/-k
    buterai: sv@i/t@a/Re/-t -> svt@a/Re/-t
    butée: sv@i/te/-j -> svte/-j
    butés: sv@i/te/-s -> svte/-s
    butor: sv@i/teR -> svteR
    butait: sv@i/tie -> svtie
    butée: sv@i/te/-j -> svte/-j

## S159 (suffix) -- lin

- merged keys [21, 23] = `-Rl` for lin (sim 0.5, comfort 453.0)
- strokeFreqSaved 28.6, freqBenefiting 28.6 of 30.1 (share by freq 0.951, by count 0.857), boundary risks 1
- fallbacks: {'keyOverlap': 7}
- alternatives: merged [[23]] sim 0.667 saved 30.1; merged [[22, 23]] sim 0.5 saved 30.1; merged [[21, 23]] sim 0.5 saved 28.6; merged [[3, 23]] sim 0.5 saved 29.9; merged [[8, 23]] sim 0.5 saved 29.5

    moulin: m@e/mtaie -> m@eRl
    masculin: mas/k@i/mtaie -> mas/k@iRl
    orphelin: eR/kp@a/mtaie -> eR/kp@aRl
    orphelins: eR/kp@a/mtaie/-s -> eR/kp@aRl/-s
    patelin: pa/t@a/mtaie -> pa/t@aRl
    orphelin: eR/kp@a/mtaie -> eR/kp@aRl
    orphelins: eR/kp@a/mtaie/-s -> eR/kp@aRl/-s
    moulins: m@e/mtaie/-s -> m@eRl/-s
    masculin: mas/k@i/mtaie -> mas/k@iRl
    patelin: pa/t@a/mtaie -> pa/t@aRl

## P095 (prefix) -- hu, u

- merged keys [11, 13] = `@i` for hu, u (sim 0.5, comfort 457.0)
- strokeFreqSaved 21.1, freqBenefiting 21.1 of 209.2 (share by freq 0.101, by count 0.507), boundary risks 4
- fallbacks: {'keyOverlap': 36}
- alternatives: merged [[11, 13]] sim 0.5 saved 21.1

    usage: @i/twaZ -> tw@aiZ
    hublot: @i/svmtae -> svmt@aie
    usages: @i/twaZ/-s -> tw@aiZ/-s
    usés: @i/twe/-s -> tw@ie/-s
    hublots: @i/svmtae/-s -> svmt@aie/-s
    usagés: @i/twa/vte/-s -> tw@ai/vte/-s
    usés: @i/twe/-s -> tw@ie/-s
    usagée: @i/twa/vte/-j -> tw@ai/vte/-j
    utopique: @i/tae/pik -> t@aie/pik
    usagées: @i/twa/vte/-js -> tw@ai/vte/-js

## P102 (prefix) -- sou°·, sau°·

- merged keys [3, 12, 14] = `sae` for sou°·, sau°· (sim 0.53, comfort 452.6)
- strokeFreqSaved 9.9, freqBenefiting 5.4 of 87.9 (share by freq 0.062, by count 0.149), boundary risks 0
- fallbacks: {'keyOverlap': 86}
- alternatives: merged [[3, 11, 14]] sim 0.595 saved 22.8; merged [[3, 12, 14]] sim 0.53 saved 9.9

    soutenue: s@e/t@a/mR@i/-j -> smR@aie/-j
    soufflerie: s@e/kpmt@a/Ri -> sRaie
    souvenue: s@e/v@a/mR@i/-j -> smR@aie/-j
    sauterie: sae/t@a/Ri -> sRaie
    soulevant: s@e/mt@a/v@ -> sv@ae
    saugrenue: sae/ksR@a/mR@i/-j -> smR@aie/-j
    soutenant: s@e/t@a/mR@ -> smR@ae
    souvenant: s@e/v@a/mR@ -> smR@ae
    soutenue: s@e/t@a/mR@i/-j -> smR@aie/-j
    sauteries: sae/t@a/Ri/-s -> sRaie/-s

## S139 (suffix) -- o, au

- merged keys [12, 14] = `ae` for o, au (sim 0.5, comfort 503.0)
- strokeFreqSaved 8.5, freqBenefiting 8.5 of 111.7 (share by freq 0.076, by count 0.204), boundary risks 0
- fallbacks: {'keyOverlap': 39}
- alternatives: merged [[12, 14]] sim 0.5 saved 8.5

    proprio: pRae/pRij/ae -> pRae/pRaiej
    trio: tRij/ae -> tRaiej
    brio: svRij/ae -> svRaiej
    gruau: ksR@i/ae -> ksR@aie
    fluo: kpmt@i/ae -> kpmt@aie
    proprios: pRae/pRij/ae/-s -> pRae/pRaiej/-s
    trios: tRij/ae/-s -> tRaiej/-s
    gruaux: ksR@i/ae/-s -> ksR@aie/-s
    frio: kpRij/ae -> kpRaiej
    brios: svRij/ae/-s -> svRaiej/-s

## S108 (suffix) -- nuer, nue, nu

- merged keys [11, 13, 22] = `@in` for nuer, nue, nu (sim 0.663, comfort 489.0)
- strokeFreqSaved 5.4, freqBenefiting 5.4 of 239.3 (share by freq 0.023, by count 0.193), boundary risks 4
- fallbacks: {'keyOverlap': 117}
- alternatives: merged [[11, 13, 22]] sim 0.663 saved 5.4

    atténuer: a/te/mR@ae/-l -> a/t@ien/-l
    ingénu: aie/vte/mR@i -> aie/vt@ien
    ingénue: aie/vte/mR@i/-j -> aie/vt@ien/-j
    charnue: pmaR/mR@i/-j -> pm@aiRn/-j
    exténué: ie/kste/mR@ae -> ie/kst@ien
    charnues: pmaR/mR@i/-js -> pm@aiRn/-js
    ingénues: aie/vte/mR@i/-js -> aie/vt@ien/-js
    exténuée: ie/kste/mR@ae/-j -> ie/kst@ien/-j
    ingénue: aie/vte/mR@i/-j -> aie/vt@ien/-j
    ingénus: aie/vte/mR@i/-s -> aie/vt@ien/-s

## P090 (prefix) -- oe·, au°·

- merged keys [11, 12, 14] = `@ae` for oe·, au°· (sim 0.5, comfort 306.8)
- strokeFreqSaved 4.0, freqBenefiting 2.0 of 117.3 (share by freq 0.017, by count 0.138), boundary risks 1
- fallbacks: {'keyOverlap': 50}
- alternatives: merged [[11, 12, 14]] sim 0.5 saved 4.0

    obéira: ae/sve/i/Ra -> @aie/Ra
    obésité: ae/sve/twi/te -> tw@aie/te
    homélie: ae/me/mti -> mt@aie
    aubépine: ae/sve/pin -> p@aien
    homélies: ae/me/mti/-s -> mt@aie/-s
    aubépines: ae/sve/pin/-s -> p@aien/-s
    obésités: ae/sve/twi/te/-s -> tw@aie/te/-s
    oléine: ae/mte/in -> @aien

## P108 (prefix) -- lai°·, len°·

- merged keys [6, 7, 8, 11] = `mtR@` for lai°· (sim 0.552, comfort 380.7)
- merged keys [6, 7, 9, 11] = `mtw@` for len°· (sim 0.552, comfort 380.7)
- strokeFreqSaved 2.5, freqBenefiting 1.3 of 74.1 (share by freq 0.017, by count 0.258), boundary risks 0
- fallbacks: {'keyOverlap': 21, 'markCostTooHigh': 2}
- alternatives: merged [[6, 7, 8, 11], [6, 7, 9, 11]] sim 0.552 saved 2.5; merged [[6, 7, 8], [6, 7, 11]] sim 0.5 saved 3.1

    lancerai: mt@/s@a/Re/-t -> mtRw@e/-t
    lancerez: mt@/s@a/Re/-d -> mtRw@e/-d
    lanceras: mt@/s@a/Ra/-d -> mtRw@a/-d
    lancerons: mt@/s@a/Rai -> mtRw@ai
    lambrequins: mt@/svR@a/kaie -> kmtw@aie
    langerai: mt@/vt@a/Re/-t -> mtRw@e/-t
    langerez: mt@/vt@a/Re/-d -> mtRw@e/-d
    langeras: mt@/vt@a/Ra/-d -> mtRw@a/-d

## Unbound families

- P005 (prefix) co+col+com+con+cor: upper bound 3629, no positive-gain option
- S013 (suffix) son çon don ton sson ron: upper bound 2551, no positive-gain option
- P017 (prefix) im in fin in: upper bound 2025, no positive-gain option
- S125 (suffix) en: upper bound 167, no positive-gain option
- P001 (prefix) a ha: upper bound 10552, all alternatives conflicted
- S022+S082 (suffix) teur ·ateur ·[di|ma|mma|na|nna|pos|sa|si|ta|tu]teur taire ·itaire: upper bound 1703, all alternatives conflicted
- P019 (prefix) reu· re°· réa· re§· re@· ree·: upper bound 1782, all alternatives conflicted
- S027 (suffix) ·isation ·itation ·ication ·ination ·osition ·@tation: upper bound 1291, all alternatives conflicted
- S035 (suffix) er é: upper bound 1050, all alternatives conflicted
- S033 (suffix) per pper pect pé ·opper pée: upper bound 1082, all alternatives conflicted
- P027 (prefix) ar aOR· aaR· aER· har: upper bound 1307, all alternatives conflicted
- P033 (prefix) aa· caa· paa· raa· baa·: upper bound 1115, all alternatives conflicted
- P013 (prefix) é hé: upper bound 2137, all alternatives conflicted
- P024+P119 (prefix) chan che ché cha char cham: upper bound 1493, all alternatives conflicted
- S068 (suffix) cier cieux rrier rier cié rieux: upper bound 458, all alternatives conflicted
- P063 (prefix) di dia: upper bound 479, all alternatives conflicted
- P058 (prefix) bou bou°·: upper bound 543, all alternatives conflicted
- P018 (prefix) déi· déa· déu· dé@· déo· déE·: upper bound 1864, all alternatives conflicted
- P060 (prefix) ra§· a§·: upper bound 529, all alternatives conflicted
- P043 (prefix) mi imai· méi· mui· moi· mai·: upper bound 810, all alternatives conflicted
- P041 (prefix) éi· ei·: upper bound 833, all alternatives conflicted
- P055 (prefix) préi· rii· rai· réi·: upper bound 588, all alternatives conflicted
- P100 (prefix) vo vau: upper bound 186, all alternatives conflicted
- P099+P136 (prefix) pé emp pan pen emb: upper bound 236, all alternatives conflicted
- P104 (prefix) va: upper bound 164, all alternatives conflicted
- P103 (prefix) ro rou: upper bound 173, all alternatives conflicted
- S134 (suffix) pide pie pier: upper bound 136, all alternatives conflicted
- P114 (prefix) jo: upper bound 112, all alternatives conflicted
- S141 (suffix) ·°lé ·°ver: upper bound 110, all alternatives conflicted
- P113 (prefix) cré cra: upper bound 114, all alternatives conflicted
- P106 (prefix) mo mor: upper bound 160, all alternatives conflicted
- P094 (prefix) héo· théo· eno·: upper bound 213, all alternatives conflicted
- P109 (prefix) par°· por°·: upper bound 147, all alternatives conflicted
- S151 (suffix) ·Eson: upper bound 67, all alternatives conflicted
- P098 (prefix) réy· rey· ru: upper bound 188, all alternatives conflicted
- P076 (prefix) eme· ee· ée·: upper bound 363, all alternatives conflicted
- P129 (prefix) inyl·: upper bound 61, all alternatives conflicted

## Prototype seed families

| seed family | prototype strict freq | bound family | new freqBenefiting | note |
|---|---|---|---|---|
| suffix -ité | 901.4 | unbound | 0 | no family |
| suffix -tion | 589.1 | S005 | 1597.7 | merged binding; benefit share 0.962; fallbacks {'keyOverlap': 72, 'markCostTooHigh': 1} |
| prefix Latin | 367.5 | P002 | 5108.8 | merged binding; benefit share 0.663; fallbacks {'keyOverlap': 2465, 'markCostTooHigh': 123, 'lostDistinction': 48} |
| prefix ex- | 151.3 | P082 | 104.1 | dedicated binding; benefit share 0.457; fallbacks {'noGain': 56} |
| suffix -ment | 127.8 | S001 | 5252.1 | merged binding; benefit share 0.992; fallbacks {'markCostTooHigh': 58, 'keyOverlap': 1, 'illegalChord': 1} |
| suffix -logie | 101.1 | S107 | 94.8 | merged binding; benefit share 0.778; fallbacks {'keyOverlap': 36, 'illegalChord': 3} |
