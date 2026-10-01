"""
Export the OPTIONAL affix abbreviations (src/affixabbrev.py) as a second Plover dictionary, on top of the stable
theory: short outline -> the same word. The main dictionary (`plover_stenalgo_dictionary.json`) is not changed and
stays complete without it; enable this one in Plover (higher priority) to use the abbreviations.

Outputs:
- plover_stenalgo_affix_dictionary.json  steno -> spelling (only abbreviations, sorted by steno)
- affix_abbreviations.tsv                 spelling, long steno, short steno, strokes saved, rule rank, anchor, k, frequency

Run: python -m util.export_affix_dictionary
Requires the stable theory (same inputs as util.export_plover_dictionary) and affix_rules.json, the rule list
written by `python -m util.affix_scan --part b --sweep --partial-overlap --settings D`
(scratch/affix-sweep-partial/D/affix-rules.json, copied to the repo root when adopted). A change of lexicon or
layout needs the affix scan (and affix_rules.json) rerun first: the rule keys were chosen against that theory.
"""
import json
import os
import time

from src import affixes as A
from src.affixabbrev import buildAbbreviations, loadRuleSpecs, theoryOutlines
from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory

KEYBOARD_JSON = "starboard3h.json"
RULES_JSON = "affix_rules.json"
MAIN_DICTIONARY = "plover_stenalgo_dictionary.json"
OUTPUT_DICTIONARY = "plover_stenalgo_affix_dictionary.json"
OUTPUT_TSV = "affix_abbreviations.tsv"


def main() -> None:
    t0 = time.time()
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    if not os.path.exists(RULES_JSON):
        raise RuntimeError(f"{RULES_JSON} not found: run the affix scan (see this module's docstring) and copy its affix-rules.json.")
    # the rules were selected with this binding mode (src.affixes.RULE_PARTIAL_OVERLAP, docs/AFFIX_RULES.md)
    A.RULE_PARTIAL_OVERLAP = True

    phonetic, disambiguated, _wordToStrokes, _wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(starboard)
    records, skipped = A.extractRecords(phonetic, disambiguated)
    print(f"{len(records)} records ({skipped} skipped) in {time.time() - t0:.0f}s", flush=True)
    seedPairs, _fams = A.loadSeeds()
    pool = A.buildCandidates(records, seedPairs)
    print(f"pool {len(pool)} nodes in {time.time() - t0:.0f}s", flush=True)
    ctx = A.SimContext(starboard, records)
    longOutline = {r.idx: A.canonicalizeStrokes(A.fullStrokesOf(r)) for r in records}

    abbreviations, stats = buildAbbreviations(
        loadRuleSpecs(RULES_JSON), pool, ctx, theoryOutlines(disambiguated), longOutline)

    stenoDict: dict[str, str] = {}
    rows = []
    for a in abbreviations:
        short = renderFinalStrokesToRTFCRE(starboard, a.outline)
        if short in stenoDict:
            raise RuntimeError(f"two abbreviations render to {short!r}: {stenoDict[short]!r} / {a.ortho!r}")
        stenoDict[short] = a.ortho
        rows.append((a, short, renderFinalStrokesToRTFCRE(starboard, a.longOutline)))
    if os.path.exists(MAIN_DICTIONARY):
        with open(MAIN_DICTIONARY, encoding="utf-8") as f:
            main = json.load(f)
        clash = [s for s in stenoDict if s in main]
        if clash:
            raise RuntimeError(f"{len(clash)} abbreviations collide with the main dictionary, e.g. {clash[:5]}")

    with open(OUTPUT_DICTIONARY, "w", encoding="utf-8") as f:
        json.dump(stenoDict, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(OUTPUT_TSV, "w", encoding="utf-8") as f:
        f.write("spelling\tlong\tshort\tsaved\trank\tanchor\tk\tfrequency\n")
        for a, short, long in rows:
            f.write(f"{a.ortho}\t{long}\t{short}\t{a.saved}\t{a.rank}\t{a.anchor}\t{a.k}\t{a.frequency:.2f}\n")

    savedFreq = sum(a.frequency * a.saved for a in abbreviations)
    print(f"Wrote {OUTPUT_DICTIONARY} ({len(stenoDict)} abbreviations) and {OUTPUT_TSV}: {stats.carriers} carrier words, "
          f"{stats.abbreviated} abbreviated, {stats.noOption} with no allowed form, {stats.outranked} lost a shared "
          f"outline to a more frequent spelling; strokes saved x frequency = {savedFreq:.0f} ({time.time() - t0:.0f}s).")
    print("abbreviations per rule rank:", dict(sorted(stats.byRank.items())))


if __name__ == "__main__":
    main()
