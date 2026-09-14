#!/bin/env python
#
# Batch 9 (UNDEFINED_SLOT cluster F) of the lexicon-defect triage plan: fills
# in "fou:tre"'s entirely-empty passé-simple and subjonctif:imparfait
# tenses (Verbiste marks foutre as defective there, likely reflecting a
# prescriptive view that a vulgar/colloquial verb "shouldn't" appear in
# literary-register tenses).
#
# resources/LexiqueMixte.tsv attests exactly 2 forms in these tenses:
# "foutit" (ind:pas:3s) and "foutît" (sub:imp:3s), each with a small but
# nonzero book-frequency -- plausible as a known French rhetorical device
# (a crude verb deliberately inflected in an elevated literary register for
# comic effect), not corpus noise.
#
# The endings for the other 10 (unattested) persons in these 2 tenses are
# derived mechanically, not guessed: fou:tre's own OTHER already-defined
# tenses (imparfait "tais/tais/tait/tions/tiez/taient", futur-simple
# "trai/tras/tra/trons/trez/tront") consistently prefix every person's
# ending with "t" (since the radical is the bare "fou"). Applying that same
# "t"-prefix to the standard regular -re-verb passé-simple/subjonctif-
# imparfait suffix set ("is/is/it/îmes/îtes/irent" and
# "isse/isses/ît/issions/issiez/issent") gives "tis/tis/tit/tîmes/tîtes/
# tirent" and "tisse/tisses/tît/tissions/tissiez/tissent" -- and the two
# attested forms ("tit" -> foutit, "tît" -> foutît) match this derivation
# exactly, confirming it rather than assuming it.
#
# Dry-run by default: only reads and reports. --apply rewrites the two
# affected tense blocks in resources/verbiste/conjugations-fr.xml, in
# place. Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
TEMPLATE_NAME = "fou:tre"

PASSE_SIMPLE_OLD = (
    "<passé-simple>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</passé-simple>"
)
PASSE_SIMPLE_NEW = (
    "<passé-simple>\n"
    "\t\t\t<p><i>tis</i></p>\n"
    "\t\t\t<p><i>tis</i></p>\n"
    "\t\t\t<p><i>tit</i></p>\n"
    "\t\t\t<p><i>tîmes</i></p>\n"
    "\t\t\t<p><i>tîtes</i></p>\n"
    "\t\t\t<p><i>tirent</i></p>\n"
    "\t\t</passé-simple>"
)

SUBJONCTIF_IMPARFAIT_OLD = (
    "<imparfait>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</imparfait>"
)
SUBJONCTIF_IMPARFAIT_NEW = (
    "<imparfait>\n"
    "\t\t\t<p><i>tisse</i></p>\n"
    "\t\t\t<p><i>tisses</i></p>\n"
    "\t\t\t<p><i>tît</i></p>\n"
    "\t\t\t<p><i>tissions</i></p>\n"
    "\t\t\t<p><i>tissiez</i></p>\n"
    "\t\t\t<p><i>tissent</i></p>\n"
    "\t\t</imparfait>"
)

CORRECTIONS = [
    (PASSE_SIMPLE_OLD, PASSE_SIMPLE_NEW),
    (SUBJONCTIF_IMPARFAIT_OLD, SUBJONCTIF_IMPARFAIT_NEW),
]


def extractTemplateBlock(content: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(TEMPLATE_NAME) + r'">.*?</template>',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={TEMPLATE_NAME!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill in fou:tre's empty passé-simple and "
        "subjonctif:imparfait tenses using the template's own internally-"
        "consistent 't'-prefix ending pattern."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    block, start, end = extractTemplateBlock(content)
    corrected = block
    applied = 0
    warnings: list[str] = []
    for old, new in CORRECTIONS:
        count = corrected.count(old)
        if count != 1:
            warnings.append(f"expected 1 occurrence, found {count}: {old!r}")
            continue
        print(f"  {old!r} ->\n  {new!r}\n")
        corrected = corrected.replace(old, new, 1)
        applied += 1

    print(f"Sections corrected: {applied} (expected {len(CORRECTIONS)})")
    for w in warnings:
        print(f"  WARNING: {w}")

    if args.apply and applied:
        newContent = content[:start] + corrected + content[end:]
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"\n--apply: wrote {applied} correction(s) to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
