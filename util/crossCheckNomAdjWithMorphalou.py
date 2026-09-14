#!/bin/env python
#
# Independent, external audit of the project's NOM/ADJ data against
# Morphalou (ATILF/CNRTL, LGPL-LR), a human-curated French inflected-forms
# lexicon (159,271 lemmas / 976,570 forms) -- see the conversation: internal
# donor-agreement (src/nomAdjParadigm.py) is not linguistic validation, and
# util/generateMissingNomAdjForms.py now treats Morphalou as authoritative
# for generation itself (generateAuthoritativeForm). This script is the
# standing, read-only audit trail for both halves of that picture:
#
#   --attested (default: on)  Checks every row ALREADY in
#       resources/LexiqueMixte.tsv/LexiqueSynthetic.tsv (not just gaps) --
#       answers "is the training data itself clean?", since the donor
#       tables learn their patterns from these rows.
#   --candidates (default: on)  Checks what
#       util/generateMissingNomAdjForms.py would generate right now
#       (mirroring its own Morphalou-authoritative logic) -- mostly a
#       sanity echo of what that script already applies internally, useful
#       to confirm nothing regressed.
#
# For every checked (lemma, gramCat, gender, number), classifies:
#   MATCH        -- Morphalou has this slot with the identical ortho.
#   MISMATCH     -- Morphalou has this slot with a DIFFERENT ortho.
#   NOT_IN_MORPHALOU -- Morphalou has no entry for this lemma+category+slot
#                   at all -- Morphalou isn't 100% complete either (see the
#                   conversation: some rare/technical/loanword vocabulary,
#                   e.g. "procalmadiol", genuinely isn't in its ~140k
#                   lemmas), so this is inconclusive, not a contradiction.
#
# Report-only: never modifies any file.
import argparse
import csv
from collections import Counter

from src.nomAdjParadigm import (
    Lemme,
    MorphalouIndex,
    NomAdjModelException,
    attestedSlots,
    chooseSourceSlot,
    deriveNomAdjEndingTables,
    generateAuthoritativeForm,
    isSuspectedInvariableForm,
    loadMorphalouIndex,
    loadNomAdjModelExceptions,
    loadWords,
    missingSlots,
    morphalouOrthos,
)
from src.word import Word

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
EXCEPTIONS_PATH = "resources/nomAdjModelExceptions.tsv"
MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"

MATCH, MISMATCH, NOT_IN_MORPHALOU = "MATCH", "MISMATCH", "NOT_IN_MORPHALOU"


def classify(lemme: str, gramCatName: str, slot: tuple[str, str], ortho: str,
             morphalou: MorphalouIndex) -> tuple[str, set[str]]:
    slotsByGender = morphalou.get((lemme, gramCatName))
    if slotsByGender is None:
        return NOT_IN_MORPHALOU, set()
    orthos = slotsByGender.get(slot)
    if orthos is None:
        return NOT_IN_MORPHALOU, set()
    return (MATCH if ortho in orthos else MISMATCH), orthos


def checkAttested(words: list[Word], morphalou: MorphalouIndex) -> tuple[Counter, list[tuple[Word, set[str]]]]:
    """Cross-check every row already in the lexicon (not just gaps) -- validates the donor tables' own training data."""
    counts: Counter = Counter()
    mismatches: list[tuple[Word, set[str]]] = []
    for slotMap in attestedSlots(words).values():
        for slot, word in slotMap.items():
            outcome, morphalouOrthosFound = classify(word.lemme, word.gramCat.name, slot, word.ortho, morphalou)
            counts[outcome] += 1
            if outcome == MISMATCH:
                mismatches.append((word, morphalouOrthosFound))
    return counts, mismatches


def checkCandidates(
    words: list[Word], morphalou: MorphalouIndex, exceptions: dict[tuple[Lemme, str], NomAdjModelException]
) -> tuple[Counter, list[tuple[Word, set[str]]]]:
    """Cross-check what util/generateMissingNomAdjForms.py would generate right now (mirrors its own logic)."""
    tables = deriveNomAdjEndingTables(words)
    slotsByLemme = attestedSlots(words)
    counts: Counter = Counter()
    mismatches: list[tuple[Word, set[str]]] = []
    for lemmeGramCat, slotMap in slotsByLemme.items():
        gramCat = next(iter(slotMap.values())).gramCat
        for slot in missingSlots(slotMap, gramCat):
            sourceSlot = chooseSourceSlot(slotMap, gramCat)
            assert sourceSlot is not None
            sourceWord = slotMap[sourceSlot]
            if isSuspectedInvariableForm(sourceWord, slot):
                continue
            if (sourceWord.lemme, gramCat.name) in exceptions:
                continue
            candidate, source = generateAuthoritativeForm(sourceWord, slot, tables, morphalou)
            if candidate is None:
                continue
            # generateAuthoritativeForm already consulted Morphalou -- re-classify only to report
            # counts/samples here, not to second-guess its decision.
            known = morphalouOrthos(morphalou, candidate.lemme, candidate.gramCat, slot)
            if known is None:
                counts[NOT_IN_MORPHALOU] += 1
            elif candidate.ortho in known:
                counts[MATCH] += 1
            else:
                counts[MISMATCH] += 1
                mismatches.append((candidate, known))
    return counts, mismatches


def printSection(title: str, counts: Counter, mismatches: list[tuple[Word, set[str]]]) -> None:
    total = sum(counts.values())
    print(f"\n=== {title}: {total} checked ===")
    for outcome in (MATCH, MISMATCH, NOT_IN_MORPHALOU):
        n = counts.get(outcome, 0)
        print(f"{outcome}: {n} ({100 * n / total:.2f}%)" if total else f"{outcome}: 0")
    checked = counts.get(MATCH, 0) + counts.get(MISMATCH, 0)
    if checked:
        print(f"Of the {checked} candidates Morphalou could actually check: "
              f"{100 * counts.get(MATCH, 0) / checked:.2f}% matched exactly.")
    if mismatches:
        print(f"--- Sample MISMATCH (showing up to 20 of {len(mismatches)}) ---")
        for word, morphalouOrthos_ in mismatches[:20]:
            print(f"  {word.lemme}_{word.gramCat.name} {(word.gender, word.number)}: "
                  f"we have {word.ortho!r}, Morphalou has {sorted(morphalouOrthos_)!r}")


def writeCsv(mismatches: list[tuple[Word, set[str]]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["lemme", "gramCat", "gender", "number", "our_ortho", "morphalou_ortho"])
        for word, morphalouOrthos_ in mismatches:
            writer.writerow([word.lemme, word.gramCat.name, word.gender, word.number,
                              word.ortho, "|".join(sorted(morphalouOrthos_))])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--morphalou", default=MORPHALOU_PATH_DEFAULT, help="Path to Morphalou3.1_CSV.csv")
    parser.add_argument("--no-attested", action="store_true", help="Skip the already-attested-data audit.")
    parser.add_argument("--no-candidates", action="store_true", help="Skip the generation-candidates audit.")
    parser.add_argument("--dump-mismatches", metavar="PATH", help="Write every MISMATCH (both sections) to a CSV.")
    args = parser.parse_args()

    print(f"Loading Morphalou from {args.morphalou} ...")
    morphalou = loadMorphalouIndex(args.morphalou)
    print(f"Indexed {len(morphalou)} NOM/ADJ lemma groups from Morphalou.")

    words = loadWords([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
    exceptions = loadNomAdjModelExceptions(EXCEPTIONS_PATH)

    allMismatches: list[tuple[Word, set[str]]] = []
    if not args.no_attested:
        counts, mismatches = checkAttested(words, morphalou)
        printSection("Already-attested lexicon data", counts, mismatches)
        allMismatches += mismatches
    if not args.no_candidates:
        counts, mismatches = checkCandidates(words, morphalou, exceptions)
        printSection("Generation candidates (mirrors generateMissingNomAdjForms.py)", counts, mismatches)
        allMismatches += mismatches

    if args.dump_mismatches:
        writeCsv(allMismatches, args.dump_mismatches)
        print(f"\nWrote {len(allMismatches)} mismatches to {args.dump_mismatches}")


if __name__ == "__main__":
    main()
