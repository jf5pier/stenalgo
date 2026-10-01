"""Split by: doubled-e in the FIRST syllable (prefix) vs a later one (root)."""
import sys, csv
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)

def doubledPositions(g):
    units, boundaries = vp._unitsAndBoundaries(g.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(g.rawOrthosyllCV)
    if len(units) != len(ortho): return []
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    out = []
    for pos, n in enumerate(nuclei):
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries): continue
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        if nxt and len(nxt) == 2 and nxt[0] == nxt[1] and nxt[0].isalpha() and nxt[0] not in "aeiouy":
            firstSyllable = not any(b <= n for b in boundaries)
            out.append((n, ortho[n], units[n], firstSyllable))
    return out

import collections
tally = collections.Counter(); flipex = collections.defaultdict(list)
for r in csv.DictReader(open("resources/LexiqueMixte.tsv"), delimiter="\t"):
    if r["cgram"] != "VER": continue
    tags = [t for t in r["infover"].split(";") if t]
    if "inf" in tags: continue
    tn = vp.getTrustedTemplate(r["lemme"], vt, ex); iw = inf.get(r["lemme"])
    if tn is None or iw is None or tn not in ct: continue
    for tag in tags:
        p = tag.split(":")
        if len(p) != 3: continue
        g = vp.generateMissingConjugatedForm(r["lemme"], ct[tn], iw, f"{p[0]}:{p[1]}", p[2], tables, minMatchRate=1.0)
        if g is None or g.ortho != r["ortho"]: continue
        hits = [h for h in doubledPositions(g) if h[1] == "e" and h[2] == "e"]  # coarse plain-e
        if not hits: continue
        wantFix = g.phonology != r["phon"] and g.phonology.replace("E", "e") == r["phon"]
        match = g.phonology == r["phon"]
        for h in hits:
            key = ("fix" if wantFix else "flip" if match else "other", "first" if h[3] else "later")
            tally[key] += 1
            if len(flipex[key]) < 4: flipex[key].append((r["ortho"], g.phonology, r["phon"]))
for k in sorted(tally): print(k, tally[k], flipex[k][:3])
