#!/usr/bin/env python
# coding: utf-8
"""
Profile buildFeasibleDiscriminatorOptions specifically (the actual slow function).
Usage: PYTHONHASHSEED=0 python scratch/perf_extract_feasible.py 2>&1 | tee scratch/perf-extract-feasible.log
"""
import cProfile
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures, buildFeasibleDiscriminatorOptions

t0 = time.perf_counter()
theory, keyboard = loadTheoryAndKeyboard()
load_time = time.perf_counter() - t0
print(f"[LOAD] {load_time:.1f}s", flush=True)
print(f"Theory size: {len(theory)} strokes, ~167k words total", flush=True)

# First, get extractDiscriminatingFeatures result
t_extract = time.perf_counter()
wordIsDiscrminatedByFeature, _, _ = extractDiscriminatingFeatures(theory)
extract_time = time.perf_counter() - t_extract
print(f"[EXTRACT] extractDiscriminatingFeatures: {extract_time:.1f}s", flush=True)
print(f"  Features discriminating: {len(wordIsDiscrminatedByFeature)}", flush=True)
total_discriminated = sum(len(words) for words in wordIsDiscrminatedByFeature.values())
print(f"  Total word-feature pairs: {total_discriminated}", flush=True)

# Now profile buildFeasibleDiscriminatorOptions
prof = cProfile.Profile()
prof.enable()
t_start = time.perf_counter()
result = buildFeasibleDiscriminatorOptions(theory, wordIsDiscrminatedByFeature)
t_end = time.perf_counter()
prof.disable()

elapsed = t_end - t_start
print(f"\n[TOTAL] buildFeasibleDiscriminatorOptions: {elapsed:.1f}s", flush=True)
print(f"Result size: {len(result)} (stroke, lemme) groups", flush=True)
total_words_in_groups = sum(len(byWord) for byWord in result.values())
print(f"Total words across all groups: {total_words_in_groups}", flush=True)
total_features_in_groups = sum(len(feats) for byWord in result.values() for feats in byWord.values())
print(f"Total feature assignments: {total_features_in_groups}", flush=True)

prof.dump_stats('scratch/perf_extract_feasible.prof')

print("\n===== By cumulative time (top 25) =====")
pstats.Stats(prof).sort_stats('cumulative').print_stats(25)

print("\n===== By internal time (top 25) =====")
pstats.Stats(prof).sort_stats('tottime').print_stats(25)
