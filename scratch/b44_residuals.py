"""Of the same-lemma residual collisions, which make a spelling unreachable in Plover?"""
import json
from collections import Counter
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from src.ambiguitychecker import findFinalCollisions, loadReform1990DoubletPairs, buildWordsByOrthoLemme, _resolveEntryWord

kb = Starboard.fromJSONFile("starboard3h.json")
phon, dis = loadPhoneticAndDisambiguatedTheory(kb)
report = findFinalCollisions(dis, loadReform1990DoubletPairs())
reachable = set(json.load(open("plover_stenalgo_dictionary.json")).values())
wordToStrokes = {w: s for s, ws in phon.items() for w in ws}
byOL = buildWordsByOrthoLemme(phon)
resolved = {_resolveEntryWord(e, o, wordToStrokes, byOL) for e in json.load(open("resolved_press_sets.json")) for o in e["pressSets"]}
stats = Counter()
for kind in ("sameLemmeGramCat", "reformDoublet"):
    for stroke, words in getattr(report, kind).items():
        lost = sorted({w.ortho for w in words} - reachable)
        twins = [w for w in words if w not in resolved and len(byOL[(w.ortho, w.lemmeGramCat)]) > 1]
        stats[f"{kind}: total"] += 1
        stats[f"{kind}: has an unresolved twin Word"] += bool(twins)
        if lost:
            stats[f"{kind}: a spelling unreachable in Plover"] += 1
            print(kind, lost, [(w.ortho, w.infoVerb, round(w.frequency, 2), w in resolved) for w in words])
for k, v in sorted(stats.items()): print(f"{v:5d} {k}")
