"""cProfile wrapper for the S2.1 appender dry-run (B43 timing question).
Usage: PYTHONHASHSEED=0 python scratch/b43_profile.py
Writes scratch/b43-s21.prof and prints the top functions by cumulative and
internal time, plus phase wall times.
"""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import findStructuralCandidates, loadTheoryAndKeyboard
from src.featureextractor import buildDiscriminatorSelection, extractDiscriminatingFeatures
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions, loadVerbisteTemplates,
    parseConjugationTemplates,
)
from util.completeVerbParadigms import (
    VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
)

t0 = time.perf_counter()
theory, _ = loadTheoryAndKeyboard()
print(f"[t] load: {time.perf_counter()-t0:.1f}s", flush=True)

prof = cProfile.Profile()
import util.completeVerbParadigms as cvp

verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

prof.enable()
r1 = extractDiscriminatingFeatures(theory)
prof.disable()
print(f"[t] extractDiscriminatingFeatures(baseline): {time.perf_counter()-t0:.1f}s", flush=True)

p2 = cProfile.Profile()
p2.enable()
r2 = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
cands, skipped = findStructuralCandidates(r1[2], theory, verbisteTemplates, exceptions,
                                          conjugationTemplates, r2)
p2.disable()
print(f"[t] endingTables+findStructuralCandidates: {time.perf_counter()-t0:.1f}s", flush=True)

p3 = cProfile.Profile()
p3.enable()
fsw = buildDiscriminatorSelection(theory, r1[0])
p3.disable()
print(f"[t] buildDiscriminatorSelection(baseline): {time.perf_counter()-t0:.1f}s", flush=True)

for name, p in (("extract", prof), ("structural", p2), ("selection", p3)):
    p.dump_stats(f"scratch/b43-{name}.prof")
    print(f"\n===== {name} (by cumulative) =====")
    pstats.Stats(p).sort_stats("cumulative").print_stats(14)
    print(f"===== {name} (by internal) =====")
    pstats.Stats(p).sort_stats("tottime").print_stats(10)
