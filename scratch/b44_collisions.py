"""B44 probe: every final steno carrying >= 2 distinct spellings (a real collision),
classified by which entries collide (primary index 0 vs alternate) and why."""
import sys
from collections import defaultdict, Counter
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util._stenorender import renderFinalStrokesToRTFCRE
from src.ambiguitychecker import loadReform1990DoubletPairs

kb = Starboard.fromJSONFile("starboard3h.json")
phon, dis = loadPhoneticAndDisambiguatedTheory(kb)
doublets = loadReform1990DoubletPairs()
bySteno = defaultdict(list)
for w, sl in dis.items():
    for i, s in enumerate(sl):
        bySteno[renderFinalStrokesToRTFCRE(kb, s)].append((w, i))
stats = Counter(); ex = defaultdict(list)
lostSpellings = set()
for st, entries in bySteno.items():
    orthos = {w.ortho for w, _ in entries}
    if len(orthos) < 2: continue
    anyAlt = any(i > 0 for _, i in entries)
    lgc = {w.lemmeGramCat for w, _ in entries}
    lemmes = {w.lemme for w, _ in entries}
    if anyAlt: kind = "involves an alternate entry"
    elif len(lgc) < 2: kind = "primary-only, one lemmeGramCat"
    elif any(frozenset({a.lemme, b.lemme}) in doublets for a, _ in entries for b, _ in entries): kind = "primary-only, reform doublet (R2)"
    else: kind = "primary-only, other"
    stats[kind] += 1
    ex[kind].append((st, sorted((w.ortho, w.lemmeGramCat, i, round(w.frequency, 2)) for w, i in entries)))
for k, v in stats.items(): print(f"{v:6d}  {k}")
for k, v in ex.items():
    print("===", k)
    for e in v[:int(sys.argv[1]) if len(sys.argv) > 1 else 12]: print("  ", e)
