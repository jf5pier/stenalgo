"""Try injecting ('e','nonfinal-open')->E and count fixes vs flips on attested finite forms."""
import sys, csv, collections
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
tables.midVowelByOrtho[("e", vp.NON_FINAL_OPEN)] = "E"
inf = vp.attestedInfinitiveWordByLemme(theory)
fix, flip, same = [], [], []
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
        if g.phonology == r["phon"]: same.append(r["ortho"])
        elif g.phonology.replace("E", "e") == r["phon"]: flip.append((r["ortho"], tag))
        else: fix.append((r["ortho"], tag, g.phonology, r["phon"]))
print(f"still-match {len(same)}, attested-coarse-e flips {len(flip)}, other mismatches {len(fix)}")
fl = collections.Counter(w.split(";")[0] if False else o for o, t in flip)
print("flip spellings:", sorted(fl)[:60])
print("fix examples:", fix[:12])
