"""
Fetches the French Wiktionary conjugation pages of the lexicon's verbs once and keeps their pronunciations in a
committed file, so that checks against Wiktionary (and a regeneration that wants them) never refetch:

  resources/wiktionaryVerbPronunciations.tsv          lemme, ortho, tags (';'-joined, sorted), ipa
  resources/wiktionaryVerbPronunciations.missing.txt  lemmas whose page does not exist or has no table (not retried)
  resources/wiktionaryVerbPronunciations.NOTICE.md    attribution (CC BY-SA 4.0)

Only what the lexicon lacks is kept: a lemma is fetched when its Verbiste template has a finite slot or a participle form
that LexiqueMixte.tsv does not attest, and only the rows (and tags) of those missing forms are stored -- that is all a check
of the generated Synthetic rows needs (the Synthetic file only fills what Mixte lacks). Verbs without a trusted template are skipped.

Resumable: a lemma already in either file is skipped. One request at a time, `--delay` seconds apart (default 0.25),
Retry-After honoured on 429/503. The page is the REST HTML of Conjugaison:français/<lemme>; util/_wiktionaryconj.py parses it.

Run: python -m util.fetch_wiktionary_conjugations [--limit N] [--delay S] [--lemmas a,b,c]   (about 50 minutes for all 6,300 verbs)
"""
import argparse
import csv
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

from src.verbparadigm import (
    allFiniteSlots,
    getTrustedTemplate,
    loadVerbisteTemplates,
    loadVerbModelExceptions,
    parseConjugationTemplates,
)
from util._wiktionaryconj import parseConjugationPage

MIXTE_PATH = "resources/LexiqueMixte.tsv"
OUTPUT_PATH = "resources/wiktionaryVerbPronunciations.tsv"
MISSING_PATH = "resources/wiktionaryVerbPronunciations.missing.txt"
HEADER = "lemme\tortho\ttags\tipa"
USER_AGENT = "stenalgo-lexicon-validation/1.0 (https://github.com/jf5pier/stenalgo-plover)"
URL = "https://fr.wiktionary.org/api/rest_v1/page/html/"
FLUSH_EVERY = 200

Entries = dict[tuple[str, str, str], set[str]]  # (lemme, ortho, ipa) -> tags


PARTICIPLE_TAGS = tuple(f"par:pas:{gender}{number}" for gender in "mf" for number in "sp")


def attestedTags(mixtePath: str = MIXTE_PATH) -> dict[str, set[str]]:
    """lemma -> the finite tags (ind:pre:1s ...) and past-participle tags (par:pas:ms ...) LexiqueMixte.tsv attests."""
    attested: dict[str, set[str]] = defaultdict(set)
    with open(mixtePath, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["cgram"] != "VER" or not row["lemme"] or row["lemme"].startswith("#"):
                continue
            tags = attested[row["lemme"]]
            for tag in row["infover"].split(";"):
                if tag.count(":") == 2:
                    tags.add(tag)
            if "par:pas" in row["infover"] and row["genre"] and row["nombre"]:
                tags.add(f"par:pas:{row['genre']}{row['nombre']}")
    return attested


def missingTagsByLemma(mixtePath: str = MIXTE_PATH) -> dict[str, set[str]]:
    """lemma -> the tags of its Verbiste template (finite slots + the four past-participle forms) that Mixte lacks.
    Lemmas without a trusted template, or with nothing missing, are absent."""
    templates = loadVerbisteTemplates("resources/verbiste/verbs-fr.xml")
    exceptions = loadVerbModelExceptions("resources/verbModelExceptions.tsv")
    conjugations = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
    result: dict[str, set[str]] = {}
    for lemma, attested in sorted(attestedTags(mixtePath).items()):
        name = getTrustedTemplate(lemma, templates, exceptions)
        if name is None or name not in conjugations:
            continue
        expected = {f"{code}:{person}" for code, person in allFiniteSlots(conjugations[name])} | set(PARTICIPLE_TAGS)
        missing = expected - attested
        if missing:
            result[lemma] = missing
    return result


def readOutput(path: str = OUTPUT_PATH) -> Entries:
    entries: Entries = defaultdict(set)
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            assert f.readline().rstrip("\n") == HEADER, f"unexpected header in {path}"
            for line in f:
                lemme, ortho, tags, ipa = line.rstrip("\n").split("\t")
                entries[(lemme, ortho, ipa)].update(tags.split(";"))
    return entries


def writeOutput(entries: Entries, path: str = OUTPUT_PATH) -> int:
    lines = sorted(f"{lemme}\t{ortho}\t{';'.join(sorted(tags))}\t{ipa}" for (lemme, ortho, ipa), tags in entries.items())
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(HEADER + "\n" + "".join(line + "\n" for line in lines))
    return len(lines)


def readMissing(path: str = MISSING_PATH) -> set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def writeMissing(missing: set[str], path: str = MISSING_PATH) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("".join(lemma + "\n" for lemma in sorted(missing)))


def addPage(entries: Entries, lemme: str, parsed: list[tuple[str, str, str]], keep: set[str] | None = None) -> int:
    """Add a page's forms; with `keep`, only the tags in it (the lemma's missing tags). Returns the rows added."""
    added = 0
    for tag, ortho, ipa in parsed:
        if keep is None or tag in keep:
            entries.setdefault((lemme, ortho, ipa), set()).add(tag)
            added += 1
    return added


def pruneToMissing(entries: Entries, missing: dict[str, set[str]]) -> Entries:
    """The entries restricted to each lemma's missing tags (rows left without a tag are dropped)."""
    pruned: Entries = {}
    for (lemme, ortho, ipa), tags in entries.items():
        kept = tags & missing.get(lemme, set())
        if kept:
            pruned[(lemme, ortho, ipa)] = kept
    return pruned


def fetchPage(lemme: str) -> str | None:
    """The page HTML, None when it does not exist; raises after repeated failures."""
    url = URL + urllib.parse.quote(f"Conjugaison:français/{lemme}", safe="")
    for attempt in range(6):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return str(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            wait = float(error.headers.get("Retry-After", 0) or 0) if error.code in (429, 503) else 0.0
            time.sleep(max(wait, 2.0 ** attempt))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2.0 ** attempt)
    raise RuntimeError(f"giving up on {lemme!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=0, help="fetch at most N pages this run")
    parser.add_argument("--delay", type=float, default=0.25, help="seconds between requests")
    parser.add_argument("--lemmas", default="", help="comma-separated lemmas (default: every VER lemma of LexiqueMixte.tsv)")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    missingByLemma = missingTagsByLemma()
    entries = pruneToMissing(readOutput(), missingByLemma)
    missing = readMissing()
    done = {lemme for lemme, _o, _i in entries} | missing
    wanted = args.lemmas.split(",") if args.lemmas else sorted(missingByLemma)
    todo = [lemma for lemma in wanted if lemma not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(missingByLemma)} verbs have forms Mixte lacks; {len(done)} lemmas already done, {len(todo)} to fetch", flush=True)
    fetched = 0
    try:
        for lemma in todo:
            html = fetchPage(lemma)
            parsed = parseConjugationPage(html) if html is not None else []
            if not (parsed and addPage(entries, lemma, parsed, missingByLemma.get(lemma, set()))):
                missing.add(lemma)  # no page, or none of its forms is one Mixte lacks
            fetched += 1
            if fetched % FLUSH_EVERY == 0:
                writeOutput(entries)
                writeMissing(missing)
                print(f"  {fetched}/{len(todo)} ({lemma})", flush=True)
            time.sleep(args.delay)
    finally:
        rows = writeOutput(entries)
        writeMissing(missing)
        print(f"{fetched} pages fetched; {rows} rows in {OUTPUT_PATH}; {len(missing)} lemmas without a usable page", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
