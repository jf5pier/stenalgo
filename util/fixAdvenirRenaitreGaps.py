#!/bin/env python
#
# Batch 9 (UNDEFINED_SLOT clusters B & C) of the lexicon-defect triage plan:
# two independent, mechanically-confirmed template completions in
# resources/verbiste/conjugations-fr.xml.
#
#   - adv:enir: the template defines ONLY the 3rd-person-singular slot for
#     every tense (correct for most weather-verb-style impersonal templates,
#     but "advenir" genuinely takes plural subjects in standard French,
#     e.g. "de tels faits adviennent rarement" -- it is not strictly
#     impersonal like "neiger"). resources/LexiqueMixte.tsv attests
#     "adviennent" (ind:pre:3p), which the template can't currently produce.
#     The ending "iennent" is confirmed by direct analogy to "venir"'s own
#     3p présent ("viennent") -- adv:enir shares venir's "-enir" radical
#     pattern (3s "ient", matching venir's "vient"). Adding only this one
#     confirmed slot (ind:pre:3p), not speculatively extending every other
#     tense's 3p, since only this slot has an attested lexicon row to verify
#     against.
#   - ren:aître: the participe-passé section is entirely empty (no <i> at
#     all for any of the 4 gender/number slots). resources/LexiqueMixte.tsv
#     attests "rené" (m/s) and "renée" (f/s), the standard past participle
#     of "renaître" (direct analogy to naître -> né/née). Radical "ren" +
#     "é"/"és"/"ée"/"ées" matches both attested rows exactly; "renés"/
#     "renées" (m/p, f/p) are added by the same regular pattern even though
#     not yet attested in the lexicon, since a participe-passé's 4 forms are
#     always regular derivatives of each other once one is confirmed.
#
# Dry-run by default: only reads and reports. --apply rewrites the affected
# <p> elements in resources/verbiste/conjugations-fr.xml, in place.
# Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"

ADVENIR_OLD_PRESENT = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>ient</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</présent>"
)
ADVENIR_NEW_PRESENT = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>ient</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>iennent</i></p>\n"
    "\t\t</présent>"
)

RENAITRE_OLD_PARTICIPE_PASSE = (
    "<participe-passé>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</participe-passé>"
)
RENAITRE_NEW_PARTICIPE_PASSE = (
    "<participe-passé>\n"
    "\t\t\t<p><i>é</i></p>\n"
    "\t\t\t<p><i>és</i></p>\n"
    "\t\t\t<p><i>ée</i></p>\n"
    "\t\t\t<p><i>ées</i></p>\n"
    "\t\t</participe-passé>"
)

TEMPLATES: dict[str, list[tuple[str, str, int]]] = {
    "adv:enir": [(ADVENIR_OLD_PRESENT, ADVENIR_NEW_PRESENT, 1)],
    "ren:aître": [(RENAITRE_OLD_PARTICIPE_PASSE, RENAITRE_NEW_PARTICIPE_PASSE, 1)],
}


def extractTemplateBlock(content: str, templateName: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(templateName) + r'">.*?</template>',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={templateName!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildCorrectedBlock(block: str, corrections: list[tuple[str, str, int]]
                         ) -> tuple[str, int, list[str]]:
    corrected = block
    applied = 0
    warnings: list[str] = []
    for old, new, expectedCount in corrections:
        count = corrected.count(old)
        if count == 0:
            warnings.append(f"expected {expectedCount} occurrence(s), found 0 -- check exact whitespace")
            continue
        if count != expectedCount:
            warnings.append(f"expected {expectedCount} occurrence(s), found {count}")
        corrected = corrected.replace(old, new)
        applied += count
    return corrected, applied, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix adv:enir's missing ind:pre:3p slot and ren:aître's "
        "entirely-missing participe-passé."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    totalApplied = 0
    for templateName, corrections in TEMPLATES.items():
        block, start, end = extractTemplateBlock(content, templateName)
        correctedBlock, applied, warnings = buildCorrectedBlock(block, corrections)

        print(f"=== {templateName} ===")
        for old, new, expectedCount in corrections:
            if old in block:
                print(f"  {old!r} ->\n  {new!r}")
        print(f"Sections corrected: {applied}")
        for w in warnings:
            print(f"  WARNING: {w}")
        print()

        if args.apply and applied:
            content = content[:start] + correctedBlock + content[end:]
            totalApplied += applied

    if args.apply:
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"--apply: wrote {totalApplied} section correction(s) to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
