import json
from src.keyboard import Starboard, canonicalizeStrokes
from util._theoryio import _loadDictionaryAndPhoneticTheory
from src.ambiguitychecker import *
from src.ambiguitychecker import _resolveEntryWord
d, phon = _loadDictionaryAndPhoneticTheory()
kb = Starboard.fromJSONFile("starboard3h.json")
kg = json.load(open("keypress_groups.json")); mbk = {int(g): frozenset(m) for g, m in kg["markersByKeypress"].items()}
rg = json.load(open("resolved_press_sets.json"))
w2s = buildWordToStrokes(phon); bol = buildWordsByOrthoLemme(phon)
g2w = buildKeypressGroupToWords(rg, mbk, w2s, bol); extra = buildKeypressGroupExtraAlternates(rg, mbk, w2s, bol)
asg = realizeKeypressGroupsAsExtraStroke(g2w, phon, kb, extraGroupSetsByWord=extra, preferredKeysByGroup=resolvePreferredKeysByGroup(mbk))
fi = buildFinalInducedStrokes(phon, g2w, asg); ex = buildExtraInducedStrokes(phon, asg, extra)
dropped = 0; shown = 0
for w, s in fi.items():
    entries = [s] + ex.get(w, [])
    if len({canonicalizeStrokes(e) for e in entries}) < len(entries):
        dropped += 1
        if shown < 5 or w.ortho == "joue": shown += 1; print(w.ortho, w.lemmeGramCat, entries, extra.get(w))
print("words with duplicate entries:", dropped)
