#!/usr/bin/env python3
"""
Line-level instrumentation of findStructuralCandidates hotpath.
Measures loop iterations and data structure sizes.
Usage: PYTHONHASHSEED=0 flock <lock> python scratch/perf_struct_lineinst.py > scratch/perf-struct-lines.log 2>&1
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions, loadVerbisteTemplates,
    parseConjugationTemplates, fullFeatureSpace, detectUndersampledLemmas,
    getTrustedTemplate, lemmeOfVerbLemmeGramCat, GramCat, WordFeature, Strokes,
    LemmeGramCat, Word
)
from util.completeVerbParadigms import (
    VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
)
from collections import defaultdict

print("=" * 70, flush=True)
print("Line-level Instrumentation: detectUndersampledLemmas hotpath", flush=True)
print("=" * 70, flush=True)

t0 = time.perf_counter()
print(f"[{time.perf_counter()-t0:.1f}s] Loading...", flush=True)
theory, _ = loadTheoryAndKeyboard()
verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
r1 = extractDiscriminatingFeatures(theory)
strokeLemmeDiscriminators = r1[2]
print(f"[{time.perf_counter()-t0:.1f}s] Loaded", flush=True)

print(f"\nData structure sizes:")
print(f"  theory: {len(theory)} strokes")
total_words = sum(len(words) for words in theory.values())
print(f"  total words in theory: {total_words}")
print(f"  strokeLemmeDiscriminators keys: {len(strokeLemmeDiscriminators)}")

# Instrument detectUndersampledLemmas
print(f"\n[{time.perf_counter()-t0:.1f}s] Instrumenting detectUndersampledLemmas...", flush=True)

lemmeGramCats = {
    lemmeGramCat for (_strokes, lemmeGramCat) in strokeLemmeDiscriminators
}
print(f"  unique lemmeGramCats in strokeLemmeDiscriminators: {len(lemmeGramCats)}")

templateByLemmeGramCat: dict[LemmeGramCat, str] = {}
t_template_build = time.perf_counter()
for lemmeGramCat in lemmeGramCats:
    lemme = lemmeOfVerbLemmeGramCat(lemmeGramCat)
    if lemme is None:
        continue
    template = getTrustedTemplate(lemme, verbisteTemplates, exceptions)
    if template is not None:
        templateByLemmeGramCat[lemmeGramCat] = template
t_template_build = time.perf_counter() - t_template_build
print(f"  lemmeGramCats with trusted templates: {len(templateByLemmeGramCat)} ({t_template_build:.3f}s)")

# Measure fullFeatureSpace calls
print(f"\n[{time.perf_counter()-t0:.1f}s] Measuring fullFeatureSpace calls...", flush=True)
t_full_space = time.perf_counter()
call_count = 0
for lemmeGramCat in templateByLemmeGramCat:
    call_count += 1
    fullFeatureSpace(strokeLemmeDiscriminators, lemmeGramCat)
    if call_count % 500 == 0:
        elapsed = time.perf_counter() - t_full_space
        rate = call_count / elapsed
        print(f"    {call_count} calls in {elapsed:.1f}s ({rate:.1f} calls/sec)")

t_full_space = time.perf_counter() - t_full_space
print(f"  Total fullFeatureSpace time: {t_full_space:.1f}s for {call_count} calls")
print(f"  Average per call: {t_full_space/call_count*1000:.2f}ms")

# Now measure the optimized version with precomputation
print(f"\n[{time.perf_counter()-t0:.1f}s] Measuring optimized version (indexed grouping)...", flush=True)
t_opt = time.perf_counter()

# Precompute: group strokeLemmeDiscriminators by lemmeGramCat
index_by_lemme: dict[LemmeGramCat, list[dict[Word, list[WordFeature]]]] = defaultdict(list)
for (_strokes, groupLemme), wordFeatures in strokeLemmeDiscriminators.items():
    index_by_lemme[groupLemme].append(wordFeatures)

# Now compute feature spaces using the index
featureSpaceByLemmeGramCat = {}
for lemmeGramCat in templateByLemmeGramCat:
    space: set[WordFeature] = set()
    for wordFeatures in index_by_lemme[lemmeGramCat]:
        for features in wordFeatures.values():
            space.update(features)
    featureSpaceByLemmeGramCat[lemmeGramCat] = space

t_opt = time.perf_counter() - t_opt
print(f"  Index time: {t_opt:.1f}s")

# Verify results match
print(f"\nVerifying optimization correctness...")
featureSpaceByLemmeGramCat_slow = {
    lemmeGramCat: fullFeatureSpace(strokeLemmeDiscriminators, lemmeGramCat)
    for lemmeGramCat in templateByLemmeGramCat
}
for lemmeGramCat in templateByLemmeGramCat:
    assert featureSpaceByLemmeGramCat[lemmeGramCat] == featureSpaceByLemmeGramCat_slow[lemmeGramCat], \
        f"Mismatch for {lemmeGramCat}"
print(f"  ✓ All results match!")

print(f"\n" + "=" * 70, flush=True)
print(f"Summary")
print(f"=" * 70, flush=True)
print(f"fullFeatureSpace (naive): {t_full_space:.1f}s")
print(f"Optimized (index): {t_opt:.1f}s")
print(f"Speedup: {t_full_space/t_opt:.1f}x")
print(f"Estimated savings: {t_full_space - t_opt:.1f}s")
