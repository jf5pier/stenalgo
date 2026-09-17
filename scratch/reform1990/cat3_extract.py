"""Extract and classify category 3 (mots empruntés) entries from the 26 Wiktionnaire
subpages, cross-checked against Lexique383/LexiqueMixte for corpus attestation.

Category 3 words split into two independent axes that can each apply or not:
  - accent: the reform adds a French-style accent to a bare loanword letter (e.g.
    arboretum -> arborétum). Same single-char-insertion mechanism as categories 5/6/12.
  - plural: the reform regularizes an irregular/foreign plural to a plain French "-s"
    (e.g. un match, des matches -> des matchs). This is a NEW mechanism: it only touches
    number="p" rows sharing the lemme, never the singular.

A word can need one, both, or neither (the "plain" bucket with no plural shown and no
accent difference from its own bare form is usually an invariable expression, not
handled here).
"""
import json
import re
import sys

sys.path.insert(0, "/home/jfsp/stenalgo")

LEXIQUE_PATH = "resources/LexiqueMixte.tsv"

ACCENT_STRIP = {
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "â": "a", "à": "a",
    "î": "i", "ï": "i",
    "ô": "o",
    "û": "u", "ü": "u",
    "œ": "oe",
}


def loadLexiqueOrthos(path: str) -> set[str]:
    orthos = set()
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        orthoIdx = header.index("ortho")
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) > orthoIdx:
                orthos.add(fields[orthoIdx])
    return orthos


def links(s: str) -> list[str]:
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", s)


def extractLines(subpagesPath: str) -> list[str]:
    d = json.load(open(subpagesPath))
    pages = d["query"]["pages"]
    lines = []
    for _, p in pages.items():
        text = p["revisions"][0]["slots"]["main"]["*"]
        for line in text.split("\n"):
            if "#Mots empruntés" in line:
                lines.append(line.strip())
    return lines


def candidateOldSpellings(newWord: str) -> list[str]:
    """All ways to strip exactly one accented letter back to its bare form."""
    candidates = []
    for i, ch in enumerate(newWord):
        if ch in ACCENT_STRIP:
            bare = ACCENT_STRIP[ch]
            candidates.append(newWord[:i] + bare + newWord[i + 1:])
    return candidates


def main() -> None:
    lines = extractLines("scratch/reform1990/subpages.json")
    lexiqueOrthos = loadLexiqueOrthos(LEXIQUE_PATH)

    rows = []
    for line in lines:
        lk = links(line)
        if not lk:
            continue
        newWord = lk[0]
        if " " in newWord or "-" in newWord:
            continue  # multi-word/hyphenated, never survives into LexiqueMixte (cat 2/4 finding)

        explicitOld = None
        m = re.search(r"au lieu d[e’']\s*\[\[([^\]|]+)", line)
        if m:
            explicitOld = m.group(1)
        else:
            m = re.search(r"plutôt qu[e’']\s*\[\[([^\]|]+)", line)
            if m:
                explicitOld = m.group(1)

        newPlural = None
        pluralLinks = re.findall(r"des \[\[([^\]|]+)", line)
        if pluralLinks:
            newPlural = pluralLinks[0]

        rows.append({
            "line": line,
            "newWord": newWord,
            "explicitOld": explicitOld,
            "newPlural": newPlural,
        })

    accentOnly, explicitPairs, pluralOnly, unclassified = [], [], [], []
    for r in rows:
        newWord = r["newWord"]
        if r["explicitOld"]:
            explicitPairs.append(r)
            continue
        cands = candidateOldSpellings(newWord)
        attestedOld = [c for c in cands if c in lexiqueOrthos]
        r["accentCandidates"] = attestedOld
        if attestedOld:
            accentOnly.append(r)
        elif r["newPlural"]:
            pluralOnly.append(r)
        else:
            unclassified.append(r)

    print(f"Total single-token cat-3 rows: {len(rows)}")
    print(f"  explicit old/new pairs (au lieu de / plutôt que): {len(explicitPairs)}")
    print(f"  accent-only (bare form attested in corpus, no explicit old): {len(accentOnly)}")
    print(f"  plural-only (has 'des X' plural, no accent match): {len(pluralOnly)}")
    print(f"  unclassified (no explicit old, no accent match, no plural shown): {len(unclassified)}")
    print()

    print("=== explicit pairs, corpus attestation ===")
    for r in explicitPairs:
        newAttested = r["newWord"] in lexiqueOrthos
        oldAttested = r["explicitOld"] in lexiqueOrthos
        print(f"{r['explicitOld']!r:20} -> {r['newWord']!r:20} old={oldAttested} new={newAttested}")

    print()
    print("=== accent-only candidates (both attested) ===")
    for r in accentOnly:
        newAttested = r["newWord"] in lexiqueOrthos
        print(f"{r['accentCandidates']} -> {r['newWord']!r:20} new_attested={newAttested} plural_shown={r['newPlural']}")

    print()
    print(f"=== plural-only sample (first 30 of {len(pluralOnly)}) ===")
    for r in pluralOnly[:30]:
        print(f"{r['newWord']!r:20} plural={r['newPlural']!r:20} new_attested={r['newWord'] in lexiqueOrthos} plural_attested={r['newPlural'] in lexiqueOrthos}")


if __name__ == "__main__":
    main()
