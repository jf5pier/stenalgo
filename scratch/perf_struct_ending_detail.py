#!/usr/bin/env python3
"""
Detail instrumentation of deriveConjugationEndingTables.
Measures theory scanning and repetitive work.
Usage: PYTHONHASHSEED=0 flock <lock> python scratch/perf_struct_ending_detail.py > scratch/perf-struct-ending-detail.log 2>&1
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import loadTheoryAndKeyboard
from src.verbparadigm import (
    deriveConjugationEndingTables, loadVerbModelExceptions, loadVerbisteTemplates,
    attestedInfinitiveWordByLemme, getTrustedTemplate, CONJUGATION_STRING_FIELDS,
    _rawInfoVerbTags, GramCat
)
from util.completeVerbParadigms import (
    VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
)
from collections import defaultdict, Counter

print("=" * 70, flush=True)
print("Instrumentation: deriveConjugationEndingTables detail", flush=True)
print("=" * 70, flush=True)

t0 = time.perf_counter()
print(f"[{time.perf_counter()-t0:.1f}s] Loading...", flush=True)
theory, _ = loadTheoryAndKeyboard()
verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugationTemplates = loadVerbisteTemplates(VERBISTE_CONJUGATIONS_PATH)
print(f"[{time.perf_counter()-t0:.1f}s] Loaded", flush=True)

# Now manually instrument the main function
print(f"\n[{time.perf_counter()-t0:.1f}s] Phase 1: attestedInfinitiveWordByLemme...", flush=True)
t_phase1 = time.perf_counter()
infinitiveByLemme = attestedInfinitiveWordByLemme(theory)
t_phase1 = time.perf_counter() - t_phase1
print(f"  Found {len(infinitiveByLemme)} infinitive lemmes in {t_phase1:.3f}s")

# Phase 2: Group infinitives by template
print(f"\n[{time.perf_counter()-t0:.1f}s] Phase 2: Group infinitives by template...", flush=True)
t_phase2 = time.perf_counter()
infinitivesByTemplate = defaultdict(list)
for lemme, donorInfinitive in infinitiveByLemme.items():
    template = getTrustedTemplate(lemme, verbisteTemplates, exceptions)
    if template is not None:
        infinitivesByTemplate[template].append(donorInfinitive)
t_phase2 = time.perf_counter() - t_phase2
print(f"  Grouped into {len(infinitivesByTemplate)} templates in {t_phase2:.3f}s")
for template, infinitiveWords in sorted(infinitivesByTemplate.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"    {template}: {len(infinitiveWords)} infinitives")

# Phase 3: Derive infinitive suffixes (using _longestCommonSuffix)
print(f"\n[{time.perf_counter()-t0:.1f}s] Phase 3: Derive infinitive suffixes...", flush=True)
t_phase3 = time.perf_counter()
infinitiveSuffixByKey = {}
for template, infinitiveWords in infinitivesByTemplate.items():
    for field in CONJUGATION_STRING_FIELDS:
        # This calls _longestCommonSuffix which iterates through the strings
        values = [getattr(w, field) for w in infinitiveWords]
        # Reimplement to measure
        if values:
            shortest = min(values, key=len)
            for length in range(len(shortest), 0, -1):
                suffix = shortest[-length:]
                if all(s.endswith(suffix) for s in values):
                    infinitiveSuffixByKey[(field, template)] = suffix
                    break
            else:
                infinitiveSuffixByKey[(field, template)] = ""
        else:
            infinitiveSuffixByKey[(field, template)] = ""
t_phase3 = time.perf_counter() - t_phase3
print(f"  Derived {len(infinitiveSuffixByKey)} suffix entries in {t_phase3:.3f}s")

# Phase 4: Main loop - scan theory to collect ending candidates
print(f"\n[{time.perf_counter()-t0:.1f}s] Phase 4: Scan theory for ending candidates...", flush=True)
t_phase4 = time.perf_counter()

candidatesByKey = defaultdict(list)
theory_scans = 0
verb_words = 0
processed_verbs = 0
for words in theory.values():
    for word in words:
        if word.gramCat != GramCat.VER:
            continue
        verb_words += 1
        # This is where most of the time should go - there are ~40k verbs
        if "inf" in _rawInfoVerbTags(word):
            continue
        template = getTrustedTemplate(word.lemme, verbisteTemplates, exceptions)
        infinitiveWord = infinitiveByLemme.get(word.lemme)
        if template is None or infinitiveWord is None:
            continue
        processed_verbs += 1
        for tag in _rawInfoVerbTags(word):
            parts = tag.split(":")
            if len(parts) != 3:
                continue
            code, personNumber = f"{parts[0]}:{parts[1]}", parts[2]
            for field in CONJUGATION_STRING_FIELDS:
                suffix = infinitiveSuffixByKey.get((field, template), "")
                infinitiveValue = getattr(infinitiveWord, field)
                radicalLen = len(infinitiveValue) - len(suffix)
                if radicalLen < 0:
                    continue
                slotValue = getattr(word, field)
                candidatesByKey[(field, template, code, personNumber)].append(slotValue[radicalLen:])

t_phase4 = time.perf_counter() - t_phase4
print(f"  Scanned {verb_words} verb words, processed {processed_verbs} for candidates in {t_phase4:.3f}s")
print(f"  Collected {sum(len(v) for v in candidatesByKey.values())} candidate endings")

# Phase 5: Compute mode for each slot
print(f"\n[{time.perf_counter()-t0:.1f}s] Phase 5: Compute mode for slot endings...", flush=True)
t_phase5 = time.perf_counter()
slotEndingByKey = {}
slotMatchRateByKey = {}
slotDonorCountByKey = {}
for key, candidates in candidatesByKey.items():
    mode, modeCount = Counter(candidates).most_common(1)[0]
    slotEndingByKey[key] = mode
    slotMatchRateByKey[key] = modeCount / len(candidates)
    slotDonorCountByKey[key] = len(candidates)
t_phase5 = time.perf_counter() - t_phase5
print(f"  Processed {len(candidatesByKey)} slot ending keys in {t_phase5:.3f}s")

print(f"\n" + "=" * 70, flush=True)
print(f"Summary of deriveConjugationEndingTables")
print(f"=" * 70, flush=True)
print(f"Phase 1 (infinitiveByLemme): {t_phase1:.3f}s")
print(f"Phase 2 (grouping): {t_phase2:.3f}s")
print(f"Phase 3 (infinitive suffixes): {t_phase3:.3f}s")
print(f"Phase 4 (theory scan): {t_phase4:.3f}s [MAIN WORKLOAD]")
print(f"Phase 5 (mode computation): {t_phase5:.3f}s")
print(f"Total: {t_phase1+t_phase2+t_phase3+t_phase4+t_phase5:.3f}s")

# Compare with actual function
print(f"\n[{time.perf_counter()-t0:.1f}s] Running actual function...", flush=True)
t_actual = time.perf_counter()
result = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
t_actual = time.perf_counter() - t_actual
print(f"  Actual function: {t_actual:.3f}s")
