#!/bin/env python
#
# Batch 9 (UNDEFINED_SLOT cluster G) of the lexicon-defect triage plan: two
# independent fixes for "s:ourdre" (one of French's most famously defective
# verbs -- prescriptively limited to the infinitive plus 3rd person).
#
#   - Adds 2 legitimate, strictly-3rd-person slots the template left blank:
#     - participe-présent: "sourdant" is the standard, dictionary-recognized
#       present participle of sourdre (e.g. "des difficultés sourdant de
#       tous côtés"), attested in resources/LexiqueMixte.tsv with nonzero
#       book-frequency; the template's participe-présent slot was simply
#       empty.
#     - Subjonctif:présent 3s "sourde": a regular mechanical extension of
#       the already-defined présent 3s ("sourd"), attested with nonzero
#       frequency in both books and films.
#     - Indicatif futur-simple 3p "sourdront": a regular mechanical
#       extension of the already-defined présent 3p ("ourdent"), attested
#       with nonzero book-frequency.
#     All 3 additions stay strictly 3rd-person, consistent with the verb's
#     well-documented defectiveness -- no 1st/2nd-person or unattested
#     tense is added.
#   - Deletes the "sourds" row (tagged imp:pre:2s;ind:pre:1s;): 1st/2nd
#     person is impossible for this verb by every grammar reference. This
#     row's frequency is 0.0 in books and 0.11 only in films -- and "sourds"
#     already exists as its own correct ADJ/NOM row (plural of "sourd" =
#     deaf) -- the exact same pattern as the "neiges"/"bruinasse" tagging
#     artifacts fixed earlier this batch (Lexique383's own automated
#     tagger matching a common word's spelling against a rare verb's
#     paradigm).
#
# Because the Conditionnel's and Subjonctif's <présent> blocks are
# byte-identical empty text in this template, the sub:pre:3s addition is
# scoped to the <Subjonctif>...</Subjonctif> sub-block specifically (not a
# whole-template string replace) so the Conditionnel's présent is never
# touched.
#
# Confirmed the "sourds" row is present in resources/Lexique383.tsv too
# (checked directly), so both lexicon files are corrected for the deletion;
# the template fix only touches resources/verbiste/conjugations-fr.xml.
#
# Dry-run by default: only reads and reports. --apply writes both changes
# in place. Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
TEMPLATE_NAME = "s:ourdre"

PARTICIPE_PRESENT_OLD = "<participe-présent>\n\t\t\t<p></p>\n\t\t</participe-présent>"
PARTICIPE_PRESENT_NEW = "<participe-présent>\n\t\t\t<p><i>ourdant</i></p>\n\t\t</participe-présent>"

FUTUR_SIMPLE_OLD = (
    "<futur-simple>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t</futur-simple>"
)
FUTUR_SIMPLE_NEW = (
    "<futur-simple>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p><i>ourdront</i></p>\n"
    "\t\t</futur-simple>"
)

SUBJONCTIF_PRESENT_OLD = (
    "<présent>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t</présent>"
)
SUBJONCTIF_PRESENT_NEW = (
    "<présent>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p><i>ourde</i></p>\n"
    "\t\t\t<p></p>\n\t\t\t<p></p>\n\t\t\t<p></p>\n"
    "\t\t</présent>"
)

ROW_TO_DELETE = ("sourds", "sourdre", "VER", "imp:pre:2s;ind:pre:1s;")


def extractBlock(content: str, tagPattern: str) -> tuple[str, int, int]:
    pattern = re.compile(tagPattern, re.DOTALL)
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one match for {tagPattern!r}, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildCorrectedTemplate(templateBlock: str) -> tuple[str, int, list[str]]:
    corrected = templateBlock
    applied = 0
    warnings: list[str] = []

    for old, new in ((PARTICIPE_PRESENT_OLD, PARTICIPE_PRESENT_NEW),
                      (FUTUR_SIMPLE_OLD, FUTUR_SIMPLE_NEW)):
        count = corrected.count(old)
        if count != 1:
            warnings.append(f"expected 1 occurrence, found {count}: {old!r}")
            continue
        corrected = corrected.replace(old, new, 1)
        applied += 1

    # Subjonctif's présent is byte-identical to Conditionnel's, so scope the
    # replacement to the <Subjonctif>...</Subjonctif> sub-block only.
    try:
        subjonctifBlock, subStart, subEnd = extractBlock(corrected, r"<Subjonctif>.*?</Subjonctif>")
    except ValueError as e:
        warnings.append(str(e))
        return corrected, applied, warnings
    count = subjonctifBlock.count(SUBJONCTIF_PRESENT_OLD)
    if count != 1:
        warnings.append(f"expected 1 occurrence of the Subjonctif présent block, found {count}")
    else:
        newSubjonctifBlock = subjonctifBlock.replace(SUBJONCTIF_PRESENT_OLD, SUBJONCTIF_PRESENT_NEW, 1)
        corrected = corrected[:subStart] + newSubjonctifBlock + corrected[subEnd:]
        applied += 1

    return corrected, applied, warnings


def deleteRowFromLexicon(path: str, apply: bool) -> tuple[bool, int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    found = False
    outputLines = [lines[0]]
    for i in range(1, len(lines)):
        if not lines[i].strip():
            outputLines.append(lines[i])
            continue
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx], fields[cgramIdx], fields[infoverIdx])
        if key == ROW_TO_DELETE:
            found = True
            if not apply:
                outputLines.append(lines[i])
            continue
        outputLines.append(lines[i])

    if apply and found:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(outputLines)

    return found, len(lines) - 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix s:ourdre: add 3 legitimate 3rd-person template "
        "slots (participe-présent, sub:pre:3s, ind:fut:3p) and delete the "
        "erroneous 'sourds' 1st/2nd-person row."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to conjugations-fr.xml and both lexicon "
        "files (default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()
    templateBlock, start, end = extractBlock(
        content, r'<template name="' + re.escape(TEMPLATE_NAME) + r'">.*?</template>')
    correctedBlock, applied, warnings = buildCorrectedTemplate(templateBlock)

    print(f"=== {TEMPLATE_NAME} template ===")
    print(f"Sections corrected: {applied} (expected 3)")
    for w in warnings:
        print(f"  WARNING: {w}")
    print()

    if args.apply and applied:
        newContent = content[:start] + correctedBlock + content[end:]
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"--apply: wrote {applied} correction(s) to {CONJUGATIONS_PATH}\n")

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        found, _ = deleteRowFromLexicon(path, args.apply)
        print(f"=== {path} ===")
        print(f"  DELETE 'sourds' row: {'found' if found else 'NOT FOUND'}")
        if args.apply and found:
            print(f"  --apply: updated {path}")
        print()


if __name__ == "__main__":
    main()
