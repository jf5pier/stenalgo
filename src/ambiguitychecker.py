#!/usr/bin/python
# coding: utf-8
"""
Phase 0 ambiguity checker (see ROADMAP.md): measures where frequency-weighted stroke
ambiguity lives in a `theory` (as built by `Dictionary.buildTheory`), before any physical
special-key or phoneme-chord assignment is committed to.

Two independently-classified kinds of ambiguity coexist in one stroke cluster:
- same-lemma ambiguity (inflected forms of one lemma, e.g. dors/dort) — the conjugation track.
- lemma-homophone ambiguity (distinct lemmas sharing a stroke, e.g. ver/vert/verre) — the
  `*`/`#` track.

Also detects the known `aller` NOM/VER cross-grammatical-category gap (see
dictionary.py:496-505): two different-gramCat, differently-spelled readings of one bare lemma
that each land in their own singleton same-lemma group and so never trip the existing
`len(lemmeWords) > 1` discrimination trigger.

Part 2 (token-level phoneme-anchor search) discovers, rather than assumes, which physical
coda-phoneme keys are usable as a reusable "meaning anchor" per atomic grammatical token
(person, number, gender, ...) across the whole lexicon, answering ROADMAP.md's open question 6
instead of guessing at it.
"""

import os
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from src.grammar import Phoneme
from src.keyboard import Keyboard, Stroke, Strokes
from src.word import (
    Lemme, LemmeGramCat, Word, WordFeature, featureTokens, groupWordsByBareLemme, groupWordsByLemme,
)
from src.featureextractor import extractDiscriminatingFeatures
from src.greedyoptimizer import FEATURE_PRIORITY, greedyOptimizeDiscriminator


# ═══════════════════════════════════════════════════════════════════════════
# Part 1 — core classification (keyboard-free)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StrokeClusterReport:
    strokes: Strokes
    words: list[Word]
    lemmeGramCatGroups: dict[LemmeGramCat, list[Word]]
    lemmaGroups: dict[Lemme, list[Word]]
    sameLemmaAmbiguous: bool          # some lemmeGramCat group has len > 1
    lemmaHomophoneAmbiguous: bool     # >= 2 distinct bare-lemme groups present
    lemmaHomophoneLemmaCount: int
    crossCategoryClash: bool          # the aller-style bug
    crossCategoryClashLemmas: list[Lemme]
    totalFrequency: float


def detectCrossCategoryClash(words: list[Word]) -> list[Lemme]:
    """
    Group by bare `lemme` (ignoring gramCat). For any bare-lemme group spanning >= 2 distinct
    lemmeGramCat values where every sub-group is a singleton (so neither trips the existing
    len(lemmeWords) > 1 trigger used by extractDiscriminatingFeatures/greedyOptimizeDiscriminator)
    and the singleton words differ in `ortho`, flag the bare lemme. Mirrors the bug documented
    at dictionary.py:496-505 (the "aller" VER/NOM case) — only fires on the otherwise-invisible
    case; a bare lemme where some sub-group already has len > 1 is already caught elsewhere.
    """
    byLemme: dict[Lemme, dict[LemmeGramCat, list[Word]]] = defaultdict(lambda: defaultdict(list))
    for word in words:
        byLemme[word.lemme][word.lemmeGramCat].append(word)

    clashes: list[Lemme] = []
    for lemme, byLemmeGramCat in byLemme.items():
        if len(byLemmeGramCat) < 2:
            continue
        if any(len(groupWords) > 1 for groupWords in byLemmeGramCat.values()):
            continue
        orthos = {word.ortho for groupWords in byLemmeGramCat.values() for word in groupWords}
        if len(orthos) > 1:
            clashes.append(lemme)
    return clashes


def classifyStrokeCluster(strokes: Strokes, words: list[Word]) -> StrokeClusterReport:
    lemmeGramCatGroups = groupWordsByLemme(words)
    lemmaGroups = groupWordsByBareLemme(words)
    clashLemmas = detectCrossCategoryClash(words)
    return StrokeClusterReport(
        strokes=strokes,
        words=words,
        lemmeGramCatGroups=lemmeGramCatGroups,
        lemmaGroups=lemmaGroups,
        sameLemmaAmbiguous=any(len(w) > 1 for w in lemmeGramCatGroups.values()),
        lemmaHomophoneAmbiguous=len(lemmaGroups) > 1,
        lemmaHomophoneLemmaCount=len(lemmaGroups),
        crossCategoryClash=len(clashLemmas) > 0,
        crossCategoryClashLemmas=clashLemmas,
        totalFrequency=sum(word.frequency for word in words),
    )


def loadIgnoredLemmas(tsvPath: str = "resources/ambiguityIgnoreList.tsv") -> dict[str, str]:
    """
    Parse resources/ambiguityIgnoreList.tsv into a {lemme: reason} dict -- lemmas
    to drop from a cluster's words before classifying it (see that file's header
    for the reason vocabulary and rationale).
    """
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rawRows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    ignored: dict[str, str] = {}
    for row in rawRows[1:]:  # skip header
        if not row.strip():
            continue
        lemme, reason, _note = row.split("\t", 2)
        ignored[lemme] = reason
    return ignored


def classifyTheory(
    theory: dict[Strokes, list[Word]], ignoredLemmas: frozenset[str] = frozenset()
) -> dict[Strokes, StrokeClusterReport]:
    """
    Single-word clusters are trivially unambiguous and skipped -- including a
    cluster that drops to <= 1 word once `ignoredLemmas` words (see
    loadIgnoredLemmas) are filtered out.
    """
    reports: dict[Strokes, StrokeClusterReport] = {}
    for strokes, words in theory.items():
        filteredWords = [w for w in words if w.lemme not in ignoredLemmas] if ignoredLemmas else words
        if len(filteredWords) > 1:
            reports[strokes] = classifyStrokeCluster(strokes, filteredWords)
    return reports


@dataclass
class ClusterSizeDistribution:
    sameLemmaGroupSizeCounts: dict[int, int]
    sameLemmaGroupSizeFrequency: dict[int, float]
    lemmaHomophoneCountCounts: dict[int, int]
    lemmaHomophoneCountFrequency: dict[int, float]


def computeClusterSizeDistribution(
    reports: dict[Strokes, StrokeClusterReport]
) -> ClusterSizeDistribution:
    sameLemmaCounts: dict[int, int] = defaultdict(int)
    sameLemmaFreq: dict[int, float] = defaultdict(float)
    lemmaHomophoneCounts: dict[int, int] = defaultdict(int)
    lemmaHomophoneFreq: dict[int, float] = defaultdict(float)
    for report in reports.values():
        for lemmeWords in report.lemmeGramCatGroups.values():
            if len(lemmeWords) > 1:
                sameLemmaCounts[len(lemmeWords)] += 1
                sameLemmaFreq[len(lemmeWords)] += sum(word.frequency for word in lemmeWords)
        if report.lemmaHomophoneAmbiguous:
            n = report.lemmaHomophoneLemmaCount
            lemmaHomophoneCounts[n] += 1
            lemmaHomophoneFreq[n] += report.totalFrequency
    return ClusterSizeDistribution(
        sameLemmaGroupSizeCounts=dict(sameLemmaCounts),
        sameLemmaGroupSizeFrequency=dict(sameLemmaFreq),
        lemmaHomophoneCountCounts=dict(lemmaHomophoneCounts),
        lemmaHomophoneCountFrequency=dict(lemmaHomophoneFreq),
    )


def computeOverflowFrequencyMass(
    reports: dict[Strokes, StrokeClusterReport], threshold: int = 5
) -> tuple[float, float, list[Strokes]]:
    """
    Headline number 1: (overflowMass, totalLemmaHomophoneMass, overflowClusterKeys) where
    'overflow' = lemmaHomophoneLemmaCount >= threshold (default 5 -- today's */# budget gives
    4 differentiable lemmas per cluster; a 5th+ lemma is beyond that budget).
    """
    lemmaHomophoneClusters = [r for r in reports.values() if r.lemmaHomophoneAmbiguous]
    totalMass = sum(r.totalFrequency for r in lemmaHomophoneClusters)
    overflowKeys = [
        strokes for strokes, r in reports.items()
        if r.lemmaHomophoneAmbiguous and r.lemmaHomophoneLemmaCount >= threshold
    ]
    overflowMass = sum(reports[strokes].totalFrequency for strokes in overflowKeys)
    return overflowMass, totalMass, overflowKeys


# ═══════════════════════════════════════════════════════════════════════════
# Part 2 — token-level phoneme-anchor search (keyboard-needing)
# ═══════════════════════════════════════════════════════════════════════════

def buildWordToStrokes(theory: dict[Strokes, list[Word]]) -> dict[Word, Strokes]:
    return {word: strokes for strokes, words in theory.items() for word in words}


def _selectCanonicalIndex(featureSet: tuple[WordFeature, ...], wordTuples: list[tuple[Word, ...]]) -> int:
    """Mirrors assignDiscriminatorKeypresses' no-stroke pick: the member whose feature is
    most linguistically unmarked (FEATURE_PRIORITY), tie-broken by corpus frequency, needs no
    added anchor phoneme at all."""
    freqByIndex = [0.0] * len(featureSet)
    for wordTuple in wordTuples:
        for i, word in enumerate(wordTuple):
            freqByIndex[i] += word.frequency
    return max(range(len(featureSet)), key=lambda i: (FEATURE_PRIORITY.get(featureSet[i], 0), freqByIndex[i]))


def buildTokenToWords(
    augmentedTheory: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]
) -> dict[str, list[tuple[Word, WordFeature]]]:
    """
    For every non-canonical (word, feature) pair in augmentedTheory (skipping the "nofeature"
    sentinel and single-member featuresets, which have no canonical/non-canonical split),
    tokenize the feature via featureTokens and record which words carry each atomic token.
    A word whose feature is a multi-token combo ("pers_3:nbr_p") appears under each of its
    tokens.
    """
    tokenToWords: dict[str, list[tuple[Word, WordFeature]]] = defaultdict(list)
    for featureSet, wordTuples in augmentedTheory.items():
        if "nofeature" in featureSet or len(featureSet) < 2:
            continue
        canonicalIndex = _selectCanonicalIndex(featureSet, wordTuples)
        for i, feature in enumerate(featureSet):
            if i == canonicalIndex:
                continue
            for wordTuple in wordTuples:
                word = wordTuple[i]
                for token in featureTokens(feature):
                    tokenToWords[token].append((word, feature))
    return dict(tokenToWords)


def _appendCodaAddition(strokes: Strokes, additionKeys: tuple[int, ...]) -> Strokes:
    if not strokes:
        return (tuple(sorted(additionKeys)),)
    lastStroke = strokes[-1]
    newLast = tuple(sorted(set(lastStroke) | set(additionKeys)))
    return strokes[:-1] + (newLast,)


def _isFeasibleAddition(
    wordStrokes: Strokes, additionKeys: tuple[int, ...], theory: dict[Strokes, list[Word]]
) -> bool:
    if not additionKeys:
        return False
    newStrokes = _appendCodaAddition(wordStrokes, additionKeys)
    if newStrokes == wordStrokes:
        return False  # no-op: addition already covered by the word's existing coda keys
    return newStrokes not in theory


@dataclass
class TokenAnchorFeasibility:
    token: str
    feasibleSingleKeyPhonemes: list[str] = field(default_factory=list)
    feasibleComboPhonemes: list[tuple[str, str]] = field(default_factory=list)

    @property
    def infeasible(self) -> bool:
        return not self.feasibleSingleKeyPhonemes and not self.feasibleComboPhonemes


def findTokenAnchors(
    tokenToWords: dict[str, list[tuple[Word, WordFeature]]],
    theory: dict[Strokes, list[Word]],
    keyboard: Keyboard,
    comboSize: int = 2,
) -> dict[str, TokenAnchorFeasibility]:
    """
    For each atomic token, scan candidate right-hand coda phonemes:
    - Round 1: every individual coda phoneme. Feasible for the token if, applied to every
      word carrying that token (appended to the word's last-syllable coda), the resulting
      Strokes never collides with another word/cluster's existing stroke, and isn't a no-op.
    - Round 2 (only if round 1 found nothing): 2-key combos of coda phonemes, capped at
      comboSize=2 -- no further escalation in Phase 0.
    """
    wordToStrokes = buildWordToStrokes(theory)
    candidatePhonemes = list(Phoneme.consonantPhonemes)
    codaKeysOf: dict[str, tuple[int, ...]] = {}
    for phoneme in candidatePhonemes:
        strokesForPhoneme = keyboard.getStrokesOfPhoneme(phoneme, "coda")
        codaKeysOf[phoneme] = strokesForPhoneme[0] if strokesForPhoneme else ()

    results: dict[str, TokenAnchorFeasibility] = {}
    for token, wordFeaturePairs in tokenToWords.items():
        words = [word for word, _ in wordFeaturePairs]
        feasibleSingle = [
            phoneme for phoneme, keys in codaKeysOf.items()
            if keys and all(_isFeasibleAddition(wordToStrokes[word], keys, theory) for word in words)
        ]
        feasibleCombo: list[tuple[str, str]] = []
        if not feasibleSingle and comboSize >= 2:
            for p1, p2 in combinations(candidatePhonemes, 2):
                keys = tuple(sorted(set(codaKeysOf.get(p1, ())) | set(codaKeysOf.get(p2, ()))))
                if keys and all(_isFeasibleAddition(wordToStrokes[word], keys, theory) for word in words):
                    feasibleCombo.append((p1, p2))
        results[token] = TokenAnchorFeasibility(
            token=token, feasibleSingleKeyPhonemes=feasibleSingle, feasibleComboPhonemes=feasibleCombo,
        )
    return results


@dataclass
class ComposedChordReport:
    feasibleWords: list[Word] = field(default_factory=list)
    infeasibleWords: list[Word] = field(default_factory=list)


def checkComposedChords(
    tokenAnchors: dict[str, TokenAnchorFeasibility],
    tokenToWords: dict[str, list[tuple[Word, WordFeature]]],
    theory: dict[Strokes, list[Word]],
    keyboard: Keyboard,
) -> ComposedChordReport:
    """
    For words needing >1 token (e.g. pers_3 + nbr_p), compose the candidate chord as the union
    of each token's chosen anchor key(s) and verify the composed stroke is still collision-free:
    a token-pair can each be individually fine and still collide once unioned on one word, or
    collide with a same-cluster sibling. Prefers a composed multi-token chord over an arbitrary
    combo -- this is the "3rd-person-plural = 3rd-person key + plural key" preference.
    """
    wordToStrokes = buildWordToStrokes(theory)
    wordFeatureTokens: dict[Word, frozenset[str]] = {}
    for pairs in tokenToWords.values():
        for word, feature in pairs:
            wordFeatureTokens[word] = featureTokens(feature)

    report = ComposedChordReport()
    for word, tokens in wordFeatureTokens.items():
        if len(tokens) <= 1:
            continue  # single-token features are covered directly by findTokenAnchors
        anchorKeys: set[int] = set()
        allTokensAnchored = True
        for token in tokens:
            feasibility = tokenAnchors.get(token)
            if feasibility is None or feasibility.infeasible:
                allTokensAnchored = False
                break
            chosenPhoneme = (
                feasibility.feasibleSingleKeyPhonemes[0] if feasibility.feasibleSingleKeyPhonemes
                else feasibility.feasibleComboPhonemes[0][0]
            )
            keys = keyboard.getStrokesOfPhoneme(chosenPhoneme, "coda")
            if keys:
                anchorKeys.update(keys[0])
        if not allTokensAnchored or not _isFeasibleAddition(wordToStrokes[word], tuple(sorted(anchorKeys)), theory):
            report.infeasibleWords.append(word)
        else:
            report.feasibleWords.append(word)
    return report


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from src.grammar import Syllable
    from src.keyboard import Starboard
    from dictionary import Dictionary

    if os.path.exists("Dictionary.pickle"):
        with open("Dictionary.pickle", "rb") as pfile:
            dictionary = pickle.load(pfile)
            Syllable.allPhonemeCol = pickle.load(pfile)
            Syllable.phonemeColByPart = pickle.load(pfile)
            Syllable.biphonemeColByPart = pickle.load(pfile)
            Syllable.multiphonemeColByPart = pickle.load(pfile)
    else:
        dictionary = Dictionary()
        dictionary.analyseSyllabification()
        Syllable.optimizeBiphonemeOrder()
        dictionary.analyseAmbiguities()

    starboard = Starboard.fromJSONFile("starboard3h.json")
    if starboard is None:
        raise RuntimeError("starboard3h.json not found; run dictionary.py once first to generate it.")

    if os.path.exists("FirstTheory.pickle"):
        with open("FirstTheory.pickle", "rb") as pfile:
            theory = pickle.load(pfile)
    else:
        theory = dictionary.buildTheory(starboard)

    ignoredLemmas = loadIgnoredLemmas()
    reports = classifyTheory(theory, ignoredLemmas=frozenset(ignoredLemmas))
    distribution = computeClusterSizeDistribution(reports)
    overflowMass, totalLemmaHomophoneMass, overflowKeys = computeOverflowFrequencyMass(reports)
    clashes = sorted({lemme for r in reports.values() for lemme in r.crossCategoryClashLemmas})

    sameLemmaClusters = sum(1 for r in reports.values() if r.sameLemmaAmbiguous)
    lemmaHomophoneClusters = sum(1 for r in reports.values() if r.lemmaHomophoneAmbiguous)

    print("\n=== Phase 0 Ambiguity Report ===")
    print(f"Multi-word clusters:                 {len(reports)}")
    print(f"Same-lemma ambiguous clusters:        {sameLemmaClusters}")
    print(f"Lemma-homophone ambiguous clusters:   {lemmaHomophoneClusters}")
    print(f"Cross-category clashes (aller-style): {len(clashes)} found: {clashes[:20]}")
    print("\nLemma-homophone cluster size distribution:")
    for n in sorted(distribution.lemmaHomophoneCountCounts):
        marker = "  <-- OVERFLOW (beyond */# budget)" if n >= 5 else ""
        print(f"  {n} lemmas: {distribution.lemmaHomophoneCountCounts[n]} clusters,"
              f" {distribution.lemmaHomophoneCountFrequency[n]:.2f} freq mass{marker}")
    pct = 100.0 * overflowMass / totalLemmaHomophoneMass if totalLemmaHomophoneMass else 0.0
    print(f"\nOverflow frequency mass: {overflowMass:.2f} ({pct:.2f}% of lemma-homophone mass)")

    with open("ambiguity_report.tsv", "w") as f:
        _ = f.write("strokes\twordCount\torthos\tsameLemmaAmbiguous\tlemmaHomophoneLemmaCount\t"
                     "crossCategoryClash\ttotalFrequency\n")
        for strokes, r in reports.items():
            strokeString = starboard.strokesToString(strokes)
            orthos = ",".join(sorted({w.ortho for w in r.words}))
            _ = f.write(f"{strokeString}\t{len(r.words)}\t{orthos}\t{r.sameLemmaAmbiguous}\t"
                         f"{r.lemmaHomophoneLemmaCount}\t{r.crossCategoryClash}\t{r.totalFrequency}\n")

    discrimFeatureWords, orderedFeatures, _strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)
    augmentedTheory = greedyOptimizeDiscriminator(theory, discrimFeatureWords, orderedFeatures, starboard)

    tokenToWords = buildTokenToWords(augmentedTheory)
    tokenAnchors = findTokenAnchors(tokenToWords, theory, starboard)
    composedReport = checkComposedChords(tokenAnchors, tokenToWords, theory, starboard)

    print("\n=== Per-token phoneme-anchor feasibility ===")
    for token, feasibility in sorted(tokenAnchors.items()):
        if feasibility.feasibleSingleKeyPhonemes:
            print(f"  {token:>10}: single-key anchors {feasibility.feasibleSingleKeyPhonemes}")
        elif feasibility.feasibleComboPhonemes:
            print(f"  {token:>10}: combo anchors {feasibility.feasibleComboPhonemes[:5]}")
        else:
            print(f"  {token:>10}: INFEASIBLE even at combo size 2")
    print(f"\nComposed multi-token chords: {len(composedReport.feasibleWords)} feasible,"
          f" {len(composedReport.infeasibleWords)} infeasible")

    with open("anchor_feasibility.tsv", "w") as f:
        _ = f.write("token\tfeasibleSingleKeys\tfeasibleCombos\tinfeasible\n")
        for token, feasibility in sorted(tokenAnchors.items()):
            _ = f.write(f"{token}\t{','.join(feasibility.feasibleSingleKeyPhonemes)}\t"
                         f"{','.join('+'.join(c) for c in feasibility.feasibleComboPhonemes)}\t"
                         f"{feasibility.infeasible}\n")
