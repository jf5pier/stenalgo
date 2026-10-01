"""Votes for e-family nuclei before a doubled letter, later syllables, by input vowel."""
import sys, collections
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
votes = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list)
for word in words:
    units, boundaries = vp._unitsAndBoundaries(word.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(word.rawOrthosyllCV)
    if len(units) != len(ortho) or vp._joinPhonology(units) != word.phonology: continue
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    for pos, n in enumerate(nuclei):
        if units[n] not in vp.MID_VOWELS or ortho[n] != "e": continue
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries): continue
        if not any(b <= n for b in boundaries): continue  # later syllables only (a boundary starts at or before the nucleus)
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        if not (nxt and len(nxt) == 2 and nxt[0] == nxt[1] and nxt[0].isalpha() and nxt[0] not in "aeiouy"): continue
        votes["all"][units[n]] += 1
        if units[n] in ("°", "2", "9"):
            if len(ex["schwa"]) < 6: ex["schwa"].append((word.lemme, word.gramCat.name, word.rawSyllCV, word.rawOrthosyllCV))
print("later-syllable plain-e before doubled:", votes["all"].most_common())
for x in ex["schwa"]: print("  ", x)
