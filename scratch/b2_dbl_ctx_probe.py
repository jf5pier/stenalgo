"""Votes for plain-e non-final nuclei whose next sounded ortho unit is a doubled letter or sc."""
import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]

def doubled(unit):
    return len(unit) == 2 and unit[0] == unit[1] and unit[0].isalpha() and not unit[0] in "aeiouyéèêàâîôûëï" or unit == "sc"

votes = collections.defaultdict(collections.Counter)
ex = collections.defaultdict(list)
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    orthoUnits, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(orthoUnits) or vp._joinPhonology(units) != word.phonology: continue
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    for pos, n in enumerate(nuclei):
        if units[n] not in vp.MID_VOWELS: continue
        final = pos == len(nuclei) - 1 or not any(b > n for b in boundaries)
        if final: continue
        nxt = next((u for u in orthoUnits[n+1:] if u != "#"), None)
        if nxt is None or not doubled(nxt): continue
        key = orthoUnits[n]
        votes[key][units[n]] += 1
        if len(ex[key]) < 4: ex[key].append((word.lemme, word.rawSyllCV, word.rawOrthosyllCV))
for key, vs in sorted(votes.items(), key=lambda kv: -kv[1].total()):
    n = vs.total()
    if n < 10: continue
    top, cnt = vs.most_common(1)[0]
    print(f"{key!r:6} n={n:5d} {vs.most_common(4)}  e.g. {ex[key][:2]}")
