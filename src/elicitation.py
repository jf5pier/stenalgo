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

from src.keyboard import Strokes
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
    reserved keys) and is not built here."""
    groups: dict[LemmaHomophoneGroupKey, list[Word]] = {}
    for strokes, words in theory.items():
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
    print("Wrote questionnaire.json")
