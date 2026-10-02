#!/usr/bin/env python
# coding: utf-8
"""
cProfile analysis of extractDiscriminatingFeatures.
Usage: PYTHONHASHSEED=0 python scratch/perf_extract_cprofile.py 2>&1 | tee scratch/perf-extract-cprofile.log
"""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures

t0 = time.perf_counter()
theory, keyboard = loadTheoryAndKeyboard()
load_time = time.perf_counter() - t0
print(f"[LOAD] {load_time:.1f}s", flush=True)
print(f"Theory size: {len(theory)} strokes, ~167k words total", flush=True)

prof = cProfile.Profile()
prof.enable()
t_start = time.perf_counter()
result = extractDiscriminatingFeatures(theory)
t_end = time.perf_counter()
prof.disable()

elapsed = t_end - t_start
print(f"\n[TOTAL] extractDiscriminatingFeatures: {elapsed:.1f}s", flush=True)
print(f"Result size: {len(result[0])} features, {len(result[1])} ordered features, {len(result[2])} stroke-lemme groups", flush=True)

prof.dump_stats('scratch/perf_extract_cprofile.prof')

print("\n===== By cumulative time (top 20) =====")
pstats.Stats(prof).sort_stats('cumulative').print_stats(20)

print("\n===== By internal time (top 20) =====")
pstats.Stats(prof).sort_stats('tottime').print_stats(20)
