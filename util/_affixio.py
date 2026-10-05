"""
Shared loading of the affix abbreviations, factored out of `util/export_affix_dictionary.py`,
`util/validate_affix_markings.py` and `util/export_affix_lessons.py`: load the stable theory, build the candidate
pool, and run `buildAbbreviations` with the committed `affix_rules.json`.

Requires the same inputs as `util.export_plover_dictionary` plus `affix_rules.json`.
"""
import time
from dataclasses import dataclass

from src import affixes as A
from src.affixabbrev import Abbreviation, AbbreviationStats, buildAbbreviations, loadRuleSpecs, theoryOutlines
from src.keyboard import Starboard, Strokes, canonicalizeStrokes
from util._theoryio import loadPhoneticAndDisambiguatedTheory


@dataclass
class LoadedAbbreviations:
    abbreviations: list[Abbreviation]
    stats: AbbreviationStats
    records: list[A.WordRecord]
    pool: dict  # type: ignore[type-arg]
    ctx: A.SimContext
    longOutline: dict[int, Strokes]
    disambiguated: dict  # type: ignore[type-arg]
    taken: set[Strokes]


def loadAbbreviations(starboard: Starboard, rulesJson: str = "affix_rules.json", verbose: bool = True) -> LoadedAbbreviations:
    t0 = time.time()
    phonetic, disambiguated, _wordToStrokes, _wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(starboard)
    records, skipped = A.extractRecords(phonetic, disambiguated)
    if verbose:
        print(f"{len(records)} records ({skipped} skipped) in {time.time() - t0:.0f}s", flush=True)
    seedPairs, _fams = A.loadSeeds()
    pool = A.buildCandidates(records, seedPairs)
    if verbose:
        print(f"pool {len(pool)} nodes in {time.time() - t0:.0f}s", flush=True)
    ctx = A.SimContext(starboard, records)
    longOutline = {r.idx: canonicalizeStrokes(A.fullStrokesOf(r)) for r in records}
    taken = theoryOutlines(disambiguated)
    abbreviations, stats = buildAbbreviations(loadRuleSpecs(rulesJson), pool, ctx, taken, longOutline)
    return LoadedAbbreviations(abbreviations, stats, records, pool, ctx, longOutline, disambiguated, taken)
