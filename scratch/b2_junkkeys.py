import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
targets = {("i","any"), ("t","any"), ("ay","any"), ("ue","any"), ("eû","any"), ("é","closed")}
shown = collections.defaultdict(int)
for word in words:
    units, _ = vp._unitsAndBoundaries(word.rawSyllCV)
    orthoUnits, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(orthoUnits) or vp._joinPhonology(units) != word.phonology: continue
    for i, u in enumerate(units):
        if u in vp.MID_VOWELS and (orthoUnits[i], "any") in targets and shown[(orthoUnits[i],"any")] < 6:
            shown[(orthoUnits[i],"any")] += 1
            print(orthoUnits[i], "->", u, "|", (word.lemme, word.gramCat.name), word.rawSyllCV, word.rawOrthosyllCV)
