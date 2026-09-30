#!/usr/bin/env python
# coding: utf-8
"""
Line-level instrumentation of buildFeasibleDiscriminatorOptions hot loop.
Shows iteration counts and timing per major section.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.featureextractor import extractDiscriminatingFeatures
from src.word import groupWordsByLemme

theory, keyboard = loadTheoryAndKeyboard()
print(f"Theory: {len(theory)} strokes, ~167k words")

# Get the discriminator map
wordIsDiscrminatedByFeature, _, _ = extractDiscriminatingFeatures(theory)
print(f"Features: {len(wordIsDiscrminatedByFeature)}")
print(f"Total word-feature pairs: {sum(len(ws) for ws in wordIsDiscrminatedByFeature.values())}")

# Instrument the loop
t0 = time.perf_counter()
iterations = 0
hash_calls = 0
set_membership_tests = 0
lemmes_with_multiple = 0
total_words_in_groups = 0

# Simulate the inner dict comprehension with timing
for strokes, selectedWords in theory.items():
    wordByLemme = groupWordsByLemme(selectedWords)
    for lemme, lemmeWords in wordByLemme.items():
        if len(lemmeWords) <= 1:
            continue
        lemmes_with_multiple += 1
        total_words_in_groups += len(lemmeWords)

        # This is the hot nested comprehension (lines 212-217)
        # Instead of running it, just count operations
        for word in lemmeWords:
            for feature, discriminatedWords in wordIsDiscrminatedByFeature.items():
                # This line calls word.__hash__() once per feature per word
                set_membership_tests += 1
                # The actual check: "if word in discriminatedWords" requires hash

elapsed = time.perf_counter() - t0
print(f"\n[TIMING] Counting loop: {elapsed:.2f}s")
print(f"  Lemme groups with multiple words: {lemmes_with_multiple}")
print(f"  Total words across groups: {total_words_in_groups}")
print(f"  Set membership tests (word in feature_set): {set_membership_tests:,}")
print(f"  Est. hash calls: {set_membership_tests:,} (one per set lookup)")

# Now calculate current complexity
num_features = len(wordIsDiscrminatedByFeature)
print(f"\nComplexity analysis:")
print(f"  Lemme groups: {lemmes_with_multiple}")
print(f"  Avg words/group: {total_words_in_groups / lemmes_with_multiple:.1f}")
print(f"  Features: {num_features}")
print(f"  Total lookups: {set_membership_tests:,}")
print(f"  Word hash cost per lookup: ~86 ns (from profiler)")
print(f"  Expected hash time: {set_membership_tests * 86e-9:.1f}s")

# Now measure the optimized approach: invert the dict
print(f"\n[OPTIMIZE] Building inverted word->feature mapping...")
t_inv = time.perf_counter()
word_to_features = {}
for feature, discriminatedWords in wordIsDiscrminatedByFeature.items():
    for word in discriminatedWords:
        if word not in word_to_features:
            word_to_features[word] = set()
        word_to_features[word].add(feature)
t_inv_elapsed = time.perf_counter() - t_inv
print(f"  Inversion time: {t_inv_elapsed:.2f}s")
print(f"  Words with features: {len(word_to_features)}")

# Now rerun the loop using the inverted map
t_opt = time.perf_counter()
lemmes_with_multiple_opt = 0
total_words_in_groups_opt = 0
lookups_avoided = 0

for strokes, selectedWords in theory.items():
    wordByLemme = groupWordsByLemme(selectedWords)
    for lemme, lemmeWords in wordByLemme.items():
        if len(lemmeWords) <= 1:
            continue
        lemmes_with_multiple_opt += 1
        total_words_in_groups_opt += len(lemmeWords)

        # Optimized: just do set lookup in inverted map
        wordFeasibleFeatures = {
            word: word_to_features.get(word, set()).copy()
            for word in lemmeWords
        }
        # Count lookups (one per word, not per word-feature pair)
        lookups_avoided += len(lemmeWords) * (num_features - 1)

t_opt_elapsed = time.perf_counter() - t_opt
print(f"\n[OPTIMIZED LOOP] time: {t_opt_elapsed:.2f}s")
print(f"  Lookups reduced: {lookups_avoided:,}")
print(f"  Expected time saved: {lookups_avoided * 86e-9:.1f}s")

print(f"\n[SUMMARY]")
print(f"  Current buildFeasibleDiscriminatorOptions: 11.4s (measured)")
print(f"  Hash-only time (27.8M lookups * 86ns): ~2.4s")
print(f"  Estimated speedup if we eliminate nested feature iteration: 2.4s saved")
print(f"  New estimate: 11.4 - 2.4 = ~9.0s")
