"""
Hand-run diagnostic: do the pronunciations of the Synthetic verb rows agree with Wiktionary?

Every VER row of resources/LexiqueSynthetic.tsv (or --synthetic PATH, e.g. a regenerated file) is compared with the
pronunciation printed for the same lemma and tag on the French Wiktionary conjugation pages
(resources/wiktionaryVerbPronunciations.tsv, committed; util.fetch_wiktionary_conjugations) and, where those pages have no
such form, with GLÀFF (glaff/glaff-1.2.2.txt, an older Wiktionnaire-derived lexicon, gitignored; see TODO.md "Install
instructions"). Both are converted to the lexicon's phoneme alphabet (util/_pronunciation.py) and compared:

  exact        the same string
  equivalent   equal once schwas, open/close mid vowels (E/e, O/o, 9/2) and a doubled glide (ij.j / i.j) are ignored;
               the detail names the relaxation that was needed, so the e/E question stays visible
  differs      a real difference (the first differing symbols are shown)
  no reference neither source has the form

A row passes if it matches ANY reference variant of ANY of its tags. Nothing here changes the lexicon.

Run: python -m util.check_against_wiktionary [--synthetic PATH] [--glaff PATH|''] [--report PATH] [--examples N]
Writes synthetic_wiktionary_report.tsv (one line per row that is not exact).
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass

from util._pronunciation import compare
from util._verbreferences import GLAFF_PATH, WIKTIONARY_PATH, loadVerbReferences

SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
REPORT_PATH = "synthetic_wiktionary_report.tsv"

References = dict[tuple[str, str], set[str]]  # (lemme, tag) -> pronunciations in the lexicon alphabet


def rowTags(infover: str, genre: str, nombre: str, nonFinite: bool = False) -> list[str]:
    """The tags a Synthetic row stands for: its finite tags, and the participle form of its gender and number; with
    `nonFinite` (--non-finite) also its `inf` and `par:pre` tags (off by default: the report of the finite rows is unchanged)."""
    tags = [tag for tag in infover.split(";") if tag.count(":") == 2 or (nonFinite and tag in ("inf", "par:pre"))]
    if "par:pas" in infover and genre and nombre:
        tags.append(f"par:pas:{genre}{nombre}")
    return tags


@dataclass
class Result:
    ortho: str
    lemme: str
    infover: str
    phon: str
    source: str
    status: str
    detail: str
    references: list[str]


def checkRow(ortho: str, lemme: str, infover: str, genre: str, nombre: str, phon: str,
             wiktionary: References, glaff: References, nonFinite: bool = False) -> Result:
    tags = rowTags(infover, genre, nombre, nonFinite)
    for source, references in (("wiktionary", wiktionary), ("glaff", glaff)):
        found: set[str] = set()
        for tag in tags:
            found |= references.get((lemme, tag), set())
        if found:
            status, detail = compare(phon, found)
            return Result(ortho, lemme, infover, phon, source, status, detail, sorted(found))
    return Result(ortho, lemme, infover, phon, "none", "no reference", "", [])


def tagFamily(infover: str) -> str:
    return "par:pas" if "par:pas" in infover else ":".join(infover.split(";")[0].split(":")[:2])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--synthetic", default=SYNTHETIC_PATH)
    parser.add_argument("--wiktionary", default=WIKTIONARY_PATH)
    parser.add_argument("--glaff", default=GLAFF_PATH, help="GLÀFF file; '' to use Wiktionary only")
    parser.add_argument("--report", default=REPORT_PATH)
    parser.add_argument("--non-finite", action="store_true", help="also check the inf and par:pre rows (GLÀFF only)")
    parser.add_argument("--examples", type=int, default=5, help="examples shown per kind of difference")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    references = loadVerbReferences(args.wiktionary, args.glaff)
    wiktionary = references.lemmaTagIndex("wiktionary")
    glaff = references.lemmaTagIndex("glaff")
    print(f"references: Wiktionary {len(wiktionary)} (lemma, tag) pairs, GLÀFF {len(glaff)}", file=sys.stderr)

    results: list[Result] = []
    with open(args.synthetic, encoding="utf-8", newline="") as f:
        for row in csv.DictReader((line.rstrip("\r\n") for line in f), delimiter="\t", quoting=csv.QUOTE_NONE):
            if row["cgram"] == "VER":
                results.append(checkRow(row["ortho"], row["lemme"], row["infover"], row["genre"], row["nombre"],
                                        row["phon"], wiktionary, glaff, args.non_finite))

    byStatus = Counter((r.source, r.status) for r in results)
    total = len(results)
    print(f"\n{total} Synthetic VER rows ({args.synthetic})")
    for (source, status), count in sorted(byStatus.items()):
        print(f"  {source:11} {status:13} {count:7}  {count / total:6.1%}")
    compared = [r for r in results if r.status != "no reference"]
    ok = sum(1 for r in compared if r.status in ("exact", "equivalent"))
    exact = sum(1 for r in compared if r.status == "exact")
    print(f"\nwith a reference: {len(compared)}; exact {exact} ({exact / len(compared):.1%}), "
          f"exact or equivalent {ok} ({ok / len(compared):.1%}), differs {len(compared) - ok}")

    print("\nby tense (rows with a reference):   exact  equivalent  differs")
    families: dict[str, Counter[str]] = defaultdict(Counter)
    for r in compared:
        families[tagFamily(r.infover)][r.status] += 1
    for family, counts in sorted(families.items(), key=lambda x: -sum(x[1].values())):
        print(f"  {family:8} {sum(counts.values()):6}   {counts['exact']:6} {counts['equivalent']:8} {counts['differs']:8}")

    for status in ("equivalent", "differs"):
        details = Counter(r.detail for r in compared if r.status == status)
        print(f"\n{status}: kinds" + (" (relaxation needed)" if status == "equivalent" else " (first differing symbols)"))
        shown = 0
        for detail, count in details.most_common(12 if status == "equivalent" else 0):
            print(f"  {count:6}  {detail}")
        if status == "differs":
            kinds: dict[str, list[Result]] = defaultdict(list)
            for r in compared:
                if r.status == "differs":
                    kinds[r.detail].append(r)
            for detail, items in sorted(kinds.items(), key=lambda x: -len(x[1]))[:args.examples * 4]:
                if shown >= args.examples * 4:
                    break
                shown += 1
                sample = items[0]
                print(f"  {len(items):5}  {detail:28} e.g. {sample.ortho} ({sample.lemme} {sample.infover}) ours {sample.phon} vs {sample.references[:3]}")

    with open(args.report, "w", encoding="utf-8", newline="") as out:
        out.write("ortho\tlemme\tinfover\tours\tsource\tstatus\tdetail\treferences\n")
        for r in results:
            if r.status != "exact":
                out.write("\t".join([r.ortho, r.lemme, r.infover, r.phon, r.source, r.status, r.detail, "|".join(r.references)]) + "\n")
    print(f"\nreport written to {args.report}", file=sys.stderr)


if __name__ == "__main__":
    main()
