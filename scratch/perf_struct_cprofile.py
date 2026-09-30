#!/usr/bin/env python3
"""
cProfile-based profiling of findStructuralCandidates and deriveConjugationEndingTables.
Usage: PYTHONHASHSEED=0 flock <lock> python scratch/perf_struct_cprofile.py > scratch/perf-struct-cprof.log 2>&1
"""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import findStructuralCandidates, loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions, loadVerbisteTemplates,
    parseConjugationTemplates,
)
from util.completeVerbParadigms import (
    VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
)

print("=" * 60, flush=True)
print("Performance Profiling: deriveConjugationEndingTables + findStructuralCandidates", flush=True)
print("=" * 60, flush=True)

t0 = time.perf_counter()
print(f"[{time.perf_counter()-t0:.1f}s] Loading theory...", flush=True)
theory, _ = loadTheoryAndKeyboard()
print(f"[{time.perf_counter()-t0:.1f}s] Theory loaded ({len(theory)} strokes)", flush=True)

print(f"[{time.perf_counter()-t0:.1f}s] Loading verb data...", flush=True)
verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
print(f"[{time.perf_counter()-t0:.1f}s] Verb data loaded", flush=True)

print(f"[{time.perf_counter()-t0:.1f}s] Extracting discriminating features...", flush=True)
r1 = extractDiscriminatingFeatures(theory)
print(f"[{time.perf_counter()-t0:.1f}s] Features extracted", flush=True)

# Profile deriveConjugationEndingTables
print(f"\n[{time.perf_counter()-t0:.1f}s] Profiling deriveConjugationEndingTables...", flush=True)
prof_ending = cProfile.Profile()
prof_ending.enable()
r2 = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
prof_ending.disable()
t_ending = time.perf_counter() - t0
print(f"[{t_ending:.1f}s] deriveConjugationEndingTables completed", flush=True)

# Profile findStructuralCandidates
print(f"\n[{time.perf_counter()-t0:.1f}s] Profiling findStructuralCandidates...", flush=True)
prof_find = cProfile.Profile()
prof_find.enable()
cands, skipped = findStructuralCandidates(r1[2], theory, verbisteTemplates, exceptions,
                                          conjugationTemplates, r2)
prof_find.disable()
t_find = time.perf_counter() - t0
print(f"[{t_find:.1f}s] findStructuralCandidates completed ({len(cands)} candidates)", flush=True)

print("\n" + "=" * 60, flush=True)
print("cProfile Results: deriveConjugationEndingTables", flush=True)
print("=" * 60, flush=True)
prof_ending.dump_stats("scratch/perf-struct-ending.prof")
pstats.Stats(prof_ending).sort_stats("cumulative").print_stats(20)
print("\n--- By tottime (internal time) ---")
pstats.Stats(prof_ending).sort_stats("tottime").print_stats(15)

print("\n" + "=" * 60, flush=True)
print("cProfile Results: findStructuralCandidates", flush=True)
print("=" * 60, flush=True)
prof_find.dump_stats("scratch/perf-struct-find.prof")
pstats.Stats(prof_find).sort_stats("cumulative").print_stats(20)
print("\n--- By tottime (internal time) ---")
pstats.Stats(prof_find).sort_stats("tottime").print_stats(15)

print("\n" + "=" * 60, flush=True)
print("Summary", flush=True)
print("=" * 60, flush=True)
print(f"deriveConjugationEndingTables: {t_ending:.1f}s")
print(f"findStructuralCandidates: {t_find:.1f}s")
