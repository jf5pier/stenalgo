"""B43 hypothesis check: do >=2 distinct lemmas' generated candidates get
appended into the SAME stroke group by temporarilyAugmented? If yes, the tail
order of that group's word list depends on the salted iteration order of
`undersampled` (detectUndersampledLemmas), and crossLemmaFeatureSetCollisions
matches feature-set tuples exactly -- so collision detection is seed-sensitive.

Usage: PYTHONHASHSEED=0 python scratch/b43_shared_groups.py
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import (
    EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH, VERBISTE_VERBS_PATH,
    findStructuralCandidates, loadTheoryAndKeyboard,
)
from src.featureextractor import extractDiscriminatingFeatures
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions,
    loadVerbisteTemplates, parseConjugationTemplates,
)

theory, _starboard = loadTheoryAndKeyboard()
templates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugations = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
print("theory loaded; running extract (for strokeLemmeDiscriminators)...", flush=True)
_, _, sld = extractDiscriminatingFeatures(theory)
tables = deriveConjugationEndingTables(theory, templates, exceptions)
print(f"strokeLemmeDiscriminators groups: {len(sld)}", flush=True)
from src.verbparadigm import detectUndersampledLemmas
undersampled = detectUndersampledLemmas(sld, templates, exceptions)
print(f"undersampled VER lemmas flagged: {len(undersampled)}", flush=True)
candidates, _skipped = findStructuralCandidates(
    sld, theory, templates, exceptions, conjugations, tables)

strokesByWord = {w: s for s, ws in theory.items() for w in ws}
byStrokes: dict = defaultdict(list)
for lemmeGramCat, _info, _gen, ref in candidates:
    byStrokes[strokesByWord[ref]].append(lemmeGramCat)

multiLemma = {s: lgcs for s, lgcs in byStrokes.items() if len(set(lgcs)) > 1}
multiCandidate = {s: lgcs for s, lgcs in byStrokes.items() if len(lgcs) > 1}
print(f"\ncandidates={len(candidates)}")
print(f"stroke groups receiving candidates: {len(byStrokes)}")
print(f"stroke groups receiving >=2 candidates (tail order matters): {len(multiCandidate)}")
print(f"stroke groups receiving candidates from >=2 DISTINCT lemmas (salted interleave): {len(multiLemma)}")
for s, lgcs in sorted(multiLemma.items(), key=lambda kv: -len(set(kv[1])))[:12]:
    print(f"  {s}: {Counter(lgcs).most_common()}")
