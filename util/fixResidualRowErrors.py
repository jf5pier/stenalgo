#!/bin/env python
#
# Batch 9/10 (residual row-level errors) of the lexicon-defect triage plan:
# four independent, individually-verified one-off row fixes, each confirmed
# against the rest of the lexicon before fixing (not guessed). All four
# exist in both resources/Lexique383.tsv and resources/LexiqueMixte.tsv, so
# both are corrected.
#
#   - "lamer"/"lamer" (VER): tagged "imp:pre:2p;" only, but ortho == lemme,
#     which can only be the infinitive -- "imp:pre:2p" of "lamer" is
#     actually "lamez" (a different spelling), so the tag is simply wrong.
#     Fix: infover -> "inf;".
#   - "allier"/"aller" (VER, ind:pre:2p): pure row-level corruption --
#     "allier" is a completely different, unrelated verb ("to ally") that
#     already has its own correct "allier"/"allier"/inf row elsewhere, and
#     "aller"'s real ind:pre:2p ("allez") already exists as its own correct
#     row too. This row doesn't describe any real word/slot; it's deleted
#     entirely rather than re-tagged.
#   - "versions"/"verser" (VER, tagged ind:imp:1s): wrong tag -- "verser"'s
#     real ind:imp:1s ("je versais") already exists as its own correct row
#     ("versais", tagged ind:imp:1s;ind:imp:2s;). "versions" is actually
#     "nous versions" (ind:imp:1p), which isn't attested anywhere else in
#     the lexicon. Fix: infover -> "ind:imp:1p;".
#   - "bouille"/"bouillir" (VER, tagged imp:pre:2s;ind:pre:3s): wrong tags --
#     "bouillir"'s real imp:pre:2s/ind:pre:3s ("bous"/"bout") already exist
#     as their own correct rows. "bouille" is actually the subjonctif
#     présent 1s/3s ("que je bouille"/"qu'il bouille", matching
#     bou:illir's own template ending "ille"), which isn't attested
#     anywhere else. Fix: infover -> "sub:pre:1s;sub:pre:3s;".
#
# Dry-run by default: only reads and reports. --apply writes the
# corrections (and the one deletion) in place. Idempotent: a no-op (0 rows
# changed) if run again after a successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

# (ortho, lemme, cgram, oldInfoVerb) -> newInfoVerb, or None to delete the row.
ROW_FIXES: dict[tuple[str, str, str, str], str | None] = {
    ("lamer", "lamer", "VER", "imp:pre:2p;"): "inf;",
    ("allier", "aller", "VER", "ind:pre:2p;"): None,
    ("versions", "verser", "VER", "ind:imp:1s;"): "ind:imp:1p;",
    ("bouille", "bouillir", "VER", "imp:pre:2s;ind:pre:3s;"): "sub:pre:1s;sub:pre:3s;",
}


def findAndFix(path: str, apply: bool) -> tuple[list[str], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    corrections: list[str] = []
    outputLines = [lines[0]]
    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            outputLines.append(lines[i])
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx], fields[cgramIdx], fields[infoverIdx])
        if key not in ROW_FIXES:
            outputLines.append(lines[i])
            continue
        newInfoVerb = ROW_FIXES[key]
        if newInfoVerb is None:
            corrections.append(f"ortho={key[0]!r} lemme={key[1]!r}: DELETE row "
                                f"(infover={key[3]!r})")
            modified += 1
            if not apply:
                outputLines.append(lines[i])
            # if apply: row is simply omitted from outputLines
            continue
        corrections.append(f"ortho={key[0]!r} lemme={key[1]!r}: {key[3]!r} -> {newInfoVerb!r}")
        modified += 1
        if apply:
            fields[infoverIdx] = newInfoVerb
            outputLines.append("\t".join(fields) + ending)
        else:
            outputLines.append(lines[i])

    if apply and modified:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(outputLines)

    return corrections, modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix 4 independent residual row-level errors: lamer's "
        "wrong tag, the spurious allier/aller row (deleted), versions's "
        "wrong tag, and bouille's wrong tags."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        corrections, modified = findAndFix(path, args.apply)
        print(f"=== {path} ===")
        for c in corrections:
            print(f"  {c}")
        print(f"Total rows found: {modified} (expected {len(ROW_FIXES)})")
        if args.apply:
            print(f"--apply: updated {path}")
        print()


if __name__ == "__main__":
    main()
