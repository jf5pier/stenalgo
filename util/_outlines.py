"""
The accepted outlines of a trainer word, tagged by kind (docs/MERGED_FEATURE_KEYS_PLAN.md, D24-D27): the outline
the hint shows above the keyboard, and every other outline the drill accepts, each `{steno, strokes, kind, rule?}`:
  long      the outline with the feature discriminating stroke (or the only outline of a word without one)
  merged    the merged outline (merged feature keys)
  affix     an affix abbreviation (`rule` = the rule rank, affix_abbreviations.tsv from S9b)
The trainer shows the long outline above the keyboard and the short ones (merged, affix) under it.
"""
import csv
import os
from typing import Any

from src.keyboard import Starboard, Strokes
from util._stenorender import checkedOutline, renderFinalStrokesToRTFCRE

AFFIX_ABBREVIATIONS = "affix_abbreviations.tsv"


class AffixShorts:
    """The affix abbreviations of S9b by the outline they shorten (RTFCRE); empty without the file (optional layer)."""

    def __init__(self, starboard: Starboard, path: str = AFFIX_ABBREVIATIONS) -> None:
        self.starboard = starboard
        self.keys = tuple(starboard.keyDisplayNames())
        self.byLong: dict[str, list[tuple[str, int]]] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for row in csv.DictReader(f, delimiter="\t"):
                    shorts = self.byLong.setdefault(row["long"], [])
                    if (row["short"], int(row["rank"])) not in shorts:
                        shorts.append((row["short"], int(row["rank"])))

    def recordsFor(self, steno: str, maxRank: int | None = None) -> list[dict[str, Any]]:
        """The affix outline records shortening `steno`, rule rank at most `maxRank` when given."""
        return [{"steno": short, "strokes": [list(stroke) for stroke in checkedOutline(short, self.keys, self.starboard)],
                 "kind": "affix", "rule": rank}
                for short, rank in self.byLong.get(steno, []) if maxRank is None or rank <= maxRank]


def outlineRecord(starboard: Starboard, strokes: Strokes, kind: str) -> dict[str, Any]:
    return {"steno": renderFinalStrokesToRTFCRE(starboard, strokes),
            "strokes": [sorted(set(stroke)) for stroke in strokes], "kind": kind}


def taggedOutlines(starboard: Starboard, strokes: Strokes, longs: list[Strokes],
                   affix: AffixShorts | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Practice (D24, D25): the hint is the long outline; the alternates are the merged outline, the other long
    outlines and the affix abbreviations of each of them."""
    if longs:
        hint = outlineRecord(starboard, longs[0], "long")
        others = [outlineRecord(starboard, strokes, "merged")] + [outlineRecord(starboard, s, "long") for s in longs[1:]]
    else:
        hint, others = outlineRecord(starboard, strokes, "long"), []
    alternates: list[dict[str, Any]] = []
    for record in others + ([] if affix is None else [r for o in [hint] + others for r in affix.recordsFor(o["steno"])]):
        if record["steno"] != hint["steno"] and all(record["steno"] != a["steno"] for a in alternates):
            alternates.append(record)
    return hint, alternates
