"""Split the backtest by before-a-doubled-consonant: fixes among e->E mismatches vs flips among matches."""
import sys, csv, re
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)

def fixdiff(a, b):
    return [(x, y) for x, y in zip(a, b) if x != y]

def beforeDoubled(g):
    units, boundaries = vp._unitsAndBoundaries(g.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(g.rawOrthosyllCV)
    if len(units) != len(ortho): return None
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    hits = []
    for pos, n in enumerate(nuclei):
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries): continue
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        if nxt and (len(nxt) == 2 and nxt[0] == nxt[1] and nxt[0].isalpha() and nxt[0] not in "aeiouy"):
            hits.append((n, ortho[n], units[n]))
    return hits

wantE_dbl, wantE_bare, flip_dbl = [], [], []
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
        hits = beforeDoubled(g)
        if not hits: continue
        # only plain-e positions, coarse unit
        plain = [h for h in hits if h[1] == "e" and h[2] in ("e", "°")]
        if not plain: continue
        if g.phonology != r["phon"] and len(fixdiff(g.phonology, r["phon"])) <= 2 and g.phonology.replace("E", "e") != r["phon"]:
            (wantE_dbl if any(h[2] == "e" for h in plain) else wantE_bare).append((r["ortho"], tag, g.phonology, r["phon"]))
        elif g.phonology == r["phon"] and any(h[2] == "e" for h in plain) and "E" not in r["phon"][max(0, plain[0][0]-1):]:
            flip_dbl.append((r["ortho"], tag, r["phon"]))

def fixdiff(a, b):
    return [(x, y) for x, y in zip(a, b) if x != y]

print("mismatched rows with plain-e before doubling:", len(wantE_dbl))
for x in wantE_dbl[:8]: print("  ", x)
print("currently-matching rows with coarse plain-e before doubling (flip risk):", len(flip_dbl))
for x in flip_dbl[:8]: print("  ", x)
