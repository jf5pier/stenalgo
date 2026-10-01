import sys
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)
for lemme, tag, pers in [("pressentir","ind:imp","2p"), ("tressaillir","ind:pre","2p"), ("pressentir","ind:imp","3s")]:
    tn = vp.getTrustedTemplate(lemme, vt, ex); iw = inf[lemme]
    g = vp.generateMissingConjugatedForm(lemme, ct[tn], iw, tag, pers, tables, minMatchRate=1.0)
    print(lemme, tag+":"+pers, "->", g.ortho, "| phon", g.rawSyllCV, "| ortho", g.rawOrthosyllCV)
