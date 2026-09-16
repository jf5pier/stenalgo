#!/usr/bin/python
# coding: utf-8
"""
Match 1990-reform new-spelling words (scraped from Wiktionnaire's annex subpages) to their
traditional-spelling counterpart already present in Lexique383, using a weighted edit
distance: substituting an accented letter for its bare counterpart (the rule always REMOVES
an accent from specific letters -- never adds one) costs almost nothing, any other edit costs
the normal 1.0. A clean match is one whose total cost comes entirely from accent-only
substitutions (i.e. cost is a multiple of ACCENT_COST with zero ordinary edits).
"""
import json
import csv
import re
from collections import defaultdict

ACCENT_COST = 0.1
ACCENT_PAIRS = {
    ("î", "i"), ("Î", "I"),
    ("û", "u"), ("Û", "U"),
    ("é", "è"), ("É", "È"),   # accent grave replacing aigu (category 5)
    ("ë", "e"), ("Ë", "E"),   # tréma removed/shifted (category 7, handled separately though)
    ("ï", "i"), ("Ï", "I"),
    ("ü", "u"), ("Ü", "U"),
}


def substitutionCost(a: str, b: str) -> float:
    if a == b:
        return 0.0
    if (a, b) in ACCENT_PAIRS or (b, a) in ACCENT_PAIRS:
        return ACCENT_COST
    return 1.0


def weightedEditDistance(a: str, b: str) -> float:
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,
                dp[i][j - 1] + 1.0,
                dp[i - 1][j - 1] + substitutionCost(a[i - 1], b[j - 1]),
            )
    return dp[n][m]


def extractFirstWord(line: str) -> str | None:
    # First wikilink on the line: [[target]] or [[target|display]]. When a display text is
    # given, it's the actual reform-affected word (e.g. "[[abcéder|abcèdera]] (il)" -- the
    # reform changes the future/conditional conjugation "abcèdera", not the infinitive lemma
    # "abcéder" the link points to), so prefer display over target. Skips section-anchor
    # links (#...).
    for m in re.finditer(r"\[\[([^\]|#]+)(?:\|([^\]]*))?\]\]", line):
        target, display = m.group(1).strip(), m.group(2)
        return display.strip() if display else target
    return None


def loadCategoryWords(subpagesJson: str, categoryTag: str, categoryLabel: str) -> list[str]:
    d = json.load(open(subpagesJson))
    pages = d["query"]["pages"]
    words = []
    for _, p in pages.items():
        wt = p["revisions"][0]["slots"]["main"]["*"]
        for line in wt.split("\n"):
            line = line.strip()
            if not line.startswith("*"):
                continue
            if categoryTag in line and categoryLabel in line:
                w = extractFirstWord(line)
                if w:
                    words.append(w)
    return words


def loadLexiqueWords(lexiquePath: str) -> tuple[set[str], set[str], dict[str, set[str]], dict[str, float]]:
    orthos: set[str] = set()
    lemmes: set[str] = set()
    gramCatsByOrtho: dict[str, set[str]] = defaultdict(set)
    freqByOrtho: dict[str, float] = defaultdict(float)
    with open(lexiquePath) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            orthos.add(row["ortho"])
            lemmes.add(row["lemme"])
            if row["cgram"]:
                gramCatsByOrtho[row["ortho"]].add(row["cgram"])
            try:
                freqByOrtho[row["ortho"]] += float(row["freqlemfilms2"]) + float(row["freqlemlivres"])
            except ValueError:
                pass
    return orthos, lemmes, gramCatsByOrtho, freqByOrtho


def findOldSpelling(newWord: str, lexiqueWords: set[str]) -> list[str]:
    """Generate every candidate old spelling by re-accenting each eligible letter (one at a
    time, and in combination for words with multiple eligible letters), and keep those that
    are real Lexique383 words. Returns all matches found (ideally exactly one).

    A plain letter can map to MORE THAN ONE accented form (e.g. plain 'i' could have been
    'î' -- circumflex -- or 'ï' -- tréma -- in the traditional spelling), so every position
    must try every accented alternative, not just one arbitrarily picked candidate."""
    alternativesByPosition: list[list[str]] = []
    eligiblePositions: list[int] = []
    for i, ch in enumerate(newWord):
        accentedForms = sorted({acc for acc, pl in ACCENT_PAIRS if pl == ch})
        if accentedForms:
            eligiblePositions.append(i)
            alternativesByPosition.append([ch] + accentedForms)  # ch itself = "unchanged"

    candidates: set[str] = set()
    from itertools import product
    for choice in product(*alternativesByPosition):
        if all(c == newWord[pos] for c, pos in zip(choice, eligiblePositions)):
            continue  # unchanged -- same as newWord itself, not a candidate
        chars = list(newWord)
        for pos, c in zip(eligiblePositions, choice):
            chars[pos] = c
        candidate = "".join(chars)
        if candidate in lexiqueWords:
            candidates.add(candidate)
    return sorted(candidates)


SUBPAGES_JSON = "scratch/reform1990/subpages.json"
LEXIQUE_PATH = "resources/Lexique383.tsv"
OUT_TSV = "scratch/reform1990/cat5_6_matches.tsv"


def gramCatsOverlap(oldCats: set[str], newCats: set[str]) -> bool:
    # cgram overlap is a HINT for manual review, not a hard filter: it correctly flags
    # mûre/mure and faîte/faite, but also flags boîte/boite and soûl/soul (both genuine
    # reform pairs whose reform-spelling row happens to only carry an unrelated homograph's
    # gramCat in the corpus), and it misses fût/fut and sûre/sure (both real false positives
    # that happen to share a gramCat). Verified by hand against the actual reform rule text.
    if not oldCats or not newCats:
        return True  # missing gramCat data -- can't rule it out, fall through to manual review
    return bool(oldCats & newCats)


# Manually vetted against the actual 1990-reform rule text (see STATUS.md for the reasoning
# behind each exclusion). Category 6 (circumflex on i/u) only has 11 corpus-attested candidates
# total, so full manual review is cheap and more reliable than any automatic gramCat/frequency
# heuristic (see gramCatsOverlap's docstring for why the automatic filter alone is insufficient).
CAT6_EXCEPTIONS = {
    "faîte": "homograph collision: 'faite' is the extremely common fem. past participle of faire",
    "fût": "homograph collision: 'fut' is the standard passé-simple of être ('il fut')",
    "mûre": "homograph collision: 'mure' is a conjugated form of murer ('to wall up')",
    "sûre": "documented Académie exception: circumflex is explicitly KEPT on sûr/sûrs/sûre/sûres "
            "because 'sure' already means something else (sour/tart)",
}


# See STATUS.md for the reasoning behind each exclusion. Not yet reviewed for category 5 --
# populate as false positives are found (same manual-review process as category 6, since the
# automatic gramCat filter proved unreliable there).
CAT5_EXCEPTIONS: dict[str, str] = {}


def processCategory(
    categoryNum: int,
    categoryTag: str,
    categoryLabel: str,
    exceptions: dict[str, str],
    lexiqueWords: set[str],
    gramCatsByOrtho: dict[str, set[str]],
    freqByOrtho: dict[str, float],
) -> list[tuple[str, str, float, bool]]:
    words = sorted(set(loadCategoryWords(SUBPAGES_JSON, categoryTag, categoryLabel)))

    print(f"=== Category {categoryNum} ({categoryLabel}): {len(words)} unique seed words ===")
    candidates, ambiguous, notFound, notInLexique = [], [], [], []
    for w in words:
        if w not in lexiqueWords:
            notInLexique.append(w)
            continue
        matches = findOldSpelling(w, lexiqueWords)
        if len(matches) == 1:
            old = matches[0]
            dist = weightedEditDistance(w, old)
            candidates.append((w, old, dist))
        elif len(matches) > 1:
            ambiguous.append((w, matches))
        else:
            notFound.append(w)

    accepted = [(w, old, dist) for w, old, dist in candidates if old not in exceptions]
    excluded = [(w, old, dist) for w, old, dist in candidates if old in exceptions]

    print(f"candidate 1:1 matches: {len(candidates)}")
    print(f"  accepted (real reform pairs): {len(accepted)}")
    print(f"  excluded (manually-vetted false positives): {len(excluded)}")
    print(f"ambiguous (>1 candidate): {len(ambiguous)}")
    print(f"no old-spelling counterpart found in Lexique383: {len(notFound)}")
    print(f"new-spelling word itself not in Lexique383: {len(notInLexique)}")
    print()
    print("-- accepted (still needs manual spot-check before trusting) --")
    for w, old, dist in accepted:
        gramOverlap = gramCatsOverlap(gramCatsByOrtho.get(old, set()), gramCatsByOrtho.get(w, set()))
        print(f"  {old} -> {w}  (cost={dist:.2f}, gramCatOverlap={gramOverlap}, "
              f"freq old={freqByOrtho.get(old, 0):.1f}, freq new={freqByOrtho.get(w, 0):.1f})")
    print()
    print("-- excluded (manually-vetted false positives) --")
    for w, old, dist in excluded:
        print(f"  {old} -> {w}: {exceptions[old]}")
    print()
    print("-- ambiguous --")
    for w, matches in ambiguous[:20]:
        print(f"  {w}: candidates={matches}")
    print()
    print("-- not found in Lexique383 (old spelling absent from corpus) --")
    print(", ".join(notFound[:40]))
    print()
    print("-- new-spelling word itself absent from Lexique383 --")
    print(", ".join(notInLexique[:40]))
    print()

    return [(w, old, dist, old in exceptions) for w, old, dist in candidates]


def main() -> None:
    orthos, lemmes, gramCatsByOrtho, freqByOrtho = loadLexiqueWords(LEXIQUE_PATH)
    lexiqueWords = orthos | lemmes

    results6 = processCategory(6, "[6]", "Accent circonflexe", CAT6_EXCEPTIONS,
                                lexiqueWords, gramCatsByOrtho, freqByOrtho)
    results5 = processCategory(5, "[5]", "Accent grave au lieu de l’accent aigu", CAT5_EXCEPTIONS,
                                lexiqueWords, gramCatsByOrtho, freqByOrtho)

    with open(OUT_TSV, "w") as f:
        f.write("oldSpelling\tnewSpelling\tcategory\tappliesToLemmeNormalization\tisException\tnote\n")
        for categoryNum, exceptions, results in ((6, CAT6_EXCEPTIONS, results6), (5, CAT5_EXCEPTIONS, results5)):
            for w, old, dist, isException in results:
                note = exceptions.get(old, "").replace("\t", " ")
                applies = not isException
                f.write(f"{old}\t{w}\t{categoryNum}\t{applies}\t{isException}\t{note}\n")


if __name__ == "__main__":
    main()
