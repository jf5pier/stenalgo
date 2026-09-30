# Phase 2 preview: candidate rules, exact-scored (top by proxy score, DESIGN §4.4)

Phase 3 (budgeted selection) and Phase 4 (keypress sharing) are not run here -- these are standalone one-rule-at-a-time evaluations, not a selection.

## prefix root `a` (k=1) -- keys None = `(no legal key found)`

forms: `a`(k=1), `a[che|ge|me|pe|ve]·`(k=2), `a[mu|pu]·`(k=2), `a[ba|bâ|ca|cha|droi|ma|na|pâ|ra|sa|ta|va|voi]·`(k=2)
- score 10526.8, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## suffix root `ment` (k=1) -- keys (20, 23, 25) = `-tlm`

forms: `ment`(k=1), `·[be|ble|bre|ca|che|chi|cie|claffe|cle|cre|cré|cu|cé|de|di|die|dre|du|dé|dû|ffle|ffre|fie|fle|ge|gi|gle|gne|gre|gré|gu|gue|ille|le|li|lle|lu|lé|lû|ma|me|mmé|mé|ne|ni|nie|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|rre|rré|ré|se|ssuie|ssé|sé|ta|te|tie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|é]-{s°,ti}ment`(k=2), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|xa|za|ça]blement`(k=3), `·[ai|bai|chai|chaî|chè|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|miè|mmai|mè|mê|nai|niai|niè|nnai|nnê|plai|plè|prê|què|rai|re|rrai|rè|sai|scè|sei|siè|ssai|ssiè|strai|sè|tai|te|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3)
- score 9139.0, strokeFreqSaved 9189.0, word exceptions 1 (freq 0.0)
- top exceptions: blèsement
    vraiment: vRie/m@ -> vRietlm
    seulement: s@/mt@a/m@ -> s@tlm
    tellement: tie/mt@a/m@ -> tietlm
    exactement: iekdnl/ak/t@a/m@ -> iekdnl/aktlm
    sûrement: s@i/R@a/m@ -> s@itlm
    complètement: kai/pmtie/t@a/m@ -> kaitlm
    doucement: pv@e/s@a/m@ -> pv@e/s@atlm
    absolument: ajk/sae/mt@i/m@ -> ajk/saetlm

## suffix root `·[be|ble|bre|ca|che|chi|cie|claffe|cle|cre|cré|cu|cé|de|di|die|dre|du|dé|dû|ffle|ffre|fie|fle|ge|gi|gle|gne|gre|gré|gu|gue|ille|le|li|lle|lu|lé|lû|ma|me|mmé|mé|ne|ni|nie|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|rre|rré|ré|se|ssuie|ssé|sé|ta|te|tie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|é]-{s°,ti}ment` (k=2) -- keys None = `(no legal key found)`

forms: `·[be|ble|bre|ca|che|chi|cie|claffe|cle|cre|cré|cu|cé|de|di|die|dre|du|dé|dû|ffle|ffre|fie|fle|ge|gi|gle|gne|gre|gré|gu|gue|ille|le|li|lle|lu|lé|lû|ma|me|mmé|mé|ne|ni|nie|nne|nné|noie|nu|nue|né|nû|pe|pie|ple|pli|ppe|pre|que|ra|re|rre|rré|ré|se|ssuie|ssé|sé|ta|te|tie|tre|trie|tru|tte|té|ve|voue|vre|vé|xcré|xe|xtre|é]-{s°,ti}ment`(k=2), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|voua|xa|za|ça]blement`(k=3), `·[ai|chai|chaî|chè|ciè|crè|cè|dai|diai|die|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|miè|mmai|mè|mê|nai|niai|niè|nnai|nnê|piè|plai|plè|prê|que|què|rai|rrai|rè|sai|scè|sei|siè|ssai|ssiè|strai|sè|tai|te|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3), `·[bi|bli|bri|chi|ci|cri|di|fi|gi|gui|illi|li|mi|ni|nni|ny|phi|pi|qui|ri|rri|sci|si|ssi|sti|thi|ti|tri|tti|vi|xi|y|ï]caments`(k=3)
- score 7794.0, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## suffix root `·[be|ble|bre|ce|che|cle|cre|de|dre|ffle|ffre|fle|ge|gle|gne|gre|gue|ille|le|lle|me|ne|nne|pe|ple|ppe|pre|que|re|rre|sce|se|sse|te|tre|tte|ve|vre|xe|xtre]ment` (k=2) -- keys None = `(no legal key found)`

forms: `·[be|ble|bre|ce|che|cle|cre|de|dre|ffle|ffre|fle|ge|gle|gne|gre|gue|ille|le|lle|me|ne|nne|pe|ple|ppe|pre|que|re|rre|sce|se|sse|te|tre|tte|ve|vre|xe|xtre]ment`(k=2), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|xa|za|ça]blement`(k=3), `·[ai|bai|chai|chaî|chè|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|miè|mmai|mè|mê|nai|niai|niè|nnai|nnê|plai|plè|prê|què|rai|re|rrai|rè|sai|scè|sei|siè|ssai|ssiè|strai|sè|tai|te|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3), `·[bi|bli|bri|chi|ci|cri|di|dri|fi|gi|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|qui|ri|rri|sci|si|ssi|thi|ti|tri|tti|vi|vri|xi|y|ï]lement`(k=3)
- score 7431.8, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## suffix root `·°ment` (k=2) -- keys None = `(no legal key found)`

forms: `·°ment`(k=2), `·[ai|bai|chai|chaî|chè|cie|ciè|crè|cè|dai|diai|die|dre|dè|e|fai|fè|gai|gè|ille|lai|lei|liè|llè|lè|mai|me|miè|mmai|mè|mê|nai|ne|niai|niè|nnai|nne|nnê|plai|plè|prê|què|rai|re|rei|rie|rrai|rè|sai|scè|se|sei|siè|ssai|ssiè|strai|sè|tai|te|tie|tè|vai|ve|vei|vè|vé|vê|xiè|xtrê|è]-{tR,tj}tement`(k=3), `·[a|ba|bla|bra|bâ|ca|cca|cha|cia|da|dia|droi|ga|geoi|gna|gra|la|loi|lâ|ma|mma|na|nia|niâ|nna|noi|noî|pa|pha|pla|qua|quoi|ra|ria|roi|rra|sa|soi|ssa|ssoi|ta|tia|toi|tra|tta|va|via|xa|za|ça]blement`(k=3), `·[bi|bli|bri|chi|ci|cri|di|dri|fi|gi|gri|gui|i|illi|li|lli|mi|ni|nni|noui|ny|phi|pi|pli|qui|ri|rri|sci|si|ssi|thi|ti|tri|tti|vi|vri|xi|y|ï]lement`(k=3)
- score 7231.8, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## prefix root `re` (k=1) -- keys (8, 16) = `R-j`

forms: `re`(k=1), `re[char|gar|mar|par|tar]·`(k=2), `re[bro|chau|co|do|fau|lo|mo|no|po|pro|vau|vo]·`(k=2), `re[bou|brou|cou|dou|fou|grou|joue|loo|loue|mou|nou|pou|tou|trou|vou]·`(k=2)
- score 5027.4, strokeFreqSaved 5927.0, word exceptions 844 (freq 869.6)
- top exceptions: reviens, revient, retrouve, retraite, reprendre, reviendra, reviendrai, représente, reprends, repris
    regarde: R@a/ksadR -> ksRajdR
    revoir: R@a/vwaR -> vRwajR
    regardez: R@a/ksaR/pve/-k -> pvRej/-k
    regarder: R@a/ksaR/pve/-l -> pvRej/-l
    retour: R@a/t@eR -> tR@ejR
    retard: R@a/taR -> tRajR
    revenir: R@a/v@a/mRiR -> vR@aj/mRiR

## prefix root `de` (k=1) -- keys (4, 5, 25) = `pv-m`

forms: `de`(k=1), `de[ba|man|ve|vi|vien|vri]·`(k=2)
- score 38.8, strokeFreqSaved 2205.0, word exceptions 56 (freq 2156.1)
- top exceptions: depuis, devrais, devrait, devez, depuis, devons, devait, debout, devais, dedans
    demain: pv@a/maie -> pvmaiem
    demande: pv@a/m@d -> pvm@dm
    demandé: pv@a/m@/pve -> pv-m/pve
    demander: pv@a/m@/pve/-l -> pv-m/pve/-l

## suffix root `tion` (k=1) -- keys (16, 17, 20) = `-jst`

forms: `tion`(k=1), `·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tion`(k=2), `·[sten|ten|tten|ven]tion`(k=2), `·[bi|ci|ddi|di|gni|li|mi|ni|ri|si|sti|ti|tri]tion`(k=2)
- score 4266.6, strokeFreqSaved 4370.5, word exceptions 36 (freq 73.9)
- top exceptions: réception, exception, description, corruption, adoption, conception, éruption, perception, rédemption, interruption
    attention: a/t@/sRwai -> ajst
    attention: a/t@/sRwai -> ajst
    situation: si/t@a/sRwai -> si/t@ajst
    solution: sae/mt@i/sRwai -> sae/mt@ijst
    position: pae/twi/sRwai -> paejst
    opération: ae/pe/Ra/sRwai -> ae/pejst
    relation: R@a/mta/sRwai -> R@ajst
    direction: pvi/Riek/sRwai -> pvi/Riejskt

## prefix root `en` (k=1) -- keys None = `(no legal key found)`

forms: `en`(k=1), `en[a|ca|châ|cloî|dia|fa|fla|foi|ga|gra|joi|la|ra|sa|ta|toi|tra|va]·`(k=2), `en[che|ge|gre|le|re|se]·`(k=2), `en[cen|chan|clen|gen|glan|gran|jam|san|vian]-{t}·`(k=2)
- score 4648.4, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## prefix root `co+col+com+con+cor` (k=1) -- keys (2, 16) = `k-j`

forms: `co+col+com+con+cor`(k=1), `co[bi|ci|di|fi|fie|gi|li|mi|ni|pi|pie|pli|pri|si|ti|tri]·`(k=2), `con[co|do|lo|o|plo|po|pro|so|to|trô|vo]·`(k=2), `com[che|de|ge|pre|que|re|se|ve]-{t}·`(k=2)
- score 2506.5, strokeFreqSaved 3165.2, word exceptions 518 (freq 623.7)
- top exceptions: confiance, comprenez, conduit, contrôler, concours, comité, congrès, conseille, confier, confié
    combien: kai/svRwaie -> ksvRwaiej
    comprends: kai/pR@/-k -> kpR@j/-k
    compris: kai/pRi -> kpRij
    comprendre: kai/pR@dR -> kpR@jdR
    content: kai/t@ -> kt@j
    compris: kai/pRi -> kpRij

## prefix root `dé` (k=1) -- keys (4, 5, 18) = `pv-k`

forms: `dé`(k=1), `dé[bou|brou|clou|cloue|cou|dou|fou|gou|goû|joue|mou|noue|pou|rou|trou|voue]·`(k=2), `dé[ba|bap|bla|boî|bra|bâ|ca|cla|coi|doua|dra|fa|fla|ga|gra|la|ma|na|pha|pla|plâ|qua|ra|sa|ta|tra|va|voi|voie]-{p}·`(k=2), `dé[bi|bri|brie|chi|ci|cli|cri|fi|fie|fri|gi|gri|gui|li|lie|mi|my|ni|pi|plie|pri|qui|ri|si|tri|vi]·`(k=2)
- score 831.7, strokeFreqSaved 2094.1, word exceptions 2128 (freq 1227.4)
- top exceptions: début, départ, dépêche, déjeuner, dépend, défendre, dépêchez, déjeuner, débile, dépose
    désolé: pve/twae/mte -> pvtwaek/mte
    désolé: pve/twae/mte -> pvtwaek/mte
    désolée: pve/twae/mte/-j -> pvtwaek/mte/-j
    déteste: pve/tiest -> pvtieskt
    dérange: pve/R@Z -> pvR@kZ
    dégage: pve/ksaZ -> kspvakZ

## suffix root `té` (k=1) -- keys (16, 18, 20) = `-jkt`

forms: `té`(k=1), `·[a|ba|bi|ca|cia|da|dua|dé|ga|gi|gra|ma|na|nna|qui|ra|ri|ria|sa|sua|ta|ti|tia|tra|tua|va|vi|via|xua]-{mi}lité`(k=3), `·rité`(k=2), `·[cu|da|ga|jo|la|lia|no|o|pa|rio|shé|ta|to|té]rité`(k=3)
- score 3177.2, strokeFreqSaved 3255.6, word exceptions 81 (freq 43.4)
- top exceptions: honnêteté, égalité, excepté, sainteté, volupté, respecté, infecté, infectés, respectée, lactée
    vérité: ve/Ri/te -> vejkt
    sécurité: se/k@i/Ri/te -> sejkt
    santé: s@/te -> s@jkt
    liberté: mti/svieR/te -> mti/sviejktR
    société: sae/sRwe/te -> sae/sRwejkt
    beauté: svae/te -> svaejkt
    réalité: Re/a/mti/te -> Rejkt
    volonté: vae/mtai/te -> vae/mtaijkt

## suffix root `·ation` (k=2) -- keys (16, 17, 20) = `-jst`

forms: `·ation`(k=2), `·[con|li|lli|llu|man|mi|ti|tio]citations`(k=4), `·[bé|cré|cé|dé|fé|gré|gé|llé|lé|mé|né|pré|pé|rré|scé|sé|té|vé|é]ration`(k=3), `·[bu|ccu|cu|du|fu|gu|ju|lu|mu|nhu|nu|ppu|pu|su|tru|tu|u|xsu]tation`(k=3)
- score 2999.2, strokeFreqSaved 3029.2, word exceptions 0 (freq 0.0)
    félicitations: kpe/mti/si/ta/sRwai/-s -> kpejst/-s
    opération: ae/pe/Ra/sRwai -> aejst
    informations: aie/kpeR/ma/sRwai/-s -> aie/kpejstR/-s
    conversation: kai/vieR/sa/sRwai -> kai/viejstR
    imagination: i/ma/vti/mRa/sRwai -> i/ma/vtijst
    explication: ie/kspmti/ka/sRwai -> ie/kspmtijst
    information: aie/kpeR/ma/sRwai -> aie/kpejstR
    réputation: Re/p@i/ta/sRwai -> Rejst

## suffix root `·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tion` (k=2) -- keys (16, 17, 18) = `-jsk`

forms: `·[a|ba|bra|ca|cia|cra|da|dia|fla|ga|gna|gra|la|lia|lla|ma|mma|na|pa|pla|qua|ra|ria|rra|sa|sla|ssa|ta|tia|tra|tta|va|via|xa|xpia]tion`(k=2), `·[bi|bli|bri|chi|di|fi|gi|i|li|mi|mmi|pi|pli|ppli|qui|ri|si|ti|tri|vi|xi|xpli]-{n,s}nation`(k=3), `·[bé|cré|dé|fé|gré|gé|lé|mé|né|pré|pé|rré|té|vé|é]ration`(k=3), `·[bu|ccu|cu|du|gu|ju|lu|mu|nhu|nu|ppu|pu|tu|xsu]cation`(k=3)
- score 2198.7, strokeFreqSaved 2379.7, word exceptions 27 (freq 141.0)
- top exceptions: opération, éducation, accusation, opérations, accusations, obligation, aviation, occupation, obligations, agitation
    relation: R@a/mta/sRwai -> R@ajsk
    informations: aie/kpeR/ma/sRwai/-s -> aie/kpejskR/-s
    imagination: i/ma/vti/mRa/sRwai -> i/majsk
    explication: ie/kspmti/ka/sRwai -> iejsk
    information: aie/kpeR/ma/sRwai -> aie/kpejskR
    organisation: eR/ksa/mRi/twa/sRwai -> eR/ksa/mRijsk

## suffix root `·ité` (k=2) -- keys None = `(no legal key found)`

forms: `·ité`(k=2), `·[bi|bli|bri|di|ffi|fi|gi|gui|li|lli|ni|pi|pli|qui|ri|si|ti|tri|vi|xi|xpli|ï]-{m,s}lité`(k=3), `·[a|ba|bra|ca|cia|da|dia|ga|gia|gna|gra|la|le|lia|lla|ma|na|nha|nia|nna|pa|pla|ra|ria|sa|ssa|ta|tia|tra|va|via]lité`(k=3), `·[cu|du|lu|mmu|pu|scu|ssu|tu]rité`(k=3)
- score 2581.0, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## suffix root `ger` (k=1) -- keys (20, 24, 25) = `-tZm`

forms: `ger`(k=1), `·[a|bra|cca|fra|ga|la|ma|mma|na|pa|ra|rra|sa|ssa|ta|tra|va]ger`(k=2), `·[dan|gran|lan|llen|man|ran|rran|tran]-{S}ger`(k=2), `·[bli|di|ffli|fi|fli|gli|i|mi|ri|rri|si|ti]gé`(k=2)
- score 1631.3, strokeFreqSaved 1892.3, word exceptions 47 (freq 226.0)
- top exceptions: obligé, déranger, dégagez, venger, ranger, obligée, messager, obligés, dégager, dérangé
    manger: m@/vte/-l -> m@tZm/-l
    changer: pm@/vte/-l -> pm@tZm/-l
    changé: pm@/vte -> pm@tZm
    danger: pv@/vte -> pv@tZm
    protéger: pRae/te/vte/-l -> pRae/tetZm/-l
    mangé: m@/vte -> m@tZm
    arranger: a/R@/vte/-l -> atZm/-l
    bouger: sv@e/vte/-l -> sv@etZm/-l

## suffix root `·°nant` (k=2) -- keys (5, 20, 22) = `v-tn`

forms: `·°nant`(k=2)
- score 2241.1, strokeFreqSaved 2241.1, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> vmaietn
    lieutenant: mtRw@ie/t@a/mR@ -> vmtRw@ietn
    surprenant: s@iR/pR@a/mR@ -> sv@itRn
    surprenante: s@iR/pR@a/mR@t -> sv@itRn/mR@t
    inconvenant: aie/kai/v@a/mR@ -> aie/kvaitn
    lieutenants: mtRw@ie/t@a/mR@/-s -> vmtRw@ietn/-s
    prévenant: pRie/v@a/mR@ -> pvRietn
    contenant: kai/t@a/mR@ -> kvaitn

## prefix root `é` (k=1) -- keys None = `(no legal key found)`

forms: `é`(k=1), `é[bou|brou|cou|crou|gou|mou|pou|prou|tou]·`(k=2), `é[chau|clo|co|lo|mo|ro|to|vo]·`(k=2), `é[bran|chan|den|lan|tan|ten|ven]·`(k=2)
- score 2221.6, strokeFreqSaved 0.0, word exceptions 0 (freq 0.0)

## suffix root `tenant` (k=2) -- keys (20, 22) = `-tn`

forms: `tenant`(k=2)
- score 2220.8, strokeFreqSaved 2220.8, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> maietn
    lieutenant: mtRw@ie/t@a/mR@ -> mtRw@ietn
    lieutenants: mtRw@ie/t@a/mR@/-s -> mtRw@ietn/-s
    contenant: kai/t@a/mR@ -> kaitn
    contenants: kai/t@a/mR@/-s -> kaitn/-s
    appartenant: a/paR/t@a/mR@ -> a/patRn
    soutenant: s@e/t@a/mR@ -> s@etn
    appartenante: a/paR/t@a/mR@t -> a/patRn/mR@t

## prefix root `pour` (k=1) -- keys (4, 8, 18) = `pR-k`

forms: `pour`(k=1)
- score 2203.7, strokeFreqSaved 2209.4, word exceptions 68 (freq 5.7)
- top exceptions: pourchassé, pourchasser, pourchasse, pourpoint, pourchassent, pourchassez, pourchassée, pourchassés, pourchassera, pourfendeur
    pourquoi: p@eR/kwa -> kpRwak
    pourquoi: p@eR/kwa -> kpRwak
    pourtant: p@eR/t@ -> ptR@k
    pourvu: p@eR/v@i -> pvR@ik
    poursuivre: p@eR/s@aijsR -> spR@aijskR
    poursuit: p@eR/s@ai -> spR@aik
    poursuite: p@eR/s@ait -> spR@aikt
    poursuivi: p@eR/s@ai/vi -> spR@aik/vi

## prefix root `sa` (k=1) -- keys (3, 20, 23) = `s-tl`

forms: `sa`(k=1), `sa[bor|bou|cré|la|le|li|lo|pris|ta|ti|to|va]-{bo,kRis}·`(k=2)
- score 2161.6, strokeFreqSaved 2194.0, word exceptions 34 (freq 12.3)
- top exceptions: sabots, sacoche, saboté, sabot, salés, sacoches, sabote, sagouin, sablés, sablé
    savoir: sa/vwaR -> svwatRl
    savez: sa/ve -> svetl
    salut: sa/mt@i -> smt@itl
    savais: sa/vie/-k -> svietl/-k
    salut: sa/mt@i -> smt@itl
    savait: sa/vie -> svietl
    salaud: sa/mtae -> smtaetl
    salope: sa/mtejk -> smtejktl

## suffix root `·[bi|ca|cer|ci|di|gi|li|mi|pre|qui|sci|si|sso|te|ter|ti|to|traî|tti|ve|ver]nant` (k=2) -- keys (18, 20, 22) = `-ktn`

forms: `·[bi|ca|cer|ci|di|gi|li|mi|pre|qui|sci|si|sso|te|ter|ti|to|traî|tti|ve|ver]nant`(k=2)
- score 2136.4, strokeFreqSaved 2136.4, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> maiektn
    concernant: kai/sieR/mR@ -> kaiktn
    fascinant: kpa/si/mR@ -> kpaktn
    surprenant: s@iR/pR@a/mR@ -> s@iktRn
    dominant: pvae/mi/mR@ -> pvaektn
    hallucinant: a/mt@i/si/mR@ -> a/mt@iktn
    inconvenant: aie/kai/v@a/mR@ -> aie/kaiktn
    revenants: R@a/v@a/mR@/-s -> R@aktn/-s

## suffix root `nant` (k=1) -- keys (16, 20, 22) = `-jtn`

forms: `nant`(k=1), `·[bi|ca|cer|ci|di|gi|li|mi|pre|qui|sci|si|sso|te|ter|ti|to|traî|tti|ve|ver]nant`(k=2)
- score 2132.9, strokeFreqSaved 2142.9, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> maiejtn
    concernant: kai/sieR/mR@ -> kaijtn
    fascinant: kpa/si/mR@ -> kpajtn
    surprenant: s@iR/pR@a/mR@ -> s@ijtRn
    tournant: t@eR/mR@ -> t@ejtRn
    dominant: pvae/mi/mR@ -> pvaejtn
    hallucinant: a/mt@i/si/mR@ -> a/mt@ijtn
    inconvenant: aie/kai/v@a/mR@ -> aie/kaijtn

## suffix root `·[pre|te|ve]nant` (k=2) -- keys (5, 20, 22) = `v-tn`

forms: `·[pre|te|ve]nant`(k=2)
- score 2080.7, strokeFreqSaved 2080.7, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> vmaietn
    surprenant: s@iR/pR@a/mR@ -> sv@itRn
    inconvenant: aie/kai/v@a/mR@ -> aie/kvaitn
    revenants: R@a/v@a/mR@/-s -> vR@atn/-s
    revenant: R@a/v@a/mR@ -> vR@atn
    prévenant: pRie/v@a/mR@ -> pvRietn
    avenant: a/v@a/mR@ -> vatn
    contenant: kai/t@a/mR@ -> kvaitn

## suffix root `·tenant` (k=2) -- keys (20, 22) = `-tn`

forms: `·tenant`(k=2)
- score 2058.9, strokeFreqSaved 2058.9, word exceptions 0 (freq 0.0)
    maintenant: maie/t@a/mR@ -> maietn
    contenant: kai/t@a/mR@ -> kaitn
    attenant: a/t@a/mR@ -> atn
    contenants: kai/t@a/mR@/-s -> kaitn/-s
    appartenant: a/paR/t@a/mR@ -> a/patRn
    soutenant: s@e/t@a/mR@ -> s@etn

## prefix root `ré` (k=1) -- keys (8, 23) = `R-l`

forms: `ré`(k=1), `réa[bo|che|gi|jus|li|mé|ni|per|ra]·`(k=3), `ré[cré|crée|e|flé|fé|gé|pre|pé|vei|vé|é]·`(k=2), `ré[com|con|pon]·`(k=2)
- score 1715.4, strokeFreqSaved 1864.9, word exceptions 204 (freq 119.5)
- top exceptions: réalité, réelle, récolte, révolte, révèle, régale, récolte, récré, régal, récoltes
    réponds: Re/pai/-k -> pRail/-k
    réveille: Re/v*iej -> vR*iejl
    répondre: Re/paidR -> pRaidRl
    réunion: Re/@i/mRwai -> R@il/mRwai
    réfléchir: Re/kpmte/pmiR -> pmRiRl
    répète: Re/piet -> pRietl
    réparer: Re/pa/Re/-l -> pRal/Re/-l

## prefix root `pou` (k=1) -- keys (4, 16) = `p-j`

forms: `pou`(k=1)
- score 1974.4, strokeFreqSaved 1975.5, word exceptions 12 (freq 1.1)
- top exceptions: poulie, poulies, pouding, poupoule, poudrage, poupoules, poudingue, poudingues, poupin, poupins
    pouvez: p@e/ve -> pvej
    pourrait: p@e/Rie -> pRiej
    pourrais: p@e/Rie/-k -> pRiej/-k
    pouvoir: p@e/vwaR -> pvwajR
    pouvais: p@e/vie/-k -> pviej/-k
    pouvait: p@e/vie -> pviej
    pouvoir: p@e/vwaR -> pvwajR
    pourra: p@e/Ra -> pRaj

## prefix root `par` (k=1) -- keys (8, 16, 18) = `R-jk`

forms: `par`(k=1)
- score 1969.0, strokeFreqSaved 1997.3, word exceptions 27 (freq 28.3)
- top exceptions: partant, partiez, partant, parvient, partions, parviens, parviennent, parviendra, parvienne, partants
    partir: paR/tiR -> tRijkR
    pardon: paR/pvai -> pvRaijk
    parti: paR/t*i -> tR*ijk
    parfois: paR/kpwa -> kpRwajk
    partout: paR/t@e -> tR@ejk
    parlez: paR/mte/-k -> mtRejk/-k
    partie: paR/ti/-j -> tRijk/-j
    partez: paR/te -> tRejk

## prefix root `de[ba|man|ve|vi|vien|vri]·` (k=2) -- keys (4, 5, 25) = `pv-m`

forms: `de[ba|man|ve|vi|vien|vri]·`(k=2)
- score 1287.5, strokeFreqSaved 1287.5, word exceptions 0 (freq 0.0)
    demandé: pv@a/m@/pve -> pv-m/pve
    demander: pv@a/m@/pve/-l -> pv-m/pve/-l
    devenir: pv@a/v@a/mRiR -> pvmRiRm
    devenu: pv@a/v@a/mR@i -> pvmR@im
    demandez: pv@a/m@/pve/-k -> pv-m/pve/-k
    demandais: pv@a/m@/pvie/-k -> pv-m/pvie/-k
    devenue: pv@a/v@a/mR@i/-j -> pvmR@im/-j
    devrions: pv@a/vRij/ai -> pvaim

## prefix root `ai·` (k=2) -- keys (8, 13, 16) = `Rij`

forms: `ai·`(k=2)
- score 1576.9, strokeFreqSaved 1660.4, word exceptions 109 (freq 83.5)
- top exceptions: habiter, habitait, habitez, abîmer, habité, abîmé, habitais, agiter, animés, abriter
    arrivé: a/Ri/v*e -> vR*iej
    arriver: a/Ri/ve/-l -> vRiej/-l
    arrivera: a/Ri/v@a/Ra -> vR@aij/Ra
    animaux: a/mRi/mae -> mRaiej
    arrivée: a/Ri/ve/-j -> vRiej/-j
    animal: a/mRi/mal -> mRaijl
    arrivés: a/Ri/ve/-s -> vRiej/-s
    arrivait: a/Ri/vie -> Rij/vie

