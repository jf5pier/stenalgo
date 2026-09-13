#!/bin/env python
#
# Investigates and (with --apply) splits a syllabification-only distinction
# out of Verbiste's "aim:er" conjugation template, into a new sibling
# template "étudi:er".
#
# Background (see PROGRESS.md's ACTIVE INVESTIGATION): src/verbparadigm.py's
# deriveConjugationEndingTables derives a per-template phonemic/syllable
# radical-stripping suffix by taking the longest common suffix of every
# donor infinitive's rawOrthosyllCV. For "aim:er" this collapses to a
# useless 1-character result, because the ~3600 consonant-final donors
# (aimer -> "...m_er") and ~48 vowel-final/hiatus donors (crier -> "...i|er",
# oublier -> "...ou|er") use two different syllable-separator conventions
# ("_" vs "|") right where the suffix is measured, even though both groups
# conjugate with byte-identical orthographic endings (Verbiste's own reason
# for keeping them in one template).
#
# Verbiste already has a precedent for a template that exists purely to
# separate a donor pool with otherwise-identical endings: "référenci:er"
# (conjugations-fr.xml) duplicates "aim:er" almost verbatim for the sole
# verb "référencier". This script does the same thing at slightly larger
# scale: duplicates "aim:er" as "étudi:er" (named after "étudier", the verb
# Bescherelle lists as its own numbered model for exactly this radical
# shape -- see conversation with the user) and repoints the 48 vowel-final
# donors from "aim:er" to it. Since the two templates' orthographic endings
# are byte-identical, generateOrthoForm's output is unaffected; only
# src/verbparadigm.py's per-template donor grouping (infinitivesByTemplate)
# changes, which is exactly what's needed to un-collapse the suffix
# derivation.
#
# Scope: explicitly does NOT touch 4 further "aim:er" donors that also fail
# to end in "_er" -- "reprogrammer", "squatter", "bitter", "stripper". Those
# are anglicism borrowings with a doubled final consonant syllabified as
# "...X_e_r" (a third, distinct shape, not a vowel-final radical); lumping
# them into "étudi:er" would be wrong, and they're rare/low-frequency enough
# that they don't block the suffix derivation for either template on their
# own. They're left as an "aim:er" donor for now (unresolved, separate
# issue).
#
# Dry-run by default: only reads and reports. --apply inserts the new
# "étudi:er" template into resources/verbiste/conjugations-fr.xml (right
# after "aim:er"'s own template block) and rewrites the <t> tag of each of
# the 48 target lemmas in resources/verbiste/verbs-fr.xml, in place.
# Idempotent: a no-op (0 rows modified) if run again after a successful
# --apply.
import argparse
import re
import sys

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
VERBS_PATH = "resources/verbiste/verbs-fr.xml"

OLD_TEMPLATE = "aim:er"
NEW_TEMPLATE = "étudi:er"

# The 48 "aim:er" donors whose rawOrthosyllCV is vowel-final/hiatus
# (doesn't end in "_er"), confirmed via FirstTheory.pickle this session --
# excludes the 4 anglicism outliers (see module docstring).
VOWEL_FINAL_LEMMAS = (
    "affluer", "agréer", "approprier", "clouer", "crier", "créer",
    "déclouer", "décrier", "démultiplier", "déplier", "enclouer", "engluer",
    "entretuer", "expatrier", "exproprier", "flouer", "gréer", "influer",
    "maugréer", "multiplier", "obstruer", "oublier", "plier", "prier",
    "procréer", "publier", "rabrouer", "rapatrier", "reclouer", "recréer",
    "refluer", "regréer", "relouer", "renflouer", "replier", "récrier",
    "récréer", "strier", "supplier", "suppléer", "toréer", "trier",
    "trouer", "ébrouer", "écrier", "écrouer", "énucléer", "évertuer",
)


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
        if any(f'<i>{lemme}</i>' in line for lemme in VOWEL_FINAL_LEMMAS)
    )
    return hasTemplate and repointedCount == len(VOWEL_FINAL_LEMMAS)


def findVerbLines(verbsContent: str) -> dict[str, str]:
    linesByLemme: dict[str, str] = {}
    for lemme in VOWEL_FINAL_LEMMAS:
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
        description="Split the 48 vowel-final/hiatus-radical donors out of "
        "Verbiste's 'aim:er' template into a new 'étudi:er' template with "
        "byte-identical endings, to fix deriveConjugationEndingTables's "
        "suffix collapse (see PROGRESS.md)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the new template to resources/verbiste/conjugations-fr.xml "
        "and repoint the 48 lemmas in resources/verbiste/verbs-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        conjugationsContent = f.read()
    with open(VERBS_PATH, encoding="utf-8") as f:
        verbsContent = f.read()

    if alreadyApplied(conjugationsContent, verbsContent):
        print("Already applied: 'étudi:er' template exists and all "
              f"{len(VOWEL_FINAL_LEMMAS)} lemmas are repointed. Nothing to do.")
        return

    newTemplateBlock = buildNewTemplateBlock(conjugationsContent)
    verbLines = findVerbLines(verbsContent)

    printSample(newTemplateBlock, verbLines)

    print("=== Summary ===")
    print(f"Lemmas to repoint: {len(verbLines)} (expected {len(VOWEL_FINAL_LEMMAS)})")
    if len(verbLines) != len(VOWEL_FINAL_LEMMAS):
        missing = set(VOWEL_FINAL_LEMMAS) - set(verbLines)
        print(f"WARNING: missing lemmas: {sorted(missing)}", file=sys.stderr)

    if args.apply:
        applyConjugationsCorrection(CONJUGATIONS_PATH, newTemplateBlock)
        nbVerbs = applyVerbsCorrection(VERBS_PATH, verbLines)
        print(f"\n--apply: inserted 'étudi:er' template into {CONJUGATIONS_PATH}")
        print(f"--apply: repointed {nbVerbs} verb entries in {VERBS_PATH}")
        if nbVerbs != len(verbLines):
            print(f"WARNING: expected {len(verbLines)} verb entries repointed, "
                  f"only repointed {nbVerbs}", file=sys.stderr)


if __name__ == "__main__":
    main()
