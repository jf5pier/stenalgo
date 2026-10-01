"""Corpus-wide vowel distribution per ortho unit in closed NON-final syllables."""
import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp

theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]

def midClosedContexts(units, boundaries):
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    out = {}
    for n in nuclei[:-1]:
        nxt = min((b for b in boundaries if b > n), default=len(units))
        coda = [u for u in units[n + 1:nxt] if u != "#" and not vp._hasNucleus(u)]
        if coda:
            out[n] = True
    return out

vowelsByKey = collections.defaultdict(collections.Counter)
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    orthoUnits, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(orthoUnits) or vp._joinPhonology(units) != word.phonology:
        continue
    for i in midClosedContexts(units, boundaries):
        vowelsByKey[orthoUnits[i]][units[i]] += 1

total = collections.Counter()
for ortho, vowels in sorted(vowelsByKey.items(), key=lambda kv: -sum(kv[1].values())):
    n = vowels.total()
    if n < 10: continue
    top, cnt = vowels.most_common(1)[0]
    if top not in vp.MID_VOWELS: continue
    total[ortho] += n
    share = cnt / n
    flag = "KEEP" if share >= 0.9 else "   ?"
    print(f"{flag} {ortho!r:8} n={n:6d} top={top} share={share:.3f}  {vowels.most_common(4)}")
