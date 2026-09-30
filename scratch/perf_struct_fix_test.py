#!/usr/bin/env python3
"""
Monkeypatch test: apply optimization to fullFeatureSpace and verify correctness.
Usage: PYTHONHASHSEED=0 flock <lock> python scratch/perf_struct_fix_test.py > scratch/perf-struct-fix-test.log 2>&1
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import findStructuralCandidates, loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions, loadVerbisteTemplates,
    parseConjugationTemplates, detectUndersampledLemmas, fullFeatureSpace,
    LemmeGramCat, WordFeature, Strokes
)
from util.completeVerbParadigms import (
    VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
)
from collections import defaultdict

print("=" * 70, flush=True)
print("Optimization Test: Monkeypatch fullFeatureSpace", flush=True)
print("=" * 70, flush=True)

t0 = time.perf_counter()
print(f"[{time.perf_counter()-t0:.1f}s] Loading...", flush=True)
theory, _ = loadTheoryAndKeyboard()
verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
print(f"[{time.perf_counter()-t0:.1f}s] Loaded", flush=True)

print(f"[{time.perf_counter()-t0:.1f}s] Extracting discriminating features...", flush=True)
r1 = extractDiscriminatingFeatures(theory)
strokeLemmeDiscriminators = r1[2]
print(f"[{time.perf_counter()-t0:.1f}s] Extracted", flush=True)

# Step 1: Run with ORIGINAL detectUndersampledLemmas
print(f"\n[{time.perf_counter()-t0:.1f}s] Step 1: Original detectUndersampledLemmas...", flush=True)
t_orig = time.perf_counter()
result_orig = detectUndersampledLemmas(strokeLemmeDiscriminators, verbisteTemplates, exceptions)
t_orig = time.perf_counter() - t_orig
print(f"  Time: {t_orig:.1f}s, Found {len(result_orig)} undersampled lemmas", flush=True)

# Step 2: Apply monkeypatch with optimized fullFeatureSpace
print(f"\n[{time.perf_counter()-t0:.1f}s] Step 2: Optimized detectUndersampledLemmas...", flush=True)

def fullFeatureSpace_optimized(
    strokeLemmeDiscriminators: dict[tuple[Strokes, LemmeGramCat], dict],
    lemmeGramCat: LemmeGramCat,
) -> set[WordFeature]:
    """Optimized version using pre-built index."""
    # This will be used with an index passed in a closure (see below)
    space: set[WordFeature] = set()
    for wordFeatures in index_by_lemme_closure.get(lemmeGramCat, []):
        for features in wordFeatures.values():
            space.update(features)
    return space

# Pre-build the index ONCE
print(f"  Building index...", flush=True)
index_by_lemme = defaultdict(list)
for (_strokes, groupLemme), wordFeatures in strokeLemmeDiscriminators.items():
    index_by_lemme[groupLemme].append(wordFeatures)
print(f"    Index built: {len(index_by_lemme)} lemmeGramCats", flush=True)

# Use closure to capture the index
index_by_lemme_closure = index_by_lemme

# Monkeypatch the function
import src.verbparadigm
original_fullFeatureSpace = src.verbparadigm.fullFeatureSpace
src.verbparadigm.fullFeatureSpace = fullFeatureSpace_optimized

t_opt = time.perf_counter()
result_opt = detectUndersampledLemmas(strokeLemmeDiscriminators, verbisteTemplates, exceptions)
t_opt = time.perf_counter() - t_opt
print(f"  Time: {t_opt:.1f}s, Found {len(result_opt)} undersampled lemmas", flush=True)

# Restore original
src.verbparadigm.fullFeatureSpace = original_fullFeatureSpace

# Step 3: Verify correctness
print(f"\n[{time.perf_counter()-t0:.1f}s] Step 3: Verifying correctness...", flush=True)
if len(result_orig) != len(result_opt):
    print(f"  ERROR: Different number of results: {len(result_orig)} vs {len(result_opt)}")
    sys.exit(1)

for lemmeGramCat in result_orig:
    if lemmeGramCat not in result_opt:
        print(f"  ERROR: Missing lemmeGramCat in optimized result: {lemmeGramCat}")
        sys.exit(1)
    orig_features = result_orig[lemmeGramCat].missingFeatures
    opt_features = result_opt[lemmeGramCat].missingFeatures
    if orig_features != opt_features:
        print(f"  ERROR: Different features for {lemmeGramCat}: {len(orig_features)} vs {len(opt_features)}")
        sys.exit(1)

print(f"  ✓ All {len(result_orig)} results match!")

print(f"\n" + "=" * 70, flush=True)
print(f"Performance Summary")
print(f"=" * 70, flush=True)
print(f"Original detectUndersampledLemmas: {t_orig:.1f}s")
print(f"Optimized detectUndersampledLemmas: {t_opt:.1f}s")
print(f"Speedup: {t_orig/t_opt:.1f}x")
print(f"Estimated savings: {t_orig - t_opt:.1f}s")

# Step 4: Run full findStructuralCandidates with optimized version
print(f"\n[{time.perf_counter()-t0:.1f}s] Step 4: Full findStructuralCandidates...", flush=True)

# Re-apply monkeypatch
src.verbparadigm.fullFeatureSpace = fullFeatureSpace_optimized

print(f"  Running with OPTIMIZED version...", flush=True)
t_find_opt = time.perf_counter()
r2 = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
cands_opt, skipped_opt = findStructuralCandidates(
    r1[2], theory, verbisteTemplates, exceptions, conjugationTemplates, r2
)
t_find_opt = time.perf_counter() - t_find_opt

# Restore original
src.verbparadigm.fullFeatureSpace = original_fullFeatureSpace

print(f"  Optimized time: {t_find_opt:.1f}s, {len(cands_opt)} candidates", flush=True)

print(f"\nEstimated savings in full S2.1 pipeline:")
print(f"  Current S2.1: ~318s (with ~126s in endingTables+findStructuralCandidates)")
print(f"  Current findStructuralCandidates: ~215s (measured with profiling)")
print(f"  Savings from this fix: ~{t_orig - t_opt:.0f}s")
print(f"  New estimated S2.1: ~{318 - (t_orig - t_opt):.0f}s")
print(f"  New estimated endingTables+findStructuralCandidates: ~{126 - (t_orig - t_opt):.0f}s")
