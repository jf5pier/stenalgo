#!/usr/bin/python
# coding: utf-8
"""
Phase E (see ATOMIC_KEYPRESS_REWIRE_PLAN.md) — elicitation before optimization.

E2/E3: enumerate every same-lemma homophone group (words sharing a lemma+gramCat that
also share a pronunciation, i.e. a stroke), every cross-spelling feature-combination pair
inside it, and report the resulting scale (group/pair counts, distinct feature
oppositions -- the actual number of questions a questionnaire would ask -- max compound
size, which markers are ever pressed together, and a greedy-coloring lower bound on K
computed with and without the co-occurrence ("pressed-together") requirement).

Nothing here touches the questionnaire itself (Phase E4, format open -- plan's open
decision §F) or the abstract grouping solver (Phase G). This module only measures.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from src.keyboard import Strokes, canonicalizeStrokes
from src.word import GramCat, Lemme, LemmeGramCat, Word, WordOrtho, groupWordsByLemme

LemmaHomophoneGroupKey = tuple[Strokes, LemmeGramCat]
# One grammatical reading of a homograph, as a full atom set -- the atomized counterpart
# of a WordFeature combination string (src/word.py's `combination`/`combinationStr`).
FeatureCombination = frozenset[str]


def wordFeatureCombinations(word: Word) -> list[FeatureCombination]:
    """
    Every distinct feature combination (grammatical reading) of one Word, as a full atom
    set (not the redundant subset-combinations Word.getFeatures() emits). A verb homograph
    ("parle" = ind-pres-1s/3s, subj-pres-1s/3s) yields one combination per _infoVerb
    entry; gender/number (shared across all of a Word's combinations) and the "VER" atom
    (participle vs. a same-spelled noun, e.g. "parlé") are folded into every combination,
    mirroring Word.getFeatures()' VER:gender:number compound.
    """
    genderNumberAtoms = {a for a in (word.gender, word.number) if a}
    verAtom = {"VER"} if word.gramCat == GramCat.VER and word.gender and word.number else set()
    if word._infoVerb:
        # A homograph Word can merge a participle combination ("fait" = participe passé
        # m:s) with a finite-verb combination of the SAME spelling ("fait" = "il fait",
        # ind pres 3s) -- gender/number lives on the Word, not per-combination, but only
        # the participle combination is actually about gender/number; a finite combination
        # must not inherit it just because some other combination of the same Word needs it.
        combinations_ = [
            frozenset(set(iv) | genderNumberAtoms | verAtom) if iv and iv[0] == "participe"
            else frozenset(iv)
            for iv in word._infoVerb
        ]
        # Subjonctif imparfait declared out of scope (2026-09-19): archaic/literary
        # tense, not worth a keypress or a questionnaire slot. Drop only that combination
        # -- a verb's other, in-scope combinations (indicatif, subjonctif présent, etc.)
        # stay in scope even when this one doesn't.
        combinations_ = [c for c in combinations_ if not ({"subjonctif", "imparfait"} <= c)]
        return combinations_
    return [frozenset(genderNumberAtoms)]


def buildLemmaHomophoneGroups(theory: dict[Strokes, list[Word]]) -> dict[LemmaHomophoneGroupKey, list[Word]]:
    """Every same-lemma (lemme+gramCat) homophone group of size > 1, across all strokes.
    Lemma-homophone (cross-lemma) grouping is a separate, unrelated track (the `*`/`#`
    reserved keys) and is not built here.

    `theory`'s own dict keys are the raw, order/repeat-preserving Strokes tuples
    `Dictionary.buildTheory` builds per word (useful for `strokesToString`'s
    human-readable rendering), not the physically-realized chord -- two words can
    collide on the same physical stroke while landing in different `theory` entries
    (differing key order, or one phoneme's dedicated key already covered by another
    phoneme's multi-key digraph). Regroup by the canonical (sorted, deduped) stroke
    first so those collisions are found here rather than staying invisible to
    elicitation."""
    byCanonicalStroke: dict[Strokes, list[Word]] = defaultdict(list)
    for strokes, words in theory.items():
        byCanonicalStroke[canonicalizeStrokes(strokes)].extend(words)

    groups: dict[LemmaHomophoneGroupKey, list[Word]] = {}
    for strokes, words in byCanonicalStroke.items():
        for lemme, lemmeWords in groupWordsByLemme(words).items():
            if len(lemmeWords) > 1:
                groups[(strokes, lemme)] = lemmeWords
    return groups


def featureCombinationsByOrtho(words: list[Word]) -> dict[WordOrtho, list[FeatureCombination]]:
    """Every distinct feature combination in a homophone group, grouped by spelling
    (combinations of the same spelling never compete -- only cross-spelling pairs matter
    for elicitation)."""
    byOrtho: dict[WordOrtho, list[FeatureCombination]] = defaultdict(list)
    for word in words:
        for combination in wordFeatureCombinations(word):
            if combination not in byOrtho[word.ortho]:
                byOrtho[word.ortho].append(combination)
    return dict(byOrtho)


@dataclass
class OppositionSample:
    homophoneGroupKey: LemmaHomophoneGroupKey
    orthoA: WordOrtho
    combinationA: FeatureCombination
    orthoB: WordOrtho
    combinationB: FeatureCombination


def enumerateOppositionSamples(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]]
) -> list[OppositionSample]:
    """E2: every spelling pair within each homophone group x every feature-combination
    combination -- the homograph repetition, so a homograph's several combinations each
    get sampled against every combination of every other spelling in the group."""
    samples: list[OppositionSample] = []
    for homophoneGroupKey, words in homophoneGroups.items():
        combinationsByOrtho = featureCombinationsByOrtho(words)
        orthos = sorted(combinationsByOrtho)
        if len(orthos) < 2:
            continue  # single spelling in this group: nothing to discriminate
        for orthoA, orthoB in combinations(orthos, 2):
            for combinationA in combinationsByOrtho[orthoA]:
                for combinationB in combinationsByOrtho[orthoB]:
                    samples.append(OppositionSample(homophoneGroupKey, orthoA, combinationA, orthoB, combinationB))
    return samples


def _greedyColorCount(nodes: set[str], edges: set[frozenset[str]]) -> int:
    """Welsh-Powell greedy coloring (largest-degree-first). Gives an upper bound on the
    true chromatic number in general, used here as a cheap, honest "at least roughly this
    many keypresses" estimate -- not a proof of optimality (that's Phase G's CP-SAT job)."""
    if not nodes:
        return 0
    adjacency: dict[str, set[str]] = {n: set() for n in nodes}
    for edge in edges:
        a, b = tuple(edge)
        adjacency[a].add(b)
        adjacency[b].add(a)
    order = sorted(nodes, key=lambda n: -len(adjacency[n]))
    colorOf: dict[str, int] = {}
    for node in order:
        usedColors = {colorOf[neighbor] for neighbor in adjacency[node] if neighbor in colorOf}
        color = next(c for c in range(len(nodes) + 1) if c not in usedColors)
        colorOf[node] = color
    return max(colorOf.values()) + 1


@dataclass
class ScaleReport:
    lemmaHomophoneGroupCount: int
    multiSpellingGroupCount: int
    totalPairCount: int
    distinctOppositions: set[frozenset[FeatureCombination]] = field(default_factory=set)
    tieOppositions: set[tuple[FeatureCombination, ...]] = field(default_factory=set)
    maxCompoundSize: int = 0
    coOccurrencePairs: set[frozenset[str]] = field(default_factory=set)
    singletonOppositionPairs: set[frozenset[str]] = field(default_factory=set)
    lowerBoundWithoutCoOccurrence: int = 0
    lowerBoundWithCoOccurrence: int = 0

    @property
    def distinctOppositionCount(self) -> int:
        return len(self.distinctOppositions)


def reportScale(homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]]) -> ScaleReport:
    """E3: the numbers that decide whether Phase E4's questionnaire is a short exchange
    or a serious undertaking, computed before any of it is built."""
    samples = enumerateOppositionSamples(homophoneGroups)
    multiSpellingGroups = {
        key for key, words in homophoneGroups.items() if len(featureCombinationsByOrtho(words)) > 1
    }

    distinctOppositions: set[frozenset[FeatureCombination]] = set()
    tieOppositions: set[tuple[FeatureCombination, ...]] = set()
    maxCompoundSize = 0
    coOccurrencePairs: set[frozenset[str]] = set()
    singletonOppositionPairs: set[frozenset[str]] = set()

    for sample in samples:
        maxCompoundSize = max(maxCompoundSize, len(sample.combinationA), len(sample.combinationB))
        for combination in (sample.combinationA, sample.combinationB):
            for a, b in combinations(sorted(combination), 2):
                coOccurrencePairs.add(frozenset({a, b}))
        if sample.combinationA == sample.combinationB:
            tieOppositions.add(tuple(sorted((sample.combinationA, sample.combinationB), key=sorted)))
            continue
        distinctOppositions.add(frozenset({sample.combinationA, sample.combinationB}))
        if len(sample.combinationA) == 1 and len(sample.combinationB) == 1:
            (a,), (b,) = sample.combinationA, sample.combinationB
            if a != b:
                singletonOppositionPairs.add(frozenset({a, b}))

    allAtoms: set[str] = {atom for combination in
                           {c for s in samples for c in (s.combinationA, s.combinationB)} for atom in combination}

    return ScaleReport(
        lemmaHomophoneGroupCount=len(homophoneGroups),
        multiSpellingGroupCount=len(multiSpellingGroups),
        totalPairCount=len(samples),
        distinctOppositions=distinctOppositions,
        tieOppositions=tieOppositions,
        maxCompoundSize=maxCompoundSize,
        coOccurrencePairs=coOccurrencePairs,
        singletonOppositionPairs=singletonOppositionPairs,
        lowerBoundWithoutCoOccurrence=_greedyColorCount(allAtoms, singletonOppositionPairs),
        lowerBoundWithCoOccurrence=_greedyColorCount(allAtoms, singletonOppositionPairs | coOccurrencePairs),
    )


@dataclass
class QuestionnaireItem:
    id: str
    lemma: str
    orthoA: WordOrtho
    atomsA: list[str]
    orthoB: WordOrtho
    atomsB: list[str]
    clean: bool  # both example spellings are free of same-group homograph contamination


def buildQuestionnaireItems(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]]
) -> list[QuestionnaireItem]:
    """
    Phase E4 input: one example pair per distinct opposition, chosen to avoid contaminating
    a combination's shown atoms with an unrelated combination of a same-lemma homograph
    (prefer a spelling that has only this one combination in its group) and, among equally
    clean candidates, the highest-frequency pair (most recognizable to answer against).
    """
    best: dict[
        frozenset[FeatureCombination],
        tuple[tuple[int, float], WordOrtho, FeatureCombination, WordOrtho, FeatureCombination, Lemme],
    ] = {}
    for (_strokes, lemmeGramCat), words in homophoneGroups.items():
        byOrtho = featureCombinationsByOrtho(words)
        orthos = sorted(byOrtho)
        if len(orthos) < 2:
            continue
        freqByOrtho = {ortho: max((w.frequency for w in words if w.ortho == ortho), default=0.0)
                       for ortho in orthos}
        cleanByOrtho = {ortho: len(byOrtho[ortho]) == 1 for ortho in orthos}
        for orthoA, orthoB in combinations(orthos, 2):
            for combinationA in byOrtho[orthoA]:
                for combinationB in byOrtho[orthoB]:
                    if combinationA == combinationB:
                        continue
                    key = frozenset({combinationA, combinationB})
                    cleanCount = int(cleanByOrtho[orthoA]) + int(cleanByOrtho[orthoB])
                    freqSum = freqByOrtho[orthoA] + freqByOrtho[orthoB]
                    score = (cleanCount, freqSum)
                    if key not in best or score > best[key][0]:
                        best[key] = (score, orthoA, combinationA, orthoB, combinationB, lemmeGramCat.rsplit("_", 1)[0])

    ranked = sorted(best.items(), key=lambda kv: kv[1][0][1], reverse=True)
    return [
        QuestionnaireItem(
            id=f"q{i}", lemma=lemma,
            orthoA=orthoA, atomsA=sorted(combinationA),
            orthoB=orthoB, atomsB=sorted(combinationB),
            clean=score[0] == 2,
        )
        for i, (_key, (score, orthoA, combinationA, orthoB, combinationB, lemma)) in enumerate(ranked)
    ]


@dataclass
class AnsweredOpposition:
    """One answered questionnaire item, as press-sets (Preferred synonym for the
    plan's "signature": Press-set) rather than the raw checkbox lists the artifact
    stores -- see GLOSSARY.md."""
    combinationA: FeatureCombination
    pressA: frozenset[str]
    combinationB: FeatureCombination
    pressB: frozenset[str]


AnswerByOpposition = dict[frozenset[FeatureCombination], dict[FeatureCombination, frozenset[str]]]


def buildAnswersByOpposition(
    answeredOppositions: list[AnsweredOpposition],
) -> tuple[AnswerByOpposition, list[frozenset[FeatureCombination]]]:
    """
    E5 step 1: index answered oppositions by the pair they were asked about -- not by
    either side alone. The same single combination legitimately needs a different press
    against different partners (e.g. a reading opposed only to one other combination
    somewhere may need no marker at all, yet need one when opposed to a third
    combination elsewhere); only an opposition key answered more than once with
    different press-sets is a genuine data inconsistency.

    Returns (answersByOpposition, duplicateOppositions). `duplicateOppositions` lists
    any opposition key that was answered more than once with disagreeing press-sets --
    E4's per-opposition dedup should make this impossible, but nothing enforces it
    upstream, so it is checked here rather than assumed.
    """
    entriesByKey: dict[frozenset[FeatureCombination], list[dict[FeatureCombination, frozenset[str]]]] = defaultdict(list)
    for answer in answeredOppositions:
        key = frozenset({answer.combinationA, answer.combinationB})
        entriesByKey[key].append({answer.combinationA: answer.pressA, answer.combinationB: answer.pressB})
    answersByOpposition: AnswerByOpposition = {}
    duplicateOppositions: list[frozenset[FeatureCombination]] = []
    for key, entries in entriesByKey.items():
        if all(entry == entries[0] for entry in entries):
            answersByOpposition[key] = entries[0]
        else:
            duplicateOppositions.append(key)
    return answersByOpposition, duplicateOppositions


PressByOrthoCombination = dict[tuple[WordOrtho, FeatureCombination], frozenset[str]]


def resolvePressByCombination(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]],
    answersByOpposition: AnswerByOpposition,
) -> tuple[dict[LemmaHomophoneGroupKey, PressByOrthoCombination], list[frozenset[FeatureCombination]]]:
    """
    E5/E6's shared resolution core, at COMBINATION granularity (one entry per
    (spelling, reading), not yet collapsed to a per-spelling list -- see
    `resolveGroupPressSets`, which is this plus the final per-spelling dedup, and
    `util/check_conjugation_disambiguation_order.py`, which needs this finer grain to
    check a specific READING's press against `conjugation_disambiguation_order.txt`'s
    per-combination rules (e.g. "a masculine reading's press must be empty", which a
    deduped per-spelling alternate list can't distinguish from an unrelated reading of
    the same spelling that happens to share the same press value).

    For every pair of distinct combinations actually co-present in a group, looks up
    that specific opposition's answer and unions it into each side's running
    per-(spelling, combination) press-set: a reading's full press-set within a group is
    the union of what it takes to tell its OWN combination apart from every *other
    spelling's* combinations in that same group -- scoped to the group, not a single
    universal press for the reading, since what a reading needs to contrast against
    varies group to group.

    A group needing an opposition missing from `answersByOpposition` (unanswered, or a
    duplicate -- see `buildAnswersByOpposition`) cannot be resolved and is left out of
    the first return value rather than risking a guess; its missing oppositions are
    collected in the second return value so the caller can re-ask.

    Returns (pressByOrthoCombinationByGroup, unresolvedOppositions).
    """
    pressByOrthoCombinationByGroup: dict[LemmaHomophoneGroupKey, PressByOrthoCombination] = {}
    unresolvedOppositions: list[frozenset[FeatureCombination]] = []
    for homophoneGroupKey, words in homophoneGroups.items():
        combinationsByOrtho = featureCombinationsByOrtho(words)
        orthos = sorted(combinationsByOrtho)
        if len(orthos) < 2:
            continue
        pressByOrthoCombination: dict[tuple[WordOrtho, FeatureCombination], set[str]] = {
            (ortho, combination): set()
            for ortho in orthos for combination in combinationsByOrtho[ortho]
        }
        groupIsResolvable = True
        for orthoA, orthoB in combinations(orthos, 2):
            for combinationA in combinationsByOrtho[orthoA]:
                for combinationB in combinationsByOrtho[orthoB]:
                    if combinationA == combinationB:
                        continue  # a genuine tie is unresolvable by any marker -- E3's concern, not E5's
                    oppositionKey = frozenset({combinationA, combinationB})
                    pressByCombination = answersByOpposition.get(oppositionKey)
                    if pressByCombination is None:
                        unresolvedOppositions.append(oppositionKey)
                        groupIsResolvable = False
                        continue
                    pressByOrthoCombination[(orthoA, combinationA)] |= pressByCombination[combinationA]
                    pressByOrthoCombination[(orthoB, combinationB)] |= pressByCombination[combinationB]
        if not groupIsResolvable:
            continue
        pressByOrthoCombinationByGroup[homophoneGroupKey] = {
            key: frozenset(press) for key, press in pressByOrthoCombination.items()
        }
    return pressByOrthoCombinationByGroup, unresolvedOppositions


def resolveGroupPressSets(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]],
    answersByOpposition: AnswerByOpposition,
) -> tuple[dict[LemmaHomophoneGroupKey, dict[WordOrtho, list[frozenset[str]]]], list[frozenset[FeatureCombination]]]:
    """
    E6: `resolvePressByCombination` collapsed to one spelling -> its distinct
    alternates. A spelling with several combinations (a homograph reading of itself,
    e.g. "calmez" = impératif 2p / indicatif présent 2p) keeps each combination's press
    separately rather than unioning them together: readings of the same spelling never
    conflict with each other (they produce the same output text -- see
    ATOMIC_KEYPRESS_REWIRE_PLAN.md's vocabulary section), so any ONE of them is
    independently sufficient to identify the spelling. Forcing the union would make the
    press over-specific (the calmez/`-kt` bug: `impératif` alone or `pers_2` alone each
    already separates "calmez" from every sibling spelling; requiring both is
    unnecessary). A spelling's resolved value is therefore the deduplicated LIST of its
    distinct per-combination press-sets -- almost always a single element, but with more
    than one when the spelling is itself a homograph.

    Returns (pressSetsByGroup, unresolvedOppositions).
    """
    pressByOrthoCombinationByGroup, unresolvedOppositions = resolvePressByCombination(
        homophoneGroups, answersByOpposition
    )
    pressSetsByGroup: dict[LemmaHomophoneGroupKey, dict[WordOrtho, list[frozenset[str]]]] = {}
    for homophoneGroupKey, words in homophoneGroups.items():
        pressByOrthoCombination = pressByOrthoCombinationByGroup.get(homophoneGroupKey)
        if pressByOrthoCombination is None:
            continue
        combinationsByOrtho = featureCombinationsByOrtho(words)
        pressSetsByGroup[homophoneGroupKey] = {
            ortho: sorted(
                {pressByOrthoCombination[(ortho, combination)] for combination in combinationsByOrtho[ortho]},
                key=lambda pressSet: (len(pressSet), sorted(pressSet)),
            )
            for ortho in sorted(combinationsByOrtho)
        }
    return pressSetsByGroup, unresolvedOppositions


@dataclass
class GroupConflict:
    """E5 finding: within one homophone group, two or more distinct spellings with an
    identical press-set among their (possibly several, one per reading) alternates --
    pressing that press-set would not tell you which spelling to produce. Two
    alternates of the SAME spelling landing on the same value is not a conflict (they
    already produce the same output text -- see `resolveGroupPressSets`)."""
    homophoneGroupKey: LemmaHomophoneGroupKey
    pressSet: frozenset[str]
    orthos: tuple[WordOrtho, ...]


def validateElicitation(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]],
    answersByOpposition: AnswerByOpposition,
) -> tuple[list[GroupConflict], list[frozenset[FeatureCombination]]]:
    """
    E5: resolve every group's per-spelling press-sets (`resolveGroupPressSets`) and check
    that no two DIFFERENT spellings in the same group land on the identical press-set (the
    plan's "every press implied by the data lands on exactly one spelling").

    Returns (conflicts, unresolvedOppositions).
    """
    pressSetsByGroup, unresolvedOppositions = resolveGroupPressSets(homophoneGroups, answersByOpposition)
    conflicts: list[GroupConflict] = []
    for homophoneGroupKey, pressSetByOrtho in pressSetsByGroup.items():
        orthosByPressSet: dict[frozenset[str], set[WordOrtho]] = defaultdict(set)
        for ortho, alternates in pressSetByOrtho.items():
            for pressSet in alternates:
                orthosByPressSet[pressSet].add(ortho)
        for pressSet, orthosSharingIt in orthosByPressSet.items():
            if len(orthosSharingIt) > 1:
                conflicts.append(GroupConflict(homophoneGroupKey, pressSet, tuple(sorted(orthosSharingIt))))
    return conflicts, unresolvedOppositions


def buildFrequencyByGroupOrtho(
    homophoneGroups: dict[LemmaHomophoneGroupKey, list[Word]],
    frequentWords: frozenset[str] = frozenset(),
) -> dict[LemmaHomophoneGroupKey, dict[WordOrtho, float]]:
    """Per group, each spelling's corpus frequency (max over its Word rows sharing that
    ortho -- same convention as `buildQuestionnaireItems`'s `freqByOrtho`). Feeds Phase
    G's frequency-weighted chord-size report; resolution/validation don't need this.

    `frequentWords` (pass `Dictionary.frequentWords`, the top-200 brief-candidate list)
    is zeroed out here for the same reason `dictionary.py`'s `analyseSyllabification`
    excludes it from syllable frequency stats: a top-200 word is a brief candidate --
    typed as a single whole-word shortcut stroke, not via its phonemic keypresses -- so
    it shouldn't inflate a keypress's apparent real-writing load (e.g. `ai`/`va`/`sais`,
    all top-200, would otherwise dominate the pers_1/impératif keypress's usage share)."""
    return {
        key: {ortho: (0.0 if ortho in frequentWords else
                      max((w.frequency for w in words if w.ortho == ortho), default=0.0))
              for ortho in {w.ortho for w in words}}
        for key, words in homophoneGroups.items()
    }


def serializeResolvedPressSets(
    pressSetsByGroup: dict[LemmaHomophoneGroupKey, dict[WordOrtho, list[frozenset[str]]]],
    frequencyByGroupOrtho: dict[LemmaHomophoneGroupKey, dict[WordOrtho, float]] | None = None,
) -> list[dict]:
    """
    E6: the persisted elicitation artifact that feeds Phase G (not `buildDiscriminatorSelection`'s
    output). One entry per validated (conflict-free -- callers should pass `validateElicitation`'s
    clean groups, or filter out its conflicting ones first) homophone group: its stroke/lemma key,
    every spelling's resolved press-sets (a list of alternates -- almost always one, more than one
    only for a spelling that is itself a homograph, see `resolveGroupPressSets`), and (when
    `frequencyByGroupOrtho` is given, see `buildFrequencyByGroupOrtho`) each spelling's corpus
    frequency, for Phase G's frequency-weighted chord-size report. JSON-serializable (Strokes is
    already tuple[tuple[int, ...], ...], trivially nested lists; press-sets sorted for stable diffs).
    """
    frequencyByGroupOrtho = frequencyByGroupOrtho or {}
    return [
        {
            "strokes": [list(stroke) for stroke in strokes],
            "lemmeGramCat": lemmeGramCat,
            "pressSets": {
                ortho: [sorted(pressSet) for pressSet in alternates]
                for ortho, alternates in pressSetByOrtho.items()
            },
            "frequencies": {
                ortho: frequencyByGroupOrtho.get((strokes, lemmeGramCat), {}).get(ortho, 0.0)
                for ortho in pressSetByOrtho
            },
        }
        for (strokes, lemmeGramCat), pressSetByOrtho in sorted(
            pressSetsByGroup.items(), key=lambda kv: kv[0][1]
        )
    ]


if __name__ == "__main__":
    import os
    import pickle

    from src.grammar import Syllable
    from dictionary import Dictionary
    from src.keyboard import Starboard

    if not os.path.exists("Dictionary.pickle") or not os.path.exists("FirstTheory.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to build Dictionary.pickle / FirstTheory.pickle.")

    with open("Dictionary.pickle", "rb") as pfile:
        _dictionary = pickle.load(pfile)
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)

    with open("FirstTheory.pickle", "rb") as pfile:
        theory: dict[Strokes, list[Word]] = pickle.load(pfile)

    homophoneGroups = buildLemmaHomophoneGroups(theory)
    report = reportScale(homophoneGroups)

    print("=== Phase E3 scale report ===")
    print(f"Same-lemma homophone groups (size > 1): {report.lemmaHomophoneGroupCount}")
    print(f"  ...with >= 2 distinct spellings:      {report.multiSpellingGroupCount}")
    print(f"Total cross-spelling combination pairs: {report.totalPairCount}")
    print(f"Distinct feature oppositions (questions): {report.distinctOppositionCount}")
    print(f"Tie oppositions (identical combinations, unresolvable by any marker): {len(report.tieOppositions)}")
    print(f"Max combination compound size:          {report.maxCompoundSize}")
    print(f"Markers ever pressed together (pairs):  {len(report.coOccurrencePairs)}")
    print(f"Singleton-opposition atom pairs:        {len(report.singletonOppositionPairs)}")
    print(f"Greedy-coloring K lower bound, without pressed-together rule: {report.lowerBoundWithoutCoOccurrence}")
    print(f"Greedy-coloring K lower bound, with pressed-together rule:    {report.lowerBoundWithCoOccurrence}")

    if report.tieOppositions:
        print("\nSample tie oppositions (identical atom sets across two spellings):")
        for tie in sorted(report.tieOppositions, key=lambda t: sorted(t[0]))[:10]:
            print("  ", sorted(tie[0]))

    import json

    items = buildQuestionnaireItems(homophoneGroups)
    print(f"\nQuestionnaire items: {len(items)} ({sum(1 for i in items if not i.clean)} not fully clean)")
    with open("questionnaire.json", "w", encoding="utf-8") as jf:
        json.dump([i.__dict__ for i in items], jf, ensure_ascii=False, indent=1)

    if os.path.exists("elicitation_answers.json"):
        with open("elicitation_answers.json", encoding="utf-8") as af:
            answerRecords = json.load(af)
        answeredOppositions = [
            AnsweredOpposition(
                combinationA=frozenset(rec["atomsA"]), pressA=frozenset(rec["checkedA"]),
                combinationB=frozenset(rec["atomsB"]), pressB=frozenset(rec["checkedB"]),
            )
            for rec in answerRecords
        ]
        answersByOpposition, duplicateOppositions = buildAnswersByOpposition(answeredOppositions)
        pressSetsByGroup, unresolvedOppositions = resolveGroupPressSets(homophoneGroups, answersByOpposition)
        conflicts, _ = validateElicitation(homophoneGroups, answersByOpposition)
        conflictedGroupKeys = {conflict.homophoneGroupKey for conflict in conflicts}

        print("\n=== Phase E5 validation report ===")
        print(f"Answered oppositions loaded:            {len(answeredOppositions)}")
        print(f"Duplicate oppositions (disagreeing answers for the same pair): {len(duplicateOppositions)}")
        print(f"Distinct unresolved oppositions encountered (groups containing them are skipped): "
              f"{len({tuple(sorted(k, key=sorted)) for k in unresolvedOppositions})}")
        print(f"Groups with a press-set conflict:                           {len(conflicts)}")

        if duplicateOppositions:
            print("\nDuplicate oppositions (same pair, disagreeing answers):")
            for key in sorted(duplicateOppositions, key=lambda k: sorted(sorted(c) for c in k))[:10]:
                print("  ", [sorted(c) for c in key])

        if conflicts:
            print("\nGroup conflicts (two spellings implying the identical press-set):")
            for conflict in conflicts[:10]:
                print(f"   press {sorted(conflict.pressSet) or '∅'} -> {conflict.orthos}"
                      f"  (group {conflict.homophoneGroupKey[1]})")

        # E6: persist the conflict-free, fully-resolved groups -- Phase G's actual input,
        # not buildDiscriminatorSelection's output. Conflicted/unresolved groups are left
        # out entirely rather than persisted half-wrong; they need re-asking first.
        cleanPressSetsByGroup = {
            key: pressSetByOrtho for key, pressSetByOrtho in pressSetsByGroup.items()
            if key not in conflictedGroupKeys
        }
        frequencyByGroupOrtho = buildFrequencyByGroupOrtho(homophoneGroups, frozenset(_dictionary.frequentWords))
        resolvedArtifact = serializeResolvedPressSets(cleanPressSetsByGroup, frequencyByGroupOrtho)
        with open("resolved_press_sets.json", "w", encoding="utf-8") as rf:
            json.dump(resolvedArtifact, rf, ensure_ascii=False, indent=1)
        print(f"\nWrote resolved_press_sets.json: {len(resolvedArtifact)} validated groups "
              f"(of {len(pressSetsByGroup)} resolved, {len(conflictedGroupKeys)} held back as conflicted)")
    else:
        print("\n(no elicitation_answers.json found -- skipping Phase E5 validation and E6 persistence)")
    print("Wrote questionnaire.json")
