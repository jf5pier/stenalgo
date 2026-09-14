#!/bin/env python
#
# Follow-up to util/fixGniezPronunciation.py (commit 83d9a32): that script
# corrected Lexique383.tsv's phon column (adding the yod dropped from
# "-iez", e.g. accompagniez ak\xa7paNe -> ak\xa7paNje) and
# LexiqueInfraCorrespondance.tsv's assoc column, but never updated
# LexiqueInfraCorrespondance.tsv's own separate "phono" column, leaving it
# at the old, un-corrected value. Since Lexique.breakdownSyllables()
# requires word.phonology == asso_word["phono"] to attach a syllable
# breakdown, this stale phono value silently orphans these 17 "-gniez" rows
# from syllable breakdown (no crash, just missing data), the same class of
# defect as the bruinasse/eusse orphans fixed earlier.
#
# Dry-run by default: only reads and reports. --apply corrects the phono
# field in place. Idempotent: a no-op if run again after a successful
# --apply (the OLD_TO_NEW mapping's old values will no longer be present).
import argparse

LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"

# (ortho, old phono, new phono) for the 17 lemmas fixed in Lexique383.tsv by
# util/fixGniezPronunciation.py.
OLD_TO_NEW: dict[tuple[str, str], str] = {
    ("accompagniez", "ak§paNe"): "ak§paNje",
    ("craigniez", "kRENe"): "kRENje",
    ("enseigniez", "@sENe"): "@sENje",
    ("feigniez", "fENe"): "fENje",
    ("gagniez", "gaNe"): "gaNje",
    ("joigniez", "ZwaNe"): "ZwaNje",
    ("peigniez", "pENe"): "pENje",
    ("plaigniez", "plENe"): "plENje",
    ("regagniez", "R°gaNe"): "R°gaNje",
    ("rejoigniez", "R°ZwaNe"): "R°ZwaNje",
    ("répugniez", "RepyNe"): "RepyNje",
    ("saigniez", "sENe"): "sENje",
    ("signiez", "siNe"): "siNje",
    ("soigniez", "swaNe"): "swaNje",
    ("souligniez", "suliNe"): "suliNje",
    ("témoigniez", "temwaNe"): "temwaNje",
    ("épargniez", "epaRNe"): "epaRNje",
}


def findAndFix(path: str, apply: bool) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    phonoIdx = header.index("phono")
    cgramIdx = header.index("cgram")

    found: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        if fields[cgramIdx] != "VER":
            continue
        key = (fields[itemIdx], fields[phonoIdx])
        if key in OLD_TO_NEW:
            newPhono = OLD_TO_NEW[key]
            found.append(f"item={key[0]!r} phono {key[1]!r} -> {newPhono!r}")
            if apply:
                fields[phonoIdx] = newPhono
                lines[i] = "\t".join(fields) + "\n"

    if apply and found:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Correct the stale phono field for the 17 '-gniez' VER "
        "rows in LexiqueInfraCorrespondance.tsv left un-updated by "
        "util/fixGniezPronunciation.py."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to LexiqueInfraCorrespondance.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    found = findAndFix(LEXIQUE_INFRA_PATH, args.apply)
    print(f"=== {LEXIQUE_INFRA_PATH} ===")
    for f in found:
        print(f"  FIX: {f}")
    print(f"Total rows found: {len(found)} (expected {len(OLD_TO_NEW)})")
    if args.apply:
        print(f"--apply: updated {LEXIQUE_INFRA_PATH}")


if __name__ == "__main__":
    main()
