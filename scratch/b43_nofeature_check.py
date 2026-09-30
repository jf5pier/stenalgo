"""B43 amplifier check: is the ~2,000-lemma 'newly colliding' set just the
("nofeature",) mega-key churning? Prints the top feature-set keys by lemma
count, baseline vs augmented (seed 0, same stages as the appender).

Usage: PYTHONHASHSEED=0 python scratch/b43_nofeature_check.py
"""
import gc
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.completeVerbParadigms import (
    EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH, VERBISTE_VERBS_PATH,
    findStructuralCandidates, loadTheoryAndKeyboard, temporarilyAugmented,
)
from src.featureextractor import buildDiscriminatorSelection, extractDiscriminatingFeatures
from src.verbparadigm import (
    crossLemmaFeatureSetCollisions, deriveConjugationEndingTables,
    loadVerbModelExceptions, loadVerbisteTemplates, newlyCollidingLemmas,
    parseConjugationTemplates,
)


def topKeys(featuresetWords, label):
    collisions = crossLemmaFeatureSetCollisions(featuresetWords)
    print(f"\n{label}: {len(featuresetWords)} feature-set keys, {len(collisions)} colliding keys")
    for fs, lemmas in sorted(collisions.items(), key=lambda kv: -len(kv[1]))[:5]:
        print(f"  {len(lemmas):5d} lemmas  key={fs}")
    return collisions


theory, _ = loadTheoryAndKeyboard()
templates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
conjugations = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
discBy, _, sld = extractDiscriminatingFeatures(theory)
tables = deriveConjugationEndingTables(theory, templates, exceptions)
candidates, _ = findStructuralCandidates(sld, theory, templates, exceptions, conjugations, tables)

baseline = buildDiscriminatorSelection(theory, discBy)
baseColl = topKeys(baseline, "BASELINE")
del discBy, sld
gc.collect()

with temporarilyAugmented(theory, candidates):
    augDiscBy, _, _ = extractDiscriminatingFeatures(theory)
    augmented = buildDiscriminatorSelection(theory, augDiscBy)
augColl = topKeys(augmented, "AUGMENTED")

newly = newlyCollidingLemmas(baseline, augmented)
print(f"\nnewlyCollidingLemmas: {len(newly)}")

# How much of `newly` is explained by the biggest colliding key alone?
biggest = max(augColl.items(), key=lambda kv: len(kv[1]))
bigLemmas = biggest[1]
print(f"biggest augmented key {biggest[0]}: {len(bigLemmas)} lemmas; "
      f"{len(newly & bigLemmas)} of the {len(newly)} newly-colliding lemmas are in it")
inBase = len(bigLemmas & baseColl.get(biggest[0], set()))
print(f"that key's lemma count in baseline: {inBase} "
      f"(diff {len(bigLemmas) - inBase} = lemmas that joined it in the augmented pass)")
