import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
votes = collections.Counter(); ex = collections.defaultdict(list)
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(ortho) or vp._joinPhonology(units) != word.phonology: continue
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    for pos, n in enumerate(nuclei):
        if units[n] not in vp.MID_VOWELS or ortho[n] != "e": continue
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries): continue
        if not any(b <= n for b in boundaries): continue  # later syllables only
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        if nxt != "sc": continue
        votes[units[n]] += 1
        if len(ex[units[n]]) < 4: ex[units[n]].append((word.lemme, word.gramCat.name, word.rawSyllCV, word.rawOrthosyllCV))
print("later-syllable plain-e before sc:", votes.most_common())
for v, xs in ex.items():
    for x in xs: print(" ", v, x)
