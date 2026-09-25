#!/bin/env python
#
# Builds resources/spellingVariants.tsv: the decisions table that keeps ONE
# canonical spelling per variant set (TODO.md "Remove spelling variants from
# the lexicon") and drops the others from the whole pipeline
# (src/spellingvariants.py enforces it).
#
# A variant set is a group of spellings of the SAME word -- 1990-reform pairs
# (resources/reform1990.tsv), the B44-known non-reform families (seeded below,
# e.g. trimbaler/trimballer, chlinguer/schlinguer), plus sets discovered
# empirically in the lexicons: two distinct lemmes that share one phonology
# string and one grammatical category, and whose spellings differ by exactly
# one application of one pattern from the small family below (geminate
# simplification, circumflex drop, accent change, ...). The same-(phon, cgram)
# grouping is the main false-positive guard; the one-pattern-once rule is what
# keeps e.g. the dessoûler/dessouler/dessaouler family separate from
# saouler/soûler.
#
# The canonical spelling of each set is the member whose inflected forms have
# the highest Google Books Ngram count in the 2010-2019 window, read from
# resources/LexiqueGoogleNgram.tsv (util/ngram_data.py extract-lexique) --
# Lexique's own frequencies are near zero for rare variants and cannot
# arbitrate. Sets the numbers cannot settle (top two within a factor of 2, or
# both under REVIEW_MIN_OCCURRENCES) are emitted with status "review" for a
# human to settle; nothing is enforced until the row is set to "active".
#
# Dry-run by default: prints the full review table. --emit additionally writes
# the draft resources/spellingVariants.tsv. THE EMITTED DRAFT MUST BE REVIEWED
# WORD-BY-WORD BEFORE THE ENFORCEMENT HOOKS RUN ON IT.
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

REFORM_TSV = "resources/reform1990.tsv"
EXCLUSIONS_TSV = "resources/lexiconExclusions.tsv"
LEXIQUE_PATHS = ("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv")
LEXIQUE_NGRAM_TSV = "resources/LexiqueGoogleNgram.tsv"
SPELLING_VARIANTS_TSV = "resources/spellingVariants.tsv"

# 2010-2019 is the last decade of the v3 corpus (books through 2019) and the
# window the canonical decision arbitrates on.
DECISION_WINDOW_COLUMN = "count2010_2019"
REVIEW_RATIO = 2.0
REVIEW_MIN_OCCURRENCES = 50

# The B44-known non-reform variant families (TODO.md), verbatim. Seeds are
# known truth: if one fails the discovery guards, the script says so loudly
# instead of silently dropping it.
SEED_VARIANT_SETS = (
    frozenset({"trimbaler", "trimballer"}),
    frozenset({"dessoûler", "dessouler", "dessaouler"}),
    frozenset({"saouler", "soûler"}),
    frozenset({"toquade", "tocade"}),
    frozenset({"toquard", "tocard"}),
    frozenset({"dégoter", "dégotter"}),
    frozenset({"zieuter", "zyeuter"}),
    frozenset({"chlinguer", "schlinguer"}),
    frozenset({"évènementiel", "événementiel"}),
    frozenset({"béluga", "beluga"}),
)

# One application of one pattern turns spelling a into spelling b (either
# direction unless marked one-way). Free position; other occurrences of the
# pattern string stay untouched ("applied once").
# (from, to, oneWay)
VARIANT_EDIT_PATTERNS: tuple[tuple[str, str, bool], ...] = (
    # circumflex drop/add
    ("û", "u", False), ("î", "i", False), ("â", "a", False),
    ("ê", "e", False), ("ô", "o", False),
    # accent changes (one-way: the reform goes é->è; e is the unaccented drift)
    ("é", "è", True), ("é", "e", True), ("è", "e", True),
    # vowel clusters
    ("aou", "oû", True), ("oû", "ou", True), ("aou", "ou", False),
    # geminate simplification, either direction
    *((double, double[0], False)
      for double in ("ll", "tt", "mm", "nn", "rr", "ss", "pp",
                     "ff", "gg", "dd", "bb", "cc", "zz")),
    # misc single-letter respellings
    ("y", "i", False), ("sch", "ch", False), ("qu", "c", True),
)

MAX_LENGTH_DIFFERENCE = 2


# ═══════════════════════════════════════════════════════════════════════════
# Pattern matching (shared with util/ngram_data.py extract-additions, which
# excludes near-variant spellings of lexicon words from the neologism table)
# ═══════════════════════════════════════════════════════════════════════════

def singleEditVariantsOf(word: str, source: str, target: str) -> set[str]:
    """Every string obtained by replacing exactly one occurrence of source
    with target in word. Other occurrences stay untouched."""
    variants: set[str] = set()
    start = word.find(source)
    while start != -1:
        variants.add(word[:start] + target + word[start + len(source):])
        start = word.find(source, start + 1)
    return variants


def singleEditVariants(word: str) -> set[str]:
    """Every string one single pattern application away from word, in EITHER
    direction (one-way restrictions do not apply here: a rare variant can sit
    on either side of a lexicon word). Used by isNearVariantSpelling."""
    variants: set[str] = set()
    for source, target, _oneWay in VARIANT_EDIT_PATTERNS:
        variants |= singleEditVariantsOf(word, source, target)
        variants |= singleEditVariantsOf(word, target, source)
    return variants


def isNearVariantSpelling(candidate: str, lexiconWords: set[str]) -> bool:
    """True if candidate is one single variant-pattern edit away from a
    lexicon word (candidate itself is NOT in lexiconWords)."""
    return bool(singleEditVariants(candidate) & lexiconWords)


def matchSingleEditPattern(a: str, b: str) -> str | None:
    """The pattern turning a into b ('é->è'), or None. Exactly one
    application of one pattern, at any position; one-way patterns only apply
    in their own direction."""
    if abs(len(a) - len(b)) > MAX_LENGTH_DIFFERENCE:
        return None
    for source, target, oneWay in VARIANT_EDIT_PATTERNS:
        if b in singleEditVariantsOf(a, source, target):
            return f"{source}->{target}"
        if not oneWay and b in singleEditVariantsOf(a, target, source):
            return f"{target}->{source}"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Inputs
# ═══════════════════════════════════════════════════════════════════════════

def loadReform1990Rows(tsvPath: str = REFORM_TSV) -> list[dict[str, str]]:
    """Non-exception rows of reform1990.tsv. isException rows (fût/fut,
    croît/croit...) collide with genuinely distinct words and must never be
    merged or dropped."""
    with open(tsvPath, newline="", encoding="utf-8") as f:
        rows = [line.rstrip("\n") for line in f if not line.startswith("#")]
    reader = csv.DictReader(rows, delimiter="\t")
    return [row for row in reader
            if row["isException"] != "True" and row["oldSpelling"]]


def loadExceptionSpellings(tsvPath: str = REFORM_TSV) -> set[str]:
    with open(tsvPath, newline="", encoding="utf-8") as f:
        rows = [line.rstrip("\n") for line in f if not line.startswith("#")]
    spellings: set[str] = set()
    for row in csv.DictReader(rows, delimiter="\t"):
        if row["isException"] == "True":
            spellings.update({row["oldSpelling"], row["newSpelling"]})
    return spellings


def loadExcludedWords(tsvPath: str = EXCLUSIONS_TSV) -> set[str]:
    with open(tsvPath, newline="", encoding="utf-8") as f:
        rows = [line for line in f if not line.startswith("#")]
    return {row["word"] for row in csv.DictReader(rows, delimiter="\t")}


def loadLexiqueRows(paths: tuple[str, ...] = LEXIQUE_PATHS) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        table = Path(path)
        if not table.exists():
            continue
        with open(table, newline="", encoding="utf-8") as f:
            rows.extend(csv.DictReader(f, delimiter="\t"))
    return rows


def loadNgramCounts(tsvPath: str = LEXIQUE_NGRAM_TSV) -> dict[str, int]:
    """word -> 2010-2019 count from LexiqueGoogleNgram.tsv."""
    with open(tsvPath, newline="", encoding="utf-8") as f:
        rows = [line.rstrip("\n") for line in f if not line.startswith("#")]
    counts: dict[str, int] = {}
    for row in csv.DictReader(rows, delimiter="\t"):
        counts[row["word"]] = int(row[DECISION_WINDOW_COLUMN])
    return counts


# ═══════════════════════════════════════════════════════════════════════════
# Union-find
# ═══════════════════════════════════════════════════════════════════════════

class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != root:  # path compression
            self.parent[item], item = root, self.parent[item]
        return root

    def union(self, a: str, b: str) -> None:
        rootA, rootB = self.find(a), self.find(b)
        if rootA != rootB:
            self.parent[rootB] = rootA

    def sets(self) -> list[frozenset[str]]:
        groups: dict[str, set[str]] = defaultdict(set)
        for item in self.parent:
            groups[self.find(item)].add(item)
        return [frozenset(group) for group in groups.values()]


# ═══════════════════════════════════════════════════════════════════════════
# Discovery (phases A-C)
# ═══════════════════════════════════════════════════════════════════════════

def discoverVariantSets(lexiqueRows: list[dict[str, str]],
                        excludedWords: set[str] | None = None,
                        exceptionSpellings: set[str] | None = None,
                        reformRows: list[dict[str, str]] | None = None,
                        ) -> tuple[list[frozenset[str]], list[frozenset[str]]]:
    """Returns (variantSets, seedSetsRejectedByGuards). Union-finds together:
    the reform1990 non-exception pairs, the SEED_VARIANT_SETS, and every pair
    of distinct lemmes sharing one (phon, cgram) group whose spellings differ
    by one single-edit pattern."""
    excludedWords = excludedWords if excludedWords is not None \
        else loadExcludedWords()
    exceptionSpellings = exceptionSpellings if exceptionSpellings is not None \
        else loadExceptionSpellings()
    reformRows = reformRows if reformRows is not None else loadReform1990Rows()
    blocked = excludedWords | exceptionSpellings

    union = UnionFind()
    reformSpellingPairs: set[frozenset[str]] = set()
    for row in reformRows:
        old, new = row["oldSpelling"], row["newSpelling"]
        reformSpellingPairs.add(frozenset({old, new}))
        union.add(old)
        union.add(new)
        union.union(old, new)

    for seed in SEED_VARIANT_SETS:
        for spelling in seed:
            union.add(spelling)
        for spelling in seed:
            union.union(sorted(seed)[0], spelling)

    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in lexiqueRows:
        groups[(row["phon"], row["cgram"])].add(row["lemme"])
    for lemmes in groups.values():
        sortedLemmes = sorted(lemmes)
        for i, lemmeA in enumerate(sortedLemmes):
            for lemmeB in sortedLemmes[i + 1:]:
                if matchSingleEditPattern(lemmeA, lemmeB) is None:
                    continue
                if lemmeA in blocked or lemmeB in blocked:
                    continue
                union.add(lemmeA)
                union.add(lemmeB)
                union.union(lemmeA, lemmeB)

    variantSets = [s for s in union.sets() if len(s) > 1]

    # Seeds are known truth: report (don't drop) any seed whose members the
    # guards refused to connect.
    roots = {spelling: union.find(spelling) for seed in SEED_VARIANT_SETS
             for spelling in seed}
    rejected = [seed for seed in SEED_VARIANT_SETS
                if len({roots[s] for s in seed}) > 1]
    return variantSets, rejected


# ═══════════════════════════════════════════════════════════════════════════
# Canonical resolution (phase D) and output
# ═══════════════════════════════════════════════════════════════════════════

def memberWindowSum(member: str, lexiqueRows: list[dict[str, str]],
                    ngramCounts: dict[str, int]) -> int:
    """The member's 2010-2019 Ngram mass: its own row plus every inflected
    ortho of rows whose lemme is the member spelling."""
    forms = {row["ortho"] for row in lexiqueRows if row["lemme"] == member}
    forms.add(member)
    return sum(ngramCounts.get(form.lower(), 0) for form in forms)


def resolveSets(variantSets: list[frozenset[str]],
                lexiqueRows: list[dict[str, str]],
                ngramCounts: dict[str, int]) -> list[dict[str, str]]:
    """Decision rows, sorted by setId: canonical = highest 2010-2019 Ngram
    mass; close calls (top two within REVIEW_RATIO, or top under
    REVIEW_MIN_OCCURRENCES) get status 'review' instead of 'active'."""
    reformPairs = loadReform1990Rows()
    reformSpellings = {spelling for row in reformPairs
                       for spelling in (row["oldSpelling"], row["newSpelling"])}
    seedSpellings = {spelling for seed in SEED_VARIANT_SETS
                     for spelling in seed}

    decisions: list[dict[str, str]] = []
    for variantSet in sorted(variantSets, key=lambda s: sorted(s)[0]):
        members = sorted(variantSet)
        sums = {member: memberWindowSum(member, lexiqueRows, ngramCounts)
                for member in members}
        ranked = sorted(members, key=lambda m: -sums[m])
        canonical, runnerUp = ranked[0], ranked[1]
        needsReview = (
            sums[canonical] < REVIEW_RATIO * max(sums[runnerUp], 1)
            or sums[canonical] < REVIEW_MIN_OCCURRENCES
        )
        if variantSet & seedSpellings:
            source = "seed"
        elif variantSet <= reformSpellings:
            source = "reform1990"
        else:
            source = "discovered"
        # Discovered sets NEVER auto-activate: same-(phon, cgram) +
        # one-pattern matching also catches genuine homophones that are
        # distinct words (tache/tâche, sur/sûr, date/datte, foret/forêt,
        # mari/marri, bite/bitte...), often with lopsided counts that would
        # otherwise look decisive. Only the curated sources (reform1990.tsv,
        # OQLF-verified; the B44 seeds) may activate without review.
        needsReview = needsReview or source == "discovered"
        note = "discovered set -- human confirms it is one word (or vetoes)" \
            if source == "discovered" else \
            ("close call or sparse data -- human settles canonical"
             if needsReview else "")
        decisions.append({
            "setId": members[0],
            "canonical": canonical,
            "dropLemmes": " ".join(m for m in members if m != canonical),
            "dropOrthos": " ".join(m for m in members if m != canonical),
            "status": "review" if needsReview else "active",
            "source": source,
            "ngramCanonical": str(sums[canonical]),
            "ngramDropped": " ".join(str(sums[m]) for m in members
                                     if m != canonical),
            "note": note,
        })
    return decisions


def printReviewTable(decisions: list[dict[str, str]]) -> None:
    print(f"{len(decisions)} variant sets\n")
    for decision in decisions:
        members = [decision["canonical"]] + decision["dropLemmes"].split()
        counts = [decision["ngramCanonical"]] + decision["ngramDropped"].split()
        flagged = " [REVIEW]" if decision["status"] == "review" else ""
        print(f"{decision['setId']}{flagged} ({decision['source']}):")
        for member, count in zip(members, counts):
            marker = "canonical" if member == decision["canonical"] \
                else "drop    "
            print(f"    {marker}  {member:<24} 2010-2019: {count}")


def emitDecisions(decisions: list[dict[str, str]],
                  outPath: str = SPELLING_VARIANTS_TSV) -> None:
    with open(outPath, "w", encoding="utf-8") as f:
        f.write("# Variant-spelling sets of the SAME word; ONE canonical "
                "spelling is kept, the others are dropped from the whole\n")
        f.write("# pipeline (src/spellingvariants.py). Canonical = highest "
                "Google Books Ngram 2010-2019 count\n")
        f.write("# (resources/LexiqueGoogleNgram.tsv). status: 'active' = "
                "enforced; 'review' = numbers cannot settle it, a human must\n")
        f.write("# set it to 'active' (possibly editing canonical) or 'veto' "
                "(genuinely distinct words -- row kept, nothing enforced).\n")
        f.write("# Generated by `python -m util.build_spelling_variants "
                "--emit`; REVIEW EVERY ROW BEFORE THE HOOKS RUN ON IT.\n")
        columns = ["setId", "canonical", "dropLemmes", "dropOrthos", "status",
                   "source", "ngramCanonical", "ngramDropped", "note"]
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(decisions)
    print(f"Wrote {outPath} ({len(decisions)} sets).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the spelling-variant decisions table "
                    "(resources/spellingVariants.tsv). Dry-run by default: "
                    "prints the review table.")
    parser.add_argument("--emit", action="store_true",
                        help="Also write the draft resources/spellingVariants.tsv.")
    args = parser.parse_args()

    ngramTable = Path(LEXIQUE_NGRAM_TSV)
    if not ngramTable.exists():
        sys.exit(f"{LEXIQUE_NGRAM_TSV} missing -- run "
                 f"`python -m util.ngram_data extract-lexique` first.")
    lexiqueRows = loadLexiqueRows()
    variantSets, rejectedSeeds = discoverVariantSets(lexiqueRows)
    if rejectedSeeds:
        print("WARNING: seed sets the discovery guards refused to connect:",
              file=sys.stderr)
        for seed in rejectedSeeds:
            print(f"    {sorted(seed)}", file=sys.stderr)
    ngramCounts = loadNgramCounts()
    decisions = resolveSets(variantSets, lexiqueRows, ngramCounts)
    printReviewTable(decisions)
    if args.emit:
        emitDecisions(decisions)


if __name__ == "__main__":
    main()
