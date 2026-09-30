#!/bin/env python
# One-off review annotator: records the session's per-set suggestion (active /
# veto / undecided) into the note column of resources/spellingVariants.tsv.
# Statuses stay "review" for every discovered set -- the human gate. When the
# decisions come back, a second pass flips statuses.
import csv

PATH = "resources/spellingVariants.tsv"

# setId -> (suggestion, reason). Discovered sets only.
SUGGEST_ACTIVE = {
    "abatage": "true variant (abattage standard)",
    "abatis": "true variant (abattis standard)",
    "age": "true variant (âge standard; unaccented is English)",
    "arien": "true variant (aryen standard)",
    "babi": "true variant (baby standard loan)",
    "bagoter": "true variant (bagotter standard)",
    "balluchon": "true variant (baluchon standard)",
    "balluchonnage": "true variant",
    "balluchonner": "true variant",
    "barbote": "true variant",
    "baronet": "true variant (baronnet standard; baronet is the English word)",
    "bignole": "true variant (bignole standard)",
    "biture": "true variant (biture standard)",
    "bonard": "true variant (bonnard standard)",
    "boniche": "true variant (bonniche/boniche both attested)",
    "bonir": "true variant (bonnir standard)",
    "bortch": "true variant (bortsch has several accepted spellings)",
    "brifer": "true variant (briffer standard)",
    "brinquebaler": "true variant (brinquebaler standard)",
    "buteur": "true variant (buteur standard)",
    "butoir": "true variant (butoir standard)",
    "canette": "true variant (canette standard)",
    "cari": "true variant (cari/carry/cary curry-family spellings)",
    "cariatide": "true variant (cariatide standard)",
    "chah": "true variant (chah/schah/shah)",
    "chape": "true variant (chape standard)",
    "cheik": "true variant (cheik standard)",
    "chlass": "true variant (schlass standard)",
    "chnoque": "true variant (schnoque standard)",
    "chnouf": "true variant (chnouf standard)",
    "chouia": "true variant (chouia standard)",
    "claper": "true variant (rare dialectal pair)",
    "comandant": "misspelling variant (commandant standard)",
    "conard": "true variant (connard standard)",
    "conasse": "true variant (connasse standard)",
    "crane": "true variant (crâne standard)",
    "dale": "true variant (dalle standard; dale accepted)",
    "diffracter": "true variant (diffracter standard)",
    "disfonctionnement": "misspelling variant (dysfonctionnement standard)",
    "dribbler": "true variant (dribbler standard)",
    "droper": "true variant (dropper standard slang)",
    "espionite": "true variant (espionnite standard)",
    "folingue": "true variant (folingue standard)",
    "frapadingue": "true variant (frapadingue/frappadingue both attested)",
    "fripe": "true variant (fripe/frippe both attested)",
    "frite": "true variant (frite standard; fritte accepted)",
    "gabare": "true variant (gabare/gabarre both attested)",
    "gapette": "true variant (gâpette/gapette both attested)",
    "glavioter": "true variant (glavioter standard)",
    "gnognote": "true variant (gnognotte standard)",
    "gnole": "true variant (gnôle standard)",
    "gratouiller": "true variant (gratouiller standard)",
    "gratouillis": "true variant (gratouillis standard)",
    "griffton": "misspelling variant (both are griffon spellings)",
    "gril": "true variant (gril is the old spelling of grill)",
    "grizzli": "true variant (grizzli/grizzly both accepted)",
    "hachisch": "true variant (haschisch/hachisch/haschich)",
    "harpie": "true variant (harpie standard; harpye archaic)",
    "imbitable": "true variant (imbitable standard)",
    "iodler": "true variant (yodler standard)",
    "jerrican": "true variant (jerrican/jerrycan both accepted)",
    "kipa": "true variant (kippa standard)",
    "kitch": "true variant (kitsch standard)",
    "laper": "true variant (laper/lapper same sense, both attested)",
    "lis": "true variant (lis/lys both accepted)",
    "louloute": "true variant (louloute standard)",
    "loupiote": "true variant (loupiote standard)",
    "maffia": "true variant (mafia standard; maffia accepted)",
    "maffieux": "true variant (mafieux standard)",
    "maffioso": "true variant (mafioso standard)",
    "mammy": "true variant (mamy/mammy both nonstandard of mamie)",
    "maronner": "true variant (marronner standard)",
    "milord": "true variant (milord standard; mylord accepted)",
    "mirmidon": "true variant (myrmidon standard)",
    "molasse": "true variant (molasse standard)",
    "momerie": "true variant (momerie standard)",
    "moudjahiddine": "true variant (moudjahidine standard; several spellings)",
    "moufette": "true variant (mouffette standard)",
    "nirvana": "true variant (nirvana standard)",
    "none": "true variant (nonne standard; none archaic)",
    "nonette": "true variant (nonnette standard)",
    "oie": "true variant (oie standard; oye archaic)",
    "paner": "true variant (paner standard)",
    "papi": "true variant (papy standard)",
    "parlote": "true variant (parlote/parlotte both attested)",
    "pchitt": "true variant (pschitt standard)",
    "piccolo": "true variant (piccolo standard)",
    "pifer": "true variant (piffer standard)",
    "pollope": "true variant (rare slang pair)",
    "pouffiasse": "true variant (pouffiasse standard)",
    "ressurgir": "true variant (resurgir/ressurgir both accepted)",
    "rho": "true variant (rho standard)",
    "roi": "true variant (roi standard; roy archaic)",
    "ruffian": "true variant (ruffian standard)",
    "sadducéen": "true variant (sadducéen standard)",
    "saoul": "true variant (saoul/soul/soûl are all spellings of one word)",
    "saoulard": "true variant (saoulard/soûlard both attested)",
    "saoulerie": "true variant (saoulerie/soûlerie both attested)",
    "sensas": "true variant (sensas/sensass slang)",
    "shrapnel": "true variant (shrapnel standard)",
    "silvaner": "true variant (sylvaner standard)",
    "snif": "true variant (snif/sniff both used)",
    "snifer": "true variant (sniffer standard)",
    "suifer": "true variant (suiffer standard)",
    "tanin": "true variant (tanin standard)",
    "tartufe": "true variant (tartuffe/tartufe both accepted)",
    "tartuferie": "true variant (tartuferie/tartufferie)",
    "tomette": "true variant (tomette standard)",
    "trotskiste": "true variant (trotskiste standard)",
    "vousoyer": "true variant (voussoyer standard)",
    "équarisseur": "true variant (équarrisseur standard)",
}

SUGGEST_VETO = {
    "bailler": "distinct: bailler (archaic, grant) vs bâiller (yawn)",
    "balade": "distinct: balade (outing) vs ballade (poem/song)",
    "bale": "bale is the English word; balle the French one",
    "bi": "distinct: bi- prefix vs by (English)",
    "bite": "distinct: bite vs bitte (mooring bit) vs byte (computing)",
    "biter": "bitter is the English word (beer)",
    "boule": "boulle is a proper noun (marqueterie Boulle)",
    "bute": "bute belongs to buter's paradigm; butte is a distinct noun",
    "buter": "distinct: buter (stumble) vs butter (butter/mound up)",
    "caler": "caller is a Canadianism for 'to call', not a spelling of caler",
    "caner": "distinct: caner (slang, chicken out) vs canner (put in cans)",
    "care": "care is the English word",
    "chasse": "distinct: chasse (hunt) vs châsse (reliquary)",
    "chile": "distinct: chile (chili spelling) vs chyme... chyle (lymph)",
    "cime": "distinct: cime (summit) vs cyme (botany)",
    "colon": "homograph collision: colon (settler) vs côlon (bowel) -- isException class",
    "cote": "distinct: cote (rating) vs cotte (armor/skirt)",
    "date": "distinct: date vs datte (fig)",
    "détoner": "distinct: détoner (detonate) vs détonner (be off-key)",
    "dine": "dyne is a physics unit; dine is a verb form",
    "foret": "distinct: forêt (forest) vs foret (drill bit)",
    "gai": "distinct in modern usage: gai (cheerful) vs gay (homosexual)",
    "gallon": "distinct: gallon (unit) vs galon (braid)",
    "gaule": "gaulle count inflated by the proper noun (De Gaulle)",
    "hale": "three distinct words: halle (market) / hale (haler) / hâle (tan)",
    "haler": "distinct: haler (tow) vs hâler (tan/redden)",
    "lire": "distinct: lire (currency/read) vs lyre (instrument)",
    "lise": "lyse (lysis) is distinct; lise is a verb form",
    "luter": "distinct: lutter (wrestle) vs luter (lute a joint)",
    "mari": "mary is the English name",
    "mater": "distinct: mater (stare down) vs mâter (mast) vs matter",
    "matin": "distinct: matin (morning) vs mâtin (mastiff)",
    "mur": "distinct: mur (wall) vs mûr (ripe)",
    "panné": "distinct: pané (breaded) vs panné (down-and-out)",
    "par": "parr (young salmon) is a distinct word",
    "parti": "party is the English loan",
    "poli": "distinct: poli (polished) vs poly- (prefix)",
    "psi": "distinct: psi (Greek letter) vs psy (psychiatry)",
    "rate": "ratte is a potato variety, a distinct word",
    "rif": "rif (Rif mountains) vs riff (music) are different things",
    "roder": "distinct: rôder (prowl) vs roder (break in an engine)",
    "rot": "distinct: rot (burp) vs rôt (roast)",
    "satire": "distinct: satire vs satyre (satyr)",
    "satirique": "distinct: satirique (satire) vs satyrique (satyr plays)",
    "sur": "distinct: sur (on) vs sûr (sure) -- isException class",
    "tache": "distinct: tache (stain) vs tâche (task)",
    "tacher": "distinct: tacher (stain) vs tâcher (task)",
    "taler": "unclear pair; taler's huge count looks like a proper noun -- leave both",
    "tiper": "tiper is the 'to tip' loan, not a spelling of typer",
    "tome": "distinct: tome (volume) vs tomme (cheese)",
}

SUGGEST_UNDECIDED = {
    "gale": "galle is both the old spelling of gale and a distinct word (burlap); counts muddy",
}

with open(PATH, newline="", encoding="utf-8") as f:
    lines = [line for line in f if not line.startswith("#")]
rows = list(csv.DictReader(lines, delimiter="\t"))
columns = list(rows[0].keys())

covered = set(SUGGEST_ACTIVE) | set(SUGGEST_VETO) | set(SUGGEST_UNDECIDED)
discovered = {row["setId"] for row in rows if row["source"] == "discovered"}
missing = discovered - covered
unknown = covered - discovered
if missing or unknown:
    raise SystemExit(f"missing: {sorted(missing)}\nunknown: {sorted(unknown)}")

for row in rows:
    if row["setId"] in SUGGEST_ACTIVE:
        row["note"] = "suggest ACTIVE -- " + SUGGEST_ACTIVE[row["setId"]]
    elif row["setId"] in SUGGEST_VETO:
        row["note"] = "suggest VETO -- " + SUGGEST_VETO[row["setId"]]
    elif row["setId"] in SUGGEST_UNDECIDED:
        row["note"] = "UNDECIDED -- " + SUGGEST_UNDECIDED[row["setId"]]

with open(PATH, "w", encoding="utf-8") as f:
    f.write("# Variant-spelling sets of the SAME word; ONE canonical spelling "
            "is kept, the others are dropped from the whole\n")
    f.write("# pipeline (src/spellingvariants.py). Canonical = highest "
            "Google Books Ngram 2010-2019 count\n")
    f.write("# (resources/LexiqueGoogleNgram.tsv). status: 'active' = "
            "enforced; 'review' = a human must set it to 'active' (possibly\n")
    f.write("# editing canonical) or 'veto' (genuinely distinct words -- row "
            "kept, nothing enforced).\n")
    f.write("# Discovered rows carry a session suggestion in the note "
            "(suggest ACTIVE / suggest VETO / UNDECIDED).\n")
    writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"Annotated {len(rows)} rows: "
      f"{len(SUGGEST_ACTIVE)} suggest-active, {len(SUGGEST_VETO)} suggest-veto, "
      f"{len(SUGGEST_UNDECIDED)} undecided.")
