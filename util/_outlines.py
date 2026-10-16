"""
The accepted outlines of a trainer word, tagged by kind (docs/MERGED_FEATURE_KEYS_PLAN.md, MKD24-MKD27): the outline
the hint shows above the keyboard, and every other outline the drill accepts, each `{steno, strokes, kind, rule?}`:
  long      the outline with the feature discriminating stroke (or the only outline of a word without one)
  merged    the merged outline (merged feature keys)
  affix     an affix abbreviation (`rule` = the rule rank, affix_abbreviations.tsv from S9b)
  brief     a word or stem brief (briefs.tsv from S9e)
The trainer shows the long outline above the keyboard and the short ones (merged, affix, brief) under it.
"""
import csv
import os
from typing import Any

from src.keyboard import Starboard, Strokes
from util._stenorender import checkedOutline, renderFinalStrokesToRTFCRE

AFFIX_ABBREVIATIONS = "affix_abbreviations.tsv"
BRIEF_ABBREVIATIONS = "briefs.tsv"


class ShortForms:
    """The short forms of S9b (affix abbreviations, with their rule rank) and S9e (briefs) by the outline they shorten (RTFCRE);
    empty without the files (optional layers)."""

    def __init__(self, starboard: Starboard, affixPath: str = AFFIX_ABBREVIATIONS, briefPath: str = BRIEF_ABBREVIATIONS) -> None:
        self.starboard = starboard
        self.keys = tuple(starboard.keyDisplayNames())
        self.byLong: dict[str, list[tuple[str, str, int | None]]] = {}
        for path, kind in ((affixPath, "affix"), (briefPath, "brief")):
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                for row in csv.DictReader(f, delimiter="\t"):
                    rank = int(row["rank"]) if kind == "affix" else None
                    shorts = self.byLong.setdefault(row["long"], [])
                    if (row["short"], kind, rank) not in shorts:
                        shorts.append((row["short"], kind, rank))

    def recordsFor(self, steno: str, maxRank: int | None = None) -> list[dict[str, Any]]:
        """The short-form records shortening `steno`: affix ones with rule rank at most `maxRank` when given, every brief."""
        records: list[dict[str, Any]] = []
        for short, kind, rank in self.byLong.get(steno, []):
            if rank is not None and maxRank is not None and rank > maxRank:
                continue
            record: dict[str, Any] = {"steno": short, "strokes": [list(stroke) for stroke in
                                                                   checkedOutline(short, self.keys, self.starboard)],
                                      "kind": kind}
            if rank is not None:
                record["rule"] = rank
            records.append(record)
        return records


def outlineRecord(starboard: Starboard, strokes: Strokes, kind: str) -> dict[str, Any]:
    return {"steno": renderFinalStrokesToRTFCRE(starboard, strokes),
            "strokes": [sorted(set(stroke)) for stroke in strokes], "kind": kind}


def taggedOutlines(starboard: Starboard, strokes: Strokes, longs: list[Strokes],
                   affix: ShortForms | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Practice (MKD24, MKD25): the hint is the long outline; the alternates are the merged outline, the other long
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
