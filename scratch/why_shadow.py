import sys
sys.path.insert(0, "/home/jfsp/Steno/stenalgo-briefs")
from src.keyboard import Starboard, canonicalizeStrokes
from util._theoryio import loadDisambiguatedTheory
from util._stenorender import renderFinalStrokesToRTFCRE
sb = Starboard.fromJSONFile("starboard3h.json")
theory = loadDisambiguatedTheory(sb)
target = canonicalizeStrokes(((7, 13, 22),))
for w, alts in theory.items():
    if any(canonicalizeStrokes(a) == target for a in alts):
        print("WORD", w.ortho, w.gramCat, [renderFinalStrokesToRTFCRE(sb, a) for a in alts])
for w, alts in theory.items():
    if w.ortho in ("il", "y", "ily"):
        print("PART", w.ortho, w.gramCat, [renderFinalStrokesToRTFCRE(sb, a) for a in alts][:3], [a for a in alts][:3])
