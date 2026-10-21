"""Hand-run: the Plover dictionary of the CURRENT theory (flag on or off) written to a chosen path, never over plover_stenalgo_dictionary.json.
Usage: STENALGO_PHONOLOGY_REWRITE=1 python -m scratch.overrides.export_flag_dictionary OUT.json"""
import json
import sys
from collections import defaultdict

from src.ambiguitychecker import findFinalCollisions, loadReform1990DoubletPairs
from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadDisambiguatedTheory

kb = Starboard.fromJSONFile("starboard3h.json")
assert kb is not None
theory = loadDisambiguatedTheory(kb)
byText: dict[str, list] = defaultdict(list)
for word, strokesList in theory.items():
    for strokes in strokesList:
        byText[renderFinalStrokesToRTFCRE(kb, strokes)].append(word)
out = {text: max(words, key=lambda w: w.frequency).ortho for text, words in byText.items()}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
report = findFinalCollisions(theory, loadReform1990DoubletPairs())
print(f"{len(out)} strokes; cross-lemma collisions {len(report.crossLemma)}, same-lemma residual {len(report.sameLemmeGramCat)}")
