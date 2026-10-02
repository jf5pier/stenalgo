#!/usr/bin/env python
# coding: utf-8
"""
Test the proposed optimization: invert wordIsDiscrminatedByFeature
dict to word->features instead of iterating feature->words for each word.
"""
import os
import sys
import time
import hashlib
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures
from src.word import groupWordsByLemme

theory, keyboard = loadTheoryAndKeyboard()
print(f"Theory: {len(theory)} strokes, ~167k words")

wordIsDiscrminatedByFeature, _, _ = extractDiscriminatingFeatures(theory)
print(f"Features: {len(wordIsDiscrminatedByFeature)}")

def buildFeasibleDiscriminatorOptions_ORIGINAL(
        theory, wordIsDiscrminatedByFeature):
    """Original implementation - nested loop over features."""
    groupFeasibleFeatures = {}
    for strokes, selectedWords in theory.items():
        wordByLemme = groupWordsByLemme(selectedWords)
        for lemme, lemmeWords in wordByLemme.items():
            if len(lemmeWords) <= 1:
                continue
            # ORIGINAL: nested comprehension - iterates features for each word
            wordFeasibleFeatures = {
                word: {
                    feature for feature, discriminatedWords in wordIsDiscrminatedByFeature.items()
                    if word in discriminatedWords
                } for word in lemmeWords
            }
            groupFeasibleFeatures[(strokes, lemme)] = wordFeasibleFeatures
    return groupFeasibleFeatures


def buildFeasibleDiscriminatorOptions_OPTIMIZED(
        theory, wordIsDiscrminatedByFeature):
    """Optimized: invert dict first, then single lookup per word."""
    # Pre-invert: word -> set[features] instead of feature -> set[words]
    word_to_features = {}
    for feature, discriminatedWords in wordIsDiscrminatedByFeature.items():
        for word in discriminatedWords:
            if word not in word_to_features:
                word_to_features[word] = set()
            word_to_features[word].add(feature)

    groupFeasibleFeatures = {}
    for strokes, selectedWords in theory.items():
        wordByLemme = groupWordsByLemme(selectedWords)
        for lemme, lemmeWords in wordByLemme.items():
            if len(lemmeWords) <= 1:
                continue
            # OPTIMIZED: single lookup per word, not per word-feature pair
            wordFeasibleFeatures = {
                word: word_to_features.get(word, set()).copy()
                for word in lemmeWords
            }
            groupFeasibleFeatures[(strokes, lemme)] = wordFeasibleFeatures
    return groupFeasibleFeatures


print("\n=== ORIGINAL ===")
t0 = time.perf_counter()
result_orig = buildFeasibleDiscriminatorOptions_ORIGINAL(theory, wordIsDiscrminatedByFeature)
t_orig = time.perf_counter() - t0
print(f"Time: {t_orig:.2f}s")
print(f"Result size: {len(result_orig)}")

print("\n=== OPTIMIZED ===")
t1 = time.perf_counter()
result_opt = buildFeasibleDiscriminatorOptions_OPTIMIZED(theory, wordIsDiscrminatedByFeature)
t_opt = time.perf_counter() - t1
print(f"Time: {t_opt:.2f}s")
print(f"Result size: {len(result_opt)}")

print(f"\n=== COMPARISON ===")
print(f"Original:  {t_orig:.2f}s")
print(f"Optimized: {t_opt:.2f}s")
print(f"Speedup:   {t_orig/t_opt:.2f}x ({100*(t_orig-t_opt)/t_orig:.1f}% faster)")

# Verify correctness: canonicalize and compare
def canonicalize(obj):
    """Convert to JSON for comparison."""
    return json.dumps(
        {str(k): list(sorted(v, key=str)) for k, v in obj.items()},
        ensure_ascii=False, default=str, sort_keys=True
    )

orig_canon = canonicalize({
    (str(s), l): {str(w): sorted(f, key=str) for w, f in byWord.items()}
    for (s, l), byWord in result_orig.items()
})
opt_canon = canonicalize({
    (str(s), l): {str(w): sorted(f, key=str) for w, f in byWord.items()}
    for (s, l), byWord in result_opt.items()
})

if orig_canon == opt_canon:
    print("\nCorrectness: PASS (output identical)")
else:
    print("\nCorrectness: FAIL (output differs)")
    # Show a small sample
    orig_hash = hashlib.sha256(orig_canon.encode()).hexdigest()[:16]
    opt_hash = hashlib.sha256(opt_canon.encode()).hexdigest()[:16]
    print(f"  Original SHA256: {orig_hash}")
    print(f"  Optimized SHA256: {opt_hash}")
