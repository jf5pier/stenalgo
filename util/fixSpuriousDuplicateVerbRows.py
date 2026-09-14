#!/bin/env python
#
# Batch 10 (SUSPECTED_WRONG_LEMME + a systematic lexicon-wide sweep for the
# same pattern) of the lexicon-defect triage plan: deletes spurious
# duplicate VER/AUX rows, each following the exact same pattern -- an
# `ortho` value that already has its own correct row elsewhere also appears
# a SECOND time under a wrong `lemme` and a tag that does NOT correctly
# describe that ortho.
#
# Sub-pattern (a): ortho duplicated under a completely unrelated REAL verb
# (confirmed via util.validateLexiconAgainstVerbiste's SUSPECTED_WRONG_LEMME
# flags):
#   contrôler (already inf; of contrôler) also spuriously tagged as
#     "chuter"'s ind:pre:2p
#   emmener (already inf; of emmener) also spuriously tagged as
#     "expliquer"'s ind:pre:2p
#   passer (already inf; of passer) also spuriously tagged as
#     "prendre"'s imp:pre:2p
#   pincer (already inf; of pincer) also spuriously tagged as
#     "pouvoir"'s ind:pre:2p
#   présenter (already inf; of présenter) also spuriously tagged as
#     "poster"'s ind:pre:2p
#   regretter (already inf; of regretter) also spuriously tagged as
#     "rester"'s imp:pre:2p
#   soigner (already inf;; of soigner) also spuriously tagged as
#     "saler"'s ind:pre:2p
#   restent (already ind:pre:3p of rester) also spuriously tagged as
#     "ruer"'s sub:pre:3p
#   eussé (a typo'd duplicate of the already-correct "eusse", both AUX and
#     VER cgram variants, sub:imp:1s of avoir) -- 2 rows.
#
# Sub-pattern (b): ortho duplicated under a bogus, self-referential or
# fabricated "lemme" that does not resolve to any real Verbiste template at
# all (found via a lexicon-wide sweep: every VER-cgram ortho with 2+ distinct
# lemme values, cross-referenced against getTrustedTemplate to find which
# occurrence's lemme is unresolvable while the OTHER occurrence's lemme *is*
# a real, resolvable verb correctly describing that ortho):
#   connais (already correctly imp:pre:2s;ind:pre:1s;ind:pre:2s; of
#     "connaître") also spuriously self-tagged lemme="connais" inf; --
#     "connais" is not itself an infinitive spelling of anything.
#   mentez (already correctly imp:pre:2p;ind:pre:2p; of "mentir") also
#     spuriously self-tagged lemme="mentez" inf;.
#   parait (already correctly ind:imp:3s; of "parer") also spuriously
#     self-tagged lemme="parait" inf;.
#   plus (already correctly ind:pas:1s;ind:pas:2s; of "plaire") also
#     spuriously self-tagged lemme="plus" par:pas; (m/p) -- "plus" is not a
#     verb lemma with its own participle.
#   réélus (already correctly par:pas; m/p of "réélire") also spuriously
#     self-tagged lemme="réélus" par:pas; m/p.
#   sais (already correctly ind:pre:1s;ind:pre:2s; of "savoir") also
#     spuriously self-tagged lemme="sais" imp:pre:2s; -- savoir's real
#     imperative 2s is the irregular "sache", not "sais".
#   voulez (already correctly ind:pre:2p; of "vouloir") also spuriously
#     tagged lemme="vouler" inf; -- "vouler" is not a real verb (truncated/
#     corrupted form of "vouloir").
#   bouffis (already correctly par:pas; m/p of "bouffir") also spuriously
#     tagged lemme="bouffi" par:pas; m/p -- "bouffi" is the adjective
#     spelling, not a verb lemma.
#   débraillés (already correctly par:pas; m/p of "débrailler") also
#     spuriously tagged lemme="débraillé" par:pas; m/p -- same
#     adjective-spelling-as-fake-lemme pattern as bouffis.
#
# Every one of these patterns (19 rows total: 10 from sub-pattern (a), 9
# from sub-pattern (b)) is confirmed present in both resources/Lexique383.tsv
# and resources/LexiqueMixte.tsv, so both files are corrected. Given the
# consistent shape across all of them (always the SAME word wrongly
# duplicated a second time with a tag that plainly doesn't describe it, while
# a correct row already exists elsewhere), this is a systematic upstream
# data artifact rather than 19 independent judgment calls -- most likely a
# handful of list-alignment/derivation bugs from whatever process originally
# built these rows in Lexique383.tsv.
#
# NOT included here (deliberately left alone, see PROGRESS.md/todo.md):
#   - "puis"/"pouvoir" (ind:pre:1s): NOT a duplicate/error -- "puis" is the
#     genuine classical/formal-register alternate of "je peux" (which
#     already exists correctly, tagged ind:pre:1s;ind:pre:2s;), a real,
#     phonologically distinct (/pɥi/ vs /pø/), coexisting form -- same
#     "dual valid conjugation" class as pa:yer/ass:eoir, not a lexicon
#     error.
#   - "croître"/"crue","crues" and "mouvoir"/"mû": circumflex-accent
#     questions needing linguistic verification, same class as the deferred
#     accroître/recroître cases -- not this batch's scope.
#
# Dry-run by default: only reads and reports. --apply deletes the matching
# rows in place. Idempotent: a no-op (0 rows found) if run again after a
# successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

# (ortho, lemme, cgram, infoVerb) rows to delete entirely.
ROWS_TO_DELETE: set[tuple[str, str, str, str]] = {
    # Sub-pattern (a): duplicated under an unrelated real verb.
    ("contrôler", "chuter", "VER", "ind:pre:2p;"),
    ("emmener", "expliquer", "VER", "ind:pre:2p;"),
    ("passer", "prendre", "VER", "imp:pre:2p;"),
    ("pincer", "pouvoir", "VER", "ind:pre:2p;"),
    ("présenter", "poster", "VER", "ind:pre:2p;"),
    ("regretter", "rester", "VER", "imp:pre:2p;"),
    ("soigner", "saler", "VER", "ind:pre:2p;"),
    ("restent", "ruer", "VER", "sub:pre:3p;"),
    ("eussé", "avoir", "AUX", "sub:imp:1s;"),
    ("eussé", "avoir", "VER", "sub:imp:1s;"),
    # Sub-pattern (b): duplicated under a bogus/unresolvable self-referential
    # or fabricated lemme.
    ("connais", "connais", "VER", "inf;"),
    ("mentez", "mentez", "VER", "inf;"),
    ("parait", "parait", "VER", "inf;"),
    ("plus", "plus", "VER", "par:pas;"),
    ("réélus", "réélus", "VER", "par:pas;"),
    ("sais", "sais", "VER", "imp:pre:2s;"),
    ("voulez", "vouler", "VER", "inf;"),
    ("bouffis", "bouffi", "VER", "par:pas;"),
    ("débraillés", "débraillé", "VER", "par:pas;"),
}


def findAndDelete(path: str, apply: bool) -> tuple[list[str], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    found: list[str] = []
    outputLines = [lines[0]]
    for i in range(1, len(lines)):
        if not lines[i].strip():
            outputLines.append(lines[i])
            continue
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx], fields[cgramIdx], fields[infoverIdx])
        if key in ROWS_TO_DELETE:
            found.append(f"ortho={key[0]!r} lemme={key[1]!r} cgram={key[2]!r} infover={key[3]!r}")
            if not apply:
                outputLines.append(lines[i])
            continue
        outputLines.append(lines[i])

    if apply and found:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(outputLines)

    return found, len(found)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete 10 spurious duplicate VER/AUX rows, each an "
        "ortho already correctly represented elsewhere, wrongly duplicated "
        "under an unrelated lemma."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the deletions to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        found, count = findAndDelete(path, args.apply)
        print(f"=== {path} ===")
        for f in found:
            print(f"  DELETE: {f}")
        print(f"Total rows found: {count} (expected {len(ROWS_TO_DELETE)})")
        if args.apply:
            print(f"--apply: updated {path}")
        print()


if __name__ == "__main__":
    main()
