import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
votes = collections.defaultdict(collections.Counter)
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    orthoUnits, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(orthoUnits) or vp._joinPhonology(units) != word.phonology: continue
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    for pos, n in enumerate(nuclei):
        if units[n] not in vp.MID_VOWELS: continue
        final = pos == len(nuclei) - 1 or not any(b > n for b in boundaries)
        syllEnd = min((b for b in boundaries if b > n), default=len(units))
        coda = [u for u in units[n+1:syllEnd] if u != "#" and not vp._hasNucleus(u)]
        ctx = ("final" if final else "nonfinal") + ("-closed" if coda else "-open")
        votes[(orthoUnits[n], ctx)][units[n]] += 1
for (ortho, ctx), vs in sorted(votes.items()):
    n = vs.total()
    if n < 20: continue
    top, cnt = vs.most_common(1)[0]
    if top not in vp.MID_VOWELS: continue
    print(f"{ortho!r:7} {ctx:14} n={n:6d} top={top} share={cnt/n:.3f} {vs.most_common(4)}")
