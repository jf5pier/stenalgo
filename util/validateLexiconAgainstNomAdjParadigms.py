#!/bin/env python
#
# Scans resources/LexiqueMixte.tsv (+ resources/LexiqueSynthetic.tsv) for NOM
# lemmas missing an "s"/"p" row or ADJ lemmas missing one of their
# m_s/m_p/f_s/f_p rows -- the noun/adjective analog of
# util/validateLexiconAgainstVerbiste.py, using src/nomAdjParadigm.py's
# enumeration-based slot detection instead of a Verbiste-template
# comparison (a NOM/ADJ paradigm has a small, fixed slot set, so there's no
# need for detectUndersampledLemmas-style sibling comparison).
#
# For every lemmeGramCat with a missing slot, this classifies the gap:
#   TAG_GAP               -- the expected ortho for the missing slot already
#                             exists as an attested row of the same lemma,
#                             just under a different/blank gender or number
#                             tag (a cheap, hand-fixable tagging bug, not a
#                             missing form -- same class as
#                             util/fixParticipeMissingNombre.py's fixes).
#   SUSPECTED_INVARIABLE  -- matches a known-regular invariable pattern (a
#                             NOM singular already ending in s/x/z) or is
#                             listed in resources/nomAdjModelExceptions.tsv
#                             with status=invariable -- not a gap to fill.
#   MISSING_FORM          -- genuinely absent; generated either straight
#                             from Morphalou (authoritative when it has an
#                             answer -- see generateAuthoritativeForm) or,
#                             absent that, from src/nomAdjParadigm.py's
#                             donor-ending-class derivation, confident
#                             enough (matchRate/donorCount) to generate.
#   MORPHALOU_NO_PHON     -- Morphalou confirms the correct ortho for this
#                             slot but the donor table has no confident
#                             phon/syllable-breakdown -- needs a human to
#                             add an override_phonology to
#                             resources/nomAdjModelExceptions.tsv.
#   LOW_CONFIDENCE        -- genuinely absent, and neither Morphalou nor the
#                             donor table has an answer -- needs a human
#                             decision (an exceptions-file entry), not a
#                             guess.
#
# Report-only: never modifies any file. Prints per-type counts and a sample
# of concrete lemmas for each type. Use --dump-csv to write every flagged
# lemma/slot (with its type) to a CSV for full review. Pass --morphalou to
# point at a local Morphalou3.1_CSV.csv (see util/generateMissingNomAdjForms.py's
# module docstring); without it, MISSING_FORM/LOW_CONFIDENCE fall back to
# donor-table-only classification (unverified against an external source).
import argparse
import csv
import os
from collections import Counter

from src.nomAdjParadigm import (
    MorphalouIndex,
    NomAdjEndingTables,
    NomAdjModelException,
    Slot,
    attestedSlots,
    chooseSourceSlot,
    deriveNomAdjEndingTables,
    generateAuthoritativeForm,
    isSuspectedInvariableForm,
    loadAllOrthosByLemme,
    loadMorphalouIndex,
    loadNomAdjModelExceptions,
    loadWords,
    missingSlots,
)
from src.word import GramCat, LemmeGramCat, Word

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
EXCEPTIONS_PATH = "resources/nomAdjModelExceptions.tsv"
MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"

TAG_GAP = "TAG_GAP"
SUSPECTED_INVARIABLE = "SUSPECTED_INVARIABLE"
MISSING_FORM = "MISSING_FORM"
MORPHALOU_NO_PHON = "MORPHALOU_NO_PHON"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
ALL_FLAG_TYPES = (TAG_GAP, SUSPECTED_INVARIABLE, MISSING_FORM, MORPHALOU_NO_PHON, LOW_CONFIDENCE)


class Flag:
    def __init__(self, flagType: str, lemmeGramCat: LemmeGramCat, gramCat: GramCat, slot: Slot, note: str):
        self.flagType = flagType
        self.lemmeGramCat = lemmeGramCat
        self.gramCat = gramCat
        self.slot = slot
        self.note = note


def orthoAlreadyPresentElsewhere(lemme: str, expectedOrtho: str, allOrthosByLemme: dict[str, set[str]]) -> bool:
    return expectedOrtho in allOrthosByLemme.get(lemme, set())


def classifyMissingSlot(
    lemmeGramCat: LemmeGramCat,
    slotMap: dict[Slot, Word],
    gramCat: GramCat,
    slot: Slot,
    allOrthosByLemme: dict[str, set[str]],
    tables: NomAdjEndingTables,
    exceptions: dict[tuple[str, str], NomAdjModelException],
    morphalou: MorphalouIndex | None,
) -> Flag:
    sourceSlot = chooseSourceSlot(slotMap, gramCat)
    assert sourceSlot is not None
    sourceWord = slotMap[sourceSlot]
    lemme = sourceWord.lemme

    exception = exceptions.get((lemme, gramCat.name))
    if exception is not None and exception.status == "invariable":
        return Flag(SUSPECTED_INVARIABLE, lemmeGramCat, gramCat, slot, "exceptions table: invariable")

    if isSuspectedInvariableForm(sourceWord, slot):
        if orthoAlreadyPresentElsewhere(lemme, sourceWord.ortho, allOrthosByLemme):
            return Flag(TAG_GAP, lemmeGramCat, gramCat, slot,
                        f"ortho {sourceWord.ortho!r} already attested, just missing the {slot} tag")
        return Flag(SUSPECTED_INVARIABLE, lemmeGramCat, gramCat, slot,
                    f"regular invariable pattern: {sourceWord.ortho!r}")

    candidate, source = generateAuthoritativeForm(sourceWord, slot, tables, morphalou)
    if candidate is not None:
        if orthoAlreadyPresentElsewhere(lemme, candidate.ortho, allOrthosByLemme):
            return Flag(TAG_GAP, lemmeGramCat, gramCat, slot,
                        f"generated ortho {candidate.ortho!r} already attested, just missing the {slot} tag")
        return Flag(MISSING_FORM, lemmeGramCat, gramCat, slot,
                    f"from {sourceSlot} {sourceWord.ortho!r} -> {candidate.ortho!r} ({source})")

    if source == "morphalou_no_phon":
        return Flag(MORPHALOU_NO_PHON, lemmeGramCat, gramCat, slot,
                    f"Morphalou confirms the ortho but donor table has no confident phon for {sourceSlot}")
    return Flag(LOW_CONFIDENCE, lemmeGramCat, gramCat, slot,
                f"no confident donor class for {sourceSlot} {sourceWord.ortho!r}, and no Morphalou entry")


def scan(
    words: list[Word],
    allOrthosByLemme: dict[str, set[str]],
    exceptions: dict[tuple[str, str], NomAdjModelException],
    morphalou: MorphalouIndex | None,
) -> list[Flag]:
    tables = deriveNomAdjEndingTables(words)
    slotsByLemme = attestedSlots(words)

    flags: list[Flag] = []
    for lemmeGramCat, slotMap in slotsByLemme.items():
        gramCat = next(iter(slotMap.values())).gramCat
        for slot in sorted(missingSlots(slotMap, gramCat)):
            flags.append(classifyMissingSlot(
                lemmeGramCat, slotMap, gramCat, slot, allOrthosByLemme, tables, exceptions, morphalou
            ))
    return flags


def printReport(flags: list[Flag]) -> None:
    counts = Counter(flag.flagType for flag in flags)
    print("=== NOM/ADJ paradigm gap report ===")
    for flagType in ALL_FLAG_TYPES:
        print(f"{flagType}: {counts.get(flagType, 0)}")
    print()
    for flagType in ALL_FLAG_TYPES:
        sample = [f for f in flags if f.flagType == flagType][:10]
        if not sample:
            continue
        print(f"--- {flagType} (showing up to 10) ---")
        for flag in sample:
            print(f"  {flag.lemmeGramCat} {flag.slot}: {flag.note}")
        print()


def writeCsv(flags: list[Flag], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(["flagType", "lemmeGramCat", "gramCat", "gender", "number", "note"])
        for flag in flags:
            writer.writerow([flag.flagType, flag.lemmeGramCat, flag.gramCat.name, *flag.slot, flag.note])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-csv", metavar="PATH", help="Write every flagged lemma/slot to a CSV.")
    parser.add_argument("--morphalou", default=MORPHALOU_PATH_DEFAULT, help="Path to Morphalou3.1_CSV.csv")
    args = parser.parse_args()

    morphalou = None
    if os.path.exists(args.morphalou):
        morphalou = loadMorphalouIndex(args.morphalou)
    else:
        print(f"WARNING: Morphalou not found at {args.morphalou!r} -- MISSING_FORM/LOW_CONFIDENCE will be "
              f"donor-table-only, unverified against an external source.\n")

    words = loadWords([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
    allOrthosByLemme = loadAllOrthosByLemme([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
    exceptions = loadNomAdjModelExceptions(EXCEPTIONS_PATH)
    flags = scan(words, allOrthosByLemme, exceptions, morphalou)
    printReport(flags)
    if args.dump_csv:
        writeCsv(flags, args.dump_csv)
        print(f"Wrote {len(flags)} flags to {args.dump_csv}")


if __name__ == "__main__":
    main()
