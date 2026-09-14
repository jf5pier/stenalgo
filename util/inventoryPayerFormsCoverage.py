#!/bin/env python
#
# Read-only inventory (never modifies any file) for the pa:yer-family
# "-ayer" verbs (balayer, essayer, payer, ...). Both the "i"-form
# (balaie/balaierai/...) and the "y"-form (balaye/balayerai/...) are
# phonologically distinct, genuinely attested spellings of every -ayer verb
# (confirmed by the user: not homophones -- "balaie" /balɛ/ has no glide,
# "balaye" /balɛj/ does -- so both need their own correctly-tagged lexicon
# row wherever they exist as real words). This script does NOT decide a
# "primary" spelling; it inventories, per lemma and per stressed slot (the
# only slots where the "i"/"y" alternation exists at all -- see
# resources/verbiste/conjugations-fr.xml's "pa:yer" template: présent
# 1s/2s/3s/3p, futur-simple/conditionnel (all persons), subjonctif présent
# 1s/2s/3s/3p, imperatif 2s), which of the two forms are present as
# correctly-tagged VER rows in resources/LexiqueMixte.tsv and which are
# missing entirely.
#
# NOTE: src/verbparadigm.py's parseConjugationTemplates only ever keeps the
# FIRST <i> child of each <p> (ElementTree's .find() semantics) -- the
# second alternative in the XML is currently inert, unused data. This script
# parses the raw XML directly to recover both alternatives for its own
# read-only cross-check; it does not change how the codebase's own
# generateOrthoForm behaves.
#
# Output: for each (lemma, slot), one of:
#   BOTH_PRESENT     -- both forms exist as their own tagged row
#   ONLY_I_PRESENT   -- only the "i"-form exists; "y"-form row missing
#   ONLY_Y_PRESENT   -- only the "y"-form exists; "i"-form row missing
#   NEITHER_PRESENT  -- neither form is in the lexicon at all for this slot
# --dump-csv writes the full per-slot inventory for review.
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
TEMPLATE_NAME = "pa:yer"


def rawDualEndingsForTemplate(xmlPath: str, templateName: str) -> dict[str, list[list[str]]]:
    """Maps code (e.g. "ind:pre") -> list of alternative-lists (one per person
    slot), reading ALL <i> children per <p> directly from the XML (unlike
    parseConjugationTemplates, which only keeps the first)."""
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


def dualSlots(rawForms: dict[str, list[list[str]]]) -> list[tuple[str, str, str, str]]:
    """Returns (code, personNumber, iForm, yForm) for every slot that has
    exactly 2 alternatives (the "i"/"y" alternation) -- single-alternative
    slots (imparfait, passé-simple, participe, unstressed persons) are
    skipped since there's nothing to inventory there."""
    slots: list[tuple[str, str, str, str]] = []
    for code, endingsList in rawForms.items():
        personIndex = IMPERATIVE_PERSON_INDEX if code == "imp:pre" else FINITE_PERSON_INDEX
        for personNumber, index in personIndex.items():
            if index >= len(endingsList):
                continue
            alternatives = endingsList[index]
            if len(alternatives) != 2:
                continue
            iForm, yForm = alternatives
            slots.append((code, personNumber, iForm, yForm))
    return slots


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only inventory of which -ayer 'i'-form/'y'-form "
        "spellings exist vs. are missing in the lexicon, per lemma and slot."
    )
    parser.add_argument("--dump-csv", default=None,
                         help="Write the full per-(lemma,slot) inventory to this CSV path.")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    template = conjugationTemplates[TEMPLATE_NAME]

    payerLemmas = sorted(
        lemme for lemme, name in verbisteTemplates.items()
        if getTrustedTemplate(lemme, verbisteTemplates, exceptions) == TEMPLATE_NAME
    )

    rawForms = rawDualEndingsForTemplate(VERBISTE_CONJUGATIONS_PATH, TEMPLATE_NAME)
    slots = dualSlots(rawForms)

    # index: (lemme, ortho) -> set of tags present in infoVerb, restricted to VER rows.
    rowsByLemmeOrtho: dict[tuple[str, str], set[str]] = {}
    with open(LEXICON_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["cgram"] != "VER":
                continue
            tags = {tag for tag in row["infover"].split(";") if tag}
            key = (row["lemme"], row["ortho"])
            rowsByLemmeOrtho.setdefault(key, set()).update(tags)

    results: list[tuple[str, str, str, str, str, str, str]] = []
    # (lemme, code, personNumber, iOrtho, yOrtho, iPresent, yPresent)
    for lemme in payerLemmas:
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError:
            continue
        for code, personNumber, iEnding, yEnding in slots:
            tag = f"{code}:{personNumber}"
            iOrtho = radical + iEnding
            yOrtho = radical + yEnding
            iTags = rowsByLemmeOrtho.get((lemme, iOrtho), set())
            yTags = rowsByLemmeOrtho.get((lemme, yOrtho), set())
            iPresent = tag in iTags
            yPresent = tag in yTags
            results.append((lemme, code, personNumber, iOrtho, yOrtho,
                             "yes" if iPresent else "no", "yes" if yPresent else "no"))

    statusCounts: Counter[str] = Counter()
    byLemmeStatus: dict[str, Counter[str]] = {}
    for lemme, code, personNumber, iOrtho, yOrtho, iPresent, yPresent in results:
        if iPresent == "yes" and yPresent == "yes":
            status = "BOTH_PRESENT"
        elif iPresent == "yes":
            status = "ONLY_I_PRESENT"
        elif yPresent == "yes":
            status = "ONLY_Y_PRESENT"
        else:
            status = "NEITHER_PRESENT"
        statusCounts[status] += 1
        byLemmeStatus.setdefault(lemme, Counter())[status] += 1

    print(f"pa:yer-family lemmas found: {len(payerLemmas)}")
    print(f"Dual-form slots per lemma: {len(slots)}")
    print(f"Total (lemma, slot) combinations inventoried: {len(results)}\n")
    print("=== Summary ===")
    for status in ("BOTH_PRESENT", "ONLY_I_PRESENT", "ONLY_Y_PRESENT", "NEITHER_PRESENT"):
        print(f"  {status}: {statusCounts[status]}")

    print("\n=== Per-lemma breakdown (lemmas with >=1 missing form) ===")
    for lemme in payerLemmas:
        counts = byLemmeStatus.get(lemme, Counter())
        missing = counts["ONLY_I_PRESENT"] + counts["ONLY_Y_PRESENT"] + counts["NEITHER_PRESENT"]
        if missing == 0:
            continue
        print(f"  {lemme}: both={counts['BOTH_PRESENT']} only_i={counts['ONLY_I_PRESENT']} "
              f"only_y={counts['ONLY_Y_PRESENT']} neither={counts['NEITHER_PRESENT']}")

    if args.dump_csv:
        with open(args.dump_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["lemme", "code", "personNumber", "iOrtho", "yOrtho", "iPresent", "yPresent"])
            for row in results:
                writer.writerow(row)
        print(f"\nWrote {len(results)} rows to {args.dump_csv}")


if __name__ == "__main__":
    main()
