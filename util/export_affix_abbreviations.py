"""
Theory Export (S8)-style trainer branch for the affix layer (Affix Abbreviation Building, S9d): the abbreviation
column of the trainer's Definitions page.

Run: python -m util.export_affix_abbreviations
Requires `affix_abbreviations.tsv` (util.export_affix_dictionary, S9b).
Output: steno-trainer/public/data/affix-abbreviations.json
    {"<spelling>": {"<long outline steno>": ["<short outline steno>", ...], ...}, ...}
The long outline is the one `definitions.json` lists as the word's chord, so the page matches a row by spelling and
chord. Every short outline of a long one is listed, the briefs (`briefs.tsv`, S9e) first, then the affix abbreviations
in TSV order (highest frequency, best saving first), a repeated short outline once. A word with a brief per mood or tense
has one entry per conjugated form (each its own long outline). A short outline whose long one is no chord of the Definitions
page (the unmerged long form of a word whose merged one is listed: `e/tie/-d` for `e/tied`) is listed under the page's chord that
spells the same strokes in one piece (`foldIntoDefinitionChords`), after that chord's own.
Also writes steno-trainer/public/data/affix-word-rules.json, {"<lowercase spelling>": [rule ranks, ascending]}: the rules that shorten a
spelling, for the trainer's abbreviation rule hint in Words and Sentences modes (the lessons carry only the words they teach).
"""
import csv
import json

SOURCE_TSV = "affix_abbreviations.tsv"
BRIEFS_TSV = "briefs.tsv"
DEFINITIONS_PATH = "steno-trainer/public/data/definitions.json"
OUTPUT_PATH = "steno-trainer/public/data/affix-abbreviations.json"
RULES_OUTPUT_PATH = "steno-trainer/public/data/affix-word-rules.json"


def buildIndex(rows: list[dict[str, str]]) -> dict[str, dict[str, list[str]]]:
    """`rows`: the TSV rows (`spelling`, `long`, `short`, ...), briefs first -> spelling -> {long -> its distinct shorts, in row order}."""
    index: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        shorts = index.setdefault(row["spelling"], {}).setdefault(row["long"], [])
        if row["short"] not in shorts:
            shorts.append(row["short"])
    return index


def _strokeLetters(steno: str) -> str:
    """The letters of an outline regardless of its stroke boundaries and order inside a stroke."""
    return "".join(sorted(steno.replace("/", "").replace("-", "")))


def foldIntoDefinitionChords(index: dict[str, dict[str, list[str]]],
                             chordsBySpelling: dict[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    """Re-keys, per spelling, each long outline that is not a chord of the Definitions page to the chords there with the same
    letters (`_strokeLetters`); a long outline matching none stays as it is. A chord's own shorts come first."""
    folded: dict[str, dict[str, list[str]]] = {}
    for spelling, byLong in index.items():
        chords = chordsBySpelling.get(spelling, [])
        result: dict[str, list[str]] = {long: list(shorts) for long, shorts in byLong.items() if long in chords}
        for long, shorts in byLong.items():
            if long in chords:
                continue
            targets = [chord for chord in chords if _strokeLetters(chord) == _strokeLetters(long)] or [long]
            for target in targets:
                known = result.setdefault(target, [])
                known.extend(short for short in shorts if short not in known)
        folded[spelling] = result
    return folded


def definitionChords(path: str) -> dict[str, list[str]]:
    """spelling -> the chords `definitions.json` lists for it."""
    with open(path, encoding="utf-8") as f:
        document = json.load(f)
    chords: dict[str, list[str]] = {}
    for _base, entries in document["groups"]:
        for ortho, _phonology, _frequency, entryChords in entries:
            known = chords.setdefault(ortho, [])
            known.extend(chord[0] for chord in entryChords if chord[0] not in known)
    return chords


def buildRuleIndex(rows: list[dict[str, str]]) -> dict[str, list[int]]:
    """`rows`: the TSV rows (`spelling`, `rank`, ...) -> lowercase spelling -> the distinct rule ranks, ascending."""
    ranks: dict[str, set[int]] = {}
    for row in rows:
        ranks.setdefault(row["spelling"].lower(), set()).add(int(row["rank"]))
    return {spelling: sorted(found) for spelling, found in ranks.items()}


def readRows(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def main() -> None:
    rows = readRows(SOURCE_TSV)
    index = foldIntoDefinitionChords(buildIndex(readRows(BRIEFS_TSV) + rows), definitionChords(DEFINITIONS_PATH))
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    with open(RULES_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(buildRuleIndex(rows), f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(index)} spellings, {sum(len(shorts) for v in index.values() for shorts in v.values())} abbreviated outlines.")


if __name__ == "__main__":
    main()
