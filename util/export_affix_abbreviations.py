"""
Theory Export (S8)-style trainer branch for the affix layer (Affix Abbreviation Building, S9d): the abbreviation
column of the trainer's Definitions page.

Run: python -m util.export_affix_abbreviations
Requires `affix_abbreviations.tsv` (util.export_affix_dictionary, S9b).
Output: steno-trainer/public/data/affix-abbreviations.json
    {"<spelling>": {"<long outline steno>": "<short outline steno>", ...}, ...}
The long outline is the one `definitions.json` lists as the word's chord, so the page matches a row by spelling and
chord. When several abbreviations share a long outline the first row of the TSV (highest frequency, best saving) wins.
"""
import csv
import json

SOURCE_TSV = "affix_abbreviations.tsv"
OUTPUT_PATH = "steno-trainer/public/data/affix-abbreviations.json"


def buildIndex(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """`rows`: the TSV rows (`spelling`, `long`, `short`, ...) -> spelling -> {long -> short}, first row wins."""
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        index.setdefault(row["spelling"], {}).setdefault(row["long"], row["short"])
    return index


def main() -> None:
    with open(SOURCE_TSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    index = buildIndex(rows)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(index)} spellings, {sum(len(v) for v in index.values())} abbreviated outlines.")


if __name__ == "__main__":
    main()
