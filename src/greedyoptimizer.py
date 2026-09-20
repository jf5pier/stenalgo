#!/usr/bin/python
# coding: utf-8
#
from itertools import combinations
from src.keyboard import Keyboard, Stroke, Strokes
from src.word import (
    Word, WordFeature, LemmeGramCat, WordOrtho, groupWordsByLemme,
    atomicFeatures, ATOMIC_FEATURE_CONFLICTS,
)
from tqdm import tqdm
from collections import defaultdict

# Linguistic markedness priority for no-stroke / simple-stroke assignment.
# Higher value = more "unmarked" in French grammar = preferred for no-stroke.
# Features absent from this table default to 0 (frequency breaks the tie).
FEATURE_PRIORITY: dict[WordFeature, int] = {
    # ── Gender / number ──────────────────────────────────────────────────────
    # Masculine singular is the canonical citation form in French
    "m:s":      95,
    "m":        85,
    "s":        80,
    "nbr_s":    75,   # singular in verb context
    "not_m_s":  30,   # negation of canonical → below average
    "f:s":      45,
    "f":        40,
    "p":        20,
    "nbr_p":    15,
    "m:p":      10,
    "f:p":       5,
    # VER + gender/number combinations (participe passé agreement)
    "VER:m:s":  90,
    "VER:f:s":  40,
    "VER:m:p":  15,
    "VER:f:p":   5,
    # ── Verb modes ────────────────────────────────────────────────────────────
    "indicatif":    90,
    "infinitif":    75,
    "participe":    60,
    "conditionnel": 35,
    "subjonctif":   25,
    "impératif":    20,
    # ── Verb tenses ───────────────────────────────────────────────────────────
    "présent":   85,
    "passé":     50,
    "imparfait": 40,
    "future":    30,
    # ── Verb person ───────────────────────────────────────────────────────────
    "pers_3":    70,
    "pers_1":    55,
    "pers_2":    45,
}

# Grammatical-category priority for the `*`/`#` cross-lemma/cross-category marking
# rule (see RESUME_2026-09-20-starhash-priority.md's regret-minimization design).
# Higher value = more canonical/unmarked, same convention as FEATURE_PRIORITY above.
# Fitted on the residual population left after that design's ratio-10x exemption and
# homograph exclusion are applied -- a single consistent linear order (`ADV > PRO:pos
# > NOM > VER > ADJ > ADJ:pos`) that reproduces every observed category-pair-type's
# regret-optimal marking direction. Categories absent here weren't observed in that
# residual; src/ambiguitychecker.py's decideStarHashMark falls back to per-pair
# frequency when either side is missing from this table.
GRAMCAT_PRIORITY: dict[str, int] = {
    "ADV":     50,
    "PRO:pos": 40,
    "NOM":     30,
    "VER":     20,
    "ADJ":     10,
    "ADJ:pos":  0,
}


def _consistencyScore(
    f: WordFeature,
    stroke: Stroke,
    keyToFeatures: dict[int, list[WordFeature]],
    atomicFeatureCache: dict[WordFeature, frozenset[str]]
) -> float:
    """Score how semantically consistent assigning feature f to stroke is.
    Shared atomic features with features already on each key score positively;
    conflicting atomic features score negatively."""
    fAtoms = atomicFeatureCache[f]
    score = 0.0
    for key in stroke:
        for ef in keyToFeatures.get(key, []):
            eAtoms = atomicFeatureCache[ef]
            score += len(fAtoms & eAtoms) * 2.0
            for atom in fAtoms:
                if ATOMIC_FEATURE_CONFLICTS.get(atom) in eAtoms:
                    score -= 3.0
    return score

verboseLemmes: list[str] = [] # ["fait", "faire"]
verboseWords: list[str] = [] # ["fais", "fait", "faits", "faites"]

def greedyOptimizeDiscriminator (
        theory: dict[Strokes, list[Word]],
        wordIsDiscrminatedByFeature: dict[WordFeature, set[Word]],
        orderedFeaturesSelected: list[WordFeature],
        keyboard: Keyboard
    ) -> dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]:
    """
    """
    featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]] = {}
    for strokes, selectedWords in tqdm(theory.items(), desc="Grouping words by feature set",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[LemmeGramCat, list[Word]] = groupWordsByLemme(selectedWords)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                print(strokes, "\n   ",  [w.ortho for w in selectedWords])
                print("   ", [w.ortho for w in lemmeWords])
                for w in selectedWords:
                    print(w.ortho, "\n   ", w.getFeatures())
                # sys.exit(1)
            # Only interested in discriminating features if there are multiple words for the same lemme
            if len(lemmeWords) > 1:
                selectedFeatureWord: list[tuple[WordFeature, Word]] = []
                wordsToAssignToFeature: list[Word] = lemmeWords[:]
                possibleFeatures = orderedFeaturesSelected[:]
                while len(wordsToAssignToFeature) > 0:
                    if len(possibleFeatures) == 0:
                        # Ran out of features to try
                        while(len(wordsToAssignToFeature) > 0):
                            word = wordsToAssignToFeature.pop(0)
                            selectedFeatureWord.append(("nofeature", word))
                            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                                print("   !No feature found for word", word.ortho)
                        continue
                    # Go through the features from the most popular to the least
                    feature = possibleFeatures.pop(0)
                    for wi, word in enumerate(wordsToAssignToFeature):
                        if word in wordIsDiscrminatedByFeature[feature]:
                            selectedFeatureWord.append((feature, word))
                            _ = wordsToAssignToFeature.pop(wi)
                            # Other words sharing the same orthograph are also discriminated by the more popular feature
                            # Remove them from the list of words to assign to a feature
                            wordsToAssignToFeature = [w for w in wordsToAssignToFeature
                                if w.ortho != word.ortho]
                            break
                featureSet: tuple[WordFeature, ...] = tuple(fw[0] for fw in selectedFeatureWord)
                featuresetWords[featureSet] = featuresetWords.get(featureSet, []) \
                    + [tuple(fw[1] for fw in selectedFeatureWord)]

    featuresetWords = {
        fs:ws for fs, ws in sorted(featuresetWords.items(), key=lambda item: len(item[1]),
                                   reverse=True)
    }
    
    print(f"{len(featuresetWords)} different feature sets found.")
    for f1, (featureset, words) in list(enumerate(featuresetWords.items()))[:20]:
        if True: #"nofeature" in featureset:
            print(f"{f1}. Feature set is used to discriminate {len(words)} words:")
            print(f"".join([f"{f:>15} " for f in featureset]))
            debugFeatureNb = 9
            #nbPrint = -1 if f1 == debugFeatureNb else 5
            nbPrint = 5
            grepWords: list[str] = []
            for wordTuple in words[:nbPrint]:
                if f1 == 9 :
                    grepWords += [wordTuple[-1].ortho]
                    orthoER = wordTuple[-1].ortho
                    orthoEZ: WordOrtho = orthoER[:-1] + "z"
                    #print(f"untracked_src/copyLineFromTo.py resources/Lexique383.tsv 2 0 3 {orthoER} VER {orthoEZ} VER 6 1 17 22 23 24 26")
                    #print(f"untracked_src/copyLineFromTo.py resources/LexiqueInfraCorrespondance.tsv 2 0 2 {orthoER} VER {orthoEZ} VER 3 1 -4 5")
                #else :
                print(f"".join([f"{word.ortho:>15} " for word in wordTuple]))
            #print("egrep \"" + "|".join([f"^{w[:-1]}[rz]\\b" for w in grepWords]) +'"')

            #        "  ", 'egrep "' + "|".join([f"^{w.ortho}\\b" for w in wordTuple]) +'"')
            # print('egrep "' + "|".join([f"^{w.ortho}\\b" for wordTuple in words for w in wordTuple]) +'"')

    # print("Most popular features:")
    # print("\n".join([f"{feature}: {len(words)} words" for feature, words in sorted(wordsUsingFeature.items(), key=lambda item: len(item[1]), reverse=True)]))

    return featuresetWords


def _buildStrokePool(keyboard: Keyboard) -> list[Stroke]:
    """Return all subsets of reserved keys (including the empty 'no stroke'), cheapest-first.
    The empty tuple () represents no modifier key and is always first (cost 0)."""
    reservedKeys: list[int] = getattr(keyboard, '_reservedKeys', [0, 1, 10, 15])
    pool: list[Stroke] = [()]  # "no stroke" is always the cheapest option
    real: list[Stroke] = []
    for n in range(1, len(reservedKeys) + 1):
        for combo in combinations(sorted(reservedKeys), n):
            real.append(combo)
    costOf: dict[Stroke, int] = {
        s: cost for s in real if (cost := keyboard.getStrokeCost(s, "onset")) is not None
    }
    real = sorted(costOf, key=lambda s: costOf[s])
    return pool + real


def assignDiscriminatorKeypresses(
    augmentedTheory: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]],
    keyboard: Keyboard
) -> dict[Stroke, list[WordFeature]]:
    """
    Greedily assigns physical strokes to discriminating features.
    A stroke may be shared by multiple non-co-occurring features.

    The empty stroke () ("no stroke") is reserved for the most frequent features,
    as an independent set in the co-occurrence graph — a feature always gets the
    same stroke across all featuresets it appears in.

    Stroke reuse prefers semantic consistency: keys already associated with "plural"
    features will not be reused for "singular" features.

    Returns a mapping stroke → [features it represents].
    """
    # ── Stroke pool ────────────────────────────────────────────────────────────
    pool = _buildStrokePool(keyboard)
    poolOrder: dict[Stroke, int] = {s: i for i, s in enumerate(pool)}

    # ── Coverable featuresets (no "nofeature") ─────────────────────────────────
    coverableFS: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]] = {
        fs: wts for fs, wts in augmentedTheory.items() if "nofeature" not in fs
    }
    totalWordGroups = sum(len(wts) for wts in coverableFS.values())

    allFeatures: set[WordFeature] = set()
    for fs in coverableFS:
        allFeatures.update(fs)

    # ── Phase 1: Greedy N-1 AND-set-cover feature selection ────────────────────
    def marginal_gain(f: WordFeature, assignedSet: set[WordFeature]) -> int:
        gain = 0
        for fs, wts in coverableFS.items():
            if f not in fs:
                continue
            N = len(fs)
            others = sum(1 for x in fs if x != f and x in assignedSet)
            if others == N - 2:   # adding f reaches the N-1 threshold
                gain += len(wts)
        return gain

    def bootstrap_gain(f: WordFeature, assignedSet: set[WordFeature]) -> int:
        """Secondary gain for N>=3 featuresets with no features assigned yet.
        Selecting f enables future marginal gains from those featuresets."""
        return sum(
            len(wts) for fs, wts in coverableFS.items()
            if f in fs
            and len(fs) >= 3
            and not any(x in assignedSet for x in fs)
        )

    assigned: list[WordFeature] = []
    assignedSet: set[WordFeature] = set()
    gainHistory: list[int] = []
    cumulHistory: list[float] = []
    cumul = 0

    while True:
        bestF: WordFeature | None = None
        bestGain = 0
        for f in allFeatures - assignedSet:
            g = marginal_gain(f, assignedSet)
            if g > bestGain:
                bestGain = g
                bestF = f
        if bestGain == 0:
            # Bootstrap: no immediate gain, but N>=3 featuresets may need priming.
            for f in allFeatures - assignedSet:
                g = bootstrap_gain(f, assignedSet)
                if g > bestGain:
                    bestGain = g
                    bestF = f
        if bestGain == 0 or bestF is None:
            break
        assigned.append(bestF)
        assignedSet.add(bestF)
        cumul += bestGain
        gainHistory.append(bestGain)
        cumulHistory.append(100.0 * cumul / totalWordGroups if totalWordGroups else 0.0)

    # Phase 1 info per feature (for diagnostics)
    phase1Round: dict[WordFeature, int] = {f: i + 1 for i, f in enumerate(assigned)}
    gainByFeature: dict[WordFeature, int] = dict(zip(assigned, gainHistory))
    cumulByFeature: dict[WordFeature, float] = dict(zip(assigned, cumulHistory))

    # ── Build co-occurrence graph ──────────────────────────────────────────────
    # Edge F1–F2 if they appear in the same featureset (they can't share a stroke).
    coOccurs: dict[WordFeature, set[WordFeature]] = {f: set() for f in assigned}
    for fs in coverableFS:
        fsSelected = [f for f in fs if f in coOccurs]
        for i, f1 in enumerate(fsSelected):
            for f2 in fsSelected[i + 1:]:
                coOccurs[f1].add(f2)
                coOccurs[f2].add(f1)

    # ── Phase 0: No-stroke identification ─────────────────────────────────────
    # Compute global frequency score per feature using positional correspondence:
    # feature at index i in featureset ↔ word at index i in each word tuple.
    featureFreqScore: dict[WordFeature, float] = {f: 0.0 for f in assignedSet}
    for fs, wordTuples in coverableFS.items():
        for i, feat in enumerate(fs):
            if feat in featureFreqScore:
                for wordTuple in wordTuples:
                    if i < len(wordTuple):
                        featureFreqScore[feat] += wordTuple[i].frequency

    def featureSortKey(f: WordFeature) -> tuple[int, float]:
        """Primary: FEATURE_PRIORITY (linguistic markedness). Secondary: corpus frequency."""
        return (FEATURE_PRIORITY.get(f, 0), featureFreqScore[f])

    # Greedy independent-set: no two no-stroke features may co-occur in the same
    # featureset (otherwise two words in that group would both map to "no stroke").
    noStrokeFeatures: set[WordFeature] = set()
    for f in sorted(assignedSet, key=featureSortKey, reverse=True):
        if not any(other in noStrokeFeatures for other in coOccurs[f]):
            noStrokeFeatures.add(f)

    # ── Phase 2: Consistency-aware stroke assignment ────────────────────────────
    # Process no-stroke features first (they get ()), then by markedness priority.
    assignedSorted = sorted(
        assigned,
        key=lambda f: (f not in noStrokeFeatures, *(-x for x in featureSortKey(f)))
    )

    atomicFeatureCache: dict[WordFeature, frozenset[str]] = {f: atomicFeatures(f) for f in assigned}
    strokeToFeatures: dict[Stroke, list[WordFeature]] = {}
    featureToStroke: dict[WordFeature, Stroke] = {}
    keyToFeatures: dict[int, list[WordFeature]] = {}
    allocatedStrokes: set[Stroke] = set()

    for f in assignedSorted:
        # Compatible existing strokes (graph-coloring constraint: no co-occurrence)
        compatible: list[Stroke] = [
            stroke for stroke, feats in strokeToFeatures.items()
            if not any(ef in coOccurs[f] for ef in feats)
        ]
        # Also offer the cheapest not-yet-allocated stroke from the pool
        for s in pool:
            if s not in allocatedStrokes:
                if s not in compatible:
                    compatible.append(s)
                break

        if not compatible:
            print(f'  WARNING: No more strokes in pool for feature "{f}"')
            continue

        # No-stroke features strongly prefer ()
        if f in noStrokeFeatures and () in compatible:
            chosen: Stroke = ()
        else:
            chosen = min(
                compatible,
                key=lambda s: (-_consistencyScore(f, s, keyToFeatures, atomicFeatureCache),
                               poolOrder.get(s, len(pool)))
            )

        if chosen not in strokeToFeatures:
            allocatedStrokes.add(chosen)
            strokeToFeatures[chosen] = []

        strokeToFeatures[chosen].append(f)
        featureToStroke[f] = chosen
        for key in chosen:
            keyToFeatures.setdefault(key, []).append(f)

    # ── Diagnostic output ──────────────────────────────────────────────────────
    print("\nFeature keypress assignment (sorted by frequency, * = no-stroke feature):")
    for f in assignedSorted:
        stroke = featureToStroke.get(f)
        strokeStr = str(stroke) if stroke is not None else "[unassigned]"
        if stroke == ():
            tag = "[no stroke]"
        elif stroke is not None and stroke in strokeToFeatures:
            tag = "[new]    " if strokeToFeatures[stroke][0] == f else "[reused] "
        else:
            tag = "[?]      "
        p1 = phase1Round.get(f, -1)
        gain = gainByFeature.get(f, 0)
        cumPct = cumulByFeature.get(f, 0.0)
        marker = "*" if f in noStrokeFeatures else " "
        print(f'  P1-{p1:2d}{marker}: feature "{f:35s}" → {strokeStr:14s} {tag}  +{gain:6d}  cumul {cumPct:.1f}%')

    print("\nFeatureset → stroke(s) example:")
    for fs, wordTuples in augmentedTheory.items():
        strokes = [featureToStroke.get(f) for f in fs if f in featureToStroke]
        strokeStr = str(strokes) if strokes else "[none]"
        exampleWords = tuple(w.ortho for w in wordTuples[0]) if wordTuples else ()
        print(f'  {str(fs):60s} → {strokeStr:20s}  e.g. {exampleWords}')

    nofeatureCount = sum(len(wts) for fs, wts in augmentedTheory.items() if "nofeature" in fs)
    uncoveredCount = sum(
        len(wts) for fs, wts in coverableFS.items()
        if sum(1 for f in fs if f in assignedSet) < len(fs) - 1
    )
    print(f"\nDistinct strokes used: {len(strokeToFeatures)}")
    print(f"No-stroke features ({len(noStrokeFeatures)}): {sorted(noStrokeFeatures)}")
    print(f"Unresolved exceptions (nofeature or zero-gain): {nofeatureCount + uncoveredCount} word groups")

    return strokeToFeatures
