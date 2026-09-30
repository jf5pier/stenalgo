"""Does a doubled consonant (or sc) after plain-e separate the E-reading from the e-reading?"""
import sys, csv, re
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)
eToE, eToElse = set(), set()
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
        if g is None or g.ortho != r["ortho"] or g.phonology == r["phon"]: continue
        (eToE if g.phonology.replace("E", "e") == r["phon"] else eToElse).add(r["ortho"])
def dbl(w): return bool(re.search(r"e([a-z])\1", w) or "esc" in w)
print("attested says E (want the rule):", len(eToE), "| doubled:", sum(map(dbl, eToE)))
print(sorted(eToE))
print("attested says e (must NOT lax):", len(eToElse), "| doubled:", sum(map(dbl, eToElse)))
print(sorted(eToElse))
