#!/bin/env python
#
# Hand-derived completion of the 26 ass:eoir dual-form gaps that
# util/fixAsseoirDualFormGaps.py's donor-borrowing approach couldn't fill
# (only 2 lemmas -- asseoir, rasseoir -- share this template, so most
# missing forms have zero cross-lemma donor data). Derived with the user,
# grounded in three kinds of evidence, never guessed cold:
#
# 1. Same-lemma sibling anchors: asseoir/rasseoir already attest ONE row
#    per alternant-family in most tenses (e.g. "assoyait" for the oi-
#    imparfait, "assoit"/"rassoit" for oi-présent-3s) -- the missing
#    sibling persons are derived by applying the exact same phon/syll_cv/
#    orthosyll_cv transformation already visible between OTHER already-
#    attested person pairs within the SAME lemma/alternant (e.g. how
#    "assoyez"/"assoyons" already relate to each other).
# 2. The "-eye-" alternant (asseyerai, asseyerions, ...) is structurally
#    identical to the pa:yer template's own "y"-form futur/cnd (radical +
#    "Ej" + "°R" + person ending) -- this session's own
#    fixPayerNonfuturVowelQuality.py/fixAyGraphemeEjQuality.py fixes
#    established that "ey"/"ay" graphemes are always open "E" + glide "j"
#    in this lexicon's transcription, and resources/LexiqueMixte.tsv's
#    "payerai"=pEj°Re / "payerions"-shaped forms give the exact futur/cnd
#    tail to splice on.
# 3. The "-oi-" alternant's imparfait 1p/2p (assoyions/assoyiez), missing
#    from BOTH ass:eoir lemmas, are cross-checked against regular "-oyer"
#    verbs elsewhere in the lexicon with the identical grapheme
#    (employions/envoyions/nettoyiez), which already attest how "oy"+
#    "-ions"/"-iez" behaves (a doubled glide "j_j" for -ions, a silent-i
#    "j_#" for -iez) -- applied to assoyer's own "wa_j" radical shape.
#
# Two kinds of fix:
#   TAG_ONLY_FIXES -- an existing resources/Lexique383.tsv row is missing a
#     tag its own sibling already carries (e.g. "assoyons" has ind:pre:1p;
#     but not the imp:pre:1p; that its "eye"-sibling "asseyons" already
#     carries for the identical, genuinely homophonous form). Fixed at the
#     Lexique383.tsv level, NOT LexiqueMixte.tsv directly -- now that
#     lexique.py's outputMixedLexique() actually regenerates
#     resources/LexiqueMixte.tsv from Lexique383.tsv + LexiqueInfraCorrespondance.tsv
#     on every run, any edit made only to LexiqueMixte.tsv is silently lost
#     the next time `python lexique.py` runs (learned the hard way earlier
#     this session -- the first version of this script patched
#     LexiqueMixte.tsv directly and the fix vanished on the next pipeline run).
#   NEW_SYNTHETIC_ROWS -- appended to resources/LexiqueSynthetic.tsv
#     (source=synthetic), per established project convention (see
#     util/fixPayerDualFormGaps.py) of not writing generated dual-form rows
#     directly into LexiqueMixte.tsv. This file isn't touched by
#     lexique.py's regeneration, so it's safe from the same trap.
#
# Dry-run by default: only reads and reports. --apply writes both. Both are
# idempotent (tag fixes are no-ops if the tag is already present; row
# generation checks resources/LexiqueSynthetic.tsv first). After --apply,
# `python lexique.py` must be re-run to actually propagate the
# Lexique383.tsv tag fixes into resources/LexiqueMixte.tsv.
import argparse
import os

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)

# (ortho, lemme, cgram, oldInfover) -> newInfover (full replacement, tag added)
TAG_ONLY_FIXES: dict[tuple[str, str, str, str], str] = {
    ("assoyons", "asseoir", "VER", "ind:pre:1p;"): "imp:pre:1p;ind:pre:1p;",
    ("assoirais", "asseoir", "VER", "cnd:pre:1s;"): "cnd:pre:1s;cnd:pre:2s;",
}

# Each: ortho, phon, lemme, infover, syll_cv, orthosyll_cv
NEW_SYNTHETIC_ROWS: list[tuple[str, str, str, str, str, str]] = [
    # --- asseoir, "oi"-imparfait (anchor: attested "assoyait"=aswajE) ---
    ("assoyais", "aswajE", "asseoir", "ind:imp:1s;ind:imp:2s;",
     "a|s_wa_j|E", "a|ss_o_y|ais"),
    ("assoyaient", "aswajE", "asseoir", "ind:imp:3p;",
     "a|s_wa_j|E", "a|ss_o_y|aient"),
    # cross-checked against employions/envoyions/nettoyiez (regular -oyer verbs)
    ("assoyions", "aswajj§", "asseoir", "ind:imp:1p;",
     "a|s_wa_j_j|§", "a|ss_o_y_i|ons"),
    ("assoyiez", "aswaje", "asseoir", "ind:imp:2p;",
     "a|s_wa_j_#|e", "a|ss_o_y_i|ez"),

    # --- asseoir, "eye"-futur/cnd (pa:yer "y"-form Ej°R pattern) ---
    ("asseyerai", "asEj°Re", "asseoir", "ind:fut:1s;",
     "a|s_E|j_°|R_e", "a|ss_e|y_e|r_ai"),
    ("asseyeras", "asEj°Ra", "asseoir", "ind:fut:2s;",
     "a|s_E|j_°|R_a", "a|ss_e|y_e|r_as"),
    ("asseyera", "asEj°Ra", "asseoir", "ind:fut:3s;",
     "a|s_E|j_°|R_a", "a|ss_e|y_e|r_a"),
    ("asseyeront", "asEj°R§", "asseoir", "ind:fut:3p;",
     "a|s_E|j_°|R_§", "a|ss_e|y_e|r_ont"),
    ("asseyerais", "asEj°RE", "asseoir", "cnd:pre:1s;cnd:pre:2s;",
     "a|s_E|j_°|R_E", "a|ss_e|y_e|r_ais"),
    ("asseyerait", "asEj°RE", "asseoir", "cnd:pre:3s;",
     "a|s_E|j_°|R_E", "a|ss_e|y_e|r_ait"),
    ("asseyeraient", "asEj°RE", "asseoir", "cnd:pre:3p;",
     "a|s_E|j_°|R_E", "a|ss_e|y_e|r_aient"),
    # tail "°R_j_§"/"r_i_ons" mirrors this lemma's own attested
    # assiérions (ié-form): asjeRj§ / a|s_j_e|R_j_§ / a|ss_i_é|r_i_ons
    ("asseyerions", "asEj°Rj§", "asseoir", "cnd:pre:1p;",
     "a|s_E|j_°|R_j_§", "a|ss_e|y_e|r_i_ons"),

    # --- asseoir, "oi"-futur/cnd gaps not covered by tag-only fixes ---
    # tail transform mirrors assiérait->assiérions within this lemma,
    # applied to the attested oi-anchor assoirait=aswaRE/a|s_wa|R_E/a|ss_oi|r_ait
    ("assoirions", "aswaRj§", "asseoir", "cnd:pre:1p;",
     "a|s_wa|R_j_§", "a|ss_oi|r_i_ons"),
    # ié-form 3p, missing entirely (assiérais/assiérait attested, assiéraient
    # isn't) -- "aient"/"ait" are homophonous in French futur/cnd, same
    # convention already used for this lemma's own asseyaient/asseyait pair
    ("assiéraient", "asjeRE", "asseoir", "cnd:pre:3p;",
     "a|s_j_e|R_E", "a|ss_i_é|r_aient"),

    # --- rasseoir, mirrors asseoir's own "R_a|..." prefix pattern ---
    ("rassoyons", "Raswaj§", "rasseoir", "ind:pre:1p;",
     "R_a|s_wa_j|§", "r_a|ss_o_y|ons"),
    # matches rasseyez's own combined tag convention (imp:pre:2p;ind:pre:2p;)
    ("rassoyez", "Raswaje", "rasseoir", "imp:pre:2p;ind:pre:2p;",
     "R_a|s_wa_j|e", "r_a|ss_o_y|ez"),
    ("rassoyais", "RaswajE", "rasseoir", "ind:imp:1s;",
     "R_a|s_wa_j|E", "r_a|ss_o_y|ais"),
    ("rassoyaient", "RaswajE", "rasseoir", "ind:imp:3p;",
     "R_a|s_wa_j|E", "r_a|ss_o_y|aient"),
    # mirrors asseoir's own attested asseyes/asseye (eye-form sub:pre)
    ("rasseyes", "RasEj", "rasseoir", "sub:pre:2s;",
     "R_a|s_E_j_#", "r_a|ss_e_y_es"),
    ("rasseye", "RasEj", "rasseoir", "sub:pre:3s;",
     "R_a|s_E_j_#", "r_a|ss_e_y_e"),
    # t->s tail swap mirrors this lemma's own attested rassoit->rassois
    # shape (identical to asseoir's own assoit->assois swap)
    ("rassois", "Raswa", "rasseoir", "imp:pre:2s;",
     "R_a|s_wa_#", "r_a|ss_oi_s"),
]


def readLines(path: str) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        return f.readlines()


def applyTagFixes(apply: bool) -> tuple[list[str], list[str]]:
    lines = readLines(LEXIQUE_383_PATH)
    header = lines[0].rstrip("\n").split("\t")
    idx = {name: header.index(name) for name in ("ortho", "lemme", "cgram", "infover")}

    fixed: list[str] = []
    skipped: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[idx["ortho"]], fields[idx["lemme"]], fields[idx["cgram"]], fields[idx["infover"]])
        if key not in TAG_ONLY_FIXES:
            continue
        newInfover = TAG_ONLY_FIXES[key]
        fixed.append(f"{key[0]!r} infover {key[3]!r} -> {newInfover!r}")
        if apply:
            fields[idx["infover"]] = newInfover
            lines[i] = "\t".join(fields) + "\n"

    if apply and fixed:
        with open(LEXIQUE_383_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    for key in TAG_ONLY_FIXES:
        if not any(key[0] in f for f in fixed):
            skipped.append(f"{key!r}: target row not found (already fixed, or moved)")

    return fixed, skipped


def applyNewRows(apply: bool) -> list[str]:
    existing: set[tuple[str, str]] = set()
    if os.path.exists(SYNTHETIC_PATH):
        for line in readLines(SYNTHETIC_PATH)[1:]:
            if not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            existing.add((fields[0], fields[2]))  # (ortho, lemme)

    toWrite: list[str] = []
    generated: list[str] = []
    for ortho, phon, lemme, infover, syll_cv, orthosyll_cv in NEW_SYNTHETIC_ROWS:
        if (ortho, lemme) in existing:
            continue
        generated.append(f"{lemme} {ortho!r} infover={infover!r}")
        row = "\t".join([
            ortho, phon, lemme, "VER", "VER", "", "", infover,
            syll_cv, orthosyll_cv, "0.0", "0.0", "synthetic",
        ]) + "\n"
        toWrite.append(row)

    if apply and toWrite:
        fileExists = os.path.exists(SYNTHETIC_PATH)
        with open(SYNTHETIC_PATH, "a", newline="", encoding="utf-8") as f:
            if not fileExists:
                f.write(SYNTHETIC_HEADER)
            f.writelines(toWrite)

    return generated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the hand-derived ass:eoir dual-form gap fixes: "
        "tag-only corrections to LexiqueMixte.tsv, new rows to "
        "LexiqueSynthetic.tsv."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Write both files (default: dry-run report only).")
    args = parser.parse_args()

    fixed, skippedTags = applyTagFixes(args.apply)
    print(f"=== Tag-only fixes to {LEXIQUE_383_PATH} ===")
    for f in fixed:
        print(f"  FIX: {f}")
    for s in skippedTags:
        print(f"  SKIP: {s}")

    generated = applyNewRows(args.apply)
    print(f"\n=== New rows for {SYNTHETIC_PATH} ({len(generated)}) ===")
    for g in generated:
        print(f"  {g}")

    if args.apply:
        print(f"\n--apply: {len(fixed)} tag fix(es) written, {len(generated)} row(s) appended")


if __name__ == "__main__":
    main()
