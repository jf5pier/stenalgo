import sys, csv
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)
import importlib.util
spec = importlib.util.spec_from_file_location("vpOld", "scratch/verbparadigm_old.py")
vpOld = importlib.util.module_from_spec(spec); spec.loader.exec_module(vpOld)
tablesOld = vpOld.deriveConjugationEndingTables(theory, vt, ex)
for lemme, tag, pers in [("aigrir","ind:pas","3p"), ("aguerrir","ind:fut","3s"), ("abêtir","ind:imp","3s")]:
    tn = vp.getTrustedTemplate(lemme, vt, ex); iw = inf[lemme]
    g = vp.generateMissingConjugatedForm(lemme, ct[tn], iw, tag, pers, tables, minMatchRate=1.0)
    go = vpOld.generateMissingConjugatedForm(lemme, ct[tn], iw, tag, pers, tablesOld, minMatchRate=1.0)
    print(lemme, tag, pers)
    print("  new:", g.phonology, g.rawSyllCV, g.rawOrthosyllCV)
    print("  old:", go.phonology, go.rawSyllCV, go.rawOrthosyllCV)
    print("  inf:", iw.phonology, iw.rawSyllCV, iw.rawOrthosyllCV)
