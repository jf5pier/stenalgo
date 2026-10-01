"""Which currently-matching rows would break if sc counted as doubled / the first syllable laxxed?"""
import sys, csv
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)

def positions(g):
    units, boundaries = vp._unitsAndBoundaries(g.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(g.rawOrthosyllCV)
    if len(units) != len(ortho): return []
    nuclei = [i for i, u in enumerate(units) if _hasNucleus(u)] if False else [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    out = []
    for pos, n in enumerate(nuclei):
        if ortho[n] != "e" or units[n] != "e": continue
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries): continue
        first = not any(b <= n for b in boundaries)
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        dbl = nxt and len(nxt) == 2 and nxt[0] == nxt[1] and nxt[0].isalpha() and nxt[0] not in "aeiouy"
        if not first and nxt == "sc": out.append("sc")
        if first and dbl: out.append("first+dbl:" + nxt)
    return out

import collections
byclass = collections.defaultdict(lambda: collections.defaultdict(str))
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
        if g is None or g.ortho != r["ortho"] or g.phonology != r["phon"]: continue
        for c in positions(g):
            byclass[c][r["ortho"]] = r["phon"]
for c, words in byclass.items():
    print(f"\n== {c}: {len(words)} words would break ==")
    for w, ph in sorted(words.items()): print(f"  {w:<20} {ph}")
