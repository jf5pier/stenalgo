"""
B43 probe: rerun util.completeVerbParadigms's main() stage by stage, printing a
sha256 digest of every intermediate structure (an order-preserving "raw" form,
plus an outer-sorted "canon" form where relevant) plus per-stage wall time.
Run twice (PYTHONHASHSEED=0 and unpinned) and diff: the first diverging stage
localizes the hash-seed sensitivity.

Read-only: never passes --apply, writes nothing.
"""
import gc
import hashlib
import json
import os
import resource
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

t0 = time.perf_counter()


def stage(name: str) -> None:
    print(f"\n### STAGE {name}  [{time.perf_counter() - t0:8.1f}s]", flush=True)


def _wordKey(w):
    return [w.ortho, w.phonology, w.lemme, w.gramCat.name, w.gender, w.number,
            w.infoVerb or "", w.rawSyllCV, w.rawOrthosyllCV]


def digest(name: str, obj) -> None:
    raw = json.dumps(obj, ensure_ascii=False, default=str)
    print(f"DIGEST {name:42} {hashlib.sha256(raw.encode()).hexdigest()[:16]}", flush=True)


def main() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 ** 3, 4 * 1024 ** 3))
    except (ValueError, OSError):
        pass

    from util.completeVerbParadigms import (
        VERBISTE_VERBS_PATH, VERBISTE_CONJUGATIONS_PATH, EXCEPTIONS_PATH,
        findStructuralCandidates, loadTheoryAndKeyboard, temporarilyAugmented,
    )
    from src.featureextractor import buildDiscriminatorSelection, extractDiscriminatingFeatures
    from src.verbparadigm import (
        crossLemmaFeatureSetCollisions, deriveConjugationEndingTables,
        loadVerbModelExceptions, loadVerbisteTemplates, newlyCollidingLemmas,
        parseConjugationTemplates,
    )

    stage("load")
    theory, _starboard = loadTheoryAndKeyboard()
    digest("theory", [
        [str(strokes), [_wordKey(w) for w in words]]
        for strokes, words in theory.items()
    ])

    stage("verbiste")
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    digest("verbisteTemplates", sorted(verbisteTemplates.items()))
    digest("conjugationTemplates", sorted(conjugationTemplates.items()))

    stage("extract-baseline")
    baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)
    digest("orderedFeaturesSelected-raw", baselineOrdered)
    digest("orderedFeaturesSelected-canon", sorted(baselineOrdered))
    discByRaw = [[f, sorted(_wordKey(w) for w in words)] for f, words in baselineDiscBy.items()]
    digest("discBy-baseline-raw", discByRaw)
    digest("discBy-baseline-canon", sorted(discByRaw))
    del discByRaw
    sldRaw = [
        [str(strokes), lemme, [[_wordKey(w), sorted(set(feats))] for w, feats in byWord.items()]]
        for (strokes, lemme), byWord in strokeLemmeDiscriminators.items()
    ]
    digest("strokeLemmeDiscriminators-raw", sldRaw)
    digest("strokeLemmeDiscriminators-canon", sorted(sldRaw))
    del sldRaw

    stage("endingTables")
    endingTables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
    digest("endingTables-infinitiveSuffixByKey", sorted(endingTables.infinitiveSuffixByKey.items()))
    digest("endingTables-slotEndingByKey", sorted((list(k), v) for k, v in endingTables.slotEndingByKey.items()))
    digest("endingTables-slotMatchRateByKey", sorted((list(k), v) for k, v in endingTables.slotMatchRateByKey.items()))

    stage("findStructuralCandidates")
    structuralCandidates, _structuralSkipped = findStructuralCandidates(
        strokeLemmeDiscriminators, theory, verbisteTemplates, exceptions,
        conjugationTemplates, endingTables,
    )
    digest("structuralCandidates", sorted(
        [lgc, info.template, sorted(info.missingFeatures), _wordKey(g)]
        for lgc, info, g, _r in structuralCandidates
    ))
    print(f"COUNT structuralCandidates={len(structuralCandidates)}", flush=True)

    stage("selection-baseline")
    baselineFeaturesetWords = buildDiscriminatorSelection(theory, baselineDiscBy)
    fswRaw = [
        [list(fs), [[_wordKey(w) for w in wt] for wt in wts]]
        for fs, wts in baselineFeaturesetWords.items()
    ]
    digest("featuresetWords-baseline-raw", fswRaw)
    digest("featuresetWords-baseline-canon", sorted(fswRaw))
    digest("collisions-baseline", sorted(
        [list(fs), sorted(lemmas)]
        for fs, lemmas in crossLemmaFeatureSetCollisions(baselineFeaturesetWords).items()
    ))
    del fswRaw, baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators
    gc.collect()

    stage("extract+selection-augmented")
    with temporarilyAugmented(theory, structuralCandidates):
        augmentedDiscBy, _augOrdered, _augSld = extractDiscriminatingFeatures(theory)
        augmentedFeaturesetWords = buildDiscriminatorSelection(theory, augmentedDiscBy)
    del augmentedDiscBy
    gc.collect()
    fswAug = [
        [list(fs), [[_wordKey(w) for w in wt] for wt in wts]]
        for fs, wts in augmentedFeaturesetWords.items()
    ]
    digest("featuresetWords-augmented-raw", fswAug)
    digest("featuresetWords-augmented-canon", sorted(fswAug))
    digest("collisions-augmented", sorted(
        [list(fs), sorted(lemmas)]
        for fs, lemmas in crossLemmaFeatureSetCollisions(augmentedFeaturesetWords).items()
    ))
    del fswAug
    gc.collect()

    stage("newlyCollidingLemmas")
    newlyColliding = newlyCollidingLemmas(baselineFeaturesetWords, augmentedFeaturesetWords)
    digest("newlyCollidingLemmas", sorted(newlyColliding))
    print(f"COUNT newlyCollidingLemmas={len(newlyColliding)}", flush=True)

    confirmed = [c for c in structuralCandidates if c[0] in newlyColliding]
    flagged = sorted({c[0] for c in confirmed})
    digest("confirmedLemmas", flagged)
    print(f"COUNT confirmedCandidates={len(confirmed)} COUNT flaggedLemmas={len(flagged)}", flush=True)

    stage("done")


if __name__ == "__main__":
    main()
