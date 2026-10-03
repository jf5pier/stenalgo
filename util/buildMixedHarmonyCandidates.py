#!/bin/env python
#
# Read-only candidate list for the `mixed` rows of the vowel-harmony report
# (docs/VOWEL_HARMONY_CANDIDATES.md), cross-validated against fr.wiktionary.
#
# For every `mixed` (lemma, position) of scratch/vowel-harmony-report.tsv (run
# `python -m util.reportVowelHarmony` first) it takes the lemma's own form in LexiqueMixte.tsv
# (the row whose ortho is the lemme), counts the mid vowels before the position, and reads the
# same-ranked mid vowel (E e O o 9 2) in the IPA of the fr.wiktionary entry of the lemma. Nothing
# in the lexicon is changed; the verdict column is a hint for a human to validate:
#   position    every lax row is stem-stressed (nothing or a schwa follows) and no tense row is: the
#               regular loi de position (abonne/abonner, family 1 of the doc): left as is by decision
#   fix-minority  Wiktionary agrees with the majority vowel: the minority rows are the candidates
#   fix-majority  Wiktionary agrees with the minority vowel: the majority rows are the candidates
#   verb-fix-*  the same two verdicts for a verb lemma: the infinitive's vowel against stem-stressed
#               finite forms is the family-1 shape (abonner), listed apart because it was left as is
#   wikt-neutral  Wiktionary gives neither the lax nor the tense member (schwa, e/ɛ variant, ...)
#   no-wikt       no usable Wiktionary pronunciation, or its mid-vowel count differs from the lexicon's
#
# Usage: python -m util.buildMixedHarmonyCandidates [--report scratch/vowel-harmony-report.tsv]
#            [--out scratch/vowel-harmony-mixed-candidates.tsv] [--offline]
# The fr.wiktionary wikitext is cached in scratch/wiktionary-cache.json (batches of 50 titles).
import argparse
import collections
import csv
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request

from util.reportVowelHarmony import LEXIQUE_MIXTE_PATH, alignedUnits

CACHE_PATH = "scratch/wiktionary-cache.json"
API = "https://fr.wiktionary.org/w/api.php"
USER_AGENT = "stenalgo-harmony-check/1.0 (jf.stpierre@gmail.com)"
MID_LEXICON = frozenset("EeOo92")
IPA_TO_XSAMPA = {"ɛ": "E", "e": "e", "ɔ": "O", "o": "o", "œ": "9", "ø": "2"}
STEM_STRESSED_NEXT = frozenset({"-", "@", "°"})


def fetchWikitext(titles: list[str], cache: dict[str, str | None]) -> None:
    missing = [t for t in titles if t not in cache]
    for start in range(0, len(missing), 50):
        batch = missing[start:start + 50]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "format": "json", "redirects": "1", "titles": "|".join(batch)})
        request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)["query"]
        redirects = {r["from"]: r["to"] for r in data.get("redirects", [])}
        normalized = {n["from"]: n["to"] for n in data.get("normalized", [])}
        texts = {}
        for page in data["pages"].values():
            revisions = page.get("revisions")
            texts[page["title"]] = revisions[0]["slots"]["main"]["*"] if revisions else None
        for title in batch:
            target = normalized.get(title, title)
            target = redirects.get(target, target)
            cache[title] = texts.get(target)
        time.sleep(1)


def frenchSection(wikitext: str) -> str:
    match = re.search(r"==\s*\{\{langue\|fr\}\}\s*==(.*?)(?=\n==\s*\{\{langue\||\Z)", wikitext, re.S)
    return match.group(1) if match else ""


def wiktionaryPronunciation(wikitext: str | None) -> str | None:
    if not wikitext:
        return None
    section = frenchSection(wikitext)
    for pattern in (r"\{\{pron\|([^|}=]+)\|fr", r"\{\{fr-(?:rég|inv|accord-[^|}]*)\|([^|}=]+)",
                    r"\|pron=([^|}]+)"):
        match = re.search(pattern, section)
        if match and match.group(1).strip():
            return match.group(1).strip().strip("\\")
    return None


def midVowelsOfIpa(ipa: str) -> list[str]:
    """The oral mid vowels of an IPA string as X-SAMPA letters; nasals (ɛ̃ œ̃ ɔ̃) are skipped."""
    decomposed = unicodedata.normalize("NFD", ipa)
    vowels = []
    for i, ch in enumerate(decomposed):
        if ch in IPA_TO_XSAMPA and not (i + 1 < len(decomposed) and decomposed[i + 1] == "̃"):
            vowels.append(IPA_TO_XSAMPA[ch])
    return vowels


def lemmaFormVowel(rows: list[dict[str, str]], lemme: str, position: int) -> tuple[str, int, int] | None:
    """(vowel of the lemma form at `position`, its rank among the row's mid vowels, mid-vowel count)."""
    for row in rows:
        if row["ortho"] != lemme:
            continue
        units = alignedUnits(row)
        if units is None or position >= len(units):
            continue
        mids = [u for u in units if u[2] in MID_LEXICON]
        if units[position][2] not in MID_LEXICON:
            continue
        rank = sum(1 for u in mids if u[0] < position)
        return units[position][2], rank, len(mids)
    return None


def nextSet(field_value: str) -> set[str]:
    names: set[str] = set()
    for item in field_value.split(","):
        if item:
            match = re.match(r"(-?[^\d]*)", item)
            assert match is not None  # the pattern matches the empty string
            names.add(match.group(1) or "-")
    return names


def verdict(record: dict[str, str], wikt: list[str] | None, lemmaInfo: tuple[str, int, int] | None) -> tuple[str, str]:
    lax, tense = record["pair"].split("/")
    laxNext, tenseNext = nextSet(record["lax_next"]), nextSet(record["tense_next"])
    if laxNext <= STEM_STRESSED_NEXT and not (tenseNext & STEM_STRESSED_NEXT):
        return "position", ""
    if lemmaInfo is None or not wikt:
        return "no-wikt", ""
    _, rank, count = lemmaInfo
    if len(wikt) != count:
        return "no-wikt", ""
    w = wikt[rank]
    if w not in (lax, tense):
        return "wikt-neutral", w
    majorityVowel = lax if int(record["lax_rows"]) >= int(record["tense_rows"]) else tense
    if int(record["lax_rows"]) == int(record["tense_rows"]):
        return ("fix-minority", w)  # tie: Wiktionary decides, both sides are "minority"
    return ("fix-minority" if w == majorityVowel else "fix-majority"), w


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", default="scratch/vowel-harmony-report.tsv")
    parser.add_argument("--out", default="scratch/vowel-harmony-mixed-candidates.tsv")
    parser.add_argument("--offline", action="store_true", help="Use the cache only, fetch nothing.")
    args = parser.parse_args()

    with open(args.report, newline="", encoding="utf-8") as f:
        mixed = [r for r in csv.DictReader(f, delimiter="\t") if r["class"] == "mixed"]
    with open(LEXIQUE_MIXTE_PATH, newline="", encoding="utf-8") as f:
        byLemma: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
        for row in csv.DictReader(f, delimiter="\t"):
            byLemma[row["lemme"]].append(row)

    cache: dict[str, str | None] = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            cache = json.load(f)
    lemmas = sorted({r["lemme"] for r in mixed})
    if not args.offline:
        fetchWikitext(lemmas, cache)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    out = []
    for record in mixed:
        lemme = record["lemme"]
        info = lemmaFormVowel(byLemma[lemme], lemme, int(record["position"]))
        ipa = wiktionaryPronunciation(cache.get(lemme))
        wikt = midVowelsOfIpa(ipa) if ipa else None
        kind, w = verdict(record, wikt, info)
        isVerb = any(r["cgram"] == "VER" and r["ortho"] == lemme for r in byLemma[lemme])
        if isVerb and kind in ("fix-minority", "fix-majority"):
            kind = "verb-" + kind  # infinitive vs stem-stressed finite forms: the family-1 shape
        out.append({**record, "lemma_form_vowel": info[0] if info else "", "wikt_ipa": ipa or "",
                    "wikt_vowel": w, "verdict": kind})
    order = {"fix-minority": 0, "fix-majority": 1, "verb-fix-minority": 2, "verb-fix-majority": 3,
             "wikt-neutral": 4, "no-wikt": 5, "position": 6}
    out.sort(key=lambda r: (order[r["verdict"]], r["pair"], r["lemme"]))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    counts = collections.Counter((r["verdict"], r["pair"]) for r in out)
    print(f"{len(out)} mixed (lemma, position) rows in {len(lemmas)} lemmas -> {args.out}")
    for (kind, pair), n in sorted(counts.items(), key=lambda kv: (order[kv[0][0]], kv[0][1])):
        print(f"  {kind:13} {pair}: {n}")


if __name__ == "__main__":
    main()
