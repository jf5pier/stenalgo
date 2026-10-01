#!/bin/env python
#
# Google Books Ngram French corpus access for the pipeline: download of the raw
# 1-gram files, extraction of the two committed tables the project keeps, and a
# thin spot-check client for the public Ngram Viewer API.
#
# Data source: Google Books Ngram Version 3 (snapshot 20200217, books through
# 2019) -- the most recent raw export Google has published. The French 1-grams
# are six gzipped shards (~5 GB total) anonymously downloadable from Google's
# own storage:
#   https://storage.googleapis.com/books/ngrams/books/20200217/fre/1-0000<i>-of-00006.gz
#   (plus totalcounts-1, per-year corpus totals)
# V3 line format (one line per token, all years packed on the line):
#   <word>_<POS>\t<year>,<match_count>,<page_count> <year>,... ...
# The parser strips the _POS suffix and folds case, so "beluga_NOUN" and
# "Beluga_NOUN" both add to the row of "beluga".
#
# Fallback corpus: Version 2 (snapshot 20120701, books through 2009) mirrored on
# the Internet Archive (item googlebooks-20120701-1grams), whose French 1-grams
# are 26+ letter files with one line per token per year:
#   <word>\t<year>\t<match_count>\t<page_count>
# Use it only if the v3 data proves unusable (its casing/accent handling could
# only be checked on a fully downloaded shard; gzip streams cannot be sampled
# mid-file). Both formats parse into the same (word, [(year, match_count)...]).
#
# The two committed tables this module produces:
#   resources/LexiqueGoogleNgram.tsv -- Ngram counts (all-time + three decade
#     windows) for every ortho/lemme of LexiqueMixte.tsv and
#     LexiqueSynthetic.tsv. The canonical frequency arbiter, e.g. for the
#     spelling-variant canonical-spelling decision (util/build_spelling_variants.py)
#     and future tie-breaks; downstream consumers never re-download anything.
#   resources/LexiqueGoogleNgramAdditions.tsv -- medium/high-frequency French
#     words ABSENT from both lexicons (and not near-variant spellings of a
#     lexicon word), sorted by recent count: candidate data for a later
#     neologism patch of the lexicon (separate TODO).
#
# Retention policy: the raw shard files under googlebooks-fre-1grams/ (gitignored,
# morphalou/-style) are KEPT until both tables above are final and committed.
# Nothing here ever deletes them automatically -- `purge` is a manual, explicit
# subcommand for after that.
#
# The Viewer API subcommand (`query`) is a convenience only: the viewer's index
# omits every word below its occurrence threshold (verified live: trimballer and
# évènementiel return empty results), i.e. exactly the rare variants the tables
# above must arbitrate. It must never be the arbiter.
import argparse
import csv
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable, Iterator, Sequence

V3_BASE = "https://storage.googleapis.com/books/ngrams/books/20200217/fre"
V3_SHARDS = tuple(f"{V3_BASE}/1-{i:05d}-of-00006.gz" for i in range(6))
CORPUS_ID_V3 = "googlebooks-fre-20200217"

V2_BASE = "https://archive.org/download/googlebooks-20120701-1grams/french"
V2_STEMS = "0123456789abcdefghijklmnopqrstuvwxyz"
V2_SHARDS = tuple(f"{V2_BASE}/googlebooks-fre-all-1gram-20120701-{stem}.gz"
                  for stem in V2_STEMS)
CORPUS_ID_V2 = "googlebooks-fre-20120701"

RAW_DIR_DEFAULT = "googlebooks-fre-1grams"

LEXIQUE_PATHS = ("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv")
# The 1990-reform spellings must be added on top of the lexicons' own words:
# S1's reform rewrites collapse old->new spellings when writing
# LexiqueMixte.tsv (it contains only évènement, never événement), so without
# this the pre-reform spelling's Ngram evidence would be invisible to the
# variant-canonical decision.
REFORM_TSV = "resources/reform1990.tsv"
LEXIQUE_NGRAM_PATH = "resources/LexiqueGoogleNgram.tsv"
LEXIQUE_NGRAM_ADDITIONS_PATH = "resources/LexiqueGoogleNgramAdditions.tsv"

# (column name, first year, last year) of each decade window kept in
# LexiqueGoogleNgram.tsv, alongside the all-time total.
WINDOWS = (
    ("count1990_1999", 1990, 1999),
    ("count2000_2009", 2000, 2009),
    ("count2010_2019", 2010, 2019),
)

USER_AGENT = "stenalgo-ngram-tool/1.0 (https://github.com/jf5pier/stenalgo)"
DOWNLOAD_CHUNK = 1 << 20


# ═══════════════════════════════════════════════════════════════════════════
# Parsing
# ═══════════════════════════════════════════════════════════════════════════

def stripPosSuffix(token: str) -> str:
    """'beluga_NOUN' -> 'beluga'. Only strips a trailing '_<ASCII uppercase>'
    tag; a French word never contains that shape, so no real token is damaged."""
    cut = token.rfind("_")
    if cut > 0 and token[cut + 1:].isascii() and token[cut + 1:].isupper():
        return token[:cut]
    return token


def parseV3Line(line: str) -> tuple[str, list[tuple[int, int]]] | None:
    """v3 packed line: 'word_POS\\t year,count,page year,count,page ...'.
    Returns (word, [(year, match_count), ...]) or None for junk lines."""
    token, _, rest = line.partition("\t")
    if not rest:
        return None
    entries: list[tuple[int, int]] = []
    for packed in rest.split():
        yearStr, _, counts = packed.partition(",")
        if not counts:
            continue
        matchStr = counts.partition(",")[0]
        try:
            entries.append((int(yearStr), int(matchStr)))
        except ValueError:
            continue
    if not entries:
        return None
    return stripPosSuffix(token), entries


def parseV2Line(line: str) -> tuple[str, list[tuple[int, int]]] | None:
    """v2 per-year line: 'word\\tyear\\tmatch_count\\tpage_count'.
    Returns (word, [(year, match_count)]) or None for junk lines."""
    columns = line.split("\t")
    if len(columns) < 3:
        return None
    try:
        return columns[0], [(int(columns[1]), int(columns[2]))]
    except ValueError:
        return None


def iterShardLines(path: Path) -> Iterator[str]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as shard:
        yield from shard


# ═══════════════════════════════════════════════════════════════════════════
# Download (resumable; nothing here ever deletes a downloaded file)
# ═══════════════════════════════════════════════════════════════════════════

def remoteSize(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return int(response.headers["Content-Length"])


def downloadFile(url: str, destination: Path, force: bool = False) -> bool:
    """Downloads url to destination, resuming a partial file if one exists.
    Returns True if a (complete) file is now on disk, False if it was already
    complete before the call."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    have = destination.stat().st_size if destination.exists() else 0
    expected = remoteSize(url)
    if have == expected and not force:
        return False
    if have > expected or force:
        destination.unlink()
        have = 0
    if have < expected:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT,
                          "Range": f"bytes={have}-"})
        with urllib.request.urlopen(request, timeout=120) as response, \
                open(destination, "ab") as out:
            while True:
                chunk = response.read(DOWNLOAD_CHUNK)
                if not chunk:
                    break
                out.write(chunk)
    finalSize = destination.stat().st_size
    if finalSize != expected:
        raise IOError(f"{destination.name}: expected {expected} bytes, "
                      f"got {finalSize} -- rerun to resume")
    return True


def downloadShards(rawDir: str = RAW_DIR_DEFAULT, corpus: str = "v3") -> None:
    shards = V3_SHARDS if corpus == "v3" else V2_SHARDS
    directory = Path(rawDir)
    for i, url in enumerate(shards, start=1):
        destination = directory / url.rsplit("/", 1)[-1]
        sizeMB = remoteSize(url) / (1 << 20)
        if downloadFile(url, destination):
            print(f"[{i}/{len(shards)}] downloaded {destination.name} "
                  f"({sizeMB:.0f} MB)")
        else:
            print(f"[{i}/{len(shards)}] already complete: {destination.name}")


# ═══════════════════════════════════════════════════════════════════════════
# Extraction
# ═══════════════════════════════════════════════════════════════════════════

def loadLexiconWords(lexiquePaths: Sequence[str] = LEXIQUE_PATHS,
                     reformTsv: str = REFORM_TSV) -> set[str]:
    """Every ortho and lemme of the two lexicons, lowercased, plus both
    spellings of every reform1990.tsv pair -- the match set for
    LexiqueGoogleNgram.tsv (see REFORM_TSV above for why the reform
    spellings are needed on top)."""
    words: set[str] = set()
    for path in lexiquePaths:
        table = Path(path)
        if not table.exists():
            continue
        with open(table, newline="", encoding="utf-8") as f:
            header = f.readline().rstrip("\r\n").split("\t")
            orthoIdx, lemmeIdx = header.index("ortho"), header.index("lemme")
            for line in f:
                columns = line.rstrip("\r\n").split("\t")
                words.add(columns[orthoIdx].lower())
                words.add(columns[lemmeIdx].lower())
    reformTable = Path(reformTsv)
    if reformTable.exists():
        with open(reformTable, newline="", encoding="utf-8") as f:
            rows = [line.rstrip("\n") for line in f
                    if not line.startswith("#")]
        reader = csv.DictReader(rows, delimiter="\t")
        for row in reader:
            for spelling in (row["oldSpelling"], row["newSpelling"]):
                if spelling:
                    words.add(spelling.lower())
    return words


def windowSums(entries: Iterable[tuple[int, int]]) -> tuple[int, ...]:
    """(countAll, count per WINDOWS decade) for one token's (year, count) list."""
    total = 0
    decades = [0] * len(WINDOWS)
    for year, count in entries:
        total += count
        for i, (_name, first, last) in enumerate(WINDOWS):
            if first <= year <= last:
                decades[i] += count
    return (total, *decades)


# Worker-side globals for the process pool (fork-inherited).
_words: set[str] = set()
_excluded: set[str] = set()
_minRecent: int = 0


def _initWorker(words: set[str], excluded: set[str], minRecent: int) -> None:
    global _words, _excluded, _minRecent
    _words, _excluded, _minRecent = words, excluded, minRecent


def _scanShard(shardPath: str) -> dict[str, tuple[int, ...]]:
    """One shard's contribution: counts for words in _words, plus not-in-lexicon
    words whose latest-decade count reaches _minRecent (the neologism
    candidates), skipping anything in _excluded."""
    global _words, _excluded, _minRecent
    recentFirst, recentLast = WINDOWS[-1][1], WINDOWS[-1][2]
    found: dict[str, tuple[int, ...]] = defaultdict(
        lambda: (0, *(0 for _ in WINDOWS)))
    with gzip.open(shardPath, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            parsed = parseV3Line(line)
            if parsed is None:
                continue
            word, entries = parsed
            word = word.lower()
            if word in _excluded:
                continue
            if word in _words:
                pass  # always kept
            elif _minRecent > 0:
                recent = sum(count for year, count in entries
                             if recentFirst <= year <= recentLast)
                if recent < _minRecent:
                    continue
            else:
                continue
            sums = windowSums(entries)
            current = found[word]
            found[word] = tuple(a + b for a, b in zip(current, sums))
    return dict(found)


def scanShards(shardPaths: Sequence[Path], words: set[str],
               excluded: set[str] | None = None, minRecent: int = 0,
               jobs: int = 1) -> dict[str, tuple[int, ...]]:
    """Streams every shard once and merges per-word (countAll, decade...)
    tuples. jobs > 1 fans the shards out over processes (each shard is an
    independent gzip stream; the word set rides along by fork)."""
    excluded = excluded or set()
    merged: dict[str, tuple[int, ...]] = defaultdict(
        lambda: (0, *(0 for _ in WINDOWS)))
    shardList = [str(p) for p in shardPaths]
    if jobs > 1 and len(shardList) > 1:
        with ProcessPoolExecutor(
                max_workers=min(jobs, len(shardList)),
                initializer=_initWorker,
                initargs=(words, excluded, minRecent)) as pool:
            for partial in pool.map(_scanShard, shardList):
                for word, sums in partial.items():
                    current = merged[word]
                    merged[word] = tuple(a + b for a, b in zip(current, sums))
    else:
        _initWorker(words, excluded, minRecent)
        for shard in shardList:
            for word, sums in _scanShard(shard).items():
                current = merged[word]
                merged[word] = tuple(a + b for a, b in zip(current, sums))
    return dict(merged)


def writeLexiqueGoogleNgram(counts: dict[str, tuple[int, ...]],
                            corpusId: str, outPath: str = LEXIQUE_NGRAM_PATH
                            ) -> None:
    windowColumns = "\t".join(name for name, _first, _last in WINDOWS)
    with open(outPath, "w", encoding="utf-8") as f:
        f.write("# Google Books Ngram counts for every ortho/lemme of "
                "LexiqueMixte.tsv and LexiqueSynthetic.tsv.\n")
        f.write("# Generated by `python -m util.ngram_data extract-lexique`; "
                f"corpus {corpusId} (case-folded, POS tags stripped,\n"
                "# all case variants of a word summed into one row).\n")
        f.write(f"word\tcountAll\t{windowColumns}\tcorpusId\n")
        for word in sorted(counts):
            f.write(word + "\t" + "\t".join(str(c) for c in counts[word])
                    + f"\t{corpusId}\n")


def extractLexiqueGoogleNgram(rawDir: str = RAW_DIR_DEFAULT,
                              corpus: str = "v3", jobs: int = 1,
                              outPath: str = LEXIQUE_NGRAM_PATH) -> int:
    words = loadLexiconWords()
    shards = sorted(Path(rawDir).glob("*.gz"))
    if not shards:
        sys.exit(f"No shard files in {rawDir}/ -- run "
                 f"`python -m util.ngram_data download` first.")
    counts = scanShards(shards, words, jobs=jobs)
    corpusId = CORPUS_ID_V3 if corpus == "v3" else CORPUS_ID_V2
    writeLexiqueGoogleNgram(counts, corpusId, outPath)
    print(f"{outPath}: {len(counts)} of {len(words)} lexicon words found "
          f"in {len(shards)} shards.")
    return len(counts)


def extractAdditions(rawDir: str = RAW_DIR_DEFAULT, corpus: str = "v3",
                     threshold: int = 5000, jobs: int = 1,
                     outPath: str = LEXIQUE_NGRAM_ADDITIONS_PATH) -> int:
    """Neologism candidates: words absent from both lexicons (and not close
    variant spellings of a lexicon word) whose 2010-2019 count clears
    `threshold`. Data for a separate follow-up TODO -- no lexicon is patched
    here. The near-variant filter runs on the (few) above-threshold
    candidates after the scan, not on every corpus token."""
    from util.build_spelling_variants import isNearVariantSpelling
    words = loadLexiconWords()
    shards = sorted(Path(rawDir).glob("*.gz"))
    if not shards:
        sys.exit(f"No shard files in {rawDir}/ -- run "
                 f"`python -m util.ngram_data download` first.")
    counts = scanShards(shards, set(), minRecent=threshold, jobs=jobs)
    recentIdx = len(WINDOWS)
    corpusId = CORPUS_ID_V3 if corpus == "v3" else CORPUS_ID_V2
    ranked = sorted(
        ((word, sums) for word, sums in counts.items()
         if word not in words and not isNearVariantSpelling(word, words)),
        key=lambda item: -item[1][recentIdx])
    with open(outPath, "w", encoding="utf-8") as f:
        f.write("# Google Books Ngram words ABSENT from LexiqueMixte.tsv and "
                "LexiqueSynthetic.tsv (and not near-variant spellings of a\n")
        f.write("# lexicon word) whose 2010-2019 count clears the threshold -- "
                "candidate neologisms for a future lexicon patch.\n")
        f.write("# Generated by `python -m util.ngram_data extract-additions`; "
                f"corpus {corpusId} (case-folded, POS tags stripped).\n")
        f.write("word\tcount2010_2019\tcountAll\tcorpusId\n")
        for word, sums in ranked:
            f.write(f"{word}\t{sums[recentIdx]}\t{sums[0]}\t{corpusId}\n")
    print(f"{outPath}: {len(ranked)} candidates at threshold >= {threshold}.")
    return len(ranked)


# ═══════════════════════════════════════════════════════════════════════════
# Ad-hoc scan of retained shards, and the Viewer API spot-check client
# ═══════════════════════════════════════════════════════════════════════════

def scanWords(wordsFile: str, rawDir: str = RAW_DIR_DEFAULT, jobs: int = 1
              ) -> dict[str, tuple[int, ...]]:
    with open(wordsFile, encoding="utf-8") as f:
        words = {line.strip().lower() for line in f if line.strip()}
    shards = sorted(Path(rawDir).glob("*.gz"))
    if not shards:
        sys.exit(f"No shard files in {rawDir}/ -- run "
                 f"`python -m util.ngram_data download` first.")
    return scanShards(shards, words, jobs=jobs)


VIEWER_JSON_URL = "https://books.google.com/ngrams/json"
# The viewer URL-caps one request at this many terms; batching keeps us well
# under the rate limit instead of firing one request per word.
VIEWER_BATCH_TERMS = 8
VIEWER_THROTTLE_SECONDS = 1.0


def _viewerFetch(batch: Sequence[str], corpus: str, yearStart: int,
                 yearEnd: int) -> list[dict]:
    """One batched viewer request; returns the parsed JSON rows."""
    # Percent-encode: accented terms make urllib's ascii URL encoding raise.
    url = (f"{VIEWER_JSON_URL}?content="
           f"{urllib.parse.quote(','.join(batch))}"
           f"&corpus={corpus}&year_start={yearStart}"
           f"&year_end={yearEnd}&smoothing=0")
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:  # noqa: BLE001 - retry then give up loudly
            if attempt == 2:
                raise
            time.sleep(5.0)
    return []  # unreachable; keeps mypy happy


def viewerShares(terms: Sequence[str], corpus: str = "30",
                 yearStart: int = 2015, yearEnd: int = 2019) -> dict[str, float]:
    """Plain NGRAM rows only: ngram -> mean relative share over the window
    (wildcard EXPANSION rows are ignored). Terms below the viewer's occurrence
    threshold simply do not come back. The corpus must be the numeric id
    ("30" = French): string names are silently ignored, falling back to
    English."""
    out: dict[str, float] = {}
    for start in range(0, len(terms), VIEWER_BATCH_TERMS):
        batch = terms[start:start + VIEWER_BATCH_TERMS]
        for row in _viewerFetch(batch, corpus, yearStart, yearEnd):
            if row.get("type") != "NGRAM":
                continue
            timeseries = row["timeseries"]
            out[row["ngram"]] = (sum(timeseries) / len(timeseries))
        if start + VIEWER_BATCH_TERMS < len(terms):
            time.sleep(VIEWER_THROTTLE_SECONDS)
    return out


def queryViewer(terms: Sequence[str], corpus: str = "30",
                yearStart: int = 2015, yearEnd: int = 2019) -> None:
    """Spot-check convenience ONLY. The viewer's index omits every word below
    its occurrence threshold (trimballer and évènementiel return empty), so an
    empty answer here means nothing; LexiqueGoogleNgram.tsv is the arbiter.
    The corpus must be the numeric id ("30" = French): string names like
    "fre"/"fre_2019" are silently ignored and fall back to English."""
    for start in range(0, len(terms), VIEWER_BATCH_TERMS):
        batch = terms[start:start + VIEWER_BATCH_TERMS]
        for row in _viewerFetch(batch, corpus, yearStart, yearEnd):
            print(json.dumps(row, ensure_ascii=False))
        if start + VIEWER_BATCH_TERMS < len(terms):
            time.sleep(VIEWER_THROTTLE_SECONDS)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Google Books Ngram French corpus: download the raw "
                    "1-gram shards and extract the committed frequency tables.")
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser(
        "download", help="Download the raw shards into the gitignored data "
                         "dir (resumable; files are kept until manually purged).")
    download.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    download.add_argument("--corpus", choices=("v3", "v2"), default="v3",
                          help="v3: 20200217 snapshot from Google (default); "
                               "v2: 20120701 snapshot from the Internet Archive.")

    extractLexique = sub.add_parser(
        "extract-lexique", help="Write resources/LexiqueGoogleNgram.tsv: Ngram "
                                "counts for every word of the two lexicons.")
    extractLexique.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    extractLexique.add_argument("--corpus", choices=("v3", "v2"), default="v3")
    extractLexique.add_argument("--jobs", type=int, default=1)
    extractLexique.add_argument("--out", default=LEXIQUE_NGRAM_PATH)

    extractAdds = sub.add_parser(
        "extract-additions", help="Write resources/LexiqueGoogleNgramAdditions."
                                  "tsv: neologism candidates missing from the lexicons.")
    extractAdds.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    extractAdds.add_argument("--corpus", choices=("v3", "v2"), default="v3")
    extractAdds.add_argument("--threshold", type=int, default=5000,
                             help="Minimum 2010-2019 count to be kept.")
    extractAdds.add_argument("--jobs", type=int, default=1)
    extractAdds.add_argument("--out", default=LEXIQUE_NGRAM_ADDITIONS_PATH)

    scan = sub.add_parser(
        "scan", help="Ad-hoc: counts for the words of a file (one per line) "
                     "from the retained shards.")
    scan.add_argument("words_file")
    scan.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    scan.add_argument("--jobs", type=int, default=1)

    query = sub.add_parser(
        "query", help="Spot-check terms against the public Ngram Viewer API "
                      "(batched, throttled). NOT an arbiter: the viewer omits "
                      "rare words entirely.")
    query.add_argument("terms", help="Comma-separated terms.")
    query.add_argument("--corpus", default="30",
                       help="Numeric viewer corpus id (30 = French); string "
                            "names are silently ignored by the endpoint.")

    purge = sub.add_parser(
        "purge", help="Delete the raw shard dir. Manual on purpose: only after "
                      "LexiqueGoogleNgram.tsv and LexiqueGoogleNgramAdditions."
                      "tsv are final and committed.")
    purge.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    purge.add_argument("--yes", action="store_true",
                       help="Actually delete (without it: prints what would go).")

    args = parser.parse_args()
    if args.command == "download":
        downloadShards(args.raw_dir, args.corpus)
    elif args.command == "extract-lexique":
        extractLexiqueGoogleNgram(args.raw_dir, args.corpus, args.jobs, args.out)
    elif args.command == "extract-additions":
        extractAdditions(args.raw_dir, args.corpus, args.threshold, args.jobs,
                         args.out)
    elif args.command == "scan":
        for word, sums in sorted(scanWords(args.words_file, args.raw_dir,
                                           args.jobs).items()):
            print(word, sums)
    elif args.command == "query":
        queryViewer(args.terms.split(","), corpus=args.corpus)
    elif args.command == "purge":
        directory = Path(args.raw_dir)
        if not directory.exists():
            print(f"{args.raw_dir}/ does not exist.")
            return
        targets = list(directory.glob("*.gz"))
        if not args.yes:
            for target in targets:
                print(f"would delete {target} "
                      f"({target.stat().st_size / (1 << 20):.0f} MB)")
            print("Rerun with --yes to delete.")
            return
        for target in targets:
            target.unlink()
        print(f"Deleted {len(targets)} shard files from {args.raw_dir}/.")


if __name__ == "__main__":
    main()
