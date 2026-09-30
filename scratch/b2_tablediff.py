import sys, importlib.util
sys.path.insert(0, ".")
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
import src.verbparadigm as vpNew
spec = importlib.util.spec_from_file_location("vpOld", "scratch/verbparadigm_old.py")
vpOld = importlib.util.module_from_spec(spec); spec.loader.exec_module(vpOld)
theory, _ = loadTheoryAndKeyboard()
words = [w for ws in theory.values() for w in ws]
vt = vpNew.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vpNew.loadVerbModelExceptions(EXCEPTIONS_PATH)
oSplit = vpOld.deriveSyllableSplitTable(words); nSplit = vpNew.deriveSyllableSplitTable(words)
assert oSplit == nSplit, [k for k in set(oSplit)|set(nSplit) if oSplit.get(k)!=nSplit.get(k)][:10]
print("split tables identical")
oT, nT = vpOld.deriveMidVowelTable(words), vpNew.deriveMidVowelTable(words)
removed = {k: v for k, v in oT.items() if k not in nT}
changed = {k: (v, nT[k]) for k, v in oT.items() if k in nT and nT[k] != v}
added = {k: v for k, v in nT.items() if k not in oT}
print(f"old rules {len(oT)}, new rules {len(nT)}; removed {len(removed)}, changed {len(changed)}, added {len(added)}")
print("removed:", sorted(removed.items()))
print("changed:", sorted(changed.items()))
print("added:", sorted(added.items()))
