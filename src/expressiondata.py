"""
Serialized data of the expression decoder (PLAN_2026-10-04-expression-decoder.md, step 5): everything
`ExpressionDecoder` and `ReadingRanker` need, as one JSON document, so a Plover plugin decodes without the
pipeline (no lexicon, no pickles, no `Starboard`).

Document (`FORMAT_VERSION`): ``rules`` (attaches, briefs, orderBan), ``wordIndex`` (the stock Plover dictionary
the outline -> word index is read from: its file name next to this one, a fingerprint of the index and its size;
``words`` holds the index itself when no file is named), ``unitStrokes`` (attach particle words only), ``attested`` (outline, normalized reading, frequency, written text), ``unitProbabilities``,
``partners`` (pinky-diagonal key conflicts), ``legality`` (the layout's chord legality). A stroke is a list of
key ids, an outline a list of strokes; both come back as sorted tuples.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

from src.expressiondecoder import ExpressionDecoder
from src.expressionranking import ReadingRanker
from src.expressionmodel import AttachRule, BriefRule, Rules
from src.keyconflicts import KeyConflicts
from src.strokes import Stroke, Strokes

__all__ = ["FORMAT_VERSION", "ChordLegality", "legalityFromStarboard", "bundleToDict", "loadBundle"]

FORMAT_VERSION = 2


class ChordLegality:
    """`SimContext.isLegal` without the layout: a chord is legal when every part (onset, nucleus, coda) share of
    it gives each finger a legal combination of that finger's keys."""

    def __init__(self, partOf: Mapping[int, str], fingers: Mapping[str, Iterable[tuple[int, ...]]]) -> None:
        self.partOf = dict(partOf)
        self.fingers = {f: frozenset(tuple(c) for c in combos) for f, combos in fingers.items()}
        self._singles = {f: frozenset(k for c in combos if len(c) == 1 for k in c)
                         for f, combos in self.fingers.items()}
        self._cache: dict[Stroke, bool] = {}

    def __call__(self, keys: Stroke) -> bool:
        v = self._cache.get(keys)
        if v is None:
            v = self._cache[keys] = self._legal(keys)
        return v

    def _legal(self, keys: Stroke) -> bool:
        if any(k not in self.partOf for k in keys):
            return False
        for part in {self.partOf[k] for k in keys}:
            sub = [k for k in set(keys) if self.partOf[k] == part]
            for finger, combos in self.fingers.items():
                mine = tuple(sorted(k for k in sub if k in self._singles[finger]))
                if mine and mine not in combos:
                    return False
        return True

    def toDict(self) -> dict:
        return {"partOf": {str(k): p for k, p in sorted(self.partOf.items())},
                "fingers": {f: sorted(list(c) for c in combos) for f, combos in self.fingers.items()}}

    @classmethod
    def fromDict(cls, data: dict) -> "ChordLegality":
        return cls({int(k): p for k, p in data["partOf"].items()}, data["fingers"])


def legalityFromStarboard(starboard: object) -> ChordLegality:
    partOf = {key: part for part, keys in starboard.keyIDinSyllabicPart.items() for key in keys}  # type: ignore[attr-defined]
    table = starboard._possibleKeypress                                                      # type: ignore[attr-defined]
    return ChordLegality(partOf, {f: list(table[f]) for f in table.fingers})


def wordIndexFingerprint(words: Mapping[Strokes, Iterable[str]]) -> str:
    """Hash of an outline -> words index, independent of file formatting and order: the `.stenalgo` file records
    it and the loader compares it with the index it read, so a dictionary built from another theory is refused."""
    digest = hashlib.sha256()
    for outline in sorted(words):
        label = "/".join(",".join(map(str, stroke)) for stroke in outline)
        for word in sorted(set(words[outline])):
            digest.update(f"{label}\t{word}\n".encode("utf-8"))
    return digest.hexdigest()


def _stroke(stroke: Iterable[int]) -> list[int]:
    return sorted(stroke)


def _tuples(value):
    """JSON lists back to the nested tuples a reading signature is made of."""
    return tuple(_tuples(v) for v in value) if isinstance(value, list) else value


def bundleToDict(rules: Rules, words: Mapping[Strokes, Iterable[str]], unitStrokes: Mapping[str, int],
                 attested: Mapping[tuple[Strokes, tuple], float], unitProbabilities: Mapping[str, float],
                 conflicts: KeyConflicts, legality: ChordLegality,
                 attestedText: Mapping[tuple[Strokes, tuple], str] | None = None,
                 wordsFile: str | None = None) -> dict:
    """`wordsFile`: name (next to the written file) of the stock dictionary that holds the word index; the
    document then stores its fingerprint instead of the 170,000 outlines."""
    outline = lambda o: [_stroke(s) for s in o]  # noqa: E731
    return {
        "format": FORMAT_VERSION,
        "rules": {
            "attaches": [{"expression": list(r.expression), "position": r.position,
                          "keypress": list(r.keypress), "family": r.family, "elision": r.elision}
                         for r in rules.attaches],
            "briefs": [{"expression": list(r.expression), "strokes": outline(r.strokes), "family": r.family}
                       for r in rules.briefs],
            "orderBan": sorted([list(a), list(b)] for a, b in rules.orderBan),
        },
        **({"wordIndex": {"file": wordsFile, "fingerprint": wordIndexFingerprint(words), "count": len(words)}}
           if wordsFile else {"words": [[outline(o), sorted(set(s))] for o, s in sorted(words.items())]}),
        # the decoder asks only about the words of attach particles (`_spans`): the rest is dead weight
        "unitStrokes": {u: unitStrokes[u] for u in sorted({u for r in rules.attaches for u in r.expression})
                        if u in unitStrokes},
        "attested": [[outline(o), sig, freq, (attestedText or {}).get((o, sig), "")]
                     for (o, sig), freq in sorted(attested.items(), key=repr)],
        "unitProbabilities": dict(sorted(unitProbabilities.items())),
        "partners": {str(k): sorted(v) for k, v in sorted(conflicts.partners.items())},
        "legality": legality.toDict(),
    }


def loadBundle(source: "str | Path | dict", words: "Mapping[Strokes, Iterable[str]] | None" = None
               ) -> tuple[ExpressionDecoder, ReadingRanker]:
    """The decoder and the ranker of a bundle (a path or an already parsed document). A bundle that names a
    word-index file needs `words`, the index read from it: it must match the recorded fingerprint."""
    data: dict
    if isinstance(source, dict):
        data = source
    else:
        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)
    if data.get("format") != FORMAT_VERSION:
        raise ValueError(f"expression data format {data.get('format')!r}, expected {FORMAT_VERSION}")
    r = data["rules"]
    outline = lambda o: tuple(tuple(s) for s in o)  # noqa: E731
    rules = Rules(
        attaches=tuple(AttachRule(tuple(a["expression"]), a["position"], tuple(a["keypress"]),
                                  a["family"], a["elision"]) for a in r["attaches"]),
        briefs=tuple(BriefRule(tuple(b["expression"]), outline(b["strokes"]), b["family"]) for b in r["briefs"]),
        orderBan=frozenset((tuple(a), tuple(b)) for a, b in r["orderBan"]))
    if "words" in data:
        words = {outline(o): s for o, s in data["words"]}
    else:
        if words is None:
            raise ValueError(f"the data names its word index ({data['wordIndex']['file']}): pass it as `words`")
        if wordIndexFingerprint(words) != data["wordIndex"]["fingerprint"]:
            raise ValueError(f"{data['wordIndex']['file']} is not the dictionary this data was built with "
                             f"(word index fingerprint differs): regenerate both from the same theory")
    conflicts = KeyConflicts({int(k): frozenset(v) for k, v in data["partners"].items()})
    decoder = ExpressionDecoder(rules, words, data["unitStrokes"], ChordLegality.fromDict(data["legality"]),
                                conflicts)
    ranker = ReadingRanker({(outline(o), _tuples(sig)): f for o, sig, f, _t in data["attested"]},
                           data["unitProbabilities"],
                           {(outline(o), _tuples(sig)): t for o, sig, _f, t in data["attested"] if t})
    return decoder, ranker
