#!/bin/env python
#
# Read-only inventory (never modifies any file) for the ass:eoir template
# (asseoir, rasseoir -- surseoir uses its own separate surs:eoir template
# and isn't flagged by the validator, so it's out of scope here). Mirrors
# util/inventoryPayerFormsCoverage.py's approach for pa:yer, generalized to
# ass:eoir's alternation shape, which is NOT a simple 2-way split:
#
#   - présent/imparfait/imperatif-présent/subjonctif-présent: 2 alternatives
#     per slot ("ie"-form e.g. "ieds"/"assieds", "oi"-form e.g. "ois"/
#     "assois").
#   - futur-simple/conditionnel-présent: 3 alternatives per slot ("iérai"/
#     "assiérai", "eyerai"/"asseyerai", "oirai"/"assoirai") -- a third,
#     distinct "eye"-radical form Verbiste itself lists but
#     src/verbparadigm.py's parseConjugationTemplates never uses (it only
#     keeps the FIRST <i> per <p>, same ElementTree.find() limitation noted
#     in inventoryPayerFormsCoverage.py).
#
# All alternatives at a given slot are phonologically genuine, independently
# attested French conjugations (not a "pick one" situation) -- this script
# inventories, per lemma/slot/alternative, whether a correctly-tagged VER
# row already exists in resources/LexiqueMixte.tsv or is missing.
#
# Output: for each (lemma, slot), one row per alternative showing present/
# absent, plus a summary status:
#   ALL_PRESENT      -- every alternative for this slot exists
#   PARTIAL          -- some but not all alternatives exist
#   NONE_PRESENT     -- no alternative exists for this slot at all
# --dump-csv writes the full per-(lemma, slot, alternative) inventory.
import argparse
import csv
import xml.etree.ElementTree as ET
from collections import Counter

from src.verbparadigm import (
    FINITE_PERSON_INDEX,
    IMPERATIVE_PERSON_INDEX,
    MOOD_TAG_TO_CODE,
    TENSE_TAG_TO_CODE,
    getTrustedTemplate,
    infinitiveRadical,
    loadVerbModelExceptions,
    loadVerbisteTemplates,
    parseConjugationTemplates,
)

LEXICON_PATH = "resources/LexiqueMixte.tsv"
VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"
TEMPLATE_NAME = "ass:eoir"


def rawAlternativesForTemplate(xmlPath: str, templateName: str) -> dict[str, list[list[str]]]:
    """Maps code (e.g. "ind:pre") -> list of alternative-lists (one per
    person slot), reading ALL <i> children per <p> directly from the XML."""
    tree = ET.parse(xmlPath)
    forms: dict[str, list[list[str]]] = {}
    for templateElement in tree.getroot().findall("template"):
        if templateElement.get("name") != templateName:
            continue
        for moodElement in templateElement:
            moodCode = MOOD_TAG_TO_CODE.get(moodElement.tag)
            if moodCode is None:
                continue
            for tenseElement in moodElement:
                tenseCode = TENSE_TAG_TO_CODE.get(tenseElement.tag)
                if tenseCode is None:
                    continue
                endings: list[list[str]] = []
                for inflectionElement in tenseElement.findall("p"):
                    alternatives = [i.text or "" for i in inflectionElement.findall("i")]
                    endings.append(alternatives)
                code = moodCode if moodCode == "inf" else f"{moodCode}:{tenseCode}"
                forms[code] = endings
        break
    return forms


def multiSlots(rawForms: dict[str, list[list[str]]]) -> list[tuple[str, str, list[str]]]:
    """Returns (code, personNumber, alternatives) for every slot with 2+
    alternatives -- single-alternative slots (passé-simple, participe-passé,
    subjonctif-imparfait, ...) are skipped, nothing to inventory there."""
    slots: list[tuple[str, str, list[str]]] = []
    for code, endingsList in rawForms.items():
        personIndex = IMPERATIVE_PERSON_INDEX if code == "imp:pre" else FINITE_PERSON_INDEX
        for personNumber, index in personIndex.items():
            if index >= len(endingsList):
                continue
            alternatives = endingsList[index]
            if len(alternatives) < 2:
                continue
            slots.append((code, personNumber, alternatives))
    return slots


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only inventory of which ass:eoir alternative "
        "spellings exist vs. are missing in the lexicon, per lemma and slot."
    )
    parser.add_argument("--dump-csv", default=None,
                         help="Write the full per-(lemma,slot,alternative) inventory to this CSV path.")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    template = conjugationTemplates[TEMPLATE_NAME]

    lemmas = sorted(
        lemme for lemme, name in verbisteTemplates.items()
        if getTrustedTemplate(lemme, verbisteTemplates, exceptions) == TEMPLATE_NAME
    )

    rawForms = rawAlternativesForTemplate(VERBISTE_CONJUGATIONS_PATH, TEMPLATE_NAME)
    slots = multiSlots(rawForms)

    rowsByLemmeOrtho: dict[tuple[str, str], set[str]] = {}
    with open(LEXICON_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["cgram"] != "VER":
                continue
            tags = {tag for tag in row["infover"].split(";") if tag}
            key = (row["lemme"], row["ortho"])
            rowsByLemmeOrtho.setdefault(key, set()).update(tags)

    results: list[tuple[str, str, str, int, str, str, str]] = []
    # (lemme, code, personNumber, altIndex, altEnding, ortho, present)
    for lemme in lemmas:
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError:
            continue
        for code, personNumber, alternatives in slots:
            tag = f"{code}:{personNumber}"
            for altIndex, ending in enumerate(alternatives):
                ortho = radical + ending
                tags = rowsByLemmeOrtho.get((lemme, ortho), set())
                present = tag in tags
                results.append((lemme, code, personNumber, altIndex, ending, ortho,
                                 "yes" if present else "no"))

    statusCounts: Counter[str] = Counter()
    byLemmeStatus: dict[str, Counter[str]] = {}
    bySlot: dict[tuple[str, str], list[tuple[str, str, str, str]]] = {}
    for lemme, code, personNumber, altIndex, ending, ortho, present in results:
        bySlot.setdefault((lemme, f"{code}:{personNumber}"), []).append(
            (str(altIndex), ending, ortho, present))

    for (lemme, slot), alts in bySlot.items():
        presentCount = sum(1 for *_, present in alts if present == "yes")
        if presentCount == len(alts):
            status = "ALL_PRESENT"
        elif presentCount == 0:
            status = "NONE_PRESENT"
        else:
            status = "PARTIAL"
        statusCounts[status] += 1
        byLemmeStatus.setdefault(lemme, Counter())[status] += 1

    print(f"ass:eoir-family lemmas found: {len(lemmas)} ({', '.join(lemmas)})")
    print(f"Multi-alternative slots per lemma: {len(slots)}")
    print(f"Total (lemma, slot) combinations inventoried: {len(bySlot)}\n")
    print("=== Summary ===")
    for status in ("ALL_PRESENT", "PARTIAL", "NONE_PRESENT"):
        print(f"  {status}: {statusCounts[status]}")

    print("\n=== PARTIAL slots (some but not all alternatives present -- the actual gaps) ===")
    for (lemme, slot), alts in sorted(bySlot.items()):
        presentCount = sum(1 for *_, present in alts if present == "yes")
        if 0 < presentCount < len(alts):
            altDesc = ", ".join(f"{ortho}({present})" for _, ending, ortho, present in alts)
            print(f"  {lemme} {slot}: {altDesc}")

    print("\n=== Per-lemma breakdown ===")
    for lemme in lemmas:
        counts = byLemmeStatus.get(lemme, Counter())
        print(f"  {lemme}: all={counts['ALL_PRESENT']} partial={counts['PARTIAL']} "
              f"none={counts['NONE_PRESENT']}")

    if args.dump_csv:
        with open(args.dump_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["lemme", "code", "personNumber", "altIndex", "ending", "ortho", "present"])
            for row in results:
                writer.writerow(row)
        print(f"\nWrote {len(results)} rows to {args.dump_csv}")


if __name__ == "__main__":
    main()
