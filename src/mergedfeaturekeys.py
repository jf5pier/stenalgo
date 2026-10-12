"""
Merged feature keys (docs/MERGED_FEATURE_KEYS_PLAN.md, D17): the rules shared by the pipeline and the hand-run
simulator `util/analyze_merged_feature_keys.py`.

Every entry (one word, one press-set alternate, so `dis` has 5) whose outline ends with a feature discriminating
stroke gets a candidate merged outline: its last base stroke (star/hash keys merged in included) united with the
feature stroke's keys; an escalated code's */# marker strokes stay after it. An entry merges when its reading's tense
is a merge-eligible tense (D5, every combination of the alternate), the merged last stroke is pressable, the outline
is free and the entry wins the merge precedence ladder (D7) against the other candidates of that outline:
  occupied   the outline is already a final outline of the theory (any word, alternates included) or a reserved
             chord of another shipped dictionary (D8): the occupant keeps it;
  level 1    two candidates of different spellings: the one whose last base stroke strictly contains the other's
             (the shared keys are sounds) wins;
  level 2    equal last base strokes, same lemme+category: the one with an absorbed feature key (already in its
             last base stroke) loses;
  tie        neither: the more frequent spelling merges (gate 3; the simulator also offers `fallback`, all keep the
             long outline, and `precedence`, the higher GRAMCAT_PRIORITY category, then the entry's `precedence`
             rank, then frequency).
Losers keep the long outline, already unique, so one pass suffices. The long outline always stays an alternate (D3).
"""
import os
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from src.ambiguitychecker import UNLISTED_CATEGORY_PRIORITY, _resolveEntryWord
from src.expressionmodel import HASH_KEY, STAR_KEY
from src.greedyoptimizer import GRAMCAT_PRIORITY
from src.keyboard import Starboard, Stroke, Strokes
from src.word import Word

MARK_KEYS = frozenset({STAR_KEY, HASH_KEY})
TENSES = ("présent", "impératif", "infinitif", "participe", "nominal", "imparfait", "future", "conditionnel",
          "subjonctif", "passé simple")
MERGE_ELIGIBLE_TENSES = frozenset(TENSES[:8])         # D5 (gates 2026-10-11 and 2026-10-12)
TIE_RULES = ("frequency", "fallback", "precedence")


def comboTense(combo: Iterable[str]) -> str:
    """The tense of one feature combination of a reading (`nominal` for NOM/ADJ gender/number)."""
    features = set(combo)
    for tense in ("infinitif", "participe", "conditionnel", "subjonctif", "impératif"):
        if tense in features:
            return tense
    if "indicatif" in features:
        if "imparfait" in features:
            return "imparfait"
        if "future" in features:
            return "future"
        return "passé simple" if "passé" in features else "présent"
    return "nominal"


def stripMarks(strokes: Strokes) -> Strokes:
    """The strokes without star/hash keys and without */# marker strokes."""
    return tuple(tuple(k for k in s if k not in MARK_KEYS) for s in strokes if not set(s) <= MARK_KEYS)


def mergeStroke(stroke: Stroke, keys: Iterable[int]) -> Stroke:
    return tuple(sorted(set(stroke) | set(keys)))


@dataclass
class MergeEntry:
    """One alternate of one word: its outline, its candidate merged outline and the merge verdict."""
    word: Word
    index: int
    final: Strokes
    baseLength: int
    groups: frozenset[int]
    tenses: frozenset[str]
    readings: list[list[str]] = field(default_factory=list)
    featureKeys: frozenset[int] = frozenset()
    mergeKeys: frozenset[int] = frozenset()
    merged: Strokes | None = None
    mergedOutline: str = ""
    outcome: str = "no feature stroke"
    partner: str = ""
    eligible: bool = False
    precedence: int = 0

    @property
    def lastBase(self) -> frozenset[int]:
        return frozenset(self.final[self.baseLength - 1])

    @property
    def absorbed(self) -> bool:
        return bool(self.mergeKeys & self.lastBase)

    @property
    def primary(self) -> Strokes:
        return self.merged if self.outcome == "merged" and self.merged is not None else self.final

    @property
    def contestKey(self) -> tuple[frozenset[int], frozenset[int]]:
        return self.lastBase, self.mergeKeys


def buildMergeEntries(disambiguated: dict[Word, list[Strokes]], wordToStrokes: dict[Word, Strokes],
                      wordsByOrthoLemme: dict[tuple[str, str], list[Word]], resolved: list[dict[str, Any]],
                      markers: Mapping[int, frozenset[str]], eligible: frozenset[str] = MERGE_ELIGIBLE_TENSES,
                      unmarked: bool = False, everyTense: bool = False,
                      entryFactory: Callable[..., MergeEntry] = MergeEntry) -> tuple[list[MergeEntry], int]:
    """Every (word, alternate) of the disambiguated theory, aligned with its resolved press-set alternate (keypress
    groups and readings). `unmarked` compares outlines without their star/hash marks; `everyTense` makes every entry
    with a feature stroke eligible. Returns the entries and the number of words whose alternates do not align."""
    pressOf: dict[Word, tuple[list[list[str]], list[list[list[str]]]]] = {}
    for record in resolved:
        for ortho, alternates in record["pressSets"].items():
            word = _resolveEntryWord(record, ortho, wordToStrokes, wordsByOrthoLemme)
            if word is not None:
                pressOf[word] = (alternates, record["readings"][ortho])
    entries: list[MergeEntry] = []
    mismatches = 0
    for word, finals in disambiguated.items():
        alternates, readings = pressOf.get(word, ([[]], [[]]))
        if len(alternates) != len(finals):
            mismatches += 1
            alternates, readings = [[]] * len(finals), [[]] * len(finals)
        baseLength = len(wordToStrokes[word])
        for index, today in enumerate(finals):
            final = stripMarks(today) if unmarked else today
            groups = frozenset(g for g, groupMarkers in markers.items() if groupMarkers & set(alternates[index]))
            entry = entryFactory(word, index, final, baseLength, groups,
                                 frozenset(comboTense(combo) for combo in readings[index]), readings[index])
            if len(final) > baseLength and not set(final[baseLength]) <= MARK_KEYS:
                entry.featureKeys = frozenset(final[baseLength])
                entry.eligible = everyTense or (bool(entry.tenses) and entry.tenses <= eligible)
            entries.append(entry)
    return entries, mismatches


def applyMergeKeys(entries: Iterable[MergeEntry], mergeKeysOf: Mapping[int, tuple[int, ...]] | None = None) -> None:
    """(Re)sets every entry's candidate merged outline, verdicts cleared. The merge keys are the feature stroke's keys
    (D9), or the union of `mergeKeysOf` over the entry's keypress groups (the simulator's key-set search)."""
    for entry in entries:
        entry.partner, entry.mergedOutline = "", ""
        if not entry.featureKeys:
            entry.merged, entry.outcome = None, "no feature stroke"
            continue
        entry.mergeKeys = entry.featureKeys if mergeKeysOf is None \
            else frozenset(k for g in entry.groups for k in mergeKeysOf[g])
        last = entry.baseLength - 1
        entry.merged = entry.final[:last] + (mergeStroke(entry.final[last], entry.mergeKeys),) \
            + entry.final[entry.baseLength + 1:]
        entry.outcome = "eligible" if entry.eligible else "excluded tense"


def beats(a: MergeEntry, b: MergeEntry) -> str:
    """The ladder level at which `a` beats `b` (`level 1`, `level 2`), or '' when it does not."""
    if a.lastBase > b.lastBase:
        return "level 1"
    if a.lastBase == b.lastBase and a.word.lemmeGramCat == b.word.lemmeGramCat and b.absorbed and not a.absorbed:
        return "level 2"
    return ""


def occupiedOutlines(entries: Iterable[MergeEntry], render: Callable[[Strokes], str],
                     replaceLong: bool = False) -> dict[str, set[str]]:
    """Outline -> spellings of every final outline of the theory (long outlines included, unless `replaceLong`: the
    fusion statistics' view, where a merge replaced the long outline)."""
    occupied: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if replaceLong and entry.featureKeys:
            continue
        occupied[render(entry.final)].add(entry.word.ortho)
    return occupied


def resolveMerges(entries: list[MergeEntry], keyboard: Starboard, reserved: Mapping[str, str],
                  render: Callable[[Strokes], str], tie: str = "frequency", marksApart: bool = False,
                  anyConflict: bool = False, occupied: dict[str, set[str]] | None = None) -> None:
    """Sets each eligible entry's outcome: merged, or the reason it keeps its long outline. `reserved` maps the chords
    of the other dictionaries to their source (D8, D16). `marksApart` is ladder level 3 on unmarked outlines (two
    entries with the same last base stroke and merge keys never block each other: S7 marks them apart afterwards);
    `anyConflict` drops the ladder (any other spelling on the outline blocks, the fusion statistics' view)."""
    if tie not in TIE_RULES:
        raise ValueError(f"unknown tie rule {tie!r}")
    if occupied is None:
        occupied = occupiedOutlines(entries, render, replaceLong=anyConflict)
    candidates: dict[str, list[MergeEntry]] = defaultdict(list)
    for entry in entries:
        if not entry.eligible or entry.merged is None:
            continue
        if keyboard.getStrokeCost(stripMarks(entry.final[entry.baseLength - 1:entry.baseLength])[0], "coda") is None:
            entry.outcome = "base unpressable"
            continue
        if keyboard.getStrokeCost(entry.merged[entry.baseLength - 1], "coda") is None:
            entry.outcome = "unpressable"
            continue
        entry.mergedOutline = render(entry.merged)
        candidates[entry.mergedOutline].append(entry)
    for outline, group in candidates.items():
        others = occupied.get(outline, set())
        if outline in reserved:
            for entry in group:
                entry.outcome, entry.partner = "other dictionary", reserved[outline]
            continue
        for entry in group:
            occupants = others - {entry.word.ortho}
            if occupants:
                entry.outcome, entry.partner = "occupied", ",".join(sorted(occupants))
        open_ = [e for e in group if e.outcome == "eligible"]
        if anyConflict:
            for entry in open_:
                rivals = [r for r in open_ if r.word.ortho != entry.word.ortho]
                entry.outcome = "conflict" if rivals else "merged"
                entry.partner = rivals[0].word.ortho if rivals else ""
            continue

        def competes(a: MergeEntry, b: MergeEntry) -> bool:
            if a.word.ortho == b.word.ortho:
                return False
            return not marksApart or a.contestKey != b.contestKey

        undominated: list[MergeEntry] = []
        for entry in open_:
            beaten = next(((r, level) for r in open_ if competes(r, entry)
                           for level in [beats(r, entry)] if level), None)
            if beaten is not None:
                entry.outcome, entry.partner = beaten[1], beaten[0].word.ortho
            else:
                undominated.append(entry)
        spellings: dict[str, float] = defaultdict(float)
        for entry in undominated:
            spellings[entry.word.ortho] += entry.word.frequency
        if all(not competes(a, b) for a in undominated for b in undominated):
            for entry in undominated:
                entry.outcome = "merged"
            continue
        rank: dict[str, tuple[int, int, float]] = {}
        for entry in undominated:
            key = (GRAMCAT_PRIORITY.get(entry.word.gramCat.name, UNLISTED_CATEGORY_PRIORITY), -entry.precedence,
                   spellings[entry.word.ortho])
            rank[entry.word.ortho] = max(rank.get(entry.word.ortho, key), key)
        winner = max(spellings, key=lambda s: (spellings[s], s)) if tie == "frequency" \
            else max(rank, key=lambda s: (rank[s], s)) if tie == "precedence" else None
        for entry in undominated:
            if entry.word.ortho == winner:
                entry.outcome = "merged"
            else:
                entry.outcome = "tie"
                entry.partner = ",".join(sorted(s for s in spellings if s != entry.word.ortho))


# The merge in the pipeline (I1): off by default, so the theory is unchanged; STENALGO_MERGE_FEATURE_KEYS=1 turns it
# on for a build.
MERGE_FEATURE_KEYS = os.environ.get("STENALGO_MERGE_FEATURE_KEYS", "") == "1"


def mergeFeatureKeys(disambiguated: dict[Word, list[Strokes]], wordToStrokes: dict[Word, Strokes],
                     wordsByOrthoLemme: dict[tuple[str, str], list[Word]], resolved: list[dict[str, Any]],
                     markers: Mapping[int, frozenset[str]], keyboard: Starboard, reserved: Mapping[str, str],
                     render: Callable[[Strokes], str]) -> tuple[dict[Word, list[Strokes]], list[MergeEntry]]:
    """
    The merged theory, after S7 (gate 4): each word's outlines in their order, an entry that merges taking its merged
    outline in place of its long one, then the long outlines of its merged entries (D3), in the same order. A word's
    first len(press-set alternates) outlines therefore stay aligned with its readings. Returns the theory and the
    merge entries (verdicts for the reports).
    """
    entries, _mismatches = buildMergeEntries(disambiguated, wordToStrokes, wordsByOrthoLemme, resolved, markers)
    applyMergeKeys(entries)
    resolveMerges(entries, keyboard, reserved, render)
    byWord: dict[Word, list[MergeEntry]] = defaultdict(list)
    for entry in entries:
        byWord[entry.word].append(entry)
    merged: dict[Word, list[Strokes]] = {}
    for word, outlines in disambiguated.items():
        wordEntries = sorted(byWord[word], key=lambda e: e.index)
        merged[word] = [e.primary for e in wordEntries] + [e.final for e in wordEntries if e.outcome == "merged"]
        assert len(wordEntries) == len(outlines)
    return merged, entries
