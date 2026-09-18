#!/usr/bin/python
# coding: utf-8
#
import math
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
from src.keyboard import Strokes
from src.word import Word, WordFeature, GramCat

NO_FEATURE = "nofeature"

# Grammatical "families" an atomic feature can belong to: two atomic features are only
# ever compared for polarity if they belong to the same family (e.g. "s" and "nbr_p" are
# both about grammatical number, "indicatif" and "présent" belong to no family and
# are always neutral toward everything).
FEATURE_FAMILIES: dict[str, str] = {
    "s": "number", "p": "number", "nbr_s": "number", "nbr_p": "number",
    "m": "gender", "f": "gender",
    "m_s": "gender_number", "f_s": "gender_number",
    "m_p": "gender_number", "f_p": "gender_number", "not_m_s": "gender_number",
    "pers_1": "person", "pers_2": "person", "pers_3": "person",
}

# Canonical value per atomic feature, used only as a fallback (see
# _computeFamilyCorrelations) for atomic-feature pairs encoded through different fields
# of Word (e.g. "s"/"p" come from the generic gender/number fields, "nbr_s"/"nbr_p" from
# parsing infoVerb) — real co-occurrence data can't say anything meaningful about such
# pairs, so the fallback encodes the hand-authored semantic identity ("s" and "nbr_s"
# both mean singular).
_VALUE_TABLES: dict[str, dict[str, str]] = {
    "number": {"s": "sing", "p": "plur", "nbr_s": "sing", "nbr_p": "plur"},
    "gender": {"m": "masc", "f": "fem"},
}

# Which field of Word each atomic feature is actually read off of. Correlation is only
# computed between atomic features sharing a notation — cross-notation presence/absence
# is dominated by which field happened to be populated for that row (e.g. most VER
# words are either a pure participle, populating gender/number, or a pure finite
# form, populating infoVerb, but rarely both), a structural artifact unrelated to
# the grammatical value itself, so it would swamp any real signal.
_ATOMIC_FEATURE_NOTATION: dict[str, str] = {
    "s": "gender_number_field", "p": "gender_number_field",
    "m": "gender_number_field", "f": "gender_number_field",
    "m_s": "gender_number_combo", "f_s": "gender_number_combo",
    "m_p": "gender_number_combo", "f_p": "gender_number_combo",
    "not_m_s": "gender_number_combo",
    "nbr_s": "verb_conjugation", "nbr_p": "verb_conjugation",
    "pers_1": "verb_conjugation", "pers_2": "verb_conjugation", "pers_3": "verb_conjugation",
}


def _familyAtomicFeatures(feature: WordFeature) -> dict[str, str]:
    """
    Every family-bearing atomic feature inside a possibly compound feature, keyed by
    family. A compound like "indicatif:pers_3:nbr_s" carries atoms from two families
    at once (person and number) since word.py combines mode/tense/person/number into
    a single ":"-joined feature.
    """
    result: dict[str, str] = {}
    for part in feature.split(":"):
        normalized = part[len("VER_"):] if part.startswith("VER_") else part
        family = FEATURE_FAMILIES.get(normalized)
        if family is not None:
            result[family] = normalized
    return result


def _computeFamilyCorrelations(words: list[Word]) -> dict[frozenset[str], float]:
    """
    Matthews correlation coefficient between every pair of atomic features belonging to
    the same family, computed over words eligible for that family (i.e. carrying any
    atomic feature from it) — this avoids spurious correlation between atomic features
    that simply never apply to the same grammatical category (e.g. a noun-only vs a
    verb-only atomic feature) rather than being truly semantically opposed.

    Correlation is only computed between atomic features that share the same
    _ATOMIC_FEATURE_NOTATION (they're read off the same field of Word, e.g. "m_s"/"f_s"
    both come from the generic gender_number combo) — restricted further to the gramCats
    where they can both actually appear, since e.g. "s"/"p" also occur on NOM/ADJ in
    addition to VER. Cross-notation pairs (e.g. "s" vs "nbr_s": one from the generic
    gender/number fields, the other parsed out of infoVerb) fall back to the
    hand-authored canonical value table instead — real presence/absence there is
    dominated by which field happened to be populated for that word (most VER words
    are either a pure participle or a pure finite form, rarely both), a structural
    artifact unrelated to the grammatical value itself, so it would swamp any
    genuine signal rather than reveal one.
    """
    atomicFeaturesByFamily: dict[str, list[str]] = {}
    for atomicFeature, family in FEATURE_FAMILIES.items():
        atomicFeaturesByFamily[family] = atomicFeaturesByFamily.get(family, []) + [atomicFeature]

    wordAtomicFeatures: list[set[str]] = [set(word.getFeatures()) for word in words]
    wordCats: list[GramCat] = [word.gramCat for word in words]
    hostCats: dict[str, set[GramCat]] = {
        atomicFeature: {cat for cat, wt in zip(wordCats, wordAtomicFeatures) if atomicFeature in wt}
        for atomicFeature in FEATURE_FAMILIES
    }

    correlations: dict[frozenset[str], float] = {}
    for family, familyAtoms in atomicFeaturesByFamily.items():
        valueTable = _VALUE_TABLES.get(family, {})
        for i, a1 in enumerate(familyAtoms):
            for a2 in familyAtoms[i:]:
                key = frozenset({a1, a2})
                sharedCats = hostCats[a1] & hostCats[a2]
                sameNotation = _ATOMIC_FEATURE_NOTATION.get(a1) == _ATOMIC_FEATURE_NOTATION.get(a2)
                if a1 == a2:
                    correlations[key] = 1.0
                elif sameNotation and sharedCats:
                    restricted = [wt for wt, cat in zip(wordAtomicFeatures, wordCats) if cat in sharedCats]
                    n11 = sum(1 for wt in restricted if a1 in wt and a2 in wt)
                    n10 = sum(1 for wt in restricted if a1 in wt and a2 not in wt)
                    n01 = sum(1 for wt in restricted if a1 not in wt and a2 in wt)
                    n00 = sum(1 for wt in restricted if a1 not in wt and a2 not in wt)
                    denom = math.sqrt((n11 + n10) * (n11 + n01) * (n00 + n10) * (n00 + n01))
                    correlations[key] = (n11 * n00 - n10 * n01) / denom if denom > 0 else 0.0
                elif a1 in valueTable and a2 in valueTable:
                    correlations[key] = 1.0 if valueTable[a1] == valueTable[a2] else -1.0
                else:
                    correlations[key] = 0.0
    return correlations


def associationScore(
        f1: WordFeature,
        f2: WordFeature,
        familyCorrelations: dict[frozenset[str], float]
    ) -> float:
    """
    +1.0 fully associated (same polarity), -1.0 fully opposed, 0.0 unrelated (no
    shared family, e.g. mode/tense atomic features, or gramCat names). When the two
    features share more than one family (e.g. "pers_3:nbr_s" vs "pers_3:nbr_p" share
    both person and number), the most opposed per-family score wins: disagreement on
    any shared dimension is enough to prefer keeping the pair apart, even if another
    shared dimension agrees.
    """
    atoms1, atoms2 = _familyAtomicFeatures(f1), _familyAtomicFeatures(f2)
    sharedFamilies = atoms1.keys() & atoms2.keys()
    if not sharedFamilies:
        return 0.0
    return min(familyCorrelations.get(frozenset({atoms1[family], atoms2[family]}), 0.0)
                for family in sharedFamilies)


def polarityAssociations(
        features: list[WordFeature],
        familyCorrelations: dict[frozenset[str], float]
    ) -> list[tuple[WordFeature, WordFeature, float]]:
    """ Every pair of features with a nonzero association score, sorted by score. """
    uniqueFeatures = sorted(set(features))
    result: list[tuple[WordFeature, WordFeature, float]] = []
    for i, f1 in enumerate(uniqueFeatures):
        for f2 in uniqueFeatures[i + 1:]:
            score = associationScore(f1, f2, familyCorrelations)
            if score != 0.0:
                result.append((f1, f2, score))
    return sorted(result, key=lambda item: (item[2], item[0], item[1]))


def _colorFeatures(
        featureSets: list[set[WordFeature]],
        penalties: list[int],
        numKeys: int,
        conflictBudget: int,
        polarityCoefficients: dict[frozenset[WordFeature], int] | None = None,
        timeLimitS: float = 30.0,
        log: bool = False
    ) -> tuple[int, bool, dict[WordFeature, int], list[int]]:
    """
    Assign every feature one of `numKeys` special keypresses. A feature set containing two
    features that share a key is flagged; flagged sets cost their penalty, and at most
    `conflictBudget` sets may be flagged. `polarityCoefficients` adds, for each pair of
    features, `coefficient * (do they end up on the same key)` to the objective
    (positive = penalty, negative = reward), independent of the conflict/budget
    mechanism above. Minimizes total cost.
    """
    polarityCoefficients = polarityCoefficients or {}
    features = sorted({f for s in featureSets for f in s} |
                       {f for pair in polarityCoefficients for f in pair})
    idx = {f: i for i, f in enumerate(features)}
    n, K = len(features), numKeys
    sets = [sorted({idx[f] for f in s}) for s in featureSets]

    model = cp_model.CpModel()
    ZERO = model.NewConstant(0)

    # ---- key assignment booleans (symmetry breaking: feature v uses keys 0..v)
    x: dict[tuple[int, int], IntVar] = {(v, c): model.NewBoolVar(f"x{v}_{c}")
         for v in range(n) for c in range(min(K, v + 1))}

    def X(v: int, c: int) -> IntVar:
        return x.get((v, c), ZERO)

    for v in range(n):
        _ = model.AddExactlyOne(X(v, c) for c in range(K))

    # ---- one conflict flag per set, wired with big-M per (set, key)
    flags: dict[int, IntVar] = {}
    for si, ids in enumerate(sets):
        if len(ids) < 2:
            continue                          # singletons can never conflict
        b = model.NewBoolVar(f"conflict{si}")
        flags[si] = b
        for c in range(K):
            # key c covers at most 1 feature of this set — unless flagged
            _ = model.Add(sum(X(v, c) for v in ids) <= 1 + (len(ids) - 1) * b)

    # ---- polarity terms: coefficient * (v1 and v2 share a key), exact AND per key
    # since the coefficient may be negative (a reward), a one-sided bound isn't
    # enough — the solver must not get the reward without actually sharing a key.
    polarityCost = []
    for pair, coefficient in polarityCoefficients.items():
        if coefficient == 0:
            continue
        v1, v2 = (idx[f] for f in pair)
        sameKey = model.NewBoolVar(f"sameKey_{v1}_{v2}")
        perKeyAnd: list[IntVar] = []
        for c in range(K):
            y = model.NewBoolVar(f"sameKeyAt_{v1}_{v2}_{c}")
            _ = model.Add(y <= X(v1, c))
            _ = model.Add(y <= X(v2, c))
            _ = model.Add(y >= X(v1, c) + X(v2, c) - 1)
            perKeyAnd.append(y)
        _ = model.Add(sameKey == sum(perKeyAnd))
        polarityCost.append(coefficient * sameKey)

    # ---- budget + objective
    _ = model.Add(sum(flags.values()) <= conflictBudget)
    model.Minimize(sum(penalties[si] * b for si, b in flags.items()) + sum(polarityCost))

    # ---- greedy warm start (may exceed the budget; CP-SAT repairs it)
    memberOf: list[list[int]] = [[] for _ in range(n)]
    for si, ids in enumerate(sets):
        for v in ids:
            memberOf[v].append(si)
    counts: list[dict[int, int]] = [{} for _ in sets]
    assign: dict[int, int] = {}
    for v in sorted(range(n), key=lambda v: -len(memberOf[v])):
        _, c = min((sum(counts[si].get(c, 0) > 0 for si in memberOf[v]), c)
                   for c in range(min(K, v + 1)))
        assign[v] = c
        for si in memberOf[v]:
            counts[si][c] = counts[si].get(c, 0) + 1
    for (v, c), var in x.items():
        _ = model.AddHint(var, int(assign[v] == c))
    for si, b in flags.items():
        _ = model.AddHint(b, int(any(cnt > 1 for cnt in counts[si].values())))

    # ---- solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeLimitS
    solver.parameters.log_search_progress = log
    status = solver.Solve(model)
    if status == cp_model.INFEASIBLE:
        raise RuntimeError("infeasible: conflict budget too small or numKeys too small")
    if status == cp_model.UNKNOWN:
        raise RuntimeError("no solution found within the time limit")

    keys: dict[WordFeature, int] = {f: next(c for c in range(min(K, idx[f] + 1))
                    if solver.BooleanValue(x[idx[f], c])) for f in features}
    conflicted = sorted(si for si, b in flags.items() if solver.BooleanValue(b))
    total = sum(penalties[si] for si in conflicted)

    return total, status == cp_model.OPTIMAL, keys, conflicted


def _minSpecialKeypressesNeeded(
        featureSets: list[set[WordFeature]],
        polarityCoefficients: dict[frozenset[WordFeature], int] | None = None,
        timeLimitS: float = 30.0,
        log: bool = False
    ) -> int:
    """ Smallest numKeys for which every feature set can be colored with zero conflicts. """
    lowerBound = max((len(s) for s in featureSets), default=0)
    penalties = [1 for _ in featureSets]
    numKeys = lowerBound
    while True:
        try:
            _colorFeatures(featureSets, penalties, numKeys, conflictBudget=0,
                          polarityCoefficients=polarityCoefficients,
                          timeLimitS=timeLimitS, log=log)
            return numKeys
        except RuntimeError:
            numKeys += 1


def satOptimizeDiscriminator(
        featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]],
        theory: dict[Strokes, list[Word]],
        numSpecialKeypresses: int | None = None,
        timeLimitS: float = 30.0,
        log: bool = False
    ) -> tuple[int, float, bool, dict[WordFeature, int], list[tuple[WordFeature, ...]]]:
    """
    Given feature sets already grouped per homophone cluster (by greedyOptimizeDiscriminator
    or the shared adaptive selection, src/featureextractor.py's buildDiscriminatorSelection),
    find the smallest subset of special keypresses that lets every feature set be fully
    distinguished (zero conflicts), or, when numSpecialKeypresses is given, minimize the total cost
    of unavoidable homophone conflicts and polarity clashes. The cost of a conflicting
    feature set is the sum of the frequencies of the words it was grouped for; the
    cost of two opposite-polarity features sharing a key is a large fixed penalty
    (and two same-polarity features sharing a key earns a small reward), scaled by
    associationScore (see polarityAssociations). `theory` is only used to compute
    family correlations for the polarity terms.
    """
    FREQUENCY_SCALE = 1_000_000
    POLARITY_PENALTY_SCALE = 1_000_000_000
    POLARITY_REWARD_SCALE = 10_000

    featureSets: list[set[WordFeature]] = []
    penalties: list[int] = []
    for featureTuple, wordTuples in featuresetWords.items():
        realFeatures = {f for f in featureTuple if f != NO_FEATURE}
        if len(realFeatures) < 2:
            continue
        featureSets.append(realFeatures)
        penalty = sum(word.frequency for wordTuple in wordTuples for word in wordTuple)
        penalties.append(round(penalty * FREQUENCY_SCALE))

    if len(featureSets) == 0:
        return 0, 0.0, True, {}, []

    allRealFeatures = sorted({f for s in featureSets for f in s})
    allWords = list({word for words in theory.values() for word in words})
    familyCorrelations = _computeFamilyCorrelations(allWords)

    polarityCoefficients: dict[frozenset[WordFeature], int] = {}
    for i, f1 in enumerate(allRealFeatures):
        for f2 in allRealFeatures[i + 1:]:
            score = associationScore(f1, f2, familyCorrelations)
            if score == 0.0:
                continue
            coefficient = round(POLARITY_PENALTY_SCALE * -score) if score < 0 \
                else round(-POLARITY_REWARD_SCALE * score)
            if coefficient != 0:
                polarityCoefficients[frozenset({f1, f2})] = coefficient

    if numSpecialKeypresses is None:
        numSpecialKeypresses = _minSpecialKeypressesNeeded(
            featureSets, polarityCoefficients=polarityCoefficients,
            timeLimitS=timeLimitS, log=log)
        conflictBudget = 0
    else:
        conflictBudget = len(featureSets)

    total, proven, keyAssignment, conflicted = _colorFeatures(
        featureSets, penalties, numSpecialKeypresses, conflictBudget,
        polarityCoefficients=polarityCoefficients, timeLimitS=timeLimitS, log=log)

    totalPenalty = total / FREQUENCY_SCALE
    conflictedFeatureSets = [tuple(sorted(featureSets[si])) for si in conflicted]

    return numSpecialKeypresses, totalPenalty, proven, keyAssignment, conflictedFeatureSets
