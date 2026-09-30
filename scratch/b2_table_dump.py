import sys
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
import src.verbparadigm as vp
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
for k, v in sorted(tables.midVowelByOrtho.items()):
    if k[0] in ("e","é","è","ê","aî","ai","ei","o","eu","au","è"): print(k, "->", v)
