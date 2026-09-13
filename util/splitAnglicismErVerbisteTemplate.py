#!/bin/env python
#
# Investigates and (with --apply) splits a second syllabification-only
# distinction out of Verbiste's "aim:er" conjugation template, into a new
# sibling template "squatt:er". Companion to splitEtudierVerbisteTemplate.py,
# which split off the 48 vowel-final/hiatus donors as "étudi:er" but
# deliberately left 4 further outliers alone.
#
# Background: after splitEtudierVerbisteTemplate.py's fix, a real end-to-end
# `util/completeVerbParadigms.py` dry run still showed a ~41% mismatch rate
# (flattened generated rawOrthosyllCV vs. ortho) -- essentially unchanged from
# the ~39% measured before *any* fix. Root cause: "aim:er"'s remaining donor
# pool still includes 4 anglicism borrowings with a doubled final consonant,
# syllabified "...X_e_r" instead of the ~3600 real donors' "...X_er"
# (reprogrammer -> "...mm_e_r", squatter/bitter -> "...tt_e_r",
# stripper -> "...pp_e_r"). Because deriveConjugationEndingTables derives one
# infinitive suffix per *template* (not per donor), these 4 words alone
# still collapse "aim:er"'s _longestCommonSuffix from "_er" down to "r" for
# ALL ~3600 donors, not just themselves -- the exact same collapse mechanism
# as the original bug, just from a smaller minority. This is what the ~41%
# mismatch rate traces back to.
#
# Fix: same technique as splitEtudierVerbisteTemplate.py -- duplicate
# "aim:er" (byte-identical orthographic endings; these 4 verbs conjugate
# completely regularly, e.g. "je squatte, nous squattons") as a new template
# "squatt:er" and repoint the 4 lemmas to it, so their outlier
# rawOrthosyllCV shape no longer pollutes "aim:er"'s own suffix derivation.
#
# Dry-run by default: only reads and reports. --apply inserts the new
# "squatt:er" template into resources/verbiste/conjugations-fr.xml (right
# after "aim:er"'s own template block) and rewrites the <t> tag of each of
# the 4 target lemmas in resources/verbiste/verbs-fr.xml, in place.
# Idempotent: a no-op (0 rows modified) if run again after a successful
# --apply.
import argparse
import re
import sys

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
VERBS_PATH = "resources/verbiste/verbs-fr.xml"

OLD_TEMPLATE = "aim:er"
NEW_TEMPLATE = "squatt:er"

# The 4 remaining "aim:er" donors whose rawOrthosyllCV is "...X_e_r"
# (doubled-consonant anglicism, neither the regular "...X_er" shape nor the
# "étudi:er" vowel-final/hiatus shape), confirmed via FirstTheory.pickle
# this session.
ANGLICISM_LEMMAS = ("reprogrammer", "squatter", "bitter", "stripper")


def extractTemplateBlock(content: str, templateName: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(templateName) + r'">.*?</template>\n?',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={templateName!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildNewTemplateBlock(content: str) -> str:
    oldBlock, _, _ = extractTemplateBlock(content, OLD_TEMPLATE)
    newBlock = oldBlock.replace(
        f'<template name="{OLD_TEMPLATE}">',
        f'<template name="{NEW_TEMPLATE}">', 1)
    if newBlock == oldBlock:
        raise ValueError("template name substitution had no effect")
    return newBlock


def alreadyApplied(conjugationsContent: str, verbsContent: str) -> bool:
    hasTemplate = f'<template name="{NEW_TEMPLATE}">' in conjugationsContent
    repointedCount = sum(
        f'<t>{NEW_TEMPLATE}</t>' in line
        for line in verbsContent.splitlines()
        if any(f'<i>{lemme}</i>' in line for lemme in ANGLICISM_LEMMAS)
    )
    return hasTemplate and repointedCount == len(ANGLICISM_LEMMAS)


def findVerbLines(verbsContent: str) -> dict[str, str]:
    linesByLemme: dict[str, str] = {}
    for lemme in ANGLICISM_LEMMAS:
        pattern = re.compile(
            r'<v><i>' + re.escape(lemme) + r'</i><t>' + re.escape(OLD_TEMPLATE)
            + r'</t><en>[^<]*</en></v>')
        matches = pattern.findall(verbsContent)
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {OLD_TEMPLATE!r} entry for "
                              f"{lemme!r}, found {len(matches)}")
        linesByLemme[lemme] = matches[0]
    return linesByLemme


def printSample(newTemplateBlock: str, verbLines: dict[str, str]) -> None:
    print("=== New template block (dry-run, no files modified) ===\n")
    print(newTemplateBlock)
    print(f"=== {len(verbLines)} verb entries to repoint "
          f"{OLD_TEMPLATE!r} -> {NEW_TEMPLATE!r} ===\n")
    for lemme, line in sorted(verbLines.items()):
        print(f"  {line} -> "
              f"{line.replace(f'<t>{OLD_TEMPLATE}</t>', f'<t>{NEW_TEMPLATE}</t>')}")


def applyConjugationsCorrection(path: str, newTemplateBlock: str) -> None:
    with open(path, encoding="utf-8") as f:
        content = f.read()
    _, _, insertAt = extractTemplateBlock(content, OLD_TEMPLATE)
    newContent = content[:insertAt] + "\n" + newTemplateBlock + content[insertAt:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(newContent)


def applyVerbsCorrection(path: str, verbLines: dict[str, str]) -> int:
    with open(path, encoding="utf-8") as f:
        content = f.read()
    modified = 0
    for lemme, oldLine in verbLines.items():
        newLine = oldLine.replace(f'<t>{OLD_TEMPLATE}</t>', f'<t>{NEW_TEMPLATE}</t>')
        if oldLine not in content:
            continue
        content = content.replace(oldLine, newLine, 1)
        modified += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split the 4 doubled-consonant anglicism donors out of "
        "Verbiste's 'aim:er' template into a new 'squatt:er' template with "
        "byte-identical endings, to fix deriveConjugationEndingTables's "
        "suffix collapse for the remaining ~3600 'aim:er' donors (see "
        "PROGRESS.md)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the new template to resources/verbiste/conjugations-fr.xml "
        "and repoint the 4 lemmas in resources/verbiste/verbs-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        conjugationsContent = f.read()
    with open(VERBS_PATH, encoding="utf-8") as f:
        verbsContent = f.read()

    if alreadyApplied(conjugationsContent, verbsContent):
        print("Already applied: 'squatt:er' template exists and all "
              f"{len(ANGLICISM_LEMMAS)} lemmas are repointed. Nothing to do.")
        return

    newTemplateBlock = buildNewTemplateBlock(conjugationsContent)
    verbLines = findVerbLines(verbsContent)

    printSample(newTemplateBlock, verbLines)

    print("=== Summary ===")
    print(f"Lemmas to repoint: {len(verbLines)} (expected {len(ANGLICISM_LEMMAS)})")
    if len(verbLines) != len(ANGLICISM_LEMMAS):
        missing = set(ANGLICISM_LEMMAS) - set(verbLines)
        print(f"WARNING: missing lemmas: {sorted(missing)}", file=sys.stderr)

    if args.apply:
        applyConjugationsCorrection(CONJUGATIONS_PATH, newTemplateBlock)
        nbVerbs = applyVerbsCorrection(VERBS_PATH, verbLines)
        print(f"\n--apply: inserted 'squatt:er' template into {CONJUGATIONS_PATH}")
        print(f"--apply: repointed {nbVerbs} verb entries in {VERBS_PATH}")
        if nbVerbs != len(verbLines):
            print(f"WARNING: expected {len(verbLines)} verb entries repointed, "
                  f"only repointed {nbVerbs}", file=sys.stderr)


if __name__ == "__main__":
    main()
