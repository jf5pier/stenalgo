#!/usr/bin/python
# coding: utf-8
"""
Phase 0 ambiguity checker (see ROADMAP.md): measures where frequency-weighted stroke
ambiguity lives in a `theory` (as built by `Dictionary.buildTheory`), before any physical
special-keypress or phoneme-chord assignment is committed to.

Two independently-classified kinds of ambiguity coexist in one stroke cluster:
- same-lemma ambiguity (inflected forms of one lemma, e.g. dors/dort) — the conjugation track.
- lemma-homophone ambiguity (distinct lemmas sharing a stroke, e.g. ver/vert/verre) — the
  `*`/`#` track.

Also detects the known `aller` NOM/VER cross-grammatical-category gap (see
dictionary.py:496-505): two different-gramCat, differently-spelled readings of one bare lemma
that each land in their own singleton same-lemma group and so never trip the existing
`len(lemmeWords) > 1` discrimination trigger.

Part 2 (atomic-feature phoneme-keypress search) discovers, rather than assumes, which physical
coda-phoneme keys are usable as a reusable "feature keypress" per atomic grammatical feature
(person, number, gender, ...) across the whole lexicon, answering ROADMAP.md's open question 6
instead of guessing at it.
"""

import os
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cmp_to_key
from itertools import combinations
from typing import TypeVar

from src.grammar import Phoneme
from src.keyboard import Keyboard, Stroke, Strokes, canonicalizeStrokes
from src.word import (
    Lemme, LemmeGramCat, Word, WordFeature, atomicFeatures, groupWordsByBareLemme, groupWordsByLemme,
)
from src.featureextractor import buildDiscriminatorSelection
from src.greedyoptimizer import FEATURE_PRIORITY, GRAMCAT_PRIORITY


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


# ═══════════════════════════════════════════════════════════════════════════
# `*`/`#` marking rule (see RESUME_2026-09-20-starhash-priority.md) -- decides,
# for a clashing pair (bucket 2's crossCategoryClashCollisions or bucket 3's
# crossLemmaCollisions, both produced by realizeKeypressGroupsAsExtraStroke),
# which side needs the extra disambiguating stroke.
# ═══════════════════════════════════════════════════════════════════════════

RATIO_EXEMPTION_THRESHOLD = 10.0


def loadReform1990DoubletPairs(tsvPath: str = "resources/reform1990.tsv") -> frozenset[frozenset[str]]:
    """
    Parses resources/reform1990.tsv into a set of {oldSpelling, newSpelling} pairs --
    genuine same-word pre/post-1990-reform spelling doublets, not real lexical
    ambiguity (Rule 3 from RESUME_2026-09-20-starhash-priority.md: the earlier
    collision-count heuristic version of this rule was tested and disproven against
    real Google Ngram data; this cross-references the file's own sourced, OQLF- and
    Journal-officiel-verified pair list instead). Rows flagged `isException=True` are
    excluded -- the file's own notes document these as colliding with a genuinely
    distinct, unrelated word (e.g. `fût`/`fut`, `croît`/`croit`) despite being a reform
    pair, so they are NOT safe doublet exemptions.
    """
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    header = rows[0].split("\t")
    columnIndex = {name: i for i, name in enumerate(header)}
    pairs: set[frozenset[str]] = set()
    for row in rows[1:]:
        if not row.strip():
            continue
        columns = row.split("\t")
        if columns[columnIndex["isException"]] == "True":
            continue
        pairs.add(frozenset({columns[columnIndex["oldSpelling"]], columns[columnIndex["newSpelling"]]}))
    return frozenset(pairs)


# Provisional per-pair overrides for the ~51 pairs where the aggregate rules below
# still misfire against the true per-pair optimum (regret > 0) -- see the design
# session's "Final recommended design" step 5. Keyed by the unordered {ortho, ortho}
# pair (this granularity matches how the design session itself lists these pairs);
# value is the ortho that gets marked. Built from a top-10-by-regret list combining
# the 10x and 100x thresholds' top lists, cross-checked against a full regeneration
# at the finally-chosen 10x threshold on freshly rebuilt Dictionary/FirstTheory
# pickles (2026-09-20) -- not yet re-verified against a canonical single run beyond
# that.
MARKING_OVERRIDES: dict[frozenset[str], str] = {
    frozenset({"sales", "salles"}): "salles",
    frozenset({"entrés", "entrées"}): "entrées",
    frozenset({"alentours", "alentour"}): "alentour",
    frozenset({"virés", "virées"}): "virées",
    frozenset({"portés", "portées"}): "portées",
    frozenset({"envolés", "envolées"}): "envolées",
    frozenset({"dorés", "dorées"}): "dorées",
    frozenset({"closes", "clauses"}): "clauses",
    frozenset({"comptés", "comtés"}): "comtés",
    frozenset({"montés", "montées"}): "montées",
    frozenset({"remontés", "remontées"}): "remontées",
    frozenset({"hautes", "hôtes"}): "hôtes",
    frozenset({"retenus", "retenues"}): "retenues",
    frozenset({"éteints", "étains"}): "étains",
    frozenset({"new", "news"}): "news",
    frozenset({"plongés", "plongées"}): "plongées",
    frozenset({"survenus", "survenues"}): "survenues",
    frozenset({"gelés", "gelées"}): "gelées",
    frozenset({"usagés", "usagers"}): "usagers",
    frozenset({"accros", "accrocs"}): "accrocs",
    frozenset({"percés", "percées"}): "percées",
    frozenset({"levés", "levers"}): "levers",
    frozenset({"traversés", "traversées"}): "traversées",
    frozenset({"rangés", "rangées"}): "rangées",
    frozenset({"réaux", "réal"}): "réal",
    frozenset({"rentrés", "rentrées"}): "rentrées",
    frozenset({"impairs", "impers"}): "impers",
    frozenset({"coronaires", "coroners"}): "coroners",
    frozenset({"crus", "crues"}): "crues",
    frozenset({"nazes", "nases"}): "nases",
    frozenset({"balèzes", "balaises"}): "balaises",
    frozenset({"lares", "lards"}): "lards",
    frozenset({"perçants", "persans"}): "persans",
    frozenset({"troués", "trouées"}): "trouées",
    frozenset({"craints", "crins"}): "crins",
    frozenset({"visés", "visées"}): "visées",
    frozenset({"ancrés", "encrés"}): "encrés",
    frozenset({"jetés", "jetées"}): "jetées",
    frozenset({"rués", "ruées"}): "ruées",
    frozenset({"dévonienne", "dévonien"}): "dévonien",
    frozenset({"pincés", "pincées"}): "pincées",
    frozenset({"monomoteurs", "monomoteur"}): "monomoteur",
    frozenset({"hautains", "hautins"}): "hautins",
    frozenset({"boursouflée", "boursoufflée"}): "boursoufflée",
    frozenset({"bouillis", "bouillies"}): "bouillies",
    frozenset({"bivalves", "bivalve"}): "bivalve",
    frozenset({"nichés", "nichées"}): "nichées",
    frozenset({"stabilisante", "stabilisant"}): "stabilisant",
    frozenset({"camés", "camées"}): "camées",
}


def decideStarHashMark(
    wordA: Word, wordB: Word, doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> Word | None:
    """
    For a clashing pair, decide which word needs the extra `*`/`#` disambiguating
    stroke, applying (in order) the design session's rules plus its provisional
    override list:
      1. Homograph exemption -- identical `ortho` means identical typed output
         regardless of which reading was meant, so there was never a real ambiguity.
         Returns None (no mark needed).
      2. Spelling-doublet exemption (`doubletPairs`, see loadReform1990DoubletPairs) --
         `wordA`/`wordB`'s lemmes are a sourced pre/post-1990-reform spelling pair,
         i.e. genuinely the same word under two spelling conventions, never a real
         ambiguity. Empty by default (opt-in via `doubletPairs`); returns None when it
         matches.
      3. Per-pair override (MARKING_OVERRIDES) -- the aggregate rules below still
         misfire (regret > 0) on this specific pair.
      4. Extreme-ratio exemption (>= RATIO_EXEMPTION_THRESHOLD) -- mark whichever
         reading is individually rarer; the frequency gap is its own mnemonic.
      5. Same-`gramCat` residual -- no categorical signal is possible (both readings
         share a category); mark whichever specific word is rarer, per-pair-optimal
         by construction.
      6. GRAMCAT_PRIORITY for the remaining cross-category residual -- the
         lower-priority (more marked) category is marked. A category pair outside
         this 6-entry table (not observed in the design session's residual) falls
         back to per-pair frequency.
    Returns the Word to mark, or None if no mark is needed.
    """
    if wordA.ortho == wordB.ortho:
        return None

    if frozenset({wordA.lemme, wordB.lemme}) in doubletPairs:
        return None

    override = MARKING_OVERRIDES.get(frozenset({wordA.ortho, wordB.ortho}))
    if override is not None:
        return wordA if wordA.ortho == override else wordB

    freqA, freqB = wordA.frequency, wordB.frequency
    lo, hi = min(freqA, freqB), max(freqA, freqB)
    ratio = hi / lo if lo > 0 else float("inf")
    if ratio >= RATIO_EXEMPTION_THRESHOLD or wordA.gramCat == wordB.gramCat:
        return wordA if freqA <= freqB else wordB

    priorityA = GRAMCAT_PRIORITY.get(wordA.gramCat.name)
    priorityB = GRAMCAT_PRIORITY.get(wordB.gramCat.name)
    if priorityA is not None and priorityB is not None:
        return wordA if priorityA < priorityB else wordB

    return wordA if freqA <= freqB else wordB


# ── N-ary generalization: a full homophone cluster, not just a pair ──────────────────

STAR = "*"
HASH = "#"
STAR_HASH = "*#"


def _starHashCompare(
    a: Word, b: Word, doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> int:
    """Comparator for ranking a cluster canonical-first (least marked first): -1 if a
    is more canonical than b, +1 if b is. Delegates to decideStarHashMark for the real
    decision; a None result (Rule 1 homograph or Rule 2 spelling-doublet exemption) has
    no ordering signal of its own, so it falls back to frequency then ortho purely to
    keep sort() stable and deterministic -- it does not imply one is "more canonical"
    than the other."""
    if a is b:
        return 0
    marked = decideStarHashMark(a, b, doubletPairs)
    if marked is None:
        if a.frequency != b.frequency:
            return -1 if a.frequency > b.frequency else 1
        return -1 if a.ortho < b.ortho else (1 if a.ortho > b.ortho else 0)
    return 1 if marked is a else -1


def rankHomophoneCluster(
    words: list[Word], doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> list[Word]:
    """Order a whole homophone cluster (>= 1 distinct-lemma readings sharing one
    stroke) canonical-first, applying decideStarHashMark pairwise as a total-order
    comparator via functools.cmp_to_key."""
    def compare(a: Word, b: Word) -> int:
        return _starHashCompare(a, b, doubletPairs)
    return sorted(words, key=cmp_to_key(compare))


def assignStarHashCombos(groupSize: int) -> list[tuple[str, ...]]:
    """
    Returns `groupSize` distinct */# marking codes, canonical (no extra stroke) first,
    in increasing order of markedness.

    A single extra stroke over the 2 reserved keys encodes 4 states -- no stroke, `*`,
    `#`, `*#` -- enough for a cluster of up to 4 distinguishable readings (see
    ROADMAP.md's 2026-09-15 reserved-key decision: up to 4 lemmas per cluster). Beyond
    that budget, each further reading gets one more whole extra syllable (appended
    stroke) of `*#` -- its rank above the 4-slot budget is encoded by HOW MANY `*#`
    syllables are appended (2, then 3, then 4, ...), not by varying their content.
    """
    codes: list[tuple[str, ...]] = [(), (STAR,), (HASH,), (STAR_HASH,)]
    n = 2
    while len(codes) < groupSize:
        codes.append((STAR_HASH,) * n)
        n += 1
    return codes[:groupSize]


def assignStarHashMarks(
    words: list[Word], doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> dict[Word, tuple[str, ...]]:
    """
    Rank a homophone cluster canonical-first and assign each member its */# marking
    code. Two kinds of reading never need to be told apart from each other, so they
    collapse to ONE representative -- their merged group's highest-frequency member --
    before ranking, keeping the cluster from consuming extra slots or escalating to an
    extra syllable it doesn't actually need:
      - identical `ortho` (decideStarHashMark's Rule 1: same typed output regardless of
        intended reading);
      - lemmes forming a `doubletPairs` entry (Rule 2: genuinely the same word under
        two 1990-reform spelling conventions, see loadReform1990DoubletPairs).
    Every word in a merged group then gets its representative's code.
    """
    byOrtho: dict[str, list[Word]] = defaultdict(list)
    for word in words:
        byOrtho[word.ortho].append(word)
    orthoGroups = list(byOrtho.values())
    representatives = [max(group, key=lambda w: w.frequency) for group in orthoGroups]

    parent = list(range(len(orthoGroups)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(representatives)):
        for j in range(i + 1, len(representatives)):
            if frozenset({representatives[i].lemme, representatives[j].lemme}) in doubletPairs:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    mergedGroups: dict[int, list[Word]] = defaultdict(list)
    for i, group in enumerate(orthoGroups):
        mergedGroups[find(i)].extend(group)

    mergedRepresentatives = [max(group, key=lambda w: w.frequency) for group in mergedGroups.values()]
    ranked = rankHomophoneCluster(mergedRepresentatives, doubletPairs)
    codes = assignStarHashCombos(len(ranked))
    codeByRepresentative = dict(zip(ranked, codes))

    codeByOrtho: dict[str, tuple[str, ...]] = {}
    for i, group in mergedGroups.items():
        rep = max(group, key=lambda w: w.frequency)
        code = codeByRepresentative[rep]
        for word in group:
            codeByOrtho[word.ortho] = code
    return {word: codeByOrtho[word.ortho] for word in words}


# Physical realization on the Starboard: `*` = key 10 (left index, off-home), `#` = key
# 15 (right index, off-home) -- both members of `Keyboard._reservedKeys` (`[0,1,10,15]`,
# see `src/keyboard.py:303`), and a legal cross-hand chord together (`*#` = both keys at
# once). Keys 0/1 (left pinky) remain unassigned/reserved for a future 3rd logical mark
# if the 4-lemma-per-stroke budget ever needs raising past what */#/*# already covers.
STAR_KEY = 10
HASH_KEY = 15

_STAR_HASH_KEYS: dict[str, Stroke] = {
    STAR: (STAR_KEY,),
    HASH: (HASH_KEY,),
    STAR_HASH: (STAR_KEY, HASH_KEY),
}


def starHashCodeToStrokes(code: tuple[str, ...]) -> Strokes:
    """Realize a symbolic */# marking code (assignStarHashCombos/assignStarHashMarks)
    as physical Starboard reserved-key strokes: each symbol in the code becomes one
    appended extra stroke/syllable, in order. The canonical empty code () maps to (),
    i.e. no extra stroke at all."""
    return tuple(_STAR_HASH_KEYS[symbol] for symbol in code)


def assignStarHashPhysicalStrokes(
    words: list[Word], doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> dict[Word, Strokes]:
    """assignStarHashMarks, realized as physical Starboard reserved-key strokes
    (starHashCodeToStrokes) instead of symbolic */# codes."""
    return {
        word: starHashCodeToStrokes(code)
        for word, code in assignStarHashMarks(words, doubletPairs).items()
    }


def groupHomophonesByReservedStroke(finalInduced: dict[Word, Strokes]) -> dict[Strokes, list[Word]]:
    """
    Groups words by their shared post-Phase-P final stroke (`finalInduced`, as computed
    by `realizeKeypressGroupsAsExtraStroke`), keeping only genuine distinct-lemma/
    `gramCat` homophone groups -- the population the */# reserved-key track (not Phase
    P) is responsible for disambiguating. A group is kept only if it has:
      - >= 2 distinct `lemmeGramCat` values -- a group with just one `lemmeGramCat`
        sharing one stroke here is an unresolved Phase P same-paradigm residual
        collision, not a */# case (Phase P's own job is to have already separated
        those onto different strokes);
      - >= 2 distinct `ortho` values -- an all-homograph group types identically
        regardless of which reading was meant, so it was never a real ambiguity
        (decideStarHashMark's Rule 2).
    """
    byStroke: dict[Strokes, list[Word]] = defaultdict(list)
    for word, stroke in finalInduced.items():
        byStroke[canonicalizeStrokes(stroke)].append(word)

    groups: dict[Strokes, list[Word]] = {}
    for stroke, words in byStroke.items():
        if len(words) < 2:
            continue
        if len({w.lemmeGramCat for w in words}) < 2:
            continue
        if len({w.ortho for w in words}) < 2:
            continue
        groups[stroke] = words
    return groups


def composeReservedKeyStrokes(
    finalInduced: dict[Word, Strokes], doubletPairs: frozenset[frozenset[str]] = frozenset()
) -> dict[Word, Strokes]:
    """
    Final realized Strokes for every word touched by the */# reserved-key track: Phase
    P's own `finalInduced` stroke, with the */# mark's extra syllable(s) appended after
    it. The two mechanisms compose safely by simple concatenation -- Phase P only ever
    picks coda-phoneme keys, which are structurally disjoint from the 2 dedicated
    reserved keys (`STAR_KEY`/`HASH_KEY` are excluded from `Keyboard.allowedKeys`), so
    appending can never re-introduce a collision between two different clusters: their
    `finalInduced` prefixes already differ, and appending more elements after a
    differing prefix keeps the whole Strokes tuple different. Words with no */# mark
    needed (the canonical member of their group, a spelling-doublet of it, or not part
    of any group at all) keep their `finalInduced` stroke unchanged. Pass `doubletPairs`
    (loadReform1990DoubletPairs) to also apply Rule 3's spelling-doublet exemption.
    """
    composed = dict(finalInduced)
    for stroke, words in groupHomophonesByReservedStroke(finalInduced).items():
        for word, extra in assignStarHashPhysicalStrokes(words, doubletPairs).items():
            if extra:
                composed[word] = finalInduced[word] + extra
    return composed


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
# Part 2 — atomic-feature phoneme-keypress search (keyboard-needing)
# ═══════════════════════════════════════════════════════════════════════════

def buildWordToStrokes(theory: dict[Strokes, list[Word]]) -> dict[Word, Strokes]:
    return {word: strokes for strokes, words in theory.items() for word in words}


def _selectCanonicalIndex(featureSet: tuple[WordFeature, ...], wordTuples: list[tuple[Word, ...]]) -> int:
    """Mirrors assignDiscriminatorKeypresses' no-stroke pick: the member whose feature is
    most linguistically unmarked (FEATURE_PRIORITY), tie-broken by corpus frequency, needs no
    added feature-keypress phoneme at all."""
    freqByIndex = [0.0] * len(featureSet)
    for wordTuple in wordTuples:
        for i, word in enumerate(wordTuple):
            freqByIndex[i] += word.frequency
    return max(range(len(featureSet)), key=lambda i: (FEATURE_PRIORITY.get(featureSet[i], 0), freqByIndex[i]))


def buildAtomicFeatureToWords(
    augmentedTheory: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]
) -> dict[str, list[tuple[Word, WordFeature]]]:
    """
    For every non-canonical (word, feature) pair in augmentedTheory (skipping the "nofeature"
    sentinel and single-member featuresets, which have no canonical/non-canonical split),
    split the feature into atomic features via atomicFeatures and record which words carry
    each one. A word whose feature is a multi-atomic-feature combo ("pers_3:nbr_p") appears
    under each of its atomic features.
    """
    atomicFeatureToWords: dict[str, list[tuple[Word, WordFeature]]] = defaultdict(list)
    for featureSet, wordTuples in augmentedTheory.items():
        if "nofeature" in featureSet or len(featureSet) < 2:
            continue
        canonicalIndex = _selectCanonicalIndex(featureSet, wordTuples)
        for i, feature in enumerate(featureSet):
            if i == canonicalIndex:
                continue
            for wordTuple in wordTuples:
                word = wordTuple[i]
                for atomicFeature in atomicFeatures(feature):
                    atomicFeatureToWords[atomicFeature].append((word, feature))
    return dict(atomicFeatureToWords)


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
class FeatureKeypressFeasibility:
    atomicFeature: str
    feasibleSingleKeyPhonemes: list[str] = field(default_factory=list)
    feasibleComboPhonemes: list[tuple[str, str]] = field(default_factory=list)

    @property
    def infeasible(self) -> bool:
        return not self.feasibleSingleKeyPhonemes and not self.feasibleComboPhonemes


def findFeatureKeypresses(
    atomicFeatureToWords: dict[str, list[tuple[Word, WordFeature]]],
    theory: dict[Strokes, list[Word]],
    keyboard: Keyboard,
    comboSize: int = 2,
) -> dict[str, FeatureKeypressFeasibility]:
    """
    For each atomic feature, scan candidate right-hand coda phonemes:
    - Round 1: every individual coda phoneme. Feasible for the atomic feature if, applied to
      every word carrying it (appended to the word's last-syllable coda), the resulting
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

    results: dict[str, FeatureKeypressFeasibility] = {}
    for atomicFeature, wordFeaturePairs in atomicFeatureToWords.items():
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
        results[atomicFeature] = FeatureKeypressFeasibility(
            atomicFeature=atomicFeature, feasibleSingleKeyPhonemes=feasibleSingle, feasibleComboPhonemes=feasibleCombo,
        )
    return results


@dataclass
class ComposedChordReport:
    feasibleWords: list[Word] = field(default_factory=list)
    infeasibleWords: list[Word] = field(default_factory=list)


def checkComposedChords(
    featureKeypresses: dict[str, FeatureKeypressFeasibility],
    atomicFeatureToWords: dict[str, list[tuple[Word, WordFeature]]],
    theory: dict[Strokes, list[Word]],
    keyboard: Keyboard,
) -> ComposedChordReport:
    """
    For words needing >1 atomic feature (e.g. pers_3 + nbr_p), compose the candidate chord as
    the union of each atomic feature's chosen keypress key(s) and verify the composed stroke
    is still collision-free: an atomic-feature pair can each be individually fine and still
    collide once unioned on one word, or collide with a same-cluster sibling. Prefers a
    composed multi-atomic-feature chord over an arbitrary combo -- this is the
    "3rd-person-plural = 3rd-person key + plural key" preference.
    """
    wordToStrokes = buildWordToStrokes(theory)
    wordAtomicFeatures: dict[Word, frozenset[str]] = {}
    for pairs in atomicFeatureToWords.values():
        for word, feature in pairs:
            wordAtomicFeatures[word] = atomicFeatures(feature)

    report = ComposedChordReport()
    for word, wordAtoms in wordAtomicFeatures.items():
        if len(wordAtoms) <= 1:
            continue  # single-atomic-feature features are covered directly by findFeatureKeypresses
        keypressKeys: set[int] = set()
        allAtomicFeaturesFeasible = True
        for atomicFeature in wordAtoms:
            feasibility = featureKeypresses.get(atomicFeature)
            if feasibility is None or feasibility.infeasible:
                allAtomicFeaturesFeasible = False
                break
            if feasibility.feasibleSingleKeyPhonemes:
                keys = keyboard.getStrokesOfPhoneme(feasibility.feasibleSingleKeyPhonemes[0], "coda")
                if keys:
                    keypressKeys.update(keys[0])
            else:
                p1, p2 = feasibility.feasibleComboPhonemes[0]
                keys1 = keyboard.getStrokesOfPhoneme(p1, "coda")
                keys2 = keyboard.getStrokesOfPhoneme(p2, "coda")
                if keys1:
                    keypressKeys.update(keys1[0])
                if keys2:
                    keypressKeys.update(keys2[0])
        if (not allAtomicFeaturesFeasible
                or not _isFeasibleAddition(wordToStrokes[word], tuple(sorted(keypressKeys)), theory)):
            report.infeasibleWords.append(word)
        else:
            report.feasibleWords.append(word)
    return report


# ═══════════════════════════════════════════════════════════════════════════
# Phase P — physical realization of Phase G's abstract keypress groups
# ═══════════════════════════════════════════════════════════════════════════

_K = TypeVar("_K")


def findCollidingInducedStrokes(inducedStrokeOf: dict[_K, Strokes]) -> list[tuple[_K, _K]]:
    """
    Given each entry's already-computed induced (candidate) stroke, find every pair that
    collides by landing on the same stroke. Generic over how the induced stroke was
    computed -- unlike findCollidingNewAdditions, doesn't assume every word got the same
    `additionKeys` (needed once different words can need different subsets of Phase G's
    keypress groups composed into their own induced stroke). Generic over the key type
    (`_K`): usually a `Word`, but `realizeKeypressGroupsAsExtraStroke`'s final
    verification pass keys by `(Word, readingIndex)` instead, so a self-homograph
    spelling's several readings (see `src.elicitation.resolveGroupPressSets`) are checked
    against every OTHER word without also being checked against each other.
    """
    seenByInducedStroke: dict[Strokes, _K] = {}
    collisions: list[tuple[_K, _K]] = []
    for key, inducedStroke in inducedStrokeOf.items():
        earlierKey = seenByInducedStroke.get(inducedStroke)
        if earlierKey is not None and earlierKey != key:
            collisions.append((earlierKey, key))
        else:
            seenByInducedStroke[inducedStroke] = key
    return collisions


def findCollidingNewAdditions(
    candidateWords: list[Word], additionKeys: tuple[int, ...], wordToStrokes: dict[Word, Strokes],
) -> list[tuple[Word, Word]]:
    """
    _isFeasibleAddition only checks one word's new candidate stroke against the existing
    `theory`; it misses two *different* newly-composed candidate strokes colliding with
    each other (e.g. two words in the same keypress group whose existing strokes differ
    but whose coda, once `additionKeys` is unioned in, become identical). Returns every
    colliding pair found among `candidateWords` under this one shared `additionKeys`.
    """
    inducedStrokeOf: dict[Word, Strokes] = {
        word: _appendCodaAddition(wordToStrokes[word], additionKeys) for word in candidateWords
    }
    return findCollidingInducedStrokes(inducedStrokeOf)


def buildWordsByOrthoLemme(theory: dict[Strokes, list[Word]]) -> dict[tuple[str, str], list[Word]]:
    """Index every Word in `theory` by (ortho, lemmeGramCat) -- the same key shape
    `resolved_press_sets.json` entries use (`entry["lemmeGramCat"]` + a press-set ortho)."""
    wordsByOrthoLemme: dict[tuple[str, str], list[Word]] = defaultdict(list)
    for words in theory.values():
        for word in words:
            wordsByOrthoLemme[(word.ortho, word.lemmeGramCat)].append(word)
    return dict(wordsByOrthoLemme)


def _resolveEntryWord(
    entry: dict, ortho: str,
    wordToStrokes: dict[Word, Strokes],
    wordsByOrthoLemme: dict[tuple[str, str], list[Word]],
) -> Word | None:
    """Find the real `Word` a `resolved_press_sets.json` entry's (ortho, lemmeGramCat) +
    existing "strokes" field identifies -- there can be more than one `Word` sharing an
    (ortho, lemmeGramCat) key, disambiguated by which one actually carries that entry's
    existing stroke in `theory`. Shared by `buildKeypressGroupToWords` and
    `buildKeypressGroupExtraAlternates`.

    The entry's "strokes" are CANONICAL (sorted, deduped -- `buildLemmaHomophoneGroups`
    regroups by `canonicalizeStrokes`), while `wordToStrokes` holds theory 1's raw,
    repeat-preserving strokes, so the comparison canonicalizes first. Comparing raw
    against canonical silently missed every word whose raw stroke repeats a key (e.g.
    "nie" /nj/, raw ((6, 8, 8, 9),)) and fell back to `candidates[0]` -- a DIFFERENT
    same-spelling Word ("nie" /ni/), which then got the other one's marks."""
    lemmeGramCat = entry["lemmeGramCat"]
    entryStrokes: Strokes = tuple(tuple(stroke) for stroke in entry["strokes"])
    candidates = wordsByOrthoLemme.get((ortho, lemmeGramCat), [])
    word = next(
        (w for w in candidates if w in wordToStrokes and canonicalizeStrokes(wordToStrokes[w]) == entryStrokes),
        None,
    )
    return word if word is not None else (candidates[0] if candidates else None)


def buildKeypressGroupToWords(
    resolvedGroups: list[dict],
    markersByKeypress: dict[int, frozenset[str]],
    wordToStrokes: dict[Word, Strokes],
    wordsByOrthoLemme: dict[tuple[str, str], list[Word]],
) -> dict[int, list[Word]]:
    """
    Replaces buildAtomicFeatureToWords's role for Phase P: maps each Phase G keypress
    group id to every real `Word` whose elicited press-set (`resolved_press_sets.json`)
    touches a marker in that group -- the population `findKeypressGroupRealizations`
    must check feasibility against. `resolvedGroups` is the parsed
    `resolved_press_sets.json` list; each entry's own "strokes" field disambiguates
    which `Word` (there can be more than one sharing an (ortho, lemmeGramCat) key) is
    the one actually carrying that entry's existing stroke in `theory`.

    Each ortho's press-sets is now a LIST of alternates (see
    `src.elicitation.resolveGroupPressSets` -- more than one only for a spelling that is
    itself a self-homograph, e.g. "calmez"). This function drives Phase P's group-by-group
    physical key SEARCH off each spelling's PRIMARY (first, smallest) alternate only, so
    the search/collision machinery below is unaffected by alternates. Any further
    alternates are realized separately, once every group already has a physical key, via
    `buildKeypressGroupExtraAlternates` + `realizeKeypressGroupsAsExtraStroke`'s
    `extraGroupSetsByWord` parameter (see DESIGN_alternate_press_sets.md section 4).
    """
    groupToWords: dict[int, list[Word]] = defaultdict(list)
    for entry in resolvedGroups:
        for ortho, alternates in entry["pressSets"].items():
            if not alternates:
                continue
            markerSet = frozenset(alternates[0])
            if not markerSet:
                continue
            word = _resolveEntryWord(entry, ortho, wordToStrokes, wordsByOrthoLemme)
            if word is None:
                continue
            for groupId, groupMarkers in markersByKeypress.items():
                if markerSet & groupMarkers:
                    groupToWords[groupId].append(word)
    return dict(groupToWords)


def buildKeypressGroupExtraAlternates(
    resolvedGroups: list[dict],
    markersByKeypress: dict[int, frozenset[str]],
    wordToStrokes: dict[Word, Strokes],
    wordsByOrthoLemme: dict[tuple[str, str], list[Word]],
) -> dict[Word, list[frozenset[int]]]:
    """
    Every OTHER (non-primary) alternate press-set a self-homograph spelling holds -- e.g.
    "calmez"'s indicatif reading (`pers_2`), once its impératif reading (`impératif`)
    already drives the primary population `buildKeypressGroupToWords` builds -- as the set
    of Phase G keypress groups THAT alternate's markers touch. Feeds
    `realizeKeypressGroupsAsExtraStroke`'s `extraGroupSetsByWord` so each such reading gets
    realized as its own additional physical extra stroke once every group's key is
    decided, rather than silently dropped: per
    `src.elicitation.resolveGroupPressSets`/`ATOMIC_KEYPRESS_REWIRE_PLAN.md`'s vocabulary,
    readings of the same spelling never conflict with each other, so each is
    independently a valid way to write that spelling.
    """
    extraGroupSetsByWord: dict[Word, list[frozenset[int]]] = defaultdict(list)
    for entry in resolvedGroups:
        for ortho, alternates in entry["pressSets"].items():
            if len(alternates) < 2:
                continue
            word = _resolveEntryWord(entry, ortho, wordToStrokes, wordsByOrthoLemme)
            if word is None:
                continue
            for markers in alternates[1:]:
                markerSet = frozenset(markers)
                if not markerSet:
                    continue
                groupIds = frozenset(
                    groupId for groupId, groupMarkers in markersByKeypress.items() if markerSet & groupMarkers
                )
                if groupIds:
                    extraGroupSetsByWord[word].append(groupIds)
    return dict(extraGroupSetsByWord)


def buildWordToGroups(groupToWords: dict[int, list[Word]]) -> dict[Word, frozenset[int]]:
    """Invert groupToWords: every Word -> the set of Phase G keypress groups it needs
    (a word needing e.g. both the "f" and "p" groups gets both group ids)."""
    wordToGroups: dict[Word, set[int]] = defaultdict(set)
    for groupId, words in groupToWords.items():
        for word in words:
            wordToGroups[word].add(groupId)
    return {word: frozenset(groups) for word, groups in wordToGroups.items()}


def _appendCodaExtraStroke(strokes: Strokes, additionKeys: tuple[int, ...]) -> Strokes:
    """
    Realizes a discriminator as a brand-new trailing stroke -- an extra "syllable"
    pressed after the word's own strokes -- rather than merging into the last existing
    stroke's chord (`_appendCodaAddition`, used by the older atomic-feature diagnostic
    path only). A word needing several Phase G groups at once gets ONE shared extra
    stroke unioning all of them, not one extra stroke per group.
    """
    return strokes + (tuple(sorted(additionKeys)),)


@dataclass
class KeypressGroupPhysicalAssignment:
    """
    Milestone-1 Phase P output: a greedy, most-constrained-group-first physical key
    assignment for every Phase G keypress group, realized as one shared extra coda
    stroke per word (see `_appendCodaExtraStroke`). Each group's candidate search
    composes with whatever's ALREADY been decided for a word's OTHER needed groups at
    that point -- groups not yet processed can't be accounted for yet, so
    `residualCollisions`/`residualTheoryCollisions` (from a final full-assignment
    verification pass, mirroring Phase G's own `verifyKeypressAssignment` habit of
    re-checking a greedy result against ground truth) report anything that slips
    through this greedy ordering rather than silently hiding it.
    """
    chosenKeysByGroup: dict[int, tuple[int, ...]] = field(default_factory=dict)
    costByGroup: dict[int, int] = field(default_factory=dict)
    alternatesByGroup: dict[int, list[tuple[tuple[int, ...], int]]] = field(default_factory=dict)
    unassignedGroups: list[int] = field(default_factory=list)
    residualCollisions: list[tuple[Word, Word]] = field(default_factory=list)
    residualTheoryCollisions: list[Word] = field(default_factory=list)
    # Different-lemma homophone pairs that still collide -- NOT this function's job to
    # prevent (see `_isInScopeCollision`'s docstring: that's the reserved */# keys'
    # track), reported here only for visibility into how much of the remaining ambiguity
    # is actually someone else's job vs. genuinely unresolved same-lemma work.
    crossLemmaCollisions: list[tuple[Word, Word]] = field(default_factory=list)
    # Same bare lemma, different gramCat (e.g. "dîner" the NOM vs "dîner" the VER) --
    # the already-documented "aller"-style cross-category clash (see
    # `detectCrossCategoryClash`), a separate issue class from both of the above and
    # NOT this function's job either (see `_isInScopeCollision`'s docstring).
    crossCategoryClashCollisions: list[tuple[Word, Word]] = field(default_factory=list)
    # Which of `preferredKeysByGroup`'s requests were actually honored (True) vs. left
    # unhonored because the requested physical key was infeasible for that group's real
    # population (False) -- a group absent here had no preference requested at all.
    preferredKeyHonoredByGroup: dict[int, bool] = field(default_factory=dict)


# Human preference (2026-09-22 session) for Phase P's physical coda-bank key choice,
# keyed by MARKER rather than a Phase G group id (which can shift between reruns as
# bundling changes) -- shared by `util/build_phase_p_realization.py`'s diagnostic
# artifact and `Dictionary.buildFinalTheory`'s real export, so both land on the same
# physical keys. `pers_3` on -t: mnemonic, many pers_3 verb forms end in a written "t".
# `impératif` on -k and `pers_2` on -d: kept in that physical order, both ahead of
# pers_3's -t.
PREFERRED_KEYS_BY_MARKER: dict[str, tuple[int, ...]] = {
    "impératif": (18,),  # -k
    "pers_2": (19,),     # -d
    "pers_3": (20,),     # -t
}


def resolvePreferredKeysByGroup(
    markersByKeypress: dict[int, frozenset[str]],
    preferredKeysByMarker: dict[str, tuple[int, ...]] = PREFERRED_KEYS_BY_MARKER,
) -> dict[int, tuple[int, ...]]:
    """Resolve `preferredKeysByMarker`'s per-marker requests to whichever Phase G group
    id actually holds that marker in THIS run (see `realizeKeypressGroupsAsExtraStroke`'s
    `preferredKeysByGroup` parameter) -- a marker absent from `markersByKeypress`
    (unpressable this run) is silently skipped."""
    preferredKeysByGroup: dict[int, tuple[int, ...]] = {}
    for marker, keys in preferredKeysByMarker.items():
        groupId = next((gid for gid, markers in markersByKeypress.items() if marker in markers), None)
        if groupId is not None:
            preferredKeysByGroup[groupId] = keys
    return preferredKeysByGroup


def _isInScopeCollision(word1: Word, word2: Word) -> bool:
    """
    True only for a genuine same-lemmeGramCat collision -- two inflected forms of the
    exact same lemma+gramCat paradigm (e.g. "dors"/"dort") -- the one thing Phase G/P's
    coda-bank keypress groups are meant to prevent. Two other patterns that can produce
    an identical composed stroke are each somebody else's job, not scored here:
    - identical orthography (e.g. a VER-participle vs ADJ homograph reading of one
      written word) produces the same typed output regardless of which grammatical
      reading was meant, so it was never a real ambiguity to begin with;
    - same bare lemma but different gramCat (e.g. "dîner" NOM vs "dîner" VER) is the
      already-documented "aller"-style cross-category clash (`detectCrossCategoryClash`),
      a separate, pre-existing issue class;
    - different lemma entirely (e.g. "abymes"/"abîmes") is cross-lemma homophone
      disambiguation, the reserved `*`/`#` keys' job (RESUME_2026-09-18's design
      decision #1), not yet applied to the live `theory` this runs against.
    """
    return word1.ortho != word2.ortho and word1.lemmeGramCat == word2.lemmeGramCat


def realizeKeypressGroupsAsExtraStroke(
    groupToWords: dict[int, list[Word]],
    theory: dict[Strokes, list[Word]],
    keyboard: Keyboard,
    comboSize: int = 2,
    extraGroupSetsByWord: dict[Word, list[frozenset[int]]] | None = None,
    preferredKeysByGroup: dict[int, tuple[int, ...]] | None = None,
) -> KeypressGroupPhysicalAssignment:
    """
    Corrected successor to the earlier (flawed) findKeypressGroupRealizations: that
    version (a) merged each group's candidate into the word's LAST existing stroke, and
    (b) tested each of Phase G's 6 groups in isolation, so a word needing two groups at
    once (e.g. "abaissées" needing both the "f" and "p" groups) was checked as if it
    only got one of them -- producing false collisions between words that don't
    actually collide once both of their needed groups' keys are composed together.

    This version appends ONE shared extra coda stroke per word (`_appendCodaExtraStroke`)
    and, when searching a group's candidate keys, composes them with whatever's already
    decided for that same word's OTHER needed groups (processed in descending affected-
    word-count order, since the biggest, most-constrained groups are hardest to move
    later). A final full-assignment verification pass (using every group's final choice
    together) surfaces anything the greedy ordering still missed.

    Candidates are ranked by the REAL composed chord's cost (`_candidateCost`), not by
    each candidate's own isolated cost: a word needing this group ALSO needing an
    already-decided other group presses their union as one physical chord, and
    `Keyboard.getStrokeCost` already prices two same-column keys (e.g. Starboard coda
    (22,23)) below the same two keys pressed cross-column (e.g. (22,24)) -- pricing the
    real composition is what lets a candidate landing in the same column as a frequently
    co-occurring group's key earn that discount, instead of every candidate being judged
    solely on its own in isolation.

    `extraGroupSetsByWord` (see `buildKeypressGroupExtraAlternates`) lists, for a spelling
    that is itself a self-homograph (more than one valid reading, e.g. "calmez" -- see
    `src.elicitation.resolveGroupPressSets`), each of its OTHER readings' own group-set --
    every group in `groupToWords`/`wordToGroups` is still decided using only each word's
    PRIMARY reading, so this never influences the search/ranking above; it only adds
    those extra readings to the FINAL verification pass below, each realized as its own
    additional physical extra stroke reusing whatever key its groups already got. Two
    readings of the SAME word colliding with each other is never flagged (`_isInScopeCollision`
    requires different orthography) -- only a collision against some OTHER word is real.

    `preferredKeysByGroup` (human preference, e.g. a mnemonic like "pers_3 on -t since
    many pers_3 forms end in a written t") requests a SPECIFIC physical key-combo for a
    given group id, tried before the normal cost-ranked search: honored outright if
    `_feasible` for that group's real population (skipping the cost comparison entirely --
    a human preference overrides the cheapest-composed-chord ranking, not just nudges it),
    left unhonored (falling back to the normal search, silently trying the next-cheapest
    candidate) if it would collide with anything. `assignment.preferredKeyHonoredByGroup`
    reports which requests actually won.
    """
    wordToStrokes = buildWordToStrokes(theory)
    wordToGroups = buildWordToGroups(groupToWords)
    candidatePhonemes = list(Phoneme.consonantPhonemes)
    codaKeysOf: dict[str, tuple[int, ...]] = {}
    for phoneme in candidatePhonemes:
        strokesForPhoneme = keyboard.getStrokesOfPhoneme(phoneme, "coda")
        codaKeysOf[phoneme] = strokesForPhoneme[0] if strokesForPhoneme else ()

    assignment = KeypressGroupPhysicalAssignment()
    allWords = {word for words in groupToWords.values() for word in words}

    # A word is "finalized" once every Phase G group it needs has been processed
    # (assigned a key or given up on) -- its own composed stroke can never change again.
    # Phase G's own verification (`verifyKeypressAssignment`) only proves the 6 groups
    # are pairwise distinguishable in the ABSTRACT (no two spellings in one homophone
    # entry induce the same set of abstract keypress ids); it says nothing about the
    # PHYSICAL result. Two different groups' key-sets being pairwise distinct is NOT
    # enough to guarantee this: a word needing several groups at once gets their UNION,
    # and that union can coincidentally equal some THIRD, single group's own key-set
    # (e.g. groups 0 and 5 individually get (17,) and (16,); a word needing both gets
    # (16,17) -- exactly group 3's own key-set, even though every pair of groups here has
    # a distinct key-set on its own). Only checking every candidate against the real
    # composed stroke of every already-finalized word -- not just pairwise group-key
    # distinctness -- catches this.
    processedGroups: set[int] = set()
    finalizedWords: set[Word] = set()
    finalizedWordsByStroke: dict[Strokes, list[Word]] = defaultdict(list)

    def _finalizeReadyWords() -> None:
        for word in allWords:
            if word in finalizedWords or not wordToGroups[word] <= processedGroups:
                continue
            keys: set[int] = set()
            for otherGroup in wordToGroups[word]:
                keys.update(assignment.chosenKeysByGroup.get(otherGroup, ()))
            stroke = _appendCodaExtraStroke(wordToStrokes[word], tuple(sorted(keys))) if keys else wordToStrokes[word]
            finalizedWordsByStroke[stroke].append(word)
            finalizedWords.add(word)

    def _composedInduced(word: Word, groupId: int, candidateKeys: tuple[int, ...]) -> Strokes:
        unionKeys: set[int] = set(candidateKeys)
        for otherGroup in wordToGroups[word]:
            if otherGroup != groupId:
                unionKeys.update(assignment.chosenKeysByGroup.get(otherGroup, ()))
        return _appendCodaExtraStroke(wordToStrokes[word], tuple(sorted(unionKeys)))

    def _isRedundantForAnyWord(words: list[Word], groupId: int, keys: tuple[int, ...]) -> bool:
        """True if some word needing groupId ALSO needs another already-decided group
        whose keys already fully cover `keys` -- the addition would be a silent no-op for
        that word (its final composed stroke wouldn't change), quietly failing to
        differentiate it from a sibling that doesn't need groupId at all."""
        keySet = set(keys)
        for word in words:
            otherKeys: set[int] = set()
            for otherGroup in wordToGroups[word]:
                if otherGroup != groupId:
                    otherKeys.update(assignment.chosenKeysByGroup.get(otherGroup, ()))
            if otherKeys and keySet <= otherKeys:
                return True
        return False

    def _feasible(words: list[Word], groupId: int, keys: tuple[int, ...]) -> bool:
        # Cheap fast-path: reusing another already-decided group's key-set outright is
        # always wrong for a word needing ONLY groupId (see this function's caller-side
        # docstring on `finalizedWordsByStroke` for why this alone isn't sufficient --
        # the full finalized-pool check below covers the multi-group composition case).
        if keys in assignment.chosenKeysByGroup.values():
            return False
        if not keys or _isRedundantForAnyWord(words, groupId, keys):
            return False
        induced = {word: _composedInduced(word, groupId, keys) for word in words}
        # A word that also needs an already-decided OTHER group gets `keys` unioned with
        # that group's key into one physical chord -- that union has to actually be
        # pressable (a legal per-finger key combo), not just theory/collision-clean.
        if any(keyboard.getStrokeCost(stroke[-1], "coda") is None for stroke in induced.values()):
            return False
        if any(stroke in theory for stroke in induced.values()):
            return False
        # Only compare pairwise collisions among words that need the exact same FULL set
        # of Phase G groups -- their eventual composed stroke is guaranteed identical
        # regardless of processing order, so a collision here is real. Two words needing
        # a *different* remaining group may still be told apart once that not-yet-decided
        # group gets a real key -- checking them against each other now, while that other
        # group still contributes nothing, would produce a false collision (this is
        # exactly the "abaissée vs abaissées" mistake this function replaces). The final
        # full-assignment verification pass below re-checks everyone for real once every
        # group has a final answer (or none, if left unassigned).
        bySignature: dict[frozenset[int], dict[Word, Strokes]] = defaultdict(dict)
        for word in words:
            bySignature[wordToGroups[word]][word] = induced[word]
        # Only an in-scope (same-lemma) collision blocks this candidate -- see
        # _isInScopeCollision: identical-spelling pairs aren't real ambiguity, and
        # cross-lemma pairs are the reserved */# keys' job, not this function's.
        if any(
            _isInScopeCollision(w1, w2)
            for sameSignatureWords in bySignature.values()
            for w1, w2 in findCollidingInducedStrokes(sameSignatureWords)
        ):
            return False
        # Also check against every already-FINALIZED word (its own groups are all
        # decided, so its stroke can't change anymore) -- this is what catches a
        # multi-group composition coinciding with some other single (or differently
        # composed) group's result, which pairwise group-key distinctness alone misses.
        for word, stroke in induced.items():
            for otherWord in finalizedWordsByStroke.get(stroke, ()):
                if otherWord != word and _isInScopeCollision(word, otherWord):
                    return False
        return True

    def _candidateCost(words: list[Word], groupId: int, keys: tuple[int, ...]) -> int:
        """
        Frequency-weighted average cost of the REAL composed extra stroke this candidate
        produces across its affected words -- not `keys` priced in isolation. A word that
        also needs an already-decided OTHER group gets `keys` unioned with that group's
        key into one physical chord before costing, so a candidate that lands in the same
        physical column as a frequently co-occurring group's key is correctly rewarded:
        `getStrokeCost` already prices a same-column 2-key combo (e.g. Starboard's coda
        pinky (22,23) or (24,25)) below pressing those same two keys as a cross-column
        combo (e.g. (22,24)/(23,25)), let alone below the cost of two separate strokes --
        pricing the real per-word composition (rather than `keys` alone) is what lets that
        existing same-column discount actually reach this ranking, instead of a candidate
        being judged solely on its own isolated cost regardless of what it gets combined
        with.
        """
        totalCost = 0.0
        totalWeight = 0.0
        for word in words:
            stroke = _composedInduced(word, groupId, keys)
            cost = keyboard.getStrokeCost(stroke[-1], "coda")
            if cost is None:
                continue  # already excluded by _feasible; defensive only
            weight = word.frequency
            totalCost += cost * weight
            totalWeight += weight
        if totalWeight == 0:
            isolatedCost = keyboard.getStrokeCost(keys, "coda")
            return isolatedCost if isolatedCost is not None else 0
        return round(totalCost / totalWeight)

    def _bestCandidate(words: list[Word], groupId: int) -> list[tuple[tuple[int, ...], int]]:
        ranked: list[tuple[tuple[int, ...], int]] = []
        seenKeys: set[tuple[int, ...]] = set()
        for keys in list(codaKeysOf.values()):
            if not keys or keys in seenKeys or not _feasible(words, groupId, keys):
                continue
            seenKeys.add(keys)
            ranked.append((keys, _candidateCost(words, groupId, keys)))
        if not ranked and comboSize >= 2:
            for p1, p2 in combinations(candidatePhonemes, 2):
                keys = tuple(sorted(set(codaKeysOf.get(p1, ())) | set(codaKeysOf.get(p2, ()))))
                if not keys or keys in seenKeys or not _feasible(words, groupId, keys):
                    continue
                seenKeys.add(keys)
                ranked.append((keys, _candidateCost(words, groupId, keys)))
        ranked.sort(key=lambda kc: kc[1])
        preferred = (preferredKeysByGroup or {}).get(groupId)
        if preferred is not None:
            if preferred in seenKeys:
                assignment.preferredKeyHonoredByGroup[groupId] = True
                ranked.sort(key=lambda kc: kc[0] != preferred)  # stable: keeps cost order among the rest
            elif _feasible(words, groupId, preferred):
                assignment.preferredKeyHonoredByGroup[groupId] = True
                ranked.insert(0, (preferred, _candidateCost(words, groupId, preferred)))
            else:
                assignment.preferredKeyHonoredByGroup[groupId] = False
        return ranked

    for groupId in sorted(groupToWords, key=lambda g: -len(groupToWords[g])):
        ranked = _bestCandidate(groupToWords[groupId], groupId)
        if ranked:
            assignment.chosenKeysByGroup[groupId] = ranked[0][0]
            assignment.costByGroup[groupId] = ranked[0][1]
            assignment.alternatesByGroup[groupId] = ranked[1:]
        else:
            assignment.unassignedGroups.append(groupId)
            assignment.alternatesByGroup[groupId] = []
        processedGroups.add(groupId)
        _finalizeReadyWords()

    # Final full-assignment verification: compose EVERY needed group's final choice per
    # word (not just what was known while that word's groups were being decided) -- and,
    # for a self-homograph word, every OTHER reading's own group-set too
    # (`extraGroupSetsByWord`), each as its own additional stroke. Keyed by (word,
    # readingIndex) rather than just `word` so two readings of the SAME word landing on
    # the identical composed stroke is never itself flagged as a collision (see
    # `findCollidingInducedStrokes`'s docstring) -- reading 0 is always the word's primary
    # (the one the search above used); readings 1+ are its extra alternates, in order.
    extraGroupSetsByWord = extraGroupSetsByWord or {}
    finalInduced: dict[tuple[Word, int], Strokes] = {}
    for word in allWords:
        keys: set[int] = set()
        for groupId in wordToGroups[word]:
            keys.update(assignment.chosenKeysByGroup.get(groupId, ()))
        finalInduced[(word, 0)] = (
            _appendCodaExtraStroke(wordToStrokes[word], tuple(sorted(keys))) if keys else wordToStrokes[word]
        )
        for readingIndex, groupSet in enumerate(extraGroupSetsByWord.get(word, ()), start=1):
            altKeys: set[int] = set()
            for groupId in groupSet:
                altKeys.update(assignment.chosenKeysByGroup.get(groupId, ()))
            finalInduced[(word, readingIndex)] = (
                _appendCodaExtraStroke(wordToStrokes[word], tuple(sorted(altKeys)))
                if altKeys else wordToStrokes[word]
            )

    assignment.residualTheoryCollisions = sorted({
        word for (word, _readingIndex), stroke in finalInduced.items()
        if stroke != wordToStrokes[word] and stroke in theory
    }, key=lambda w: w.ortho)
    allFinalCollisions = findCollidingInducedStrokes(finalInduced)
    assignment.residualCollisions = [
        (w1, w2) for (w1, _i1), (w2, _i2) in allFinalCollisions if _isInScopeCollision(w1, w2)
    ]
    assignment.crossCategoryClashCollisions = [
        (w1, w2) for (w1, _i1), (w2, _i2) in allFinalCollisions
        if w1.ortho != w2.ortho and w1.lemme == w2.lemme and w1.lemmeGramCat != w2.lemmeGramCat
    ]
    assignment.crossLemmaCollisions = [
        (w1, w2) for (w1, _i1), (w2, _i2) in allFinalCollisions if w1.ortho != w2.ortho and w1.lemme != w2.lemme
    ]
    return assignment


def buildFinalInducedStrokes(
    theory: dict[Strokes, list[Word]],
    groupToWords: dict[int, list[Word]],
    assignment: KeypressGroupPhysicalAssignment,
) -> dict[Word, Strokes]:
    """
    Phase P's final stroke for EVERY word in `theory` -- not just the ones
    `realizeKeypressGroupsAsExtraStroke` had to consider (its own `allWords` is only the
    words touched by some Phase G group). `composeReservedKeyStrokes` needs the whole
    lexicon, since a */# homophone cluster can include words Phase P never touched at
    all. A word touched by no Phase G group keeps its theory-1 stroke unchanged; a word
    needing one or more groups gets `assignment.chosenKeysByGroup`'s keys for each,
    unioned into one shared extra coda stroke -- the same reconstruction
    `realizeKeypressGroupsAsExtraStroke` already does internally for its own
    verification pass, generalized here to the full lexicon.
    """
    wordToStrokes = buildWordToStrokes(theory)
    wordToGroups = buildWordToGroups(groupToWords)
    finalInduced: dict[Word, Strokes] = {}
    for word, strokes in wordToStrokes.items():
        keys: set[int] = set()
        for groupId in wordToGroups.get(word, frozenset()):
            keys.update(assignment.chosenKeysByGroup.get(groupId, ()))
        finalInduced[word] = _appendCodaExtraStroke(strokes, tuple(sorted(keys))) if keys else strokes
    return finalInduced


def buildExtraInducedStrokes(
    theory: dict[Strokes, list[Word]],
    assignment: KeypressGroupPhysicalAssignment,
    extraGroupSetsByWord: dict[Word, list[frozenset[int]]],
) -> dict[Word, list[Strokes]]:
    """
    A self-homograph word's OTHER readings (see `buildKeypressGroupExtraAlternates`,
    `src.elicitation.resolveGroupPressSets` -- e.g. "calmez"'s indicatif reading, once
    its impératif reading already drives `buildFinalInducedStrokes`' one stroke per
    word), each composed into its own additional Strokes the same way
    `buildFinalInducedStrokes` composes a word's primary stroke: its theory-1 base plus
    that reading's own group-set's already-decided physical keys.

    Deliberately NOT run through `composeReservedKeyStrokes` (the `*`/`#` cross-lemma
    track): that track isn't wired into a self-homograph's alternates yet, matching
    CLAUDE.md's own note that the cross-lemma track isn't yet wired into `dictionary.py`'s
    persisted output at all -- an alternate stroke colliding with an unrelated lemma's
    stroke is a pre-existing class of gap this function doesn't newly introduce.
    """
    wordToStrokes = buildWordToStrokes(theory)
    extraByWord: dict[Word, list[Strokes]] = {}
    for word, groupSets in extraGroupSetsByWord.items():
        strokes: list[Strokes] = []
        for groupSet in groupSets:
            keys: set[int] = set()
            for groupId in groupSet:
                keys.update(assignment.chosenKeysByGroup.get(groupId, ()))
            if keys:
                strokes.append(_appendCodaExtraStroke(wordToStrokes[word], tuple(sorted(keys))))
        if strokes:
            extraByWord[word] = strokes
    return extraByWord


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

    augmentedTheory = buildDiscriminatorSelection(theory)

    atomicFeatureToWords = buildAtomicFeatureToWords(augmentedTheory)
    featureKeypresses = findFeatureKeypresses(atomicFeatureToWords, theory, starboard)
    composedReport = checkComposedChords(featureKeypresses, atomicFeatureToWords, theory, starboard)

    print("\n=== Per-atomic-feature phoneme-keypress feasibility ===")
    for atomicFeature, feasibility in sorted(featureKeypresses.items()):
        if feasibility.feasibleSingleKeyPhonemes:
            print(f"  {atomicFeature:>10}: single-key candidates {feasibility.feasibleSingleKeyPhonemes}")
        elif feasibility.feasibleComboPhonemes:
            print(f"  {atomicFeature:>10}: combo candidates {feasibility.feasibleComboPhonemes[:5]}")
        else:
            print(f"  {atomicFeature:>10}: INFEASIBLE even at combo size 2")
    print(f"\nComposed multi-atomic-feature chords: {len(composedReport.feasibleWords)} feasible,"
          f" {len(composedReport.infeasibleWords)} infeasible")

    with open("feature_keypress_feasibility.tsv", "w") as f:
        _ = f.write("atomicFeature\tfeasibleSingleKeys\tfeasibleCombos\tinfeasible\n")
        for atomicFeature, feasibility in sorted(featureKeypresses.items()):
            _ = f.write(f"{atomicFeature}\t{','.join(feasibility.feasibleSingleKeyPhonemes)}\t"
                         f"{','.join('+'.join(c) for c in feasibility.feasibleComboPhonemes)}\t"
                         f"{feasibility.infeasible}\n")
