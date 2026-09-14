#!/bin/env python
#
# Fixes the last remaining WRONG_ENDING flag: "o:uïr"'s conditionnel:présent
# lists 3 archaic alternative spellings per slot (e.g. 1s "irais"/"uïrais"/
# "rrais", i.e. "oirais"/"ouïrais"/"orrais" once combined with the radical
# "o") but generation only ever reads the FIRST <i> child, currently
# "irais" ("oirais"). The lexicon's one attested conditionnel row,
# "ouïrais" (cnd:pre:1s), matches the SECOND alternative ("uïrais") instead.
# Reordering so "uïrais"-style forms are primary across all 6 persons of
# this tense (the same "uï" alternation choice presumably applies uniformly
# across the person paradigm, matching how the l:éguer/harc:eler/dép:ecer
# fixes earlier this session applied their own confirmed choice across a
# whole tense rather than just the one attested slot) fixes the flag without
# touching futur-simple (unattested in the lexicon, left alone).
#
# Dry-run by default: only reads and reports. --apply rewrites the
# conditionnel:présent block in resources/verbiste/conjugations-fr.xml, in
# place. Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
TEMPLATE_NAME = "o:uïr"

OLD_BLOCK = (
    "<Conditionnel>\n"
    "\t\t<présent>\n"
    "\t\t\t<p><i>irais</i><i>uïrais</i><i>rrais</i></p>\n"
    "\t\t\t<p><i>irais</i><i>uïrais</i><i>rrais</i></p>\n"
    "\t\t\t<p><i>irait</i><i>uïrait</i><i>rrait</i></p>\n"
    "\t\t\t<p><i>irions</i><i>uïrions</i><i>rrions</i></p>\n"
    "\t\t\t<p><i>iriez</i><i>uïriez</i><i>rriez</i></p>\n"
    "\t\t\t<p><i>iraient</i><i>uïraient</i><i>rraient</i></p>\n"
    "\t\t</présent>\n"
    "\t</Conditionnel>"
)
NEW_BLOCK = (
    "<Conditionnel>\n"
    "\t\t<présent>\n"
    "\t\t\t<p><i>uïrais</i><i>irais</i><i>rrais</i></p>\n"
    "\t\t\t<p><i>uïrais</i><i>irais</i><i>rrais</i></p>\n"
    "\t\t\t<p><i>uïrait</i><i>irait</i><i>rrait</i></p>\n"
    "\t\t\t<p><i>uïrions</i><i>irions</i><i>rrions</i></p>\n"
    "\t\t\t<p><i>uïriez</i><i>iriez</i><i>rriez</i></p>\n"
    "\t\t\t<p><i>uïraient</i><i>iraient</i><i>rraient</i></p>\n"
    "\t\t</présent>\n"
    "\t</Conditionnel>"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reorder o:uïr's conditionnel:présent alternatives so "
        "the attested 'uï'-form is primary."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the correction to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'<template name="' + re.escape(TEMPLATE_NAME) + r'">.*?</template>', re.DOTALL)
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        print(f"WARNING: expected exactly one <template name={TEMPLATE_NAME!r}> block, "
              f"found {len(matches)}")
        return
    block = matches[0].group(0)

    count = block.count(OLD_BLOCK)
    print(f"Occurrences of the old Conditionnel block: {count}")
    if count != 1:
        print("Not applying: expected exactly 1 occurrence.")
        return
    print(f"{OLD_BLOCK!r} ->\n{NEW_BLOCK!r}")

    if args.apply:
        newContent = content[:matches[0].start()] + block.replace(OLD_BLOCK, NEW_BLOCK, 1) + content[matches[0].end():]
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"\n--apply: wrote correction to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
