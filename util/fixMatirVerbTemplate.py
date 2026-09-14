#!/bin/env python
#
# Batch 9 (residual UNDEFINED_SLOT/WRONG_ENDING) of the lexicon-defect
# triage plan: resources/verbiste/verbs-fr.xml itself mis-assigns "matir"
# ("to matte/dull a metal surface") to the "men:tir" template (the
# irregular short-form -ir conjugation used by mentir/sentir/partir --
# "je mats, tu mats, il mat"), when "matir" is actually a plain regular
# -ir/-iss- verb like its own sibling "amatir" (correctly assigned "fin:ir"
# a few lines above it in verbs-fr.xml). Confirmed against
# resources/LexiqueMixte.tsv's own attested row: "matisse" (subjonctif
# présent 1s/3s) is the fin:ir-pattern form (radical "mat" + "-isse", like
# "finisse") -- the men:tir template can't produce "matisse" at all (its own
# subjonctif présent radical+ending would be "mate"), which is exactly what
# util/validateLexiconAgainstVerbiste.py flags as WRONG_ENDING.
#
# This corrects Verbiste's own source data directly (verbs-fr.xml), the
# same kind of upstream correction already applied to conjugations-fr.xml
# for l:éguer/diss:équer/harc:eler/dép:ecer/préd:ire/l:éser --
# verbModelExceptions.tsv is NOT the right place for this: that table is
# scoped to lemmas ABSENT from Verbiste's own verbs-fr.xml mapping (see its
# own docstring), while "matir" IS present there, just mis-mapped;
# src/verbparadigm.py's getTrustedTemplate always trusts a Verbiste-present
# mapping over an exceptions-file entry, so an exceptions-file entry alone
# would have no effect here.
#
# Dry-run by default: only reads and reports. --apply rewrites the one
# affected <v> line in resources/verbiste/verbs-fr.xml, in place.
# Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse

VERBS_PATH = "resources/verbiste/verbs-fr.xml"

OLD_LINE = "<v><i>matir</i><t>men:tir</t><en>matir</en></v>"
NEW_LINE = "<v><i>matir</i><t>fin:ir</t><en>matir</en></v>"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix Verbiste's own mis-assignment of 'matir' to the "
        "men:tir template (should be fin:ir, like its sibling 'amatir')."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the correction to resources/verbiste/verbs-fr.xml (default: dry-run).",
    )
    args = parser.parse_args()

    with open(VERBS_PATH, encoding="utf-8") as f:
        content = f.read()

    count = content.count(OLD_LINE)
    print(f"Occurrences of {OLD_LINE!r}: {count}")
    if count == 1:
        print(f"  -> {NEW_LINE!r}")
    elif count == 0:
        print("Already applied (or line not found as expected).")
        return
    else:
        print(f"WARNING: expected exactly 1 occurrence, found {count}; not applying.")
        return

    if args.apply:
        newContent = content.replace(OLD_LINE, NEW_LINE, 1)
        with open(VERBS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"\n--apply: wrote correction to {VERBS_PATH}")


if __name__ == "__main__":
    main()
