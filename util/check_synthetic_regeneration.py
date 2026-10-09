"""
Hand-run diagnostic: is resources/LexiqueSynthetic.tsv a pure function of its inputs?

Copies the repo (without .git, env, scratch, steno-trainer, node_modules, googlebooks-fre-1grams)
to a temp dir, empties the Synthetic lexicon to its header, deletes the pickles, runs
`python -m util.build_synthetic_lexicon` there (twice by default, from scratch each time),
compares the two regenerated files (they must be byte-identical) and writes
`synthetic_regen_report.tsv`: one line per differing key against the committed file,
`only-committed | only-regenerated | column-diff:<cols>`, with per-lemma counts on stderr.

Run: python -m util.check_synthetic_regeneration [--runs N] [--keep]   (about 6 min per run)
Reports; fixes nothing.
"""
import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from collections import Counter

SYNTHETIC = "resources/LexiqueSynthetic.tsv"
REPORT = "synthetic_regen_report.tsv"
EXCLUDES = (".git", "env", "scratch", "steno-trainer", "node_modules", "googlebooks-fre-1grams", "__pycache__", "tmp", "sorties")
KEY = ("ortho", "lemme", "cgram", "genre", "nombre")


def copyRepo(root: str, dest: str) -> None:
    def ignore(directory: str, names: list[str]) -> list[str]:
        skipped = [n for n in names if directory == root and n in EXCLUDES]
        skipped += [n for n in names if n.endswith(".pickle") or n == "__pycache__"]
        return skipped
    shutil.copytree(root, dest, ignore=ignore, symlinks=True)


def readTable(path: str) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = list(reader.fieldnames or [])
        return header, list(reader)


def md5(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def regenerate(root: str, workDir: str, forcedRules: Sequence[str] = ()) -> str:
    copyRepo(root, workDir)
    target = os.path.join(workDir, SYNTHETIC)
    with open(os.path.join(root, SYNTHETIC), encoding="utf-8") as f:
        header = f.readline()
    with open(target, "w", encoding="utf-8") as f:
        f.write(header)
    python = os.path.join(root, "env", "bin", "python")
    if not os.path.exists(python):
        python = sys.executable
    subprocess.run([python, "-m", "util.build_synthetic_lexicon",
                    *(a for spec in forcedRules for a in ("--force-rule", spec))], cwd=workDir, check=True)
    return target


def keyOf(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row[k] for k in KEY)


def writeReport(committedPath: str, regeneratedPath: str, reportPath: str) -> None:
    header, committed = readTable(committedPath)
    _, regenerated = readTable(regeneratedPath)
    byKeyC: dict[tuple[str, ...], list[dict[str, str]]] = {}
    byKeyR: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in committed:
        byKeyC.setdefault(keyOf(row), []).append(row)
    for row in regenerated:
        byKeyR.setdefault(keyOf(row), []).append(row)
    perLemma: Counter[tuple[str, str]] = Counter()
    kinds: Counter[str] = Counter()
    with open(reportPath, "w", encoding="utf-8") as out:
        out.write("kind\t" + "\t".join(KEY) + "\tcgram_detail\n")
        for key in sorted(set(byKeyC) | set(byKeyR)):
            c, r = byKeyC.get(key), byKeyR.get(key)
            if c is None or r is None:
                kind = "only-committed" if r is None else "only-regenerated"
                detail = ""
            else:
                cols = [h for h in header if [x[h] for x in c] != [x[h] for x in r]]
                if not cols:
                    continue
                kind = "column-diff:" + ",".join(cols)
                detail = "; ".join(f"{h}: {c[0][h]} -> {r[0][h]}" for h in cols)
            kinds[kind.split(":")[0]] += 1
            perLemma[(kind.split(":")[0], key[1])] += 1
            out.write(kind + "\t" + "\t".join(key) + "\t" + detail + "\n")
    print(f"committed {len(committed)} rows, regenerated {len(regenerated)} rows", file=sys.stderr)
    for kind, n in kinds.items():
        print(f"{kind}: {n} keys", file=sys.stderr)
        top = [(l, n2) for (k, l), n2 in perLemma.most_common() if k == kind][:15]
        print("  top lemmas: " + ", ".join(f"{l} {n2}" for l, n2 in top), file=sys.stderr)
    print(f"report written to {reportPath}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--force-rule", action="append", default=[], metavar="NAME[=PARAM]",
                        help="passed to util.build_synthetic_lexicon (measuring a mechanism without a decision)")
    parser.add_argument("--keep", action="store_true", help="keep the temp dirs")
    args = parser.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    produced: list[str] = []
    temps: list[str] = []
    for run in range(args.runs):
        temp = tempfile.mkdtemp(prefix=f"synthregen{run}_")
        temps.append(temp)
        produced.append(regenerate(root, os.path.join(temp, "repo"), args.force_rule))
    sums = [md5(p) for p in produced]
    print("regenerated md5s: " + " ".join(sums), file=sys.stderr)
    if len(set(sums)) > 1:
        print("NOT DETERMINISTIC: the regenerated files differ between runs", file=sys.stderr)
    writeReport(SYNTHETIC, produced[0], REPORT)
    if args.keep:
        print("kept: " + " ".join(produced), file=sys.stderr)
    else:
        for temp in temps:
            shutil.rmtree(temp, ignore_errors=True)
    if len(set(sums)) > 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
