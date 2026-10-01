"""List every sameLemmaGramCat residual collision group with its words."""
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from src.ambiguitychecker import findFinalCollisions, loadReform1990DoubletPairs

kb = Starboard.fromJSONFile("starboard3h.json")
phon, dis = loadPhoneticAndDisambiguatedTheory(kb)
report = findFinalCollisions(dis, loadReform1990DoubletPairs())

groups = sorted(report.sameLemmeGramCat.values(), key=lambda ws: ws[0].lemmeGramCat)
print(f"{len(groups)} groups, {sum(len(ws) for ws in groups)} words\n")
for words in groups:
    lemme = words[0].lemmeGramCat
    forms = ", ".join(f"{w.ortho} [{w.infoVerb or w.gender + '_' + w.number if w.gender else w.infoVerb or '-'}]"
                      for w in sorted(words, key=lambda w: w.ortho))
    print(f"{lemme}: {forms}")
