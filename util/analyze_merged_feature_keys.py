"""
Hand-run diagnostic: the merged-feature-keys simulator (docs/MERGED_FEATURE_KEYS_PLAN.md, iteration 1).

Every entry (one word, one press-set alternate, so `dis` has 5) whose outline ends with a feature discriminating
stroke gets a candidate merged outline: its last base stroke (star/hash keys merged in included) united with the
feature stroke's keys; an escalated code's */# marker strokes stay after it. An entry merges when its reading's tense
is merge-eligible (D5, every combination of the alternate), the merged last stroke is pressable, the outline is free
and the entry wins the merge precedence ladder (D7) against the other candidates of that outline:
  occupied   the outline is already a final outline of the theory (any word, alternates included) or a chord of
             another shipped dictionary (D8): the occupant keeps it;
  level 1    two candidates of different spellings: the one whose last base stroke strictly contains the other's
             (the shared keys are sounds) wins;
  level 2    equal last base strokes, same lemme+category: the one with an absorbed feature key (already in its
             last base stroke) loses;
  tie        neither: --tie fallback (all keep the long outline), frequency (the more frequent spelling merges) or
             precedence (the higher GRAMCAT_PRIORITY category, then the earlier line of
             conjugation_disambiguation_order.txt for the entry's reading, then frequency).
Losers keep the long outline, already unique, so one pass suffices. The long outline always stays an alternate (D3).

--order after-s7 (default) compares today's final outlines, star/hash marks included (a mark can make room:
`sais` takes `siek` when `sec` is `sie*k`). --order before-s7 compares unmarked outlines (level 3: two spellings with
the same last base stroke and the same feature keys never block each other) and then recomposes the S7 marks over
the whole merged theory (composeReservedKeyStrokesForEntries, long outlines kept as alternates).

Frequency = Lexique film frequency of the word, split over its alternates with the reading-share table
(resources/readingShares.tsv, D13).

--regression reproduces docs/CONJUGATION_FUSION_STATS.md: every tense eligible, marks ignored, no ladder (any other
spelling on the outline is a conflict), words counted by their primary alternate.

Prerequisites: DisambiguatedTheory.pickle (or both pickles), starboard3h.json, keypress_groups.json,
resolved_press_sets.json, realization_report.json, resources/readingShares.tsv, the lexicons, the shipped
plover_stenalgo_*.json chords and scratch/expr-briefs.tsv.
Outputs: OUT/metrics.md and OUT/entries.tsv. ~2 min.

Run: python -m util.analyze_merged_feature_keys [--eligible T,T...] [--tie fallback|frequency|precedence]
     [--order after-s7|before-s7] [--regression] [--out DIR]
"""
import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from src.ambiguitychecker import (
    UNLISTED_CATEGORY_PRIORITY,
    _resolveEntryWord,
    composeReservedKeyStrokesForEntries,
    loadReform1990DoubletPairs,
)
from src.greedyoptimizer import GRAMCAT_PRIORITY
from src.keyboard import Starboard, Stroke, Strokes
from src.word import Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util.build_reading_shares import LEXICON_DEFAULTS, classKey, loadLexiqueClasses
from util.check_conjugation_disambiguation_order import parsePrecedenceOrder
from util.export_plover_numbers import reservedNumberStrokes
from util.export_plover_spelling import reservedSpellingStrokes

MARK_KEYS = frozenset({10, 15})
ELIGIBLE_DEFAULT = ("présent", "impératif", "infinitif", "participe", "nominal")
EXCLUDED_DEFAULT = ("future", "passé simple", "conditionnel", "imparfait", "subjonctif")
RESERVED_DICTIONARIES = ("plover_stenalgo_punctuation.json", "plover_stenalgo_commands.json",
                         "plover_stenalgo_pluvier_punctuation.json", "plover_stenalgo_pluvier_numbers.json",
                         "plover_stenalgo_lapwing_numbers.json", "plover_stenalgo_spelling.json")
EXPRESSION_BRIEFS = "scratch/expr-briefs.tsv"
READING_SHARES = "resources/readingShares.tsv"
OUT_DEFAULT = "scratch/merged-keys/baseline"
TOP_EXAMPLES = 30
MOODS = {"indicatif": "ind", "subjonctif": "sub", "conditionnel": "cnd", "impératif": "imp"}


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


def comboReading(combo: Iterable[str]) -> str:
    """The reading-share table's notation of a feature combination (`ind:pre:1s`, `par:pas`, `nom:f`...)."""
    features = set(combo)
    if "infinitif" in features:
        return "inf"
    if "participe" in features:
        return "par:pas" if "passé" in features else "par:pre"
    gender = "f" if "f" in features else "m" if "m" in features else ""
    number = "p" if "p" in features else "s" if "s" in features else ""
    mood = next((MOODS[m] for m in MOODS if m in features), None)
    if mood is None:
        return f"nom:{gender}{number}"
    tense = "pre"
    if mood != "cnd":
        tense = "imp" if "imparfait" in features else "pas" if "passé" in features \
            else "fut" if "future" in features else "pre"
    person = next((f[-1] for f in features if f.startswith("pers_")), "")
    return f"{mood}:{tense}:{person}{'p' if 'nbr_p' in features else 's'}"


class ReadingShares:
    """The reading-share table looked up by an entry's reading set in the theory's lexicons (D13)."""

    def __init__(self, sharesPath: str = READING_SHARES, lexiconPaths: Iterable[str] = LEXICON_DEFAULTS) -> None:
        self.classes, _frequencies = loadLexiqueClasses(lexiconPaths)
        self.shares: dict[str, dict[str, float]] = defaultdict(dict)
        with open(sharesPath, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                self.shares[row["class"]][row["reading"]] = float(row["share"])
        self.misses = 0

    def share(self, word: Word, combo: Iterable[str]) -> float:
        """The share of a combination's reading in the word's class; 1 when the class is unknown."""
        lemme, cgram = word.lemmeGramCat.rsplit("_", 1)
        readingClass = self.classes.get((word.ortho.lower(), lemme, cgram))
        if readingClass is None:
            self.misses += 1
            return 1.0
        reading = comboReading(combo)
        table = self.shares[classKey(readingClass)]
        if reading.startswith("nom:"):
            return sum(s for r, s in table.items() if r.startswith(reading))
        if reading in table:
            return table[reading]
        self.misses += 1
        return 1.0 / len(readingClass)


PARTICIPLE_BACKDROP = frozenset({"VER", "participe", "passé"})


def precedenceIndex(combos: Iterable[Iterable[str]], order: list[frozenset[str]]) -> int:
    """The earliest conjugation_disambiguation_order.txt line any of the entry's readings matches (its most
    specific line, a participle read by its gender/number); len(order) when none matches."""
    best = len(order)
    for combo in combos:
        features = frozenset(combo)
        if "participe" in features:
            features -= PARTICIPLE_BACKDROP
        matches = [(len(line), -i) for i, line in enumerate(order) if line <= features]
        if matches:
            best = min(best, -max(matches)[1])
    return best


@dataclass
class Entry:
    """One alternate of one word: today's outline, its candidate merged outline and the simulator's verdict."""
    word: Word
    index: int
    final: Strokes
    baseLength: int
    groups: frozenset[int]
    tenses: frozenset[str]
    frequency: float
    featureKeys: frozenset[int] = frozenset()
    mergeKeys: frozenset[int] = frozenset()
    merged: Strokes | None = None
    mergedOutline: str = ""
    outcome: str = "no feature stroke"
    partner: str = ""
    eligible: bool = False
    precedence: int = 0
    today: Strokes = ()
    composedPrimary: Strokes | None = None
    composedLong: Strokes | None = None

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
    def shipped(self) -> Strokes:
        """The primary outline as shipped: after the S7 recomposition under before-s7."""
        return self.composedPrimary if self.composedPrimary is not None else self.primary

    @property
    def shippedLong(self) -> Strokes:
        return self.composedLong if self.composedLong is not None else self.final

    @property
    def contestKey(self) -> tuple[frozenset[int], frozenset[int]]:
        return self.lastBase, self.mergeKeys


@dataclass
class Options:
    eligible: frozenset[str]
    tie: str
    order: str
    regression: bool
    out: str
    mergeKeys: dict[int, tuple[int, ...]] = field(default_factory=dict)


@dataclass
class Simulation:
    entries: list[Entry]
    keysOf: dict[int, tuple[int, ...]]
    markers: dict[int, frozenset[str]]
    reservedCount: int
    preexistingCollisions: int
    alignmentMismatches: int
    shareMisses: int
    finalCollisions: list[str] = field(default_factory=list)
    markChanges: list[Entry] = field(default_factory=list)


def stripMarks(strokes: Strokes) -> Strokes:
    """The strokes without star/hash keys and without */# marker strokes (the --regression view)."""
    return tuple(tuple(k for k in s if k not in MARK_KEYS) for s in strokes if not set(s) <= MARK_KEYS)


def mergeStroke(stroke: Stroke, keys: Iterable[int]) -> Stroke:
    return tuple(sorted(set(stroke) | set(keys)))


def loadReservedChords() -> dict[str, str]:
    """Outline -> source of every chord of the other shipped dictionaries and of the expression briefs (D8)."""
    reserved: dict[str, str] = {}
    for path in RESERVED_DICTIONARIES:
        with open(path, encoding="utf-8") as f:
            for outline in json.load(f):
                reserved.setdefault(outline, path.removeprefix("plover_stenalgo_").removesuffix(".json"))
    with open(EXPRESSION_BRIEFS, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            reserved.setdefault(row["rtfcre"], "expression brief")
    return reserved


def buildEntries(disambiguated: dict[Word, list[Strokes]], wordToStrokes: dict[Word, Strokes],
                 wordsByOrthoLemme: dict[tuple[str, str], list[Word]], resolved: list[dict[str, Any]],
                 markers: dict[int, frozenset[str]], keysOf: dict[int, tuple[int, ...]],
                 shares: ReadingShares, options: Options) -> tuple[list[Entry], int]:
    """Every (word, alternate) of the disambiguated theory, with its frequency share and candidate merged outline."""
    pressOf: dict[Word, tuple[list[list[str]], list[list[list[str]]]]] = {}
    for record in resolved:
        for ortho, alternates in record["pressSets"].items():
            word = _resolveEntryWord(record, ortho, wordToStrokes, wordsByOrthoLemme)
            if word is not None:
                pressOf[word] = (alternates, record["readings"][ortho])
    entries: list[Entry] = []
    mismatches = 0
    order = parsePrecedenceOrder()
    for word, finals in disambiguated.items():
        alternates, readings = pressOf.get(word, ([[]], [[]]))
        if len(alternates) != len(finals):
            mismatches += 1
            alternates, readings = [[]] * len(finals), [[]] * len(finals)
        weights = [sum(shares.share(word, combo) for combo in combos) if combos else 1.0 for combos in readings]
        if sum(weights) <= 0:
            weights = [1.0] * len(weights)
        baseLength = len(wordToStrokes[word])
        for index, today in enumerate(finals):
            final = stripMarks(today) if options.regression or options.order == "before-s7" else today
            groups = frozenset(g for g, groupMarkers in markers.items() if groupMarkers & set(alternates[index]))
            entry = Entry(word, index, final, baseLength, groups,
                          frozenset(comboTense(combo) for combo in readings[index]),
                          word.frequency * weights[index] / sum(weights),
                          precedence=precedenceIndex(readings[index], order), today=today)
            hasFeatureStroke = len(final) > baseLength and not set(final[baseLength]) <= MARK_KEYS
            if hasFeatureStroke:
                entry.featureKeys = frozenset(final[baseLength])
                if entry.featureKeys != {k for g in groups for k in keysOf[g]}:
                    mismatches += 1
                entry.eligible = options.regression or (bool(entry.tenses) and entry.tenses <= options.eligible)
            entries.append(entry)
    return entries, mismatches


def applyMergeKeys(entries: Iterable[Entry], mergeKeysOf: dict[int, tuple[int, ...]]) -> None:
    """(Re)sets every entry's candidate merged outline for the merge key-set of each group (D9), verdicts cleared."""
    for entry in entries:
        entry.partner, entry.mergedOutline = "", ""
        entry.composedPrimary = entry.composedLong = None
        if not entry.featureKeys:
            entry.merged, entry.outcome = None, "no feature stroke"
            continue
        entry.mergeKeys = frozenset(k for g in entry.groups for k in mergeKeysOf[g])
        last = entry.baseLength - 1
        entry.merged = entry.final[:last] + (mergeStroke(entry.final[last], entry.mergeKeys),) \
            + entry.final[entry.baseLength + 1:]
        entry.outcome = "eligible" if entry.eligible else "excluded tense"


def encodingClashes(entries: Iterable[Entry], mergeKeysOf: dict[int, tuple[int, ...]]) -> list[str]:
    """The merge key-sets that two group sets of eligible entries share (f, p and f+p must stay distinct from each
    other and from every union that occurs)."""
    groupSets = {e.groups for e in entries if e.eligible and e.featureKeys}
    byKeys: dict[frozenset[int], list[frozenset[int]]] = defaultdict(list)
    for groups in groupSets:
        byKeys[frozenset(k for g in groups for k in mergeKeysOf[g])].append(groups)
    return [f"{sorted(keys)}: {' / '.join(str(sorted(g)) for g in sets)}"
            for keys, sets in byKeys.items() if len(sets) > 1]


def beats(a: Entry, b: Entry) -> str:
    """The ladder level at which `a` beats `b` (`level 1`, `level 2`), or '' when it does not."""
    if a.lastBase > b.lastBase:
        return "level 1"
    if a.lastBase == b.lastBase and a.word.lemmeGramCat == b.word.lemmeGramCat and b.absorbed and not a.absorbed:
        return "level 2"
    return ""


def occupiedOutlines(entries: list[Entry], options: Options, render: Any) -> dict[str, set[str]]:
    """Outline -> spellings of every final outline of the theory (long outlines included)."""
    occupied: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if options.regression and entry.featureKeys:
            continue  # the fusion statistics replaced the long outline instead of keeping it
        occupied[render(entry.final)].add(entry.word.ortho)
    return occupied


def resolveMerges(entries: list[Entry], keyboard: Starboard, reserved: dict[str, str], options: Options,
                  render: Any, occupied: dict[str, set[str]] | None = None) -> None:
    """Sets each eligible entry's outcome: merged, or the reason it keeps its long outline."""
    if occupied is None:
        occupied = occupiedOutlines(entries, options, render)
    candidates: dict[str, list[Entry]] = defaultdict(list)
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
        if options.regression:
            for entry in open_:
                rivals = [r for r in open_ if r.word.ortho != entry.word.ortho]
                entry.outcome = "conflict" if rivals else "merged"
                entry.partner = rivals[0].word.ortho if rivals else ""
            continue
        def competes(a: Entry, b: Entry) -> bool:
            if a.word.ortho == b.word.ortho:
                return False
            return options.order != "before-s7" or a.contestKey != b.contestKey  # level 3: S7 marks them apart

        undominated: list[Entry] = []
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
        winner = max(spellings, key=lambda s: (spellings[s], s)) if options.tie == "frequency" \
            else max(rank, key=lambda s: (rank[s], s)) if options.tie == "precedence" else None
        for entry in undominated:
            if entry.word.ortho == winner:
                entry.outcome = "merged"
            else:
                entry.outcome = "tie"
                entry.partner = ",".join(sorted(s for s in spellings if s != entry.word.ortho))


def recomposeMarks(entries: list[Entry], wordToStrokes: dict[Word, Strokes]) -> list[Entry]:
    """
    before-s7: S7 over the merged theory, each word's entries = its primary outlines (merged or long, unmarked) then
    the long outlines of its merged entries (D3). Returns the entries whose long outline's marks changed.
    """
    byWord: dict[Word, list[Entry]] = defaultdict(list)
    for entry in entries:
        byWord[entry.word].append(entry)
    entriesByWord: dict[Word, list[Strokes]] = {}
    for word, wordEntries in byWord.items():
        wordEntries.sort(key=lambda e: e.index)
        entriesByWord[word] = [e.primary for e in wordEntries] + [e.final for e in wordEntries if e.outcome == "merged"]
    composed = composeReservedKeyStrokesForEntries(
        entriesByWord, loadReform1990DoubletPairs(),
        phonemeStrokeCounts={word: len(wordToStrokes[word]) for word in entriesByWord},
        reservedStrokes=reservedNumberStrokes() | reservedSpellingStrokes())
    changed: list[Entry] = []
    for word, wordEntries in byWord.items():
        longs = iter(composed[word][len(wordEntries):])
        for entry in wordEntries:
            entry.composedPrimary = composed[word][entry.index]
            entry.composedLong = next(longs) if entry.outcome == "merged" else entry.composedPrimary
            if entry.composedLong != entry.today:
                changed.append(entry)
    return changed


def checkCollisions(entries: list[Entry], reserved: dict[str, str], render: Any) -> tuple[int, list[str]]:
    """H1: outlines shared by two spellings, before (today's outlines) and after (shipped primary and long outlines)."""
    def collisions(outlines: Iterable[tuple[str, str]]) -> list[str]:
        owners: dict[str, set[str]] = defaultdict(set)
        for outline, ortho in outlines:
            owners[outline].add(ortho)
        clashes = [o for o, s in owners.items() if len(s) > 1]
        clashes += [o for o in owners if o in reserved]
        return sorted(set(clashes))
    today = [(render(e.today), e.word.ortho) for e in entries]
    after = [(render(e.shippedLong), e.word.ortho) for e in entries] \
        + [(render(e.shipped), e.word.ortho) for e in entries if e.outcome == "merged"]
    before = set(collisions(today))
    return len(before), [o for o in collisions(after) if o not in before]


@dataclass
class Context:
    """Everything loaded once: the keyboard, the entries (merge keys applied per variant), the reserved chords."""
    keyboard: Starboard
    entries: list[Entry]
    wordToStrokes: dict[Word, Strokes]
    keysOf: dict[int, tuple[int, ...]]
    markers: dict[int, frozenset[str]]
    reserved: dict[str, str]
    mismatches: int
    shareMisses: int
    renderCache: dict[Strokes, str] = field(default_factory=dict)

    def render(self, strokes: Strokes) -> str:
        if strokes not in self.renderCache:
            self.renderCache[strokes] = renderFinalStrokesToRTFCRE(self.keyboard, strokes)
        return self.renderCache[strokes]


def loadContext(options: Options) -> Context:
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    if keyboard is None:
        raise RuntimeError("starboard3h.json not found; run from the repo root.")
    _phonetic, disambiguated, wordToStrokes, wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(keyboard)
    with open("realization_report.json", encoding="utf-8") as f:
        keysOf = {int(g): tuple(v["chosenKeys"]) for g, v in json.load(f)["keypressGroups"].items()}
    with open("keypress_groups.json", encoding="utf-8") as f:
        markers = {int(g): frozenset(m) for g, m in json.load(f)["markersByKeypress"].items()}
    with open("resolved_press_sets.json", encoding="utf-8") as f:
        resolved: list[dict[str, Any]] = json.load(f)
    shares = ReadingShares()
    entries, mismatches = buildEntries(disambiguated, wordToStrokes, wordsByOrthoLemme, resolved, markers, keysOf,
                                       shares, options)
    reserved = {} if options.regression else loadReservedChords()
    return Context(keyboard, entries, wordToStrokes, keysOf, markers, reserved, mismatches, shares.misses)


def simulate(ctx: Context, options: Options, occupied: dict[str, set[str]] | None = None) -> Simulation:
    applyMergeKeys(ctx.entries, {**ctx.keysOf, **options.mergeKeys})
    resolveMerges(ctx.entries, ctx.keyboard, ctx.reserved, options, ctx.render, occupied)
    markChanges = recomposeMarks(ctx.entries, ctx.wordToStrokes) if options.order == "before-s7" else []
    before, newCollisions = checkCollisions(ctx.entries, ctx.reserved, ctx.render)
    return Simulation(ctx.entries, ctx.keysOf, ctx.markers, len(ctx.reserved), before, ctx.mismatches,
                      ctx.shareMisses, newCollisions, markChanges)


def runSimulation(options: Options) -> Simulation:
    return simulate(loadContext(options), options)


# --- reporting ------------------------------------------------------------------------------------------------------

def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "-"


def strokeCost(keyboard: Starboard, stroke: Stroke) -> float:
    cost = keyboard.getStrokeCost(stroke, "coda")
    return float(cost) if cost is not None else 0.0


def regressionReport(sim: Simulation) -> list[str]:
    """The docs/CONJUGATION_FUSION_STATS.md headline: words needing a group, by their primary alternate."""
    primaries = [e for e in sim.entries if e.index == 0 and e.merged is not None]
    outcomes = Counter(e.outcome for e in primaries)
    return ["## Regression (all tenses, marks ignored, no ladder)", "",
            f"{len(primaries)} words needing at least one group (primary alternate): "
            f"no conflict {outcomes['merged']}, conflict {outcomes['conflict'] + outcomes['occupied']} (with a candidate "
            f"{outcomes['conflict']}, with an outline kept as is {outcomes['occupied']}), unpressable "
            f"{outcomes['unpressable'] + outcomes['base unpressable']} (base unpressable {outcomes['base unpressable']}).",
            "Reference (docs/CONJUGATION_FUSION_STATS.md): 139,757 words; clean 127,839 + abbrevOnly 122 = 127,961 "
            "without a full-form conflict; unpressable 448.", ""]


def metricsReport(sim: Simulation, options: Options) -> list[str]:
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    assert keyboard is not None
    entries = sim.entries
    total = sum(e.frequency for e in entries)
    lines = ["# Merged feature keys: simulation", "",
             f"Options: eligible {', '.join(sorted(options.eligible))}; tie {options.tie}; order {options.order}.",
             f"Entries {len(entries)} ({len({e.word for e in entries})} words); film frequency mass {total:.0f}; "
             f"reserved chords {sim.reservedCount}; alternate/feature-key mismatches {sim.alignmentMismatches}; "
             f"reading-share misses {sim.shareMisses}.", ""]

    # H1, H2
    unpressableMerged = sum(1 for e in entries if e.outcome == "merged"
                            and keyboard.getStrokeCost(e.shipped[e.baseLength - 1], "coda") is None)
    lines += ["## Hard constraints", "",
              f"- H1 new collisions: **{len(sim.finalCollisions)}** (outlines already shared today: "
              f"{sim.preexistingCollisions}) {', '.join(sim.finalCollisions[:10])}",
              f"- H2 unpressable merged strokes: **{unpressableMerged}**",
              "- H3 reserved dictionaries unchanged by construction (a merge never takes a reserved chord).",
              "- H4 not checked by the simulator (pipeline step I5).", ""]

    # M1
    today = sum(e.frequency * len(e.today) for e in entries) / total
    merged = sum(e.frequency * len(e.shipped) for e in entries) / total
    primaries = [e for e in entries if e.index == 0]
    todayCount = sum(len(e.today) for e in primaries) / len(primaries)
    mergedCount = sum(len(e.shipped) for e in primaries) / len(primaries)
    lines += ["## M1 strokes per word", "", "| | Today | Merged | Delta |", "|---|---|---|---|",
              f"| frequency-weighted (all entries) | {today:.4f} | {merged:.4f} | {merged - today:+.4f} "
              f"({100 * (merged - today) / today:+.2f}%) |",
              f"| unweighted (primary alternate of each word) | {todayCount:.4f} | {mergedCount:.4f} | "
              f"{mergedCount - todayCount:+.4f} |", ""]

    # M2
    withFeature = [e for e in entries if e.merged is not None]
    eligible = [e for e in withFeature if e.eligible]
    done = [e for e in eligible if e.outcome == "merged"]
    lines += ["## M2 merge rate", "",
              f"Entries with a feature stroke: {len(withFeature)} ({pct(sum(e.frequency for e in withFeature), total)} "
              f"of running words); eligible {len(eligible)} ({pct(sum(e.frequency for e in eligible), total)}); "
              f"merged {len(done)} ({pct(sum(e.frequency for e in done), total)}).", "",
              "| Slice | Eligible | Merged | Rate | Eligible freq | Merged freq | Rate (freq) |",
              "|---|---|---|---|---|---|---|"]

    def rateRow(label: str, pool: list[Entry]) -> str:
        hit = [e for e in pool if e.outcome == "merged"]
        poolFreq = sum(e.frequency for e in pool)
        hitFreq = sum(e.frequency for e in hit)
        return (f"| {label} | {len(pool)} | {len(hit)} | {pct(len(hit), len(pool))} | {pct(poolFreq, total)} | "
                f"{pct(hitFreq, total)} | {pct(hitFreq, poolFreq)} |")
    lines.append(rateRow("all", eligible))
    for group in sorted(sim.keysOf):
        lines.append(rateRow(f"group {group} {'+'.join(sorted(sim.markers[group]))} {sim.keysOf[group]}",
                             [e for e in eligible if group in e.groups]))
    for tense in ELIGIBLE_DEFAULT + EXCLUDED_DEFAULT:
        pool = [e for e in eligible if tense in e.tenses]
        if pool:
            lines.append(rateRow(f"tense {tense}", pool))
    excluded = [e for e in withFeature if not e.eligible]
    lines += ["", f"Excluded tenses keep {len(excluded)} entries ({pct(sum(e.frequency for e in excluded), total)} "
              "of running words) on the feature stroke.", ""]

    # M3
    spellingFrequency: dict[str, float] = defaultdict(float)
    for word in {e.word for e in entries}:
        spellingFrequency[word.ortho] += word.frequency
    rank = {s: i for i, s in enumerate(sorted(spellingFrequency, key=lambda s: -spellingFrequency[s]))}
    fallbacks = [e for e in eligible if e.outcome != "merged"]
    reasons = Counter(e.outcome for e in fallbacks)
    reasonFreq: dict[str, float] = defaultdict(float)
    for e in fallbacks:
        reasonFreq[e.outcome] += e.frequency
    lines += ["## M3 exceptions (eligible entries keeping the long outline)", "",
              "| Reason | Entries | Freq | In top 1,000 spellings | In top 5,000 |", "|---|---|---|---|---|"]
    for reason, n in reasons.most_common():
        inTop = [e for e in fallbacks if e.outcome == reason]
        lines.append(f"| {reason} | {n} | {pct(reasonFreq[reason], total)} | "
                     f"{len({e.word.ortho for e in inTop if rank[e.word.ortho] < 1000})} | "
                     f"{len({e.word.ortho for e in inTop if rank[e.word.ortho] < 5000})} |")
    lines += ["", f"Top {TOP_EXAMPLES} by frequency:", ""]
    for e in sorted(fallbacks, key=lambda x: -x.frequency)[:TOP_EXAMPLES]:
        lines.append(f"- `{e.word.ortho}` ({e.word.lemmeGramCat}, {'/'.join(sorted(e.tenses))}, "
                     f"{e.frequency:.1f}) [{e.mergedOutline or '-'}]: {e.outcome}"
                     f"{' vs `' + e.partner + '`' if e.partner else ''}")
    lines.append("")

    # M4
    weight = sum(e.frequency for e in done)
    mergedCost = sum(e.frequency * strokeCost(keyboard, e.shipped[e.baseLength - 1]) for e in done)
    longCost = sum(e.frequency * (strokeCost(keyboard, e.today[e.baseLength - 1])
                                  + strokeCost(keyboard, e.today[e.baseLength])) for e in done)
    lines += ["## M4 chord cost of the merged entries (frequency-weighted mean `getStrokeCost`, coda)", "",
              f"Merged last stroke {mergedCost / weight if weight else 0:.1f} vs last base stroke + feature stroke "
              f"{longCost / weight if weight else 0:.1f}.", ""]

    # M5
    def markLoad(outline: Any) -> tuple[int, int, float]:
        marked = sum(1 for e in entries if any(set(s) & MARK_KEYS for s in outline(e)))
        escalated = sum(1 for e in entries if any(set(s) <= MARK_KEYS for s in outline(e)))
        return marked, escalated, sum(e.frequency * sum(len(set(s) & MARK_KEYS) for s in outline(e))
                                      for e in entries) / total
    todayLoad, shippedLoad = markLoad(lambda e: e.today), markLoad(lambda e: e.shipped)
    lines += ["## M5 star/hash load (primary outlines)", "", "| | Entries with a mark | Escalated codes | "
              "Mark keys typed per word (freq-weighted) |", "|---|---|---|---|",
              f"| today | {todayLoad[0]} | {todayLoad[1]} | {todayLoad[2]:.4f} |",
              f"| merged | {shippedLoad[0]} | {shippedLoad[1]} | {shippedLoad[2]:.4f} |", ""]
    if options.order == "before-s7":
        changes = sim.markChanges
        lines += [f"Long outlines whose marks changed under before-s7: {len(changes)} entries "
                  f"({pct(sum(e.frequency for e in changes), total)} of running words). Top 15:", ""]
        def render(strokes: Strokes) -> str:
            return renderFinalStrokesToRTFCRE(keyboard, strokes)
        for e in sorted(changes, key=lambda x: -x.frequency)[:15]:
            lines.append(f"- `{e.word.ortho}` ({e.word.lemmeGramCat}, {e.frequency:.1f}): {render(e.today)} -> "
                         f"{render(e.shippedLong)}{' (primary ' + render(e.shipped) + ')' if e.outcome == 'merged' else ''}")
        lines.append("")
    return lines


CODA_KEYS = tuple(range(16, 26))
CODA_DIGRAPHS = ((16, 17), (16, 18), (17, 19), (18, 19), (20, 22), (22, 23), (24, 25))  # the Realization Phase's
F_GROUP, P_GROUP = 1, 5
LEARN_TOP = 50


def strokesPerWord(entries: Iterable[Entry], total: float) -> float:
    return sum(e.frequency * len(e.shipped) for e in entries) / total


def absorptionReport(ctx: Context) -> list[str]:
    """5a: per coda key, how often the last phoneme stroke already holds it, and its pressability with the most
    frequent last-stroke codas of the f and plural entries."""
    eligible = [e for e in ctx.entries if e.eligible and e.featureKeys]
    fp = [e for e in eligible if e.groups & {F_GROUP, P_GROUP}]
    allFreq = sum(e.frequency for e in eligible)
    fpFreq = sum(e.frequency for e in fp)
    codaFreq: dict[frozenset[int], float] = defaultdict(float)
    for e in fp:
        codaFreq[frozenset(k for k in stripMarks((tuple(e.lastBase),))[0] if k in CODA_KEYS)] += e.frequency
    topCodas = sorted(codaFreq, key=lambda c: -codaFreq[c])[:LEARN_TOP]
    topFreq = sum(codaFreq[c] for c in topCodas)
    lines = ["## 5a absorption risk per coda key", "",
             f"Eligible entries with a feature stroke: {len(eligible)}; of them needing f or plural: {len(fp)}. "
             f"Pressable = the key added to one of the {LEARN_TOP} most frequent last-stroke codas of the f/plural "
             f"entries ({pct(topFreq, fpFreq)} of their frequency) still has a `getStrokeCost`.", "",
             "| Key | Already in the last stroke (all eligible, freq) | (f/plural entries, freq) | Pressable codas "
             "(of 50) | Pressable (freq) |", "|---|---|---|---|---|"]
    for keys in [(k,) for k in CODA_KEYS] + list(CODA_DIGRAPHS):
        keySet = set(keys)
        inAll = sum(e.frequency for e in eligible if keySet & e.lastBase)
        inFp = sum(e.frequency for e in fp if keySet & e.lastBase)
        pressable = [c for c in topCodas if ctx.keyboard.getStrokeCost(tuple(sorted(c | keySet)), "coda") is not None]
        name = "".join(ctx.keyboard.keyDisplayName(k).strip("-") for k in keys)
        lines.append(f"| {keys} -{name} | {pct(inAll, allFreq)} | {pct(inFp, fpFreq)} | {len(pressable)} | "
                     f"{pct(sum(codaFreq[c] for c in pressable), topFreq)} |")
    return lines + [""]


def searchMergeKeys(ctx: Context, options: Options) -> list[str]:
    """5b: every (f, plural) merge key-set pair among the coda keys and the Realization Phase digraphs, ranked by M1,
    then M4; a pair whose key-sets clash with another group set's (f, p, f+p and every occurring union) is rejected."""
    total = sum(e.frequency for e in ctx.entries)
    occupied = occupiedOutlines(ctx.entries, options, ctx.render)
    for e in ctx.entries:
        e.composedPrimary = e.composedLong = None
    today = sum(e.frequency * len(e.today) for e in ctx.entries) / total
    candidates = [(k,) for k in CODA_KEYS] + list(CODA_DIGRAPHS)
    rows: list[tuple[float, float, str]] = []
    rejected: list[str] = []
    for fKeys in candidates:
        for pKeys in candidates:
            if fKeys == pKeys:
                continue
            mergeKeys = {**ctx.keysOf, F_GROUP: fKeys, P_GROUP: pKeys}
            clashes = encodingClashes(ctx.entries, mergeKeys)
            label = f"f={'+'.join(map(str, fKeys))} p={'+'.join(map(str, pKeys))}"
            if clashes:
                rejected.append(f"{label}: {clashes[0]}")
                continue
            simulate(ctx, Options(options.eligible, options.tie, options.order, False, options.out, mergeKeys),
                     occupied)
            done = [e for e in ctx.entries if e.outcome == "merged"]
            fpDone = [e for e in done if e.groups & {F_GROUP, P_GROUP}]
            fpEligible = [e for e in ctx.entries if e.eligible and e.groups & {F_GROUP, P_GROUP}]
            unpressable = sum(e.frequency for e in fpEligible if e.outcome == "unpressable")
            weight = sum(e.frequency for e in done)
            cost = sum(e.frequency * strokeCost(ctx.keyboard, e.shipped[e.baseLength - 1]) for e in done) / weight
            m1 = strokesPerWord(ctx.entries, total)
            order = "" if max(fKeys) < min(pKeys) else " (f after p)"
            rows.append((m1, cost, f"| {label}{order} | {m1:.4f} ({100 * (m1 - today) / today:+.2f}%) | "
                         f"{pct(sum(e.frequency for e in fpDone), sum(e.frequency for e in fpEligible))} | "
                         f"{pct(unpressable, sum(e.frequency for e in fpEligible))} | {len(done)} | {cost:.1f} |"))
            print(rows[-1][2], flush=True)
    rows.sort()
    header = ["| Merge key-sets | M1 strokes/word (vs today) | f/plural merged (freq) | f/plural unpressable "
              "(freq) | Entries merged | M4 merged-stroke cost |", "|---|---|---|---|---|---|"]
    return (["## 5b merge key-sets for f (group 1) and plural (group 5)", "",
             f"Options: eligible {', '.join(sorted(options.eligible))}; tie {options.tie}; order {options.order}. "
             f"Today {today:.4f} strokes per word. {len(rows)} valid pairs, {len(rejected)} rejected (key-set clash).",
             "", "Top 5:", ""] + header + [r[2] for r in rows[:5]]
            + ["", "All valid pairs:", ""] + header + [r[2] for r in rows]
            + ["", "Rejected (first clash):", ""] + [f"- {r}" for r in rejected] + [""])


def writeEntries(entries: list[Entry], path: str, render: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("ortho\tlemmeGramCat\talternate\ttenses\tgroups\tfrequency\toutcome\tpartner\tlong\tmerged\n")
        for e in sorted(entries, key=lambda x: (-x.frequency, x.word.ortho, x.index)):
            if e.merged is None:
                continue
            f.write(f"{e.word.ortho}\t{e.word.lemmeGramCat}\t{e.index}\t{'/'.join(sorted(e.tenses))}\t"
                    f"{','.join(map(str, sorted(e.groups)))}\t{e.frequency:.3f}\t{e.outcome}\t{e.partner}\t"
                    f"{render(e.shippedLong)}\t{render(e.shipped) if e.outcome == 'merged' else e.mergedOutline}\n")


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eligible", default=",".join(ELIGIBLE_DEFAULT),
                        help="comma-separated tenses; 'all' for every tense")
    parser.add_argument("--tie", choices=("fallback", "frequency", "precedence"), default="fallback")
    parser.add_argument("--order", choices=("after-s7", "before-s7"), default="after-s7")
    parser.add_argument("--regression", action="store_true")
    parser.add_argument("--merge-keys", default="",
                        help="merge key-sets by marker, e.g. f=22,p=24+25 (default: each group's feature key)")
    parser.add_argument("--search", action="store_true", help="iteration 5: absorption table and (f, p) key search")
    parser.add_argument("--out", default=OUT_DEFAULT)
    args = parser.parse_args()
    eligible = ELIGIBLE_DEFAULT + EXCLUDED_DEFAULT if args.eligible == "all" else tuple(args.eligible.split(","))
    unknown = set(eligible) - set(ELIGIBLE_DEFAULT + EXCLUDED_DEFAULT)
    if unknown:
        parser.error(f"unknown tenses {sorted(unknown)}")
    options = Options(frozenset(eligible), args.tie, args.order, args.regression, args.out)
    os.makedirs(options.out, exist_ok=True)
    ctx = loadContext(options)
    mergeKeysArgument: str = args.merge_keys
    for assignment in filter(None, mergeKeysArgument.split(",")):
        marker, keys = assignment.split("=")
        group = next(g for g, m in ctx.markers.items() if marker in m)
        options.mergeKeys[group] = tuple(int(k) for k in keys.split("+"))
    if args.search:
        report = absorptionReport(ctx) + searchMergeKeys(ctx, options)
        with open(os.path.join(options.out, "search.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
        return
    sim = simulate(ctx, options)
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    assert keyboard is not None
    lines = regressionReport(sim) if options.regression else metricsReport(sim, options)
    with open(os.path.join(options.out, "metrics.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    writeEntries(sim.entries, os.path.join(options.out, "entries.tsv"),
                 lambda s: renderFinalStrokesToRTFCRE(keyboard, s))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
