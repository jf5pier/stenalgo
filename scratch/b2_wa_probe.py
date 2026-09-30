import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
def midClosed(units, boundaries):
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    for n in nuclei[:-1]:
        nxt = min((b for b in boundaries if b > n), default=len(units))
        coda = [u for u in units[n+1:nxt] if u != "#" and not vp._hasNucleus(u)]
        if coda: yield n
shown = 0
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    orthoUnits, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(orthoUnits) or vp._joinPhonology(units) != word.phonology: continue
    for i in midClosed(units, boundaries):
        if orthoUnits[i] == "o" and units[i] == "wa":
            print((word.lemme, word.gramCat), "|", word.rawSyllCV, "|", word.rawOrthosyllCV)
            shown += 1
            break
    if shown >= 12: break
